import os
import unittest

import helpers
from carnet_lib import registers


class CliErrorsTest(helpers.ProjectCase):
    def test_registre_qui_n_est_pas_en_utf8(self):
        registers.init(self.root)
        with open(self.memory / "learnings.md", "ab") as handle:
            handle.write(b"\xff\xfe")
        code, out, err = helpers.run_cli("context", root=self.root)
        self.assertEqual(code, 1)
        self.assertEqual(out["error"], "encodage_invalide")
        self.assertNotIn("Traceback", err)

    @unittest.skipIf(os.name == "nt" or os.geteuid() == 0, "les permissions ne bloquent pas ce compte")
    def test_dossier_non_inscriptible(self):
        locked = self.root / "verrouille"
        locked.mkdir()
        locked.chmod(0o500)
        self.addCleanup(locked.chmod, 0o700)
        code, out, err = helpers.run_cli("init", root=locked)
        self.assertEqual(code, 1)
        self.assertEqual(out["error"], "erreur_fichier")
        self.assertNotIn("Traceback", err)
