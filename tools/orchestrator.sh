#!/bin/bash
# R2: the orchestrator's start: the user runs it once, in their terminal, and chats with the session it runs; a shipped
# definition reaches the session by `hd` printing it (hd.reread), so it never ends for one.
cd "${HD_ROOT:-$(dirname "$(readlink -f "$0")")/..}" || exit 1
exec claude --agent orchestrator "drive"
