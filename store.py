"""Profile-scoped transactional SQLite sidecar for SkillSense.

The database contains retrieval metadata only. Skill files are never modified.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import sqlite3
import tempfile
import time

SCHEMA = 1

def data_dir() -> Path:
    try:
        from plugins.plugin_storage import plugin_data_dir
        return Path(plugin_data_dir("skillsense"))
    except ImportError:
        home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        return home / "plugin-data" / "skillsense"

def open_db(home: Path | None = None) -> sqlite3.Connection:
    root = Path(home) if home else data_dir()
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "data.db", timeout=10)
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

def sync(conn: sqlite3.Connection, skills: list) -> dict[str, int]:
    """One transaction. Changed sources invalidate approvals rather than applying stale metadata."""
    changed, added, current = 0, 0, {skill.identity for skill in skills}
    with conn:
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
        # Scope removal to the complete selected root list; caller must avoid accidental subset scans.
        for old in conn.execute("SELECT id FROM skills").fetchall():
            if old["id"] not in current:
                conn.execute("DELETE FROM skills WHERE id=?", (old["id"],))
    return {"total":len(skills),"added":added,"changed":changed}

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
        row = conn.execute("SELECT pending FROM skills WHERE id=?", (identity,)).fetchone()
        if row is None or not row["pending"]:
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
    fd, temporary = tempfile.mkstemp(dir=root, prefix=".index-", suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as file:
            json.dump({"schema":SCHEMA,"skills":payload},file,ensure_ascii=False,separators=(",",":"))
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary,root/"index.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return len(payload)

def read_index(home: Path | None = None) -> list[dict]:
    path = (Path(home) if home else data_dir()) / "index.json"
    try:
        if path.stat().st_size > 3_000_000:
            return []
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema") != SCHEMA or not isinstance(value.get("skills"),list):
            return []
        return value["skills"][:2500]
    except (FileNotFoundError,OSError,ValueError,TypeError,AttributeError):
        return []
