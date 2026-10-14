# Carnet: design

Date: 2026-10-14
Statut: à relire par l'utilisateur avant le plan d'implémentation

## But

Carnet est un plugin Claude Code pour un étudiant qui enchaîne les projets. Il garde une mémoire durable et relue par l'utilisateur dans chaque projet, et il en tire des rapports pour deux lecteurs: l'utilisateur lui-même (PERSO) et des responsables d'entreprise (ENTREPRISE). Chaque rapport dit ce qui a été fait, ce qui a bloqué et ce qui vient ensuite.

La mémoire s'inspire de la page Notion "La vraie mémoire de ton agent Claude Code: 5 registres + rituel + Obsidian" (registres numérotés, rituel de fermeture en 3 questions, références `[[ID]]` compatibles Obsidian). Elle s'appuie sur deux outils que l'utilisateur a déjà: claude-mem (résumés de sessions) et graphify (graphe de connaissances, optionnel).

## Hors périmètre de la v1

- Pas de gabarit PROF.
- Pas de PDF, Word ni HTML: Markdown seulement.
- Pas de hook, ni de brouillon automatique à la fermeture de session. Tout passe par deux commandes.
- Pas de `evals.md`: ce registre sert à évaluer des sorties d'IA et colle mal à ces projets.
- Pas de serveur MCP.
- Pas de vault Obsidian central: les registres vivent dans chaque projet.

## Décisions de cadrage

| Sujet | Choix |
|---|---|
| Mémoire | Registres durables validés par l'utilisateur, rapports générés depuis ces registres |
| Emplacement | `<projet>/.claude/memory/` |
| Formats | Markdown seulement |
| Déclenchement | Commandes `/carnet:wrapup` et `/carnet:report`, aucun hook |
| Gabarits | Deux gabarits fixes: PERSO et ENTREPRISE |
| Période d'un rapport | Depuis le dernier rapport du même gabarit, modifiable par `--depuis <date>` ou `--tout` |
| Ton | Naturel et direct, règles de style écrites dans les gabarits |
| Architecture | Skills (conversation et rédaction) + script Python (partie déterministe) |

## Structure du plugin

```
carnet/
  .claude-plugin/plugin.json
  skills/
    wrapup/SKILL.md          rituel de fin de session
    report/SKILL.md          génération d'un rapport PERSO ou ENTREPRISE
  templates/
    perso.md                 gabarit + règles de style
    entreprise.md            gabarit + règles de style
    style.txt                expressions à éviter, une par ligne
  bin/carnet.py              point d'entrée du script (Python 3.9+, bibliothèque standard seulement)
  bin/carnet_lib/            modules du script: registers, sources, context, reports, style
  tests/                     tests unittest
  docs/superpowers/specs/    cette spec
```

Les skills appellent le script par `python3 "${CLAUDE_SKILL_DIR}/../../bin/carnet.py" <commande>`. `${CLAUDE_SKILL_DIR}` est la variable que les skills de claude-mem utilisent déjà pour ça (voir "Points à vérifier").

## Données dans chaque projet

```
<projet>/.claude/memory/
  decisions.md   learnings.md   blockers.md   journal.md
  reports/       AAAA-MM-JJ-perso.md, AAAA-MM-JJ-entreprise.md
```

Chaque registre a un header YAML, un tableau d'index et des entrées. Les entrées peuvent citer d'autres entrées avec `[[BDR-001]]`. Le script traite ces références comme du texte, sauf pour émettre un avertissement quand l'ID cité n'existe pas.

### decisions.md (préfixe BDR)

```markdown
---
registre: decisions
prefixe: BDR
---
# Décisions

## Index
| ID | Date | Titre | Statut |
|----|------|-------|--------|
| BDR-001 | 2026-10-14 | Registres par projet | actée |

## BDR-001 · Registres par projet
- **Date:** 2026-10-14
- **Décision:** ...
- **Pourquoi:** ...
- **Alternatives:** ...
- **Statut:** actée
```

Statuts: `actée`, `remplacée`, `abandonnée`.

### learnings.md (préfixe LRN)

Même forme. Champs: `Date`, `Pattern observé`, `Contexte`, `Application future`. L'index a les colonnes `ID | Date | Titre`.

### blockers.md (préfixe BLK)

Même forme. Champs: `Date`, `Friction`, `Cause réelle`, `Solution`, `Statut`. Statuts: `ouvert`, `résolu`. Index: `ID | Date | Titre | Statut`. `Solution` reste vide tant que le blocage est ouvert. Quand `set-status` passe un blocage à `résolu`, il ajoute la ligne `- **Résolu le:** AAAA-MM-JJ` après `Statut` (et la retire si le blocage est rouvert).

### journal.md

Pas d'index. Une entrée par rituel, en ordre chronologique:

```markdown
## 2026-10-14
3 à 5 lignes factuelles: ce qui a été fait, les BDR/LRN/BLK créés.
Suite: ce qui vient ensuite, avec une date si elle existe.
```

Plusieurs entrées le même jour sont permises. La ligne `Suite:` de l'entrée la plus récente alimente la rubrique "suite" des rapports.

### reports/

Un rapport validé est enregistré sous `reports/AAAA-MM-JJ-<gabarit>.md` (suffixe `-2`, `-3` en cas de collision). Un petit header YAML garde le gabarit et la période (`du`, `au`). Il n'y a pas de fichier d'état: la date du dernier rapport se lit dans les noms de fichiers.

## Le script `carnet.py`

Toutes les commandes acceptent `--project-root <chemin>` (défaut: dossier courant) et répondent en JSON sur la sortie standard. Une erreur donne un code de sortie non nul et un JSON `{"error": "...", "detail": "..."}`.

| Commande | Rôle |
|---|---|
| `init` | Crée `.claude/memory/` et les quatre registres vides (header + index). N'écrase jamais un fichier existant. |
| `add <registre>` | Lit l'entrée en JSON sur l'entrée standard. Attribue l'ID suivant, ajoute l'entrée, ajoute la ligne d'index. Renvoie l'ID et d'éventuels avertissements. Pour `journal`, ajoute l'entrée du jour. |
| `set-status <ID> <statut>` | Change le statut d'une entrée (entrée et ligne d'index). Pour un blocage résolu, accepte `--solution "..."`. |
| `context [--since <date\|journal\|rapport>] [--until <date>] [--gabarit <g>]` | Rassemble la matière brute, voir plus bas. `journal` = depuis la dernière entrée du journal, `rapport` = depuis le dernier rapport de `--gabarit`. |
| `last-report <gabarit>` | Renvoie la date et le chemin du dernier rapport de ce gabarit, ou `null`. |
| `save-report <gabarit> --from <fichier> --du <date> --au <date>` | Enregistre le rapport dans `reports/` et renvoie le chemin avec le résultat du contrôle de style. |
| `style-check <gabarit> --from <fichier>` | Applique seulement le contrôle de style. |

Les écritures passent par un fichier temporaire puis un renommage. Si un registre est illisible (header absent, tableau d'index cassé après une édition manuelle), `add` et `set-status` refusent d'écrire et indiquent la ligne fautive.

### Sortie de `context`

```json
{
  "project": {"root": "...", "name": "...", "initialized": true},
  "since": "2026-10-01", "until": "2026-10-14",
  "registers": {
    "decisions": [...], "learnings": [...],
    "blockers": {"opened": [...], "open": [...], "resolved": [...]},
    "journal": [...],
    "last_journal_date": "2026-10-12",
    "last_dates": {"decisions": "...", "learnings": null, "blockers": "...", "journal": "..."}
  },
  "previous_report": {"gabarit": "entreprise", "date": "...", "path": "..."},
  "claude_mem": {
    "status": "ok", "match": "cwd",
    "summaries": [{"date": "...", "request": "...", "investigated": "...",
                   "learned": "...", "completed": "...", "next_steps": "...",
                   "files_edited": [...], "unvalidated": true}]
  },
  "graphify": {"status": "ok", "excerpt": "..."}
}
```

- `since` est inclusif, `until` aussi, au jour près. Sans `--since`, `context` remonte tout le projet.
- `blockers.opened` liste les blocages créés dans la période. `open` liste tous les blocages encore ouverts, quelle que soit leur date. `resolved` liste ceux résolus dans la période.
- Un résumé claude-mem est `unvalidated` si sa date est strictement postérieure à `last_journal_date`: la session n'a pas encore eu son rituel.
- `previous_report` est présent quand un rapport du gabarit demandé existe déjà. La skill le lit pour ne pas répéter ce qu'il couvrait.

## Sources externes

### claude-mem

- Base: `~/.claude-mem/claude-mem.db`, chemin remplaçable par la variable d'environnement `CARNET_CLAUDE_MEM_DB` (utile pour les tests).
- Ouverture en lecture seule: `sqlite3.connect("file:<chemin>?mode=ro", uri=True)`, délai d'attente court.
- Requête sur `session_summaries` jointe à `sdk_sessions` par `memory_session_id`. Champs lus: `request, investigated, learned, completed, next_steps, files_edited, created_at`.
- Correspondance au projet: sessions dont le `cwd` est la racine ou un sous-dossier, plus les sessions de même `project` que le nom du dossier racine dont le `cwd` est absent ou n'est pas un chemin POSIX (sessions enregistrées sous un autre système). Si rien ne correspond, repli sur le seul `project`. `match` vaut `"cwd"`, `"name"` ou `"cwd+name"`.
- Chaque champ de résumé est tronqué à 500 caractères. La date d'un résumé est la partie date de `created_at` (UTC).
- Les résumés réels sont rédigés en anglais: les skills et les gabarits demandent de les réécrire en français.
- Si la base est absente, verrouillée, ou si une table ou colonne attendue manque, `claude_mem.status` vaut `"unavailable"` avec une `reason`. Le reste de `context` n'est pas affecté.

### graphify

- Si `<projet>/graphify-out/GRAPH_REPORT.md` existe, `excerpt` contient ses premières lignes utiles (limite de taille fixe). Sinon `status` vaut `"absent"`, sans message pour l'utilisateur.
- graphify sert uniquement à décrire le projet dans le rapport PERSO (modules principaux). Il ne sert jamais de source pour un fait sur l'avancement.

## Skill `/carnet:wrapup`

Reprend le rituel de la page Notion.

1. Si `.claude/memory/` n'existe pas, lance `init`. Dans un dépôt git, demande une fois s'il faut ajouter `.claude/memory/` au `.gitignore`: les registres PERSO contiennent des notes franches.
2. Lance `context --since <last_journal_date>`. Les sessions passées sans rituel arrivent via les résumés claude-mem `unvalidated`.
3. Relit la session en cours et ce contexte, puis cherche: les décisions qui compteront dans un mois, les observations qui changent la façon de faire, les blocages qui ont coûté plus de 30 minutes (même résolus), et les blocages ouverts qui viennent d'être résolus.
4. Propose, pour chacun des trois registres, une entrée formatée prête à l'ajout ou un "rien à ajouter" avec la raison. Propose aussi les changements de statut de blocages. Toujours une entrée de journal avec sa ligne `Suite:`. Au plus une question si un point est ambigu.
5. Affiche tout et attend l'accord. Rien n'est écrit avant. Après l'accord, appelle `add` et `set-status`.
6. Termine par un récap en trois lignes: ce qui a été ajouté, les blocages encore ouverts, et une alerte si un registre n'a rien reçu depuis plus de deux semaines.

## Skill `/carnet:report perso|entreprise [--depuis <date> | --tout]`

1. Sans argument, demande quel gabarit. Détermine la période: `--depuis`, `--tout`, sinon la date du dernier rapport du même gabarit (`last-report`).
2. Lance `context` pour cette période.
3. Si les registres sont vides sur la période mais que claude-mem a des résumés, propose de lancer `/carnet:wrapup` d'abord. Si l'utilisateur préfère continuer, fait un brouillon marqué "non validé".
4. Remplit le gabarit en suivant ses règles de style. Chaque affirmation vient d'une entrée de registre ou d'un résumé claude-mem. Si la période est vide, le dit au lieu de broder. Les dates et échéances viennent seulement des lignes `Suite:` ou des registres.
5. Écrit le brouillon dans un fichier temporaire, lance `style-check`, corrige les signalements, puis affiche le rapport.
6. L'utilisateur demande des retouches ou valide. À la validation, `save-report` enregistre le rapport.

## Gabarits

### PERSO

Sections: `Ce que j'ai fait`, `Décisions`, `Ce que j'ai appris`, `Ce qui a bloqué`, `Fichiers touchés`, `La suite`.

- `Ce qui a bloqué`: ce qui s'est passé, la cause réelle, où ça en est.
- `Décisions`: la décision, la raison, les alternatives écartées. Les IDs (`BDR-001`) sont gardés.
- `Fichiers touchés`: issu de claude-mem seulement, si disponible.
- Une ligne de contexte en tête peut s'appuyer sur graphify pour dire ce qu'est le projet.
- Pas de limite de longueur, mais pas de remplissage.

### ENTREPRISE

Sections: `Où j'en suis` (fait / en cours / à risque), `Blocages et ce qu'il me faut`, `Prochaines étapes`.

- Une page, environ 250 mots au maximum.
- Réécrit pour un lecteur extérieur: pas d'IDs internes, pas de `[[ ]]`, pas de jargon de l'outil, pas de détail franc qui n'a pas sa place dans un point externe (la `Cause réelle` d'un blocage est reformulée avec sobriété).
- Chaque blocage dit ce dont l'auteur a besoin (une décision, une information, un accès) ou précise qu'il n'attend rien.
- Les échéances viennent des lignes `Suite:`. Sans date connue: "pas de date arrêtée". Jamais de date inventée.

### Règles de style (dans les deux gabarits)

- Première personne ("j'ai"), ou "on" quand les registres décrivent un travail à plusieurs.
- Phrases courtes, un fait par phrase, noms précis (fichier, outil, durée) plutôt que des généralités.
- Pas de tiret cadratin. Pas de conclusion qui répète le texte.
- Pas de formules creuses, pas d'adjectifs flatteurs sur son propre travail.
- Un blocage se raconte en trois temps: ce qui s'est passé, la cause, où ça en est.
- Français, accents corrects.

### Contrôle de style

`style-check` renvoie une liste d'avertissements (ligne, motif). Il ne bloque jamais: la skill corrige puis réessaie, et l'utilisateur a le dernier mot.

- Tous les gabarits: tiret cadratin `—`, et les expressions listées dans `templates/style.txt` (une par ligne, modifiable par l'utilisateur). Liste initiale: "il est important de noter", "il convient de", "n'hésitez pas", "dans le cadre de", "force est de", "je tiens à", "en conclusion", "en résumé", "robuste", "solution complète".
- ENTREPRISE en plus: IDs de la forme `BDR-001`, `LRN-001`, `BLK-001`, références `[[`, et plus de 300 mots (l'objectif reste 250, le seuil d'alerte laisse une marge).

## Erreurs

| Situation | Comportement |
|---|---|
| claude-mem absent, verrouillé ou au schéma différent | `claude_mem.status = "unavailable"` avec la raison. Les skills le disent en une ligne et continuent avec les registres. |
| graphify absent | Ignoré en silence. |
| Registre illisible après édition manuelle | `add` et `set-status` refusent d'écrire, indiquent la ligne fautive, ne réécrivent jamais à l'aveugle. |
| Référence `[[ID]]` vers un ID inexistant | Avertissement dans la réponse de `add`, écriture faite. |
| `.claude/memory/` absent | `wrapup` lance `init`. `report` propose `wrapup` d'abord. |
| Période sans aucune matière | La skill le dit et ne produit pas de rapport. |
| Projet non détecté | Dossier courant par défaut, `--project-root` pour forcer. |

## Tests

- Le script est testé avec `unittest` (`python3 -m unittest discover -s tests`), sans dépendance.
- Une fausse base claude-mem est construite dans les tests d'après le schéma réel de `session_summaries` et `sdk_sessions` (version 13.37.0 de claude-mem).
- Cas couverts: `init` qui n'écrase rien, IDs successifs, index à jour après `add` et `set-status`, refus d'écrire sur un registre cassé, filtrage par date (bornes incluses), `blockers.open` indépendant de la période, résumé `unvalidated`, correspondance `cwd` puis `name`, `last-report` avec plusieurs rapports, collision de noms dans `save-report`, contrôle de style (tiret cadratin, expressions, IDs et longueur pour ENTREPRISE), sources manquantes (base absente, colonne absente, graphify absent).
- Les deux skills sont des consignes, pas du code. Elles sont vérifiées à la main sur un projet jetable avec une checklist qui figure dans le plan (rituel complet, rapport PERSO, rapport ENTREPRISE, cas "registres vides", cas "claude-mem indisponible").

## Points à vérifier au début du plan

1. `${CLAUDE_SKILL_DIR}/../../bin/carnet.py` se résout bien quand le plugin est installé (les skills de claude-mem l'utilisent, mais la remontée de deux niveaux n'est pas testée). Repli possible: placer le script dans chaque skill ou utiliser `${CLAUDE_PLUGIN_ROOT}`.
2. Les noms invoqués: `/carnet:wrapup` et `/carnet:report` (espace de noms du plugin) fonctionnent, et le plugin se charge avec `claude --plugin-dir ~/Documents/carnet` pour le développement.
3. Les versions futures de claude-mem peuvent changer le schéma: le comportement dégradé décrit plus haut couvre ce cas, les tests le simulent.
