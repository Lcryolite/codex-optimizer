from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-optimizer"
HOOK = PLUGIN / "hooks" / "codex_optimizer_hook.py"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"
LIB = PLUGIN / "lib"
sys.path.insert(0, str(LIB))

from codex_optimizer.compact import CompactionConfig, compact_tool_output  # noqa: E402
from codex_optimizer.metrics import load_metrics, record  # noqa: E402


class HookManifestContractTests(unittest.TestCase):
    def test_plugin_registers_all_runtime_hooks(self) -> None:
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]

        self.assertIn("SessionStart", hooks)
        self.assertIn("PreToolUse", hooks)
        self.assertIn("PostToolUse", hooks)
        self.assertEqual(hooks["PreToolUse"][0]["matcher"], "Bash")
        self.assertEqual(hooks["PostToolUse"][0]["matcher"], "*")
        self.assertNotIn(
            "additionalContextLimit", hooks["PostToolUse"][0]["hooks"][0]
        )

    def test_launcher_survives_a_deleted_session_cache_root(self) -> None:
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        command = hooks["SessionStart"][0]["hooks"][0]["command"]
        with tempfile.TemporaryDirectory() as temporary:
            versions = Path(temporary) / "codex-optimizer"
            versions.mkdir()
            (versions / "current").symlink_to(PLUGIN, target_is_directory=True)
            environment = os.environ.copy()
            environment["PLUGIN_ROOT"] = str(versions / "deleted-version")
            environment["PLUGIN_DATA"] = str(Path(temporary) / "data")
            result = subprocess.run(
                command,
                shell=True,
                input="{}",
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response["systemMessage"], "[codex-optimizer] active")


class MetricsTests(unittest.TestCase):
    def test_corrupt_metric_values_cannot_break_recording(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary)
            (data / "metrics.json").write_text(
                '{"events":"broken","stages":{"Git Compaction":"bad"}}',
                encoding="utf-8",
            )
            previous = os.environ.get("PLUGIN_DATA")
            os.environ["PLUGIN_DATA"] = temporary
            try:
                record(100, 40, ("Git Compaction",))
                metrics = load_metrics()
            finally:
                if previous is None:
                    os.environ.pop("PLUGIN_DATA", None)
                else:
                    os.environ["PLUGIN_DATA"] = previous

        self.assertEqual(metrics["events"], 1)
        self.assertEqual(metrics["candidate_reduction_chars"], 60)
        self.assertEqual(metrics["estimated_candidate_reduction_tokens"], 15)
        self.assertEqual(metrics["stages"]["Git Compaction"], 1)

    def test_legacy_context_metrics_are_migrated_as_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary)
            (data / "metrics.json").write_text(
                json.dumps(
                    {
                        "events": 2,
                        "source_chars": 300,
                        "compact_context_chars": 100,
                        "context_delta_chars": 200,
                        "estimated_context_delta_tokens": 50,
                        "stages": {"Git Compaction": 2},
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("PLUGIN_DATA")
            os.environ["PLUGIN_DATA"] = temporary
            try:
                metrics = load_metrics()
            finally:
                if previous is None:
                    os.environ.pop("PLUGIN_DATA", None)
                else:
                    os.environ["PLUGIN_DATA"] = previous

        self.assertEqual(metrics["candidate_chars"], 100)
        self.assertEqual(metrics["candidate_reduction_chars"], 200)
        self.assertEqual(metrics["estimated_candidate_reduction_tokens"], 50)


class CompactionStageTests(unittest.TestCase):
    def assert_stage(
        self,
        stage: str,
        tool_name: str,
        tool_input: dict[str, object],
        output: str,
        *,
        config: CompactionConfig | None = None,
    ) -> str:
        result = compact_tool_output(
            tool_name,
            tool_input,
            output,
            config=config or CompactionConfig(),
        )
        self.assertTrue(result.changed, stage)
        self.assertIn(stage, result.stages)
        self.assertLess(len(result.text), len(output))
        return result.text

    def test_ansi_stripping(self) -> None:
        text = self.assert_stage(
            "ANSI Stripping", "Bash", {"command": "printf ok"}, "\x1b[31merror\x1b[0m"
        )
        self.assertEqual(text, "error")

    def test_test_aggregation(self) -> None:
        raw = "\n".join([f"test_case_{index} PASSED" for index in range(30)])
        raw += "\n================ 30 passed, 2 skipped in 1.20s ================\n"
        text = self.assert_stage("Test Aggregation", "Bash", {"command": "pytest -q"}, raw)
        self.assertIn("30 passed", text)
        self.assertNotIn("Failures:", text)

    def test_build_filtering(self) -> None:
        raw = "\n".join([f"   Compiling crate_{index} v0.1.0" for index in range(30)])
        text = self.assert_stage("Build Filtering", "Bash", {"command": "cargo build"}, raw)
        self.assertIn("Build successful", text)

    def test_git_compaction(self) -> None:
        raw = "## main...origin/main\n" + "\n".join(
            [f" M src/module_{index}.py" for index in range(30)]
        )
        text = self.assert_stage("Git Compaction", "Bash", {"command": "git status --short --branch"}, raw)
        self.assertIn("Modified: 30 files", text)

    def test_linter_aggregation(self) -> None:
        raw = "\n".join(
            [f"src/file_{index}.js:{index}:3: error no-unused-vars unused value" for index in range(30)]
        )
        text = self.assert_stage("Linter Aggregation", "Bash", {"command": "eslint src"}, raw)
        self.assertIn("30 error", text)

    def test_search_grouping(self) -> None:
        raw = "\n".join(
            [f"src/file_{index // 10}.py:{index + 1}:needle in a long matching source line" for index in range(30)]
        )
        text = self.assert_stage("Search Grouping", "Bash", {"command": "rg -n needle src"}, raw)
        self.assertIn("src/file_0.py", text)

    def test_source_filtering_and_smart_truncation(self) -> None:
        raw = "\n".join(
            line
            for index in range(40)
            for line in (f"# comment {index}", f"value_{index} = {index}")
        )
        config = CompactionConfig(exact_read_lines=5, smart_max_lines=12, max_chars=20_000)
        result = compact_tool_output("Read", {"path": "src/example.py"}, raw, config=config)

        self.assertIn("Source Code Filtering", result.stages)
        self.assertIn("Smart Truncation", result.stages)
        self.assertLessEqual(len(result.text.splitlines()), 15)

    def test_source_filtering_preserves_userscript_metadata(self) -> None:
        metadata = "\n".join(
            (
                "// ==UserScript==",
                "// @name Codex Optimizer Fixture",
                "// @match https://example.com/*",
                "// ==/UserScript==",
            )
        )
        raw = metadata + "\n" + "\n".join(
            line
            for index in range(30)
            for line in (f"// removable {index}", f"const value{index} = {index};")
        )
        result = compact_tool_output(
            "Read",
            {"path": "fixture.user.js"},
            raw,
            config=CompactionConfig(exact_read_lines=5, smart_max_lines=40, max_chars=20_000),
        )

        self.assertIn("Source Code Filtering", result.stages)
        self.assertIn("// @name Codex Optimizer Fixture", result.text)
        self.assertNotIn("// removable", result.text)

    def test_anchor_safe_read_compaction(self) -> None:
        raw = "\n".join(f"{index} # a1b2:value_{index} = {index}" for index in range(1, 41))
        text = self.assert_stage(
            "Anchor-Safe Read Compaction",
            "Read",
            {"path": "src/example.py"},
            raw,
            config=CompactionConfig(exact_read_lines=5, smart_max_lines=10, max_chars=20_000),
        )
        self.assertIn("anchor-safe", text)
        for line in text.splitlines():
            if "# a1b2:" in line:
                self.assertRegex(line, r"^\d+ # a1b2:")

    def test_hard_truncation(self) -> None:
        raw = "0123456789\n" * 200
        text = self.assert_stage(
            "Hard Truncation",
            "Bash",
            {"command": "unknown-command"},
            raw,
            config=CompactionConfig(max_chars=180, smart_max_lines=10_000),
        )
        self.assertLessEqual(len(text), 180)
        self.assertIn("truncated", text)

    def test_small_and_explicit_reads_remain_exact(self) -> None:
        small = "\n".join(f"line {index}" for index in range(80))
        self.assertFalse(compact_tool_output("Read", {"path": "a.py"}, small).changed)

        large = "\n".join(f"line {index}" for index in range(300))
        explicit = compact_tool_output(
            "Read", {"path": "a.py", "offset": 1, "limit": 300}, large
        )
        self.assertFalse(explicit.changed)


class RuntimeHookTests(unittest.TestCase):
    def run_hook(
        self,
        action: str,
        payload: dict[str, object],
        *,
        fake_rtk: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        environment = os.environ.copy()
        environment["HOME"] = str(root / "home")
        environment["PLUGIN_ROOT"] = str(PLUGIN)
        environment["PLUGIN_DATA"] = str(root / "data")
        if fake_rtk:
            binary = root / "rtk"
            binary.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = rewrite ]; then printf 'rtk git status --short\\n'; exit 3; fi\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            environment["PATH"] = f"{root}:{environment.get('PATH', '')}"

        return subprocess.run(
            [sys.executable, str(HOOK), action],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    def test_pre_tool_use_rewrites_without_repeating_the_command(self) -> None:
        result = self.run_hook(
            "pre-tool-use",
            {"tool_name": "Bash", "tool_input": {"command": "git status"}},
            fake_rtk=True,
        )
        response = json.loads(result.stdout)

        self.assertEqual(
            response,
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": {"command": "rtk git status --short"},
                }
            },
        )

    def test_pre_tool_use_never_delegates_sudo(self) -> None:
        result = self.run_hook(
            "pre-tool-use",
            {"tool_name": "Bash", "tool_input": {"command": "FOO=1 sudo id"}},
            fake_rtk=True,
        )
        self.assertEqual(result.stdout, "")

    def test_pre_tool_use_does_not_auto_allow_git_push(self) -> None:
        result = self.run_hook(
            "pre-tool-use",
            {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
            fake_rtk=True,
        )
        self.assertEqual(result.stdout, "")

    def test_post_tool_use_reports_stages_without_adding_model_context(self) -> None:
        raw = "\x1b[32m" + "\n".join(f"case_{index} PASSED" for index in range(30))
        raw += "\n30 passed in 1.0s\x1b[0m"
        result = self.run_hook(
            "post-tool-use",
            {
                "tool_name": "Bash",
                "tool_input": {"command": "pytest -q"},
                "tool_response": {"output": raw},
            },
        )
        response = json.loads(result.stdout)

        self.assertNotIn("continue", response)
        self.assertNotEqual(response.get("decision"), "block")
        self.assertIn("ANSI Stripping", response["systemMessage"])
        self.assertIn("Test Aggregation", response["systemMessage"])
        self.assertNotIn("hookSpecificOutput", response)
        self.assertNotIn("additionalContext", json.dumps(response))

    def test_session_start_injects_only_compact_mode_state(self) -> None:
        result = self.run_hook("session-start", {"session_id": "test"})
        response = json.loads(result.stdout)
        context = response["hookSpecificOutput"]["additionalContext"]

        self.assertEqual(
            context,
            "codex-optimizer: caveman=full; ponytail=full; rtk=on.",
        )
        self.assertEqual(response["systemMessage"], "[codex-optimizer] active")


if __name__ == "__main__":
    unittest.main()
