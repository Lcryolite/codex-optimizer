"""Deterministic output compaction pipeline used by PostToolUse hooks."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re


ALL_STAGES = (
    "ANSI Stripping",
    "Test Aggregation",
    "Build Filtering",
    "Git Compaction",
    "Linter Aggregation",
    "Search Grouping",
    "Source Code Filtering",
    "Smart Truncation",
    "Anchor-Safe Read Compaction",
    "Hard Truncation",
)

ANSI_RE = re.compile(r"(?:\x1B\][^\x07]*(?:\x07|\x1B\\)|\x1B\[[0-?]*[ -/]*[@-~])")
ANCHOR_PATTERNS = (
    re.compile(r"^\s*(?:>>>|>>|[>+\-*]+)?\s*(\d+)\s*#\s*[A-Za-z0-9_-]{2,32}:(.*)$"),
    re.compile(r"^\s*(?:>>>|>>|[>+\-*]+)?\s*(\d+)\s*:\s*[A-Za-z0-9_-]{1,32}\|(.*)$"),
    re.compile(r"^\s*(?:>>>|>>|[>+\-*]+)?\s*(\d+)[a-z]{2}\|(.*)$"),
)
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".java",
    ".js", ".jsx", ".kt", ".kts", ".php", ".py", ".rb", ".rs", ".scss",
    ".sh", ".swift", ".ts", ".tsx", ".vue",
}


@dataclass(frozen=True)
class CompactionConfig:
    max_chars: int = 12_000
    smart_max_lines: int = 220
    exact_read_lines: int = 80
    source_filtering: bool = True
    smart_truncation: bool = True
    preserve_skill_reads: bool = True


@dataclass(frozen=True)
class CompactionResult:
    text: str
    stages: tuple[str, ...]
    original_chars: int

    @property
    def changed(self) -> bool:
        return self.text != "" and bool(self.stages)

    @property
    def compacted_chars(self) -> int:
        return len(self.text)

    @property
    def saved_chars(self) -> int:
        return max(0, self.original_chars - self.compacted_chars)


def _apply(current: str, candidate: str | None, stage: str, stages: list[str]) -> str:
    if candidate is not None and candidate != current and len(candidate) < len(current):
        stages.append(stage)
        return candidate
    return current


def _normalized_command(command: str) -> str:
    value = command.strip()
    value = re.sub(r"^(?:rtk\s+)+", "", value)
    return value


def _test_summary(output: str, command: str) -> str | None:
    if not re.match(r"^(?:npm|pnpm|yarn|bun)\s+test\b|^cargo\s+test\b|^go\s+test\b|^pytest\b|^python\s+-m\s+pytest\b|^(?:npx\s+)?(?:vitest|jest)\b", command):
        return None
    patterns = (
        re.compile(r"(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+skipped)?", re.I),
        re.compile(r"Tests?:\s*(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+skipped)?", re.I),
        re.compile(r"test result:\s*\w+\.\s*(\d+)\s+passed;\s*(\d+)\s+failed", re.I),
    )
    matches = [match for pattern in patterns for match in pattern.finditer(output)]
    match = matches[-1] if matches else None
    if match:
        passed = int(match.group(1) or 0)
        failed = int(match.group(2) or 0) if match.lastindex and match.lastindex >= 2 else 0
        skipped = int(match.group(3) or 0) if match.lastindex and match.lastindex >= 3 else 0
    else:
        passed = sum(bool(re.search(r"\b(?:PASSED|PASS|ok)\b|[✓✔]", line)) for line in output.splitlines())
        failed = sum(bool(re.search(r"\b(?:FAILED|FAIL)\b|[✗✕]", line)) for line in output.splitlines())
        skipped = 0
    failure_start = re.compile(r"^(?:FAIL(?:ED)?\s+|\s*[●✗✕]\s+|thread\s+'.+'\s+panicked)", re.I)
    failures = [line.strip() for line in output.splitlines() if failure_start.search(line)]
    lines = ["Test Results:", f"  PASS: {passed} passed"]
    if failed:
        lines.append(f"  FAIL: {failed} failed")
    if skipped:
        lines.append(f"  SKIP: {skipped} skipped")
    if failures:
        lines.append("  Failures:")
        lines.extend(f"  - {line[:120]}" for line in failures[:5])
    return "\n".join(lines)


def _build_summary(output: str, command: str) -> str | None:
    if not re.match(r"^cargo\s+(?:build|check)\b|^(?:npm|pnpm|yarn)\s+(?:run\s+)?build\b|^(?:npx\s+)?tsc\b|^make\b|^cmake\b|^gradle\b|^mvn\b|^go\s+(?:build|install)\b|^pip\s+install\b", command):
        return None
    lines = output.splitlines()
    compiled = sum(bool(re.match(r"^\s*(?:Compiling|Checking|Building)\s+", line)) for line in lines)
    errors = [line for line in lines if re.match(r"^(?:error(?:\[|:)|\[ERROR\]|FAIL)", line)]
    warnings = [line for line in lines if re.match(r"^(?:warning:|warn:|\[WARNING\])", line)]
    if not errors and not warnings:
        return f"[OK] Build successful ({compiled} units compiled)"
    result: list[str] = []
    if errors:
        result.append(f"[ERROR] {len(errors)} error(s):")
        result.extend(errors[:10])
    if warnings:
        result.append(f"[WARN] {len(warnings)} warning(s)")
        result.extend(warnings[:5])
    return "\n".join(result)


def _git_summary(output: str, command: str) -> str | None:
    if not command.startswith("git "):
        return None
    if command.startswith("git status"):
        if not re.search(r"^(?:## |[ MADRCU?]{2}\s)", output, re.M):
            return None
        branch = ""
        staged: list[str] = []
        modified: list[str] = []
        untracked: list[str] = []
        conflicts: list[str] = []
        for line in output.splitlines():
            if line.startswith("## "):
                branch = line[3:].split("...")[0]
            elif len(line) >= 4:
                status, filename = line[:2], line[3:]
                if status[0] in "MADRC":
                    staged.append(filename)
                if status[1] in "MD":
                    modified.append(filename)
                if status == "??":
                    untracked.append(filename)
                if "U" in status:
                    conflicts.append(filename)
        result = [f"Branch: {branch or '(unknown)'}"]
        for label, files, limit in (("Staged", staged, 5), ("Modified", modified, 5), ("Untracked", untracked, 3), ("Conflicts", conflicts, 5)):
            if files:
                result.append(f"{label}: {len(files)} files")
                result.extend(f"  {name}" for name in files[:limit])
                if len(files) > limit:
                    result.append(f"  ... +{len(files) - limit} more")
        return "\n".join(result)
    if command.startswith("git log"):
        lines = output.splitlines()
        return "\n".join([line[:77] + "..." if len(line) > 80 else line for line in lines[:20]] + ([f"... and {len(lines) - 20} more commits"] if len(lines) > 20 else []))
    if command.startswith("git diff") and "diff --git " in output:
        result: list[str] = []
        current = ""
        added = removed = 0
        for line in output.splitlines():
            if line.startswith("diff --git "):
                if current:
                    result.append(f"  +{added} -{removed}")
                match = re.match(r"diff --git a/(.+) b/(.+)", line)
                current = match.group(2) if match else "unknown"
                result.append(f"> {current}")
                added = removed = 0
            elif line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        if current:
            result.append(f"  +{added} -{removed}")
        return "\n".join(result)
    return None


def _linter_summary(output: str, command: str) -> str | None:
    if not re.search(r"(?:^|\s)(?:eslint|biome|ruff|flake8|pylint|clippy|shellcheck|golangci-lint)(?:\s|$)", command):
        return None
    matches: list[tuple[str, str, str, str]] = []
    pattern = re.compile(r"^(.+?):(\d+)(?::\d+)?:\s*(?:(error|warning)\s+)?(.+)$", re.I)
    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            matches.append((match.group(1), match.group(2), (match.group(3) or "error").lower(), match.group(4)))
    if not matches:
        return None
    errors = sum(level == "error" for _, _, level, _ in matches)
    warnings = len(matches) - errors
    result = [f"Lint Results: {errors} error(s), {warnings} warning(s)"]
    result.extend(f"  {path}:{line} {level}: {message[:100]}" for path, line, level, message in matches[:12])
    if len(matches) > 12:
        result.append(f"  ... +{len(matches) - 12} more")
    return "\n".join(result)


def _search_summary(output: str, command: str) -> str | None:
    if not re.search(r"(?:^|\s)(?:rg|grep|git\s+grep)(?:\s|$)", command):
        return None
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    pattern = re.compile(r"^(.+?):(\d+):(.*)$")
    for line in output.splitlines():
        match = pattern.match(line)
        if not match:
            return None
        groups[match.group(1)].append((match.group(2), match.group(3).strip()))
    if not groups:
        return None
    result: list[str] = []
    total = sum(len(matches) for matches in groups.values())
    for path, matches in groups.items():
        result.append(f"> {path} ({len(matches)})")
        result.extend(f"  {line}: {content[:90]}" for line, content in matches[:8])
        if len(matches) > 8:
            result.append(f"  ... +{len(matches) - 8} more")
    result.append(f"{total} matches in {len(groups)} files")
    return "\n".join(result)


def _is_source(path: str) -> bool:
    return Path(path).suffix.lower() in SOURCE_SUFFIXES


def _is_skill_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return "/.codex/skills/" in normalized or "/.agents/skills/" in normalized or "/skills/" in normalized and normalized.endswith("/SKILL.md")


def _filter_source(output: str, path: str) -> str | None:
    if not _is_source(path):
        return None
    suffix = Path(path).suffix.lower()
    result: list[str] = []
    metadata = False
    previous_blank = False
    for line in output.splitlines():
        stripped = line.strip()
        if stripped == "// ==UserScript==":
            metadata = True
        if metadata:
            result.append(line)
            if stripped == "// ==/UserScript==":
                metadata = False
            continue
        is_comment = stripped.startswith("#") if suffix in {".py", ".rb", ".sh"} else stripped.startswith("//")
        if is_comment:
            continue
        if not stripped:
            if previous_blank:
                continue
            previous_blank = True
        else:
            previous_blank = False
        result.append(line.rstrip())
    return "\n".join(result).strip("\n")


def _parse_anchor(line: str) -> int | None:
    for pattern in ANCHOR_PATTERNS:
        match = pattern.match(line)
        if match:
            value = int(match.group(1))
            return value if value > 0 else None
    return None


def _looks_anchored(lines: list[str]) -> bool:
    relevant = [line for line in lines[:200] if line.strip()]
    anchors = [_parse_anchor(line) for line in relevant]
    numbers = [number for number in anchors if number is not None]
    return len(numbers) >= 2 and any(right > left for left, right in zip(numbers, numbers[1:])) and len(numbers) / max(len(relevant), len(numbers)) >= 0.5


def _anchor_safe(lines: list[str], max_lines: int) -> str:
    marker = "[codex-optimizer anchor-safe: remaining anchored read lines omitted]"
    keep = max(2, max_lines - 1)
    head = (keep + 1) // 2
    tail = keep // 2
    return "\n".join(lines[:head] + [marker] + (lines[-tail:] if tail else []))


def _smart_truncate(output: str, max_lines: int) -> str | None:
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return None
    marker = f"... [{len(lines) - max_lines + 1} lines omitted by smart truncation] ..."
    keep = max(2, max_lines - 1)
    head = (keep + 1) // 2
    tail = keep // 2
    return "\n".join(lines[:head] + [marker] + (lines[-tail:] if tail else []))


def _hard_truncate(output: str, max_chars: int) -> str | None:
    if len(output) <= max_chars:
        return None
    marker = "\n... [hard truncated] ...\n"
    available = max_chars - len(marker)
    if available <= 0:
        return marker[:max_chars]
    head = (available + 1) // 2
    tail = available // 2
    return output[:head] + marker + (output[-tail:] if tail else "")


def compact_tool_output(
    tool_name: str,
    tool_input: dict[str, object],
    output: str,
    *,
    config: CompactionConfig | None = None,
) -> CompactionResult:
    settings = config or CompactionConfig()
    original = output
    current = output
    stages: list[str] = []
    stripped = ANSI_RE.sub("", current)
    current = _apply(current, stripped, "ANSI Stripping", stages)

    normalized_tool = tool_name.lower()
    command = _normalized_command(str(tool_input.get("command", "")))
    if normalized_tool in {"bash", "exec_command", "shell"} or command:
        current = _apply(current, _build_summary(current, command), "Build Filtering", stages)
        current = _apply(current, _test_summary(current, command), "Test Aggregation", stages)
        current = _apply(current, _git_summary(current, command), "Git Compaction", stages)
        current = _apply(current, _linter_summary(current, command), "Linter Aggregation", stages)
        current = _apply(current, _search_summary(current, command), "Search Grouping", stages)

    is_read = normalized_tool in {"read", "read_file"}
    if is_read:
        line_count = len(current.splitlines())
        path = str(tool_input.get("path", tool_input.get("file_path", "")))
        explicit_range = "offset" in tool_input or "limit" in tool_input
        if explicit_range or line_count <= settings.exact_read_lines or settings.preserve_skill_reads and _is_skill_path(path):
            return CompactionResult(current, tuple(stages), len(original))
        lines = current.splitlines()
        if _looks_anchored(lines) and settings.smart_truncation and len(lines) > settings.smart_max_lines:
            current = _apply(current, _anchor_safe(lines, settings.smart_max_lines), "Anchor-Safe Read Compaction", stages)
        else:
            needs_lossy = len(current) > settings.max_chars or line_count > settings.smart_max_lines
            if settings.source_filtering and needs_lossy:
                current = _apply(current, _filter_source(current, path), "Source Code Filtering", stages)
            if settings.smart_truncation:
                current = _apply(current, _smart_truncate(current, settings.smart_max_lines), "Smart Truncation", stages)

    current = _apply(current, _hard_truncate(current, settings.max_chars), "Hard Truncation", stages)
    return CompactionResult(current, tuple(stages), len(original))
