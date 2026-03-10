#!/usr/bin/env python3
"""Check due review items and write results back to Bloom Learning state."""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

from learning_state import load_state, record_review_result, save_state, sync_spaced_repetition, topic_dir_from_path


def main():
    parser = argparse.ArgumentParser(description="Check and manage spaced repetition reviews")
    parser.add_argument("path", help="Path to spaced-repetition.md")
    parser.add_argument("--date", help="Override today's date (YYYY-MM-DD)", default=None)
    parser.add_argument("--update", action="store_true", help="Update file with review results")
    parser.add_argument("--results", help="JSON: {\"concept\": true/false, ...}", default=None)
    parser.add_argument("--sync", action="store_true", help="Regenerate spaced-repetition.md from state.json and exit")

    args = parser.parse_args()
    review_path = Path(args.path)
    if not review_path.exists():
        print(f"Error: File not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    topic_dir = topic_dir_from_path(review_path)
    state = load_state(topic_dir)
    review_date = args.date or datetime.now().strftime("%Y-%m-%d")

    if args.sync:
        sync_spaced_repetition(topic_dir, state)
        print("Spaced repetition file synchronized from state.json.")
        return

    if args.update:
        if not args.results:
            print("Error: --update requires --results", file=sys.stderr)
            sys.exit(1)
        try:
            results = json.loads(args.results)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --results: {e}", file=sys.stderr)
            sys.exit(1)

        for concept, correct in results.items():
            record_review_result(state, concept, bool(correct), review_date)
        save_state(topic_dir, state)
        sync_spaced_repetition(topic_dir, state)
        print("Spaced repetition file updated.")
        return

    due_items = [
        item
        for item in state["reviews"]["due"]
        if item.get("next_review") and item["next_review"] <= review_date
    ]

    if not due_items:
        print("No items due for review today. Proceed to new material.")
        return

    print(f"## Due for Review Today ({len(due_items)} items)\n")
    for item in due_items:
        concept = item.get("concept", "Unknown")
        last = item.get("last_reviewed", "?")
        interval = item.get("interval", "?")
        print(f"- [ ] **{concept}** (last reviewed: {last}, interval: {interval} days)")

    print(f"\nReview these {len(due_items)} items before starting new material.")


if __name__ == "__main__":
    main()
