#!/bin/bash
# R2: the orchestrator's supervisor: the user runs it once, in their terminal, and chats with the session it runs; a
# shipped definition reaches the session by `hd` printing it (hd.reread). It starts the next session whenever one ends,
# until the user ends one (their /exit or Ctrl-C: a clean exit with no hand-off left): a session that restarted itself
# (`hd restart`) left state/orchestrator-handoff.md for its successor, and a crash exits unclean.
cd "${HD_ROOT:-$(dirname "$(readlink -f "$0")")/..}" || exit 1
while :; do
    claude --agent orchestrator "drive"
    rc=$?
    [ -e state/orchestrator-handoff.md ] || [ "$rc" -ne 0 ] || exit 0
    echo "orchestrator.sh: the session ended (exit $rc$([ -e state/orchestrator-handoff.md ] && echo ', restarted itself')): starting the next"
done
