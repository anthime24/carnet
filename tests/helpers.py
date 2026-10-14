import json
import os
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
