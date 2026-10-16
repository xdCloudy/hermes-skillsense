"""Canonical Hermes skill eligibility adapter.

This adapter uses Hermes' own public skill listing rather than reimplementing
platform, environment, app, disabled, project or plugin precedence rules.
It is invoked once per agent/router startup, NEVER on every turn.
"""
from __future__ import annotations

from collections import Counter
import json
from typing import Any


def native_skill_allowlist() -> dict[str, str]:
    """Return loadable skill names -> their native descriptions.

    Empty mapping means no skills can be verified; never fall back to a raw
    filesystem list. Hermes can legitimately return an empty catalogue.
    """
    try:
        from tools.skills_tool import skills_list  # Host-only import.
        raw = skills_list()
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("success") is not True:
            return {}
        entries = data.get("skills")
        if not isinstance(entries, list):
            return {}
        parsed: list[tuple[str, str]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name, desc = entry.get("name"), entry.get("description", "")
            if (not isinstance(name, str) or not name or len(name) > 200
                    or not isinstance(desc, str)):
                continue
            parsed.append((name, desc))
        duplicates = Counter(name for name, _ in parsed)
        return {name: desc for name, desc in parsed if duplicates[name] == 1}
    except Exception:
        # A plugin must not break inference if Hermes catalogue access fails.
        return {}


def filter_index_to_native(records: list[dict], available: dict[str, str]) -> list[dict]:
    """Keep only unambiguous, verifiably present Hermes load names.

    Source descriptions must match Hermes' own catalogue to prevent
    misattributing an alias to a shadowed/project skill. The native list
    truncates descriptions at 1024 chars; our source values are shorter.
    Missing descriptions cannot be safely attributed; do not suggest them.
    """
    if not available:
        return []
    eligible: list[dict] = []
    counts = Counter(str(r.get("name")) for r in records if isinstance(r,dict))
    for record in records:
        if not isinstance(record,dict):
            continue
        name = record.get("name")
        source = record.get("source_description")
        if (not isinstance(name,str) or counts[name] != 1
                or name not in available or not isinstance(source,str) or not source):
            continue
        # Preserve Hermes case-insensitive comparisons for ordinary short descriptions.
        if source.strip().casefold() != available[name].strip().casefold():
            continue
        eligible.append(record)
    return eligible
