#!/usr/bin/env python3
"""
Hash parity check — verifies that the stored content_hash matches:
  1. Python SHA-256 (UTF-8, same normalization as Edge Function)
  2. PostgreSQL sha256() with equivalent normalization

Usage: python scripts/hash_parity_check.py
"""

import hashlib
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path


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
    for key in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def py_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def rest_get(url: str, key: str, params: dict) -> list:
    qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(
        f"{url}?{qs}",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_diverse_thoughts(supabase_url: str, key: str) -> list:
    base = f"{supabase_url}/rest/v1/thoughts"
    thoughts = []
    seen_ids = set()

    # Pull 2 from each category for variety
    for category in ("insight", "idea", "project", "person", "admin"):
        rows = rest_get(base, key, {
            "select": "id,raw_text,content_hash,category,source",
            "category": f"eq.{category}",
            "status": "eq.active",
            "order": "created_at.desc",
            "limit": "2",
        })
        for r in rows:
            if r["id"] not in seen_ids and r.get("content_hash"):
                seen_ids.add(r["id"])
                thoughts.append(r)

    # Top up to 10 with misc sources if needed
    if len(thoughts) < 10:
        rows = rest_get(base, key, {
            "select": "id,raw_text,content_hash,category,source",
            "status": "eq.active",
            "order": "created_at.asc",  # oldest — likely different content style
            "limit": "20",
        })
        for r in rows:
            if r["id"] not in seen_ids and r.get("content_hash"):
                seen_ids.add(r["id"])
                thoughts.append(r)
                if len(thoughts) >= 10:
                    break

    return thoughts[:10]


def pg_hashes(supabase_url: str, key: str, thoughts: list[dict]) -> dict[str, str]:
    """Call hash_thought_text(raw) RPC for each thought's raw_text."""
    results = {}
    for t in thoughts:
        body = json.dumps({"raw": t["raw_text"]}).encode("utf-8")
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/rpc/hash_thought_text",
            data=body,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if isinstance(result, str) and len(result) == 64:
                    results[t["id"]] = result
        except Exception as e:
            print(f"  [warn] hash_thought_text RPC failed for {t['id']}: {e}")
    return results


def main() -> None:
    env = load_env()
    url = env["SUPABASE_URL"]
    key = env["SUPABASE_SERVICE_ROLE_KEY"]

    print("Fetching 10 diverse thoughts...")
    thoughts = fetch_diverse_thoughts(url, key)
    print(f"Fetched {len(thoughts)} thoughts.\n")

    print("Running PostgreSQL hash via hash_thought_text() RPC...")
    pg = pg_hashes(url, key, thoughts)
    if not pg:
        print("  PostgreSQL hashes unavailable — will skip that column.\n")

    # Header
    col = 10
    print(f"{'#':<3} {'Category':<9} {'Source':<14} {'Raw text (50 chars)':<52} {'stored==py':<11} {'stored==pg':<11} {'py==pg'}")
    print("-" * 115)

    all_ok = True
    for i, t in enumerate(thoughts, 1):
        tid = t["id"]
        raw = t["raw_text"] or ""
        stored = (t["content_hash"] or "").lower()
        computed = py_hash(raw)
        pg_hash = pg.get(tid, "")

        stored_py = "OK" if stored == computed else "MISMATCH"
        stored_pg = ("OK" if stored == pg_hash else "MISMATCH") if pg_hash else "N/A"
        py_pg     = ("OK" if computed == pg_hash else "MISMATCH") if pg_hash else "N/A"

        if "MISMATCH" in f"{stored_py}{stored_pg}{py_pg}":
            all_ok = False

        preview = raw.replace("\n", " ")[:50]
        print(f"{i:<3} {t['category']:<9} {(t['source'] or ''):<14} {preview:<52} {stored_py:<11} {stored_pg:<11} {py_pg}")

    print()
    if all_ok:
        print("All hashes match.")
    else:
        print("MISMATCHES detected — see rows above.")
        # Print detail for mismatches
        for t in thoughts:
            raw = t["raw_text"] or ""
            stored = (t["content_hash"] or "").lower()
            computed = py_hash(raw)
            pg_hash = pg.get(t["id"], "")
            if stored != computed or (pg_hash and stored != pg_hash):
                print(f"\nMismatch detail — ID: {t['id']}")
                print(f"  raw_text repr: {repr(raw[:120])}")
                print(f"  normalized:    {repr(normalize(raw[:120]))}")
                print(f"  stored hash:   {stored}")
                print(f"  python hash:   {computed}")
                if pg_hash:
                    print(f"  pg hash:       {pg_hash}")


if __name__ == "__main__":
    main()
