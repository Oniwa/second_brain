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
    `ID: ${t.id}`,
  ];
  return lines.filter(Boolean).join("\n");
}

// ── Tool handlers ─────────────────────────────────────────────────────────────

async function semanticSearch(args: {
  query: string;
  limit?: number;
  category?: string;
  status?: string;
}): Promise<string> {
  const embedding = await generateEmbedding(args.query);
  const { data, error } = await supabase.rpc("semantic_search", {
    query_embedding: embedding,
    match_limit: args.limit ?? 10,
    filter_category: args.category ?? null,
    filter_status: args.status === "all" ? null : (args.status ?? "active"),
  });
  if (error) throw new Error(`Search failed: ${error.message}`);
  if (!data || data.length === 0) return "No matching thoughts found.";
  return data.map((t: Record<string, unknown>) => formatThought(t)).join("\n\n---\n\n");
}

async function listRecent(args: {
  days?: number;
  category?: string;
  status?: string;
}): Promise<string> {
  const since = new Date();
  since.setDate(since.getDate() - (args.days ?? 7));

  let query = supabase
    .from("thoughts")
    .select("id, title, summary, category, people, topics, action_items, source, created_at")
    .gte("created_at", since.toISOString())
    .order("created_at", { ascending: false })
    .limit(50);

  if ((args.status ?? "active") !== "all") {
    query = query.eq("status", args.status ?? "active");
  }

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

  const [windowResult, allTimeResult] = await Promise.all([
    supabase
      .from("thoughts")
      .select("category, topics, created_at, status")
      .gte("created_at", since.toISOString()),
    supabase
      .from("thoughts")
      .select("status"),
  ]);

  if (windowResult.error) throw new Error(`Stats failed: ${windowResult.error.message}`);
  if (allTimeResult.error) throw new Error(`Stats failed: ${allTimeResult.error.message}`);

  const data = windowResult.data ?? [];

  // All-time status counts
  const statusCounts: Record<string, number> = {};
  for (const t of allTimeResult.data ?? []) {
    statusCounts[t.status] = (statusCounts[t.status] ?? 0) + 1;
  }
  const totalAllTime = Object.values(statusCounts).reduce((a, b) => a + b, 0);

  // Time-windowed category and topic distribution
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

  const lines = [
    "**Brain overview (all time)**",
    `Total thoughts: ${totalAllTime}`,
    ...["active", "archived", "needs_review"].map((s) => `  ${s}: ${statusCounts[s] ?? 0}`),
    "",
    `**Trends — last ${args.days ?? 30} days**`,
    `Captures this period: ${data.length}`,
    "",
    "**By category:**",
    ...sortedCats.map(([cat, n]) => `  ${cat}: ${n}`),
    "",
    "**Top topics:**",
    ...topTopics.map(([topic, n]) => `  ${topic}: ${n}`),
  ];
  return lines.join("\n");
}

async function updateThought(args: {
  id: string;
  raw_text?: string;
  title?: string;
  summary?: string;
  category?: string;
  people?: string[];
  topics?: string[];
  action_items?: string[];
  status?: string;
}): Promise<string> {
  const { id, ...fields } = args;
  const updates = Object.fromEntries(Object.entries(fields).filter(([, v]) => v !== undefined));
  if (Object.keys(updates).length === 0) return "No fields provided to update.";
  const { data, error } = await supabase
    .from("thoughts")
    .update(updates)
    .eq("id", id)
    .select("title")
    .single();
  if (error) throw new Error(`Update failed: ${error.message}`);
  if (!data) return `No thought found with ID ${id}.`;
  return `Updated: ${data.title}`;
}

async function archiveThought(args: { id: string }): Promise<string> {
  const { data, error } = await supabase
    .from("thoughts")
    .update({ status: "archived" })
    .eq("id", args.id)
    .select("title")
    .single();
  if (error) throw new Error(`Archive failed: ${error.message}`);
  if (!data) return `No thought found with ID ${args.id}.`;
  return `Archived: ${data.title}`;
}

async function deleteThought(args: { id: string }): Promise<string> {
  const { error, count } = await supabase
    .from("thoughts")
    .delete({ count: "exact" })
    .eq("id", args.id);
  if (error) throw new Error(`Delete failed: ${error.message}`);
  if (count === 0) return `No thought found with ID ${args.id}.`;
  return `Deleted thought ${args.id}.`;
}

async function meetingPrep(args: {
  meeting: string;
  people?: string[];
}): Promise<string> {
  const { meeting, people = [] } = args;

  const embedding = await generateEmbedding(meeting);

  // Run semantic search + one people-array query per named person, all in parallel
  const [semanticResult, ...peopleResults] = await Promise.all([
    supabase.rpc("semantic_search", {
      query_embedding: embedding,
      match_limit: 15,
      filter_category: null,
      filter_status: "active",
    }),
    ...people.map((person) =>
      supabase
        .from("thoughts")
        .select("id, title, summary, category, people, topics, action_items, source, created_at")
        .eq("status", "active")
        .contains("people", [person])
        .order("created_at", { ascending: false })
        .limit(10)
    ),
  ]);

  if (semanticResult.error) throw new Error(`Search failed: ${semanticResult.error.message}`);

  // Merge and deduplicate — explicit people matches first (highest signal), then semantic
  const seen = new Set<string>();
  const merged: Record<string, unknown>[] = [];

  for (const result of peopleResults) {
    for (const t of (result.data ?? [])) {
      if (!seen.has(t.id as string)) { seen.add(t.id as string); merged.push(t); }
    }
  }
  for (const t of (semanticResult.data ?? [])) {
    if (!seen.has(t.id as string)) { seen.add(t.id as string); merged.push(t); }
  }

  if (merged.length === 0) {
    return `No relevant context found for "${meeting}". Nothing captured about this yet.`;
  }

  const peopleLabel = people.length ? ` · people: ${people.join(", ")}` : "";
  return `**Meeting prep context: "${meeting}"**${peopleLabel}\n(${merged.length} relevant thoughts)\n\n` +
    merged.map((t) => formatThought(t)).join("\n\n---\n\n");
}

async function getThought(args: { id: string }): Promise<string> {
  const { data, error } = await supabase
    .from("thoughts")
    .select("id, raw_text, title, summary, category, people, topics, action_items, source, status, confidence, created_at, updated_at")
    .eq("id", args.id)
    .single();
  if (error) throw new Error(`Lookup failed: ${error.message}`);
  if (!data) return `No thought found with ID ${args.id}.`;

  const lines = [
    `**${data.title}** [${data.category}]`,
    `Status: ${data.status} · Confidence: ${(data.confidence * 100).toFixed(0)}%`,
    `Source: ${data.source} · Captured: ${new Date(data.created_at).toLocaleDateString()}`,
    "",
    `**Summary:** ${data.summary}`,
    data.people?.length ? `**People:** ${data.people.join(", ")}` : "",
    data.topics?.length ? `**Topics:** ${data.topics.join(", ")}` : "",
    data.action_items?.length ? `**Actions:** ${data.action_items.join(" | ")}` : "",
    "",
    `**Raw text:**`,
    data.raw_text,
    "",
    `ID: ${data.id}`,
  ];
  return lines.filter((l) => l !== undefined && l !== null).join("\n");
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
  { name: "second-brain", version: "1.3.0" },
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
          status: {
            type: "string",
            enum: ["active", "archived", "all"],
            description: "Filter by status (default: active)",
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
          status: {
            type: "string",
            enum: ["active", "archived", "all"],
            description: "Filter by status (default: active)",
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
      name: "update_thought",
      description: "Update fields on an existing thought — correct people, topics, title, category, or any other field.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "The UUID of the thought to update" },
          raw_text: { type: "string", description: "Corrected raw text" },
          title: { type: "string", description: "Updated title" },
          summary: { type: "string", description: "Updated summary" },
          category: { type: "string", enum: ["person", "project", "idea", "admin", "insight"] },
          people: { type: "array", items: { type: "string" }, description: "Updated people list" },
          topics: { type: "array", items: { type: "string" }, description: "Updated topics list" },
          action_items: { type: "array", items: { type: "string" }, description: "Updated action items" },
          status: { type: "string", enum: ["active", "needs_review", "archived"] },
        },
        required: ["id"],
      },
    },
    {
      name: "archive_thought",
      description: "Archive a completed thought. Archived thoughts are hidden from default searches but can be found using status: 'archived' or 'all' in semantic_search or list_recent.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "The UUID of the thought to archive" },
        },
        required: ["id"],
      },
    },
    {
      name: "delete_thought",
      description: "Permanently delete a thought from your brain by its ID.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "The UUID of the thought to delete" },
        },
        required: ["id"],
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
    {
      name: "get_thought",
      description: "Fetch a single thought by ID, including its full raw text exactly as captured.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "The UUID of the thought to retrieve" },
        },
        required: ["id"],
      },
    },
    {
      name: "meeting_prep",
      description: "Pull all relevant context from your brain to prepare for a meeting. Combines semantic search on the meeting topic with people-specific lookups. Returns raw context; Claude synthesizes the prep brief.",
      inputSchema: {
        type: "object",
        properties: {
          meeting: { type: "string", description: "Description of the meeting — topic, purpose, or freeform (e.g. '1:1 with Mike about Q3 pricing')" },
          people: {
            type: "array",
            items: { type: "string" },
            description: "Names of people in the meeting to look up explicitly (optional but improves recall)",
          },
        },
        required: ["meeting"],
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
      case "update_thought":
        text = await updateThought(a as Parameters<typeof updateThought>[0]);
        break;
      case "archive_thought":
        text = await archiveThought(a as Parameters<typeof archiveThought>[0]);
        break;
      case "delete_thought":
        text = await deleteThought(a as Parameters<typeof deleteThought>[0]);
        break;
      case "get_thought":
        text = await getThought(a as Parameters<typeof getThought>[0]);
        break;
      case "get_context":
        text = await getContext(a as Parameters<typeof getContext>[0]);
        break;
      case "meeting_prep":
        text = await meetingPrep(a as Parameters<typeof meetingPrep>[0]);
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
