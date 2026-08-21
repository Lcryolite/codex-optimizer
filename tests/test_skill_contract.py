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
HOOK = PLUGIN / "hooks" / "codex_optimizer_hook.py"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PONYTAIL = ROOT / "plugins" / "ponytail"


class PersistentDefaultsContractTests(unittest.TestCase):
    def test_marketplace_exposes_complete_upstream_ponytail_plugin(self) -> None:
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        entries = {entry["name"]: entry for entry in marketplace["plugins"]}
        ponytail_manifest = json.loads(
            (PONYTAIL / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            entries["ponytail"]["source"],
            {"source": "local", "path": "./plugins/ponytail"},
        )
        self.assertEqual(ponytail_manifest["name"], "ponytail")
        self.assertEqual(ponytail_manifest["skills"], "./skills/")
        self.assertEqual(ponytail_manifest["hooks"], "./hooks/claude-codex-hooks.json")
        self.assertTrue((PONYTAIL / "skills" / "ponytail" / "SKILL.md").is_file())
        self.assertTrue((PONYTAIL / "skills" / "ponytail-review" / "SKILL.md").is_file())
        self.assertTrue((PONYTAIL / "hooks" / "ponytail-activate.js").is_file())

    def test_codex_optimizer_does_not_shadow_upstream_ponytail_rules(self) -> None:
        own_skill = SKILL.read_text(encoding="utf-8")
        own_modes = (SKILL.parent / "references" / "mode-settings.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("Ponytail", own_skill)
        self.assertNotIn("Ponytail", own_modes)

    def test_every_caveman_level_reaches_session_context(self) -> None:
        for level in ("off", "lite", "full", "ultra", "micro"):
            with self.subTest(level=level), tempfile.TemporaryDirectory() as temporary:
                environment = os.environ.copy()
                environment["HOME"] = temporary
                environment["PLUGIN_ROOT"] = str(PLUGIN)
                subprocess.run(
                    [sys.executable, str(CONFIG), "set", "caveman", level],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=environment,
                )
                result = subprocess.run(
                    [sys.executable, str(HOOK), "session-start"],
                    input="{}",
                    check=True,
                    capture_output=True,
                    text=True,
                    env=environment,
                )

            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn(f"caveman={level}", context)

    def test_session_start_loads_saved_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ.copy()
            environment["HOME"] = temporary
            environment["PLUGIN_ROOT"] = str(PLUGIN)
            environment["PLUGIN_DATA"] = str(Path(temporary) / "data")
            subprocess.run(
                [sys.executable, str(CONFIG), "set", "caveman", "off"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            result = subprocess.run(
                [sys.executable, str(HOOK), "session-start"],
                input="{}",
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )

        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("caveman=off", context)

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

    def test_public_files_do_not_contain_machine_specific_home_paths(self) -> None:
        public_text_files = (
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and ".venv" not in path.parts
            and (
                path.suffix in {".json", ".md", ".py", ".sh", ".toml"}
                or path.name == "LICENSE"
            )
        )
        unix_home = re.compile(
            re.escape(str(Path("/", "home"))) + r"/[A-Za-z0-9._-]+"
            + "|"
            + re.escape(str(Path("/", "Users"))) + r"/[A-Za-z0-9._-]+"
            + "|"
            + re.escape(str(Path("/", "root"))) + r"(?:/|\b)"
        )
        windows_home = re.compile(
            r"[A-Za-z]:" + re.escape("\\Users\\") + r"[^\\\s]+",
            re.IGNORECASE,
        )

        violations = []
        for path in public_text_files:
            text = path.read_text(encoding="utf-8", errors="replace")
            if unix_home.search(text) or windows_home.search(text):
                violations.append(str(path.relative_to(ROOT)))

        self.assertEqual(violations, [], f"machine-specific paths found in: {violations}")


if __name__ == "__main__":
    unittest.main()
