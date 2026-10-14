import json

import helpers
from carnet_lib import registers
from carnet_lib.errors import CarnetError


class AddTest(helpers.ProjectCase):
    def setUp(self):
        super().setUp()
        registers.init(self.root)

    def read(self, name):
        return (self.memory / f"{name}.md").read_text(encoding="utf-8")

    def test_premiere_decision(self):
        result = registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        self.assertEqual(result["id"], "BDR-001")
        self.assertEqual(result["warnings"], [])
        text = self.read("decisions")
        self.assertIn("| BDR-001 | 2026-10-14 | Registres par projet | actée |", text)
        self.assertTrue(
            text.endswith(
                "## BDR-001 · Registres par projet\n"
                "- **Date:** 2026-10-14\n"
                "- **Décision:** Un dossier .claude/memory par projet\n"
                "- **Pourquoi:** Chaque projet reste autonome\n"
                "- **Alternatives:** Un vault central\n"
                "- **Statut:** actée\n"
            )
        )

    def test_ids_successifs_et_index_dans_l_ordre(self):
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        second = registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-15")
        self.assertEqual(second["id"], "BDR-002")
        text = self.read("decisions")
        self.assertLess(text.index("| BDR-001 |"), text.index("| BDR-002 |"))
        self.assertLess(text.index("| BDR-002 |"), text.index("## BDR-001"))

    def test_l_id_suit_le_plus_grand_deja_present(self):
        path = self.memory / "decisions.md"
        text = path.read_text(encoding="utf-8")
        text += "| BDR-007 | 2026-10-01 | Ancienne | actée |\n\n## BDR-007 · Ancienne\n- **Date:** 2026-10-01\n"
        path.write_text(text, encoding="utf-8")
        result = registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        self.assertEqual(result["id"], "BDR-008")

    def test_blocage_par_defaut_ouvert_sans_solution(self):
        result = registers.add(self.root, "blockers", helpers.BLOCKER, today="2026-10-14")
        self.assertEqual(result["id"], "BLK-001")
        text = self.read("blockers")
        self.assertIn("| BLK-001 | 2026-10-14 | Chemin du script introuvable | ouvert |", text)
        self.assertTrue(text.endswith("- **Solution:**\n- **Statut:** ouvert\n"))

    def test_apprentissage_sans_statut(self):
        result = registers.add(self.root, "learnings", helpers.LEARNING, today="2026-10-14")
        self.assertEqual(result["id"], "LRN-001")
        self.assertIn("| LRN-001 | 2026-10-14 | Lire le schéma avant d'écrire la requête |", self.read("learnings"))

    def test_pipe_et_retours_a_la_ligne_ne_cassent_rien(self):
        data = dict(helpers.DECISION, titre="A | B", pourquoi="ligne 1\nligne 2")
        registers.add(self.root, "decisions", data, today="2026-10-14")
        text = self.read("decisions")
        self.assertIn("| BDR-001 | 2026-10-14 | A / B | actée |", text)
        self.assertIn("- **Pourquoi:** ligne 1 ligne 2\n", text)

    def test_champs_manquants(self):
        with self.assertRaises(CarnetError) as ctx:
            registers.add(self.root, "decisions", {"titre": "x"})
        self.assertEqual(ctx.exception.error, "champs_manquants")
        self.assertEqual(ctx.exception.detail, "decision, pourquoi")

    def test_statut_invalide(self):
        with self.assertRaises(CarnetError) as ctx:
            registers.add(self.root, "decisions", dict(helpers.DECISION, statut="bof"))
        self.assertEqual(ctx.exception.error, "statut_invalide")

    def test_date_invalide(self):
        with self.assertRaises(CarnetError) as ctx:
            registers.add(self.root, "decisions", dict(helpers.DECISION, date="hier"))
        self.assertEqual(ctx.exception.error, "date_invalide")

    def test_registre_illisible_refuse_d_ecrire(self):
        path = self.memory / "decisions.md"
        broken = path.read_text(encoding="utf-8").replace(
            "| ID | Date | Titre | Statut |", "| Identifiant | Date |"
        )
        path.write_text(broken, encoding="utf-8")
        with self.assertRaises(CarnetError) as ctx:
            registers.add(self.root, "decisions", helpers.DECISION)
        self.assertEqual(ctx.exception.error, "registre_illisible")
        self.assertTrue(ctx.exception.detail.startswith("decisions.md:"))
        self.assertEqual(path.read_text(encoding="utf-8"), broken)

    def test_registre_absent(self):
        other = self.root / "autre"
        other.mkdir()
        with self.assertRaises(CarnetError) as ctx:
            registers.add(other, "decisions", helpers.DECISION)
        self.assertEqual(ctx.exception.error, "registre_absent")

    def test_reference_inconnue_avertit_mais_ecrit(self):
        data = dict(helpers.DECISION, pourquoi="Suite à [[BLK-009]]")
        result = registers.add(self.root, "decisions", data, today="2026-10-14")
        self.assertEqual(result["warnings"], ["Référence [[BLK-009]] introuvable"])
        self.assertIn("| BDR-001 |", self.read("decisions"))

    def test_reference_connue_sans_avertissement(self):
        registers.add(self.root, "blockers", helpers.BLOCKER, today="2026-10-14")
        data = dict(helpers.DECISION, pourquoi="Suite à [[BLK-001]]")
        result = registers.add(self.root, "decisions", data, today="2026-10-14")
        self.assertEqual(result["warnings"], [])

    def test_journal(self):
        data = {"lignes": ["Parseur écrit.", "Tests verts."], "suite": "Écrire les skills"}
        result = registers.add(self.root, "journal", data, today="2026-10-14")
        self.assertIsNone(result["id"])
        self.assertEqual(result["date"], "2026-10-14")
        self.assertTrue(
            self.read("journal").endswith(
                "# Journal\n\n## 2026-10-14\nParseur écrit.\nTests verts.\nSuite: Écrire les skills\n"
            )
        )

    def test_journal_exige_lignes_et_suite(self):
        with self.assertRaises(CarnetError) as ctx:
            registers.add(self.root, "journal", {"lignes": ["x"]})
        self.assertEqual(ctx.exception.detail, "suite")
        with self.assertRaises(CarnetError) as ctx:
            registers.add(self.root, "journal", {"suite": "x"})
        self.assertEqual(ctx.exception.detail, "lignes")

    def test_journal_ligne_qui_ressemble_a_une_structure(self):
        data = {"lignes": ["## 2026-01-01", "Suite: fausse", "normale"], "suite": "vraie"}
        registers.add(self.root, "journal", data, today="2026-10-14")
        self.assertEqual(
            registers.read_journal(self.root),
            [
                {
                    "date": "2026-10-14",
                    "lignes": ["- ## 2026-01-01", "- Suite: fausse", "normale"],
                    "suite": "vraie",
                }
            ],
        )

    def test_journal_lignes_de_mauvais_type(self):
        for lignes in (5, {"a": 1}, [["x"]]):
            with self.subTest(lignes=lignes):
                with self.assertRaises(CarnetError) as ctx:
                    registers.add(self.root, "journal", {"lignes": lignes, "suite": "x"})
                self.assertEqual(ctx.exception.error, "entree_invalide")

    def test_cli_add_lit_le_json_sur_l_entree_standard(self):
        code, out, _ = helpers.run_cli(
            "add", "learnings", root=self.root, stdin=json.dumps(helpers.LEARNING)
        )
        self.assertEqual(code, 0)
        self.assertEqual(out["id"], "LRN-001")
        self.assertIn("2026-10-14", self.read("learnings"))

    def test_cli_json_invalide(self):
        code, out, _ = helpers.run_cli("add", "decisions", root=self.root, stdin="pas du json")
        self.assertEqual(code, 1)
        self.assertEqual(out["error"], "json_invalide")
