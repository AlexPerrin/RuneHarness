---
slug: harness-recordings-all-filters
track: harness
title: The RSProx text transcripts searched by track.sh recordings are made with every
  filter on
kind: change
priority: P1
deps: []
created: '2026-11-01T13:04:29Z'
---
Hand-back of server-clan-channels-1: the text transcripts behind track.sh recordings were made with the clan filters off, so 'track.sh recordings CLANSETTINGS' finds nothing. The run re-transcribed recordings 2778, 2895, 2896, 3084 and 3086 by hand with every filter on (RSProx 1.0.5 TranscribeCommand on gunzipped inputs) into evidence/server-clan-channels/rsprox-home/. Non-blocking (worked around per run) but each clan/packet-family run repeats it. Acceptance: the transcripts are regenerated with every filter on; 'track.sh recordings CLANSETTINGS' returns lines from those recordings; a test covers the filter setting.
