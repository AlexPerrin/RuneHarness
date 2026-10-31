#!/usr/bin/env bash
# tools/track.sh <verb> <slug> [TCOMMIT]: the harness track (docs/ARCHITECTURE.md). Env from hd: SLUG HEAD T TCOMMIT
# EVIDENCE HD_ROOT. Verbs: build (the suite at T in a throwaway worktree; build = gate here) | gate (every check and
# gate row of the contract) | check-dry-run | check-docs | ship (fast-forward main to T, push).
set -euo pipefail
verb=$1; slug=${2:-}; tc=${3:-${TCOMMIT:-}}
repo=$(cd "$(dirname "$0")/.." && pwd)   # the harness code; root: where state and evidence live
root=${HD_ROOT:-$repo}
state=$root/state/$slug
record() {  # record <ok> <name> <<< detail  → state/<slug>/<name>.json {T, ok, detail}
  mkdir -p "$state"
  python3 -c 'import json,sys;print(json.dumps({"T":sys.argv[1],"ok":sys.argv[2]=="true","detail":sys.stdin.read()[-2000:]}))' "${T:-}" "$1" > "$state/$2.json"
}
copy() {  # the build copy at TCOMMIT, never the tree anyone commits from
  wt=$repo/.worktrees/$slug-build
  if [ -d "$wt" ]; then git -C "$wt" checkout -q --detach "$tc"; else git -C "$repo" worktree add -q --detach "$wt" "$tc"; fi
  echo "$wt"
}

build() {
  wt=$(copy)
  if out=$(cd "$wt" && python3 -m unittest discover -s tests 2>&1); then record true build <<< "$out"; else record false build <<< "$out"; fi
}
gate() {  # every check: and gate: row of the contract at T, from the build copy (hd rows applies the hand-over's rules)
  wt=$(copy)
  if out=$(HD_ROOT=$root python3 "$repo/hd.py" rows "$slug" "$tc" "$wt" 2>&1); then record true gate <<< "$out"; else record false gate <<< "$out"; fi
}
check_dry_run() {  # the candidate plans no public act main's pass does not (an upstream step changed by mistake acts within a minute)
  mine=$(python3 "$repo/hd.py" tick --dry-run | grep -E 'shipping upstream|publishing v' | sort || true)
  theirs=$(HD_ROOT=$root python3 hd.py tick --dry-run | grep -E 'shipping upstream|publishing v' | sort || true)
  extra=$(comm -13 <(echo "$mine") <(echo "$theirs")); [ -z "$extra" ] || { echo "plans a public act main does not: $extra"; exit 1; }
}
check_docs() {  # every requirement has its test class and its acceptance row
  [ "$(grep -cE '^class R[1-8]\(' tests/test_hd.py)" = 8 ] && [ "$(grep -c '"id": "R' docs/ACCEPTANCE.json)" = 8 ] || { echo "a requirement lacks its test class or acceptance row"; exit 1; }
}
ship() {  # main moves only by fast-forward to T; a dirty tree is refused (R8: the pass never merges into someone's edits)
  [ -z "$(git -C "$repo" status --porcelain)" ] || { echo "refused: $repo has uncommitted edits"; exit 1; }
  git -C "$repo" merge -q --ff-only "$tc" && git -C "$repo" push -q origin main && echo "main at $(git -C "$repo" rev-parse --short HEAD)"
}

case $verb in build|gate|check-dry-run|check-docs|ship) "${verb//-/_}" ;; *) echo "verbs: build gate check-dry-run check-docs ship" >&2; exit 2 ;; esac
