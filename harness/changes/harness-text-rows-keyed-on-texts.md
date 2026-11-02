---
slug: harness-text-rows-keyed-on-texts
track: harness
title: A row that reads the public texts is keyed on them, and the texts row checks
  every text posted
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T19:41:31Z'
---
Sweep 74 P3-a: every row's key is the tree plus the tools files (hd.py:1234-1253 key, ROWKEYS hd.py:1724, :1839); rows() keeps a stored result on a key match (hd.py:3181-3185); but text.py texts and evidence read $EVIDENCE/*.md outside the tree, so their result stays ok however the texts change. goblin-367: state/goblin-367-rsprox-dump/row-check-texts.json 'texts: ok' at 18:50:57Z; goblin-367-rsprox-dump-19 wrote three evidence/goblin-367-rsprox-dump/pr-reply-*.md at 19:30:25Z; the change went 'gated; waiting for the user's yes' at 19:30:43Z (events.jsonl:11001) with no new gate (proc-gate.json 18:50:51Z), so the card carries replies no row checked (clean on reading). Also text.py:53-66 (server tools) checks only pr-title.txt, pr-body.md, pr-comment.md for fork-PR links while public_texts (hd.py:2864-2868) posts one_comment([push, *replies]) with every pr-reply-*.md. Key such rows on the public texts' digest (digest(json.dumps(public_texts(ctx, ch))), hd.py:1942, :3368) and have texts cover everything public_texts posts. Evidence: evidence/monitor/sweep-74.md
