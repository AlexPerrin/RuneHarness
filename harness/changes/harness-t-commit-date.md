---
slug: harness-t-commit-date
track: harness
title: The loop's T merge commits are dated 2000-01-01
kind: change
priority: P2
deps: []
created: '2026-11-01T01:55:22Z'
---
The user saw a238c43 shown as 27 years ago on GitHub. hd builds each T merge commit (T: <slug> <head> onto <base>) with a fixed author and committer date of 2000-01-01 so T is reproducible, and ship fast-forwards the live branch onto it, so the fixed date reaches v8 and its remote. Keep T reproducible but realistic: date it from the newest of its parents' committer dates. The same inputs then still give the same commit. Existing T commits on v8 stay; do not rewrite pushed history. One test per requirement touched.
