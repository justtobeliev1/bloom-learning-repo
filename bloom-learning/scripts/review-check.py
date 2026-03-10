#!/usr/bin/env python3
"""
review-check.py — Parse spaced-repetition.md and output items due for review today.

Usage:
    python3 review-check.py <path-to-spaced-repetition.md> [--date YYYY-MM-DD] [--update]

Arguments:
    path          Path to the spaced-repetition.md file
    --date        Override today's date (for testing). Default: today
    --update      After review, update intervals in the file (requires --results)
    --results     JSON string of review results: {"concept": true/false, ...}

Output:
    Prints due items as a Markdown checklist. If no items due, prints a message.

Examples:
    python3 review-check.py ./_meta/spaced-repetition.md
    python3 review-check.py ./_meta/spaced-repetition.md --date 2025-03-15
    python3 review-check.py ./_meta/spaced-repetition.md --update --results '{"递归": true, "闭包": false}'
"""

import sys
import re
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path


def parse_table(content: str, header_pattern: str) -> list[dict]:
    """Parse a Markdown table section into a list of dicts."""
    lines = content.split("\n")
    rows = []
    in_section = False
    headers = []

    for line in lines:
        stripped = line.strip()
        if header_pattern in stripped:
            in_section = True
            continue
        if in_section and stripped.startswith("|") and not stripped.startswith("|--"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not headers:
                headers = cells
            else:
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
        elif in_section and stripped.startswith("#") and not stripped.startswith("|"):
            break  # Next section

    return rows


def calculate_next_review(interval_days: int, ease: float, correct: bool) -> tuple[int, float]:
    """Calculate next interval and ease factor using simplified SM-2."""
    if not correct:
        return 1, max(1.3, ease - 0.2)

    if interval_days <= 1:
        new_interval = 3
    else:
        new_interval = round(interval_days * ease)

    new_ease = min(3.0, ease + 0.1)
    return new_interval, new_ease


def get_due_items(file_path: str, check_date: str = None) -> list[dict]:
    """Read spaced-repetition.md and return items due for review."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    today = datetime.strptime(check_date, "%Y-%m-%d").date() if check_date else datetime.now().date()

    rows = parse_table(content, "## Due for Review")
    due = []

    for row in rows:
        next_review_str = row.get("Next review", "").strip()
        if not next_review_str:
            continue
        try:
            next_review = datetime.strptime(next_review_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if next_review <= today:
            due.append(row)

    return due


def update_file(file_path: str, results: dict, check_date: str = None):
    """Update spaced-repetition.md with review results."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    today = check_date or datetime.now().strftime("%Y-%m-%d")
    today_date = datetime.strptime(today, "%Y-%m-%d").date()

    lines = content.split("\n")
    new_lines = []
    in_due_table = False
    headers = []
    header_indices = {}

    for line in lines:
        stripped = line.strip()

        if "## Due for Review" in stripped:
            in_due_table = True
            new_lines.append(line)
            continue

        if in_due_table and stripped.startswith("|") and not stripped.startswith("|--"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]

            if not headers:
                headers = cells
                header_indices = {h: i for i, h in enumerate(headers)}
                new_lines.append(line)
                continue

            concept = cells[header_indices.get("Concept", 0)]

            if concept in results:
                correct = results[concept]
                interval = int(cells[header_indices.get("Interval", 3)] or "1")
                ease = float(cells[header_indices.get("Ease", 4)] or "2.5")

                new_interval, new_ease = calculate_next_review(interval, ease, correct)
                next_date = (today_date + timedelta(days=new_interval)).strftime("%Y-%m-%d")

                cells[header_indices["Last reviewed"]] = today
                cells[header_indices["Next review"]] = next_date
                cells[header_indices["Interval"]] = str(new_interval)
                cells[header_indices["Ease"]] = f"{new_ease:.1f}"

                new_line = "| " + " | ".join(cells) + " |"
                new_lines.append(new_line)
                continue

        if in_due_table and stripped.startswith("#") and not stripped.startswith("|"):
            in_due_table = False

        new_lines.append(line)

    path.write_text("\n".join(new_lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Check and manage spaced repetition reviews")
    parser.add_argument("path", help="Path to spaced-repetition.md")
    parser.add_argument("--date", help="Override today's date (YYYY-MM-DD)", default=None)
    parser.add_argument("--update", action="store_true", help="Update file with review results")
    parser.add_argument("--results", help="JSON: {\"concept\": true/false, ...}", default=None)

    args = parser.parse_args()

    if args.update:
        if not args.results:
            print("Error: --update requires --results", file=sys.stderr)
            sys.exit(1)
        try:
            results = json.loads(args.results)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --results: {e}", file=sys.stderr)
            sys.exit(1)

        update_file(args.path, results, args.date)
        print("Spaced repetition file updated.")
        return

    due_items = get_due_items(args.path, args.date)

    if not due_items:
        print("No items due for review today. Proceed to new material.")
        return

    print(f"## Due for Review Today ({len(due_items)} items)\n")
    for item in due_items:
        concept = item.get("Concept", "Unknown")
        last = item.get("Last reviewed", "?")
        interval = item.get("Interval", "?")
        print(f"- [ ] **{concept}** (last reviewed: {last}, interval: {interval} days)")

    print(f"\nReview these {len(due_items)} items before starting new material.")


if __name__ == "__main__":
    main()
