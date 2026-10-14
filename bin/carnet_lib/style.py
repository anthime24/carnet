import re
from pathlib import Path

ID_RE = re.compile(r"\b(?:BDR|LRN|BLK)-\d+\b")
MAX_WORDS_ENTREPRISE = 300


def load_phrases(path):
    path = Path(path)
    if not path.exists():
        return []
    phrases = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw and not raw.startswith("#"):
            phrases.append(raw)
    return phrases


def _normalize(text):
    return text.replace("’", "'")


def _warning(number, motif, line):
    return {"line": number, "motif": motif, "extrait": line.strip()[:120]}


def check(text, gabarit, phrases):
    patterns = [
        (phrase, re.compile(r"(?<!\w)" + re.escape(_normalize(phrase)) + r"(?!\w)", re.IGNORECASE))
        for phrase in phrases
    ]
    warnings = []
    for number, line in enumerate(text.split("\n"), start=1):
        if "—" in line:
            warnings.append(_warning(number, "tiret cadratin", line))
        normalized = _normalize(line)
        for phrase, pattern in patterns:
            if pattern.search(normalized):
                warnings.append(_warning(number, f"expression à éviter: {phrase}", line))
        if gabarit == "entreprise":
            for match in ID_RE.finditer(line):
                warnings.append(_warning(number, f"ID interne: {match.group(0)}", line))
            if "[[" in line:
                warnings.append(_warning(number, "référence [[ ]] interne", line))
    if gabarit == "entreprise":
        words = len(text.split())
        if words > MAX_WORDS_ENTREPRISE:
            warnings.append(
                {"line": 0, "motif": f"plus de {MAX_WORDS_ENTREPRISE} mots ({words})", "extrait": ""}
            )
    return warnings
