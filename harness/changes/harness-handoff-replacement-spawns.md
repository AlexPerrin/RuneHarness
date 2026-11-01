---
slug: harness-handoff-replacement-spawns
track: harness
title: A run that hands off near its context limit is replaced at once by a run that
  resumes from its handoff
kind: change
priority: P0
deps: []
created: '2026-11-01T18:03:49Z'
---
The user's word: "agents should gracefully handoff to it's replacement when context window is near". cannon-354-reset-ammo-varp-2 hit the context limit after the in-game proof (A1, A2, A4, A5) and wrote evidence/cannon-354-reset-ammo-varp/handoff.md, but no replacement run followed: hd shows the change 'dev run due: head 7a8b2331a not handed over' and lists no spawn, because the tier hold keeps every P2 change from spawning while P1 changes are open, waiting or not (harness-hold-p3-while-higher-open). The reply to a-thoren's finding 4433251631 therefore was never written. Acceptance: (1) the outgoing run's handoff happens before the limit, with its state written (handoff.md: what is proven, what is left, the exact next step, whether a server/desktop is up); (2) a run that ended in a handoff is replaced in the same pass by a run of the same role on the same change, whose brief names the handoff file and says to resume from it, and the tier hold and the slot count do not hold that replacement; (3) a test covers a handoff while a higher tier is open: the replacement is listed in the same pass.
