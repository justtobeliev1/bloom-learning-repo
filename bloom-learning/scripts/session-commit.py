#!/usr/bin/env python3
"""Persist Bloom Learning session updates across Markdown files and state.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from learning_state import (
    CURRENT_STATE_END,
    CURRENT_STATE_START,
    MASTERY_SNAPSHOT_END,
    MASTERY_SNAPSHOT_START,
    SESSION_LOG_END,
    SESSION_LOG_START,
    ensure_review_entry,
    iso_today,
    knowledge_map_path_for_topic,
    load_state,
    progress_path_for_topic,
    render_mastery_snapshot,
    render_progress_current_state,
    render_session_log,
    replace_marked_section,
    save_state,
    slugify_note_name,
    sync_spaced_repetition,
    upsert_concept,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Commit a learning session to Bloom Learning files")
    parser.add_argument("topic_path", help="Path to the topic directory containing _meta/")
    parser.add_argument("--payload", required=True, help="JSON payload describing the session update")
    parser.add_argument("--date", default=None, help="Override session date (YYYY-MM-DD)")
    return parser.parse_args()


def load_payload(raw_payload: str) -> dict:
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON payload: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(payload, dict):
        print("Error: payload must be a JSON object", file=sys.stderr)
        sys.exit(1)
    return payload


def ensure_marked_file(path: Path, title: str, start_marker: str, end_marker: str, placeholder_body: str) -> None:
    if path.exists():
        return
    path.write_text(
        f"# {title}\n\n{start_marker}\n{placeholder_body}\n{end_marker}\n",
        encoding="utf-8",
    )


def write_note(topic_dir: Path, concept_payload: dict) -> str:
    concept_name = concept_payload["name"]
    note_path = topic_dir / "notes" / f"{slugify_note_name(concept_name)}.md"
    existing_understanding = concept_payload.get("my_understanding_prompt", "Write your understanding here.")

    if note_path.exists():
        existing_text = note_path.read_text(encoding="utf-8")
        match = re.search(r"## My Understanding\s*\n(.*)", existing_text, re.DOTALL)
        if match and match.group(1).strip():
            existing_understanding = match.group(1).strip()

    key_points = concept_payload.get("key_points") or ["Add key points from the session."]
    examples = concept_payload.get("examples") or ["Add concrete examples from the session."]
    related = concept_payload.get("related") or []
    prerequisite_for = concept_payload.get("prerequisite_for") or []

    note_text = "\n".join(
        [
            f"# {concept_name}",
            "",
            "## Core Idea",
            concept_payload.get("core_idea", "Add a 2-3 sentence summary."),
            "",
            "## Key Points",
            *[f"- {point}" for point in key_points],
            "",
            "## Examples",
            *[f"- {example}" for example in examples],
            "",
            "## Connections",
            *([f"- Related to: [[{item}]]" for item in related] or ["- Related to: [[other-concept]]"]),
            *([f"- Prerequisite for: [[{item}]]" for item in prerequisite_for] or ["- Prerequisite for: [[next-concept]]"]),
            "",
            "## My Understanding",
            existing_understanding,
            "",
        ]
    )
    note_path.write_text(note_text, encoding="utf-8")
    return note_path.relative_to(topic_dir).as_posix()


def update_progress(topic_dir: Path, state: dict) -> None:
    progress_path = progress_path_for_topic(topic_dir)
    ensure_marked_file(
        progress_path,
        f"Learning Progress: {state['topic']}",
        CURRENT_STATE_START,
        CURRENT_STATE_END,
        render_progress_current_state(state),
    )
    text = progress_path.read_text(encoding="utf-8")
    had_session_marker = SESSION_LOG_START in text
    text = replace_marked_section(text, CURRENT_STATE_START, CURRENT_STATE_END, render_progress_current_state(state))
    text = replace_marked_section(text, SESSION_LOG_START, SESSION_LOG_END, render_session_log(state))
    if not had_session_marker:
        text = text.rstrip() + (
            "\n\n## Session Log\n\n"
            f"{SESSION_LOG_START}\n{render_session_log(state)}\n{SESSION_LOG_END}\n"
        )
    progress_path.write_text(text, encoding="utf-8")


def update_knowledge_map(topic_dir: Path, state: dict, mastered_names: list[str]) -> None:
    knowledge_map_path = knowledge_map_path_for_topic(topic_dir)
    ensure_marked_file(
        knowledge_map_path,
        f"Knowledge Map: {state['topic']}",
        MASTERY_SNAPSHOT_START,
        MASTERY_SNAPSHOT_END,
        render_mastery_snapshot(state),
    )

    text = knowledge_map_path.read_text(encoding="utf-8")
    had_mastery_marker = MASTERY_SNAPSHOT_START in text
    lines = text.splitlines()
    lowered_mastered = [name.casefold() for name in mastered_names]
    updated_lines = []
    for line in lines:
        updated_line = line
        for concept_name, concept_key in zip(mastered_names, lowered_mastered):
            if concept_key in line.casefold() and "- [ ]" in line:
                updated_line = line.replace("- [ ]", "- [x]", 1)
                break
        updated_lines.append(updated_line)

    text = "\n".join(updated_lines)
    text = replace_marked_section(text, MASTERY_SNAPSHOT_START, MASTERY_SNAPSHOT_END, render_mastery_snapshot(state))

    if not had_mastery_marker:
        text = text.rstrip() + (
            "\n\n## Mastery Snapshot\n\n"
            f"{MASTERY_SNAPSHOT_START}\n{render_mastery_snapshot(state)}\n{MASTERY_SNAPSHOT_END}\n"
        )
    knowledge_map_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    payload = load_payload(args.payload)
    topic_dir = Path(args.topic_path)
    session_date = args.date or iso_today()

    state = load_state(topic_dir)

    module_name = payload.get("module") or state["current"].get("module", "Module 1")
    concept_name = payload.get("concept") or state["current"].get("concept", "1.1")
    state["current"]["module"] = module_name
    state["current"]["concept"] = concept_name

    learner_updates = payload.get("learner")
    if isinstance(learner_updates, dict):
        state["learner"].update(learner_updates)

    if concept_name:
        upsert_concept(state, concept_name, module=module_name)

    mastered_payloads = payload.get("mastered_concepts", [])
    mastered_names = []

    for item in mastered_payloads:
        concept_payload = {"name": item} if isinstance(item, str) else dict(item)
        concept_payload.setdefault("module", module_name)
        concept_payload.setdefault("core_idea", "Add a 2-3 sentence summary.")
        concept_payload["name"] = str(concept_payload["name"]).strip()
        if not concept_payload["name"]:
            continue

        note_path = write_note(topic_dir, concept_payload)
        upsert_concept(
            state,
            concept_payload["name"],
            module=concept_payload.get("module"),
            status="mastered",
            note_path=note_path,
            related=concept_payload.get("related") or [],
            prerequisite_for=concept_payload.get("prerequisite_for") or [],
        )
        ensure_review_entry(state, concept_payload["name"], session_date)
        mastered_names.append(concept_payload["name"])

    covered_concepts = payload.get("covered_concepts")
    if not isinstance(covered_concepts, list):
        covered_concepts = [concept_name] if concept_name else []

    session_entry = {
        "index": len(state.get("sessions", [])) + 1,
        "date": session_date,
        "summary": payload.get("session_summary", "Session committed."),
        "module": module_name,
        "concept": concept_name,
        "covered_concepts": [item for item in covered_concepts if item],
        "mastered_concepts": mastered_names,
        "struggles": payload.get("struggles", []),
        "wins": payload.get("wins", []),
        "next_session": payload.get("next_session", ""),
    }
    state.setdefault("sessions", []).append(session_entry)

    save_state(topic_dir, state)
    update_progress(topic_dir, state)
    update_knowledge_map(topic_dir, state, mastered_names)
    sync_spaced_repetition(topic_dir, state)

    print("Session committed successfully.")


if __name__ == "__main__":
    main()
