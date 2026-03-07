#!/usr/bin/env python3
"""
nudge.py — Sends a Discord DM prompt if no thoughts have been captured recently.

Run daily via cron. Stays silent if you've captured recently.

Usage:
  python3 scripts/nudge.py            # send nudge if overdue (default: 2 days)
  python3 scripts/nudge.py --days 3   # custom threshold
  python3 scripts/nudge.py --test     # print nudge without sending
"""

import argparse
import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

PROMPTS = [
    # People / relationships
    "Is there anyone you need to follow up with?",
    "Who did you talk to recently that's worth remembering?",
    "Is there someone you've been meaning to reach out to?",
    # Projects
    "What's one thing that's been sitting on your to-do list too long?",
    "What project have you been avoiding — and why?",
    "What's the next small step on your most important project?",
    # Ideas
    "What's something you read, watched, or heard recently that stuck with you?",
    "What's a problem you've been turning over in your head?",
    "What's an idea you haven't written down yet?",
    # Health / habits
    "Did you do anything this week toward your health goals?",
    "What's one habit you want to build or break?",
    "How are you feeling physically and mentally right now?",
    # General
    "What's on your mind right now?",
    "What do you want to remember about today?",
    "What's one thing you're grateful for or excited about?",
    "What decision have you been putting off?",
    "What's something small that would make next week better?",
]


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
    for key in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "DISCORD_BOT_TOKEN", "DISCORD_USER_ID"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def days_since_last_capture(supabase_url: str, service_role_key: str) -> float:
    url = (
        f"{supabase_url}/rest/v1/thoughts"
        f"?select=created_at&order=created_at.desc&limit=1"
    )
    req = urllib.request.Request(
        url,
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        results = json.loads(resp.read().decode("utf-8"))

    if not results:
        return float("inf")  # No thoughts at all — definitely nudge

    last = datetime.fromisoformat(results[0]["created_at"].replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - last
    return delta.total_seconds() / 86400


def send_discord_dm(bot_token: str, user_id: str, message: str) -> None:
    headers = {
        "User-Agent": "DiscordBot (https://github.com/Oniwa/second_brain, 1.0)",
        "Content-Type": "application/json",
        "Authorization": f"Bot {bot_token}",
    }

    # Create DM channel
    req = urllib.request.Request(
        "https://discord.com/api/v10/users/@me/channels",
        data=json.dumps({"recipient_id": user_id}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        channel_id = json.loads(resp.read().decode("utf-8"))["id"]

    # Send message
    urllib.request.urlopen(
        urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            data=json.dumps({"content": message}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Second Brain nudge system")
    parser.add_argument("--days", type=float, default=2.0,
                        help="Days of silence before nudging (default: 2)")
    parser.add_argument("--test", action="store_true",
                        help="Print nudge message without sending")
    args = parser.parse_args()

    env = load_env()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not env.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    gap = days_since_last_capture(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])

    if gap < args.days:
        print(f"Last capture was {gap:.1f} days ago — no nudge needed.")
        return

    prompt = random.choice(PROMPTS)
    days_str = "a while" if gap == float("inf") else f"{gap:.0f} day{'s' if gap >= 2 else ''}"
    message = (
        f"🧠 Your second brain hasn't heard from you in {days_str}.\n\n"
        f"**Here's a prompt to get started:**\n> {prompt}\n\n"
        f"Reply in #sb-inbox or use the CLI: `python3 scripts/brain.py \"your thought\"`"
    )

    print(f"Gap: {gap:.1f} days (threshold: {args.days}) — sending nudge.")
    print(f"Prompt: {prompt}")

    if args.test:
        print("\n[TEST MODE] Message not sent.")
        print(f"\n{message}")
        return

    if not env.get("DISCORD_BOT_TOKEN") or not env.get("DISCORD_USER_ID"):
        print("DISCORD_BOT_TOKEN or DISCORD_USER_ID not set.", file=sys.stderr)
        sys.exit(1)

    send_discord_dm(env["DISCORD_BOT_TOKEN"], env["DISCORD_USER_ID"], message)
    print("Nudge sent.")


if __name__ == "__main__":
    main()
