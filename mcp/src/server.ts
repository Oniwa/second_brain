import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createClient } from "@supabase/supabase-js";
import * as dotenv from "dotenv";
import * as path from "path";
import * as url from "url";

// Load .env from project root (two levels up from mcp/src/)
const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY!;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !OPENAI_API_KEY) {
  console.error("Missing required environment variables. Check your .env file.");
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

// ── Helpers ──────────────────────────────────────────────────────────────────

async function generateEmbedding(text: string): Promise<number[]> {
  const res = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: "text-embedding-3-small", input: text }),
  });
  if (!res.ok) throw new Error(`Embedding failed: ${await res.text()}`);
  const data = await res.json();
  return data.data[0].embedding;
}

function formatThought(t: Record<string, unknown>): string {
  const lines: string[] = [
    `**${t.title ?? "Untitled"}** [${t.category}]`,
    t.summary ? `${t.summary}` : "",
    t.people && (t.people as string[]).length
      ? `People: ${(t.people as string[]).join(", ")}`
      : "",
    t.topics && (t.topics as string[]).length
      ? `Topics: ${(t.topics as string[]).join(", ")}`
      : "",
    t.action_items && (t.action_items as string[]).length
      ? `Actions: ${(t.action_items as string[]).join(" | ")}`
      : "",
    `Captured: ${new Date(t.created_at as string).toLocaleDateString()} · Source: ${t.source ?? "unknown"}`,
    t.similarity ? `Similarity: ${((t.similarity as number) * 100).toFixed(1)}%` : "",
  ];
  return lines.filter(Boolean).join("\n");
}

// ── Tool handlers ─────────────────────────────────────────────────────────────

async function semanticSearch(args: {
  query: string;
  limit?: number;
  category?: string;
}): Promise<string> {
  const embedding = await generateEmbedding(args.query);
  const { data, error } = await supabase.rpc("semantic_search", {
    query_embedding: embedding,
    match_limit: args.limit ?? 10,
    filter_category: args.category ?? null,
    filter_status: "active",
  });
  if (error) throw new Error(`Search failed: ${error.message}`);
  if (!data || data.length === 0) return "No matching thoughts found.";
  return data.map((t: Record<string, unknown>) => formatThought(t)).join("\n\n---\n\n");
}

async function listRecent(args: {
  days?: number;
  category?: string;
}): Promise<string> {
  const since = new Date();
  since.setDate(since.getDate() - (args.days ?? 7));

  let query = supabase
    .from("thoughts")
    .select("id, title, summary, category, people, topics, action_items, source, created_at")
    .eq("status", "active")
    .gte("created_at", since.toISOString())
    .order("created_at", { ascending: false })
    .limit(50);

  if (args.category) query = query.eq("category", args.category);

  const { data, error } = await query;
  if (error) throw new Error(`List failed: ${error.message}`);
  if (!data || data.length === 0)
    return `No thoughts captured in the last ${args.days ?? 7} days.`;
  return `${data.length} thought(s) in the last ${args.days ?? 7} days:\n\n` +
    data.map((t: Record<string, unknown>) => formatThought(t)).join("\n\n---\n\n");
}

async function captureThought(args: {
  text: string;
  source?: string;
}): Promise<string> {
  const res = await fetch(`${SUPABASE_URL}/functions/v1/process-thought`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
    },
    body: JSON.stringify({ text: args.text, source: args.source ?? "mcp" }),
  });
  const data = await res.json();
  if (!res.ok || !data.ok)
    throw new Error(data.error ?? "Capture failed");
  return [
    `✓ Captured: **${data.title}**`,
    `Category: ${data.category} (confidence: ${(data.confidence * 100).toFixed(0)}%)`,
    `Status: ${data.status}`,
    `ID: ${data.id}`,
  ].join("\n");
}

async function getStats(args: { days?: number }): Promise<string> {
  const since = new Date();
  since.setDate(since.getDate() - (args.days ?? 30));

  const { data, error } = await supabase
    .from("thoughts")
    .select("category, topics, created_at, status")
    .gte("created_at", since.toISOString());

  if (error) throw new Error(`Stats failed: ${error.message}`);
  if (!data || data.length === 0)
    return `No thoughts in the last ${args.days ?? 30} days.`;

  // Category distribution
  const cats: Record<string, number> = {};
  const topicCount: Record<string, number> = {};
  for (const t of data) {
    cats[t.category] = (cats[t.category] ?? 0) + 1;
    for (const topic of t.topics ?? []) {
      topicCount[topic] = (topicCount[topic] ?? 0) + 1;
    }
  }

  const sortedCats = Object.entries(cats).sort((a, b) => b[1] - a[1]);
  const topTopics = Object.entries(topicCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  const needsReview = data.filter((t) => t.status === "needs_review").length;

  const lines = [
    `**Brain stats — last ${args.days ?? 30} days**`,
    `Total captures: ${data.length}`,
    "",
    "**By category:**",
    ...sortedCats.map(([cat, n]) => `  ${cat}: ${n}`),
    "",
    "**Top topics:**",
    ...topTopics.map(([topic, n]) => `  ${topic}: ${n}`),
    "",
    needsReview > 0 ? `⚠️ ${needsReview} thought(s) need review` : "✓ No thoughts need review",
  ];
  return lines.join("\n");
}

async function getContext(args: { topic: string }): Promise<string> {
  // Combine semantic search + keyword match on topics array
  const [embedding, keywordResult] = await Promise.all([
    generateEmbedding(args.topic),
    supabase
      .from("thoughts")
      .select("id, title, summary, category, people, topics, action_items, source, created_at")
      .eq("status", "active")
      .contains("topics", [args.topic])
      .order("created_at", { ascending: false })
      .limit(20),
  ]);

  const { data: semanticData, error: semErr } = await supabase.rpc("semantic_search", {
    query_embedding: embedding,
    match_limit: 20,
    filter_category: null,
    filter_status: "active",
  });
  if (semErr) throw new Error(`Context search failed: ${semErr.message}`);

  // Merge and deduplicate by id, keyword matches first
  const seen = new Set<string>();
  const merged: Record<string, unknown>[] = [];
  for (const t of (keywordResult.data ?? [])) {
    if (!seen.has(t.id as string)) { seen.add(t.id as string); merged.push(t); }
  }
  for (const t of (semanticData ?? [])) {
    if (!seen.has(t.id as string)) { seen.add(t.id as string); merged.push(t); }
  }

  if (merged.length === 0) return `No context found for "${args.topic}".`;
  return `**Context for "${args.topic}"** (${merged.length} thoughts)\n\n` +
    merged.map((t) => formatThought(t)).join("\n\n---\n\n");
}

// ── MCP Server ────────────────────────────────────────────────────────────────

const server = new Server(
  { name: "second-brain", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "semantic_search",
      description: "Search your brain by meaning. Finds thoughts semantically related to your query, not just keyword matches.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "What you want to find" },
          limit: { type: "number", description: "Max results (default 10)" },
          category: {
            type: "string",
            enum: ["person", "project", "idea", "admin", "insight"],
            description: "Filter by category (optional)",
          },
        },
        required: ["query"],
      },
    },
    {
      name: "list_recent",
      description: "Browse recently captured thoughts, optionally filtered by category.",
      inputSchema: {
        type: "object",
        properties: {
          days: { type: "number", description: "How many days back to look (default 7)" },
          category: {
            type: "string",
            enum: ["person", "project", "idea", "admin", "insight"],
            description: "Filter by category (optional)",
          },
        },
      },
    },
    {
      name: "capture_thought",
      description: "Save a new thought to your brain. It will be automatically embedded, classified, and stored.",
      inputSchema: {
        type: "object",
        properties: {
          text: { type: "string", description: "The thought to capture" },
          source: { type: "string", description: "Where this came from (default: mcp)" },
        },
        required: ["text"],
      },
    },
    {
      name: "get_stats",
      description: "See thinking patterns over time — category breakdown, top topics, capture frequency.",
      inputSchema: {
        type: "object",
        properties: {
          days: { type: "number", description: "Time range in days (default 30)" },
        },
      },
    },
    {
      name: "get_context",
      description: "Pull everything your brain knows about a topic. Combines semantic search with keyword matching.",
      inputSchema: {
        type: "object",
        properties: {
          topic: { type: "string", description: "The topic to gather context on" },
        },
        required: ["topic"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const a = (args ?? {}) as Record<string, unknown>;

  try {
    let text: string;
    switch (name) {
      case "semantic_search":
        text = await semanticSearch(a as Parameters<typeof semanticSearch>[0]);
        break;
      case "list_recent":
        text = await listRecent(a as Parameters<typeof listRecent>[0]);
        break;
      case "capture_thought":
        text = await captureThought(a as Parameters<typeof captureThought>[0]);
        break;
      case "get_stats":
        text = await getStats(a as Parameters<typeof getStats>[0]);
        break;
      case "get_context":
        text = await getContext(a as Parameters<typeof getContext>[0]);
        break;
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    return { content: [{ type: "text", text }] };
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${(err as Error).message}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Second Brain MCP server running");
