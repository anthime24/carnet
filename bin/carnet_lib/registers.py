import os
import re
from datetime import date
from pathlib import Path

from .errors import CarnetError

MEMORY_REL = Path(".claude") / "memory"
JOURNAL = "journal"

REGISTERS = {
    "decisions": {
        "prefix": "BDR",
        "title": "Décisions",
        "fields": [
            ("decision", "Décision"),
            ("pourquoi", "Pourquoi"),
            ("alternatives", "Alternatives"),
            ("statut", "Statut"),
        ],
        "index": [("id", "ID"), ("date", "Date"), ("titre", "Titre"), ("statut", "Statut")],
        "statuses": ["actée", "remplacée", "abandonnée"],
        "required": ["titre", "decision", "pourquoi"],
        "defaults": {"alternatives": "", "statut": "actée"},
    },
    "learnings": {
        "prefix": "LRN",
        "title": "Apprentissages",
        "fields": [
            ("pattern", "Pattern observé"),
            ("contexte", "Contexte"),
            ("application", "Application future"),
        ],
        "index": [("id", "ID"), ("date", "Date"), ("titre", "Titre")],
        "statuses": [],
        "required": ["titre", "pattern", "contexte", "application"],
        "defaults": {},
    },
    "blockers": {
        "prefix": "BLK",
        "title": "Blocages",
        "fields": [
            ("friction", "Friction"),
            ("cause", "Cause réelle"),
            ("solution", "Solution"),
            ("statut", "Statut"),
        ],
        "index": [("id", "ID"), ("date", "Date"), ("titre", "Titre"), ("statut", "Statut")],
        "statuses": ["ouvert", "résolu"],
        "required": ["titre", "friction", "cause"],
        "defaults": {"solution": "", "statut": "ouvert"},
    },
}
ALL_REGISTERS = ["decisions", "learnings", "blockers", JOURNAL]


def today_iso():
    return os.environ.get("CARNET_TODAY") or date.today().isoformat()


def memory_dir(root):
    return Path(root) / MEMORY_REL


def clean(value):
    """Une valeur tient sur une ligne: les retours à la ligne deviennent des espaces."""
    return " ".join(("" if value is None else str(value)).split())


def atomic_write(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def initial_text(name):
    if name == JOURNAL:
        return "---\nregistre: journal\n---\n# Journal\n"
    spec = REGISTERS[name]
    labels = [label for _, label in spec["index"]]
    head = "| " + " | ".join(labels) + " |"
    sep = "|" + "|".join("-" * (len(label) + 2) for label in labels) + "|"
    return (
        f"---\nregistre: {name}\nprefixe: {spec['prefix']}\n---\n"
        f"# {spec['title']}\n\n## Index\n{head}\n{sep}\n"
    )


def init(root):
    mem = memory_dir(root)
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "reports").mkdir(exist_ok=True)
    created, existing = [], []
    for name in ALL_REGISTERS:
        path = mem / f"{name}.md"
        if path.exists():
            existing.append(path.name)
        else:
            atomic_write(path, initial_text(name))
            created.append(path.name)
    return {"memory_dir": str(mem), "created": created, "existing": existing}
