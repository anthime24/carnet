# Gabarit ENTREPRISE

Point d'étape pour un responsable d'entreprise. Une page, 250 mots au maximum. Il lit vite et n'a pas le contexte du projet.

## Squelette

```markdown
# <nom du projet>: point du <date>

## Où j'en suis

**Fait:** ...
**En cours:** ...
**À risque:** ...

## Blocages et ce qu'il me faut

...

## Prochaines étapes

...
```

Supprime la ligne `À risque` s'il n'y a rien à signaler. Supprime `En cours` de la même façon.

## D'où vient chaque section

Tout vient de la sortie de `context`. Rien d'autre.

- **Où j'en suis**: le fait vient des `lignes` du journal et de `claude_mem.summaries[].completed`. L'en cours et les risques se déduisent des lignes `suite` et des blocages ouverts. Une décision n'apparaît que si elle change la direction du projet.
- **Blocages et ce qu'il me faut**: `registers.blockers.open`. Pour chacun, une phrase sur ce qui coince, puis ce dont j'ai besoin (une décision, une information, un accès) ou "je n'attends rien". Les blocages de `resolved`: une ligne chacun, sans l'histoire. S'il n'y en a aucun, écris "Rien de bloquant."
- **Prochaines étapes**: la ligne `suite` de l'entrée de journal la plus récente. Une échéance seulement si une date figure dans les registres. Sinon écris "pas de date arrêtée".

## Règles de fond

- Écris pour un lecteur extérieur. Pas d'IDs (`BDR-001`), pas de `[[ ]]`, pas de jargon de l'outil, pas de nom de fichier interne sauf s'il parle au lecteur.
- La `cause` et la `friction` d'un blocage servent à comprendre la situation. Ne les cite jamais telles quelles: reformule avec sobriété ce qui coince, pas qui a mal fait quoi, ni les galères de l'auteur.
- Les lignes du journal peuvent citer des IDs (`BLK-001`) ou des `[[ ]]`: retire-les.
- Ne raconte pas le chemin parcouru. Dis où on en est.
- Chaque affirmation vient des registres ou de claude-mem. N'invente ni date, ni chiffre, ni avancement.
- Les résumés claude-mem sont souvent en anglais. Réécris-les en français.
- Un résumé marqué `unvalidated` n'a pas eu son rituel: signale-le à l'utilisateur avant qu'il envoie le rapport.

## Règles de style

- Première personne ("j'ai"), ou "on" quand les registres décrivent un travail à plusieurs.
- Phrases courtes, un fait par phrase. Des noms précis (outil, durée, livrable) plutôt que des généralités.
- Pas de tiret cadratin. Pas de conclusion qui répète le texte.
- Pas de formules creuses ("il est important de noter", "n'hésitez pas") ni d'adjectifs flatteurs sur son propre travail.
- Un blocage se raconte en trois temps: ce qui s'est passé, la cause, où ça en est. Sans dramatiser.
- Français, accents corrects.
- Une fois le brouillon écrit, lance `style-check` et corrige ce qu'il signale avant de montrer le rapport.
