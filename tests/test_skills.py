import re
import unittest

import helpers
import carnet


class SkillsTest(unittest.TestCase):
    def skill(self, name):
        return (helpers.ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def commands(self, text):
        return set(re.findall(r'carnet\.py"\s+([a-z][a-z-]*)', text))

    def check_skill(self, name, expected_commands):
        text = self.skill(name)
        self.assertTrue(text.startswith(f"---\nname: {name}\ndescription: "))
        used = self.commands(text)
        self.assertTrue(expected_commands <= used, f"commandes manquantes: {expected_commands - used}")
        self.assertTrue(used <= set(carnet.HANDLERS), f"commandes inconnues: {used - set(carnet.HANDLERS)}")
        script = helpers.ROOT / "skills" / name / ".." / ".." / "bin" / "carnet.py"
        self.assertTrue(script.resolve().is_file())

    def test_wrapup(self):
        self.check_skill("wrapup", {"init", "context", "add", "set-status"})
        text = self.skill("wrapup")
        for phrase in ["Attends l'accord", "Suite:", "--since journal", "last_dates"]:
            self.assertIn(phrase, text)

    def test_report(self):
        self.check_skill("report", {"context", "style-check", "save-report"})
        text = self.skill("report")
        for phrase in ["--since rapport", "--depuis", "--tout", "templates/perso.md", "templates/entreprise.md", "non validé"]:
            self.assertIn(phrase, text)
        for name in ("perso.md", "entreprise.md"):
            self.assertTrue((helpers.ROOT / "templates" / name).is_file())
