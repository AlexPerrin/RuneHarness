#!/usr/bin/env bash
# tools/track.sh <verb> <slug> [TCOMMIT]: the harness track (docs/ARCHITECTURE.md). Env from hd: SLUG HEAD T TCOMMIT
# EVIDENCE BUILD HD_ROOT TOOLS (<repo path>:<tools branch>:<sha>:<owner/repo> per product tools branch the change carries). Verbs: build
# (the build copy at T) | gate (every check and gate row of the contract, BUILD = the copy) | check-tests | check-dry-run |
# check-docs (each on $BUILD) | check-tools (each carried head's tests, in its repo's build copy) | ship (unless a branch moved
# past its gated base: fast-forward and push each carried tools branch, then the live checkout's branch to T, push; one ship at
# a time, under state/ship.lock; a T already on the live branch moves nothing). hd runs
# gate and ship for the harness batch, slug ship-harness, NAMES its changes.
set -euo pipefail
verb=$1; slug=${2:-}; tc=${3:-${TCOMMIT:-}}
repo=$(cd "$(dirname "$0")/.." && pwd)   # the harness code; root: where state and evidence live
root=${HD_ROOT:-$repo}
state=$root/state/$slug
record() {  # record <ok> <name> <<< detail  → state/<slug>/<name>.json {T, ok, detail}
  mkdir -p "$state"
  python3 -c 'import json,sys;print(json.dumps({"T":sys.argv[1],"ok":sys.argv[2]=="true","detail":sys.stdin.read()[-2000:]}))' "${T:-}" "$1" > "$state/.$2.$$.tmp"
  mv -f "$state/.$2.$$.tmp" "$state/$2.json"   # whole or not at all: hd reads it at any moment
}
copy() {  # the build copy at TCOMMIT, never the tree anyone commits from
  wt=$repo/.worktrees/$slug-build
  if [ -d "$wt" ]; then git -C "$wt" checkout -q --detach "$tc"; else git -C "$repo" worktree add -q --detach "$wt" "$tc"; fi
  echo "$wt"
}

build() {  # the loop's verb alone: a dev's run would overwrite the loop's record and move the copy a running gate reads
  [ -n "${T:-}" ] && [ -n "${TCOMMIT:-}" ] || { echo "refused: build is the loop's (T and TCOMMIT unset); a harness dev runs the unit tests in its worktree" >&2; exit 2; }
  wt=$(copy); record true build <<< "build copy $wt at $tc"
}
summary() { grep -E '^(Ran |OK|FAILED|(FAIL|ERROR): [^ ]+ \()|refused: '; }   # unittest's verdict, each failing test and a refusal, whatever the tests print
check_tests() { (cd "$BUILD" && env -u ROWS python3 -m unittest discover -s tests 2>&1 | summary); }
gate() {  # every check: and gate: row of the contracts of NAMES (the batch's changes, comma-separated) at T, from the build copy; kept by T as gate-<T>
  wt=$(copy); mkdir -p "$state"; ROWS=$(mktemp -d "$state/.rows.XXXXXX"); export ROWS; trap 'rm -rf "$ROWS"' EXIT   # each member runs its rows; a check of the tree alone runs once (rowmemo)
  if out=$(HD_ROOT=$root python3 "$repo/hd.py" rows "${NAMES:-$slug}" "$tc" "$wt" 2>&1); then record true gate <<< "$out"; else record false gate <<< "$out"; fi
  cp "$state/gate.json" "$state/.gate.$$.tmp"; mv -f "$state/.gate.$$.tmp" "$state/gate-$T.json"
}
check_dry_run() {  # the candidate plans no public act main's pass does not (an upstream step changed by mistake acts within a minute); both read GitHub from the passes' cache alone (HD_GH=cache), never the network
  export HD_GH=cache
  mine=$(python3 "$repo/hd.py" tick --dry-run | grep -E 'carrying upstream|publishing v' | sort || true)
  theirs=$(HD_ROOT=$root python3 "$BUILD/hd.py" tick --dry-run | grep -E 'carrying upstream|publishing v' | sort || true)
  mine=$( (echo "$mine"; python3 "$repo/hd.py" tick --dry-run | grep -E 'carrying upstream|publishing v' || true) | sort -u)  # main's plan before and after: a state change between the two runs (an approval) is no extra act
  extra=$(comm -13 <(echo "$mine") <(echo "$theirs")); [ -z "$extra" ] || { echo "plans a public act main does not: $extra"; exit 1; }
}
check_docs() {  # every requirement has its test class and its acceptance row; the source docs one fact per line
  [ "$(grep -cE '^class R[1-8]\(' "$BUILD/tests/test_hd.py")" = 8 ] && [ "$(grep -c '"id": "R' "$BUILD/docs/ACCEPTANCE.json")" = 8 ] || { echo "a requirement lacks its test class or acceptance row"; exit 1; }
  (cd "$BUILD" && python3 tools/docfmt.py --check docs/PROBLEM.md docs/PRD.md docs/ARCHITECTURE.md)   # one fact per line: siblings merge (R8)
}
check_tools() {  # each carried tools head: a fast-forward of its branch, its tools/**/test_*.py pass at that head
  for t in ${TOOLS:-}; do
    IFS=: read -r path branch sha name <<< "$t"; wt=$path/.worktrees/$SLUG-build
    git -C "$path" merge-base --is-ancestor "$branch" "$sha" || { echo "$path: $sha is not a fast-forward of $branch"; exit 1; }
    if [ -d "$wt" ]; then git -C "$wt" checkout -q --detach "$sha"; else git -C "$path" worktree add -q --detach "$wt" "$sha"; fi
    tests=$(git -C "$wt" ls-files tools | grep -E '(^|/)test_[^/]*\.py$' || true)
    [ -z "$tests" ] || (cd "$wt" && python3 -m unittest $tests 2>&1 | summary) || { echo "$path at ${sha:0:9}: tests fail"; exit 1; }
  done
}
ship() {  # the live branch moves only by fast-forward to T (R8: the pass never merges into someone's edits; definitions under harness/ are not edits T touches)
  mkdir -p "$root/state"; exec 9> "$root/state/ship.lock"; flock 9   # one ship at a time on the live checkout, whatever started it
  if git -C "$repo" merge-base --is-ancestor "$tc" HEAD; then   # T already landed (a ship before this one): nothing to move
    rm -f "$state/proc-ship.json" "$state"/gate-*.json; echo "${tc:0:9} is already on the live branch"; exit 0
  fi
  [ -z "$(git -C "$repo" status --porcelain -- . ':!harness')" ] || { echo "refused: $repo has uncommitted edits"; exit 1; }
  moved=$(git -C "$repo" merge-base --is-ancestor HEAD "$tc" || echo "live branch")
  for t in ${TOOLS:-}; do  # nothing moves unless every branch fast-forwards to its gated head
    IFS=: read -r path branch sha name <<< "$t"; wt=$path/.worktrees/${branch##*/}
    [ -z "$(git -C "$wt" status --porcelain --untracked-files=no)" ] || { echo "refused: $wt has uncommitted edits"; exit 1; }
    git -C "$wt" merge-base --is-ancestor HEAD "$sha" || moved="$moved $branch"
  done
  if [ -n "$moved" ]; then  # a branch moved past the gated base: the next pass rebases a carried head onto its moved branch (a conflict: the dev) and re-gates
    rm -f "$state/proc-ship.json"; echo "$moved moved past T's base; the next pass merges the batch again"; exit 0
  fi
  for t in ${TOOLS:-}; do  # each carried tools branch first, in its worktree, pushed to its repo's own remote (the fork's is never origin: upstream)
    IFS=: read -r path branch sha name <<< "$t"; wt=$path/.worktrees/${branch##*/}
    remote=$(git -C "$path" remote -v | awk -v n="$name" '!r && $3 == "(push)" && $2 ~ ("[:/]" n "(\\.git)?$") { print $1; r = 1 }')
    [ -n "$remote" ] || { echo "refused: $path has no remote for $name"; exit 1; }
    git -C "$wt" merge -q --ff-only "$sha"; git -C "$path" push -q "$remote" "$branch"; echo "$branch at ${sha:0:9}, pushed to $remote"
  done
  git -C "$repo" merge -q --ff-only "$tc"; git -C "$repo" push -q origin HEAD; echo "$(git -C "$repo" branch --show-current) at $(git -C "$repo" rev-parse --short HEAD)"
  rm -f "$state"/gate-*.json   # every kept gate was of a tree on the old base
}

rowmemo() {  # within one gate (ROWS), a check whose input is the tree and the batch's TOOLS alone gives every member its first result
  [ -n "${ROWS:-}" ] || { "$1"; return; }
  [ -f "$ROWS/$1.rc" ] || { rc=0; ( "$1" ) > "$ROWS/$1.out" 2>&1 || rc=$?; echo "$rc" > "$ROWS/$1.rc"; }
  cat "$ROWS/$1.out"; return "$(cat "$ROWS/$1.rc")"
}

case $verb in build|gate|ship) "$verb" ;; check-tests|check-dry-run|check-docs|check-tools) rowmemo "${verb//-/_}" ;; *) echo "verbs: build gate check-tests check-dry-run check-docs check-tools ship" >&2; exit 2 ;; esac
