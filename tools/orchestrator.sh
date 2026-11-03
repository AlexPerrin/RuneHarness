#!/bin/bash
# R2: the orchestrator's supervisor: the user runs it once, in their terminal, and chats with the session it runs; a
# shipped definition reaches the session by `hd` printing it (hd.reread). It starts the next session when one ends by
# `hd restart` (state/orchestrator-restarting) or crashes after its start (a non-zero exit with state/orchestrator-started,
# written by the SessionStart hook); it stops on the user's exit (/exit or Ctrl-C exit 0) and on a session that fails at its start.
cd "${HD_ROOT:-$(dirname "$(readlink -f "$0")")/..}" || exit 1
while :; do
    rm -f state/orchestrator-started state/orchestrator-restarting
    claude --agent orchestrator "drive"
    rc=$?
    if [ -e state/orchestrator-restarting ]; then
        echo "orchestrator.sh: the session restarted itself: starting the next"
    elif [ "$rc" -ne 0 ] && [ -e state/orchestrator-started ]; then
        echo "orchestrator.sh: the session ended (exit $rc): starting the next"
    else
        [ "$rc" -ne 0 ] && echo "orchestrator.sh: claude failed at its start (exit $rc): not restarted"
        exit "$rc"
    fi
done
