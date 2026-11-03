# ISSUES

The open ledger of the v8 build. A quick fix lands at once and is not logged. What lands here is a root cause in the
design or a rewrite too large for the run, and the measurements of v7 that were never confirmed; newest first.

## Open
- **v9 (the user, 2026-11-02: "We will branch the major revision (sqlite) as v9 ... We will action the migration
  seperately"): state moves into one SQLite store, and commitments are recorded, not re-derived.** Two root causes
  behind most v8 bugs found in monitor sweeps 66-89 (evidence/monitor/):
  1. Untyped state in many JSON/markdown files with no schema, migration or transaction: answers stored without their
     question; contract rows classified by text prefix; legacy records lacking new fields (answer-5 without `holds:`,
     proc records without exit status); strikes counted from a result file's presence or mtime; fact ids from the
     wall clock; two writers emitting two `ended` events for one run.
  2. Decisions re-derived from live facts each pass instead of recorded once: an approval compared against texts
     recomputed from the live PR, so a carry stopped after its push can never resume (goblin-367, 22:08Z); gates
     keyed on tools helpers re-run CI on unchanged trees; every pass re-reads all git/gh facts (15-44 s ticks), and
     a per-pass cache then served stale refs.
  Shape: one SQLite file (WAL; the hook, tick and runs write concurrently) holds everything now under `state/` and
  `events.jsonl`: runs, facts/events, contract rows, asks and answers (with their question), approvals (the exact
  texts and steps they cover), carry step logs (resume from the log), gate/ship records and strikes, a cross-pass
  fact cache keyed on the refs read. Definitions (`harness/changes/`), evidence and PR texts stay files (git history,
  agents edit them as text). Start with the approval + carry log (the goblin-367 P0), then move the rest; a major
  revision, gated by the user at deployment, on branch v9.
- **The compose file was not validated from this session**: the v7 guard refuses `docker compose config`; the first
  `ship` validates it.
- **The sidecar's data and image come from v7's tools branch** (`osrs-rsps-test:241`, `sidecar/data`): the server
  files the test server needs beyond the fork's tree are not yet on `local/harness`.
- **Unconfirmed v7 measurements** (the monitor): the 131-module recompile after adding a pack module; why every
  SubagentStop hook was cancelled; that the binary RSProx recordings hold clan packets; the fixed-mode login
  coordinates as the cause of the 10-31 login stall.
