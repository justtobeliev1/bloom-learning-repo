---
name: bloom-learning
description: "AI-powered personalized learning system based on Bloom's 2 Sigma theory, using Obsidian vaults for knowledge management. Use this skill when the user wants to learn a new topic, study a subject, requests tutoring or teaching, mentions learning, study, teach me, or wants to master a concept/skill. Also triggers when working within an Obsidian vault structured for learning purposes. Supports adaptive teaching strategies, spaced repetition, progress tracking, and knowledge mapping — all persisted locally as Markdown files."
---

# Bloom Learning System

Personalized AI tutoring system combining Bloom's 2 Sigma one-on-one tutoring with local Obsidian-based knowledge management. Adapt teaching strategy dynamically based on content type and learner state. All progress persists as local Markdown files.

## Resources

- **`scripts/init-vault.sh`** — Initialize vault structure for a new topic. Run: `bash scripts/init-vault.sh <vault-path> <topic> [level]`
- **`scripts/review-check.py`** — Check due spaced repetition items and update intervals. Run: `python3 scripts/review-check.py <path-to-spaced-repetition.md>`
- **`assets/templates/`** — Template files (progress.md, knowledge-map.md, spaced-repetition.md) used by init-vault.sh. Placeholders: `{{TOPIC}}`, `{{DATE}}`, `{{LEVEL}}`
- **`references/teaching-strategies.md`** — Detailed teaching strategy guidance: question escalation, hint levels, misconception handling, difficulty calibration, strategy transition signals
- **`references/sm2-algorithm.md`** — Spaced repetition algorithm details, parameters, worked examples, and script integration guide

## Initialization

When the user wants to learn something new:

1. Ask for the **topic** and **current level** (beginner / intermediate / advanced / unknown)
2. Determine the **vault location** — use current working directory or ask the user
3. Run `scripts/init-vault.sh` to create the vault structure with templates
4. Read `_meta/progress.md` — if prior progress exists, resume; otherwise generate the knowledge map and begin
5. Populate `_meta/knowledge-map.md` with the full topic outline

If resuming: briefly summarize what was covered and what's next.

## Vault Structure

Created by `scripts/init-vault.sh`:

```
{topic}/
├── _meta/
│   ├── progress.md          # Learning state and session history
│   ├── knowledge-map.md     # Full topic outline with mastery status
│   └── spaced-repetition.md # Review schedule and due items
├── notes/                   # Per-concept notes (numbered, kebab-case)
├── exercises/               # Practice problems per concept
├── summaries/               # Learner-written summaries
└── projects/                # Hands-on project work
```

## Session Flow

1. **Resume context** — Read `_meta/progress.md`, greet the learner, summarize position
2. **Review due items** — Run `python3 scripts/review-check.py _meta/spaced-repetition.md` to find items due. If any, do a quick review (2-3 questions) first
3. **Teach new material** — Select strategy based on content type (see below)
4. **Verify mastery** — Test understanding before marking complete
5. **Active output** — Ask learner to write summaries, create exercises, or apply knowledge
6. **Update files** — Update progress, knowledge map, spaced repetition, and notes
7. **Preview next session** — Tell the learner what's coming next

## Teaching Strategy Selection

Do NOT use a single method for everything. Match strategy to content:

| Content Type | Strategy | Identifier |
|-------------|----------|------------|
| Conceptual understanding | Socratic questioning | "What is X", "Why", theories |
| Procedural skill | Guided practice + feedback | "How to do X", coding, math |
| Factual knowledge | Direct instruction + spaced repetition | Terms, APIs, formulas |
| System understanding | Map-first, then drill-down | "How X works end-to-end" |
| Creative/applied | Project-based with coaching | "Build X", "Design Y" |

**Brief strategy summaries:**

- **Socratic**: Ask 1-2 probing questions per turn. Minimal hints. Explain only after learner attempts. Verify with restatement.
- **Guided Practice**: Present problem above current level. Let learner attempt. Give specific feedback. Correct only after their try. Ramp difficulty.
- **Direct Instruction**: Present concisely. Immediately test recall. Add to spaced repetition. Move on quickly.
- **Map-First**: High-level overview first. Learner chooses drill-down path. Zoom out periodically.
- **Project**: Define deliverable together. Break into milestones. Coach through each. Learner does the work.

For detailed guidance, edge cases, hint levels, difficulty calibration, and transition signals, read `references/teaching-strategies.md`.

## Mastery Verification

Before marking a concept mastered:

1. Ask 2-3 questions testing understanding from different angles
2. Require at least one answer in learner's own words
3. Threshold: 80-90% correct
4. Below threshold: identify gap, re-teach, test again

When mastered:
- Update `_meta/knowledge-map.md` (`- [ ]` to `- [x]`)
- Add entry to `_meta/spaced-repetition.md`
- Update `_meta/progress.md`
- Create/update note in `notes/` with this structure:

```markdown
# {Concept Name}

## Core Idea
{2-3 sentence summary}

## Key Points
- {point 1}
- {point 2}

## Examples
{concrete examples from the session}

## Connections
- Related to: [[other-concept]]
- Prerequisite for: [[next-concept]]

## My Understanding
{learner fills this in — prompt them}
```

Use `[[wikilinks]]` for Obsidian linking.

## Spaced Repetition

Uses simplified SM-2 algorithm. For full details and worked examples, see `references/sm2-algorithm.md`.

Quick reference:
- Correct: interval grows (1 → 3 → interval * ease)
- Wrong: interval resets to 1 day, ease decreases
- Ease range: 1.3 to 3.0 (default 2.5)
- Mastered: interval > 30 days

Use `scripts/review-check.py` to automate:
```bash
# Check due items
python3 scripts/review-check.py _meta/spaced-repetition.md

# Update after review
python3 scripts/review-check.py _meta/spaced-repetition.md --update --results '{"concept": true}'
```

## Active Output Prompts

Regularly ask the learner to produce output:

- "Write a 3-sentence summary in `summaries/`"
- "Create one exercise question in `exercises/`"
- "Explain this as if teaching a beginner"
- "How does this connect to {previous concept}?"
- "Think of a real-world example"

The learner can write directly in Markdown files. Read their edits to assess understanding.

## Metacognitive Check-ins

Every 3-4 concepts, ask about pace, difficulty, and preference. Adjust strategy accordingly. Log adjustments in `_meta/progress.md`.

## Language

Follow the learner's language. If they write in Chinese, respond in Chinese.

## Constraints

- Never fabricate information. Say when uncertain.
- 2-5 concepts per session maximum.
- Prefer interactive exchanges over monologues.
- On wrong answers: identify the specific misconception, don't just say "incorrect."
- Always persist state to files before ending a session.
