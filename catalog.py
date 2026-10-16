"""Read-only, bounded Hermes SKILL.md scanning and metadata validation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import re
import unicodedata

MAX_SKILL_BYTES = 200_000
MAX_SKILLS = 2500
_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,99}$")
_SAFE = re.compile(r"[\x00-\x1f\x7f-\x9f]+")

@dataclass(frozen=True)
class Skill:
    identity: str
    name: str
    description: str
    tags: tuple[str, ...]
    intents: tuple[str, ...]
    path: str
    sha256: str

def clean_text(value: str, max_len: int = 240) -> str:
    return _SAFE.sub(" ", unicodedata.normalize("NFKC", str(value))).strip()[:max_len].strip()

def frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Intentionally restricted YAML subset; never evaluates YAML tags."""
    if not text.startswith("---\n"):
        return {}, text
    end = re.search(r"(?m)^---\s*$", text[4:16000])
    if not end:
        return {}, text
    bound = end.start() + 4
    header, body = text[4:bound], text[bound + len(end.group()):]
    data: dict[str, object] = {}
    scope, tags = "", []
    for line in header.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        match = re.match(r"^([a-zA-Z][\w-]*):\s*(.*)$", stripped)
        if match:
            key, val = match.groups()
            if indent == 0:
                scope = key
                if key in ("name", "description", "platforms", "requires"):
                    data[key] = val.strip().strip('"').strip("'")
            elif key == "tags" and scope == "metadata" and val.startswith("[") and val.endswith("]"):
                tags += [v.strip().strip("'\"") for v in val[1:-1].split(",")]
            elif key == "tags" and scope == "metadata":
                scope = "tags"
        elif stripped.startswith("- ") and scope == "tags":
            tags.append(stripped[2:].strip("'\" "))
    data["tags"] = tags[:12]
    return data, body

def _activation(body: str) -> str:
    found = re.search(r"(?im)^#{1,3}\s*(when to use|use cases|triggers)\b[^\n]*\n", body)
    if not found:
        return ""
    segment = re.split(r"(?m)^#{1,3}\s", body[found.end():], 1)[0]
    return clean_text(re.sub(r"[*#]", "", segment), 360)

def scan_skills(roots: list[Path]) -> list[Skill]:
    """Only scans explicitly trusted roots; never follows symlinks."""
    found: dict[str, Skill] = {}
    total = 0
    for raw_root in roots:
        root = Path(raw_root).expanduser()
        if not root.is_dir():
            continue
        root = root.resolve()
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith((".", "_"))
                             and not (Path(directory) / d).is_symlink())
            if "SKILL.md" not in files:
                continue
            total += 1
            if total > MAX_SKILLS:
                return sorted(found.values(), key=lambda s: (s.name, s.identity))
            path = Path(directory) / "SKILL.md"
            try:
                if path.is_symlink() or not path.resolve().is_relative_to(root):
                    continue
                if path.stat().st_size > MAX_SKILL_BYTES:
                    continue
                body = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError, ValueError):
                continue
            metadata, instructions = frontmatter(body)
            name = str(metadata.get("name") or path.parent.name).lower()
            if not _NAME.fullmatch(name):
                continue
            if metadata.get("platforms") or metadata.get("requires"):
                continue  # Can't safely infer Hermes availability requirements.
            rel = path.parent.relative_to(root).as_posix()
            identity = f"{root.as_posix()}::{rel}"
            tags = tuple(clean_text(str(t), 40).lower() for t in metadata.get("tags",[])
                         if clean_text(str(t), 40))[:12]
            trigger = _activation(instructions)
            found[identity] = Skill(identity, name,
                clean_text(str(metadata.get("description", ""))),
                tags, (trigger,) if trigger else (), str(path),
                hashlib.sha256(body.encode("utf-8")).hexdigest())
    return sorted(found.values(), key=lambda s: (s.name, s.identity))

FIELDS = frozenset(("description", "tags", "aliases", "positive_intents", "negative_intents"))

def validate_proposal(raw: object) -> dict[str, object]:
    """Independently check model JSON; proposals require later approval."""
    if not isinstance(raw, dict) or set(raw) - FIELDS:
        raise ValueError("unsupported proposal fields")
    result: dict[str, object] = {}
    if "description" in raw:
        value = raw["description"]
        if not isinstance(value, str) or len(value) > 240:
            raise ValueError("invalid description")
        result["description"] = clean_text(value)
    for key, limit in (("tags", 12), ("aliases", 8),
                       ("positive_intents", 8), ("negative_intents", 6)):
        arr = raw.get(key, [])
        if not isinstance(arr, list) or len(arr) > limit:
            raise ValueError(f"invalid {key}")
        values: list[str] = []
        for item in arr:
            if not isinstance(item, str) or not 2 <= len(item) <= 100:
                raise ValueError(f"invalid {key} item")
            item = clean_text(item, 100)
            if item.casefold() not in {s.casefold() for s in values}:
                values.append(item)
        result[key] = values
    if not (result.get("description") or result.get("tags") or result.get("aliases")):
        raise ValueError("empty proposal")
    return result
