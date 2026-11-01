---
slug: harness-state-atomic-write
track: harness
title: hd never reads a half-written state record
kind: change
priority: P0
deps: []
created: '2026-11-01T13:11:28Z'
---
hd crashed in the orchestrator's pass (2026-11-01, during a gate): nxt() -> rec(slug, 'gate') -> json.loads raised JSONDecodeError 'Expecting value: line 1 column 1 (char 0)' on an empty gate record (hd.py:306, :704). The rerun a moment later passed, so the record was read while being written. A crashed pass prints nothing, so the loop stops acting until the next wake. Acceptance: every state/ JSON record is written atomically (temp file + os.replace) and rec() never sees a partial file; a test covers a reader racing a writer.
