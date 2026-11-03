---
slug: harness-qa-unjustified-upstream-test
track: harness
title: qa passed an upstream PR's non-dupe test as justified
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T02:13:40Z'
---
The user (2026-11-01, ET): 'Use tests sparingly in upstream PRs (content/quest/src/test/kotlin/org/rsmod/content/quest/area/lumbridge/CooksAssistantInteractionTest.kt), use tests to show dupe checks for items for eg.' quest-cooksassistant was carried at 1d586b49f with that interaction test although the server track.md (line 21: 'Default no tests, except a dupe test per item-moving flow and a rule with several cases, justified in the PR text') and the style row ('no unjustified test') forbid it. The qa judgment (qa-server) must refuse any upstream test that is not a dupe test of an item-moving flow or a multi-case rule justified in the PR text, and the dev rules say so where tests are written.
