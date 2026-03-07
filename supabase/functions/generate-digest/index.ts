import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const SONNET_MODEL = "claude-sonnet-4-6";

const DAILY_PROMPT = `You are a personal assistant generating a brief daily digest from someone's second brain.

Given the list of their active thoughts below, produce a digest with exactly this structure:

**Daily Digest**

📋 Top 3 actions:
• [most urgent action item]
• [second action item]
• [third action item]

⏳ One thing that's been sitting:
[A thought captured more than 2 days ago that hasn't been acted on]

Keep the entire digest under 150 words. Be specific — use the actual titles and details from their thoughts, not generic advice. If there are fewer than 3 action items, list what exists.`;

const WEEKLY_PROMPT = `You are a personal assistant generating a weekly digest from someone's second brain.

Given the list of their active thoughts below, produce a digest with exactly this structure:

**Weekly Digest**

📋 Top 3 actions:
• [most important action item]
• [second action item]
• [third action item]

⏳ One thing that's been sitting:
[A thought that has been sitting the longest without action]

💡 Pattern noticed:
[One honest observation about how they've been spending their mental energy this week]

📚 Reading list reminder:
[List their queued books, or note if none are captured]

Keep the entire digest under 250 words. Be specific and direct — use actual titles and names from their data.`;

const WEEKLY_REVIEW_PROMPT = `You are a personal assistant generating a thoughtful weekly review from someone's second brain.
This is meant to be read slowly on a Sunday morning as a reflective practice — not scanned quickly.

You will receive two lists: ACTIVE THOUGHTS (what's currently on their mind) and ARCHIVED THIS WEEK (what they completed or put to rest).

Produce a review with exactly this structure:

**Weekly Review**

✅ Completed this week:
[List each archived thought by title, 1-2 words on what it was. If none, say "Nothing archived this week — consider if anything can be closed out."]

🧠 What's been on your mind:
[2-3 sentences describing the dominant themes across their active thoughts. Be specific — name the actual topics and projects.]

🔍 Open loops to notice:
[2-3 thoughts that have been sitting without action the longest. Name them explicitly.]

🎯 One thing to focus on next week:
[Pick the single most important active thought and make a case for why it deserves attention.]

💬 Honest reflection:
[One candid observation — something they might be avoiding, a pattern in their captures, or a tension between two things they care about. Be direct but kind.]

Keep the entire review under 500 words. Use actual titles and names from the data. Write in second person ("you").`;

interface Thought {
  title: string;
  summary: string;
  category: string;
  action_items: string[];
  people: string[];
  topics: string[];
  created_at: string;
  source: string;
}

function formatThoughts(thoughts: Thought[]): string {
  return thoughts.map((t, i) => {
    const age = Math.floor(
      (Date.now() - new Date(t.created_at).getTime()) / (1000 * 60 * 60 * 24)
    );
    const lines = [
      `${i + 1}. [${t.category}] ${t.title}`,
      `   Summary: ${t.summary}`,
      t.action_items.length ? `   Actions: ${t.action_items.join(" | ")}` : "",
      t.people.length ? `   People: ${t.people.join(", ")}` : "",
      t.topics.length ? `   Topics: ${t.topics.join(", ")}` : "",
      `   Captured: ${age} day(s) ago via ${t.source}`,
    ];
    return lines.filter(Boolean).join("\n");
  }).join("\n\n");
}

async function callClaude(prompt: string, thoughts: Thought[], archivedThoughts?: Thought[]): Promise<string> {
  let content = `${prompt}\n\n---\nACTIVE THOUGHTS:\n\n${formatThoughts(thoughts)}`;
  if (archivedThoughts && archivedThoughts.length > 0) {
    content += `\n\n---\nARCHIVED THIS WEEK:\n\n${formatThoughts(archivedThoughts)}`;
  }

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: SONNET_MODEL,
      max_tokens: 1024,
      messages: [{ role: "user", content }],
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Claude API error: ${err}`);
  }

  const data = await response.json();
  return data.content[0].text.trim();
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  let body: { type: "daily" | "weekly" | "weekly-review" };
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const { type } = body;
  if (type !== "daily" && type !== "weekly" && type !== "weekly-review") {
    return new Response(JSON.stringify({ error: "type must be 'daily', 'weekly', or 'weekly-review'" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

  // Query active thoughts — last 7 days for daily, 30 for weekly/weekly-review
  const days = type === "daily" ? 7 : 30;
  const since = new Date();
  since.setDate(since.getDate() - days);

  const { data: thoughts, error } = await supabase
    .from("thoughts")
    .select("title, summary, category, action_items, people, topics, created_at, source")
    .eq("status", "active")
    .gte("created_at", since.toISOString())
    .order("created_at", { ascending: false });

  if (error) {
    return new Response(JSON.stringify({ error: `DB query failed: ${error.message}` }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!thoughts || thoughts.length === 0) {
    return new Response(
      JSON.stringify({ digest: `No active thoughts in the last ${days} days.` }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }

  // For weekly review, also fetch thoughts archived in the last 7 days
  let archivedThoughts: Thought[] | undefined;
  if (type === "weekly-review") {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const { data: archived } = await supabase
      .from("thoughts")
      .select("title, summary, category, action_items, people, topics, created_at, source")
      .eq("status", "archived")
      .gte("updated_at", weekAgo.toISOString())
      .order("updated_at", { ascending: false });
    archivedThoughts = (archived ?? []) as Thought[];
  }

  try {
    const prompt = type === "daily" ? DAILY_PROMPT : type === "weekly" ? WEEKLY_PROMPT : WEEKLY_REVIEW_PROMPT;
    const digest = await callClaude(prompt, thoughts as Thought[], archivedThoughts);
    const subject = type === "daily"
      ? `🧠 Second Brain — Daily Digest`
      : type === "weekly"
      ? `🧠 Second Brain — Weekly Digest`
      : `🧠 Second Brain — Weekly Review`;

    return new Response(
      JSON.stringify({ digest, subject, thought_count: thoughts.length }),
      {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: (err as Error).message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
