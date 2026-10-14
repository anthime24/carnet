import helpers
from carnet_lib import registers
from carnet_lib.errors import CarnetError


class SetStatusTest(helpers.ProjectCase):
    def setUp(self):
        super().setUp()
        registers.init(self.root)
        registers.add(self.root, "blockers", helpers.BLOCKER, today="2026-10-14")
        registers.add(self.root, "blockers", dict(helpers.BLOCKER, titre="Deuxième"), today="2026-10-14")

    def read(self, name):
        return (self.memory / f"{name}.md").read_text(encoding="utf-8")

    def test_resoudre_un_blocage_avec_solution(self):
        result = registers.set_status(
            self.root, "BLK-001", "résolu", solution="Chemin corrigé", today="2026-10-15"
        )
        self.assertEqual(result["statut"], "résolu")
        text = self.read("blockers")
        self.assertIn("| BLK-001 | 2026-10-14 | Chemin du script introuvable | résolu |", text)
        self.assertIn(
            "- **Solution:** Chemin corrigé\n- **Statut:** résolu\n- **Résolu le:** 2026-10-15\n",
            text,
        )

    def test_l_autre_blocage_ne_bouge_pas(self):
        registers.set_status(self.root, "BLK-001", "résolu", today="2026-10-15")
        text = self.read("blockers")
        self.assertIn("| BLK-002 | 2026-10-14 | Deuxième | ouvert |", text)
        self.assertTrue(text.endswith("- **Solution:**\n- **Statut:** ouvert\n"))

    def test_resoudre_le_dernier_blocage_du_fichier(self):
        registers.set_status(self.root, "BLK-002", "résolu", today="2026-10-15")
        self.assertTrue(self.read("blockers").endswith("- **Statut:** résolu\n- **Résolu le:** 2026-10-15\n"))

    def test_rouvrir_retire_la_date_de_resolution(self):
        registers.set_status(self.root, "BLK-001", "résolu", today="2026-10-15")
        registers.set_status(self.root, "BLK-001", "ouvert")
        text = self.read("blockers")
        self.assertNotIn("Résolu le", text)
        self.assertIn("| BLK-001 | 2026-10-14 | Chemin du script introuvable | ouvert |", text)

    def test_statut_d_une_decision(self):
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        registers.set_status(self.root, "BDR-001", "remplacée")
        text = self.read("decisions")
        self.assertIn("| BDR-001 | 2026-10-14 | Registres par projet | remplacée |", text)
        self.assertTrue(text.endswith("- **Statut:** remplacée\n"))

    def test_apprentissage_sans_statut(self):
        registers.add(self.root, "learnings", helpers.LEARNING, today="2026-10-14")
        with self.assertRaises(CarnetError) as ctx:
            registers.set_status(self.root, "LRN-001", "ouvert")
        self.assertEqual(ctx.exception.error, "statut_non_gere")

    def test_erreurs(self):
        cases = [
            (("BLK-001", "actée"), "statut_invalide"),
            (("BLK-009", "résolu"), "id_introuvable"),
            (("XYZ-001", "résolu"), "id_inconnu"),
            (("pas-un-id", "résolu"), "id_inconnu"),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                with self.assertRaises(CarnetError) as ctx:
                    registers.set_status(self.root, *args)
                self.assertEqual(ctx.exception.error, expected)

    def test_solution_refusee_hors_blocages(self):
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        with self.assertRaises(CarnetError) as ctx:
            registers.set_status(self.root, "BDR-001", "actée", solution="x")
        self.assertEqual(ctx.exception.error, "option_invalide")

    def test_cli(self):
        code, out, _ = helpers.run_cli(
            "set-status", "BLK-001", "résolu", "--solution", "Chemin corrigé", root=self.root
        )
        self.assertEqual(code, 0)
        self.assertEqual(out["id"], "BLK-001")
        self.assertIn("- **Résolu le:** 2026-10-14\n", self.read("blockers"))
