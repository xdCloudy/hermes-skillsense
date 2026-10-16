"""Fast, deterministic, no-model/no-network skill hint retrieval."""
from __future__ import annotations
from collections import Counter
import re
import threading
from .core import BM25Index, Document, tokenize
import hashlib
import time
from .catalog import clean_text
from .store import read_index, read_native_snapshot
from .eligibility import compose_native_records

def _phrase_in_tokens(phrase: str, query_tokens: tuple[str, ...]) -> bool:
    """Require complete adjacent tokens, not substrings inside larger words."""
    parts = tokenize(phrase)
    n = len(parts)
    return bool(n and n <= len(query_tokens)
                and any(query_tokens[i:i+n] == parts
                        for i in range(len(query_tokens)-n+1)))


class Router:
    def __init__(self, records: list[dict]):
        self.records = {str(r["id"]):r for r in records if isinstance(r,dict)
                        and isinstance(r.get("id"),str) and isinstance(r.get("name"),str)}
        self._name_counts = Counter(r["name"] for r in self.records.values())
        self.index = BM25Index(Document(identity,
            " ".join([r.get("name","")]*5
                     + [r.get("description","")]*2
                     + list(r.get("tags") or [])*3
                     + list(r.get("aliases") or [])*3
                     + list(r.get("intents") or [])))
                     for identity,r in self.records.items())

    def suggest(self, query: str, max_suggestions: int = 2) -> str | None:
        # Hermes can provide multimodal turns as lists of content parts.
        # Never stringify attachments or non-text objects for retrieval.
        if not isinstance(query, str) or not query.strip() or not self.records:
            return None
        # Bound work BEFORE Unicode normalization on arbitrarily large turns.
        query = clean_text(query[:2000], 1000)
        ordered_tokens = tokenize(query)
        query_tokens = set(ordered_tokens)
        candidates = self.index.search(query, limit=6)
        if not candidates:
            return None
        # We deliberately do NOT use the raw BM25 score as calibrated confidence.
        top = candidates[0]
        primary = self.records[top.skill_id]
        if self._name_counts[primary["name"]] != 1:
            return None  # Duplicate names need native Hermes precedence resolution.
        n = primary["name"].replace("-", " ")
        aliases = [str(a) for a in primary.get("aliases") or []]
        exact = (_phrase_in_tokens(n, ordered_tokens)
                 or _phrase_in_tokens(primary["name"], ordered_tokens)
                 or any(len(a) >= 4 and _phrase_in_tokens(a, ordered_tokens)
                        for a in aliases))
        # Explicitly approved negative intent examples veto an otherwise strong
        # match. A single generic negative word is insufficient for a veto.
        if any(len(tokenize(negative)) >= 2
               and _phrase_in_tokens(negative, ordered_tokens)
               for negative in primary.get("negative_intents") or []):
            return None
        source_tokens = set(tokenize(" ".join([primary["name"],
                               primary.get("description","")] + list(primary.get("tags") or []))))
        evidence = len(source_tokens & query_tokens)
        if not exact and evidence < 2:
            return None
        if len(candidates) > 1 and not exact and candidates[1].score >= top.score * 0.85:
            return None
        count = min(max(1,int(max_suggestions)),3)
        selected = [top]  # Default to one precise hint; do not force top-K.
        seen = {primary["name"]}
        if count > 1 and len(candidates) > 1:
            for c in candidates[1:]:
                if c.score < top.score * 0.8:
                    break
                r = self.records[c.skill_id]
                if (r["name"] not in seen
                    and self._name_counts[r["name"]] == 1
                    and len(set(tokenize(r["name"])) & query_tokens) >= 1
                    and not any(len(tokenize(negative)) >= 2
                                and _phrase_in_tokens(negative, ordered_tokens)
                                for negative in r.get("negative_intents") or [])):
                    selected.append(c)
                    seen.add(r["name"])
                    break
        names = []
        for c in selected[:count]:
            r = self.records[c.skill_id]
            title = clean_text(r["name"], 65)
            terms = sorted(set(tokenize(" ".join([r.get("description","")] + list(r.get("tags") or [])))) & query_tokens)[:3]
            # Never inject untrusted skill descriptions or instructions directly.
            names.append("- " + title + (" (matched: " + ", ".join(terms) + ")" if terms else ""))
        return "Potentially relevant installed skills (verify availability; open with skill_view if needed):\n" + "\n".join(names)

_cache: Router | None = None
_cache_refreshed = 0.0
_CACHE_REFRESH_SECONDS = 60.0
_lock = threading.Lock()
_recent_lock = threading.Lock()
_recent: dict[str, tuple[str,float]] = {}

def get_router() -> Router:
    """Recheck index/snapshot once a minute; never trust expired eligibility forever."""
    global _cache, _cache_refreshed
    now = time.monotonic()
    if _cache is None or now - _cache_refreshed >= _CACHE_REFRESH_SECONDS:
        with _lock:
            now = time.monotonic()
            if _cache is None or now - _cache_refreshed >= _CACHE_REFRESH_SECONDS:
                _cache = Router(compose_native_records(read_index(), read_native_snapshot()))
                _cache_refreshed = now
    return _cache

def clear_cache() -> None:
    global _cache, _cache_refreshed
    with _lock:
        _cache = None
        _cache_refreshed = 0.0

def hint(user_message: str, max_suggestions: int = 2, session_id: str = "") -> dict | None:
    try:
        value = get_router().suggest(user_message, max_suggestions)
        if not value:
            return None
        if session_id:
            fingerprint = hashlib.sha256(value.encode("utf-8")).hexdigest()
            now = time.monotonic()
            with _recent_lock:
                old = _recent.get(str(session_id))
                if old and old[0] == fingerprint and now - old[1] < 300:
                    return None
                if len(_recent) >= 256:
                    _recent.clear()
                _recent[str(session_id)] = (fingerprint, now)
        return {"context": value}
    except Exception:
        # A broken cache must never fail a Hermes turn.
        return None
