#!/usr/bin/env python3
"""
migrate_claude.py — Import Claude conversation export into Second Brain.

Usage:
  python3 scripts/migrate_claude.py path/to/data-*.zip
  python3 scripts/migrate_claude.py path/to/data-*.zip --dry-run   # preview only
  python3 scripts/migrate_claude.py path/to/data-*.zip --verbose   # show Haiku reasoning

What it does:
  1. Reads conversations.json + memories.json from the export zip
  2. For each conversation, extracts your (human) messages
  3. Asks Claude Haiku: "Is there anything worth remembering long-term?"
  4. If yes, checks semantic similarity against existing thoughts (skips if >90% match)
  5. Imports via process-thought Edge Function (same pipeline as normal captures)
  6. Tags source as "claude-export" and stores conversation UUID to prevent re-import

Deduplication:
  - Skips conversations already imported (by UUID stored in thoughts.raw_text)
  - Skips thoughts that semantically match existing ones (cosine similarity > 0.90)
  - Safe to re-run at any time
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

SIMILARITY_THRESHOLD = 0.90  # skip if existing thought is this similar

# Conversations to explicitly skip (not personally relevant or already captured)
SKIP_CONVERSATION_UUIDS = {
    "a7b4a365-99b9-4e08-94d1-e4751d97af6d",  # Learning to drive from Kansas handbook (friend's kid)
    "2eaec120-c0f9-4009-a248-27688d22b186",  # Kansas driver's exam preparation guide (friend's kid)
    "467a7cd4-7fbb-4488-b165-d35110824e8c",  # The Giver: book and movie differences (duplicate)
    "f020eb90-9eef-4433-a692-1dd8d6c0ac2a",  # The Giver practice quiz (duplicate)
}
HAIKU_MODEL = "claude-haiku-4-5-20251001"

EXTRACTION_PROMPT = """\
You are reviewing a conversation between a user and Claude AI to extract anything worth \
storing in a personal second brain (a long-term knowledge system).

Look specifically for:
- Decisions the user made
- Personal facts, goals, or preferences the user shared
- Action items or commitments the user mentioned
- Insights or ideas the user expressed or clearly found valuable
- Projects, interests, or plans the user described

Ignore:
- Questions answered by Claude (it's the user's brain, not Claude's)
- Debugging sessions or one-off technical lookups
- Small talk or meta-conversation about Claude itself
- Content that would only make sense in context of that conversation

The conversation title is: {title}

The user's messages (in order):
{messages}

Respond in JSON only, no markdown fences. Use this format:
{{
  "worth_importing": true or false,
  "thought": "A single clear thought to capture (2-4 sentences max). Write it as a \
first-person note, e.g. 'I decided...', 'I want to...', 'I learned...'. \
Omit if worth_importing is false.",
  "reason": "One sentence explaining your decision."
}}"""


def load_env() -> dict:
    env_path = PROJECT_ROOT / ".env"
    env = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    for key in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def extract_text(content_blocks) -> str:
    """Extract plain text from Claude's content block format."""
    if isinstance(content_blocks, str):
        return content_blocks
    parts = []
    for block in content_blocks or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts).strip()


def get_already_imported(supabase_url: str, service_role_key: str) -> set:
    """Return set of conversation UUIDs already imported."""
    url = (
        f"{supabase_url}/rest/v1/thoughts"
        f"?select=raw_text&source=eq.claude-export"
    )
    req = urllib.request.Request(
        url,
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        rows = json.loads(resp.read().decode("utf-8"))

    imported = set()
    for row in rows:
        raw = row.get("raw_text", "")
        # UUID is stored at end of raw_text as "[conv:UUID]"
        if "[conv:" in raw:
            uuid = raw.split("[conv:")[-1].rstrip("]")
            imported.add(uuid)
    return imported


def generate_embedding(text: str, openai_api_key: str) -> list:
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps({"model": "text-embedding-3-small", "input": text}).encode(),
        headers={
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["data"][0]["embedding"]


def check_similarity(embedding: list, supabase_url: str, service_role_key: str) -> float:
    """Return highest similarity score against existing active thoughts."""
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/rpc/semantic_search",
        data=json.dumps({
            "query_embedding": embedding,
            "match_limit": 1,
            "filter_category": None,
            "filter_status": "active",
        }).encode(),
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        results = json.loads(resp.read().decode("utf-8"))
    if not results:
        return 0.0
    return float(results[0].get("similarity", 0.0))


def ask_haiku(title: str, human_messages: list[str], anthropic_api_key: str) -> dict:
    """Ask Haiku whether the conversation is worth importing."""
    messages_text = "\n\n".join(f"[{i+1}] {m}" for i, m in enumerate(human_messages))
    prompt = EXTRACTION_PROMPT.format(title=title, messages=messages_text)

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": HAIKU_MODEL,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        }).encode(),
        headers={
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    raw = data["content"][0]["text"].strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    # Extract just the first JSON object (handles trailing text)
    brace_depth = 0
    end = 0
    for i, ch in enumerate(raw):
        if ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0:
                end = i + 1
                break
    return json.loads(raw[:end] if end else raw)


def capture_thought(text: str, supabase_url: str, service_role_key: str) -> dict:
    """Send thought through process-thought Edge Function."""
    req = urllib.request.Request(
        f"{supabase_url}/functions/v1/process-thought",
        data=json.dumps({"text": text, "source": "claude-export"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {service_role_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def migrate_memories(memories: list, env: dict, dry_run: bool, verbose: bool) -> int:
    """Import the Claude memory block as a single thought."""
    if not memories:
        return 0

    mem_text = memories[0].get("conversations_memory", "").strip()
    if not mem_text:
        return 0

    print("\n── Claude Memory Block ──")
    thought_text = (
        f"Claude's accumulated memory about me (imported from claude.ai export):\n\n"
        f"{mem_text}\n\n[conv:claude-memory]"
    )

    if dry_run:
        print("  [DRY RUN] Would import Claude memory block")
        if verbose:
            print(f"  Preview: {mem_text[:300]}...")
        return 1

    result = capture_thought(thought_text, env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
    if result.get("ok"):
        print(f"  ✓ Imported: {result['title']}")
        return 1
    else:
        print(f"  ✗ Failed: {result.get('error', 'unknown')}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Migrate Claude export to Second Brain")
    parser.add_argument("zip_file", help="Path to Claude export zip file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without importing anything")
    parser.add_argument("--verbose", action="store_true",
                        help="Show Haiku's reasoning for each decision")
    args = parser.parse_args()

    zip_path = Path(args.zip_file)
    if not zip_path.exists():
        print(f"Error: {zip_path} not found", file=sys.stderr)
        sys.exit(1)

    env = load_env()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
                            "OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not env.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Read export
    with zipfile.ZipFile(zip_path) as zf:
        convos = json.loads(zf.read("conversations.json"))
        memories = json.loads(zf.read("memories.json")) if "memories.json" in zf.namelist() else []

    print(f"Export contains: {len(convos)} conversations, {len(memories)} memory block(s)")

    if args.dry_run:
        print("DRY RUN MODE — nothing will be imported\n")

    # Get already-imported conversation UUIDs
    already_imported = set()
    if not args.dry_run:
        print("Checking for already-imported conversations...")
        already_imported = get_already_imported(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
        if already_imported:
            print(f"  {len(already_imported)} conversation(s) already imported — will skip")

    imported = 0
    skipped_already = 0
    skipped_haiku = 0
    skipped_dupe = 0
    errors = 0

    # Import memory block first
    imported += migrate_memories(memories, env, args.dry_run, args.verbose)

    print(f"\n── Processing {len(convos)} conversations ──\n")

    for convo in convos:
        uuid = convo.get("uuid", "")
        title = convo.get("name") or "(untitled)"
        messages = convo.get("chat_messages", [])

        # Extract human messages only
        human_msgs = []
        for m in messages:
            if m.get("sender") == "human":
                text = extract_text(m.get("content") or m.get("text", ""))
                if text:
                    human_msgs.append(text)

        if not human_msgs:
            print(f"  SKIP  {title[:55]} — no human messages")
            skipped_haiku += 1
            continue

        # Skip explicitly excluded conversations
        if uuid in SKIP_CONVERSATION_UUIDS:
            print(f"  SKIP  {title[:55]} — excluded")
            skipped_already += 1
            continue

        # Skip already imported
        if uuid in already_imported:
            print(f"  SKIP  {title[:55]} — already imported")
            skipped_already += 1
            continue

        print(f"  CHECK {title[:55]}")

        # Ask Haiku
        try:
            result = ask_haiku(title, human_msgs, env["ANTHROPIC_API_KEY"])
        except Exception as e:
            print(f"    ✗ Haiku error: {e}")
            errors += 1
            time.sleep(1)
            continue

        if args.verbose:
            print(f"    Haiku: {result.get('reason', '')}")

        if not result.get("worth_importing"):
            print(f"    → Skip: {result.get('reason', 'not worth importing')}")
            skipped_haiku += 1
            continue

        thought_text = result.get("thought", "")
        if not thought_text:
            skipped_haiku += 1
            continue

        # Append conversation UUID for dedup tracking
        full_text = f"{thought_text}\n\n[conv:{uuid}]"

        if args.dry_run:
            print(f"    → [DRY RUN] Would import: {thought_text[:120]}")
            imported += 1
            continue

        # Check semantic similarity
        try:
            embedding = generate_embedding(thought_text, env["OPENAI_API_KEY"])
            similarity = check_similarity(embedding, env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
        except Exception as e:
            print(f"    ✗ Similarity check error: {e}")
            errors += 1
            continue

        if similarity >= SIMILARITY_THRESHOLD:
            print(f"    → Skip: too similar to existing thought ({similarity*100:.0f}% match)")
            skipped_dupe += 1
            continue

        # Import
        try:
            capture_result = capture_thought(full_text, env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
            if capture_result.get("ok"):
                print(f"    ✓ Imported: {capture_result['title']}")
                imported += 1
            else:
                print(f"    ✗ Import failed: {capture_result.get('error', 'unknown')}")
                errors += 1
        except Exception as e:
            print(f"    ✗ Import error: {e}")
            errors += 1

        # Brief pause to avoid rate limits
        time.sleep(0.5)

    print(f"""
── Migration complete ──
  Imported:          {imported}
  Already imported:  {skipped_already}
  Skipped by Haiku:  {skipped_haiku}
  Skipped (dupe):    {skipped_dupe}
  Errors:            {errors}
""")


if __name__ == "__main__":
    main()
