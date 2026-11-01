---
slug: harness-pass-lock-short
track: harness
title: The pass reads outside the state lock and holds it only to decide and write;
  hooks never wait on it; a pass is bounded in time and memory
kind: change
priority: P0
deps: []
created: '2026-11-01T21:43:49Z'
---
Root cause found by the monitor sweep (2026-11-01 ~21:45Z), and the user's report: "hd also hold 3-4 GB of memory." A pass holds hd's state lock across all its git and GitHub reads: 20-74 s per pass, back to back (journal 21:32-21:38Z, 3.6G memory peak); one pass took >120 s. hook.py bind() (and, once harness-hook-writes-locked ships, end_run) waits on that lock, but PreToolUse/SubagentStart hooks time out at 10 s and SubagentStop at 30 s, so they are cancelled: agents never bind (a57c2d6... cancelled 5 times from 21:28:13Z; harness-e2e-test-flaky-1 10 times, harness-limits-are-bugs-root-cause-1 7 times), their runs are dropped 'no longer due' while the agents work (21:29:33Z, 21:34:41Z), -2 runs are listed for live agents, hand-backs land untracked (stop-unmatched 21:31:58Z), and a cancelled PreToolUse runs none of its deny rules (hd approve/close refusal, cycle commit refusal) - a hole in the user's authority. Against the workflow: 'the orchestrator spawns every run; every run is a visible agent' needs the agent-run binding recorded as a fact at spawn, never a write racing a slow pass.

Supersedes (merge, by the root-cause rule): harness-base-move-keeps-runs (misdiagnosed: v8 did not move the dev refs; the agents created them at 21:32:58Z/21:33:01Z; a bound run is never dropped), the end_run part of harness-hook-writes-locked, and harness-spawn-for-ended-run-refused's dependence on a hook that is cancelled.

Acceptance: (1) a pass gathers all facts (git, GitHub, docker) without the lock, then takes the lock only to re-read state, decide and write (milliseconds); (2) hooks never wait on the lock: the hook appends a fact (bind, end, context-limit, idle) to an append-only events file with O_APPEND, and the pass folds facts into run records under its short lock; deny rules read only definitions and the command, never the lock; (3) a pass's peak RSS stays under 200 MB and its wall time is bounded by its slowest single read (no per-change repeated reads; GitHub and git reads memoised per pass; large outputs streamed, not held); (4) tests: a hook during a long pass completes in <1 s and its fact is folded in; a pass's peak memory on the live state is measured and asserted; the three cancelled-hook cases above replayed.
