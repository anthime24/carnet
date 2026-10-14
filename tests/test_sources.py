import sqlite3

import helpers
from carnet_lib import sources


class ClaudeMemTest(helpers.ProjectCase):
    def setUp(self):
        super().setUp()
        self.db = self.root / "fake.db"
        self.name = self.root.name

    def read(self, since=None, until=None, last=None, path=None):
        return sources.read_claude_mem(self.root, since, until, last, path=path or self.db)

    def summary(self, sid, project, created_at="2026-10-10T09:00:00.000Z", request="req", files="[]"):
        return (sid, project, created_at, request, "fait", "suite", files)

    def test_correspondance_par_cwd(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "carnet", str(self.root)), ("s2", "autre", "/ailleurs")],
            summaries=[
                self.summary("s1", "carnet", request="Écrire le parseur", files='["bin/carnet.py"]'),
                self.summary("s2", "autre", request="Sans rapport"),
            ],
        )
        result = self.read()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["match"], "cwd")
        self.assertEqual([s["request"] for s in result["summaries"]], ["Écrire le parseur"])
        self.assertEqual(result["summaries"][0]["files_edited"], ["bin/carnet.py"])
        self.assertEqual(result["summaries"][0]["date"], "2026-10-10")

    def test_sous_dossier_du_projet(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "carnet", str(self.root / "src"))],
            summaries=[self.summary("s1", "carnet")],
        )
        self.assertEqual(len(self.read()["summaries"]), 1)

    def test_session_enregistree_sur_un_autre_systeme(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", self.name, "C:/Users/x/proj"), ("s2", self.name, None)],
            summaries=[self.summary("s1", self.name), self.summary("s2", self.name)],
        )
        result = self.read()
        self.assertEqual(result["match"], "name")
        self.assertEqual(len(result["summaries"]), 2)

    def test_melange_cwd_et_nom(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", self.name, "C:/Users/x/proj"), ("s2", self.name, str(self.root))],
            summaries=[
                self.summary("s1", self.name, created_at="2026-10-01T09:00:00.000Z"),
                self.summary("s2", self.name, created_at="2026-10-02T09:00:00.000Z"),
            ],
        )
        result = self.read()
        self.assertEqual(result["match"], "cwd+name")
        self.assertEqual([s["date"] for s in result["summaries"]], ["2026-10-01", "2026-10-02"])

    def test_repli_sur_le_nom_du_projet(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", self.name, "/autre/endroit/" + self.name)],
            summaries=[self.summary("s1", self.name)],
        )
        result = self.read()
        self.assertEqual(result["match"], "name")
        self.assertEqual(len(result["summaries"]), 1)

    def test_aucun_resume_correspondant(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "autre", "/ailleurs")],
            summaries=[self.summary("s1", "autre")],
        )
        result = self.read()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summaries"], [])

    def test_bornes_de_dates_inclusives(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "carnet", str(self.root))],
            summaries=[
                self.summary("s1", "carnet", created_at="2026-10-01T09:00:00.000Z"),
                self.summary("s1", "carnet", created_at="2026-10-05T09:00:00.000Z"),
                self.summary("s1", "carnet", created_at="2026-10-10T23:59:00.000Z"),
                self.summary("s1", "carnet", created_at="2026-10-11T00:01:00.000Z"),
            ],
        )
        dates = [s["date"] for s in self.read(since="2026-10-05", until="2026-10-10")["summaries"]]
        self.assertEqual(dates, ["2026-10-05", "2026-10-10"])

    def test_non_valide_apres_la_derniere_entree_du_journal(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "carnet", str(self.root))],
            summaries=[
                self.summary("s1", "carnet", created_at="2026-10-05T09:00:00.000Z"),
                self.summary("s1", "carnet", created_at="2026-10-06T09:00:00.000Z"),
            ],
        )
        flags = [s["unvalidated"] for s in self.read(last="2026-10-05")["summaries"]]
        self.assertEqual(flags, [False, True])
        flags = [s["unvalidated"] for s in self.read(last=None)["summaries"]]
        self.assertEqual(flags, [True, True])

    def test_champs_tronques(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "carnet", str(self.root))],
            summaries=[self.summary("s1", "carnet", request="x" * 600)],
        )
        request = self.read()["summaries"][0]["request"]
        self.assertEqual(len(request), 500)
        self.assertTrue(request.endswith("…"))

    def test_liste_de_fichiers_invalide(self):
        helpers.make_claude_mem_db(
            self.db,
            sessions=[("s1", "carnet", str(self.root))],
            summaries=[self.summary("s1", "carnet", files="pas du json")],
        )
        self.assertEqual(self.read()["summaries"][0]["files_edited"], [])

    def test_base_absente(self):
        result = self.read(path=self.root / "absente.db")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("introuvable", result["reason"])
        self.assertEqual(result["summaries"], [])

    def test_colonne_manquante(self):
        conn = sqlite3.connect(str(self.db))
        conn.executescript(
            "CREATE TABLE sdk_sessions (memory_session_id TEXT, project TEXT, cwd TEXT);"
            "CREATE TABLE session_summaries (memory_session_id TEXT, project TEXT, "
            "created_at TEXT, created_at_epoch INTEGER);"
        )
        conn.close()
        result = self.read()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("schéma", result["reason"])

    def test_fichier_corrompu(self):
        self.db.write_bytes(b"ceci n'est pas une base sqlite" * 10)
        self.assertEqual(self.read()["status"], "unavailable")

    def test_chemin_avec_espaces_et_diese(self):
        folder = self.root / "dossier avec espaces #1"
        folder.mkdir()
        db = folder / "claude mem.db"
        helpers.make_claude_mem_db(
            db, sessions=[("s1", "carnet", str(self.root))], summaries=[self.summary("s1", "carnet")]
        )
        result = self.read(path=db)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["summaries"]), 1)

    def test_la_base_n_est_pas_modifiee(self):
        helpers.make_claude_mem_db(
            self.db, sessions=[("s1", "carnet", str(self.root))], summaries=[self.summary("s1", "carnet")]
        )
        before = self.db.read_bytes()
        self.read()
        self.assertEqual(self.db.read_bytes(), before)


class GraphifyTest(helpers.ProjectCase):
    def test_absent(self):
        self.assertEqual(sources.read_graphify(self.root), {"status": "absent"})

    def test_present(self):
        folder = self.root / "graphify-out"
        folder.mkdir()
        (folder / "GRAPH_REPORT.md").write_text("# Rapport\nModules: a, b\n", encoding="utf-8")
        result = sources.read_graphify(self.root)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["excerpt"], "# Rapport\nModules: a, b")

    def test_extrait_coupe_a_une_fin_de_ligne(self):
        folder = self.root / "graphify-out"
        folder.mkdir()
        (folder / "GRAPH_REPORT.md").write_text("ligne\n" * 1000, encoding="utf-8")
        excerpt = sources.read_graphify(self.root)["excerpt"]
        self.assertLessEqual(len(excerpt), 3000)
        self.assertTrue(excerpt.endswith("ligne"))
