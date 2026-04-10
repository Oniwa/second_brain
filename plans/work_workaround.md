# Work Computer Semantic Search Workaround

## Problem
On work computer, thought capture works but semantic search fails. Suspected cause: corporate firewall blocks outbound calls to `api.openai.com`. Capture works because it goes through the Supabase Edge Function (`process-thought`) which calls OpenAI server-side. Search fails because `brain.py` calls OpenAI directly to generate the query embedding.

## Diagnosis
Run on work computer to confirm:
```bash
curl -I https://api.openai.com
curl -I https://zkdblldjdgadqukpttwl.supabase.co
```
Expected: first times out, second responds.

## Solution: Proxy Embedding Through Edge Function

Add a `generate-embedding` Supabase Edge Function. `brain.py` calls it instead of OpenAI directly. Work machine only needs to reach `supabase.co`, which it already can. Same semantic quality everywhere, no dual code paths.

### Step 1 — `supabase/functions/generate-embedding/index.ts` (NEW)

Simple passthrough — accepts text, calls OpenAI, returns the vector:

```typescript
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY")!;

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

  const { text } = await req.json();
  if (!text) {
    return new Response(JSON.stringify({ error: "text required" }), { status: 400 });
  }

  const res = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: "text-embedding-3-small", input: text }),
  });

  const data = await res.json();
  return new Response(JSON.stringify({ embedding: data.data[0].embedding }), {
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
});
```

Deploy: `supabase functions deploy generate-embedding`

### Step 2 — `scripts/brain.py` (MODIFY)

Replace the direct OpenAI call in `search()` with a call to the Edge Function:

**Current (lines 101-112):**
```python
embed_url = "https://api.openai.com/v1/embeddings"
embed_headers = {
    "Authorization": f"Bearer {env['OPENAI_API_KEY']}",
    "Content-Type": "application/json",
}
embed_result = api_request(
    embed_url,
    method="POST",
    body={"model": "text-embedding-3-small", "input": query},
    headers=embed_headers,
)
embedding = embed_result["data"][0]["embedding"]
```

**Replace with:**
```python
embed_url = f"{env['SUPABASE_URL']}/functions/v1/generate-embedding"
embed_headers = {
    "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
    "Content-Type": "application/json",
}
embed_result = api_request(
    embed_url,
    method="POST",
    body={"text": query},
    headers=embed_headers,
)
embedding = embed_result["embedding"]
```

`OPENAI_API_KEY` no longer needed in `.env` on work machine for search to work.

## Execution Order

1. Confirm diagnosis with `curl` commands above
2. Create and deploy `generate-embedding` Edge Function
3. Update `brain.py` `search()` function
4. Test on work machine: `python3 scripts/brain.py --search "test query"`

## Notes
- Adds one extra network hop (work → Supabase → OpenAI) but latency is negligible
- No change to search quality — same model, same vectors
- `mcp/src/server.ts` calls OpenAI directly too — if MCP is used on work machine, it would need the same treatment. Defer until needed.
