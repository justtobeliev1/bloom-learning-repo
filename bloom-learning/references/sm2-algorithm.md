# SM-2 Spaced Repetition Algorithm

Reference for the simplified SM-2 algorithm used in this learning system.

## Table of Contents

1. [Overview](#overview)
2. [Core Parameters](#core-parameters)
3. [Algorithm Rules](#algorithm-rules)
4. [Examples](#examples)
5. [Integration with review-check.py](#integration-with-review-checkpy)

## Overview

SM-2 (SuperMemo 2) is a spaced repetition algorithm that calculates optimal review intervals based on how well you remember each item. We use a simplified version that tracks two variables per concept: **interval** (days until next review) and **ease factor** (multiplier for interval growth).

The core insight: items you remember well get reviewed less frequently; items you struggle with get reviewed sooner.

## Core Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| **Interval** | Days until next review | 1 | 1 to unlimited |
| **Ease Factor** | Multiplier for interval growth | 2.5 | 1.3 to 3.0 |

## Algorithm Rules

### On Correct Answer

1. If interval = 1 day (first review): set interval to **3 days**
2. Otherwise: `new_interval = previous_interval * ease_factor` (rounded)
3. Increase ease: `new_ease = min(3.0, ease + 0.1)`

### On Wrong Answer

1. Reset interval to **1 day** (review again tomorrow)
2. Decrease ease: `new_ease = max(1.3, ease - 0.2)`

### Mastery Threshold

When a concept's interval exceeds **30 days**, move it from "Due for Review" to "Mastered" in `_meta/state.json`, then regenerate `spaced-repetition.md`. Mastered items are still tracked but reviewed less frequently.

## Examples

### Example 1: Smooth Learning

A concept "recursion" with default ease (2.5):

| Review # | Correct? | Old Interval | New Interval | Ease |
|----------|----------|-------------|-------------|------|
| 1 | Yes | 1 day | 3 days | 2.6 |
| 2 | Yes | 3 days | 8 days | 2.7 |
| 3 | Yes | 8 days | 22 days | 2.8 |
| 4 | Yes | 22 days | 62 days | 2.9 |
| → Mastered (62 > 30) |

### Example 2: With a Stumble

A concept "closures" where the learner forgets once:

| Review # | Correct? | Old Interval | New Interval | Ease |
|----------|----------|-------------|-------------|------|
| 1 | Yes | 1 day | 3 days | 2.6 |
| 2 | No | 3 days | 1 day | 2.4 |
| 3 | Yes | 1 day | 3 days | 2.5 |
| 4 | Yes | 3 days | 8 days | 2.6 |
| 5 | Yes | 8 days | 21 days | 2.7 |
| 6 | Yes | 21 days | 57 days | 2.8 |
| → Mastered |

### Example 3: Persistent Difficulty

A concept that the learner repeatedly forgets:

| Review # | Correct? | Old Interval | New Interval | Ease |
|----------|----------|-------------|-------------|------|
| 1 | No | 1 day | 1 day | 2.3 |
| 2 | No | 1 day | 1 day | 2.1 |
| 3 | Yes | 1 day | 3 days | 2.2 |
| 4 | No | 3 days | 1 day | 2.0 |

Notice ease drops quickly with repeated failures, making future intervals grow more slowly even after correct answers. This is intentional — difficult concepts get more frequent review.

## Integration with review-check.py

The `scripts/review-check.py` script automates this algorithm and keeps `_meta/state.json` in sync:

```bash
# Check what's due today
python3 scripts/review-check.py ./_meta/spaced-repetition.md

# Update after review (concept correct: true, another wrong: false)
python3 scripts/review-check.py ./_meta/spaced-repetition.md \
    --update --results '{"recursion": true, "closures": false}'

# Check with a specific date (for testing)
python3 scripts/review-check.py ./_meta/spaced-repetition.md --date 2025-03-20

# Rebuild the rendered markdown from state.json
python3 scripts/review-check.py ./_meta/spaced-repetition.md --sync
```

The script treats `_meta/state.json` as the source of truth, applies the SM-2 rules there, and writes the rendered schedule back to `spaced-repetition.md`.
