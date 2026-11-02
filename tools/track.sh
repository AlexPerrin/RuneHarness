#!/usr/bin/env bash
# tools/track.sh <verb> <slug> [TCOMMIT]: the harness track (docs/ARCHITECTURE.md). Env from hd: SLUG HEAD T TCOMMIT
# EVIDENCE BUILD HD_ROOT G (the gate key) TOOLS (<repo path>:<tools branch>:<sha>:<owner/repo> per product tools branch the change carries). Verbs: build
# (the build copy at T) | test <slug> [unittest args] (a dev's run of the suite in its worktree, as check-tests runs it) | gate (every check and gate row of the contract, BUILD = the copy) | check-tests | check-dry-run |
# check-docs (each on $BUILD) | check-tools (each carried head's tests, in its repo's build copy) | ship (unless a branch moved
# past its gated base: fast-forward and push each carried tools branch, then the live checkout's branch to T under the state lock, push; one ship at
# a time, under state/ship.lock; a T already on the live branch moves only the carried tools branches not yet holding their heads). hd runs
# gate and ship for the harness batch, slug ship-harness, NAMES its changes.
set -euo pipefail
verb=$1; slug=${2:-${SLUG:-}}; tc=${3:-${TCOMMIT:-}}
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
unit='import atexit, os, shutil, signal, sys, tempfile, unittest; d = tempfile.tempdir = os.environ["TMPDIR"] = tempfile.mkdtemp(prefix=f"hd-run-{os.getpid()}-"); atexit.register(shutil.rmtree, d, True); signal.signal(signal.SIGTERM, lambda *a: (shutil.rmtree(d, True), os._exit(143))); unittest.main(module=None, argv=["unittest"] + sys.argv[1:], testRunner=unittest.TextTestRunner(stream=os.fdopen(3, "w")))'   # python3 -m unittest whose runner alone writes fd 3; every temp dir of its tests (and their processes) under one root it removes at its end and at its stop (SIGTERM: a stopped gate leaves none)
summary() { python3 -c '
import os, re, sys
t = sys.stdin.read(); body, _, end = t.partition("\n" + "-" * 70 + "\nRan ")
if len(sys.argv) > 1:   # the whole report, outliving the temp root of the runner and any filter on this output
    f = sys.argv[1]; os.makedirs(os.path.dirname(f), exist_ok=True); open(f + ".tmp", "w").write(t); os.replace(f + ".tmp", f)
failed = []
for b in re.split(r"^=+\n", body, flags=re.M)[1:]:   # each failing test: its name and its traceback tail (the assertion), so the gate record says why
    head, _, tb = b.partition("-" * 70 + "\n")
    if re.match(r"(FAIL|ERROR): ", head):
        print(head.strip()); print("\n".join(tb.strip().splitlines()[-6:])); failed.append(head.strip().split(": ", 1)[1])
if failed and len(sys.argv) > 1: print("failed: " + ", ".join(failed) + "; whole report: " + sys.argv[1])   # last but the verdict: the tail of a record keeps it
for l in ("Ran " + end if end else t).splitlines():
    if re.match(r"(Ran |OK|FAILED)", l) or "refused: " in l: print(l)
' "$@"; }   # unittest's verdict, each failing test with its traceback tail, and a refusal; read from the runner's fd 3 alone, never what the tests print (to /dev/null)
suite() {  # suite [unittest args]: the suite of the tree in the cwd (all of tests/ by default) through the runner, its whole report kept in $state/tests.txt
  [ $# -gt 0 ] || set -- discover -s tests
  env -u ROWS python3 -c "$unit" "$@" 3>&1 >/dev/null 2>&1 | summary "$state/tests.txt"
}
check_tests() { [ -z "${ROWS:-}" ] || state=${ROWS%/*}; (cd "$BUILD" && suite); }   # in a gate the report is the gate's own (state/<batch>/tests.txt, beside ROWS), never a member's that its dev's test overwrites
gate() {  # every check: and gate: row of the contracts of NAMES (the batch's changes, comma-separated) at T, from the build copy; recorded under the gate key G, kept as gate-<G>
  wt=$(copy); export ROWS=$state/.rows; rm -rf "$ROWS"; mkdir -p "$ROWS"   # each member runs its rows; a check of the tree alone runs once (rowmemo); the change's one memo dir, emptied by each gate: a killed gate leaves no temp dir
  out=$(HD_ROOT=$root TOOLS_ROOT=$wt LIVE=$repo python3 "$repo/hd.py" rows "${NAMES:-$slug}" "$tc" "$wt" 2>&1) && rc=0 || rc=$?   # the rows are T's own scripts (the files its key names); main's plan is LIVE's
  [ $rc != 75 ] || { echo "$out"; exit 75; }   # a row held (its source down): no result, hd starts the gate again
  T=${G:-${T:-}}; record "$([ $rc = 0 ] && echo true || echo false)" gate <<< "$out"
  cp "$state/gate.json" "$state/.gate.$$.tmp"; mv -f "$state/.gate.$$.tmp" "$state/gate-$T.json"
}
check_dry_run() {  # the candidate plans no public act main's pass does not (an upstream step changed by mistake acts within a minute); a dry-run reads GitHub from the passes' cache and git from the local refs alone (HD_OFFLINE), never the network
  live=${LIVE:-$repo}; mine=$(python3 "$live/hd.py" tick --dry-run | grep -E 'carrying upstream|publishing v' | sort || true)
  plan=$(HD_ROOT=$root python3 "$BUILD/hd.py" tick --dry-run 2>&1) && ! grep -q '^Traceback' <<< "$plan" || { echo "the candidate's pass fails:"; tail -c 2000 <<< "$plan"; exit 1; }   # a crash plans nothing: it must fail, never pass as no extra act
  theirs=$(grep -E 'carrying upstream|publishing v' <<< "$plan" | sort || true)
  mine=$( (echo "$mine"; python3 "$live/hd.py" tick --dry-run | grep -E 'carrying upstream|publishing v' || true) | sort -u)  # main's plan before and after: a state change between the two runs (an approval) is no extra act
  extra=$(comm -13 <(echo "$mine") <(echo "$theirs")); [ -z "$extra" ] || { echo "plans a public act main does not: $extra"; exit 1; }
}
check_docs() {  # every requirement has its test class and its acceptance row; the source docs one fact per line
  [ "$(grep -cE '^class R[1-8]\(' "$BUILD/tests/test_hd.py")" = 8 ] && [ "$(grep -c '"id": "R' "$BUILD/docs/ACCEPTANCE.json")" = 8 ] || { echo "a requirement lacks its test class or acceptance row"; exit 1; }
  (cd "$BUILD" && python3 tools/docfmt.py --check docs/PROBLEM.md docs/PRD.md docs/ARCHITECTURE.md)   # one fact per line: siblings merge (R8)
}
check_tools() {  # each carried tools head: a fast-forward of its branch, its tools/**/test_*.py pass at that head (with HOME and PATH alone: the gate's T, TCOMMIT and SLUG are not the product tests')
  for t in ${TOOLS:-}; do
    IFS=: read -r path branch sha name <<< "$t"; wt=$path/.worktrees/$SLUG-build
    git -C "$path" merge-base --is-ancestor "$branch" "$sha" || { echo "$path: $sha is not a fast-forward of $branch"; exit 1; }
    if [ -d "$wt" ]; then git -C "$wt" checkout -q --detach "$sha"; else git -C "$path" worktree add -q --detach "$wt" "$sha"; fi
    tests=$(git -C "$wt" ls-files tools | grep -E '(^|/)test_[^/]*\.py$' || true)
    [ -z "$tests" ] || (cd "$wt" && env -i HOME="$HOME" PATH="$PATH" python3 -c "$unit" $tests 3>&1 >/dev/null 2>&1 | summary) || { echo "$path at ${sha:0:9}: tests fail"; exit 1; }
  done
}
ship() {  # the live branch moves only by fast-forward to T (R8: the pass never merges into someone's edits; definitions under harness/ are not edits T touches)
  mkdir -p "$root/state"; exec 9> "$root/state/ship.lock"; flock 9   # one ship at a time on the live checkout, whatever started it
  landed=; moved= todo=   # T already on the live branch (a ship before this one) moves no live branch, but each carried tools head still lands
  if git -C "$repo" merge-base --is-ancestor "$tc" HEAD; then landed=1; else
    [ -z "$(git -C "$repo" status --porcelain -- . ':!harness')" ] || { echo "refused: $repo has uncommitted edits"; exit 1; }
    moved=$(git -C "$repo" merge-base --is-ancestor HEAD "$tc" || echo "live branch"); fi
  for t in ${TOOLS:-}; do  # nothing moves unless every branch fast-forwards to its gated head; a branch holding its head already is done
    IFS=: read -r path branch sha name <<< "$t"; wt=$path/.worktrees/${branch##*/}
    git -C "$wt" merge-base --is-ancestor "$sha" HEAD && [ -z "$(git -C "$path" rev-list -1 "$branch" --not --remotes 2>/dev/null)" ] && continue
    [ -z "$(git -C "$wt" status --porcelain --untracked-files=no)" ] || { echo "refused: $wt has uncommitted edits"; exit 1; }
    git -C "$wt" merge-base --is-ancestor HEAD "$sha" || moved="$moved $branch"; todo="$todo $t"
  done
  if [ -n "$landed" ] && [ -z "$todo" ] && [ -z "$moved" ]; then
    rm -f "$state/proc-ship.json"; kept; echo "${tc:0:9} is already on the live branch, every carried tools head on its branch"; exit 0
  fi
  if [ -n "$moved" ]; then  # a branch moved past the gated base: the next pass rebases a carried head onto its moved branch (a conflict: the dev) and re-gates
    rm -f "$state/proc-ship.json"; echo "$moved moved past T's base; the next pass merges the batch again"; exit 0
  fi
  for t in $todo; do  # each carried tools branch first, in its worktree, pushed to its repo's own remote (the fork's is never origin: upstream)
    IFS=: read -r path branch sha name <<< "$t"; wt=$path/.worktrees/${branch##*/}
    remote=$(git -C "$path" remote -v | awk -v n="$name" '!r && $3 == "(push)" && $2 ~ ("[:/]" n "(\\.git)?$") { print $1; r = 1 }')
    [ -n "$remote" ] || { echo "refused: $path has no remote for $name"; exit 1; }
    git -C "$wt" merge -q --ff-only "$sha"; git -C "$path" push -q "$remote" "$branch"; echo "$branch at ${sha:0:9}, pushed to $remote"
  done
  [ -n "$landed" ] || flock "$root/state/.lock" git -C "$repo" merge -q --ff-only "$tc"; git -C "$repo" push -q origin HEAD; echo "$(git -C "$repo" branch --show-current) at $(git -C "$repo" rev-parse --short HEAD)"
  kept
}
kept() { local f; for f in "$state"/gate-*.json; do [ "$f" = "$state/gate-${G:-}.json" ] || rm -f "$f"; done; }   # every kept gate but the shipped tree's (G) was of a tree on the old base

rowmemo() {  # within one gate (ROWS), a check whose input is the tree and the batch's TOOLS alone gives every member its first result
  [ -n "${ROWS:-}" ] || { "$1"; return; }
  [ -f "$ROWS/$1.rc" ] || { rc=0; ( "$1" ) > "$ROWS/$1.out" 2>&1 || rc=$?; echo "$rc" > "$ROWS/$1.rc"; }
  cat "$ROWS/$1.out"; return "$(cat "$ROWS/$1.rc")"
}

case $verb in build|gate|ship) "$verb" ;; test) [ -n "$slug" ] || { echo "track.sh test <slug> [unittest args]" >&2; exit 2; }; shift 2; suite "$@" ;; check-tests|check-dry-run|check-docs|check-tools) rowmemo "${verb//-/_}" ;; *) echo "verbs: build gate test check-tests check-dry-run check-docs check-tools ship" >&2; exit 2 ;; esac
