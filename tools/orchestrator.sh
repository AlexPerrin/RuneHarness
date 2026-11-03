#!/bin/bash
# The orchestrator's supervisor (docs/V9-PROPOSAL.md §3.16): the user runs it once, in their terminal, and chats with the
# session it runs. A session ends by `hd restart` (drained: context limit or a moved definition), by a crash, or by the
# user's /exit; the ledger says which, and only the user's exit stops the loop.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
while :; do
  claude --agent orchestrator "drive"
  python3 harness/hd.py session-ended $$ || break
done
