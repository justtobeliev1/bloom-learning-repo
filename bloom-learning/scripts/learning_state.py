#!/usr/bin/env python3
"""Shared helpers for Bloom Learning state management."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_EASE = 2.5
MASTERY_INTERVAL_DAYS = 30

CURRENT_STATE_START = "<!-- BLOOM:CURRENT_STATE:START -->"
CURRENT_STATE_END = "<!-- BLOOM:CURRENT_STATE:END -->"
SESSION_LOG_START = "<!-- BLOOM:SESSION_LOG:START -->"
SESSION_LOG_END = "<!-- BLOOM:SESSION_LOG:END -->"
MASTERY_SNAPSHOT_START = "<!-- BLOOM:MASTERY_SNAPSHOT:START -->"
MASTERY_SNAPSHOT_END = "<!-- BLOOM:MASTERY_SNAPSHOT:END -->"


def iso_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def default_state(topic: str, level: str, date_str: str | None = None) -> dict:
    created_at = date_str or iso_today()
    return {
        "version": 2,
        "topic": topic,
        "created_at": created_at,
        "updated_at": created_at,
        "learner": {
            "level": level,
            "language": "auto",
            "pace": "adaptive",
            "preferences": [],
        },
        "current": {"module": "Module 1", "concept": "1.1"},
        "concepts": {},
        "reviews": {"due": [], "mastered": []},
        "sessions": [],
    }


def topic_dir_from_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir() and (candidate / "_meta").exists():
        return candidate
    if candidate.name == "_meta":
        return candidate.parent
    return candidate.parent.parent


def state_path_for_topic(topic_dir: str | Path) -> Path:
    return Path(topic_dir) / "_meta" / "state.json"


def progress_path_for_topic(topic_dir: str | Path) -> Path:
    return Path(topic_dir) / "_meta" / "progress.md"


def knowledge_map_path_for_topic(topic_dir: str | Path) -> Path:
    return Path(topic_dir) / "_meta" / "knowledge-map.md"


def review_path_for_topic(topic_dir: str | Path) -> Path:
    return Path(topic_dir) / "_meta" / "spaced-repetition.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_state_shape(state: dict) -> dict:
    state.setdefault("version", 2)
    state.setdefault("topic", "Untitled Topic")
    state.setdefault("created_at", iso_today())
    state.setdefault("updated_at", iso_today())
    learner = state.setdefault("learner", {})
    learner.setdefault("level", "unknown")
    learner.setdefault("language", "auto")
    learner.setdefault("pace", "adaptive")
    learner.setdefault("preferences", [])
    current = state.setdefault("current", {})
    current.setdefault("module", "Module 1")
    current.setdefault("concept", "1.1")
    state.setdefault("concepts", {})
    reviews = state.setdefault("reviews", {})
    reviews.setdefault("due", [])
    reviews.setdefault("mastered", [])
    state.setdefault("sessions", [])

    for bucket in ("due", "mastered"):
        reviews[bucket] = [normalize_review_item(item) for item in reviews[bucket]]

    sort_reviews(state)
    return state


def load_state(topic_dir: str | Path) -> dict:
    path = state_path_for_topic(topic_dir)
    if path.exists():
        return ensure_state_shape(load_json(path))

    topic_dir = Path(topic_dir)
    review_path = review_path_for_topic(topic_dir)
    if review_path.exists():
        state = bootstrap_state_from_markdown(topic_dir)
        save_state(topic_dir, state)
        return state

    raise FileNotFoundError(f"State file not found: {path}")


def save_state(topic_dir: str | Path, state: dict) -> None:
    state["updated_at"] = iso_today()
    save_json(state_path_for_topic(topic_dir), ensure_state_shape(state))


def normalize_review_item(item: dict) -> dict:
    normalized = {
        "concept": str(item.get("concept", "")).strip(),
        "last_reviewed": str(item.get("last_reviewed", "")).strip(),
        "next_review": str(item.get("next_review", "")).strip(),
        "interval": int(float(item.get("interval", 1) or 1)),
        "ease": round(float(item.get("ease", DEFAULT_EASE) or DEFAULT_EASE), 1),
    }
    return normalized


def calculate_next_review(interval_days: int, ease: float, correct: bool) -> tuple[int, float]:
    if not correct:
        return 1, max(1.3, round(ease - 0.2, 1))

    if interval_days <= 1:
        new_interval = 3
    else:
        new_interval = round(interval_days * ease)

    new_ease = min(3.0, round(ease + 0.1, 1))
    return new_interval, new_ease


def _review_sort_key(item: dict):
    next_review = item.get("next_review") or "9999-12-31"
    return (next_review, item.get("concept", "").casefold())


def sort_reviews(state: dict) -> None:
    reviews = state["reviews"]
    reviews["due"] = sorted(reviews.get("due", []), key=_review_sort_key)
    reviews["mastered"] = sorted(reviews.get("mastered", []), key=lambda item: item.get("concept", "").casefold())


def _remove_concept_from_reviews(state: dict, concept: str) -> dict | None:
    removed_item = None
    for bucket in ("due", "mastered"):
        remaining = []
        for item in state["reviews"][bucket]:
            if item.get("concept") == concept:
                removed_item = item
            else:
                remaining.append(item)
        state["reviews"][bucket] = remaining
    return removed_item


def set_review_item(state: dict, item: dict, target_bucket: str) -> None:
    item = normalize_review_item(item)
    _remove_concept_from_reviews(state, item["concept"])
    state["reviews"][target_bucket].append(item)
    sort_reviews(state)


def ensure_review_entry(state: dict, concept: str, review_date: str) -> None:
    if find_review_item(state, concept):
        return
    next_review = (parse_date(review_date) + timedelta(days=1)).strftime("%Y-%m-%d")
    set_review_item(
        state,
        {
            "concept": concept,
            "last_reviewed": review_date,
            "next_review": next_review,
            "interval": 1,
            "ease": DEFAULT_EASE,
        },
        "due",
    )


def record_review_result(state: dict, concept: str, correct: bool, review_date: str) -> dict:
    existing = find_review_item(state, concept) or {
        "concept": concept,
        "last_reviewed": review_date,
        "next_review": review_date,
        "interval": 1,
        "ease": DEFAULT_EASE,
    }
    new_interval, new_ease = calculate_next_review(existing["interval"], existing["ease"], correct)
    updated = {
        "concept": concept,
        "last_reviewed": review_date,
        "next_review": (parse_date(review_date) + timedelta(days=new_interval)).strftime("%Y-%m-%d"),
        "interval": new_interval,
        "ease": new_ease,
    }
    target_bucket = "mastered" if new_interval > MASTERY_INTERVAL_DAYS else "due"
    set_review_item(state, updated, target_bucket)
    return updated


def migrate_mastered(state: dict) -> None:
    for item in list(state["reviews"]["due"]):
        if item["interval"] > MASTERY_INTERVAL_DAYS:
            set_review_item(state, item, "mastered")
    sort_reviews(state)


def find_review_item(state: dict, concept: str) -> dict | None:
    for bucket in ("due", "mastered"):
        for item in state["reviews"][bucket]:
            if item.get("concept") == concept:
                return item
    return None


def upsert_concept(
    state: dict,
    concept: str,
    module: str | None = None,
    status: str | None = None,
    note_path: str | None = None,
    related: list[str] | None = None,
    prerequisite_for: list[str] | None = None,
) -> dict:
    concepts = state.setdefault("concepts", {})
    entry = concepts.setdefault(concept, {})
    entry.setdefault("status", "learning")
    entry.setdefault("module", module or state["current"].get("module", "Module 1"))
    entry.setdefault("note_path", note_path or "")
    entry.setdefault("connections", {"related": [], "prerequisite_for": []})
    if module:
        entry["module"] = module
    if status:
        entry["status"] = status
    if note_path:
        entry["note_path"] = note_path
    if related is not None:
        entry["connections"]["related"] = related
    if prerequisite_for is not None:
        entry["connections"]["prerequisite_for"] = prerequisite_for
    entry["updated_at"] = iso_today()
    return entry


def slugify_note_name(value: str) -> str:
    sanitized = value.strip().replace("/", "-")
    sanitized = re.sub(r"\s+", "-", sanitized)
    sanitized = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", sanitized, flags=re.UNICODE)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    return sanitized or "concept-note"


def render_spaced_repetition_markdown(state: dict) -> str:
    migrate_mastered(state)
    lines = [
        "# Spaced Repetition Schedule",
        "",
        "> Generated from `_meta/state.json`. Update reviews via `scripts/review-check.py` or `scripts/session-commit.py`.",
        "",
        "## Due for Review",
        "| Concept | Last reviewed | Next review | Interval | Ease |",
        "|---------|---------------|-------------|----------|------|",
    ]

    for item in state["reviews"]["due"]:
        lines.append(
            f"| {item['concept']} | {item['last_reviewed']} | {item['next_review']} | {item['interval']} | {item['ease']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Mastered (interval > 30 days)",
            "| Concept | Last reviewed | Next review | Interval | Ease |",
            "|---------|---------------|-------------|----------|------|",
        ]
    )

    for item in state["reviews"]["mastered"]:
        lines.append(
            f"| {item['concept']} | {item['last_reviewed']} | {item['next_review']} | {item['interval']} | {item['ease']:.1f} |"
        )

    return "\n".join(lines) + "\n"


def sync_spaced_repetition(topic_dir: str | Path, state: dict | None = None) -> None:
    current_state = ensure_state_shape(state or load_state(topic_dir))
    migrate_mastered(current_state)
    save_state(topic_dir, current_state)
    review_path_for_topic(topic_dir).write_text(
        render_spaced_repetition_markdown(current_state),
        encoding="utf-8",
    )


def render_progress_current_state(state: dict) -> str:
    total_concepts = len(state["concepts"])
    mastered_count = sum(1 for concept in state["concepts"].values() if concept.get("status") == "mastered")
    total_text = str(total_concepts) if total_concepts else "?"
    last_session = state["sessions"][-1]["date"] if state["sessions"] else state.get("created_at", iso_today())
    return "\n".join(
        [
            f"- **Current module**: {state['current'].get('module', 'Module 1')}",
            f"- **Current concept**: {state['current'].get('concept', '1.1')}",
            f"- **Overall mastery**: {mastered_count}/{total_text} concepts mastered",
            f"- **Session count**: {len(state['sessions'])}",
            f"- **Last session**: {last_session}",
            f"- **Learner level**: {state['learner'].get('level', 'unknown')}",
        ]
    )


def render_session_log(state: dict) -> str:
    sessions = state.get("sessions", [])
    if not sessions:
        return (
            "> Sessions will be logged here as learning progresses.\n"
            "> Each session records concepts covered, mastery results, struggles, and next plans."
        )

    blocks = []
    for session in reversed(sessions):
        blocks.extend(
            [
                f"### Session {session.get('index', '?')} - {session.get('date', iso_today())}",
                f"- Summary: {session.get('summary', 'N/A')}",
                f"- Module: {session.get('module', 'N/A')}",
                f"- Concept: {session.get('concept', 'N/A')}",
            ]
        )

        covered = session.get("covered_concepts", [])
        if covered:
            blocks.append(f"- Covered concepts: {', '.join(covered)}")

        mastered = session.get("mastered_concepts", [])
        if mastered:
            blocks.append(f"- Mastered: {', '.join(mastered)}")

        struggles = session.get("struggles", [])
        if struggles:
            blocks.append(f"- Struggles: {'; '.join(struggles)}")

        wins = session.get("wins", [])
        if wins:
            blocks.append(f"- Wins: {'; '.join(wins)}")

        if session.get("next_session"):
            blocks.append(f"- Next session: {session['next_session']}")

        blocks.append("")

    return "\n".join(blocks).rstrip()


def render_mastery_snapshot(state: dict) -> str:
    entries = []
    for concept_name, concept in sorted(state["concepts"].items(), key=lambda pair: pair[0].casefold()):
        checkbox = "x" if concept.get("status") == "mastered" else " "
        module = concept.get("module", "Module 1")
        entries.append(f"- [{checkbox}] {concept_name} ({module})")
    if not entries:
        entries.append("- [ ] No concepts tracked yet")
    return "\n".join(entries)


def replace_marked_section(text: str, start_marker: str, end_marker: str, body: str) -> str:
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    replacement = f"{start_marker}\n{body}\n{end_marker}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + f"\n\n{replacement}\n"


def parse_markdown_table(section_text: str) -> list[dict]:
    headers = None
    rows = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
        if not headers:
            headers = cells
            continue
        if all(not cell or set(cell) <= {"-"} for cell in cells):
            continue
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def _extract_section(content: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(content)
    return match.group(1) if match else ""


def bootstrap_state_from_markdown(topic_dir: str | Path) -> dict:
    topic_dir = Path(topic_dir)
    review_path = review_path_for_topic(topic_dir)
    progress_path = progress_path_for_topic(topic_dir)
    level = "unknown"
    current_module = "Module 1"
    current_concept = "1.1"

    if progress_path.exists():
        progress_text = progress_path.read_text(encoding="utf-8")
        level_match = re.search(r"\*\*Learner level\*\*:\s*(.+)", progress_text)
        module_match = re.search(r"\*\*Current module\*\*:\s*(.+)", progress_text)
        concept_match = re.search(r"\*\*Current concept\*\*:\s*(.+)", progress_text)
        if level_match:
            level = level_match.group(1).strip()
        if module_match:
            current_module = module_match.group(1).strip()
        if concept_match:
            current_concept = concept_match.group(1).strip()

    state = default_state(topic_dir.name, level, iso_today())
    state["current"]["module"] = current_module
    state["current"]["concept"] = current_concept

    if not review_path.exists():
        return state

    content = review_path.read_text(encoding="utf-8")
    due_rows = parse_markdown_table(_extract_section(content, "## Due for Review"))
    mastered_rows = parse_markdown_table(_extract_section(content, "## Mastered (interval > 30 days)"))

    for row in due_rows:
        concept = row.get("Concept", "").strip()
        if not concept:
            continue
        item = normalize_review_item(
            {
                "concept": concept,
                "last_reviewed": row.get("Last reviewed", ""),
                "next_review": row.get("Next review", ""),
                "interval": row.get("Interval", 1),
                "ease": row.get("Ease", DEFAULT_EASE),
            }
        )
        state["reviews"]["due"].append(item)
        upsert_concept(state, concept)

    for row in mastered_rows:
        concept = row.get("Concept", "").strip()
        if not concept:
            continue
        item = normalize_review_item(
            {
                "concept": concept,
                "last_reviewed": row.get("Last reviewed", ""),
                "next_review": row.get("Next review", ""),
                "interval": row.get("Interval", MASTERY_INTERVAL_DAYS + 1),
                "ease": row.get("Ease", DEFAULT_EASE),
            }
        )
        state["reviews"]["mastered"].append(item)
        upsert_concept(state, concept, status="mastered")

    sort_reviews(state)
    return state
