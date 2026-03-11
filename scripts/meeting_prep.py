#!/usr/bin/env python3
"""
meeting_prep.py — Pull context from your second brain to prepare for a meeting.

Usage:
  python scripts/meeting_prep.py "1:1 with Mike about Q3 pricing"
  python scripts/meeting_prep.py "relaunch planning" --people Mike Sarah
  python scripts/meeting_prep.py "IRM Thursday morning" --send
  python scripts/meeting_prep.py "standup" --test
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

HAIKU_MODEL = "claude-haiku-4-5-20251001"

PREP_PROMPT = """You are a personal assistant preparing someone for a meeting.
Below is raw context pulled from their second brain — thoughts, notes, and action items related to this meeting.

Synthesize this into a focused meeting prep brief using exactly this structure:

**Meeting Prep: {meeting}**

👥 What you know about the people:
{people_section}

📋 Relevant context:
• [2-4 most relevant thoughts, specific details only]

⚡ Open action items:
• [any open actions from the context — or "None captured" if empty]

❓ Questions worth asking:
• [1-3 questions suggested by gaps or unresolved threads in the context]

Be specific — use actual names, project names, and details from the data. Keep the entire brief under 300 words. If there's no relevant context, say so honestly."""


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
    for key in (
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "DISCORD_BOT_TOKEN", "DISCORD_USER_ID",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def api_post(url: str, body: dict, headers: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            msg = json.loads(raw).get("error") or raw
        except json.JSONDecodeError:
            msg = raw
        print(f"HTTP {e.code}: {msg}", file=sys.stderr)
        sys.exit(1)


def generate_embedding(text: str, openai_key: str) -> list:
    result = api_post(
        "https://api.openai.com/v1/embeddings",
        {"model": "text-embedding-3-small", "input": text},
        {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
    )
    return result["data"][0]["embedding"]


def semantic_search(embedding: list, supabase_url: str, key: str, limit: int = 15) -> list:
    result = api_post(
        f"{supabase_url}/rest/v1/rpc/semantic_search",
        {
            "query_embedding": embedding,
            "match_limit": limit,
            "filter_category": None,
            "filter_status": "active",
        },
        {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return result if isinstance(result, list) else []


def people_search(person: str, supabase_url: str, key: str) -> list:
    import urllib.parse
    params = urllib.parse.urlencode({
        "select": "id,title,summary,category,people,topics,action_items,source,created_at",
        "status": "eq.active",
        "people": f"cs.{{{person}}}",
        "order": "created_at.desc",
        "limit": "10",
    })
    url = f"{supabase_url}/rest/v1/thoughts?{params}"
    req = urllib.request.Request(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return []


def format_thought(t: dict) -> str:
    lines = [f"[{t.get('category', '?')}] {t.get('title', 'Untitled')}"]
    if t.get("summary"):
        lines.append(f"  Summary: {t['summary']}")
    if t.get("people"):
        lines.append(f"  People: {', '.join(t['people'])}")
    if t.get("topics"):
        lines.append(f"  Topics: {', '.join(t['topics'])}")
    if t.get("action_items"):
        lines.append(f"  Actions: {' | '.join(t['action_items'])}")
    lines.append(f"  Captured: {t.get('created_at', '')[:10]} · {t.get('source', 'unknown')}")
    return "\n".join(lines)


def call_haiku(meeting: str, people: list, thoughts: list, anthropic_key: str) -> str:
    context_text = "\n\n".join(format_thought(t) for t in thoughts)

    if people:
        people_section = "\n".join(f"• {p}" for p in people)
    else:
        people_section = "• (no people explicitly specified)"

    prompt = PREP_PROMPT.format(meeting=meeting, people_section=people_section)
    content = f"{prompt}\n\n---\nCONTEXT FROM BRAIN:\n\n{context_text}"

    result = api_post(
        "https://api.anthropic.com/v1/messages",
        {
            "model": HAIKU_MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": content}],
        },
        {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    return result["content"][0]["text"].strip()


def send_discord_dm(bot_token: str, user_id: str, message: str) -> None:
    headers = {
        "User-Agent": "DiscordBot (https://github.com/Oniwa/second_brain, 1.0)",
        "Content-Type": "application/json",
        "Authorization": f"Bot {bot_token}",
    }
    req = urllib.request.Request(
        "https://discord.com/api/v10/users/@me/channels",
        data=json.dumps({"recipient_id": user_id}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        channel_id = json.loads(resp.read().decode("utf-8"))["id"]

    chunks = [message[i:i + 1900] for i in range(0, len(message), 1900)]
    for chunk in chunks:
        urllib.request.urlopen(
            urllib.request.Request(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                data=json.dumps({"content": chunk}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Meeting prep from your second brain")
    parser.add_argument("meeting", help="Meeting description (e.g. '1:1 with Mike about pricing')")
    parser.add_argument("--people", nargs="+", metavar="NAME",
                        help="Names of people in the meeting for targeted lookup")
    parser.add_argument("--send", action="store_true",
                        help="Send the prep brief via Discord DM")
    parser.add_argument("--test", action="store_true",
                        help="Show raw search results without AI synthesis")
    args = parser.parse_args()

    env = load_env()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "OPENAI_API_KEY") if not env.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    people = args.people or []

    print(f"Searching brain for: {args.meeting}")
    if people:
        print(f"People: {', '.join(people)}")

    # Embed + semantic search
    embedding = generate_embedding(args.meeting, env["OPENAI_API_KEY"])
    sem_results = semantic_search(embedding, env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])

    # People keyword searches
    people_results = []
    for person in people:
        people_results.extend(people_search(person, env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]))

    # Merge, people matches first, deduplicate by id
    seen = set()
    merged = []
    for t in people_results + sem_results:
        tid = t.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            merged.append(t)

    print(f"Found {len(merged)} relevant thoughts\n")

    if not merged:
        print("Nothing captured about this meeting yet.")
        return

    if args.test:
        print("=== RAW RESULTS (test mode) ===\n")
        for t in merged:
            print(format_thought(t))
            print()
        return

    if not env.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — showing raw results instead.\n")
        for t in merged:
            print(format_thought(t))
            print()
        return

    print("Synthesizing prep brief...")
    brief = call_haiku(args.meeting, people, merged, env["ANTHROPIC_API_KEY"])

    print("\n" + "=" * 50)
    print(brief)
    print("=" * 50)

    if args.send:
        if env.get("DISCORD_BOT_TOKEN") and env.get("DISCORD_USER_ID"):
            try:
                send_discord_dm(env["DISCORD_BOT_TOKEN"], env["DISCORD_USER_ID"], brief)
                print("\n✓ Sent via Discord DM")
            except Exception as e:
                print(f"\n✗ Discord DM failed: {e}", file=sys.stderr)
        else:
            print("\nSkipping Discord (DISCORD_BOT_TOKEN or DISCORD_USER_ID not set)", file=sys.stderr)


if __name__ == "__main__":
    main()
