---
slug: h-osrs-mcp-launcher-leak
track: harness
priority: P1
---
# osrs-mcp launchers leak: one container every ~30 s, none exits

Observed 2026-11-11: 33 osrs-mcp containers (eclipse-temurin:21, ~85 MB each, idle) with three Claude sessions running (orchestrator, driver, one console). Created about every 30 s from 02:03 ET (the orchestrator and driver tmux start), sometimes in pairs 3 s apart. Every mcp/osrs-mcp.sh launcher is alive, parented by /init (PID 413), blocked in wait on its docker run: its EXIT/TERM trap never fires and nothing closes its stdin. The console session's osrs-mcp failed with CONNECT_SUSPENDED (timed out) at startup, which fits a client that gives up and reconnects without ending the old launcher; the mechanism is not confirmed. Find the root cause (which session reconnects, why the old launcher survives its client) and fix it in the launcher and the harness: a launcher ends with its client (parent gone or stdin closed) and removes its container; a start for a client replaces its predecessor, so at most one osrs-mcp container per session; hd or the supervisor reports a count above the session count as an alert. A test per rule. The 33 running containers are the user's to stop.

## Root cause (found by the user's one-off fix)
fbc5be6 started the server as `docker run … &` then `wait`. A background job in a script has /dev/null as stdin unless
it is passed on, so the server never saw its client: the connection timed out, the client retried, and each retry left a
launcher and a container. Fixed in mcp/osrs-mcp.sh (`<&0`) with tests/test_osrs_mcp_launcher.py. What remains: the dev
checks a client's restart replaces its predecessor (at most one container per session) and adds the count alert.
