#!/usr/bin/env python3
"""
setup_rpi.py — One-shot Raspberry Pi setup for Second Brain

Run this on your Pi after cloning the repo and copying .env and token.json:
  sudo python3 scripts/setup_rpi.py

What it does:
  1. Checks all required environment variables are present
  2. Installs Python dependencies
  3. Installs the Discord bot as a systemd service (auto-start on boot)
  4. Sets up all cron jobs (digests, review, nudge, reminders)
  5. Prints verification commands
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DISCORD_DIR = PROJECT_ROOT / "discord"
SERVICE_NAME = "second-brain-bot"
SERVICE_SRC = DISCORD_DIR / "second-brain-bot.service"
SERVICE_DEST = Path(f"/etc/systemd/system/{SERVICE_NAME}.service")
CRON_FILE = Path("/etc/cron.d/second-brain")

REQUIRED_ENV_VARS = [
    "DISCORD_BOT_TOKEN",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DISCORD_USER_ID",
    "GMAIL_RECIPIENT",
]


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def check_root() -> None:
    if os.geteuid() != 0:
        print("This script must be run with sudo:")
        print("  sudo python3 scripts/setup_rpi.py")
        sys.exit(1)


def check_env() -> None:
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        print(f"ERROR: .env not found at {env_file}")
        print("Copy .env from your dev machine first:")
        print("  scp /path/to/second_brain/.env <user>@<pi-ip>:~/second_brain/.env")
        sys.exit(1)

    # Parse .env
    env = {}
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    # Environment variables take precedence
    for key in REQUIRED_ENV_VARS:
        if key in os.environ:
            env[key] = os.environ[key]

    missing = [k for k in REQUIRED_ENV_VARS if not env.get(k)]
    if missing:
        print(f"ERROR: Missing required keys in .env: {', '.join(missing)}")
        sys.exit(1)

    print(f"  .env found — all required keys present")

    # Check token.json for Gmail
    token_file = PROJECT_ROOT / "token.json"
    if not token_file.exists():
        print("  WARNING: token.json not found — Gmail delivery will fail.")
        print("  Copy token.json from your dev machine:")
        print("  scp /path/to/second_brain/token.json <user>@<pi-ip>:~/second_brain/token.json")
    else:
        print("  token.json found — Gmail delivery ready")


def install_dependencies() -> None:
    print("\n[2/4] Installing Python dependencies...")
    requirements = [
        DISCORD_DIR / "requirements.txt",
        DISCORD_DIR / "digest-requirements.txt",
    ]
    for req in requirements:
        if req.exists():
            run(["pip3", "install", "-r", str(req), "--break-system-packages", "-q"])
        else:
            print(f"  (skipping {req.name} — not found)")


def install_systemd_service() -> None:
    print("\n[3/4] Installing Discord bot systemd service...")

    actual_user = os.environ.get("SUDO_USER", "pi")
    project_path = str(PROJECT_ROOT)

    service_content = SERVICE_SRC.read_text()
    service_content = service_content.replace("/home/pi/second_brain", project_path)
    service_content = service_content.replace("User=pi", f"User={actual_user}")
    service_content = service_content.replace(
        "EnvironmentFile=/home/pi/second_brain/.env",
        f"EnvironmentFile={project_path}/.env"
    )

    SERVICE_DEST.write_text(service_content)
    print(f"  Wrote {SERVICE_DEST}")

    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", SERVICE_NAME])
    run(["systemctl", "start", SERVICE_NAME])
    print("  Discord bot service enabled and started")


def setup_cron() -> None:
    print("\n[4/4] Setting up cron jobs...")

    actual_user = os.environ.get("SUDO_USER", "pi")
    project_path = str(PROJECT_ROOT)
    python = "/usr/bin/python3"
    log_dir = f"{project_path}/logs"

    Path(log_dir).mkdir(exist_ok=True)

    digest  = f"{project_path}/discord/digest.py"
    nudge   = f"{project_path}/scripts/nudge.py"
    remind  = f"{project_path}/scripts/remind.py"

    jobs = [
        ("Daily digest — 7am", f"0 7 * * *   {actual_user} {python} {digest} --daily >> {log_dir}/digest-daily.log 2>&1"),
        ("Reminder check — 8am", f"0 8 * * *   {actual_user} {python} {remind} >> {log_dir}/remind.log 2>&1"),
        ("Nudge check — 6pm (silent if captured recently)", f"0 18 * * *  {actual_user} {python} {nudge} >> {log_dir}/nudge.log 2>&1"),
        ("Weekly digest — Sunday 8am", f"0 8 * * 0   {actual_user} {python} {digest} --weekly >> {log_dir}/digest-weekly.log 2>&1"),
        ("Weekly review — Sunday 9am", f"0 9 * * 0   {actual_user} {python} {digest} --review >> {log_dir}/digest-review.log 2>&1"),
    ]

    if CRON_FILE.exists():
        CRON_FILE.unlink()

    lines = ["# Second Brain cron jobs — managed by setup_rpi.py\n"]
    for label, job in jobs:
        lines.append(f"# {label}\n{job}\n")

    CRON_FILE.write_text("\n".join(lines))
    print(f"  Wrote {CRON_FILE}")
    for label, _ in jobs:
        print(f"  + {label}")


def print_next_steps() -> None:
    print(f"""
{'=' * 55}
  Setup complete! Verify with:

  Discord bot:
    sudo systemctl status {SERVICE_NAME}
    sudo journalctl -u {SERVICE_NAME} -f

  Cron jobs:
    cat {CRON_FILE}

  Test scripts manually:
    python3 discord/digest.py --daily
    python3 scripts/remind.py --test
    python3 scripts/nudge.py --test

  After any code update on dev machine:
    git pull origin develop
    sudo systemctl restart {SERVICE_NAME}
{'=' * 55}
""")


def main() -> None:
    print("=" * 55)
    print("  Second Brain — Raspberry Pi Setup")
    print("=" * 55)

    check_root()
    print("\n[1/4] Checking environment...")
    check_env()
    install_dependencies()
    install_systemd_service()
    setup_cron()
    print_next_steps()


if __name__ == "__main__":
    main()
