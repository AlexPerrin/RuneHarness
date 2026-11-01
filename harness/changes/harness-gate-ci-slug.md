---
slug: harness-gate-ci-slug
track: harness
title: The gate's ci row runs track.sh gate-ci with no slug, so its push refspec is
  gate/ and every server gate fails
kind: change
priority: P0
deps: []
created: '2026-11-01T00:24:41Z'
---
The server contract's row 'ci | ... | gate: tools/track.sh gate-ci' passes no slug argument, and tools/track.sh reads the slug only from $2 (line 14: slug=${2:-}), so gate_ci pushes "$TCOMMIT:refs/heads/gate/" and git refuses. Evidence: state/genie-review-355/gate.json at T 69fca5fb9 (commit 42fa642ee): 'fatal: invalid refspec '42fa642eed182f5436287466ad4cc889b39e8a9b:refs/heads/gate/''; the other check rows passed. hd rows already exports SLUG in the row env (hd.py Ctx.env), so the fix is for track.sh to fall back to it (slug=${2:-${SLUG:-}}) or for the seed row in tools/track.md and every server contract to pass $SLUG. The state dir line also uses the empty slug (state/ instead of state/<slug>). Every server change reaching its gate fails the same way (gate-ci has never run for real, docs/HANDOFF.md). One test per requirement touched.
