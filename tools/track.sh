#!/usr/bin/env bash
# tools/track.sh <verb> <slug>: the harness track's scripts (docs/ARCHITECTURE.md). Env from hd: SLUG HEAD T TCOMMIT.
set -euo pipefail
verb=$1; slug=$2; shift 2

build()         { :; }   # R8: a throwaway worktree at TCOMMIT; the test suite; writes state/<slug>/build.json (build = gate here).
gate()          { :; }   # the contract's check rows (tests, dry-run); writes state/<slug>/gate.json.
check_dry_run() { :; }   # `hd tick --dry-run` at TCOMMIT plans no upstream action main's pass does not.
ship()          { :; }   # fast-forward main to TCOMMIT in ~/osrs-harness (refused while its tree is dirty: an alert) and push.

case $verb in build|gate|check-dry-run|ship) ${verb//-/_} "$@" ;; *) echo "verbs: build gate check-dry-run ship" >&2; exit 2 ;; esac
