---
slug: harness-devtools-review-gaps
track: harness
mechanism: devtools
title: Devtools read chathead expressions and jingles, and interact_object reaches
  every loc
kind: change
priority: P1
deps:
- client-devtools-review-gaps
- harness-mcp-restart-on-ship
- harness-devtools-call-names-port
- harness-devtools-endpoint-owner
created: '2026-11-01T05:23:40Z'
---
quest-cooksassistant-6 hand-back: three review steps rested on code reading or a workaround because the devtools data tools cannot answer them. (1) Chathead expressions: no tool reads the animation on a dialogue's chathead model, so every quest's expression rows are judged from code only. (2) Jingles: get_sound_history does not capture jingles (the Cook's Assistant completion jingle), so jingle rows are code-only. (3) interact_object cannot click the Lumbridge castle range; the run needed a workaround (evidence/quest-cooksassistant/handoff.md). Expected: get_dialogue (or a history tool) returns the chathead's anim id, the sound history includes jingles with their ids and ticks, and interact_object reaches a loc whose clickable model is offset from its tile. Proof: in a quest dialogue the expression id is read; a quest completion's jingle is read; interact_object 'Cook' on the Lumbridge range works. One test per requirement touched.

Also (filed): the permission classifier denies a qa run's own test-account game actions (continue_dialogue, ::invclear)
genie-review-355-132 hand-back (qa, ~01:2xZ): the permission classifier blocked mcp__osrs-devtools-desktop__continue_dialogue and a '::invclear' chat command on its own run's desktop and server; it worked around by dropping spawned logs. A qa run playing its own instance needs these allowed in the committed .claude/settings.json (::empty stays forbidden on the tester account per CLAUDE.md; ::invclear on a run's own account is the cleanup). Evidence: evidence/genie-review-355/ingame-review-132/summary.txt

Also (filed): R6 desktop-call bound test fails under parallel load
harness-orchestrator-self-restart-1 saw R6.test_a_desktop_call_is_answered_within_its_bound_when_its_token_read_or_endpoint_hangs (0.3 s bound) fail once alongside other classes; passed on rerun and on v8. A bound that depends on host load is a time estimate: decide on an observable fact. Evidence: evidence/harness-orchestrator-self-restart/tests-R2-R5-R6.txt

Also (filed): A desktop devtools call answers within its bound: type_chat hung 30 minutes
hunter-feat-pr-22 (qa, head 89632544d): the desktop's type_chat hung for 30 minutes during the bird house test, which ended play; none of the other activities could be played at this head (6 rows failed, 97 not judged). The same run's first up again failed with no inventory sent after login (as server-world-entities-14; joined harness-live-stack-issuer). Evidence: evidence/hunter-feat-pr/qa-in-game-22.md

Also (filed): A desktop walk_to reports progress, ends on its own bound and stops on cancel
Sweep 76 P2-a: server-world-entities-16 called walk_to(7781, 3080,3250) at 18:23:44Z; the MCP log (~/.cache/claude-cli-nodejs/-home-alex-osrs-harness/mcp-logs-osrs-devtools-desktop/2026-11-02T18-00-03-239Z.jsonl) shows 'still running' every 27 s until 18:53:46Z 'no response or progress notification for 1800s; aborting'; the player was still on 3088,3218. walk() (mcp/devtools_bridge.py:147-179) loops while True with no overall bound and sends no MCP progress notification; handle() (:225) drops every notification including notifications/cancelled, so after the abort the walk thread kept clicking the client ('Opened the bank by accident' 18:55:02Z). Bound the walk on observed facts (no tile progress), send progress notifications, and honour cancel. Evidence: evidence/monitor/sweep-76.md, subagents/agent-a62e0ccbd7f164988.jsonl

Also (filed): A run reaches only its own desktop, over the devtools tools or HTTP alike
Sweep 77 P5-a: hunter-feat-pr-27 wrote evidence/hunter-feat-pr/qa27/dt.py (19:53:36Z), which reads state/<change>/up.json['token'] and POSTs tools/call to 127.0.0.1:7780/mcp, skipping hook.py own_desktop (:267) and the idle count (:649); evidence/server-clan-channels/dt.py does the same via desktop_login.call. Any run can read any change's up.json token, so own_desktop is advisory. No harm seen (own desktop). Evidence: evidence/monitor/sweep-77.md
