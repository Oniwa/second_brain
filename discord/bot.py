#!/usr/bin/env python3
"""
Second Brain Discord Bot

Watches #sb-inbox for messages:
  - Any message            → captured as a thought (receipt in thread)
  - !brain <question>      → semantic search + Haiku synthesis → answer in thread
  - !prep <description>    → meeting prep brief → reply in thread
      Optional: !prep 1:1 with Mike --people Mike

Usage:
  pip install -r discord/requirements.txt
  python discord/bot.py
"""

import asyncio
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

import aiohttp
import discord

INBOX_CHANNEL = "sb-inbox"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

BRAIN_QUERY_PROMPT = """You are a personal assistant answering a question using someone's second brain notes.

The user asked: {question}

Below are the most relevant thoughts from their brain. Answer the question directly and concisely using this context.
- Be specific — reference actual titles, names, and details from the notes
- If the notes don't contain a clear answer, say so honestly
- Keep the response under 200 words

RELEVANT THOUGHTS:
{context}"""

MEETING_PREP_PROMPT = """You are a personal assistant preparing someone for a meeting.
Below is raw context pulled from their second brain related to this meeting.

Synthesize a focused prep brief using exactly this structure:

**Meeting Prep: {meeting}**

👥 What you know about the people:
{people_section}

📋 Relevant context:
• [2-4 most relevant thoughts, specific details only]

⚡ Open action items:
• [any open actions from the context — or "None captured" if empty]

❓ Questions worth asking:
• [1-3 questions suggested by gaps or unresolved threads in the context]

Be specific — use actual names, project names, and details. Keep under 300 words."""


def load_env() -> dict:
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
    for key in (
        "DISCORD_BOT_TOKEN", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def parse_people_flag(text: str) -> tuple[str, list[str]]:
    """Extract --people Name1 Name2 from text. Returns (cleaned_text, people_list)."""
    match = re.search(r"--people\s+(.+?)(?:\s*--|$)", text, re.IGNORECASE)
    if not match:
        return text.strip(), []
    people = [p.strip() for p in match.group(1).split() if p.strip()]
    cleaned = text[:match.start()].strip()
    return cleaned, people


def capture_thought_sync(supabase_url: str, service_role_key: str, text: str) -> dict:
    url = f"{supabase_url}/functions/v1/process-thought"
    body = json.dumps({"text": text, "source": "discord"}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {service_role_key}"},
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


async def generate_embedding(session: aiohttp.ClientSession, text: str, openai_key: str) -> list:
    async with session.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
        json={"model": "text-embedding-3-small", "input": text},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data["data"][0]["embedding"]


async def semantic_search(
    session: aiohttp.ClientSession,
    supabase_url: str,
    key: str,
    embedding: list,
    limit: int = 10,
) -> list:
    async with session.post(
        f"{supabase_url}/rest/v1/rpc/semantic_search",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"query_embedding": embedding, "match_limit": limit, "filter_category": None, "filter_status": "active"},
    ) as resp:
        resp.raise_for_status()
        return await resp.json()


async def people_search(
    session: aiohttp.ClientSession,
    supabase_url: str,
    key: str,
    person: str,
) -> list:
    async with session.get(
        f"{supabase_url}/rest/v1/thoughts",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        params={
            "select": "id,title,summary,category,people,topics,action_items,source,created_at",
            "status": "eq.active",
            "people": f"cs.{{{person}}}",
            "order": "created_at.desc",
            "limit": "10",
        },
    ) as resp:
        if resp.status != 200:
            return []
        return await resp.json()


async def call_haiku(session: aiohttp.ClientSession, anthropic_key: str, prompt: str) -> str:
    async with session.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={"model": HAIKU_MODEL, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data["content"][0]["text"].strip()


def format_thought(t: dict) -> str:
    lines = [f"[{t.get('category', '?')}] {t.get('title', 'Untitled')}"]
    if t.get("summary"):
        lines.append(f"  {t['summary']}")
    if t.get("people"):
        lines.append(f"  People: {', '.join(t['people'])}")
    if t.get("topics"):
        lines.append(f"  Topics: {', '.join(t['topics'])}")
    if t.get("action_items"):
        lines.append(f"  Actions: {' | '.join(t['action_items'])}")
    return "\n".join(lines)


def merge_dedupe(people_results: list[list], semantic_results: list) -> list:
    seen = set()
    merged = []
    for results in people_results:
        for t in results:
            if t["id"] not in seen:
                seen.add(t["id"])
                merged.append(t)
    for t in semantic_results:
        if t["id"] not in seen:
            seen.add(t["id"])
            merged.append(t)
    return merged


class SecondBrainBot(discord.Client):
    def __init__(self, env: dict):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.env = env

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} — watching #{INBOX_CHANNEL}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.channel.name != INBOX_CHANNEL:
            return
        text = message.content.strip()
        if not text:
            return

        if text.lower().startswith("!brain "):
            await self.handle_brain_query(message, text[7:].strip())
        elif text.lower().startswith("!prep "):
            await self.handle_meeting_prep(message, text[6:].strip())
        else:
            await self.handle_capture(message, text)

    async def handle_capture(self, message: discord.Message, text: str) -> None:
        try:
            await message.add_reaction("⏳")
        except discord.HTTPException:
            pass

        result = await asyncio.get_event_loop().run_in_executor(
            None, capture_thought_sync,
            self.env["SUPABASE_URL"], self.env["SUPABASE_SERVICE_ROLE_KEY"], text,
        )

        try:
            await message.remove_reaction("⏳", self.user)
        except discord.HTTPException:
            pass

        if "error" in result:
            await message.add_reaction("❌")
            await message.reply(f"Failed to capture: {result['error']}", mention_author=False)
            return

        await message.add_reaction("✅")
        confidence = int(result["confidence"] * 100)
        receipt = (
            f"**{result['title']}**\n"
            f"Category: `{result['category']}` · Confidence: {confidence}%\n"
            f"Status: `{result['status']}` · ID: `{result['id']}`"
        )
        try:
            thread = await message.create_thread(name=result["title"][:100])
            await thread.send(receipt)
        except discord.HTTPException:
            await message.reply(receipt, mention_author=False)

    async def handle_brain_query(self, message: discord.Message, query: str) -> None:
        if not query:
            await message.reply("Usage: `!brain <your question>`", mention_author=False)
            return
        if not self.env.get("OPENAI_API_KEY") or not self.env.get("ANTHROPIC_API_KEY"):
            await message.reply("OPENAI_API_KEY or ANTHROPIC_API_KEY not configured.", mention_author=False)
            return

        try:
            await message.add_reaction("🔍")
        except discord.HTTPException:
            pass

        try:
            async with aiohttp.ClientSession() as session:
                embedding = await generate_embedding(session, query, self.env["OPENAI_API_KEY"])
                results = await semantic_search(
                    session, self.env["SUPABASE_URL"], self.env["SUPABASE_SERVICE_ROLE_KEY"], embedding, limit=8
                )

                if not results:
                    await message.reply("Nothing relevant found in your brain.", mention_author=False)
                    return

                context = "\n\n".join(format_thought(t) for t in results)
                prompt = BRAIN_QUERY_PROMPT.format(question=query, context=context)
                answer = await call_haiku(session, self.env["ANTHROPIC_API_KEY"], prompt)

            try:
                await message.remove_reaction("🔍", self.user)
            except discord.HTTPException:
                pass

            await message.add_reaction("✅")
            try:
                thread = await message.create_thread(name=f"!brain: {query[:80]}")
                await thread.send(answer)
            except discord.HTTPException:
                await message.reply(answer, mention_author=False)

        except Exception as e:
            try:
                await message.remove_reaction("🔍", self.user)
            except discord.HTTPException:
                pass
            await message.add_reaction("❌")
            await message.reply(f"Query failed: {e}", mention_author=False)

    async def handle_meeting_prep(self, message: discord.Message, text: str) -> None:
        meeting, people = parse_people_flag(text)
        if not meeting:
            await message.reply("Usage: `!prep <meeting description> [--people Name1 Name2]`", mention_author=False)
            return
        if not self.env.get("OPENAI_API_KEY") or not self.env.get("ANTHROPIC_API_KEY"):
            await message.reply("OPENAI_API_KEY or ANTHROPIC_API_KEY not configured.", mention_author=False)
            return

        try:
            await message.add_reaction("⏳")
        except discord.HTTPException:
            pass

        try:
            async with aiohttp.ClientSession() as session:
                embedding = await generate_embedding(session, meeting, self.env["OPENAI_API_KEY"])

                people_results, sem_results = await asyncio.gather(
                    asyncio.gather(*[
                        people_search(session, self.env["SUPABASE_URL"], self.env["SUPABASE_SERVICE_ROLE_KEY"], p)
                        for p in people
                    ]) if people else asyncio.gather(),
                    semantic_search(
                        session, self.env["SUPABASE_URL"], self.env["SUPABASE_SERVICE_ROLE_KEY"], embedding, limit=12
                    ),
                )

                merged = merge_dedupe(list(people_results), sem_results)

                if not merged:
                    await message.reply(f"No context found for \"{meeting}\".", mention_author=False)
                    return

                context = "\n\n".join(format_thought(t) for t in merged)
                people_section = "\n".join(f"• {p}" for p in people) if people else "• (none specified)"
                prompt = MEETING_PREP_PROMPT.format(
                    meeting=meeting, people_section=people_section, context=context
                )
                # Add context to prompt
                full_prompt = prompt + f"\n\nCONTEXT FROM BRAIN:\n\n{context}"
                brief = await call_haiku(session, self.env["ANTHROPIC_API_KEY"], full_prompt)

            try:
                await message.remove_reaction("⏳", self.user)
            except discord.HTTPException:
                pass

            await message.add_reaction("✅")
            try:
                thread = await message.create_thread(name=f"!prep: {meeting[:80]}")
                await thread.send(brief)
            except discord.HTTPException:
                await message.reply(brief, mention_author=False)

        except Exception as e:
            try:
                await message.remove_reaction("⏳", self.user)
            except discord.HTTPException:
                pass
            await message.add_reaction("❌")
            await message.reply(f"Meeting prep failed: {e}", mention_author=False)


def main() -> None:
    env = load_env()
    missing = [
        k for k in ("DISCORD_BOT_TOKEN", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
        if not env.get(k)
    ]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        raise SystemExit(1)

    bot = SecondBrainBot(env)
    bot.run(env["DISCORD_BOT_TOKEN"], log_handler=None)


if __name__ == "__main__":
    main()
