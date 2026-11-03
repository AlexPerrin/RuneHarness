---
slug: harness-gate-rekey-on-tools
track: harness
title: A gate failure recorded before a tools fix stands after the fix ships, so the
  change goes to a dev who cannot fix it
kind: change
priority: P0
deps: []
created: '2026-11-01T00:30:34Z'
---
The build and gate records are keyed by the tree only (hd.py:525-533: `b["T"] != tree`, `g["T"] != tree`). A fix to the track tools (the fork's local/harness, the client's client/harness-v8, or this repo's tools/) changes neither the change's head nor its tree, so the old failure is read back and the pass routes it to a dev run.
Evidence:
- state/genie-review-355/gate.json (mtime 2026-11-01T00:21:11Z): T 69fca5fb9..., ok false, "FAIL: ci: tools/track.sh gate-ci / fatal: invalid refspec '42fa642ee...:refs/heads/gate/'".
- The fix (harness-gate-ci-slug, fork local/harness f0e5b0ae0 at 00:27:03Z) went done at 00:28:17Z; the same second events.jsonl records genie-review-355 "gate failed: dev" with that same detail, and no gate ran after (gate.log, proc-gate.json still 00:20:57Z). hd now lists "genie-review-355 [server P0]: gate failed: dev"; the dev already said no code change of theirs can pass it (record ask 00:24:49Z).
Fix: store with each build and gate record what produced it (the tools heads ctx.tools(ch) already returns and the track script's own commit), and re-run when it differs, the way handover already compares tools. Coordinate with harness-start-reset-on-script-change (same root: results not keyed by the script version); one mechanism for both if it fits. One test per requirement touched (R5). Prove it with one real pass that re-gates genie-review-355 on 69fca5fb9.
