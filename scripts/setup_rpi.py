#!/usr/bin/env python3
"""
setup_rpi.py — One-shot Raspberry Pi setup for Second Brain

Run this on your Pi after cloning the repo and copying .env:
  python3 scripts/setup_rpi.py

What it does:
  1. Installs Python dependencies (discord.py, google-auth libs)
  2. Installs the Discord bot as a systemd service (auto-start on boot)
  3. Sets up daily + weekly digest cron jobs
  4. Prints next steps
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
CRON_MARKER = "# second-brain-digest"


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
        print(f"ERROR: .env file not found at {env_file}")
        print("Copy .env.example to .env and fill in your credentials first.")
        sys.exit(1)
    print(f"  .env found at {env_file}")


def install_dependencies() -> None:
    print("\n[1/4] Installing Python dependencies...")
    requirements = [
        DISCORD_DIR / "requirements.txt",
        PROJECT_ROOT / "discord" / "digest-requirements.txt",
    ]
    for req in requirements:
        if req.exists():
            run(["pip3", "install", "-r", str(req), "--break-system-packages", "-q"])
        else:
            print(f"  (skipping {req.name} — not found yet)")


def install_systemd_service() -> None:
    print("\n[2/4] Installing systemd service for Discord bot...")

    # Read the service file and update the path for this Pi's actual location
    service_content = SERVICE_SRC.read_text()
    actual_user = os.environ.get("SUDO_USER", "pi")
    actual_home = Path(f"/home/{actual_user}")
    project_path = str(PROJECT_ROOT)

    # Replace placeholder paths with actual paths
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
    print(f"  Discord bot service enabled and started.")


def setup_cron() -> None:
    print("\n[3/4] Setting up digest cron jobs...")

    actual_user = os.environ.get("SUDO_USER", "pi")
    project_path = str(PROJECT_ROOT)
    python = "/usr/bin/python3"
    digest_script = f"{project_path}/discord/digest.py"
    log_dir = f"{project_path}/logs"

    # Ensure log directory exists
    Path(log_dir).mkdir(exist_ok=True)

    nudge_script = f"{project_path}/scripts/nudge.py"
    daily_job = (
        f"0 7 * * * {actual_user} {python} {digest_script} --daily "
        f">> {log_dir}/digest-daily.log 2>&1 {CRON_MARKER}"
    )
    weekly_job = (
        f"0 8 * * 0 {actual_user} {python} {digest_script} --weekly "
        f">> {log_dir}/digest-weekly.log 2>&1 {CRON_MARKER}"
    )
    nudge_job = (
        f"0 18 * * * {actual_user} {python} {nudge_script} "
        f">> {log_dir}/nudge.log 2>&1 {CRON_MARKER}"
    )

    cron_file = Path("/etc/cron.d/second-brain-digest")

    # Remove old entries if they exist
    if cron_file.exists():
        cron_file.unlink()

    cron_file.write_text(
        f"# Second Brain digest + nudge cron jobs\n"
        f"# Daily digest at 7am\n"
        f"{daily_job}\n"
        f"# Weekly digest Sunday at 8am\n"
        f"{weekly_job}\n"
        f"# Nudge check at 6pm daily (sends only if silent for 2+ days)\n"
        f"{nudge_job}\n"
    )
    print(f"  Wrote {cron_file}")
    print("  NOTE: Cron jobs will activate once discord/digest.py is built (Phase 4).")


def print_next_steps() -> None:
    actual_user = os.environ.get("SUDO_USER", "pi")
    print("\n[4/4] Done! Here's what's running:\n")
    print("  Discord bot:")
    print(f"    sudo systemctl status {SERVICE_NAME}")
    print(f"    sudo journalctl -u {SERVICE_NAME} -f   # live logs")
    print()
    print("  Digest cron jobs: installed but waiting for discord/digest.py (Phase 4)")
    print()
    print("  Next steps:")
    print("  1. Complete Gmail API setup (credentials.json in project root)")
    print("  2. Build Phase 4 with Claude Code (discord/digest.py)")
    print(f"  3. Run once to authorize Gmail:")
    print(f"     python3 discord/digest.py --auth")
    print(f"  4. Test manually:")
    print(f"     python3 discord/digest.py --daily")
    print(f"     python3 discord/digest.py --weekly")
    print()
    print("  The cron jobs will then run automatically on schedule.")


def main() -> None:
    print("=" * 55)
    print("  Second Brain — Raspberry Pi Setup")
    print("=" * 55)

    check_root()
    check_env()
    install_dependencies()
    install_systemd_service()
    setup_cron()
    print_next_steps()


if __name__ == "__main__":
    main()
