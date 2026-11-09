#!/usr/bin/env bash
# MCP stdio server for OpenRune-Developer-Tools running in the Android plugin host (see
# tools/devtools_mcp.py for setup). Register: {"command": "<repo>/tools/devtools-mcp.sh"}.
exec python3 -I "$(dirname "$(readlink -f "$0")")/devtools_mcp.py" "$@"
