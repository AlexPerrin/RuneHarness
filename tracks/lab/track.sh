#!/usr/bin/env bash
# The PR lab's script (docs/ARCHITECTURE.md §11): recipe | gate. AlexPerrin/pr-lab is a repo of our own that is its own
# upstream: the loop's GitHub paths run against it. Started by the pass with HD_ROOT, HD_SLUG, HD_KEY, HD_TREE, HD_TCOMMIT,
# HD_REPO set; its last act records the job (`hd gate`).
set -euo pipefail
HD_ROOT=${HD_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}; hd="python3 $HD_ROOT/harness/hd.py"
verb=${1:?usage: track.sh recipe|gate <slug> [key]}; slug=${2:-}; key=${3:-}
case "$verb" in
  recipe) printf 'gate lab-1\n' ;;
  gate) dir="$HD_ROOT/state/$slug/cand-${HD_TREE:0:12}"   # the candidate's files, extracted once
        $hd own dir "$dir" "job:gate:$key"   # released once the job ends
        [ -d "$dir" ] || { rm -rf "$dir.tmp"; mkdir -p "$dir.tmp"; git -C "$HD_REPO" archive "$HD_TCOMMIT" | tar -x -C "$dir.tmp"; mv "$dir.tmp" "$dir"; }
        exec $hd gate "$slug" "$key" "$dir" ;;
  *) echo "track.sh: unknown verb $verb" >&2; exit 64 ;;
esac
