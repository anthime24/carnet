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


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REF_RE = re.compile(r"\[\[([A-Z]{3}-\d+)\]\]")


def _bad(path, number, message):
    return CarnetError("registre_illisible", f"{path.name}:{number}: {message}")


def _lines(text):
    return [line.rstrip("\r") for line in text.split("\n")]


def _read(root, name):
    path = memory_dir(root) / f"{name}.md"
    if not path.exists():
        raise CarnetError("registre_absent", f"{path} n'existe pas, lancer `carnet.py init`")
    return path, _lines(path.read_text(encoding="utf-8"))


def _save(path, lines):
    while lines and lines[-1] == "":
        lines.pop()
    atomic_write(path, "\n".join(lines) + "\n")


def _with_block(lines, block):
    out = list(lines)
    while out and out[-1] == "":
        out.pop()
    return out + [""] + block


def _check_header(name, lines, path):
    if not lines or lines[0] != "---":
        raise _bad(path, 1, "header YAML absent")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise _bad(path, 1, "header YAML non fermé")
    meta = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    if meta.get("registre") != name:
        raise _bad(path, 2, f"« registre: {name} » attendu dans le header")
    if name != JOURNAL and meta.get("prefixe") != REGISTERS[name]["prefix"]:
        raise _bad(path, 3, f"« prefixe: {REGISTERS[name]['prefix']} » attendu dans le header")


def _cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _locate_index(name, lines, path):
    labels = [label for _, label in REGISTERS[name]["index"]]
    try:
        start = lines.index("## Index")
    except ValueError:
        raise _bad(path, 1, "section « ## Index » absente")
    expected = "| " + " | ".join(labels) + " |"
    if start + 2 >= len(lines) or lines[start + 1].strip() != expected:
        raise _bad(path, start + 2, f"en-tête du tableau attendu: {expected}")
    if not re.match(r"^\|[-| :]+\|$", lines[start + 2].strip()):
        raise _bad(path, start + 3, "ligne de séparation du tableau attendue")
    first = start + 3
    end = first
    while end < len(lines) and lines[end].startswith("|"):
        if len(_cells(lines[end])) != len(labels):
            raise _bad(path, end + 1, f"{len(labels)} colonnes attendues")
        end += 1
    return first, end


def _next_id(spec, lines, first, end):
    numbers = [0]
    heading = re.compile(rf"^## {spec['prefix']}-(\d+) · ")
    for line in lines:
        match = heading.match(line)
        if match:
            numbers.append(int(match.group(1)))
    for line in lines[first:end]:
        match = re.fullmatch(rf"{spec['prefix']}-(\d+)", _cells(line)[0])
        if match:
            numbers.append(int(match.group(1)))
    return f"{spec['prefix']}-{max(numbers) + 1:03d}"


def _day(data, today):
    day = clean(data.get("date") or today or today_iso())
    if not DATE_RE.match(day):
        raise CarnetError("date_invalide", day)
    return day


def known_ids(root):
    ids = set()
    for name, spec in REGISTERS.items():
        path = memory_dir(root) / f"{name}.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            ids.update(re.findall(rf"^## ({spec['prefix']}-\d+) · ", text, re.M))
    return ids


def _reference_warnings(root, texts, own_id=None):
    known = known_ids(root)
    if own_id:
        known.add(own_id)
    cited = set()
    for text in texts:
        cited.update(REF_RE.findall(text))
    return [f"Référence [[{ref}]] introuvable" for ref in sorted(cited - known)]


def _normalize(spec, data, today):
    missing = [key for key in spec["required"] if not clean(data.get(key, ""))]
    if missing:
        raise CarnetError("champs_manquants", ", ".join(missing))
    entry = {"date": _day(data, today), "titre": clean(data["titre"])}
    for key, _ in spec["fields"]:
        entry[key] = clean(data.get(key) or spec["defaults"].get(key, ""))
    if spec["statuses"] and entry["statut"] not in spec["statuses"]:
        raise CarnetError(
            "statut_invalide",
            f"{entry['statut']} (valeurs possibles: {', '.join(spec['statuses'])})",
        )
    return entry


def _add_journal(root, data, today):
    raw = data.get("lignes") or []
    if isinstance(raw, str):
        raw = [raw]
    lignes = [clean(line) for line in raw if clean(line)]
    suite = clean(data.get("suite", ""))
    missing = [key for key, value in (("lignes", lignes), ("suite", suite)) if not value]
    if missing:
        raise CarnetError("champs_manquants", ", ".join(missing))
    day = _day(data, today)
    path, lines = _read(root, JOURNAL)
    _check_header(JOURNAL, lines, path)
    warnings = _reference_warnings(root, lignes + [suite])
    _save(path, _with_block(lines, [f"## {day}", *lignes, f"Suite: {suite}"]))
    return {"id": None, "date": day, "file": str(path), "warnings": warnings}


def add(root, name, data, today=None):
    if name not in ALL_REGISTERS:
        raise CarnetError("registre_inconnu", name)
    if not isinstance(data, dict):
        raise CarnetError("entree_invalide", "un objet JSON est attendu")
    if name == JOURNAL:
        return _add_journal(root, data, today)
    spec = REGISTERS[name]
    entry = _normalize(spec, data, today)
    path, lines = _read(root, name)
    _check_header(name, lines, path)
    first, end = _locate_index(name, lines, path)
    entry_id = _next_id(spec, lines, first, end)
    warnings = _reference_warnings(root, list(entry.values()), own_id=entry_id)
    cells = [
        entry_id if key == "id" else entry[key].replace("|", "/") for key, _ in spec["index"]
    ]
    lines.insert(end, "| " + " | ".join(cells) + " |")
    block = [f"## {entry_id} · {entry['titre']}", f"- **Date:** {entry['date']}"]
    block += [f"- **{label}:** {entry[key]}".rstrip() for key, label in spec["fields"]]
    _save(path, _with_block(lines, block))
    return {"id": entry_id, "file": str(path), "warnings": warnings}


def _register_for_id(entry_id):
    match = re.fullmatch(r"([A-Z]{3})-\d+", entry_id)
    if match:
        for name, spec in REGISTERS.items():
            if spec["prefix"] == match.group(1):
                return name
    raise CarnetError("id_inconnu", entry_id)


def _block_end(lines, heading_index):
    for i in range(heading_index + 1, len(lines)):
        if lines[i].startswith("## "):
            return i
    return len(lines)


def _upsert_line(lines, heading_index, label, value, after_label):
    prefix = f"- **{label}:**"
    text = f"{prefix} {value}".rstrip()
    end = _block_end(lines, heading_index)
    for i in range(heading_index + 1, end):
        if lines[i].startswith(prefix):
            lines[i] = text
            return
    anchor = f"- **{after_label}:**"
    for i in range(heading_index + 1, end):
        if lines[i].startswith(anchor):
            lines.insert(i + 1, text)
            return
    while end > heading_index + 1 and lines[end - 1] == "":
        end -= 1
    lines.insert(end, text)


def _remove_line(lines, heading_index, label):
    prefix = f"- **{label}:**"
    for i in range(heading_index + 1, _block_end(lines, heading_index)):
        if lines[i].startswith(prefix):
            del lines[i]
            return


def set_status(root, entry_id, status, solution=None, today=None):
    name = _register_for_id(entry_id)
    spec = REGISTERS[name]
    if not spec["statuses"]:
        raise CarnetError("statut_non_gere", f"le registre {name} n'a pas de statut")
    if status not in spec["statuses"]:
        raise CarnetError(
            "statut_invalide", f"{status} (valeurs possibles: {', '.join(spec['statuses'])})"
        )
    if solution is not None and name != "blockers":
        raise CarnetError("option_invalide", "--solution ne concerne que les blocages")
    path, lines = _read(root, name)
    _check_header(name, lines, path)
    first, end = _locate_index(name, lines, path)
    row = next((i for i in range(first, end) if _cells(lines[i])[0] == entry_id), None)
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith(f"## {entry_id} · ")), None
    )
    if row is None or heading is None:
        raise CarnetError("id_introuvable", f"{entry_id} dans {path.name}")
    block_end = _block_end(lines, heading)
    if not any(lines[i].startswith("- **Statut:**") for i in range(heading + 1, block_end)):
        raise _bad(path, heading + 1, f"ligne « Statut » absente pour {entry_id}")
    cells = _cells(lines[row])
    cells[[key for key, _ in spec["index"]].index("statut")] = status
    lines[row] = "| " + " | ".join(cells) + " |"
    _upsert_line(lines, heading, "Statut", status, "Date")
    if solution is not None:
        _upsert_line(lines, heading, "Solution", clean(solution), "Cause réelle")
    if name == "blockers":
        if status == "résolu":
            _upsert_line(lines, heading, "Résolu le", today or today_iso(), "Statut")
        else:
            _remove_line(lines, heading, "Résolu le")
    _save(path, lines)
    return {"id": entry_id, "statut": status, "file": str(path)}
