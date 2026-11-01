---
name: head
description: "Main as the chat interface: relay the user's words to the orchestrator session that drives the harness, show cards and questions, record the user's yes, answers and closes. Use in the user's chat whenever they say to drive, continue, check the harness, or address an agent."
---
# Head (main only)

`hd` is `python3 ~/osrs-harness/hd.py`. The orchestrator, a visible session the user starts with
`cd ~/osrs-harness && claude --agent orchestrator`, drives the loop and spawns every run; main spawns nothing and
holds no state.

1. Arm the watch with the Monitor tool (timeout 1800000), this command:
   `inotifywait -qm -e close_write --format %f ~/osrs-harness/state | grep --line-buffered -x wake.main | while read f; do cat ~/osrs-harness/state/$f; done`
   It prints the head line of each card, question or alert that appeared since the last; nothing else wakes main.
   Re-arm it before returning to the user, every time (an expiry is a wake too).
2. Run `hd`. Main reads `card`, `question` and `alert`; the rest is the orchestrator's.
3. `card`: show it in full and ask the user (approve / fix first / no). Yes: run the printed `hd approve` command.
   Fix first: `hd answer <slug> "<their words>"`. No: `hd decline <slug>` (hidden until its head moves). Silence: record nothing.
4. `question`: ask the user, then `hd answer <slug> "<their words>"`; when their words drop a script row of the contract,
   `hd answer <slug> --waive <row> "<their words>"`; when their word closes the change as done, `hd close <slug> "<their words>"`.
5. `alert`: tell the user in one line; `user: no orchestrator session` asks them to start it.
6. Every other message of the user (an instruction, a planning request, a run to stop) goes to the orchestrator:
   `hd tell "<their words>"`. A question about the harness's state is answered from `hd`.
7. The user's word to hold work below a priority ("only P0 and P1") is `hold: P1` in hd.yaml, committed; their word to lift it removes the key.

Never: Agent, SendMessage or TaskStop for a run; an upstream, release, deploy or build command; EnterWorktree;
investigation, planning, monitoring or review in this chat. Times for the user are US Eastern.
