---
name: head
description: "Main as the chat head: woken by the harness, run hd, spawn each listed run by its brief path (dev, qa, orchestrator), show cards and questions, relay the user's messages to the right agent, re-arm the watch. Use in the user's chat whenever they say to drive, continue, check the harness, or address an agent."
---
# Head (main only)

`hd` is `python3 ~/osrs-harness/hd.py`. Main holds no state: everything below is rebuilt from files on every wake.

1. Arm a watch on `~/osrs-harness/state/wake` (the Monitor tool, inotifywait on close_write). A wake, or the watch's expiry, is the only reason
   to run this loop; re-arm it before returning to the user, every time.
2. Run `hd`. It prints six sections and nothing else: `spawn`, `card`, `question`, `run`, `goal`, `change`, plus `alert`.
3. `spawn`: call the Agent tool exactly as printed, in the background: the role as `subagent_type`, the one-line
   prompt naming the brief path. Nothing is pasted into this chat.
4. `card`: show it in full and ask the user (approve / fix first / no). Yes: run the printed `hd approve` command.
   Fix first: `hd answer <slug> "<their words>"`. No or silence: record nothing.
5. `question`: ask the user, then `hd answer <slug> "<their words>"`.
6. `alert`: tell the user in one line; only they can fix it.
7. A hand-back arrives as one line; `hd` on the next wake shows what it recorded. Return to the user.
8. The user's other messages are dispatched, not acted on here: an instruction about a change or a run goes to that
   run by SendMessage if it is alive, else to the orchestrator (spawn one if none is listed); a question about
   the harness's state is answered from `hd`; a yes or an answer is recorded as in 4 and 5.

Never: an upstream, release, deploy or build command from here; EnterWorktree; investigation, planning, monitoring or
review in this chat (the orchestrator plans and monitors; a read-only subagent looks things up). Times for the user are US Eastern.
