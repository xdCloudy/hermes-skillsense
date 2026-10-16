"""Pure, dependency-free BM25 search primitives for SkillSense.

This core deliberately has no Hermes imports, filesystem activity, model calls,
network access, or state persistence. The live plugin does NOT use it yet.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Iterable

_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text: str) -> tuple[str, ...]:
    """Normalize Unicode words; punctuation and underscores split terms."""
    return tuple(_TOKEN.findall((text or "").casefold()))


@dataclass(frozen=True)
class Document:
    skill_id: str
    text: str


@dataclass(frozen=True)
class Match:
    skill_id: str
    score: float


class BM25Index:
    """Small immutable ranking index with deterministic tie ordering."""

    def __init__(self, documents: Iterable[Document], *, k1: float = 1.2, b: float = 0.75):
        if not (math.isfinite(k1) and k1 > 0):
            raise ValueError("k1 must be positive and finite")
        if not (math.isfinite(b) and 0 <= b <= 1):
            raise ValueError("b must be finite and between 0 and 1")
        docs = tuple(documents)
        if len({d.skill_id for d in docs}) != len(docs):
            raise ValueError("duplicate skill_id")
        if any(not d.skill_id or not isinstance(d.text, str) for d in docs):
            raise ValueError("documents require an ID and text")
        self._k1, self._b = k1, b
        self._ids = tuple(d.skill_id for d in docs)
        self._counts = tuple(Counter(tokenize(d.text)) for d in docs)
        self._lengths = tuple(sum(freq.values()) for freq in self._counts)
        self._mean_length = sum(self._lengths) / len(docs) if docs else 0.0
        self._document_frequency = Counter()
        for counts in self._counts:
            self._document_frequency.update(counts.keys())

    def search(self, query: str, *, limit: int = 3) -> list[Match]:
        if limit <= 0 or not self._ids:
            return []
        query_terms = set(tokenize(query))
        if not query_terms:
            return []
        n_docs = len(self._ids)
        results: list[Match] = []
        for skill_id, counts, length in zip(self._ids, self._counts, self._lengths):
            score = 0.0
            normalized_length = length / (self._mean_length or 1)
            for term in query_terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                df = self._document_frequency[term]
                idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                denominator = frequency + self._k1 * (1 - self._b + self._b * normalized_length)
                score += idf * frequency * (self._k1 + 1) / denominator
            if score > 0 and math.isfinite(score):
                results.append(Match(skill_id=skill_id, score=score))
        return sorted(results, key=lambda match: (-match.score, match.skill_id))[:limit]

    @property
    def size(self) -> int:
        return len(self._ids)
