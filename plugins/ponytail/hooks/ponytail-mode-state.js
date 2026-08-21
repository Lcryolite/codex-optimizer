#!/usr/bin/env node
"use strict";

const fs = require("fs");
const { getDefaultMode } = require("../upstream/hooks/ponytail-config");
const { clearMode, readMode, setMode } = require("../upstream/hooks/ponytail-runtime");

const event = process.argv[2];
if (event !== "SessionStart" && event !== "SubagentStart") process.exit(2);

let payload = {};
try {
  payload = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
} catch (_) {}

const startsFresh = event === "SessionStart" &&
  (payload.source === "startup" || payload.source === "clear" || !payload.source);
const mode = startsFresh ? getDefaultMode() : (readMode() || getDefaultMode());

try {
  if (mode === "off") clearMode();
  else setMode(mode);
} catch (_) {}

// Full is the upstream default. Codex discovers and loads the upstream skill
// only for coding tasks, so the common path needs no model-visible hook output.
if (mode === "full") process.exit(0);

const context = mode === "off"
  ? "PONYTAIL MODE OFF. Do not load or apply Ponytail until the user enables it."
  : `PONYTAIL MODE ${mode.toUpperCase()}. On coding tasks, load the Ponytail skill and apply ${mode} intensity.`;

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: event,
    additionalContext: context,
  },
}));
