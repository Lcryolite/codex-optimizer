"""Safe delegation to the installed RTK command rewriter."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess


SUDO_WORD = re.compile(r"(?<![A-Za-z0-9_-])sudo(?![A-Za-z0-9_-])")
SENSITIVE_COMMANDS = {
    ("cargo", "publish"),
    ("docker", "push"),
    ("gh", "release"),
    ("git", "push"),
    ("kubectl", "apply"),
    ("kubectl", "delete"),
    ("npm", "publish"),
    ("pnpm", "publish"),
    ("terraform", "apply"),
    ("terraform", "destroy"),
    ("yarn", "publish"),
}
SENSITIVE_WORDS = {"rm", "shred"}


def _shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command.replace("\\\n", ""), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def contains_sudo(command: str) -> bool:
    """Conservatively recognize sudo anywhere in shell syntax."""

    return any(SUDO_WORD.search(token) for token in _shell_tokens(command))


def contains_approval_sensitive_mutation(command: str) -> bool:
    """Keep publish, remote-write, and destructive commands in Codex's normal approval path."""

    words = [token.lower() for token in _shell_tokens(command)]
    if any(word in SENSITIVE_WORDS for word in words):
        return True
    return any(pair in SENSITIVE_COMMANDS for pair in zip(words, words[1:]))


def rewrite_with_rtk(command: str) -> str:
    executable = shutil.which("rtk")
    if executable is None:
        return command
    try:
        result = subprocess.run(
            [executable, "rewrite", command],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return command
    rewritten = result.stdout.rstrip("\n")
    # RTK uses exit 3 to signal that a rewrite occurred. Its stdout is the
    # protocol payload; an empty payload means the command is unsupported.
    return rewritten if result.returncode in {0, 3} and rewritten else command


def safe_rewrite(command: str) -> str:
    try:
        if contains_sudo(command) or contains_approval_sensitive_mutation(command):
            return command
    except ValueError:
        return command
    return rewrite_with_rtk(command)
