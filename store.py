"""Profile-scoped transactional SQLite sidecar for SkillSense.

The database contains retrieval metadata only. Skill files are never modified.
"""
from __future__ import annotations
from pathlib import Path
import json
import hashlib
import math
import os
import re
import sqlite3
import tempfile
import time

SCHEMA = 1
# Mirror the canonical adapter's accepted Hermes load-name alphabet.
# A persisted snapshot is still untrusted after a manual edit or corruption.
_LOAD_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_./:-]{0,199}\Z")
_MAX_CATALOGUE_SKILLS = 2500
_MAX_INDEX_BYTES = 3_000_000

def data_dir() -> Path:
    try:
        from plugins.plugin_storage import plugin_data_dir
        return Path(plugin_data_dir("skillsense"))
    except ImportError:
        home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        return home / "plugin-data" / "skillsense"

def _secure_sidecar_directory(root: Path) -> None:
    """Prevent readable SQLite WAL/SHM journals in legacy sidecar directories.

    Open the final directory without following a symlink before tightening its
    permissions. All ancestor directories are controlled by Hermes/the user.
    """
    if os.name != "posix":
        return
    if not hasattr(os, "O_NOFOLLOW") and root.is_symlink():
        raise OSError("SkillSense storage directory must not be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(root, flags)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise PermissionError("SkillSense storage directory is not owned by this user")
        os.fchmod(fd, 0o700)
    finally:
        os.close(fd)


def open_db(home: Path | None = None) -> sqlite3.Connection:
    root = Path(home) if home else data_dir()
    # Reopening an older profile must also secure the directory, not just the
    # data.db file: WAL and shared-memory files live alongside the database.
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    _secure_sidecar_directory(root)
    db_path = root / "data.db"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(db_path, flags, 0o600)
    try:
        if os.name == "posix":
            # Also repair permissions on a database created by older versions.
            os.fchmod(fd, 0o600)
    finally:
        os.close(fd)
    db = sqlite3.connect(db_path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("PRAGMA journal_mode=WAL")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA:
        db.close()
        raise RuntimeError("SkillSense sidecar was created by a newer version")
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS skills(
            id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
            tags TEXT NOT NULL, intents TEXT NOT NULL,
            source_hash TEXT NOT NULL, path TEXT NOT NULL,
            approved TEXT, pending TEXT, status TEXT NOT NULL DEFAULT 'source',
            scanned_at INTEGER NOT NULL
        )""")
        db.execute("PRAGMA user_version=1")
    return db

def _invalidate_published_index(conn: sqlite3.Connection) -> None:
    """Fail closed before mutations that can change active retrieval metadata.

    SQLite commits and an atomic JSON rename cannot be one transaction. Mark
    the old index unusable *before* changing database state; a crash, publish
    failure or partial maintenance then leaves native-only routing rather than
    continuing to serve revoked aliases.
    """
    db_path = next((path for _, name, path in conn.execute("PRAGMA database_list")
                    if name == "main"), "")
    if not db_path:
        raise RuntimeError("Cannot determine SkillSense sidecar location")
    root = Path(db_path).parent
    target = root / "index.json"
    if not target.exists():
        return
    fd, temporary = tempfile.mkstemp(dir=root, prefix=".index-dirty-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": SCHEMA, "skills": [], "maintenance_incomplete": True},
                      stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def sync(conn: sqlite3.Connection, skills: list, roots: list[Path] | None = None) -> dict[str, int]:
    """Upsert changed files; prune only within explicitly scanned complete roots."""
    changed, added, current = 0, 0, {skill.identity for skill in skills}
    with conn:
        _invalidate_published_index(conn)
        for item in skills:
            row = conn.execute("SELECT source_hash FROM skills WHERE id=?", (item.identity,)).fetchone()
            if row is None:
                added += 1
                conn.execute("""INSERT INTO skills
                    (id,name,description,tags,intents,source_hash,path,status,scanned_at)
                    VALUES (?,?,?,?,?,?,?,'source',?)""",
                    (item.identity,item.name,item.description,json.dumps(item.tags),
                     json.dumps(item.intents),item.sha256,item.path,int(time.time())))
            else:
                changed_source = row["source_hash"] != item.sha256
                if changed_source:
                    changed += 1
                conn.execute("""UPDATE skills SET name=?,description=?,tags=?,intents=?,
                    source_hash=?,path=?,scanned_at=?,
                    approved=CASE WHEN ? THEN NULL ELSE approved END,
                    pending=CASE WHEN ? THEN NULL ELSE pending END,
                    status=CASE WHEN ? THEN 'stale' ELSE status END WHERE id=?""",
                    (item.name,item.description,json.dumps(item.tags),json.dumps(item.intents),
                     item.sha256,item.path,int(time.time()),changed_source,changed_source,
                     changed_source,item.identity))
        # A partial root scan must NEVER erase metadata for other roots.
        removed = 0
        scope = [Path(root).expanduser().resolve() for root in (roots or [])]
        if scope:
            for old in conn.execute("SELECT id,path FROM skills").fetchall():
                if old["id"] in current:
                    continue
                path = Path(old["path"]).resolve()
                if any(path.is_relative_to(root) for root in scope):
                    conn.execute("DELETE FROM skills WHERE id=?", (old["id"],))
                    removed += 1
    return {"total":len(skills),"added":added,"changed":changed,"removed":removed}

def stage(conn: sqlite3.Connection, identity: str, source_hash: str, proposal: dict) -> bool:
    """Compare-and-swap source hash; rejects model responses for changed skills."""
    from .catalog import validate_proposal
    clean = validate_proposal(proposal)
    with conn:
        cursor = conn.execute(
            "UPDATE skills SET pending=?,status='pending' WHERE id=? AND source_hash=?",
            (json.dumps(clean,ensure_ascii=False),identity,source_hash))
    return cursor.rowcount == 1

def decide(conn: sqlite3.Connection, identity: str, approve: bool) -> bool:
    with conn:
        row = conn.execute("SELECT pending,path,source_hash FROM skills WHERE id=?", (identity,)).fetchone()
        if row is None or not row["pending"]:
            return False
        _invalidate_published_index(conn)
        # Either decision may affect an existing approved proposal. If the
        # source changed, revoke stale enrichment before *approval or rejection*.
        try:
            data = Path(row["path"]).read_text(encoding="utf-8")
            current_hash = hashlib.sha256(data.encode("utf-8")).hexdigest()
        except (OSError, UnicodeError, ValueError):
            current_hash = None
        if current_hash != row["source_hash"]:
            conn.execute("UPDATE skills SET approved=NULL,pending=NULL,status='stale' WHERE id=?",
                         (identity,))
            return False
        if approve:
            conn.execute("UPDATE skills SET approved=pending,pending=NULL,status='approved' WHERE id=?",
                         (identity,))
        else:
            conn.execute("UPDATE skills SET pending=NULL,status='rejected' WHERE id=?",
                         (identity,))
    return True

def rows(conn: sqlite3.Connection) -> list[dict]:
    result = []
    for row in conn.execute("SELECT * FROM skills ORDER BY name,id"):
        item = dict(row)
        for field in ("tags","intents","approved","pending"):
            item[field] = json.loads(item[field]) if item[field] else None
        result.append(item)
    return result

def publish_index(conn: sqlite3.Connection, home: Path | None = None) -> int:
    """Write complete approved index to a temp file, fsync and atomic replace."""
    root = Path(home) if home else data_dir()
    root.mkdir(parents=True, exist_ok=True)
    payload = []
    for r in rows(conn):
        metadata = r["approved"] or {}
        payload.append({
            "id":r["id"],"name":r["name"],"source_description":r["description"],
            "description":metadata.get("description") or r["description"],
            "tags":list(r["tags"] or []) + list(metadata.get("tags", [])),
            "aliases":list(metadata.get("aliases",[])),
            "intents":list(r["intents"] or []) + list(metadata.get("positive_intents", [])),
            "negative_intents":list(metadata.get("negative_intents", []))
        })
    # Match the reader's hard bounds BEFORE publication. Multiple partial
    # root scans can accumulate more sidecar rows than a single 2,500-skill
    # scan, and approved metadata can exceed the index byte budget.
    if len(payload) > _MAX_CATALOGUE_SKILLS:
        raise ValueError("SkillSense index exceeds 2500 skills; reconcile unused roots")
    encoded = json.dumps({"schema":SCHEMA,"skills":payload},
                         ensure_ascii=False,separators=(",",":")).encode("utf-8")
    if len(encoded) > _MAX_INDEX_BYTES:
        raise ValueError("SkillSense index exceeds 3 MB; reduce approved metadata")
    fd, temporary = tempfile.mkstemp(dir=root, prefix=".index-", suffix=".json")
    try:
        with os.fdopen(fd,"wb") as file:
            file.write(encoded)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary,root/"index.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return len(payload)

def save_native_snapshot(available: dict[str, str], home: Path | None = None) -> None:
    """Persist a canonical Hermes catalogue from the local CLI rebuild.

    The isolated plugin host does not need Hermes internal imports at all.
    Call only after a successful Hermes listing, including verified emptiness.
    Failed catalogue lookups must leave an older snapshot untouched.
    """
    root = Path(home) if home else data_dir()
    root.mkdir(parents=True,exist_ok=True)
    valid = {name:desc for name,desc in available.items()
             if isinstance(name,str) and _LOAD_NAME.fullmatch(name)
             and isinstance(desc,str) and len(desc) <= 1024}
    if len(valid) > _MAX_CATALOGUE_SKILLS:
        raise ValueError("Canonical Hermes skill catalogue exceeds 2500 entries")
    fd, tmp = tempfile.mkstemp(dir=root,prefix=".native-",suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump({"schema":SCHEMA,"captured_at":time.time(),"skills":valid},
                      stream,ensure_ascii=False,separators=(",",":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp,root/"native-catalogue.json")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_native_snapshot(home: Path | None = None) -> dict[str,str]:
    root = Path(home) if home else data_dir()
    file = root / "native-catalogue.json"
    try:
        if file.stat().st_size > 2_000_000:
            return {}
        data = json.loads(file.read_text(encoding="utf-8"))
        if (not isinstance(data,dict) or type(data.get("schema")) is not int
                or data["schema"] != SCHEMA
                or set(data) != {"schema", "captured_at", "skills"}):
            return {}
        if (type(data.get("captured_at")) not in (int,float)
                or not math.isfinite(data["captured_at"])):
            return {}
        now=time.time()
        # Never trust snapshots from the future or older than seven days.
        if not 0 <= now-data["captured_at"] <= 7*86400:
            return {}
        rows=data.get("skills")
        if (not isinstance(rows,dict) or len(rows) > _MAX_CATALOGUE_SKILLS
                or any(not isinstance(name,str) or not _LOAD_NAME.fullmatch(name)
                       or not isinstance(desc,str) or len(desc) > 1024
                       for name,desc in rows.items())):
            return {}
        return rows
    except (OSError,ValueError,TypeError,AttributeError):
        return {}


def _valid_index_skill(record: object) -> bool:
    """Only publisher-shaped, bounded metadata may enter the live BM25 index.

    Invalid generated enrichment must not poison routing for otherwise verified
    native skills. Reject the entire sidecar index, then use native fallback.
    """
    if not isinstance(record, dict):
        return False
    text_fields = ("id", "name", "source_description", "description")
    if any(not isinstance(record.get(field), str) for field in text_fields):
        return False
    if not 0 < len(record["id"]) <= 4096:
        return False
    if not _LOAD_NAME.fullmatch(record["name"]):
        return False
    if any(len(record[field]) > 1024 for field in ("source_description", "description")):
        return False
    for field in ("tags", "aliases", "intents", "negative_intents"):
        values = record.get(field)
        if (not isinstance(values, list) or len(values) > 128
                or any(not isinstance(item, str) or len(item) > 1000 for item in values)):
            return False
    return True


def read_index_status(home: Path | None = None) -> tuple[list[dict], bool]:
    path = (Path(home) if home else data_dir()) / "index.json"
    try:
        if path.stat().st_size > _MAX_INDEX_BYTES:
            return [], False
        value = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(value, dict) or value.get("schema") != SCHEMA
                or set(value) != {"schema", "skills"}):
            return [], False
        records = value.get("skills")
        # Never accept a truncated catalogue: it could remove valid matches
        # while leaving stale enrichment for unexamined records.
        if (not isinstance(records, list) or len(records) > _MAX_CATALOGUE_SKILLS
                or not all(_valid_index_skill(record) for record in records)):
            return [], False
        identities = [record["id"] for record in records]
        if len(identities) != len(set(identities)):
            return [], False
        return records, True
    except (FileNotFoundError,OSError,ValueError,TypeError,AttributeError):
        return [], False

def read_index(home: Path | None = None) -> list[dict]:
    """Get verified index records, or no enrichment if unavailable/invalid."""
    return read_index_status(home)[0]
