import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
CLI = BIN / "carnet.py"
sys.path.insert(0, str(BIN))


class ProjectCase(unittest.TestCase):
    """Fournit un dossier projet temporaire, supprimé après chaque test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()
        self.memory = self.root / ".claude" / "memory"


def run_cli(*args, root=None, stdin=None, env_extra=None):
    """Lance bin/carnet.py. Renvoie (code de sortie, JSON décodé ou None, stderr)."""
    env = dict(os.environ)
    env["CARNET_TODAY"] = "2026-10-14"
    env["CARNET_CLAUDE_MEM_DB"] = str(ROOT / "tests" / "absent.db")
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, str(CLI), *args]
    if root is not None:
        cmd += ["--project-root", str(root)]
    proc = subprocess.run(
        cmd, input=stdin, capture_output=True, text=True, encoding="utf-8", env=env
    )
    out = json.loads(proc.stdout) if proc.stdout.strip() else None
    return proc.returncode, out, proc.stderr


DECISION = {
    "titre": "Registres par projet",
    "decision": "Un dossier .claude/memory par projet",
    "pourquoi": "Chaque projet reste autonome",
    "alternatives": "Un vault central",
}
LEARNING = {
    "titre": "Lire le schéma avant d'écrire la requête",
    "pattern": "Interroger la vraie base évite les colonnes imaginaires",
    "contexte": "Lecture de claude-mem",
    "application": "Inspecter les données réelles d'abord",
}
BLOCKER = {
    "titre": "Chemin du script introuvable",
    "friction": "La skill ne trouvait pas carnet.py",
    "cause": "Mauvais niveau de remontée dans le chemin",
}


def make_claude_mem_db(path, sessions, summaries):
    """Fausse base claude-mem, avec les colonnes réelles lues par le plugin (claude-mem 13.37.0).

    sessions:  [(memory_session_id, project, cwd)]
    summaries: [(memory_session_id, project, created_at, request, completed, next_steps, files_edited)]
    """
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE sdk_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, memory_session_id TEXT UNIQUE,
            project TEXT NOT NULL, cwd TEXT);
        CREATE TABLE session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, memory_session_id TEXT NOT NULL,
            project TEXT NOT NULL, request TEXT, investigated TEXT, learned TEXT,
            completed TEXT, next_steps TEXT, files_read TEXT, files_edited TEXT,
            created_at TEXT NOT NULL, created_at_epoch INTEGER NOT NULL);
        """
    )
    conn.executemany(
        "INSERT INTO sdk_sessions (memory_session_id, project, cwd) VALUES (?, ?, ?)", sessions
    )
    for i, (sid, project, created_at, request, completed, next_steps, files) in enumerate(summaries):
        conn.execute(
            "INSERT INTO session_summaries (memory_session_id, project, request, investigated, "
            "learned, completed, next_steps, files_edited, created_at, created_at_epoch) "
            "VALUES (?, ?, ?, '', '', ?, ?, ?, ?, ?)",
            (sid, project, request, completed, next_steps, files, created_at, i),
        )
    conn.commit()
    conn.close()
