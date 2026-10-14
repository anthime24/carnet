# Gabarit PERSO

Rapport pour moi. Détaillé, honnête, technique. Pas de limite de longueur, mais pas de remplissage.

## Squelette

```markdown
# Point perso: <nom du projet>, du <date de début> au <date de fin>

<Une ligne qui dit ce qu'est le projet.>

## Ce que j'ai fait

## Décisions

## Ce que j'ai appris

## Ce qui a bloqué

## Fichiers touchés

## La suite
```

## D'où vient chaque section

Tout vient de la sortie de `context`. Rien d'autre.

- **Ligne sous le titre**: ce qu'est le projet. Appuie-toi sur `graphify.excerpt` s'il existe, sinon sur le journal. C'est le seul usage de graphify.
- **Ce que j'ai fait**: les `lignes` du journal sur la période, complétées par `claude_mem.summaries[].completed`. Regroupe par sujet si ça se lit mieux qu'une liste par date.
- **Décisions**: `registers.decisions`. Pour chaque décision: ce qui a été décidé, pourquoi, ce qui a été écarté. Garde les IDs (`BDR-001`).
- **Ce que j'ai appris**: `registers.learnings`, avec leurs IDs.
- **Ce qui a bloqué**: `registers.blockers.opened`, `resolved` et `open`. Les blocages encore ouverts viennent en premier. Pour chacun, trois temps: ce qui s'est passé, la cause réelle, où ça en est.
- **Fichiers touchés**: les `files_edited` de `claude_mem.summaries`, sans doublon. Si claude-mem est indisponible ou si la liste est vide, supprime la section au lieu de la laisser vide.
- **La suite**: la ligne `suite` de l'entrée de journal la plus récente, puis les blocages encore ouverts qui demandent une action.

## Règles de fond

- Chaque affirmation vient d'une entrée de registre ou d'un résumé claude-mem. Si la période est vide, dis-le. N'invente rien.
- Les résumés claude-mem sont souvent en anglais. Réécris-les en français.
- Un résumé marqué `unvalidated` n'a pas eu son rituel. Tu peux t'en servir, mais signale-le à l'utilisateur.
- Aucune date ni échéance qui ne figure pas dans les registres.

## Règles de style

- Première personne ("j'ai"), ou "on" quand les registres décrivent un travail à plusieurs.
- Phrases courtes, un fait par phrase. Des noms précis (fichier, outil, durée) plutôt que des généralités.
- Pas de tiret cadratin. Pas de conclusion qui répète le texte.
- Pas de formules creuses ("il est important de noter", "n'hésitez pas") ni d'adjectifs flatteurs sur son propre travail.
- Un blocage se raconte en trois temps: ce qui s'est passé, la cause, où ça en est. Sans dramatiser.
- Français, accents corrects.
- Une fois le brouillon écrit, lance `style-check` et corrige ce qu'il signale avant de montrer le rapport.
