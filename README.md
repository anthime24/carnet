# Carnet

Plugin Claude Code pour garder une mémoire de projet relue par toi, et en tirer des rapports.

- `/carnet:wrapup` fait le rituel de fin de session. Claude relit la session et propose des entrées pour `decisions`, `learnings`, `blockers` et `journal`. Rien n'est écrit sans ton accord.
- `/carnet:report perso|entreprise` écrit un rapport en Markdown depuis ces registres, avec les résumés de claude-mem et le rapport de graphify s'il existe. Options: `--depuis <date>`, `--tout`.

Les registres vivent dans `<projet>/.claude/memory/`. C'est du Markdown à plat, tu peux ouvrir ce dossier comme vault Obsidian. Les rapports validés vont dans `reports/`.

## Installer (développement)

```bash
claude --plugin-dir ~/Documents/carnet
```

## Tests

```bash
python3 -m unittest discover -s tests
```

Python 3.9+, aucune dépendance.

## Pour changer le ton

Ajoute les expressions que tu repères dans les rapports générés à `templates/style.txt`, une par ligne. Les règles de style complètes sont dans `templates/perso.md` et `templates/entreprise.md`.
