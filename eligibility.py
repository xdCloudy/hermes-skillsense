"""Canonical Hermes skill eligibility adapter.

This adapter uses Hermes' own public skill listing rather than reimplementing
platform, environment, app, disabled, project or plugin precedence rules.
It is invoked once per agent/router startup, NEVER on every turn.
"""
from __future__ import annotations

from collections import Counter
import json
from typing import Any
import re

# Match the bounds and load-name grammar used by the persisted snapshot.
_LOAD_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_./:-]{0,199}\Z")
_MAX_NATIVE_SKILLS = 2500
_MAX_NATIVE_REPLY_CHARS = 2_000_000


def native_skill_catalogue() -> dict[str, str] | None:
    """Capture a validated host catalogue, distinguishing failure from empty.

    None means Hermes was unreachable or returned an invalid listing; an empty
    mapping means Hermes explicitly confirmed that no skills are visible.
    Both states must abstain at runtime, but refreshing a verified empty list
    must revoke all previously cached load names.
    """
    try:
        from tools.skills_tool import skills_list  # Host-only import.
        raw = skills_list()
        # This is maintenance-only, but malformed host output must not cause
        # a large parser allocation or a false verified-empty refresh.
        if not isinstance(raw, str) or len(raw) > _MAX_NATIVE_REPLY_CHARS:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("success") is not True:
            return None
        entries = data.get("skills")
        if not isinstance(entries, list) or len(entries) > _MAX_NATIVE_SKILLS:
            return None
        parsed: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                return None
            name, desc = entry.get("name"), entry.get("description", "")
            if (not isinstance(name, str) or not _LOAD_NAME.fullmatch(name)
                    or not isinstance(desc, str) or len(desc) > 1024
                    or name in parsed):
                # Duplicate/invalid load names are not proven unambiguous.
                # Reject the whole host reply rather than silently replacing
                # a verified catalogue with a potentially misleading subset.
                return None
            parsed[name] = desc
        return parsed
    except Exception:
        # A plugin must not break inference if Hermes catalogue access fails.
        return None


def native_skill_allowlist() -> dict[str, str]:
    """Compatibility adapter: missing and empty both fail closed to no hints."""
    return native_skill_catalogue() or {}


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

def compose_native_records(records: list[dict], available: dict[str, str]) -> list[dict]:
    """Index enriched local matches and safe native-only fallback entries.

    Plugin-provided or unsupported-source skills may be absent from the
    sidecar; their *native* descriptions remain searchable without enrichment.
    Never apply a possibly shadowed/stale local sidecar to these entries.
    """
    from .catalog import clean_text
    matched = filter_index_to_native(records, available)
    used = {r["name"] for r in matched}
    for name, description in sorted(available.items()):
        if name in used or not description or not description.strip():
            continue
        matched.append({
            "id": "native::" + name, "name": name,
            "source_description": description,
            "description": clean_text(description, 240),
            "tags": [], "aliases": [], "intents": [], "negative_intents": [],
        })
    return matched
