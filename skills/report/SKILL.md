---
name: report
description: Génère un rapport de projet en Markdown, au gabarit PERSO (pour soi) ou ENTREPRISE (pour un responsable d'entreprise), à partir des registres du projet, de claude-mem et de graphify. À utiliser quand l'utilisateur veut un rapport, un point d'étape ou un résumé à envoyer. Arguments, perso ou entreprise, puis --depuis <date> ou --tout.
---

# Rapport de projet

Arguments reçus: $ARGUMENTS

Le script du plugin fait la partie mécanique. Toi, tu rédiges à partir de ce qu'il te donne. Le script répond toujours en JSON. Une erreur donne `{"error": ..., "detail": ...}`.

Les commandes s'exécutent dans le dossier du projet. Si tu travailles ailleurs, ajoute `--project-root <chemin>`. Écris le chemin du script en entier à chaque appel Bash.

## 1. Gabarit et période

- Gabarit: `perso` ou `entreprise`. S'il manque, demande lequel.
- Période:
  - `--depuis <date>`: `--since <date>`.
  - `--tout`: pas de `--since`.
  - par défaut: `--since rapport`, c'est-à-dire depuis le dernier rapport du même gabarit.

## 2. Rassembler la matière

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" context --since rapport --gabarit entreprise
```

Remplace `entreprise` par le gabarit choisi, et ajuste `--since` selon la période. Avec `--tout`, retire `--since` et garde `--gabarit`.

Si `previous_report` n'est pas `null`, lis le fichier indiqué dans `path` pour ne pas répéter ce qu'il couvrait déjà.

## 3. Vérifier qu'il y a de quoi écrire

- Si `project.initialized` vaut `false`, ou si les registres sont vides sur la période mais que `claude_mem.summaries` contient des résumés: propose de lancer `/carnet:wrapup` d'abord, c'est ce qui rend le rapport fiable. Si l'utilisateur préfère continuer, fais un brouillon et mets en première ligne `> Brouillon non validé: basé sur claude-mem sans rituel de fermeture`. Dis-lui de retirer cette ligne avant d'envoyer.
- Si rien n'existe sur la période (ni registres, ni résumés), dis-le et arrête-toi. N'écris pas de rapport vide.
- Si `claude_mem.status` vaut `unavailable`, dis-le en une ligne (avec `reason`) et continue avec les registres.

## 4. Rédiger

Lis le gabarit avec l'outil Read:
- `${CLAUDE_SKILL_DIR}/../../templates/perso.md`
- `${CLAUDE_SKILL_DIR}/../../templates/entreprise.md`

Suis-le à la lettre: squelette, d'où vient chaque section, règles de fond, règles de style. Trois règles passent avant tout:
1. Chaque affirmation vient d'une entrée de registre ou d'un résumé claude-mem. N'invente rien, ni fait, ni date, ni chiffre.
2. Les résumés claude-mem sont souvent en anglais. Réécris-les en français.
3. Un résumé `unvalidated` n'a pas eu son rituel: dis-le à l'utilisateur.

## 5. Contrôler le style

Écris le brouillon dans un fichier temporaire, puis lance le contrôle dans le même appel Bash:

```bash
draft="$(mktemp)"
cat > "$draft" <<'MD'
(le rapport)
MD
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" style-check entreprise --from "$draft"
echo "brouillon: $draft"
```

Remplace `entreprise` par le gabarit choisi. Corrige chaque avertissement de `warnings` (tiret cadratin, expression creuse, ID interne, trop de mots), puis relance jusqu'à ce qu'il n'en reste plus, ou jusqu'à ce que les restes soient voulus. Les avertissements ne bloquent jamais: l'utilisateur a le dernier mot.

## 6. Montrer, retoucher, valider

Affiche le rapport. L'utilisateur demande des retouches, tu les fais et tu relances le contrôle de style. Quand il valide:

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" save-report entreprise --from /tmp/chemin-du-brouillon --du 2026-10-01 --au 2026-10-14
```

- `--from`: le chemin du brouillon affiché à l'étape 5.
- `--du`: la valeur `since` de la sortie de `context`, ou le mot `début` quand elle vaut `null`.
- `--au`: la valeur `until` de la sortie de `context`.

Donne à l'utilisateur le `path` du rapport enregistré. S'il reste des `warnings`, rappelle-les.
