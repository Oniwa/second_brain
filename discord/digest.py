#!/usr/bin/env python3
"""
Second Brain Digest — delivers daily and weekly digests via Discord DM + Gmail.

Usage:
  python3 digest.py --auth            # First-run Gmail authorization
  python3 digest.py --daily           # Send daily digest
  python3 digest.py --weekly          # Send weekly digest
  python3 digest.py --daily --test    # Print digest without sending
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Missing dependencies. Run: pip3 install -r discord/digest-requirements.txt")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


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
        "DISCORD_BOT_TOKEN", "DISCORD_USER_ID", "GMAIL_RECIPIENT",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def authorize_gmail() -> None:
    """Run the OAuth flow and save token.json. Run once interactively."""
    if not CREDENTIALS_FILE.exists():
        print(f"credentials.json not found at {CREDENTIALS_FILE}")
        sys.exit(1)
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    print(f"Authorization successful. Token saved to {TOKEN_FILE}")


def get_gmail_service():
    if not TOKEN_FILE.exists():
        print("token.json not found. Run: python3 discord/digest.py --auth")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_digest(supabase_url: str, service_role_key: str, digest_type: str) -> dict:
    url = f"{supabase_url}/functions/v1/generate-digest"
    body = json.dumps({"type": digest_type}).encode("utf-8")
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return {"error": json.loads(raw).get("error", raw)}
        except json.JSONDecodeError:
            return {"error": raw}


DISCORD_HEADERS = {
    "User-Agent": "DiscordBot (https://github.com/Oniwa/second_brain, 1.0)",
    "Content-Type": "application/json",
}


def send_discord_dm(bot_token: str, user_id: str, message: str) -> None:
    headers = {**DISCORD_HEADERS, "Authorization": f"Bot {bot_token}"}

    # Step 1: Create DM channel
    dm_req = urllib.request.Request(
        "https://discord.com/api/v10/users/@me/channels",
        data=json.dumps({"recipient_id": user_id}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(dm_req) as resp:
        channel = json.loads(resp.read().decode("utf-8"))
    channel_id = channel["id"]

    # Step 2: Send message (split if over 1900 chars)
    msg_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
    for chunk in chunks:
        msg_req = urllib.request.Request(
            msg_url,
            data=json.dumps({"content": chunk}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(msg_req):
            pass


def send_gmail(service, recipient: str, subject: str, body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "me"
    msg["To"] = recipient

    # Plain text part
    text_part = MIMEText(
        body.replace("**", "").replace("•", "-").replace("📋", "").replace("⏳", "").replace("💡", "").replace("📚", ""),
        "plain"
    )
    # Simple HTML part
    html_body = body.replace("\n", "<br>").replace("**", "<strong>").replace("**", "</strong>")
    html_part = MIMEText(f"<html><body><p>{html_body}</p></body></html>", "html")

    msg.attach(text_part)
    msg.attach(html_part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def run_digest(digest_type: str, test_mode: bool = False) -> None:
    env = load_env()

    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not env.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    print(f"Fetching {digest_type} digest...")
    result = fetch_digest(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"], digest_type)

    if "error" in result:
        print(f"Error fetching digest: {result['error']}")
        sys.exit(1)

    digest = result["digest"]
    subject = result["subject"]
    thought_count = result.get("thought_count", 0)

    print(f"\n{subject} ({thought_count} thoughts)\n")
    print("=" * 50)
    print(digest)
    print("=" * 50)

    if test_mode:
        print("\n[TEST MODE] Digest not sent.")
        return

    # Send Discord DM
    if env.get("DISCORD_BOT_TOKEN") and env.get("DISCORD_USER_ID"):
        try:
            send_discord_dm(env["DISCORD_BOT_TOKEN"], env["DISCORD_USER_ID"], f"**{subject}**\n\n{digest}")
            print("✓ Discord DM sent")
        except Exception as e:
            print(f"✗ Discord DM failed: {e}")
    else:
        print("Skipping Discord DM (DISCORD_BOT_TOKEN or DISCORD_USER_ID not set)")

    # Send Gmail
    if env.get("GMAIL_RECIPIENT"):
        try:
            gmail = get_gmail_service()
            send_gmail(gmail, env["GMAIL_RECIPIENT"], subject, digest)
            print(f"✓ Gmail sent to {env['GMAIL_RECIPIENT']}")
        except Exception as e:
            print(f"✗ Gmail failed: {e}")
    else:
        print("Skipping Gmail (GMAIL_RECIPIENT not set)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Second Brain digest delivery")
    parser.add_argument("--auth", action="store_true", help="Authorize Gmail (run once)")
    parser.add_argument("--daily", action="store_true", help="Send daily digest")
    parser.add_argument("--weekly", action="store_true", help="Send weekly digest")
    parser.add_argument("--test", action="store_true", help="Print digest without sending")
    args = parser.parse_args()

    if args.auth:
        authorize_gmail()
    elif args.daily:
        run_digest("daily", test_mode=args.test)
    elif args.weekly:
        run_digest("weekly", test_mode=args.test)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
