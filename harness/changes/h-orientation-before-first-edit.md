---
slug: h-orientation-before-first-edit
track: harness
priority: P2
---
# agents spend their first calls orienting: measure it per run and cut the crawl

The user's hand-off (2026-11-09), verbatim below. Solution design is the dev's; check each fact against the code and the ledger before acting on it.

Problem: a dev run makes many tool calls before its first edit, most of them searching, reading and re-reading state the harness already holds.

## Baseline
Mean tool calls before the first edit per run, from an audit of run transcripts (fork = OpenRune-Server, client = osrs-plugins-reverse, harness = this repo):

| category | fork | client | harness |
|---|---|---|---|
| search (grep, rg, find) | 9.9 | 8.9 | 4.5 |
| read (cat, sed, head, ls) | 5.6 | 5.7 | 2.4 |
| `hd show` | 3.7 | 1.5 | 1.8 |
| git | 2.8 | 1.6 | 2.0 |
| brief, definition, rules | 1.2 | 1.4 | 1.1 |
| **total** | 23.2 | 19.1 | 11.8 |

Central has no audit yet.

## Issues, by impact
### 1. Search dominates the first calls (43% of fork, 47% of client)
- The brief names the clone by path and gives no map of the code, so each run discovers the layout itself.
- Fork: 5,300 files, 3,081 Kotlin (about 366k lines); 923 tracked files in `.data/raw-cache` and 813 in `content/drops` appear in searches. Central: 338 files (133 Kotlin). Client: 372 files (189 Java, C++ native).
- Runs work in per-change worktrees under `<repo>/.worktrees/`, up to `agents: 5` at once.
### 2. Reads to orient (24% of fork, 30% of client)
- The brief holds the definition, criteria and findings but no file or symbol pointers.
- `dev.md` sends the dev on to read `tracks/<repo>/track.md` (122 lines for the fork).
- Sessions start from this checkout, so the product repo's own agent doc is not auto-loaded: fork CLAUDE.md is `@AGENTS.md` (471 lines), client has CLAUDE.md and HANDOFF.md, Central has neither at its root. How much of the read count these account for is unmeasured.
### 3. `hd show` is called again after the brief (16% of fork)
- `cmd_show` prints the same text as `brief_text` plus the last 12 events, so a call after spawn mostly repeats the brief. Why fork runs call it 3.7 times is not established. One possibility is refreshing criteria results after a build or gate; the transcripts (`run.transcript` holds the paths) would show it.
### 4. Git is run to learn the dev ref's state (12% of fork)
- The brief reports build, gate and ship results but not the dev ref's position against base or the clone's status.
### 5. The measure itself is missing
- `hook.py` `end()` stores only `context_tokens` in `run.usage_json`; `kpi.py` has no first-edit row.
- docs/V9-BRIEF.md:193 reports medians (server-dev 15, client-dev 14.5, harness-dev 11) by a different method than the audit above, so the two are not comparable.

## Constraints any solution meets
- `decide.py` takes no subprocess and no clock; changes follow CLAUDE.md's iteration protocol (fewer concepts, a test per requirement touched, docs state current truth).
- The host is memory-constrained: the WSL VM freezes under Windows memory overcommit (HANDOFF ask 21), with up to five runs alive at once.
- Privacy: code and data stay local.

## KPIs
All per run, reported per track (fork, client, central, harness), as median and mean, by one method: the first Edit or Write, or a Bash write (`sed -i`, `cat >`, heredoc to a file, `.write(`, `tee`), as in V9-BRIEF.
1. Calls before the first edit, total.
2. Calls before the first edit by category: search, read, `hd show`, git, brief and rules (the table above).
3. Tokens consumed before the first edit (the cost of the crawl; context tokens at that point).
4. Share of first-edit calls that are search or read.
5. Runs that call `hd show` after their brief, and how often.
Record these when a run ends, so the baseline above is reproducible and later changes are judged on the same numbers. No target is set here.

## Already on main since the note's facts (bf37ab9, h-route-failures-brief-reruns): check before building on it
- `act.brief_text` adds "your branch against <base>" (`git diff --stat base...tip`) and "the previous run" (its end and record, with the failures after it). This touches issue 4 and gives a re-run file pointers; a first run still gets no map (issue 1).
- `kpi.py` now has "median calls before the first edit": dev code runs, computed at `hd kpi` time from each transcript, counting Edit/Write/NotebookEdit only (no Bash writes), one median over all tracks. It does not meet KPIs 1-5: no per-track split, no categories, no tokens at the first edit, no `hd show` count, not recorded at run end, and not the V9-BRIEF method. Replace it with the recorded measure, so there is one method.
