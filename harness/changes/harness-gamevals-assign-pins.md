---
slug: harness-gamevals-assign-pins
track: harness
title: gamevals.py assign sees the pins without the hd env
kind: change
priority: P1
mechanism: server
deps: []
created: '2026-11-02T04:53:30Z'
---
Server track.md tells a dev to run tools/server/gamevals.py assign <clone> by hand, but members() reads the pins only from $PINS, which only hd's env sets; a hand-run assign skips every pin (e.g. feat/hunter, fix/25-ice-mountain-music-area) and hands out ids the hand-over's check then refuses (hunter-feat-pr-17: three ids, and the repeated renumber answers of 2026-10-31). Root cause: two callers derive the member list differently. Fix: one member list for assign and check (read the pins from hd.yaml, or a track.sh verb that runs assign with hd's env), so an assign can never pick an id check refuses.
