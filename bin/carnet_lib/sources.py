import json
import os
import re
import sqlite3
from pathlib import Path
from urllib.parse import quote

DEFAULT_DB = Path.home() / ".claude-mem" / "claude-mem.db"
MAX_FIELD_CHARS = 500
MAX_GRAPHIFY_CHARS = 3000
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

QUERY = """
SELECT s.created_at, s.request, s.investigated, s.learned, s.completed,
       s.next_steps, s.files_edited, s.project AS project, d.cwd AS cwd
FROM session_summaries s
JOIN sdk_sessions d ON d.memory_session_id = s.memory_session_id
WHERE d.cwd = :root OR substr(d.cwd, 1, :n) = :prefix OR s.project = :name
"""


def db_path():
    return Path(os.environ.get("CARNET_CLAUDE_MEM_DB") or DEFAULT_DB)


def _unavailable(reason):
    return {"status": "unavailable", "reason": reason, "summaries": []}


def _shorten(value):
    value = " ".join(str(value or "").split())
    if len(value) <= MAX_FIELD_CHARS:
        return value
    return value[: MAX_FIELD_CHARS - 1].rstrip() + "…"


def _files(value):
    try:
        data = json.loads(value or "[]")
    except (TypeError, ValueError):
        return []
    return [str(item) for item in data] if isinstance(data, list) else []


def _fetch(path, root_text, prefix, name):
    uri = "file:" + quote(str(path)) + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=2)
    conn.row_factory = sqlite3.Row
    try:
        params = {"root": root_text, "n": len(prefix), "prefix": prefix, "name": name}
        return conn.execute(QUERY, params).fetchall()
    finally:
        conn.close()


def _choose(rows, root_text, prefix, name):
    """Renvoie (lignes retenues, type de correspondance)."""
    by_cwd, foreign, same_name = [], [], []
    for row in rows:
        cwd = row["cwd"]
        if cwd is not None and (cwd == root_text or cwd.startswith(prefix)):
            by_cwd.append(row)
        elif row["project"] == name and (cwd is None or not cwd.startswith("/")):
            foreign.append(row)
        elif row["project"] == name:
            same_name.append(row)
    if by_cwd or foreign:
        if by_cwd and foreign:
            return by_cwd + foreign, "cwd+name"
        return (by_cwd, "cwd") if by_cwd else (foreign, "name")
    return (same_name, "name") if same_name else ([], "cwd")


def read_claude_mem(root, since, until, last_journal_date, path=None):
    path = Path(path) if path else db_path()
    if not path.exists():
        return _unavailable(f"base introuvable: {path}")
    root_text = str(root)
    prefix = root_text.rstrip("/") + "/"
    name = Path(root_text).name
    try:
        rows = _fetch(path, root_text, prefix, name)
    except sqlite3.Error as exc:
        return _unavailable(f"base illisible ou schéma inattendu: {exc}")
    chosen, match = _choose(rows, root_text, prefix, name)
    summaries = []
    for row in sorted(chosen, key=lambda r: r["created_at"] or ""):
        found = DAY_RE.match(row["created_at"] or "")
        if not found:
            continue
        day = found.group(0)
        if (since and day < since) or (until and day > until):
            continue
        summaries.append(
            {
                "date": day,
                "request": _shorten(row["request"]),
                "investigated": _shorten(row["investigated"]),
                "learned": _shorten(row["learned"]),
                "completed": _shorten(row["completed"]),
                "next_steps": _shorten(row["next_steps"]),
                "files_edited": _files(row["files_edited"]),
                "unvalidated": last_journal_date is None or day > last_journal_date,
            }
        )
    return {"status": "ok", "match": match, "summaries": summaries}


def read_graphify(root):
    path = Path(root) / "graphify-out" / "GRAPH_REPORT.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"status": "absent"}
    excerpt = text[:MAX_GRAPHIFY_CHARS]
    if len(text) > MAX_GRAPHIFY_CHARS and "\n" in excerpt:
        excerpt = excerpt.rsplit("\n", 1)[0]
    return {"status": "ok", "excerpt": excerpt.strip()}
