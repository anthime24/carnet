import json
import unittest

import helpers


class ManifestTest(unittest.TestCase):
    def test_manifeste_valide(self):
        path = helpers.ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "carnet")
        self.assertTrue(data["description"])
        self.assertRegex(data["version"], r"^\d+\.\d+\.\d+$")
