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

    def test_auteur_et_depot_publics(self):
        data = json.loads((helpers.ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["author"]["name"], "anthime24")
        self.assertEqual(data["repository"], "https://github.com/anthime24/carnet")


class MarketplaceTest(unittest.TestCase):
    def load(self, name):
        path = helpers.ROOT / ".claude-plugin" / name
        return json.loads(path.read_text(encoding="utf-8"))

    def test_le_catalogue_decrit_le_plugin(self):
        market = self.load("marketplace.json")
        plugin = self.load("plugin.json")
        self.assertEqual(market["name"], "carnet")
        self.assertEqual(market["owner"]["name"], "anthime24")
        self.assertEqual(len(market["plugins"]), 1)
        entry = market["plugins"][0]
        self.assertEqual(entry["name"], plugin["name"])
        self.assertEqual(entry["source"], "./")
        self.assertEqual(entry["version"], plugin["version"])
        self.assertEqual(entry["description"], plugin["description"])
