---
slug: harness-watches-wake-on-change
track: harness
title: Each session's watch wakes only on a change in what it acts on
kind: change
priority: P0
deps: []
created: '2026-11-01T12:13:08Z'
---
The user (2026-11-01, relayed by main): wake events spam both the orchestrator and head chats; hide them or make them more useful. Main now filters its own watch to fire only when hd's card/question/alert lines change. Expected: the head skill's watch and the orchestrator's watch each wake only when the lines that session acts on change (main: card/question/alert/message; orchestrator: spawn/message/hand-back), with one documented command each. Also: the 'no orchestrator session' alert stays up while the orchestrator runs (it must clear when the orchestrator session is alive), and a card the user declined is not shown again until its hold clears. One test per requirement touched.
