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

Also (filed): An approved carry resumes the exact texts the user approved and is never stopped mid-carry by a harness ship
Sweep 89 round 5 P0-a: the user approved goblin-367-rsprox-dump at def7f2c59 at 22:03:37Z (texts a436c427). state/goblin-367-rsprox-dump/ship.log: 22:04:13Z pushed def7f2c59 to content/goblin-diplomacy, 22:04:14Z updated the body of PR 367, then the CI wait. At 22:08:28Z the ship of harness-handoff-on-open-dep (eee436a) changed hd.py, so ctx.start (hd.py:~1400, outdated carry) stopped the carry (events.jsonl:11748, pid 2733043); the rerun (pid 2821117) logged 'refused: no yes at def7f2c59 and these texts' (ship.rc 1) and the step became 'the comment misses findings IC_kwDOQBbPT88AAAABhyfg1w: dev' (11750). Upstream now: #367 has the new head and body, CI running, no comment, still draft: the one atomic upstream action is broken. Root causes: approved() (hd.py:2013) compares the yes against public_texts recomputed from the live PR (hd.py:2942: the body when it differs from the live one, the push summary when the push moves the PR), so the carry's own first writes change the texts and a stopped carry can never resume; and every harness ship changes hd.py and stops every carry in flight while carries wait 5-20 min on CI. Fix: bind the yes to the card's texts as a record and have the carry post exactly those, skipping steps already done; never stop a carry that holds a yes (let it finish or resume from its own log). The goblin-367 carry must finish with the approved comment and ready once CI is green, with no dev rewrite of the comment. Evidence: state/goblin-367-rsprox-dump/ship.log, evidence/monitor/sweep-89.md
