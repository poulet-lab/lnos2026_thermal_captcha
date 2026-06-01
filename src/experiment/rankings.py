"""Rankings and score comparisons."""

from __future__ import annotations

from collections import Counter, defaultdict

from .globals import TRIALS_PER_PERSON
from .responses import load_responses


def person_scores() -> dict[int, int]:
    rows = load_responses()
    scores: dict[int, int] = defaultdict(int)
    for row in rows:
        if row.get("correct", "").lower() == "true":
            scores[int(row["person"])] += 1
    return dict(scores)


def score_distribution() -> Counter[int]:
    """How many people got each score (0–TRIALS_PER_PERSON)."""
    scores = person_scores()
    all_people = {int(r["person"]) for r in load_responses()}
    dist: Counter[int] = Counter()
    for person in all_people:
        dist[scores.get(person, 0)] += 1
    return dist


def score_comparison(score: int) -> tuple[int, int, int]:
    """Return (above, same, below) counts including current person."""
    dist = score_distribution()
    above = sum(count for s, count in dist.items() if s > score)
    same = dist.get(score, 0)
    below = sum(count for s, count in dist.items() if s < score)
    return above, same, below


def stimulus_trace_ranking() -> list[tuple[str, int]]:
    """Raw count of correct identifications per stimulus name."""
    rows = load_responses()
    counts: Counter[str] = Counter()
    for row in rows:
        if row.get("correct", "").lower() == "true":
            counts[row["stimulus_type"]] += 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))
