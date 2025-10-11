#!/usr/bin/env bash
# Wrapper script to run ai CLI in sandboxed environment
# Usage: ./sandbox-run.sh act "your prompt"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SANDBOX_PROFILE="$SCRIPT_DIR/sandbox.sb"

CWD="$(pwd)"
export CWD HOME

exec sandbox-exec \
    -D "CWD=$CWD" \
    -D "HOME=$HOME" \
    -f "$SANDBOX_PROFILE" \
    uv run --directory "$SCRIPT_DIR" ai "$@"
