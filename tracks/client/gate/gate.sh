#!/usr/bin/env bash
# tracks/client/gate/gate.sh <verb> <slug> [arg]: the client track's gate and every verb a scripted criterion runs but check-log
# (track.sh dispatches them here); the build is build/build.sh's, sourced. The pass keys a gate by the tree and the recipe
# version. Env from hd: SLUG HEAD T (the tree) TCOMMIT BASE CLONE EVIDENCE BUILD HD_ROOT HD_KEY. Verbs:
#   gate TCOMMIT      the build, then every scripted criterion of the change from the build copy (`hd gate`), which records the job
#   check-evidence | check-probe | check-netqa | check-state-doc   the seed criteria
. "$(dirname "$0")/../build/build.sh"   # verb slug arg self(tools/build) repo root state ev dev copy atomic record tree build check_log
gate() {  # the build (cached by T), then `hd gate`: every scripted criterion in the build copy; a criterion exiting 75 (its source down) leaves no result and the pass starts the gate again
  tc=${TCOMMIT:-$arg}; T=${T:-$(git -C "$repo" rev-parse "$tc^{tree}")}
  HD_KEY= "$self/build.sh" build "$slug" "$tc" || { $hd job gate "$T:client-1" fail "build failed at ${T:0:12}: $ev/repack-$T.log"; return 1; }
  git -C "$copy" reset -q --hard "$tc"
  BUILD=$copy exec $hd gate "$slug" "$T:client-1" "$copy"
}
noapk='^(docs|protmap|tools/protmap)/'   # paths the APK never contains
untouched() {  # the change's own diff (merge base with BASE to HEAD) touches no APK input: no build or mobile run measures it
  [ -n "${BASE:-}" ] && [ -n "${HEAD:-}" ] || return 1; d=$(git -C "$repo" diff --name-only "$BASE...$HEAD") || return 1
  [ -z "$d" ] || ! grep -qvE "$noapk" <<< "$d" || return 1; echo "no APK input changed since ${BASE:0:12}"; }
check_evidence() { untouched && return 0; for p in "$ev"/*logcat*.txt "$ev"/*.dump.* "$ev"/*devtools*.json; do [ -e "$p" ] && { echo "mobile evidence: $(basename "$p")"; return 0; }; done; echo "no logcat extract, dump or devtools JSON in $ev"; return 1; }
check_probe() { untouched && return 0
  f=$ev/api-probe.tsv; [ -f "$f" ] || { echo "no api-probe.tsv in $ev"; return 1; }
  b=$(grep -oE '^# build: \S*-g[0-9a-f]+' "$f" | grep -oE '[0-9a-f]+$' || true); [ -n "$b" ] || { echo "$f has no '# build:' line"; return 1; }
  case $HEAD in "$b"*) echo "probe built at $HEAD"; return 0 ;; esac
  d=$(git -C "$repo" diff --name-only "$b" "$HEAD" | grep -v '^docs/' || true); [ -z "$d" ] && echo "probe at $b, only docs differ" || { echo "probe built at $b, not $HEAD: rerun it"; return 1; }
}
check_netqa() { grep -qE '^network: true' "$root/harness/changes/$slug.md" 2>/dev/null || { echo "no network QA needed"; return 0; }
  grep -lq 'PASS' "$ev"/netqa*.md 2>/dev/null && echo "network QA PASS" || { echo "network: true and no netqa*.md with PASS in $ev"; return 1; }; }
check_state_doc() { untouched && return 0; r=$(grep -oE '^# result: pass [0-9]+ / [0-9]+ = [0-9.]+%' "$ev/api-probe.tsv" 2>/dev/null | grep -oE '[0-9.]+%$' || true); [ -n "$r" ] || { echo "no probe result"; return 1; }; grep -q "$r" "${BUILD:-.}/docs/client-state.md" && echo "client-state.md carries the probe's $r" || { echo "docs/client-state.md does not carry the probe's result $r"; return 1; }; }

case $verb in gate|check-evidence|check-probe|check-netqa|check-state-doc) "${verb//-/_}" ;;
  *) echo "verbs: gate check-evidence check-probe check-netqa check-state-doc" >&2; exit 2 ;; esac
