#!/usr/bin/env bash
# tracks/central/track.sh <verb> <slug> [key]: the Central track (docs/ARCHITECTURE.md §11). Central is a library the game
# server runs in-process (game.yml `central.same-instance`), so a Central head reaches the test server only inside a server
# image built with it (the fork's build with CENTRAL=<clone>:<commit>). Env from hd: HD_ROOT HD_KEY HD_TREE HD_TCOMMIT HD_HEAD
# HD_REPO HD_BUILDS and the short names SLUG HEAD T TCOMMIT BASE CLONE BUILD EVIDENCE. Verbs:
#   recipe            one version per verb the pass keys a job by (build, gate)
#   build <slug> [key]  the candidate compiled (gradle assemble) in the build copy <repo>/.worktrees/<slug>-build, in a container
#   test              every module's tests (gradle test) in the build copy (a criterion: cwd the build copy)
#   gate <slug> <key> the build copy at the candidate, then `hd gate`: every scripted criterion
#   up <slug> [N]     a test server built from the fork's base with this head as its Central, N desktops (the fork's up); a head
#                     whose embedded Central reads OPENRUNE_JAV_CONFIG_URL_TEMPLATE serves jav_config itself (CENTRAL_JAV: no http-<slug>)
#   down | log        the fork's, for that server
set -euo pipefail
verb=$1; slug=${2:-${SLUG:-}}; arg=${3:-}
self=$(cd "$(dirname "$0")" && pwd)
root=${HD_ROOT:-$(cd "$self/../.." && pwd)}; hd="python3 $root/harness/hd.py"
repo=${HD_REPO:-$HOME/src/OpenRune-Central-Server}
fork=${FORK_REPO:-$HOME/src/OpenRune-Server}
case "$verb" in recipe) printf 'build central-1\ngate central-1\n'; exit 0 ;; esac
[ -f "$root/harness/changes/$slug.md" ] || { echo "no change \"$slug\": tracks/central/track.sh <verb> <slug> [key]" >&2; exit 2; }
state=$root/state/$slug; mkdir -p "$state"
copy=$repo/.worktrees/$slug-build
size=(--cpus=4 --memory=5g)
slot() {  # slot <command...>: the command under one of the HD_BUILDS build slots (the first free, else waiting on the first)
  local n=${HD_BUILDS:-3} i fd rc tried=; mkdir -p "$root/state"
  for i in $(seq 1 "$n") 1; do exec {fd}> "$root/state/build.$i.lock"
    if [ "$i" = 1 ] && [ -n "$tried" ]; then flock "$fd"; else flock -n "$fd" || { exec {fd}>&-; tried=1; continue; }; fi
    "${@//@SLOT@/$i}"; rc=$?; exec {fd}>&-; return $rc
  done
}
gradle() {  # gradle <tasks...>: in the build copy, in a container, the one Gradle home every slug shares (content-addressed)
  local i; for i in $(seq 1 "${HD_BUILDS:-3}"); do docker run --rm -v "gradle-$i:/gradle" eclipse-temurin:21 chown 1000:1000 /gradle; done
  slot docker run --rm --init "${size[@]}" --name "central-$slug-$$" -u 1000:1000 -e HOME=/gradle/home -e GRADLE_USER_HOME=/gradle \
    -v "gradle-@SLOT@:/gradle" -v "$repo/.git:$repo/.git:ro" -v "$copy:$copy" -w "$copy" \
    eclipse-temurin:21 bash ./gradlew --console=plain --no-daemon --max-workers=4 -Dorg.gradle.jvmargs=-Xmx1536m "$@"
}
checkout() {  # the build copy at the candidate commit
  local tc=${TCOMMIT:-${arg:-dev/$slug}}  # no key before the first candidate: the dev ref
  if [ -d "$copy" ]; then git -C "$copy" reset -q --hard "$tc" && git -C "$copy" clean -fdq; else git -C "$repo" worktree add -q --detach "$copy" "$tc"; fi
  $hd own worktree "$copy" "$slug"   # released with the change (docs/ARCHITECTURE.md §6)
}
case "$verb" in
  build) checkout; if gradle assemble -x test; then [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "assembled ${T:-}"; else [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "gradle assemble"; exit 1; fi ;;
  test) copy=${BUILD:-$copy}; gradle test ;;
  gate) checkout; BUILD=$copy exec $hd gate "$slug" "${T:-$HD_TREE}:central-1" "$copy" ;;
  up) tc=$(git -C "$fork" rev-parse origin/main); h=${HEAD:-$(git -C "$repo" rev-parse "dev/$slug")}
      ! git -C "$repo" grep -q OPENRUNE_JAV_CONFIG_URL_TEMPLATE "$h" -- central-app/src/main || export CENTRAL_JAV=1   # a head whose embedded Central reads a local jav_config serves the desktops itself
      CENTRAL="$repo:$h" TCOMMIT=$tc HD_KEY= HD_REPO=$fork bash "$self/../fork/track.sh" build "$slug" "$tc"
      HD_REPO=$fork exec bash "$self/../fork/track.sh" up "$slug" "$arg" ;;
  down|log) HD_REPO=$fork exec bash "$self/../fork/track.sh" "$verb" "$slug" "$arg" ;;
  *) echo "verbs: recipe build test gate up down log" >&2; exit 2 ;;
esac
