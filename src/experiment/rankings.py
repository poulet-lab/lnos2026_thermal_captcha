"""Rankings and score comparisons."""

from __future__ import annotations

from collections import Counter, defaultdict

from .responses import load_responses


def person_scores(exclude_person: int | None = None) -> dict[int, int]:
    rows = load_responses()
    scores: dict[int, int] = defaultdict(int)
    for row in rows:
        person = int(row["person"])
        if exclude_person is not None and person == exclude_person:
            continue
        if row.get("correct", "").lower() == "true":
            scores[person] += 1
    return dict(scores)


def score_distribution(exclude_person: int | None = None) -> Counter[int]:
    """How many people got each score (0–10), optionally excluding one person."""
    scores = person_scores(exclude_person=exclude_person)
    all_people = {
        int(r["person"])
        for r in load_responses()
        if exclude_person is None or int(r["person"]) != exclude_person
    }
    dist: Counter[int] = Counter()
    for person in all_people:
        dist[scores.get(person, 0)] += 1
    return dist


def score_comparison(score: int, exclude_person: int) -> tuple[int, int, int]:
    """Return (above, same, below) counts for other people only."""
    dist = score_distribution(exclude_person=exclude_person)
    above = sum(count for s, count in dist.items() if s > score)
    same = dist.get(score, 0)
    below = sum(count for s, count in dist.items() if s < score)
    return above, same, below


def is_first_player(exclude_person: int) -> bool:
    """True when no other people have played besides exclude_person."""
    others = {
        int(r["person"])
        for r in load_responses()
        if int(r["person"]) != exclude_person
    }
    return len(others) == 0


def stimulus_trace_ranking() -> list[tuple[str, int]]:
    """Raw count of correct identifications per stimulus name."""
    rows = load_responses()
    counts: Counter[str] = Counter()
    for row in rows:
        if row.get("correct", "").lower() == "true":
            counts[row["stimulus_type"]] += 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))
