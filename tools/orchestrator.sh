#!/bin/bash
# R2: the orchestrator's supervisor: the user starts it once, in their terminal, and chats with the session it runs;
# a session that ends by `hd restart` (its mark state/orchestrator.restart) is followed by a fresh one on the live
# definition; one the user ends ends the supervisor.
cd "${HD_ROOT:-$(dirname "$(readlink -f "$0")")/..}" || exit 1
while :; do
  rm -f state/orchestrator.restart
  claude --agent orchestrator "drive"
  stty sane 2>/dev/null
  [ -e state/orchestrator.restart ] || exit 0
done
