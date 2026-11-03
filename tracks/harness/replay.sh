#!/usr/bin/env bash
# The replay criterion (docs/ARCHITECTURE.md §9), run by the gate with cwd = the candidate's files: the candidate's pass
# over a snapshot of the live ledger plans what its base's pass plans (the base: the candidate's merge base with the live
# branch, so only the change's own effect shows), or evidence/<slug>/replay.md explains the difference.
set -euo pipefail
work=$(mktemp -d); snap=$work/hd.db; base=$work/base
python3 -c 'import sqlite3, sys; sqlite3.connect(sys.argv[1]).backup(sqlite3.connect(sys.argv[2]))' "$HD_DB" "$snap"
mb=$(git -C "$HD_REPO" merge-base "$HD_TCOMMIT" "$HD_BASE")
mkdir -p "$base"; git -C "$HD_REPO" archive "$mb" | tar -x -C "$base"
defs=$HD_ROOT/harness   # the same definitions on both sides: the live ones
was=$(cd "$base" && python3 harness/hd.py tick --dry-run --offline --db "$snap" --defs "$defs")
cand=$(python3 harness/hd.py tick --dry-run --offline --db "$snap" --defs "$defs")
if diff <(echo "$was") <(echo "$cand"); then echo "replay: the candidate plans what its base ${mb:0:7} plans"; exit 0; fi
if [ -s "$HD_ROOT/evidence/$HD_SLUG/replay.md" ]; then echo "replay: differs from its base ${mb:0:7} as explained in evidence/$HD_SLUG/replay.md"; exit 0; fi
echo "replay: the candidate plans differently from its base ${mb:0:7} and evidence/$HD_SLUG/replay.md does not explain it"; exit 1
