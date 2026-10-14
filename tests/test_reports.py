from pathlib import Path

import helpers
from carnet_lib import reports
from carnet_lib.errors import CarnetError


class ReportsTest(helpers.ProjectCase):
    def make(self, *names):
        folder = self.memory / "reports"
        folder.mkdir(parents=True, exist_ok=True)
        for name in names:
            (folder / name).write_text("x", encoding="utf-8")

    def test_aucun_rapport(self):
        self.assertIsNone(reports.last_report(self.root, "perso"))
        self.make()
        self.assertIsNone(reports.last_report(self.root, "perso"))

    def test_dernier_rapport_par_gabarit(self):
        self.make("2026-10-01-perso.md", "2026-10-05-perso.md", "2026-10-09-entreprise.md", "notes.md")
        perso = reports.last_report(self.root, "perso")
        self.assertEqual(perso["date"], "2026-10-05")
        self.assertTrue(perso["path"].endswith("2026-10-05-perso.md"))
        self.assertEqual(reports.last_report(self.root, "entreprise")["date"], "2026-10-09")

    def test_le_suffixe_le_plus_grand_gagne(self):
        self.make("2026-10-14-perso.md", "2026-10-14-perso-2.md")
        self.assertTrue(reports.last_report(self.root, "perso")["path"].endswith("2026-10-14-perso-2.md"))

    def test_gabarit_inconnu(self):
        with self.assertRaises(CarnetError) as ctx:
            reports.last_report(self.root, "prof")
        self.assertEqual(ctx.exception.error, "gabarit_inconnu")

    def test_enregistrer_un_rapport(self):
        result = reports.save_report(
            self.root, "perso", "Corps du rapport\n", "2026-10-01", "2026-10-14", [], today="2026-10-14"
        )
        path = Path(result["path"])
        self.assertEqual(path.name, "2026-10-14-perso.md")
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "---\ngabarit: perso\ndu: 2026-10-01\nau: 2026-10-14\n---\nCorps du rapport\n",
        )
        self.assertEqual(result["warnings"], [])

    def test_collision_de_noms(self):
        names = []
        for _ in range(3):
            result = reports.save_report(self.root, "perso", "x", "début", "2026-10-14", [], today="2026-10-14")
            names.append(Path(result["path"]).name)
        self.assertEqual(names, ["2026-10-14-perso.md", "2026-10-14-perso-2.md", "2026-10-14-perso-3.md"])

    def test_les_avertissements_de_style_n_empechent_pas_l_ecriture(self):
        result = reports.save_report(
            self.root, "perso", "texte — tiret", "2026-10-01", "2026-10-14", [], today="2026-10-14"
        )
        self.assertTrue(Path(result["path"]).exists())
        self.assertEqual(result["warnings"][0]["motif"], "tiret cadratin")

    def test_dates_invalides(self):
        with self.assertRaises(CarnetError) as ctx:
            reports.save_report(self.root, "perso", "x", "hier", "2026-10-14", [])
        self.assertEqual(ctx.exception.error, "date_invalide")
        with self.assertRaises(CarnetError):
            reports.save_report(self.root, "perso", "x", "2026-10-01", "début", [])

    def test_cli_enregistrer_puis_retrouver(self):
        draft = self.root / "brouillon.md"
        draft.write_text("Point d'étape\n", encoding="utf-8")
        code, out, _ = helpers.run_cli(
            "save-report", "entreprise", "--from", str(draft), "--du", "début", "--au", "2026-10-14",
            root=self.root,
        )
        self.assertEqual(code, 0)
        self.assertTrue(out["path"].endswith("2026-10-14-entreprise.md"))
        code, out, _ = helpers.run_cli("last-report", "entreprise", root=self.root)
        self.assertEqual(code, 0)
        self.assertEqual(out["date"], "2026-10-14")
        code, out, _ = helpers.run_cli("last-report", "perso", root=self.root)
        self.assertEqual(code, 0)
        self.assertIsNone(out)
