from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "plugins"
    / "codex-optimizer"
    / "skills"
    / "codex-optimizer"
    / "scripts"
    / "rtk_rewrite.py"
)


class RtkRewriteSafetyTests(unittest.TestCase):
    def run_helper(self, command: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        marker = directory / "rtk-called"
        fake_rtk = directory / "rtk"
        fake_rtk.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$RTK_MARKER\"\nprintf 'rewritten\\n'\nexit 3\n",
            encoding="utf-8",
        )
        fake_rtk.chmod(0o755)
        environment = os.environ.copy()
        environment["PATH"] = str(directory)
        environment["RTK_MARKER"] = str(marker)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), command],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        return result, marker

    def test_refuses_sudo_before_delegating_to_rtk(self) -> None:
        unsafe_commands = (
            "git status & sudo id",
            "git status\nsudo id",
            "FOO=1 sudo id",
            "env FOO=1 sudo id",
            "command sudo id",
            "/usr/bin/sudo id",
            "s'u'do id",
            "echo $(sudo id)",
            'echo "$(sudo id)"',
            "su\\\ndo id",
        )

        for command in unsafe_commands:
            with self.subTest(command=command):
                result, marker = self.run_helper(command)
                self.assertEqual(result.returncode, 3)
                self.assertIn("refusing sudo command", result.stderr)
                self.assertFalse(marker.exists(), "unsafe command reached RTK")

    def test_safe_command_is_delegated(self) -> None:
        result, marker = self.run_helper("git status")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "rewritten\n")
        self.assertTrue(marker.exists())

    def test_approval_sensitive_mutation_is_not_delegated(self) -> None:
        for command in (
            "git push origin main",
            "npm publish",
            "cargo publish",
            "rm -rf build",
            "echo ok && docker push example/image",
        ):
            with self.subTest(command=command):
                result, marker = self.run_helper(command)
                self.assertEqual(result.returncode, 3)
                self.assertIn("approval-sensitive mutation", result.stderr)
                self.assertFalse(marker.exists())

    def test_rewrite_exit_code_three_is_success(self) -> None:
        result, _ = self.run_helper("cargo test")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "rewritten\n")

    def test_similar_command_names_are_not_blocked(self) -> None:
        for command in ("nosudo --help", "sudoers-check"):
            with self.subTest(command=command):
                result, marker = self.run_helper(command)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(marker.exists())

    def test_explicit_raw_output_marker_bypasses_rtk(self) -> None:
        for command in (
            "CODEX_OPTIMIZER_RAW=1 git status --porcelain=v2",
            "env CODEX_OPTIMIZER_RAW=true rg --json needle .",
        ):
            with self.subTest(command=command):
                result, marker = self.run_helper(command)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, f"{command}\n")
                self.assertFalse(marker.exists())

    def test_disabled_raw_output_marker_does_not_bypass_rtk(self) -> None:
        result, marker = self.run_helper("CODEX_OPTIMIZER_RAW=0 git status")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "rewritten\n")
        self.assertTrue(marker.exists())


if __name__ == "__main__":
    unittest.main()
