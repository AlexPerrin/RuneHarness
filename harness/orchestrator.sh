#!/bin/bash
# The orchestrator's supervisor (docs/ARCHITECTURE.md §13): the user runs it once, in their terminal, and chats with the
# session it runs. The session runs in a user scope so each run's shell can be moved into the run's own scope. A session
# ends by `hd restart` (drained: context limit or a moved definition), by a crash, or by the user's /exit; the ledger says
# which, and only the user's exit stops the loop. The minute timer that runs the pass is started once, from this checkout.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
# A timer left by another checkout (the runtime moved) is replaced: its passes would write that checkout's paths.
systemctl --user show -p ExecStart hd-loop.service | grep -qF " $PWD/harness/hd.py tick" ||
  { systemctl --user stop hd-loop.timer hd-loop.service 2>/dev/null; systemctl --user reset-failed hd-loop.service 2>/dev/null; false; } ||
  systemd-run --user --quiet --unit hd-loop --on-calendar='*:*:00' --timer-property=AccuracySec=1s python3 "$PWD/harness/hd.py" tick
n=0
while :; do
  n=$((n + 1)); unit=hd-orchestrator-$$-$n
  systemd-run --user --scope --quiet --collect --unit "$unit" -- claude --agent orchestrator --remote-control orchestrator "drive"
  systemctl --user stop "$unit.scope" 2>/dev/null   # what the session left behind (MCP servers, a watch) ends with it
  python3 harness/hd.py session-ended || break
done
