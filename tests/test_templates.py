import unittest

import helpers

PERSO = [
    "## Ce que j'ai fait",
    "## Décisions",
    "## Ce que j'ai appris",
    "## Ce qui a bloqué",
    "## Fichiers touchés",
    "## La suite",
]
ENTREPRISE = ["## Où j'en suis", "## Blocages et ce qu'il me faut", "## Prochaines étapes"]


class TemplatesTest(unittest.TestCase):
    def read(self, name):
        return (helpers.ROOT / "templates" / name).read_text(encoding="utf-8")

    def test_sections_du_gabarit_perso(self):
        text = self.read("perso.md")
        for heading in PERSO:
            self.assertIn(heading, text)

    def test_sections_du_gabarit_entreprise(self):
        text = self.read("entreprise.md")
        for heading in ENTREPRISE:
            self.assertIn(heading, text)

    def test_regles_de_style_dans_les_deux_gabarits(self):
        for name in ("perso.md", "entreprise.md"):
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("## Règles de style", text)
                self.assertIn("## D'où vient chaque section", text)
                self.assertIn("style-check", text)

    def test_entreprise_fixe_la_limite_de_longueur(self):
        self.assertIn("250 mots", self.read("entreprise.md"))
