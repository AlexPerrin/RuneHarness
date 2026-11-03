---
slug: harness-parallel-spawn-binding
track: harness
title: Runs spawned together bind to the wrong agent, or to none
kind: change
priority: P0
deps: []
created: '2026-10-31T23:37:31Z'
---
The head spawned three qa runs in one message at 23:35Z: cannon-review-354-1, genie-review-355-1 and goblin-diplomacy-review-367-1, each prompt naming its own brief. Only one start bound, as cannon-review-354-1, at 23:35:37Z. That run ended at 23:36:49Z with record false after 15 turns, which is the goblin agent's lifetime. The goblin agent recorded its hd ask on goblin-diplomacy-review-367. The runs files for genie-review-355-1 and goblin-diplomacy-review-367-1 have started None, so the pass lists both as spawns again, and it lists cannon-review-354-2 although the cannon agent is still alive. Root cause to find: how SubagentStart in hook.py matches an agent to its run (it should key on the brief path in that agent's prompt). Also close harness-client-track-root: its fix is 201278e on v8, but its dev was spawned outside the loop, so the pass still says dev run due. One test per requirement touched.
