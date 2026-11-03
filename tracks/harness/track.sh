#!/usr/bin/env bash
# The harness track's script (docs/V9-PROPOSAL.md §3.9): test | gate | ship | recipe. Blocks on facts, logs its
# steps with `hd step`, records its result with `hd artefact`. Skeleton: every verb is unimplemented.
set -euo pipefail
verb=${1:?usage: track.sh test|gate|ship|recipe <slug> [key]}
case "$verb" in
  recipe) echo "harness-1" ;;                         # bump when the output of build/gate/ship changes (§3.6 key())
  test|gate|ship) echo "track.sh $verb: not implemented" >&2; exit 64 ;;
  *) echo "track.sh: unknown verb $verb" >&2; exit 64 ;;
esac
