import helpers
from carnet_lib import context, registers, reports
from carnet_lib.errors import CarnetError


class ContextTest(helpers.ProjectCase):
    def setUp(self):
        super().setUp()
        self.no_db = self.root / "absente.db"

    def populate(self):
        registers.init(self.root)
        add = registers.add
        add(self.root, "decisions", dict(helpers.DECISION, titre="Ancienne"), today="2026-09-20")
        add(self.root, "decisions", helpers.DECISION, today="2026-10-10")
        add(self.root, "blockers", dict(helpers.BLOCKER, titre="Vieux blocage"), today="2026-09-20")
        add(self.root, "blockers", helpers.BLOCKER, today="2026-10-10")
        registers.set_status(self.root, "BLK-002", "résolu", solution="Chemin corrigé", today="2026-10-12")
        add(self.root, "journal", {"lignes": ["Ancienne session"], "suite": "A"}, today="2026-09-20")
        add(self.root, "journal", {"lignes": ["Parseur écrit"], "suite": "Écrire les skills"}, today="2026-10-10")

    def build(self, **kwargs):
        kwargs.setdefault("today", "2026-10-14")
        kwargs.setdefault("db_path", self.no_db)
        return context.build(self.root, **kwargs)

    def ids(self, entries):
        return [entry["id"] for entry in entries]

    def test_matiere_d_une_periode(self):
        self.populate()
        ctx = self.build(since="2026-10-01", until="2026-10-14")
        regs = ctx["registers"]
        self.assertEqual(self.ids(regs["decisions"]), ["BDR-002"])
        self.assertEqual(self.ids(regs["blockers"]["opened"]), ["BLK-002"])
        self.assertEqual(self.ids(regs["blockers"]["open"]), ["BLK-001"])
        self.assertEqual(self.ids(regs["blockers"]["resolved"]), ["BLK-002"])
        self.assertEqual([e["date"] for e in regs["journal"]], ["2026-10-10"])
        self.assertEqual(regs["last_journal_date"], "2026-10-10")
        self.assertEqual(regs["last_dates"]["decisions"], "2026-10-10")
        self.assertEqual(ctx["project"], {"root": str(self.root), "name": self.root.name, "initialized": True})
        self.assertEqual(ctx["since"], "2026-10-01")
        self.assertEqual(ctx["until"], "2026-10-14")
        self.assertEqual(ctx["claude_mem"]["status"], "unavailable")
        self.assertEqual(ctx["graphify"], {"status": "absent"})
        self.assertIsNone(ctx["previous_report"])

    def test_sans_borne_tout_le_projet(self):
        self.populate()
        ctx = self.build()
        self.assertEqual(self.ids(ctx["registers"]["decisions"]), ["BDR-001", "BDR-002"])
        self.assertIsNone(ctx["since"])

    def test_un_blocage_resolu_apres_la_periode_n_est_pas_resolu_dans_la_periode(self):
        self.populate()
        ctx = self.build(since="2026-10-01", until="2026-10-11")
        self.assertEqual(ctx["registers"]["blockers"]["resolved"], [])

    def test_depuis_le_journal(self):
        self.populate()
        ctx = self.build(since="journal")
        self.assertEqual(ctx["since"], "2026-10-10")
        self.assertEqual(self.ids(ctx["registers"]["decisions"]), ["BDR-002"])

    def test_depuis_le_dernier_rapport(self):
        self.populate()
        reports.save_report(self.root, "perso", "Corps", "début", "2026-10-05", [], today="2026-10-05")
        ctx = self.build(since="rapport", gabarit="perso")
        self.assertEqual(ctx["since"], "2026-10-05")
        self.assertEqual(ctx["previous_report"]["date"], "2026-10-05")
        self.assertEqual(self.ids(ctx["registers"]["decisions"]), ["BDR-002"])

    def test_depuis_le_dernier_rapport_sans_rapport_existant(self):
        self.populate()
        ctx = self.build(since="rapport", gabarit="entreprise")
        self.assertIsNone(ctx["since"])
        self.assertIsNone(ctx["previous_report"])

    def test_rapport_exige_un_gabarit(self):
        self.populate()
        with self.assertRaises(CarnetError) as ctx:
            self.build(since="rapport")
        self.assertEqual(ctx.exception.error, "gabarit_requis")

    def test_date_invalide(self):
        self.populate()
        with self.assertRaises(CarnetError) as ctx:
            self.build(since="hier")
        self.assertEqual(ctx.exception.error, "date_invalide")

    def test_projet_sans_memoire(self):
        ctx = self.build()
        self.assertFalse(ctx["project"]["initialized"])
        regs = ctx["registers"]
        self.assertEqual(regs["decisions"], [])
        self.assertEqual(regs["blockers"], {"opened": [], "open": [], "resolved": []})
        self.assertEqual(regs["journal"], [])
        self.assertIsNone(regs["last_journal_date"])
        self.assertEqual(regs["last_dates"]["journal"], None)

    def test_registres_vides_mais_initialises(self):
        registers.init(self.root)
        ctx = self.build(since="journal")
        self.assertTrue(ctx["project"]["initialized"])
        self.assertEqual(ctx["registers"]["learnings"], [])
        self.assertIsNone(ctx["since"])

    def test_resumes_claude_mem_non_valides(self):
        self.populate()
        db = self.root / "fake.db"
        helpers.make_claude_mem_db(
            db,
            sessions=[("s1", "carnet", str(self.root))],
            summaries=[
                ("s1", "carnet", "2026-10-10T09:00:00.000Z", "Déjà fait", "ok", "suite", "[]"),
                ("s1", "carnet", "2026-10-12T09:00:00.000Z", "Pas de rituel", "ok", "suite", "[]"),
            ],
        )
        ctx = self.build(since="2026-10-01", db_path=db)
        self.assertEqual(ctx["claude_mem"]["status"], "ok")
        flags = {s["request"]: s["unvalidated"] for s in ctx["claude_mem"]["summaries"]}
        self.assertEqual(flags, {"Déjà fait": False, "Pas de rituel": True})

    def test_cli_context(self):
        self.populate()
        code, out, _ = helpers.run_cli("context", "--since", "2026-10-01", root=self.root)
        self.assertEqual(code, 0)
        self.assertEqual(out["registers"]["last_journal_date"], "2026-10-10")
        self.assertEqual(out["until"], "2026-10-14")
        self.assertEqual(out["claude_mem"]["status"], "unavailable")

    def test_cli_context_sur_un_projet_sans_memoire(self):
        code, out, _ = helpers.run_cli("context", "--gabarit", "perso", root=self.root)
        self.assertEqual(code, 0)
        self.assertFalse(out["project"]["initialized"])
