---
slug: harness-answer-reaches-dev
track: harness
title: The user's fix-first answer on any change reaches its dev step
kind: change
priority: P0
mechanism: contract
deps: []
created: '2026-11-01T22:02:33Z'
---
Monitor sweep 3 (2026-11-01 ~22:01Z): hd answer writes a harness-track answer as a 'note' row (hd.py:1937) that no step reads. harness-spotless-check-row's answer-1 (21:32:16Z: 'Fix first: the spotless verb must create or reuse the slug's gradle volume...') came after its 21:31:12Z handover; since then only its old head f49d91a was built/gated 5 times and no dev run was listed - the user's word is lost and the change would ship unfixed. Same for harness-hook-writes-locked and harness-hold-card answers sent by the orchestrator. Root cause: R3 says the answer is a contract row, but a row nobody checks has no effect. Acceptance: an answer recorded after a handover on any track makes the change's next step a dev run whose brief carries the answer (the head is not built, gated or shipped until a new handover); a test covers a harness change answered after handover.
