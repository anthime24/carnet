import helpers
from carnet_lib import registers


class ReadTest(helpers.ProjectCase):
    def setUp(self):
        super().setUp()
        registers.init(self.root)

    def test_lire_les_decisions(self):
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        self.assertEqual(
            registers.read_entries(self.root, "decisions"),
            [
                {
                    "id": "BDR-001",
                    "titre": "Registres par projet",
                    "date": "2026-10-14",
                    "decision": "Un dossier .claude/memory par projet",
                    "pourquoi": "Chaque projet reste autonome",
                    "alternatives": "Un vault central",
                    "statut": "actée",
                }
            ],
        )

    def test_lire_un_blocage_resolu(self):
        registers.add(self.root, "blockers", helpers.BLOCKER, today="2026-10-14")
        registers.set_status(self.root, "BLK-001", "résolu", solution="Corrigé", today="2026-10-16")
        entry = registers.read_entries(self.root, "blockers")[0]
        self.assertEqual(entry["statut"], "résolu")
        self.assertEqual(entry["solution"], "Corrigé")
        self.assertEqual(entry["resolu_le"], "2026-10-16")

    def test_lire_le_journal(self):
        registers.add(self.root, "journal", {"lignes": ["A", "B"], "suite": "C"}, today="2026-10-14")
        self.assertEqual(
            registers.read_journal(self.root),
            [{"date": "2026-10-14", "lignes": ["A", "B"], "suite": "C"}],
        )

    def test_deux_rituels_le_meme_jour(self):
        registers.add(self.root, "journal", {"lignes": ["Matin"], "suite": "Premier"}, today="2026-10-14")
        registers.add(self.root, "journal", {"lignes": ["Soir"], "suite": "Dernier"}, today="2026-10-14")
        entries = registers.read_journal(self.root)
        self.assertEqual([e["suite"] for e in entries], ["Premier", "Dernier"])
        self.assertEqual(registers.last_dates(self.root)["journal"], "2026-10-14")

    def test_entree_de_journal_ecrite_a_la_main_sans_suite(self):
        path = self.memory / "journal.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n## 2026-09-01\nPremière note\n", encoding="utf-8")
        self.assertEqual(
            registers.read_journal(self.root),
            [{"date": "2026-09-01", "lignes": ["Première note"], "suite": ""}],
        )

    def test_fichier_absent(self):
        other = self.root / "autre"
        other.mkdir()
        self.assertEqual(registers.read_entries(other, "decisions"), [])
        self.assertEqual(registers.read_journal(other), [])
        self.assertEqual(
            registers.last_dates(other),
            {"decisions": None, "learnings": None, "blockers": None, "journal": None},
        )

    def test_dernieres_dates(self):
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-09-20")
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-10")
        registers.add(self.root, "blockers", helpers.BLOCKER, today="2026-10-01")
        self.assertEqual(
            registers.last_dates(self.root),
            {"decisions": "2026-10-10", "learnings": None, "blockers": "2026-10-01", "journal": None},
        )

    def test_fichier_avec_fins_de_ligne_windows(self):
        registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-14")
        path = self.memory / "decisions.md"
        crlf = path.read_text(encoding="utf-8").replace("\n", "\r\n")
        path.write_bytes(crlf.encode("utf-8"))
        entries = registers.read_entries(self.root, "decisions")
        self.assertEqual(entries[0]["titre"], "Registres par projet")
        self.assertEqual(entries[0]["statut"], "actée")
        result = registers.add(self.root, "decisions", helpers.DECISION, today="2026-10-15")
        self.assertEqual(result["id"], "BDR-002")
        self.assertEqual(len(registers.read_entries(self.root, "decisions")), 2)
