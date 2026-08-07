#!/usr/bin/env python3
"""
Unit tests for the Discord message splitter in digest.py.
Pure logic, no network — run directly: python3 discord/test_digest_chunking.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from digest import split_discord_message, DISCORD_CHUNK_LIMIT


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


def test_short_message_single_chunk():
    message = "Hello, this is a short digest."
    chunks = split_discord_message(message)
    check("short message returns one chunk", chunks == [message])


def test_every_chunk_under_limit():
    message = ("This is a paragraph of digest content. " * 200) + "\n\n" + \
               ("Another paragraph follows here too. " * 200)
    chunks = split_discord_message(message)
    check("every chunk <= limit", all(len(c) <= DISCORD_CHUNK_LIMIT for c in chunks))


def test_reassembly_lossless():
    message = ("Paragraph one.\n\n" * 100) + ("Line two.\n" * 100) + ("word " * 500)
    chunks = split_discord_message(message)
    check("join(chunks) == original message", "".join(chunks) == message)


def test_no_mid_word_split_when_boundary_available():
    words = ["alpha", "beta", "gamma", "delta", "epsilon"] * 100
    message = " ".join(words)
    chunks = split_discord_message(message)
    ok = True
    for i in range(len(chunks) - 1):
        # A boundary split consumes the trailing whitespace/newline into the
        # earlier chunk, so the next chunk should never start mid-word.
        if chunks[i + 1] and not chunks[i + 1][0].isspace():
            prev_char = chunks[i][-1]
            if prev_char not in (" ", "\n"):
                ok = False
    check("no chunk starts mid-word when a boundary existed", ok)


def test_single_overlong_line_still_splits():
    message = "x" * 5000  # one line, no spaces/newlines at all
    chunks = split_discord_message(message)
    check("overlong single line splits into multiple chunks", len(chunks) > 1)
    check("overlong-line chunks still <= limit", all(len(c) <= DISCORD_CHUNK_LIMIT for c in chunks))
    check("overlong-line reassembly lossless", "".join(chunks) == message)


def test_prefers_paragraph_over_line_over_word_boundary():
    # Construct a message where a paragraph break falls within the window.
    message = ("a" * 1000) + "\n\n" + ("b" * 1000)
    chunks = split_discord_message(message, limit=1500)
    check("splits on paragraph boundary when available", chunks[0] == ("a" * 1000) + "\n\n")


if __name__ == "__main__":
    test_short_message_single_chunk()
    test_every_chunk_under_limit()
    test_reassembly_lossless()
    test_no_mid_word_split_when_boundary_available()
    test_single_overlong_line_still_splits()
    test_prefers_paragraph_over_line_over_word_boundary()
    print("\nAll digest chunking tests passed.")
