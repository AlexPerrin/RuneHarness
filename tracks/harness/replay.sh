#!/usr/bin/env bash
# The replay criterion (docs/ARCHITECTURE.md §9), run by the gate with cwd = the candidate's files: the candidate's
# pass over a snapshot of the live ledger plans what the live pass plans, or evidence/<slug>/replay.md explains why not.
set -euo pipefail
snap=$(mktemp -d)/hd.db
python3 -c 'import sqlite3, sys; sqlite3.connect(sys.argv[1]).backup(sqlite3.connect(sys.argv[2]))' "$HD_DB" "$snap"
live=$(python3 "$HD_ROOT/harness/hd.py" tick --dry-run --offline --db "$snap")
cand=$(python3 harness/hd.py tick --dry-run --offline --db "$snap")
if diff <(echo "$live") <(echo "$cand"); then echo "replay: the candidate plans what the live pass plans"; exit 0; fi
if [ -s "$HD_ROOT/evidence/$HD_SLUG/replay.md" ]; then echo "replay: differs as explained in evidence/$HD_SLUG/replay.md"; exit 0; fi
echo "replay: the candidate plans differently and evidence/$HD_SLUG/replay.md does not explain it"; exit 1
