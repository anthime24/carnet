#!/usr/bin/env python3
"""Carnet: registres de projet et matière première pour les rapports."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from carnet_lib import registers, style  # noqa: E402
from carnet_lib.errors import CarnetError  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
STYLE_FILE = PLUGIN_ROOT / "templates" / "style.txt"
GABARITS = ("perso", "entreprise")


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project-root", default=".", help="dossier racine du projet (défaut: dossier courant)"
    )
    parser = argparse.ArgumentParser(prog="carnet.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", parents=[common], help="crée .claude/memory/ et les registres")

    add = sub.add_parser(
        "add", parents=[common], help="ajoute une entrée (objet JSON sur l'entrée standard)"
    )
    add.add_argument("registre", choices=registers.ALL_REGISTERS)

    set_status = sub.add_parser(
        "set-status", parents=[common], help="change le statut d'une entrée"
    )
    set_status.add_argument("id")
    set_status.add_argument("statut")
    set_status.add_argument("--solution", help="solution (blocages seulement)")

    style_check = sub.add_parser(
        "style-check", parents=[common], help="contrôle de style d'un brouillon de rapport"
    )
    style_check.add_argument("gabarit", choices=GABARITS)
    style_check.add_argument("--from", dest="source", required=True, help="fichier du brouillon")
    return parser


def cmd_init(args, root):
    return registers.init(root)


def cmd_add(args, root):
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        raise CarnetError("json_invalide", str(exc))
    return registers.add(root, args.registre, data)


def cmd_set_status(args, root):
    return registers.set_status(root, args.id, args.statut, solution=args.solution)


def _read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise CarnetError("fichier_illisible", f"{path}: {exc}")


def cmd_style_check(args, root):
    text = _read_text(args.source)
    return {"warnings": style.check(text, args.gabarit, style.load_phrases(STYLE_FILE))}


HANDLERS = {
    "init": cmd_init,
    "add": cmd_add,
    "set-status": cmd_set_status,
    "style-check": cmd_style_check,
}


def emit(payload, code=0):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return code


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    try:
        return emit(HANDLERS[args.command](args, root))
    except CarnetError as exc:
        return emit({"error": exc.error, "detail": exc.detail}, 1)


if __name__ == "__main__":
    sys.exit(main())
