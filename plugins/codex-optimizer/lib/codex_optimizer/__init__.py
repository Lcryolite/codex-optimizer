"""Runtime support for the Codex Optimizer plugin."""

from .compact import ALL_STAGES, CompactionConfig, CompactionResult, compact_tool_output

__all__ = ["ALL_STAGES", "CompactionConfig", "CompactionResult", "compact_tool_output"]
