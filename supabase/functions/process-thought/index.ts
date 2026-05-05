import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY")!;
const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const CONFIDENCE_THRESHOLD = 0.7;
const EMBEDDING_MODEL = "text-embedding-3-small";
const HAIKU_MODEL = "claude-haiku-4-5-20251001";
const SONNET_MODEL = "claude-sonnet-4-6";

const URL_REGEX = /https?:\/\/[^\s<>"{}|\\^`[\]]+/g;
function extractUrls(text: string): string[] {
  return [...text.matchAll(URL_REGEX)].map(m => m[0]);
}

function normalizeText(text: string): string {
  return text.toLowerCase().trim().replace(/\s+/g, " ");
}

async function hashText(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

interface ClassificationResult {
  category: "person" | "project" | "idea" | "admin" | "insight";
  title: string;
  summary: string;
  people: string[];
  topics: string[];
  action_items: string[];
  confidence: number;
}

const CLASSIFICATION_PROMPT = `You are a personal knowledge classification engine.

Classify the following thought and return ONLY valid JSON matching this exact schema:
{
  "category": "person|project|idea|admin|insight",
  "title": "Short descriptive title (max 8 words)",
  "summary": "One sentence summary",
  "people": ["Name1", "Name2"],
  "topics": ["topic1", "topic2"],
  "action_items": ["Specific next action if any"],
  "confidence": 0.85
}

Categories:
- person: thoughts about specific individuals (conversations, impressions, follow-ups)
- project: work or personal projects, tasks, deliverables
- idea: concepts, hypotheses, creative thoughts, observations
- admin: logistics, scheduling, housekeeping, references
- insight: patterns noticed, lessons learned, realizations

Rules:
- confidence is your certainty about the category (0.0-1.0)
- people is empty array if no specific people mentioned
- action_items is empty array if no clear next action
- Return ONLY JSON, no explanation, no markdown`;

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: text,
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`OpenAI embedding failed: ${err}`);
  }

  const data = await response.json();
  return data.data[0].embedding;
}

async function classify(
  text: string,
  model: string,
): Promise<ClassificationResult> {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: `${CLASSIFICATION_PROMPT}\n\nThought to classify:\n${text}`,
        },
      ],
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Anthropic classification failed (${model}): ${err}`);
  }

  const data = await response.json();
  const raw = data.content[0].text.trim();

  try {
    const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "").trim();
    return JSON.parse(cleaned) as ClassificationResult;
  } catch {
    throw new Error(`Classification returned invalid JSON from ${model}: ${raw}`);
  }
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

  let body: { text: string; source?: string; id?: string; is_external?: boolean };
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const { text, source = "api", id, is_external = false } = body;

  if (!text || typeof text !== "string" || text.trim().length === 0) {
    return new Response(JSON.stringify({ error: "text field is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const trimmed = text.trim();
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const contentHash = await hashText(normalizeText(trimmed));

    if (id) {
      // Update mode — re-embed and re-classify, preserve status
      const { data: existing, error: fetchError } = await supabase
        .from("thoughts")
        .select("id, status")
        .eq("id", id)
        .single();
      if (fetchError || !existing) {
        return new Response(JSON.stringify({ error: `No thought found with ID ${id}` }), {
          status: 404,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }

      const { data: duplicate } = await supabase
        .from("thoughts")
        .select("id, title, category")
        .eq("content_hash", contentHash)
        .neq("id", id)
        .maybeSingle();
      if (duplicate) {
        return new Response(
          JSON.stringify({ ok: false, duplicate: true, id: duplicate.id, title: duplicate.title, category: duplicate.category }),
          { status: 200, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } },
        );
      }

      const [embedding, haikusResult] = await Promise.all([
        generateEmbedding(trimmed),
        classify(trimmed, HAIKU_MODEL),
      ]);

      let classification = haikusResult;
      let model_used = HAIKU_MODEL;

      if (classification.confidence < CONFIDENCE_THRESHOLD) {
        console.log(`Low confidence (${classification.confidence}) — escalating to Sonnet`);
        classification = await classify(trimmed, SONNET_MODEL);
        model_used = SONNET_MODEL;
      }

      const urls = extractUrls(trimmed);

      const updatePayload: Record<string, unknown> = {
        raw_text: trimmed,
        embedding,
        category: classification.category,
        title: classification.title,
        summary: classification.summary,
        people: classification.people,
        topics: classification.topics,
        action_items: classification.action_items,
        urls,
        confidence: classification.confidence,
        content_hash: contentHash,
      };
      if (body.is_external !== undefined) updatePayload.is_external = is_external;

      const { data, error } = await supabase
        .from("thoughts")
        .update(updatePayload)
        .eq("id", id)
        .select("id, title, category, confidence, status")
        .single();

      if (error) throw new Error(`Database update failed: ${error.message}`);
      if (!data) {
        return new Response(JSON.stringify({ error: `No thought found with ID ${id}` }), {
          status: 404,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }

      return new Response(
        JSON.stringify({ ok: true, updated: true, id: data.id, title: data.title, category: data.category, confidence: data.confidence, status: data.status, model_used }),
        { status: 200, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } },
      );
    }

    // Insert mode — duplicate check before any LLM calls
    const { data: existingDup } = await supabase
      .from("thoughts")
      .select("id, title, category")
      .eq("content_hash", contentHash)
      .maybeSingle();
    if (existingDup) {
      return new Response(
        JSON.stringify({ ok: false, duplicate: true, id: existingDup.id, title: existingDup.title, category: existingDup.category }),
        { status: 200, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } },
      );
    }

    // Run embedding and Haiku classification in parallel
    const [embedding, haikusResult] = await Promise.all([
      generateEmbedding(trimmed),
      classify(trimmed, HAIKU_MODEL),
    ]);

    let classification = haikusResult;
    let model_used = HAIKU_MODEL;

    // Escalate to Sonnet if confidence is too low
    if (classification.confidence < CONFIDENCE_THRESHOLD) {
      console.log(
        `Low confidence (${classification.confidence}) — escalating to Sonnet`,
      );
      classification = await classify(trimmed, SONNET_MODEL);
      model_used = SONNET_MODEL;
    }

    // Determine status based on final confidence
    const status = classification.confidence >= CONFIDENCE_THRESHOLD
      ? "active"
      : "needs_review";

    const urls = extractUrls(trimmed);

    const { data, error } = await supabase
      .from("thoughts")
      .insert({
        raw_text: trimmed,
        embedding,
        category: classification.category,
        title: classification.title,
        summary: classification.summary,
        people: classification.people,
        topics: classification.topics,
        action_items: classification.action_items,
        urls,
        confidence: classification.confidence,
        source,
        status,
        content_hash: contentHash,
        is_external,
      })
      .select("id, title, category, confidence, status")
      .single();

    if (error) {
      throw new Error(`Database insert failed: ${error.message}`);
    }

    return new Response(
      JSON.stringify({
        ok: true,
        id: data.id,
        title: data.title,
        category: data.category,
        confidence: data.confidence,
        status: data.status,
        model_used,
      }),
      {
        status: 201,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      },
    );
  } catch (err) {
    console.error("process-thought error:", err);
    return new Response(
      JSON.stringify({ error: (err as Error).message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
});
