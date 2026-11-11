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
[ -f "$root/harness/changes/$slug.md" ] || [ -f "$root/harness/goals/$slug.md" ] || grep -qxF -- "${slug%-*}" <(sed -n 's#^feature: *#pr-#p' "$root"/harness/changes/*.md 2>/dev/null | tr / -) || case $slug in live|staging) ;; *) echo "no change or goal \"$slug\": tracks/fork/track.sh <verb> <slug> [arg]" >&2; exit 2 ;; esac
state=$root/state/$slug; mkdir -p "$state"
dev=$repo/.worktrees/$slug; copy=$repo/.worktrees/$slug-build
atomic() { cat > "$1.$$.tmp"; if [ -s "$1.$$.tmp" ]; then mv -f "$1.$$.tmp" "$1"; else rm -f "$1.$$.tmp"; return 1; fi; }   # a state record whole or not at all: hd reads it at any moment
record() { python3 -c 'import json,os,sys;print(json.dumps({"T":sys.argv[1],"ok":sys.argv[2]=="true","detail":sys.stdin.read()[-2000:],"head":os.environ.get("HEAD","")}))' "$T" "$1" | atomic "$state/$2.json"; }
cause() { local w; w=$(grep -m1 -A2 '^\* What went wrong:' "$1" | tail -n +2 | paste -sd' '); echo "${w:-$(tail -c 300 "$1" | tail -1)}"; }   # what a failed log names: gradle's failing task and reason, never its timing line (alert 88: one cause read as two)
v=2   # the version of what a build keeps (or:<T>'s label hd.build, the store's s<v>-<ck>): bumped when one kept may be wrong (2: packed with no other tree's incremental state)
size=(--cpus=4 --memory=5g)   # one build or check container's share of the host; hd.yaml builds (HD_BUILDS) bounds how many run at once
slot() {  # slot <command...>: the command under one of the HD_BUILDS build slots (the first free, else waiting on the first)
  local n=${HD_BUILDS:-3} i fd rc; mkdir -p ~/.cache/hd
  for i in $(seq 1 "$n") 1; do exec {fd}> ~/.cache/hd/build.$i.lock   # machine-wide, as the gradle-<i> volume it guards: every checkout takes the same slots
    if [ "$i" = 1 ] && [ -n "${tried:-}" ]; then flock "$fd"; else flock -n "$fd" || { exec {fd}>&-; tried=1; continue; }; fi
    "${@//@SLOT@/$i}"; rc=$?; exec {fd}>&-; return $rc
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
  [ -d "$dev" ] || { git -C "$repo" worktree add -q "$dev" -B "dev/$slug" "$(git -C "$repo" rev-parse -q --verify "fork/dev/$slug" || echo origin/main)"; $hd own worktree "$dev" "$slug"; }
  idx=$(git -C "$dev" rev-parse --git-path snapshot-index); rm -f "$idx"   # from HEAD: add -A alone drops tracked files under ignored paths
  GIT_INDEX_FILE=$idx git -C "$dev" read-tree HEAD && GIT_INDEX_FILE=$idx git -C "$dev" add -A . && snap=$(git -C "$dev" commit-tree "$(GIT_INDEX_FILE=$idx git -C "$dev" write-tree)" -p HEAD -m snapshot)
  while IFS='=' read -r name val; do [ -n "${!name:-}" ] || export "$name=$val"; done < <($hd candidate "$slug" --composite)   # the libraries the candidate builds in (on staging: the test server's), unless the dev names one
  read -r T tc < <($hd candidate "$slug" --head "$snap"); T=$T$(composite_suffix)
}
composite_suffix() {  # the image of a composite build is its own: _c<central tree12>, _f<filestore tree12> (decide.built; docker refuses '+' in a tag)
  local p c r; for r in CENTRAL FILESTORE; do [ -n "${!r:-}" ] || continue; IFS=: read -r p c <<< "${!r}"; printf '_%s%s' "${r:0:1}" "$(git -C "$p" rev-parse "$c^{tree}" | cut -c1-12)" | tr CF cf; done; echo
}
filestore() {  # the change's FileStore head, published by its own track to a Maven directory (Gradle 9 cannot configure its build, nor include it):
  # every dev.or2 module it holds resolves from there alone (build/filestore.init.gradle); fdir (that directory) and fvols for build and tests
  fdir= fvols=(); [ -n "${FILESTORE:-}" ] || return 0
  IFS=: read -r fpath fcommit <<< "$FILESTORE"; fdir=$fpath/.worktrees/$slug-filestore/.m2
  TCOMMIT=$fcommit HD_REPO=$fpath HD_KEY= bash "$self/../../filestore/track.sh" publish "$slug" "$fcommit"
  fvols=(-v "$fdir:$fdir:ro" -v "$self/filestore.init.gradle:/filestore.init.gradle:ro")
}
central() {  # the change's Central dependencies, merged by hd, built in (gate/central.init.gradle): cdir and cvols for build and tests
  cdir= cvols=(); [ -n "${CENTRAL:-}" ] || return 0
  IFS=: read -r cpath ccommit <<< "$CENTRAL"; cdir=$cpath/.worktrees/$slug-central
  if [ -d "$cdir" ]; then git -C "$cdir" reset -q --hard "$ccommit" && git -C "$cdir" clean -fdq; else git -C "$cpath" worktree add -q --detach "$cdir" "$ccommit"; fi; $hd own worktree "$cdir" "$slug"
  cvols=(-v "$cpath/.git:$cpath/.git:ro" -v "$cdir:$cdir" -v "$self/central.init.gradle:/central.init.gradle:ro")
}
build() { tree; { flock 9; build_locked; } 9> "$state/build.lock"; }   # one build of a slug at a time (the pass's and its dev's): the second waits, then reuses a cached or:<T>; the lock ends with the build, never held by the gate or its rows after it
build_locked() {
  if [ "$(docker image inspect -f '{{index .Config.Labels "hd.build"}}' "or:$T" 2>/dev/null)" = "$v" ]; then $hd own image "or:$T" "$slug@$T"; echo "cached or:$T"; record true build <<< "cached"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "cached or:$T"; return; fi   # cached: or:<T> of this version (an older one's is built again)
  n=1; while [ -e "$state/build-$T-$n.log" ]; do n=$((n + 1)); done; log=$state/build-$T-$n.log   # each attempt its own log (under the lock)
  if [ -d "$copy" ]; then git -C "$copy" reset -q --hard "$tc" && git -C "$copy" clean -fdq; else git -C "$repo" worktree add -q --detach "$copy" "$tc"; fi
  $hd own worktree "$copy" "$slug"   # every artifact a row of its owner: hd releases it once no owner is live (docs/ARCHITECTURE.md §6)
  cp "$copy/game.example.yml" "$copy/game.yml"   # every build renders T's config, as release-server.yml: game.yml is ignored, so clean keeps an older tree's
  # the one harness setting beyond game.example.yml: embedded Central's http on 9090, the port upstream's test server serves (update-test-server.yml HTTP_PORT; the code's default is 8080)
  grep -qE '^[[:space:]]+http-port:' "$copy/game.yml" || sed -i '/^central:/a\  http-port: 9090' "$copy/game.yml"
  if grep -q '\.m2-rsprot' "$copy/settings.gradle.kts"; then  # local/android pins an rsprot published only to the clone's .m2-rsprot
    [ -d "$repo/.m2-rsprot" ] || { echo "no $repo/.m2-rsprot: the tree pins a locally published rsprot" | tee "$log" | record false build; echo "build failed: $log"; return 1; }
    cp -a "$repo/.m2-rsprot" "$copy/"
  fi
  ck=$(git -C "$copy" ls-tree -r "$tc" | grep -E 'or-cache/|/pack/|gamevals|raw-cache' | sha1sum | cut -c1-12)   # the cache's inputs
  gk=$(git -C "$repo" rev-parse -q --verify "$tc:game.example.yml" | cut -c1-12 || true)   # the game data's: the revision (game.example.yml), as the gate's release asset
  cs=or-cache-store-${gk:-none}; $hd own volume "$cs" "$slug@$T"   # one store per revision, kept while a head builds from it
  central; filestore >> "$log" 2>&1 || { record false build < "$log"; echo "build failed: $log"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "FileStore publish"; return 1; }
  vols=(-v "gradle-@SLOT@:/gradle" -v "$cs:/store" "${cvols[@]}" "${fvols[@]}")   # one Gradle home per build slot: shared across slugs, one writer each (Gradle's locks do not reach across containers)
  local i; for i in $(seq 1 "${HD_BUILDS:-3}"); do docker run --rm -v "gradle-$i:/gradle" eclipse-temurin:21 chown 1000:1000 /gradle; done
  docker run --rm -v "$cs:/store" eclipse-temurin:21 chown 1000:1000 /store   # docker makes a new volume root's; the build runs as 1000
  gd=$state/.game-data-$gk.tgz; rm -f "$gd"   # the revision missing from the store: the gate's release asset of it (seeded from an image), so a build needs openrs2 only for a revision no image holds yet
  if [ -n "$gk" ] && ! docker run --rm -v "$cs:/store" eclipse-temurin:21 sh -c "[ -d /store/s$v-$ck ] || [ -d /store/g-$gk ]" >/dev/null 2>&1; then
    R=$(git -C "$repo" remote get-url fork 2>/dev/null | sed -E 's#.*github.com[:/]##; s#\.git$##' || true)
    [ -z "$R" ] || gh release download game-data -R "$R" -p "game-data-$gk.tar.gz" -O "$gd" >/dev/null 2>&1 || rm -f "$gd"
  fi
  [ -s "$gd" ] && vols+=(-v "$gd:/game-data.tgz:ro")
  owner=${OWNER:-$slug}; [ -z "${HD_KEY:-}" ] || owner=job:${HD_KIND:-build}:$HD_KEY   # the job's container goes with the job, a kill included; a dev's with its change
  $hd own container "build-$slug" "$owner"
  docker rm -f "build-$slug" >/dev/null 2>&1 || true   # a killed build's container, still running: the slug's build lock is held, it is no one else's
  trap 'docker rm -f "build-$slug" >/dev/null 2>&1 || true' EXIT; trap 'exit 143' TERM INT   # a stopped build's container ends with it
  box "$log" --rm --name "build-$slug" -u 1000:1000 -e HOME=/gradle/home -e GRADLE_USER_HOME=/gradle -e CK="$ck" -e V="$v" -e GK="$gk" -e CDIR="$cdir" -e FDIR="$fdir" \
    "${vols[@]}" -v "$repo/.git:$repo/.git:ro" -v "$copy:$copy" -w "$copy" \
    eclipse-temurin:21 bash -c '
      set -e; mkdir -p "$HOME"; g="./gradlew --console=plain --build-cache --no-configuration-cache --max-workers=4 -Dorg.gradle.jvmargs=-Xmx1536m${CDIR:+ --init-script /central.init.gradle}${FDIR:+ --init-script /filestore.init.gradle}"
      s=/store/s$V-$CK d=/store/g-$GK   # s: every output of the cache step (api/generated is compiled, the gamevals are read at boot); d: the game data of the revision
      if [ -d $s ]; then cp -a $s/. .; else
        rm -f .data/cache/incremental_*   # or-cache packs incrementally: state the copy kept from another tree skips a type whose toml is unchanged though an id it resolves moved
        [ -z "$GK" ] || [ -d $d ] || [ ! -s /game-data.tgz ] || { rm -rf $d.tmp && mkdir -p $d.tmp/.data && tar -xzf /game-data.tgz -C $d.tmp/.data && mv $d.tmp $d; }   # the asset: the revision stored, never openrs2
        if [ -n "$GK" ] && [ -d $d ]; then cp -a $d/. . && rm -f .data/cache/incremental_*   # the revision downloaded once: every tree repacks it, as CI on a cache hit
          $g :or-cache:buildCache   # freshCache past its download (its FRESH_INSTALL builds the cache next)
        else
          $g :or-cache:freshCache
          [ -z "$GK" ] || { rm -rf $d.tmp && mkdir -p $d.tmp && cp -a --parents .data/cache .data/gamevals-binary/gamevals.dat .data/gamevals-binary/gamevals_generated.dat $d.tmp/ && mv $d.tmp $d; }   # whole or not at all
        fi
        $g :or-cache:mergePluginGamevals   # release-server.yml: freshCache, then mergePluginGamevals, then shadowJar
        rm -rf $s.tmp && mkdir -p $s.tmp && cp -a --parents .data/cache .data/gamevals .data/gamevals-binary api/generated $s.tmp/ && mv $s.tmp $s
      fi
      $g :server:app:shadowJar' || { record false build < "$log"; echo "build failed: $log"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "$(cause "$log")"; return 1; }
  trap - EXIT TERM INT   # past its container: a gate sourcing this never removes a later build's
  rm -f "$gd"
  st=$copy/.image; rm -rf "$st"; mkdir -p "$st/.data"   # release-server.yml's bundle: server.jar, game.yml, .data/ without raw-cache; no key or database (up and deploy give their own)
  cp "$copy/server/app/build/libs/server.jar" "$copy/game.yml" "$st/"
  tar -C "$copy/.data" --exclude=./raw-cache --exclude=./client.key --exclude=./game.key --exclude=./postgres -c . | tar -C "$st/.data" -x
  $hd own image "or:$T" "$slug@$T"
  hosted "$log" docker build -q --label hd.build=$v -f "$self/Dockerfile" -t "or:$T" "$st" || { rm -rf "$st"; record false build < "$log"; echo "build failed: $log"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" fail "docker build"; return 1; }
  rm -rf "$st"   # the context is the image's now
  [ -n "$(docker ps -q -f name=^build-)" ] || docker builder prune -f >/dev/null 2>&1 || true   # the last build ended: its build cache goes with it
  record true build < "$log"; echo "built or:$T"; [ -z "${HD_KEY:-}" ] || $hd job build "$HD_KEY" ok "or:$T"
}
[ "${BASH_SOURCE[0]}" = "$0" ] || return 0   # sourced by gate.sh: its functions alone
case $verb in build) build ;; tree) tree; echo "$tc $T" ;;
  *) echo "verbs: build tree" >&2; exit 2 ;; esac
