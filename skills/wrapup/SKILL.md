---
name: wrapup
description: Rituel de fin de session. Relit la session, propose des entrées pour les registres décisions, apprentissages et blocages du projet, ajoute toujours une entrée au journal avec la suite, et n'écrit qu'après accord de l'utilisateur. À utiliser quand l'utilisateur veut clôturer une session, faire le point, ou lance le rituel de fermeture.
---

# Rituel de fin de session

Le script du plugin fait la partie mécanique (IDs, index, lecture de claude-mem). Toi, tu relis la session, tu proposes, tu rédiges. Le script répond toujours en JSON. Une erreur donne `{"error": ..., "detail": ...}`.

Les commandes s'exécutent dans le dossier du projet. Si tu travailles ailleurs, ajoute `--project-root <chemin>`. Écris le chemin du script en entier à chaque appel Bash, l'état du shell ne se conserve pas d'un appel à l'autre.

## 1. Préparer

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" init
```

`init` ne remplace jamais un fichier existant. Si `created` n'est pas vide et que le dossier est un dépôt git (`git rev-parse --is-inside-work-tree`), demande une seule fois s'il faut ajouter `.claude/memory/` au `.gitignore`, parce que les registres PERSO contiennent des notes franches. N'y touche que si l'utilisateur dit oui.

## 2. Lire l'état

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" context --since journal
```

Regarde:
- `registers.blockers.open`: les blocages encore ouverts.
- `registers.last_dates`: la date de la dernière entrée de chaque registre.
- `claude_mem.summaries`: ceux marqués `unvalidated: true` viennent de sessions passées sans rituel. Ils sont souvent en anglais, réécris-les en français.
- Si `claude_mem.status` vaut `unavailable`, dis-le en une ligne (avec `reason`) et continue avec la session en cours.

## 3. Relire la session

Cherche quatre choses, dans la session en cours et dans les résumés non validés:
1. **Décidé**: ce qui a été décidé et qui comptera encore dans un mois.
2. **Appris**: ce qui a été observé et change la façon de faire.
3. **Bloqué**: tout ce qui a coûté plus de 30 minutes, même si c'est résolu.
4. **Résolu**: les blocages de `registers.blockers.open` qui ont été réglés pendant la session.

## 4. Proposer

Montre à l'utilisateur, en français courant et pas en JSON:
- Pour chacun des trois registres (décisions, apprentissages, blocages): une entrée prête à ajouter, ou "Rien à ajouter" avec la raison en une phrase. Répondre non est normal, une session de routine n'a pas besoin de BDR.
- Les changements de statut proposés (blocage résolu, avec sa solution).
- L'entrée de journal, toujours: 3 à 5 lignes factuelles (ce qui a été fait, les IDs créés) et une ligne `Suite:`. Mets une date dans `Suite:` seulement si l'utilisateur en a donné une.

Pose une seule question, et seulement si un point est vraiment ambigu.

Pour lier des entrées, écris `[[BDR-001]]` dans le texte.

Champs de chaque registre (tous en texte, sur une ligne):
- `decisions`: `titre`, `decision`, `pourquoi`, `alternatives` (facultatif), `statut` (facultatif, `actée` par défaut).
- `learnings`: `titre`, `pattern`, `contexte`, `application`.
- `blockers`: `titre`, `friction`, `cause` (la cause réelle), `solution` (facultatif), `statut` (`ouvert` par défaut).
- `journal`: `lignes` (liste de phrases) et `suite`.

## 5. Attendre l'accord

Attends l'accord de l'utilisateur. N'écris rien avant. S'il corrige, reprends la proposition et montre-la à nouveau.

## 6. Écrire

Après l'accord, dans cet ordre: décisions, apprentissages, blocages, changements de statut, puis le journal en dernier pour qu'il cite les IDs créés (ils sont dans les réponses du script).

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" add decisions <<'JSON'
{"titre": "...", "decision": "...", "pourquoi": "...", "alternatives": "..."}
JSON
```

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" set-status BLK-001 résolu --solution "..."
```

```bash
python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" add journal <<'JSON'
{"lignes": ["...", "..."], "suite": "..."}
JSON
```

Lis `warnings` dans chaque réponse: une "référence introuvable" veut dire que tu as cité un ID qui n'existe pas, corrige-le avec l'utilisateur. Si l'erreur est `registre_illisible`, montre `detail` à l'utilisateur et ne tente pas de réparer le fichier à l'aveugle.

## 7. Récap

Trois lignes:
- ce qui a été ajouté aujourd'hui,
- les blocages encore ouverts (nombre et titres),
- une alerte pour chaque registre dont `last_dates` est vide ou remonte à plus de 14 jours avant `until`.

## Style

Ce que tu écris dans les registres est relu des mois plus tard par l'utilisateur, et parfois par d'autres. Reste naturel et direct: phrases courtes, "j'ai", faits précis, pas de formules creuses, pas de tiret cadratin, pas d'adjectifs flatteurs.
