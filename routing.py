"""Fast, deterministic, no-model/no-network skill hint retrieval."""
from __future__ import annotations
from collections import Counter
import re
import threading
from .core import BM25Index, Document, tokenize
import hashlib
import time
from .catalog import clean_text
from .store import read_index

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
        if not query or not self.records:
            return None
        query = clean_text(query, 1000)
        query_tokens = set(tokenize(query))
        candidates = self.index.search(query, limit=6)
        if not candidates:
            return None
        # We deliberately do NOT use the raw BM25 score as calibrated confidence.
        top = candidates[0]
        primary = self.records[top.skill_id]
        if self._name_counts[primary["name"]] != 1:
            return None  # Duplicate names need native Hermes precedence resolution.
        n = primary["name"].replace("-", " ")
        aliases = [str(a).lower() for a in primary.get("aliases") or []]
        exact = (n.lower() in query.lower() or primary["name"].lower() in query.lower()
                 or any(len(a) >= 4 and a in query.lower() for a in aliases))
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
                if r["name"] not in seen and len(set(tokenize(r["name"])) & query_tokens) >= 1:
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
_lock = threading.Lock()
_recent_lock = threading.Lock()
_recent: dict[str, tuple[str,float]] = {}

def get_router() -> Router:
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                _cache = Router(read_index())
    return _cache

def clear_cache() -> None:
    global _cache
    with _lock:
        _cache = None

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
