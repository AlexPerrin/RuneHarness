---
slug: harness-round-crosses-track
track: harness
title: A maintainer round the user moves to another repo becomes a change on that
  track and closes the old PR with a link
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T22:04:44Z'
---
Sweep 89 round 3 P2-a: after harness-filestore-track shipped (22:03:04), server-448-cickwdoqbbpt88aaaabijnvha-2 was listed and started as a server-track run (state/events.jsonl:11701-11703) with pr: 448 and the OpenRune-Server clone; its contract's answer-2 reads only 'the user: a' (written before d4f21fe's quoting), so the run must guess that (a) meant 'add FileStore as a target, port the fix as a new PR on OpenRune/OpenRune-FileStore, close #448 pointing to it'. A server-track change's card and ship act only on OpenRune-Server #448; no hd step moves a round to another track. Needed: the round's next step is a change on the target track (a new PR there) plus a close of the old PR with a link, an upstream act on a card. The orchestrator told run -2 the question and to file the port with hd new --track filestore. Evidence: evidence/monitor/sweep-89.md
