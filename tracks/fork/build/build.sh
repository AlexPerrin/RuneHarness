#!/usr/bin/env bash
# tracks/fork/build/build.sh <verb> <slug> [arg]: the server track's build, the code a build runs and nothing else (track.sh
# dispatches build and tree here; gate/gate.sh sources it). The pass keys a build by the tree and the recipe version. Env from hd:
# SLUG HEAD T (the tree) TCOMMIT BASE CLONE EVIDENCE CENTRAL HD_ROOT HD_KEY HD_BUILDS. Verbs:
#   build [TCOMMIT]   the image or:<T> of the tree T (a dev: the working copy snapshotted, its candidate from `hd candidate`); cached by T;
#                     CENTRAL=<Central clone>:<commit> builds and tests with that Central in place of the published dev.or2 modules
#                     (build/central.init.gradle substitutes each, :central-app included); state/<slug>/build.lock is held by the build alone
#                     each container takes one of hd.yaml's build slots (flock); a step failed for the host's cause (memory, disk, docker) exits 75, no result
#   tree              prints TCOMMIT and T (a dev: the working copy snapshotted)
set -euo pipefail
verb=$1; slug=${2:-${SLUG:-}}; arg=${3:-}   # a criterion passes no slug: hd exports SLUG
self=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)   # tracks/fork/build (also when gate.sh sources it)
root=${HD_ROOT:-$(cd "$self/../../.." && pwd)}; hd="python3 $root/harness/hd.py"
repo=${HD_REPO:-$(dirname "$(git -C "${CLONE:-$HOME/src/OpenRune-Server}" rev-parse --path-format=absolute --git-common-dir)")}   # the main checkout, also when CLONE names a worktree of it (a brief's clone)
[ -f "$root/harness/changes/$slug.md" ] || [ -f "$root/harness/goals/$slug.md" ] || case $slug in live|staging) ;; *) echo "no change or goal \"$slug\": tracks/fork/track.sh <verb> <slug> [arg]" >&2; exit 2 ;; esac
state=$root/state/$slug; mkdir -p "$state"
dev=$repo/.worktrees/$slug; copy=$repo/.worktrees/$slug-build
atomic() { cat > "$1.$$.tmp"; if [ -s "$1.$$.tmp" ]; then mv -f "$1.$$.tmp" "$1"; else rm -f "$1.$$.tmp"; return 1; fi; }   # a state record whole or not at all: hd reads it at any moment
record() { python3 -c 'import json,os,sys;print(json.dumps({"T":sys.argv[1],"ok":sys.argv[2]=="true","detail":sys.stdin.read()[-2000:],"head":os.environ.get("HEAD","")}))' "$T" "$1" | atomic "$state/$2.json"; }
size=(--cpus=4 --memory=5g)   # one build or check container's share of the host; hd.yaml builds (HD_BUILDS) bounds how many run at once
slot() {  # slot <command...>: the command under one of the HD_BUILDS build slots (the first free, else waiting on the first)
  local n=${HD_BUILDS:-3} i fd rc; mkdir -p "$root/state"
  for i in $(seq 1 "$n") 1; do exec {fd}> "$root/state/build.$i.lock"
    if [ "$i" = 1 ] && [ -n "${tried:-}" ]; then flock "$fd"; else flock -n "$fd" || { exec {fd}>&-; tried=1; continue; }; fi
    "$@"; rc=$?; exec {fd}>&-; return $rc
  done
}
fault='cannot allocate memory|no space left on device|Cannot connect to the Docker daemon|error during connect|is already in use by container'   # the host refusing the step (memory, disk, the daemon, a container left by a killed run), never the tree
ooms() { dmesg 2>/dev/null | grep -c '\] Out of memory: Killed process' || true; }   # the host OOM killer's kills so far (a container's own --memory limit logs 'Memory cgroup out of memory')
hosted() {  # hosted <log> <command...>: the command, its output appended to log; failed for the host's cause, not the tree's, it exits 75: no result, the pass runs it again
  local log=$1 n rc=0 why; shift; n=$(ooms); "$@" >> "$log" 2>&1 || rc=$?
  [ $rc != 0 ] || return 0
  why=$(grep -m1 -oiE "$fault" "$log") || { [ "$rc" = 137 ] && [ "$(ooms)" -gt "$n" ] && why="killed by the host's OOM killer"; } || return $rc
  echo "the host's fault, not the tree's ($why): no result"; exit 75
}
box() { local log=$1; shift; hosted "$log" slot docker run --init "${size[@]}" "$@"; }   # box <log> <docker run args>: one container in a build slot; --init: a stop's SIGTERM, proxied by docker run, ends it

tree() {  # TCOMMIT and T: the pass gives them; a dev's build snapshots the working copy and asks hd
  tc=${TCOMMIT:-${arg:-}}   # the pass's TCOMMIT (its argument is the job key), or a dev's argument
  if [ -n "$tc" ]; then git -C "$repo" rev-parse -q --verify "$tc^{commit}" >/dev/null || { echo "$tc is not a commit: TCOMMIT is the commit of T" >&2; exit 2; }; T=${T:-$(git -C "$repo" rev-parse "$tc^{tree}")$(composite_suffix)}; return; fi
  [ -d "$dev" ] || git -C "$repo" worktree add -q "$dev" -B "dev/$slug" "$(git -C "$repo" rev-parse -q --verify "fork/dev/$slug" || echo origin/main)"
  idx=$(git -C "$dev" rev-parse --git-path snapshot-index); rm -f "$idx"   # from HEAD: add -A alone drops tracked files under ignored paths
  GIT_INDEX_FILE=$idx git -C "$dev" read-tree HEAD && GIT_INDEX_FILE=$idx git -C "$dev" add -A . && snap=$(git -C "$dev" commit-tree "$(GIT_INDEX_FILE=$idx git -C "$dev" write-tree)" -p HEAD -m snapshot)
  read -r T tc < <($hd candidate "$slug" --head "$snap"); T=$T$(composite_suffix)
}
composite_suffix() {  # the image of a composite build is its own: _c<central tree12>, _f<filestore tree12> (decide.built; docker refuses '+' in a tag)
  local p c; for v in CENTRAL FILESTORE; do [ -n "${!v:-}" ] || continue; IFS=: read -r p c <<< "${!v}"; printf '_%s%s' "${v:0:1}" "$(git -C "$p" rev-parse "$c^{tree}" | cut -c1-12)" | tr CF cf; done; echo
}
filestore() {  # the change's FileStore dependency, built in (build/filestore.init.gradle): fdir and fvols for build and tests
  fdir= fvols=(); [ -n "${FILESTORE:-}" ] || return 0
  IFS=: read -r fpath fcommit <<< "$FILESTORE"; fdir=$fpath/.worktrees/$slug-filestore
  if [ -d "$fdir" ]; then git -C "$fdir" reset -q --hard "$fcommit" && git -C "$fdir" clean -fdq; else git -C "$fpath" worktree add -q --detach "$fdir" "$fcommit"; fi
  fvols=(-v "$fpath/.git:$fpath/.git:ro" -v "$fdir:$fdir" -v "$self/filestore.init.gradle:/filestore.init.gradle:ro")
}
central() {  # the change's Central dependencies, merged by hd, built in (gate/central.init.gradle): cdir and cvols for build and tests
  cdir= cvols=(); [ -n "${CENTRAL:-}" ] || return 0
  IFS=: read -r cpath ccommit <<< "$CENTRAL"; cdir=$cpath/.worktrees/$slug-central
  if [ -d "$cdir" ]; then git -C "$cdir" reset -q --hard "$ccommit" && git -C "$cdir" clean -fdq; else git -C "$cpath" worktree add -q --detach "$cdir" "$ccommit"; fi
  cvols=(-v "$cpath/.git:$cpath/.git:ro" -v "$cdir:$cdir" -v "$self/central.init.gradle:/central.init.gradle:ro")
}
build() { tree; { flock 9; build_locked; } 9> "$state/build.lock"; }   # one build of a slug at a time (the pass's and its dev's): the second waits, then reuses a cached or:<T>; the lock ends with the build, never held by the gate or its rows after it
build_locked() {
  if docker image inspect "or:$T" >/dev/null 2>&1; then echo "cached or:$T"; record true build <<< "cached"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "cached or:$T"; return; fi
  n=1; while [ -e "$state/build-$T-$n.log" ]; do n=$((n + 1)); done; log=$state/build-$T-$n.log   # each attempt its own log (under the lock)
  if [ -d "$copy" ]; then git -C "$copy" reset -q --hard "$tc" && git -C "$copy" clean -fdq; else git -C "$repo" worktree add -q --detach "$copy" "$tc"; fi
  cp "$copy/game.example.yml" "$copy/game.yml"   # every build renders T's config: game.yml is ignored, so clean keeps an older tree's
  if grep -q '\.m2-rsprot' "$copy/settings.gradle.kts"; then  # local/android pins an rsprot published only to the clone's .m2-rsprot
    [ -d "$repo/.m2-rsprot" ] || { echo "no $repo/.m2-rsprot: the tree pins a locally published rsprot" | tee "$log" | record false build; echo "build failed: $log"; return 1; }
    cp -a "$repo/.m2-rsprot" "$copy/"
  fi
  ck=$(git -C "$copy" ls-tree -r "$tc" | grep -E 'or-cache/|/pack/|gamevals|raw-cache' | sha1sum | cut -c1-12)   # the cache's inputs
  gk=$(git -C "$repo" rev-parse -q --verify "$tc:game.example.yml" | cut -c1-12 || true)   # the game data's: the revision (game.example.yml), as the gate's release asset
  central; filestore; vols=(-v "gradle-$slug:/gradle" -v or-cache-store:/store "${cvols[@]}" "${fvols[@]}")
  docker run --rm "${vols[@]}" eclipse-temurin:21 chown 1000:1000 /gradle /store   # docker makes a new volume root's; the build runs as 1000
  gd=$state/.game-data-$gk.tgz; rm -f "$gd"   # the revision missing from the store: the gate's release asset of it (seeded from an image), so a build needs openrs2 only for a revision no image holds yet
  if [ -n "$gk" ] && ! docker run --rm -v or-cache-store:/store eclipse-temurin:21 sh -c "[ -d /store/s-$ck ] || [ -d /store/g-$gk ]" >/dev/null 2>&1; then
    R=$(git -C "$repo" remote get-url fork 2>/dev/null | sed -E 's#.*github.com[:/]##; s#\.git$##' || true)
    [ -z "$R" ] || gh release download game-data -R "$R" -p "game-data-$gk.tar.gz" -O "$gd" >/dev/null 2>&1 || rm -f "$gd"
  fi
  [ -s "$gd" ] && vols+=(-v "$gd:/game-data.tgz:ro")
  docker rm -f "build-$slug" >/dev/null 2>&1 || true   # a killed build's container, still running: the slug's build lock is held, it is no one else's
  trap 'docker rm -f "build-$slug" >/dev/null 2>&1 || true' EXIT; trap 'exit 143' TERM INT   # a stopped build's container ends with it
  box "$log" --rm --name "build-$slug" -u 1000:1000 -e HOME=/gradle/home -e GRADLE_USER_HOME=/gradle -e CK="$ck" -e GK="$gk" -e CDIR="$cdir" -e FDIR="$fdir" \
    "${vols[@]}" -v "$repo/.git:$repo/.git:ro" -v "$copy:$copy" -w "$copy" \
    eclipse-temurin:21 bash -c '
      set -e; mkdir -p "$HOME"; g="./gradlew --console=plain --build-cache --no-configuration-cache --max-workers=4 -Dorg.gradle.jvmargs=-Xmx1536m${CDIR:+ --init-script /central.init.gradle}${FDIR:+ --init-script /filestore.init.gradle}"
      s=/store/s-$CK d=/store/g-$GK   # s: every output of the cache step (api/generated is compiled, the gamevals are read at boot); d: the game data of the revision
      if [ -d $s ]; then cp -a $s/. .; else
        [ -z "$GK" ] || [ -d $d ] || [ ! -s /game-data.tgz ] || { rm -rf $d.tmp && mkdir -p $d.tmp/.data && tar -xzf /game-data.tgz -C $d.tmp/.data && mv $d.tmp $d; }   # the asset: the revision stored, never openrs2
        if [ -n "$GK" ] && [ -d $d ]; then cp -a $d/. .   # the revision downloaded once: every tree repacks it, as CI on a cache hit
        else
          $g :or-cache:freshCache
          [ -z "$GK" ] || { rm -rf $d.tmp && mkdir -p $d.tmp && cp -a --parents .data/cache .data/gamevals-binary/gamevals.dat .data/gamevals-binary/gamevals_generated.dat $d.tmp/ && mv $d.tmp $d; }   # whole or not at all
        fi
        $g :or-cache:mergePluginGamevals :or-cache:buildCache
        rm -rf $s.tmp && mkdir -p $s.tmp && cp -a --parents .data/cache .data/gamevals .data/gamevals-binary api/generated $s.tmp/ && mv $s.tmp $s
      fi
      $g generateRsa :server:app:installDist -x test' || { record false build < "$log"; echo "build failed: $log"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "$(tail -c 300 "$log" | tail -1)"; return 1; }
  trap - EXIT TERM INT   # past its container: a gate sourcing this never removes a later build's
  rm -f "$gd"
  st=$copy/.image; rm -rf "$st"; mkdir -p "$st/data"
  cp -a "$copy/server/app/build/install/app" "$st/server"; cp "$copy/game.yml" "$st/"
  cp -a "$copy/.data/." "$st/data/"; rm -rf "$st/data/client.key" "$st/data/game.key" "$st/data/postgres"
  hosted "$log" docker build -q -f "$self/Dockerfile" -t "or:$T" "$st" || { record false build < "$log"; echo "build failed: $log"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "docker build"; return 1; }
  record true build < "$log"; echo "built or:$T"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "or:$T"
}
[ "${BASH_SOURCE[0]}" = "$0" ] || return 0   # sourced by gate.sh: its functions alone
case $verb in build) build ;; tree) tree; echo "$tc $T" ;;
  *) echo "verbs: build tree" >&2; exit 2 ;; esac
