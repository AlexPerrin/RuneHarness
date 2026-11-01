---
slug: harness-devtools-review-gaps
track: harness
mechanism: devtools
title: Devtools read chathead expressions and jingles, and interact_object reaches
  every loc
kind: change
priority: P1
deps:
- client-devtools-review-gaps
created: '2026-11-01T05:23:40Z'
---
quest-cooksassistant-6 hand-back: three review steps rested on code reading or a workaround because the devtools data tools cannot answer them. (1) Chathead expressions: no tool reads the animation on a dialogue's chathead model, so every quest's expression rows are judged from code only. (2) Jingles: get_sound_history does not capture jingles (the Cook's Assistant completion jingle), so jingle rows are code-only. (3) interact_object cannot click the Lumbridge castle range; the run needed a workaround (evidence/quest-cooksassistant/handoff.md). Expected: get_dialogue (or a history tool) returns the chathead's anim id, the sound history includes jingles with their ids and ticks, and interact_object reaches a loc whose clickable model is offset from its tile. Proof: in a quest dialogue the expression id is read; a quest completion's jingle is read; interact_object 'Cook' on the Lumbridge range works. One test per requirement touched.
