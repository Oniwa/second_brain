#!/usr/bin/env python3
"""
backfill_urls.py — Extract URLs from raw_text and populate the urls[] column
for all thoughts that currently have an empty urls array.

Usage:
  python scripts/backfill_urls.py [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

URL_REGEX = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


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


def api_request(url, *, method="GET", body=None, headers):
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else []
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        print(f"HTTP {e.code}: {raw}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Backfill urls[] from raw_text")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be updated without writing")
    args = parser.parse_args()

    env = load_env()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not env.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    base = env["SUPABASE_URL"]
    key = env["SUPABASE_SERVICE_ROLE_KEY"]
    headers_read = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    headers_write = {
        **headers_read,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    # Fetch all rows where urls is the empty array
    params = urllib.parse.urlencode({
        "select": "id,raw_text",
        "urls": "eq.{}",
        "order": "created_at.asc",
    })
    thoughts = api_request(f"{base}/rest/v1/thoughts?{params}", headers=headers_read)

    print(f"Found {len(thoughts)} thought(s) with empty urls array")
    updated = skipped = 0

    for t in thoughts:
        found = URL_REGEX.findall(t["raw_text"])
        if not found:
            skipped += 1
            continue

        if args.dry_run:
            print(f"  [dry-run] {t['id']}: {found}")
            updated += 1
            continue

        patch_url = (
            f"{base}/rest/v1/thoughts"
            f"?id=eq.{urllib.parse.quote(t['id'])}"
        )
        api_request(
            patch_url,
            method="PATCH",
            body={"urls": found},
            headers=headers_write,
        )
        print(f"  Updated {t['id']}: {found}")
        updated += 1

    print(f"\nDone. Updated: {updated}  Skipped (no URLs): {skipped}")


if __name__ == "__main__":
    main()
