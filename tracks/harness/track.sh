#!/usr/bin/env bash
# The harness track's script (docs/ARCHITECTURE.md §9): recipe | test | gate | ship. Started by the pass in a systemd
# scope with HD_ROOT, HD_DB, HD_SLUG, HD_KEY, HD_TREE, HD_TCOMMIT, HD_HEAD, HD_BASE, HD_REPO, HD_CLONE, HD_LOG, HD_RC
# set; its last act records the job (`hd gate`, `hd job`).
set -euo pipefail
HD_ROOT=${HD_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
hd="python3 $HD_ROOT/harness/hd.py"
verb=${1:?usage: track.sh recipe|test|gate|ship <slug> [key]}; slug=${2:-}; key=${3:-}

unpack() {  # $1 tcommit $2 tree → the candidate's files under state/<slug>/cand-<tree12>, extracted once
  local dir="$HD_ROOT/state/$slug/cand-${2:0:12}"
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir.tmp"; git -C "$HD_REPO" archive "$1" | tar -x -C "$dir.tmp"; mv "$dir.tmp" "$dir"
  fi
  echo "$dir"
}

case "$verb" in
  recipe) printf 'gate harness-1\nship harness-1\n' ;;   # bump a version when that verb's output changes (ARCHITECTURE §6)
  test) exec python3 -m unittest discover -s tests ;;
  gate) exec $hd gate "$slug" "$key" "$(unpack "$HD_TCOMMIT" "$HD_TREE")" ;;
  ship)
    # The candidate on the live tip: the gated one, or a new merge gated here; then the live branch fast-forwards.
    if ! read -r tree tcommit < <($hd candidate "$slug"); then
      $hd job ship "$key" fail "the head no longer merges with ${HD_BASE#refs/heads/}"; exit 1
    fi
    if [ "$tree" != "$HD_TREE" ]; then
      HD_TREE=$tree HD_TCOMMIT=$tcommit $hd gate "$slug" "$tree:harness-1" "$(unpack "$tcommit" "$tree")" \
        || { $hd job ship "$key" fail "gate failed on the merge with the live tip"; exit 1; }
    fi
    git -C "$HD_ROOT" merge --ff-only -q "$tcommit"
    git -C "$HD_ROOT" push -q origin "HEAD:${HD_BASE#refs/heads/}"
    $hd job ship "$key" ok "$(git -C "$HD_ROOT" rev-parse --short "$tcommit")" ;;
  *) echo "track.sh: unknown verb $verb" >&2; exit 64 ;;
esac
