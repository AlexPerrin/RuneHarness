---
slug: harness-verdict-no-unjudged-pass
track: harness
title: A verdict never records an unjudged row as pass
kind: change
priority: P1
deps: []
created: '2026-11-01T06:17:19Z'
---
server-friends-chat-clan-channels-11 recorded FAIL 4 rows at 1c323b5fe and marked acc-3, acc-11, acc-13, acc-15, acc-16, acc-18, acc-20, acc-21, claims, playable and unsourced as pass although none was checked in game at that head (listed only in the accuracy row's note). A verdict whose rows pass without being judged can later carry a change to approval on rows no one checked. Expected: a verdict row is pass, fail, or not-judged; hd verdict refuses a PASS verdict with any not-judged row, a FAIL verdict may carry not-judged rows, and the next brief lists them as the judge's open rows. qa.md says the same. One test per requirement touched.
