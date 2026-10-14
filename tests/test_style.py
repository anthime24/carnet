import helpers
from carnet_lib import style

PHRASES = ["il est important de noter", "n'hésitez pas", "robuste"]


class StyleTest(helpers.ProjectCase):
    def test_texte_propre(self):
        self.assertEqual(style.check("J'ai écrit le parseur.\nIl passe les tests.", "perso", PHRASES), [])

    def test_tiret_cadratin_avec_numero_de_ligne(self):
        warnings = style.check("ligne un\nligne deux — avec tiret", "perso", PHRASES)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["line"], 2)
        self.assertEqual(warnings[0]["motif"], "tiret cadratin")

    def test_expression_sans_casse(self):
        warnings = style.check("Début\nIl est important de noter que ça marche.", "perso", PHRASES)
        self.assertEqual(warnings[0]["line"], 2)
        self.assertEqual(warnings[0]["motif"], "expression à éviter: il est important de noter")

    def test_apostrophe_typographique(self):
        warnings = style.check("N’hésitez pas à me écrire.", "perso", PHRASES)
        self.assertEqual(len(warnings), 1)

    def test_mot_entier_seulement(self):
        self.assertEqual(style.check("La robustesse du parseur.", "perso", PHRASES), [])
        self.assertEqual(len(style.check("Un parseur robuste.", "perso", PHRASES)), 1)

    def test_ids_internes_seulement_pour_entreprise(self):
        text = "Voir BDR-001 pour la raison."
        self.assertEqual(style.check(text, "perso", []), [])
        warnings = style.check(text, "entreprise", [])
        self.assertEqual(warnings[0]["motif"], "ID interne: BDR-001")

    def test_references_croisees_pour_entreprise(self):
        warnings = style.check("Suite à [[BLK-001]]", "entreprise", [])
        motifs = [w["motif"] for w in warnings]
        self.assertIn("référence [[ ]] interne", motifs)
        self.assertIn("ID interne: BLK-001", motifs)

    def test_longueur_entreprise(self):
        long_text = " ".join(["mot"] * 301)
        warnings = style.check(long_text, "entreprise", [])
        self.assertEqual(warnings[0]["line"], 0)
        self.assertEqual(warnings[0]["motif"], "plus de 300 mots (301)")
        self.assertEqual(style.check(long_text, "perso", []), [])
        self.assertEqual(style.check(" ".join(["mot"] * 300), "entreprise", []), [])

    def test_charger_les_expressions(self):
        path = self.root / "style.txt"
        path.write_text("# commentaire\n\nrobuste\n  en conclusion  \n", encoding="utf-8")
        self.assertEqual(style.load_phrases(path), ["robuste", "en conclusion"])
        self.assertEqual(style.load_phrases(self.root / "absent.txt"), [])

    def test_cli_style_check(self):
        draft = self.root / "brouillon.md"
        draft.write_text("Bonjour\nIl convient de noter que oui.\n", encoding="utf-8")
        code, out, _ = helpers.run_cli("style-check", "perso", "--from", str(draft))
        self.assertEqual(code, 0)
        self.assertEqual(out["warnings"][0]["line"], 2)
        self.assertTrue(out["warnings"][0]["motif"].startswith("expression à éviter"))

    def test_cli_fichier_illisible(self):
        code, out, _ = helpers.run_cli("style-check", "perso", "--from", str(self.root / "absent.md"))
        self.assertEqual(code, 1)
        self.assertEqual(out["error"], "fichier_illisible")
