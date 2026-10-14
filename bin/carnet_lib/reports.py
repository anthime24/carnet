import re

from . import registers, style
from .errors import CarnetError

GABARITS = ("perso", "entreprise")
NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(perso|entreprise)(?:-(\d+))?\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def reports_dir(root):
    return registers.memory_dir(root) / "reports"


def _check_gabarit(gabarit):
    if gabarit not in GABARITS:
        raise CarnetError("gabarit_inconnu", f"{gabarit} (valeurs possibles: {', '.join(GABARITS)})")


def last_report(root, gabarit):
    _check_gabarit(gabarit)
    folder = reports_dir(root)
    found = []
    if folder.is_dir():
        for path in folder.iterdir():
            match = NAME_RE.match(path.name)
            if match and match.group(2) == gabarit:
                found.append((match.group(1), int(match.group(3) or 1), path))
    if not found:
        return None
    day, _, path = max(found)
    return {"gabarit": gabarit, "date": day, "path": str(path)}


def save_report(root, gabarit, body, du, au, phrases, today=None):
    _check_gabarit(gabarit)
    if not (DATE_RE.match(du) or du == "début"):
        raise CarnetError("date_invalide", f"--du: {du}")
    if not DATE_RE.match(au):
        raise CarnetError("date_invalide", f"--au: {au}")
    day = today or registers.today_iso()
    folder = reports_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        suffix = "" if number == 1 else f"-{number}"
        path = folder / f"{day}-{gabarit}{suffix}.md"
        if not path.exists():
            break
        number += 1
    text = f"---\ngabarit: {gabarit}\ndu: {du}\nau: {au}\n---\n{body.strip()}\n"
    registers.atomic_write(path, text)
    return {"path": str(path), "warnings": style.check(body, gabarit, phrases)}
