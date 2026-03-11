#!/usr/bin/env python3
"""
remind.py — Check your second brain for upcoming birthdays, follow-ups, and anniversaries.

Queries thoughts tagged with topics: birthday, anniversary, follow-up, reminder.
Sends them to Claude Haiku to identify what's due within the lookahead window.
Sends a Discord DM if anything is due. Silent if nothing is upcoming.

Capture conventions:
  "Mike's birthday is March 15"            → topics: [birthday], people: [Mike]
  "Follow up with Sarah about X by Mar 20" → topics: [follow-up], people: [Sarah]
  "Wedding anniversary April 3"            → topics: [anniversary]

Usage:
  python scripts/remind.py              # check next 7 days (default)
  python scripts/remind.py --days 3     # tighter lookahead
  python scripts/remind.py --test       # print without sending Discord DM
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HAIKU_MODEL = "claude-haiku-4-5-20251001"
REMINDER_TOPICS = ["birthday", "anniversary", "follow-up", "followup", "reminder"]

REMIND_PROMPT = """You are a personal assistant checking someone's notes for upcoming dates.

Today is {today}. The lookahead window is {days} day(s) — flag anything due today through {end_date}.

Below are notes from their second brain tagged as birthdays, anniversaries, follow-ups, or reminders.
For each one, determine if it falls within the lookahead window.

Rules:
- For recurring dates (birthdays, anniversaries): check if this year's occurrence is within the window.
- For one-time follow-ups: check if the specified date is within the window.
- If no specific date can be found in the note, skip it.
- If the date has already passed this year (for recurring) or overall (for one-time), skip it.

Return ONLY the items that are due within the window, using this format:

🎂 [Birthday] Mike — March 15 (in 3 days)
📅 [Follow-up] Sarah re: contract — March 20 (today)
💍 [Anniversary] Wedding — April 3 (in 7 days)

If nothing is due within the window, reply with exactly: NONE"""


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
        "ANTHROPIC_API_KEY", "DISCORD_BOT_TOKEN", "DISCORD_USER_ID",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def fetch_reminder_thoughts(supabase_url: str, key: str) -> list:
    """Fetch all active thoughts tagged with any reminder-related topic."""
    results = []
    seen = set()

    for topic in REMINDER_TOPICS:
        params = urllib.parse.urlencode({
            "select": "id,title,summary,raw_text,people,topics,action_items,created_at",
            "status": "eq.active",
            "people": f"cs.{{{topic}}}",  # won't match but topics filter below handles it
        })
        # Use topics contains filter
        url = (
            f"{supabase_url}/rest/v1/thoughts"
            f"?select=id,title,summary,raw_text,people,topics,action_items,created_at"
            f"&status=eq.active"
            f"&topics=cs.{{{urllib.parse.quote(topic)}}}"
            f"&order=created_at.asc"
        )
        req = urllib.request.Request(url, headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                for t in json.loads(resp.read().decode("utf-8")):
                    if t["id"] not in seen:
                        seen.add(t["id"])
                        results.append(t)
        except urllib.error.HTTPError:
            continue

    return results


def format_for_haiku(thoughts: list) -> str:
    lines = []
    for t in thoughts:
        parts = [f"- {t.get('title', 'Untitled')}"]
        if t.get("summary"):
            parts.append(f"  Note: {t['summary']}")
        if t.get("raw_text"):
            parts.append(f"  Raw: {t['raw_text']}")
        if t.get("people"):
            parts.append(f"  People: {', '.join(t['people'])}")
        if t.get("topics"):
            parts.append(f"  Topics: {', '.join(t['topics'])}")
        if t.get("action_items"):
            parts.append(f"  Actions: {' | '.join(t['action_items'])}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


def call_haiku(thoughts: list, days: int, anthropic_key: str) -> str:
    today = date.today()
    from datetime import timedelta
    end_date = today + timedelta(days=days)

    prompt = REMIND_PROMPT.format(
        today=today.strftime("%B %d, %Y"),
        days=days,
        end_date=end_date.strftime("%B %d, %Y"),
    )
    content = f"{prompt}\n\n---\nNOTES:\n\n{format_for_haiku(thoughts)}"

    data = json.dumps({
        "model": HAIKU_MODEL,
        "max_tokens": 512,
        "messages": [{"role": "user", "content": content}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        print(f"Haiku error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


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

    urllib.request.urlopen(
        urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            data=json.dumps({"content": message}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Second Brain reminder checker")
    parser.add_argument("--days", type=int, default=7,
                        help="Lookahead window in days (default: 7)")
    parser.add_argument("--test", action="store_true",
                        help="Print output without sending Discord DM")
    args = parser.parse_args()

    env = load_env()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "ANTHROPIC_API_KEY") if not env.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    print(f"Checking reminders for the next {args.days} day(s)...")
    thoughts = fetch_reminder_thoughts(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])

    if not thoughts:
        print("No reminder thoughts found (nothing tagged birthday, anniversary, follow-up, or reminder).")
        return

    print(f"Found {len(thoughts)} reminder thought(s) — checking dates with Haiku...")
    result = call_haiku(thoughts, args.days, env["ANTHROPIC_API_KEY"])

    if result.strip().upper() == "NONE":
        print(f"Nothing due in the next {args.days} day(s).")
        return

    message = f"⏰ **Upcoming reminders ({args.days}-day window)**\n\n{result}"

    print("\n" + "=" * 50)
    print(message)
    print("=" * 50)

    if args.test:
        print("\n[TEST MODE] Not sent.")
        return

    if not env.get("DISCORD_BOT_TOKEN") or not env.get("DISCORD_USER_ID"):
        print("DISCORD_BOT_TOKEN or DISCORD_USER_ID not set — skipping Discord DM.", file=sys.stderr)
        return

    try:
        send_discord_dm(env["DISCORD_BOT_TOKEN"], env["DISCORD_USER_ID"], message)
        print("✓ Discord DM sent")
    except Exception as e:
        print(f"✗ Discord DM failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
