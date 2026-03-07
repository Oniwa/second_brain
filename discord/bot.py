#!/usr/bin/env python3
"""
Second Brain Discord Bot

Watches #sb-inbox and captures any message posted there to your brain.
Replies in-thread with a receipt showing title, category, and confidence.

Usage:
  pip install -r requirements.txt
  python bot.py
"""

import asyncio
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import discord

INBOX_CHANNEL = "sb-inbox"


def load_env() -> dict:
    """Load .env from the project root (parent of discord/)."""
    env_path = Path(__file__).parent.parent / ".env"
    env = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    for key in ("DISCORD_BOT_TOKEN", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def capture_thought(supabase_url: str, service_role_key: str, text: str) -> dict:
    """Call the process-thought Edge Function synchronously."""
    url = f"{supabase_url}/functions/v1/process-thought"
    body = json.dumps({"text": text, "source": "discord"}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {service_role_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return {"error": json.loads(raw).get("error", raw)}
        except json.JSONDecodeError:
            return {"error": raw}


class SecondBrainBot(discord.Client):
    def __init__(self, supabase_url: str, service_role_key: str):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.supabase_url = supabase_url
        self.service_role_key = service_role_key

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} — watching #{INBOX_CHANNEL}")

    async def on_message(self, message: discord.Message) -> None:
        # Ignore bots and messages outside #sb-inbox
        if message.author.bot:
            return
        if message.channel.name != INBOX_CHANNEL:
            return
        # Ignore empty messages (attachments only, etc.)
        text = message.content.strip()
        if not text:
            return

        # Add a ⏳ reaction so the user knows it's processing
        try:
            await message.add_reaction("⏳")
        except discord.HTTPException:
            pass

        # Run the blocking HTTP call in a thread pool so we don't block the event loop
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            capture_thought,
            self.supabase_url,
            self.service_role_key,
            text,
        )

        # Remove the ⏳ reaction
        try:
            await message.remove_reaction("⏳", self.user)
        except discord.HTTPException:
            pass

        if "error" in result:
            await message.add_reaction("❌")
            await message.reply(f"Failed to capture: {result['error']}", mention_author=False)
            return

        # Success — reply in thread with receipt
        await message.add_reaction("✅")
        confidence = int(result["confidence"] * 100)
        receipt = (
            f"**{result['title']}**\n"
            f"Category: `{result['category']}` · Confidence: {confidence}%\n"
            f"Status: `{result['status']}` · ID: `{result['id']}`"
        )

        # Reply in a thread if possible, otherwise just reply
        try:
            thread = await message.create_thread(name=result["title"][:100])
            await thread.send(receipt)
        except discord.HTTPException:
            await message.reply(receipt, mention_author=False)


def main() -> None:
    env = load_env()

    missing = [
        k for k in ("DISCORD_BOT_TOKEN", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
        if not env.get(k)
    ]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print("Add them to your .env file.")
        raise SystemExit(1)

    bot = SecondBrainBot(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
    bot.run(env["DISCORD_BOT_TOKEN"], log_handler=None)


if __name__ == "__main__":
    main()
