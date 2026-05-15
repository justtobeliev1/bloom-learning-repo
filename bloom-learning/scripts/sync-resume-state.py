#!/usr/bin/env python3
"""Rebuild lightweight resume files from the canonical Bloom state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from learning_state import load_state, sync_spaced_repetition, write_resume_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync current.md and state-lite.json from state.json")
    parser.add_argument("topic_path", help="Path to the topic directory containing _meta/")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topic_dir = Path(args.topic_path)
    try:
        state = load_state(topic_dir)
        sync_spaced_repetition(topic_dir, state)
        write_resume_state(topic_dir, state)
    except Exception as exc:
        print(f"Error: failed to sync resume state: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
