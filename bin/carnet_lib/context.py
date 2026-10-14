import re
from pathlib import Path

from . import registers, reports, sources
from .errors import CarnetError

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_date(label, value):
    if value is not None and not DATE_RE.match(value):
        raise CarnetError("date_invalide", f"--{label}: {value}")


def build(root, since=None, until=None, gabarit=None, today=None, db_path=None):
    root = Path(root)
    until = until or today or registers.today_iso()
    journal = registers.read_journal(root)
    last_journal_date = max((entry["date"] for entry in journal), default=None)
    previous = reports.last_report(root, gabarit) if gabarit else None
    if since == "journal":
        since = last_journal_date
    elif since == "rapport":
        if not gabarit:
            raise CarnetError("gabarit_requis", "--since rapport demande --gabarit")
        since = previous["date"] if previous else None
    _check_date("since", since)
    _check_date("until", until)

    def in_period(day):
        return bool(day) and (since is None or day >= since) and (until is None or day <= until)

    decisions = registers.read_entries(root, "decisions")
    learnings = registers.read_entries(root, "learnings")
    blockers = registers.read_entries(root, "blockers")
    return {
        "project": {
            "root": str(root),
            "name": root.name,
            "initialized": registers.memory_dir(root).is_dir(),
        },
        "since": since,
        "until": until,
        "registers": {
            "decisions": [e for e in decisions if in_period(e["date"])],
            "learnings": [e for e in learnings if in_period(e["date"])],
            "blockers": {
                "opened": [e for e in blockers if in_period(e["date"])],
                "open": [e for e in blockers if e["statut"] == "ouvert"],
                "resolved": [
                    e
                    for e in blockers
                    if e["statut"] == "résolu" and in_period(e.get("resolu_le") or e["date"])
                ],
            },
            "journal": [e for e in journal if in_period(e["date"])],
            "last_journal_date": last_journal_date,
            "last_dates": registers.last_dates(root),
        },
        "previous_report": previous,
        "claude_mem": sources.read_claude_mem(root, since, until, last_journal_date, path=db_path),
        "graphify": sources.read_graphify(root),
    }
