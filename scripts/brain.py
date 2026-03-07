#!/usr/bin/env python3
"""
brain.py — CLI capture tool for Open Brain
Cross-platform (Windows + Linux)

Usage:
  python brain.py "your thought here"
  python brain.py --recent [--days 7] [--category project]
  python brain.py --search "what you want to find" [--category idea]
  python brain.py --stats [--days 30]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_env() -> dict:
    """Load .env from the project root (parent of scripts/)."""
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
    # Environment variables take precedence over .env file
    for key in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def api_request(url: str, *, method: str = "GET", body: dict | None = None, headers: dict) -> dict:
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            err = json.loads(raw)
            msg = err.get("error") or err.get("message") or raw
        except json.JSONDecodeError:
            msg = raw
        print(f"Error {e.code}: {msg}", file=sys.stderr)
        sys.exit(1)


def capture(env: dict, text: str, source: str = "cli") -> None:
    url = f"{env['SUPABASE_URL']}/functions/v1/process-thought"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
    }
    result = api_request(url, method="POST", body={"text": text, "source": source}, headers=headers)
    print(f"Captured: {result['title']}")
    print(f"Category: {result['category']} (confidence: {int(result['confidence'] * 100)}%)")
    print(f"Status:   {result['status']}")
    print(f"ID:       {result['id']}")


def recent(env: dict, days: int = 7, category: str | None = None) -> None:
    params: dict = {"status": "eq.active", "order": "created_at.desc", "limit": "50"}
    # Date filter
    import datetime
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat()
    params["created_at"] = f"gte.{since}"
    if category:
        params["category"] = f"eq.{category}"

    # Select specific columns
    params["select"] = "title,category,summary,people,topics,action_items,source,created_at"

    url = f"{env['SUPABASE_URL']}/rest/v1/thoughts?{urllib.parse.urlencode(params)}"
    headers = {
        "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
    }
    results = api_request(url, headers=headers)
    if not results:
        print(f"No thoughts in the last {days} day(s).")
        return

    print(f"{len(results)} thought(s) in the last {days} day(s):\n")
    for t in results:
        _print_thought(t)


def search(env: dict, query: str, limit: int = 10, category: str | None = None) -> None:
    # Generate embedding
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

    # Call semantic_search RPC
    url = f"{env['SUPABASE_URL']}/rest/v1/rpc/semantic_search"
    headers = {
        "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        "Content-Type": "application/json",
    }
    body = {
        "query_embedding": embedding,
        "match_limit": limit,
        "filter_category": category,
        "filter_status": "active",
    }
    results = api_request(url, method="POST", body=body, headers=headers)
    if not results:
        print("No matching thoughts found.")
        return

    print(f"{len(results)} result(s) for '{query}':\n")
    for t in results:
        similarity = t.get("similarity", 0)
        _print_thought(t, similarity=similarity)


def stats(env: dict, days: int = 30) -> None:
    import datetime
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat()
    params = {
        "select": "category,topics,status",
        "status": "neq.archived",
        "created_at": f"gte.{since}",
    }
    url = f"{env['SUPABASE_URL']}/rest/v1/thoughts?{urllib.parse.urlencode(params)}"
    headers = {
        "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
    }
    results = api_request(url, headers=headers)
    if not results:
        print(f"No thoughts in the last {days} day(s).")
        return

    cats: dict[str, int] = {}
    topic_counts: dict[str, int] = {}
    needs_review = 0
    for t in results:
        cats[t["category"]] = cats.get(t["category"], 0) + 1
        for topic in t.get("topics") or []:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        if t["status"] == "needs_review":
            needs_review += 1

    print(f"Brain stats — last {days} days ({len(results)} total)\n")
    print("By category:")
    for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {n}")
    print("\nTop topics:")
    for topic, n in sorted(topic_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {topic}: {n}")
    if needs_review:
        print(f"\n{needs_review} thought(s) need review")
    else:
        print("\nNo thoughts need review")


def _print_thought(t: dict, similarity: float | None = None) -> None:
    print(f"[{t.get('category', '?')}] {t.get('title', 'Untitled')}")
    if t.get("summary"):
        print(f"  {t['summary']}")
    if t.get("people"):
        print(f"  People:  {', '.join(t['people'])}")
    if t.get("topics"):
        print(f"  Topics:  {', '.join(t['topics'])}")
    if t.get("action_items"):
        print(f"  Actions: {' | '.join(t['action_items'])}")
    captured = t.get("created_at", "")[:10]
    source = t.get("source", "unknown")
    sim_str = f" · {similarity * 100:.1f}% match" if similarity is not None else ""
    print(f"  {captured} · {source}{sim_str}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="brain",
        description="Open Brain CLI — capture and search your second brain",
    )
    parser.add_argument("thought", nargs="?", help="Thought to capture")
    parser.add_argument("--recent", action="store_true", help="List recent thoughts")
    parser.add_argument("--search", metavar="QUERY", help="Semantic search")
    parser.add_argument("--stats", action="store_true", help="Show brain stats")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--limit", type=int, default=10, help="Max search results (default: 10)")
    parser.add_argument(
        "--category",
        choices=["person", "project", "idea", "admin", "insight"],
        help="Filter by category",
    )
    parser.add_argument("--source", default="cli", help="Source label for captures (default: cli)")
    parser.add_argument("--delete", metavar="ID", help="Delete a thought by its UUID")

    args = parser.parse_args()

    env = load_env()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not env.get(k)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Copy .env.example to .env and fill in your credentials.", file=sys.stderr)
        sys.exit(1)

    if args.delete:
        url = f"{env['SUPABASE_URL']}/rest/v1/thoughts?id=eq.{urllib.parse.quote(args.delete)}"
        headers = {
            "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
            "Prefer": "return=representation",
        }
        req = urllib.request.Request(url, headers=headers, method="DELETE")
        try:
            with urllib.request.urlopen(req) as resp:
                deleted = json.loads(resp.read().decode("utf-8"))
                if deleted:
                    print(f"Deleted: {deleted[0].get('title', args.delete)}")
                else:
                    print(f"No thought found with ID {args.delete}")
        except urllib.error.HTTPError as e:
            print(f"Error {e.code}: {e.read().decode()}", file=sys.stderr)
            sys.exit(1)
    elif args.thought:
        capture(env, args.thought, source=args.source)
    elif args.recent:
        recent(env, days=args.days, category=args.category)
    elif args.search:
        if not env.get("OPENAI_API_KEY"):
            print("OPENAI_API_KEY required for search.", file=sys.stderr)
            sys.exit(1)
        search(env, args.search, limit=args.limit, category=args.category)
    elif args.stats:
        stats(env, days=args.days if args.days != 7 else 30)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
