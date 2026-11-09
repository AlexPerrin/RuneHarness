#!/usr/bin/env bash
# tracks/client/build/build.sh <verb> <slug> [arg]: the client track's build, the code a build runs and nothing else (track.sh
# dispatches build, check-log and tree here; gate/gate.sh sources it). The pass keys a build by the tree and the recipe version.
# Env from hd: SLUG HEAD T (the tree) TCOMMIT BASE CLONE EVIDENCE BUILD HD_ROOT HD_KEY. Verbs:
#   build [TCOMMIT]   the devtools plugin (host/plugins/devtools/build.sh on the copy's own re/devtools, a shared clone of the
#                     main one, re/devtools-build and re/host/plugins-extra), host build, ninja and the repack with OPENRUNE=1
#                     LOCAL_AUTH=1 in the build copy, SERVER $server (the mobile's own loopback: up's adb reverse maps it to the live Central's http), the login modulus the live stack's key pair's (state/live/key/client.key of
#                     osrs-harness, the key every live image carries); the APK is kept only when its repack log passes check-log; cached by T
#                     while it carries that modulus and endpoint (evidence/<slug>/<T>.apk, <T>.devtools.jar, the jar boot pushes, and <T>.devtools-desktop.jar, its
#                     classes before dexing, the jar the server track's desktops load from the build of slug live)
#   check-log         the newest repack log patched every telemetry line, the RSA modulus, jav_config and appauth (a seed row)
#   tree              prints TCOMMIT and T (a dev: the working copy snapshotted)
set -euo pipefail
verb=$1; slug=${2:-${SLUG:-}}; arg=${3:-}   # a criterion passes no slug: hd exports SLUG
self=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)   # tracks/client/build (also when gate.sh sources it)
root=${HD_ROOT:-$(cd "$self/../../.." && pwd)}; hd="python3 $root/harness/hd.py"
repo=${HD_REPO:-$HOME/osrs-plugins-reverse}   # the main checkout (re/ lives there)
[ -f "$root/harness/changes/$slug.md" ] || [ -f "$root/harness/goals/$slug.md" ] || case $slug in live) ;; *) echo "no change or goal \"$slug\": tracks/client/track.sh <verb> <slug> [arg]" >&2; exit 2 ;; esac
state=$root/state/$slug; mkdir -p "$state"
ev=${EVIDENCE:-$root/evidence/$slug}; mkdir -p "$ev"
dev=$repo/.worktrees/$slug; copy=$repo/.worktrees/$slug-build
ndk=${ANDROID_NDK:-$HOME/Android/Sdk/ndk/android-ndk-r27d}
atomic() { cat > "$1.$$.tmp"; if [ -s "$1.$$.tmp" ]; then mv -f "$1.$$.tmp" "$1"; else rm -f "$1.$$.tmp"; return 1; fi; }   # a state record whole or not at all: hd reads it at any moment
pair=$root/state/live/key/client.key   # the live stack's key pair: every APK's modulus, the key ship puts in every live image
modulus() { sed -n 's/^Modulus: //p' "$pair" 2>/dev/null; }
server=127.0.0.1:8443   # the APK's jav_config endpoint: the port Central's jav_config names its sign-in on (the fork track's central_jav)
carries() { unzip -p "$1" lib/arm64-v8a/liblibs.hal.system.osclient.so 2>/dev/null | grep -aF "$2" >/dev/null; }   # carries APK MODULUS: the APK's game library holds that login modulus (no -q: its early exit SIGPIPEs unzip, a pipefail failure)
record() { python3 -c 'import json,sys;print(json.dumps({"T":sys.argv[1],"ok":sys.argv[2]=="true","detail":sys.stdin.read()[-2000:]}))' "$T" "$1" | atomic "$state/$2.json"; }

tree() {
  tc=${TCOMMIT:-$arg}   # the pass's TCOMMIT (its argument is the job key), or a dev's argument
  if [ -n "$tc" ]; then T=${T:-$(git -C "$repo" rev-parse "$tc^{tree}")}; return; fi
  [ -d "$dev" ] || git -C "$repo" worktree add -q "$dev" -B "client/$slug" "$(git -C "$repo" rev-parse -q --verify "origin/client/$slug" || echo origin/HEAD)"
  idx=$(git -C "$dev" rev-parse --git-path snapshot-index); rm -f "$idx"
  GIT_INDEX_FILE=$idx git -C "$dev" add -A . && snap=$(git -C "$dev" commit-tree "$(GIT_INDEX_FILE=$idx git -C "$dev" write-tree)" -p HEAD -m snapshot)
  read -r T tc < <($hd candidate "$slug" --head "$snap")
}
build() {
  tree
  m=$(modulus); [ ${#m} = 256 ] || { record false build <<< "no live key pair in $pair"; echo "build: no live key pair in $pair"; return 1; }
  if [ -f "$ev/$T.apk" ] && [ -f "$ev/$T.devtools.jar" ] && [ -f "$ev/$T.devtools-desktop.jar" ] && carries "$ev/$T.apk" "$m" && carries "$ev/$T.apk" "http://$server/jav_config.ws"; then echo "cached $ev/$T.apk"; record true build <<< "cached"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "cached"; return; fi
  if [ -d "$copy" ]; then git -C "$copy" reset -q --hard "$tc" && git -C "$copy" clean -fdq; else git -C "$repo" worktree add -q --detach "$copy" "$tc"; fi
  [ ! -f "$root/harness/changes/$slug.md" ] || python3 "$root/harness/hd.py" own worktree "$copy" "$slug" >/dev/null 2>&1 || true   # a change's build copy; a goal's and the live build's stay
  mkdir -p "$copy/re/host"; for f in base.apk split_config.arm64_v8a.apk; do ln -sfn "$repo/$f" "$copy/$f"; done  # the ignored store APKs
  for e in "$repo"/re/*; do n=$(basename "$e"); case $n in host|build|out|apk|devtools|devtools-build) ;; *) ln -sfn "$e" "$copy/re/$n" ;; esac; done
  for n in apk devtools devtools-build; do [ ! -L "$copy/re/$n" ] || rm "$copy/re/$n"; done   # a copy made before linked them; re/apk is the repack's decoded tree, one per copy
  [ -d "$copy/re/devtools/.git" ] || git clone -q --shared "$repo/re/devtools" "$copy/re/devtools"   # its own checkout; the objects stay shared
  mkdir -p "$copy/re/devtools-build"; ln -sfn "$repo/re/devtools-build/lombok-1.18.30.jar" "$copy/re/devtools-build/lombok-1.18.30.jar"
  [ -d "$copy/re/host/plugins-extra" ] || cp -a "$repo/re/host/plugins-extra" "$copy/re/host/"
  [ -f "$copy/re/build/build.ninja" ] || cmake -S "$copy/native" -B "$copy/re/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_TOOLCHAIN_FILE="$ndk/build/cmake/android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 >/dev/null
  log=$ev/repack-$T.log
  (cd "$copy" && host/plugins/devtools/build.sh && host/build.sh && ninja -C re/build && MODULUS=$m SERVER=$server OPENRUNE=1 LOCAL_AUTH=1 tools/repack.sh) > "$log" 2>&1 || { record false build < "$log"; echo "build failed: $log"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "$(tail -c 300 "$log" | tail -1)"; return 1; }
  EVIDENCE=$ev check_log >/dev/null || { record false build <<< "repack log fails the privacy check: $log"; rm -f "$copy/re/out/osrs-runelite.apk"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "the repack log fails the privacy check"; return 1; }
  cp "$copy/re/host/plugins-extra/devtools.jar" "$ev/$T.devtools.jar"; cp "$copy/re/devtools-build/devtools.jar" "$ev/$T.devtools-desktop.jar"; cp "$copy/re/out/osrs-runelite.apk" "$ev/$T.apk"; record true build < "$log"; echo "built $ev/$T.apk"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "$ev/$T.apk"
}
check_log() {
  l=$(ls -t "$ev"/repack*.log 2>/dev/null | head -1 || true); [ -n "$l" ] || { echo "no repack log in $ev"; return 1; }
  [ "$(grep -c '^telemetry:' "$l")" = 7 ] && grep -q '^patched RSA modulus' "$l" && grep -q '^patched /jav_config\.ws' "$l" && grep -qE '^patched \S*/net/openid/appauth/' "$l" \
    && echo "repack log: 7 telemetry lines, RSA modulus, jav_config and appauth patched" || { echo "$l: the APK talks to Jagex (OPENRUNE=1 LOCAL_AUTH=1 tools/repack.sh)"; return 1; }
}

[ "${BASH_SOURCE[0]}" = "$0" ] || return 0   # sourced by gate.sh: its functions alone
case $verb in build|check-log) "${verb//-/_}" ;; tree) tree; echo "$tc $T" ;;
  *) echo "verbs: build check-log tree" >&2; exit 2 ;; esac
