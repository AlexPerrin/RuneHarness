# ISSUES

The open ledger of the v8 build. A quick fix lands at once and is not logged. What lands here is a root cause in the
design or a rewrite too large for the run, and the measurements of v7 that were never confirmed; newest first.

## Open
- **A dev's tap on the mobile is never retried** (`tools/mobile_login.py`): a missed tap waits forever; the screen
  state needs a readable fact (the host's logcat lines) per dialog.
- **`hd-public` finds the PR with `gh pr list --head owner:branch`**, a form not verified against a real fork branch;
  if gh ignores the owner part the lookup finds nothing and a second draft PR is opened. Check once before the first ship.
- **The compose file was not validated from this session**: the v7 guard refuses `docker compose config`; the first
  `ship` validates it.
- **The sidecar's data and image come from v7's tools branch** (`osrs-rsps-test:241`, `sidecar/data`): the server
  files the test server needs beyond the fork's tree are not yet on `local/harness`.
- **Unconfirmed v7 measurements** (the monitor): the 131-module recompile after adding a pack module; why every
  SubagentStop hook was cancelled; that the binary RSProx recordings hold clan packets; the fixed-mode login
  coordinates as the cause of the 10-31 login stall.
