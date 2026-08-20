from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-optimizer"
SKILL = (
    ROOT
    / "plugins"
    / "codex-optimizer"
    / "skills"
    / "codex-optimizer"
    / "SKILL.md"
)
CONFIG = SKILL.parent / "scripts" / "codex_config.py"


class PersistentDefaultsContractTests(unittest.TestCase):
    def test_skill_loads_effective_defaults_once_per_conversation(self) -> None:
        instructions = SKILL.read_text(encoding="utf-8")

        self.assertIn("codex_config.py show", instructions)
        self.assertRegex(instructions, re.compile(r"once.*conversation", re.IGNORECASE))
        self.assertRegex(instructions, re.compile(r"effective.*defaults", re.IGNORECASE))

    def test_saved_override_is_visible_to_a_new_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ.copy()
            environment["HOME"] = temporary
            subprocess.run(
                [sys.executable, str(CONFIG), "set", "caveman", "off"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            result = subprocess.run(
                [sys.executable, str(CONFIG), "show"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )

        self.assertEqual(json.loads(result.stdout)["caveman"], "off")

    def test_public_identity_and_hook_version_are_consistent(self) -> None:
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        repository_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and ".venv" not in path.parts
            and (path.suffix in {".json", ".md", ".py", ".toml"} or path.name == "LICENSE")
        )

        self.assertEqual(manifest["name"], "codex-optimizer")
        self.assertTrue(manifest["version"].startswith("0.2.0"))
        forbidden_name = "pix" + "-optimizer"
        self.assertNotIn(forbidden_name, repository_text.lower())


if __name__ == "__main__":
    unittest.main()
