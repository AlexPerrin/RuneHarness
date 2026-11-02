---
slug: harness-tools-ship-keeps-live
track: harness
title: a tools ship takes unchanged content off the live server until each head re-gates
kind: change
priority: P1
mechanism: tree
deps: []
created: '2026-11-02T03:49:33Z'
---
sweep-31 P1-a: integration() (hd.py:1825-1830) keeps a head only while ctx.gated(ch, head) holds, and gated() (hd.py:1104-1115) compares against the current gate key, which includes the tools/build and tools/gate hashes; the 03:30:05Z tools ship dropped every head not yet re-gated, so deploy 834be1a6a (from 03:48:06Z) leaves out server-world-entities, quest-cooksassistant and quest-restlessghost, all in live's state/live/tree.json. A head stays in T_int while its gate passed at the same head and tree under an earlier tools key, until the new gate fails. evidence/monitor/sweep-31.md
