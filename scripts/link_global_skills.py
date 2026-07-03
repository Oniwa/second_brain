#!/usr/bin/env python3
"""Symlink genuinely cross-project skills from this repo into ~/.claude/commands/
so they stay in lockstep with the canonical, source-controlled copy here.

Idempotent — safe to re-run, including after cloning this repo onto a new machine.
"""
import shutil
from datetime import datetime
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_DIR / ".claude" / "commands"
DEST_DIR = Path.home() / ".claude" / "commands"

# Skills used across projects, not just second_brain (e.g. recap writes to the
# second-brain MCP server, which is registered globally). pan/synth/transcript
# are only ever invoked from within this repo, so they stay repo-local.
GLOBAL_SKILLS = ["recap.md", "grill-me.md"]


def backup(path: Path) -> Path:
    dest = path.with_name(f"{path.name}.bak.{datetime.now():%Y%m%d%H%M%S}")
    shutil.move(str(path), str(dest))
    return dest


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    for skill in GLOBAL_SKILLS:
        src = SRC_DIR / skill
        dest = DEST_DIR / skill

        if not src.exists():
            print(f"skip: {skill} not found in {SRC_DIR}")
            continue

        if dest.is_symlink() and dest.resolve() == src.resolve():
            print(f"ok: {skill} already linked")
            continue

        if dest.exists() or dest.is_symlink():
            backed_up = backup(dest)
            print(f"backed up existing {skill} -> {backed_up}")

        dest.symlink_to(src)
        print(f"linked: {dest} -> {src}")


if __name__ == "__main__":
    main()
