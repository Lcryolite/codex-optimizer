#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'

> codex-optimizer-demo@1.0.0 test
> jest --runInBand

PASS src/auth.test.ts
  ✓ refreshes an expired token (8 ms)
  ✓ rejects a malformed token (2 ms)
PASS src/user.test.ts
  ✓ returns the current user (3 ms)
  ✓ rejects an unknown user (1 ms)

Test Suites: 2 passed, 2 total
Tests:       4 passed, 4 total
Snapshots:   0 total
Time:        1.248 s
Ran all test suites.
EOF
