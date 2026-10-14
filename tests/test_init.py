import helpers
from carnet_lib import registers

ALL = ["blockers.md", "decisions.md", "journal.md", "learnings.md"]


class InitTest(helpers.ProjectCase):
    def test_cree_les_quatre_registres_et_le_dossier_reports(self):
        result = registers.init(self.root)
        self.assertEqual(sorted(result["created"]), ALL)
        self.assertEqual(result["existing"], [])
        self.assertTrue((self.memory / "reports").is_dir())
        decisions = (self.memory / "decisions.md").read_text(encoding="utf-8")
        self.assertEqual(
            decisions,
            "---\nregistre: decisions\nprefixe: BDR\n---\n# Décisions\n\n"
            "## Index\n| ID | Date | Titre | Statut |\n|----|------|-------|--------|\n",
        )
        learnings = (self.memory / "learnings.md").read_text(encoding="utf-8")
        self.assertIn("| ID | Date | Titre |\n|----|------|-------|\n", learnings)
        journal = (self.memory / "journal.md").read_text(encoding="utf-8")
        self.assertEqual(journal, "---\nregistre: journal\n---\n# Journal\n")

    def test_n_ecrase_rien(self):
        registers.init(self.root)
        path = self.memory / "journal.md"
        path.write_text("contenu perso\n", encoding="utf-8")
        result = registers.init(self.root)
        self.assertEqual(result["created"], [])
        self.assertEqual(sorted(result["existing"]), ALL)
        self.assertEqual(path.read_text(encoding="utf-8"), "contenu perso\n")

    def test_cli_init_repond_en_json(self):
        code, out, _ = helpers.run_cli("init", root=self.root)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(out["created"]), ALL)
        self.assertEqual(out["memory_dir"], str(self.memory))
