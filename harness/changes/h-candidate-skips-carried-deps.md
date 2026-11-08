---
slug: h-candidate-skips-carried-deps
track: harness
priority: P0
---
# A candidate leaves out a dependency head a later head already carries

act.candidate folds merge-tree over base, each dep head and the head in turn, so two dep heads that conflict with each other (h-ref-server-bundle 983b9c0 and h-ref-sign-in-no-issuer b09eaa8: tracks/fork/track.sh, test_tools.py, docs/ARCHITECTURE.md) fail every dependent's hd submit, even when the dependent's head merged both and resolved the conflict (h-ref-embedded-central 0a… at harness/h-ref-embedded-central: 'the candidate on refs/heads/v9 conflicts'). Fix (run 263 wrote and tested it, then took it out of its own change since the live hd submit computes the candidate): in act.candidate, before the fold, heads = [h for i, h in enumerate(heads) if not any(is_ancestor(path, h, l) for l in heads[i + 1:])]; docs/ARCHITECTURE.md candidate(): 'each dependency head not yet in it nor in a later head'; a test in tests/test_observe.py: two branches editing the same line conflict as [d1, d2], and [d1, d2, head] where head merged both with a resolution returns head. Done when hd submit h-ref-embedded-central builds its candidate on v9 with both deps still unlanded. Found by run 263.
