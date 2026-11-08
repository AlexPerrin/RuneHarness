---
slug: h-dep-gate-failed-waits
track: harness
priority: P0
---
# A dependent's dev waits while a same-track dep's head failed its gate

decide.deps_live lets a dependent's dev run once a same-track dep has any submission (the dep joins the candidate). When that dep's submitted head failed its gate (h-ref-server-bundle, h-ref-pins-audit, h-ref-sign-in-no-issuer: replay at 983b9c0, 5db15f0, 7fb9fc6), the dependent builds on a head that cannot ship, and an umbrella whose remaining work is the observation over its landed parts (h-reference-deployment, run 270) is run with nothing it can prove. A same-track dep joins the candidate only while its latest head has not failed its gate; otherwise the dependent waits on 'dep <x> gate failed at <head>'. Done when tests/test_decide.py covers it over a ledger snapshot and the replay shows h-reference-deployment waiting instead of a dev run.
