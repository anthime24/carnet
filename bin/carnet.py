#!/usr/bin/env python3
"""Carnet: registres de projet et matière première pour les rapports."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from carnet_lib import registers  # noqa: E402
from carnet_lib.errors import CarnetError  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project-root", default=".", help="dossier racine du projet (défaut: dossier courant)"
    )
    parser = argparse.ArgumentParser(prog="carnet.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", parents=[common], help="crée .claude/memory/ et les registres")
    return parser


def cmd_init(args, root):
    return registers.init(root)


HANDLERS = {"init": cmd_init}


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
