#!/usr/bin/env bash
# tracks/fork/gate/gate.sh <verb> <slug> [arg]: the server track's gate and every verb a scripted criterion runs (track.sh dispatches
# them here); the build is build/build.sh's, sourced. The pass keys a gate by the tree, the head's tree and the recipe version (HD_KEY). Env from hd: SLUG HEAD T
# (the tree) TCOMMIT BASE CLONE EVIDENCE CENTRAL HD_ROOT HD_KEY. Verbs:
#   test [MODULE...]  build, then each module's tests (and integration tests, where it applies integration-test-suite) and spotlessCheck on the build copy (no module: those holding a file
#                     the change's tree changes from staging, its candidate's base); log evidence/<slug>/test.log, result state/<slug>/test.json
#   spotless          spotlessCheck alone on those modules at PR_TCOMMIT, the tree CI's Formatting checks (unset or a conflict: TCOMMIT;
#                     no TCOMMIT: the working copy's head on upstream main), no build;
#                     log evidence/<slug>/spotless.log, result state/<slug>/spotless.json
#   gate TCOMMIT      the build, then every scripted criterion of the change from the build copy (`hd gate`), which records the job
#   gate-ci           fork CI and Formatting green on gate/<slug> (blocks until both conclude: one conditional read of the
#                     sha's runs, free while unchanged; a GitHub quota refusal holds until its reset) at a child of the PR's own
#                     candidate PR_TCOMMIT (hd gate: the head and its deps on upstream main, not staging; a conflict fails; unset: TCOMMIT) whose
#                     workflows first move the runner's ephemeral ports above the game port 43594 (an outgoing socket on it
#                     fails the boot's bind), and with CENTRAL build that Central in, as build does (the change's head unchanged)
#                     and whose CI restores the game data from the fork release asset game-data-<game.example.yml blob12>
#                     (seeded once from or:<T>) on an actions/cache miss, never openrs2 (no asset fails that step, the runner's),
#                     unless the head changes the revision (game.example.yml): then neither restores and the CI runs :or-cache:freshCache,
#                     the head's step; every other head packs on the restored revision (its cache inputs': the head's step);
#                     each step is timed alone (the job's timeout-minutes on every step), so a timeout names the step that ran
#                     out; a run failed at a step the head does not touch is re-run once its source answers, and after 3
#                     attempts the row exits 75: held, no result; a run GitHub started no job of is dispatched again
#                     (the head's only when it changes a workflow), held the same after 3 such runs
#   ci-step STEP      the carry's CI wait (hd.py ci_fault) asks of an upstream CI step that failed: exit 0 when STEP reads nothing
#                     the head (HEAD over BASE) changes, once its source answers (gate-ci's own classifier); 1 when it is the head's
. "$(dirname "$0")/../build/build.sh"   # verb slug arg self(tools/build) repo root state dev copy atomic record size hosted box tree central build
projects() { local f d; for f; do d=$(dirname "$f"); while [ "$d" != . ] && [ ! -f "$copy/$d/build.gradle.kts" ]; do d=$(dirname "$d"); done; [ "$d" = . ] || { [ "${d##*/}" = pack ] && d=${d%/pack}/$(basename "${d%/pack}")-pack; echo ":${d//\//:}"; }; done | sort -u; }   # the Gradle projects holding these files: settings.gradle.kts names a pack directory <parent>-pack
projdir() { local d=${1#:}; d=${d//://}; [ "${d##*/}" = "$(basename "$(dirname "$d")")-pack" ] && d=$(dirname "$d")/pack; echo "$d"; }   # a project's directory
tests() { build; gradle_check test "$@"; }
spotless() {  # the check row: spotlessCheck on every module the head changes, so a lint the ratchet sees in a touched file fails the hand-over, not CI; no build (the gate's holds the build lock)
  tree; [ -d "$copy" ] || { git -C "$repo" worktree add -q --detach "$copy" "$tc"; $hd own worktree "$copy" "$slug"; }
  # on the tree CI's Formatting checks: the PR's candidate on upstream main (a dev: its own head), never the merge with staging, whose imports differ
  trap "git -C '$copy' reset -q --hard '$tc'" EXIT   # the build copy back at the gate's tree for the criteria after this one (a trap: errexit holds in gradle_check)
  case ${PR_TCOMMIT:-} in ""|conflict:*) tc=${snap:-$tc} ;; *) tc=$PR_TCOMMIT ;; esac
  gradle_check spotless
}
gradle_check() {  # gradle_check test|spotless [MODULE...]: spotless's JGit cannot open a linked worktree: the container sees the copy's .git as a plain repo of T, its objects borrowed
  local kind=$1; shift; git -C "$copy" reset -q --hard "$tc"; git -C "$copy" clean -fdq   # apart: a failed reset in an && list would not stop the verb
  local mods=("$@") f d g=$state/$kind.git out=${EVIDENCE:-$root/evidence/$slug} mb changed
  if [ ${#mods[@]} = 0 ]; then   # each read on its own line, so one that fails stops the verb instead of reading as no module touched
    mb=$(git -C "$repo" merge-base "$(git -C "$repo" rev-parse -q --verify staging || echo origin/main)" "$tc"); changed=$(git -C "$repo" diff --name-only "$mb" "$tc")
    mapfile -t mods < <(projects $changed)
  fi
  if [ ${#mods[@]} = 0 ]; then [ "$kind" = spotless ] && { echo "no module touched"; record true spotless <<< "no module touched"; return 0; }
    echo "no module touched: tools/track.sh test <slug> MODULE..."; return 2; fi
  echo "modules: ${mods[*]}"
  rm -rf "$g"; git init -q --bare "$g"; git --git-dir="$g" config core.bare false; git --git-dir="$g" config core.worktree "$copy"
  echo "$repo/.git/objects" > "$g/objects/info/alternates"
  git --git-dir="$g" update-ref refs/remotes/origin/main "$(git -C "$repo" rev-parse origin/main)"; git --git-dir="$g" update-ref --no-deref HEAD "$tc"
  git -C "$copy" update-index -q --refresh || true; cp "$(git -C "$copy" rev-parse --absolute-git-dir)/index" "$g/index"
  echo "gitdir: $g" > "$state/$kind.gitfile"; mkdir -p "$out"
  local tasks=(); for d in "${mods[@]}"; do rm -rf "$copy/$(projdir "$d")"/build/test-results/{test,integration}   # the report is this run's
    if [ "$kind" = test ]; then tasks+=("$d:test"); if grep -qs '"integration-test-suite"' "$copy/$(projdir "$d")/build.gradle.kts"; then tasks+=("$d:integration"); fi; fi   # upstream CI runs integration too, where the plugin registers it (a src/integration alone registers nothing)
    tasks+=("$d:spotlessCheck"); done
  local i; for i in $(seq 1 "${HD_BUILDS:-3}"); do docker run --rm -v "gradle-$i:/gradle" eclipse-temurin:21 chown 1000:1000 /gradle; done   # one Gradle home per build slot: a volume docker makes is root's, the run is 1000 (spotless runs on a slug never built)
  : > "$out/$kind.log"; central; filestore; box "$out/$kind.log" --rm --name "$kind-$slug" -u 1000:1000 -e HOME=/gradle/home -e GRADLE_USER_HOME=/gradle -e CDIR="$cdir" -e FDIR="$fdir" \
    -v "gradle-@SLOT@:/gradle" "${cvols[@]}" "${fvols[@]}" -v "$repo/.git:$repo/.git:ro" -v "$g:$g:ro" -v "$copy:$copy" -v "$state/$kind.gitfile:$copy/.git:ro" -w "$copy" \
    eclipse-temurin:21 bash -c './gradlew --console=plain --build-cache --no-configuration-cache --max-workers=4 -Dorg.gradle.jvmargs=-Xmx1536m${CDIR:+ --init-script /central.init.gradle}${FDIR:+ --init-script /filestore.init.gradle} --continue "$@"' _ \
    "${tasks[@]}" && ok=true || ok=false
  for d in "${mods[@]}"; do cat "$copy/$(projdir "$d")"/build/test-results/{test,integration}/*.xml 2>/dev/null | grep -o '<testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' || true; done >> "$out/$kind.log"
  record "$ok" "$kind" < "$out/$kind.log"; grep -E -A1 '^<testsuite|went wrong|violations|FAILED|BUILD' "$out/$kind.log" | grep -v '^--$' || true; [ "$ok" = true ]
}
gate() {  # the build (cached by T), then `hd gate`: every scripted criterion in the build copy; a criterion exiting 75 (its source down) leaves no result and the pass starts the gate again
  tc=${TCOMMIT:-$arg}; OWNER=${HD_KEY:+job:gate:$HD_KEY} HD_KEY= build; git -C "$copy" reset -q --hard "$tc" && git -C "$copy" clean -fdq   # the build records no job under the gate's key
  BUILD=$copy exec $hd gate "$slug" "${HD_KEY:-$T:fork-1}" "$copy"
}
gate_sha() {  # a child of TCOMMIT whose workflows move the ephemeral ports off the game port, and with CENTRAL hold that Central tree at .central/ built in
  set -e   # a command substitution does not inherit it
  idx=$state/gate-ci.index   # the change's own index (gates of other changes run at once), read-tree replaces it: no temp dir a killed gate leaves behind
  GIT_INDEX_FILE=$idx git -C "$repo" read-tree "$TCOMMIT"
  step='      - name: Ephemeral ports above the game port (tools/gate/gate.sh gate-ci)
        run: sysctl net.ipv4.ip_local_port_range; sudo sysctl -w net.ipv4.ip_local_port_range="49152 65535"'
  if [ -n "${CENTRAL:-}" ]; then
    IFS=: read -r cpath ccommit <<< "$CENTRAL"; git -C "$repo" fetch -q "$cpath" "$ccommit"
    GIT_INDEX_FILE=$idx git -C "$repo" read-tree --prefix=.central/ "$ccommit"
    GIT_INDEX_FILE=$idx git -C "$repo" update-index --add --cacheinfo "100644,$(git -C "$repo" hash-object -w "$self/central.init.gradle"),.central.init.gradle"
    step="$step"'
      - name: Central of the gate tree (tools/gate/gate.sh gate-ci)
        run: |
          mv .central "$RUNNER_TEMP/central"; echo "CDIR=$RUNNER_TEMP/central" >> "$GITHUB_ENV"
          mkdir -p "${GRADLE_USER_HOME:-$HOME/.gradle}/init.d"; mv .central.init.gradle "${GRADLE_USER_HOME:-$HOME/.gradle}/init.d/central.gradle"'
  fi
  for f in ci format; do f=.github/workflows/$f.yml
    y=$(git -C "$repo" show "$TCOMMIT:$f" | awk -v step="$step" '{print} /uses: gradle\/actions\/setup-gradle@/{print step; n++} END{exit n!=1}') || { echo "$f: no single setup-gradle step to follow" >&2; return 1; }
    y=$(game_data "$y")
    GIT_INDEX_FILE=$idx git -C "$repo" update-index --cacheinfo "100644,$(printf '%s\n' "$y" | git -C "$repo" hash-object -w --stdin),$f"
  done
  d=$(git -C "$repo" show -s --format=%cI "$TCOMMIT")   # dated as T: the same T and workflows push the same sha, whose green runs answer gate-ci again with no new run
  GIT_AUTHOR_DATE=$d GIT_COMMITTER_DATE=$d git -C "$repo" commit-tree "$(GIT_INDEX_FILE=$idx git -C "$repo" write-tree)" -p "$TCOMMIT" -m "gate: $TCOMMIT${CENTRAL:+ with Central ${ccommit:-}}"
}
gate_ci() {  # pushes T (gate_sha) to gate/<slug>; the newest run of each workflow at that sha concludes green, or the row fails;
  # a run failed at a step the head does not touch is the source's, not the head's: re-run once that source answers; held (exit 75: hd records no result) after 3 attempts
  R=$(git -C "$repo" remote get-url fork | sed -E 's#.*github.com[:/]##; s#\.git$##')
  case ${PR_TCOMMIT:-} in "") ;; conflict:*) echo "the PR's head does not merge with upstream main, $PR_TCOMMIT"; return 1 ;; *) TCOMMIT=$PR_TCOMMIT ;; esac   # the scratch merge: the PR on upstream main, never staging's other heads (G4)
  seed
  sha=$(gate_sha); git -C "$repo" push -q --force fork "$sha:refs/heads/gate/$slug"
  q="repos/$R/actions/runs?branch=gate/$slug&head_sha=$sha&per_page=100" etag= runs= ran= rr=; declare -A zn=()
  while :; do
    read_runs || return 1; ok=0
    for wf in CI Formatting; do
      read -r _ st id att <<< "$(grep -m1 "^$wf " <<< "$runs" || true)"   # newest first
      case $st in success/*) ok=$((ok + 1)) ;;
        failure/completed|cancelled/completed|timed_out/completed|startup_failure/completed) case " $rr " in *" $id.$att "*) continue ;; esac   # its re-run asked for: GitHub has not yet shown it
          f=$(failed_step "$id")
          if ! infra "$f"; then echo "$wf $st at '$f' on gate/$slug at $sha (T $TCOMMIT)"; return 1; fi
          if [ "$f" = "(no job)" ]; then   # GitHub started no job (an outage): a re-run has no failed job to run, a new dispatch does
            [ "${zn[$wf]:-0}" -lt 2 ] || { echo "$wf started no job in 3 runs on gate/$slug at $sha: no result"; exit 75; }
            echo "$wf $st with no job started on gate/$slug at $sha, not the head's: dispatched again"
            if gh workflow run "$wf" -R "$R" --ref "gate/$slug"; then rr="$rr $id.$att"; zn[$wf]=$((${zn[$wf]:-0} + 1)); fi; continue
          fi
          [ "$att" -lt 3 ] || { echo "$wf failed at '$f' in $att attempts on gate/$slug at $sha, a step the head does not touch: no result"; exit 75; }
          echo "$wf failed at '$f', a step the head does not touch: re-run once its source answers"; answers "$f"
          if gh run rerun "$id" --failed -R "$R"; then rr="$rr $id.$att"; fi ;;
        */completed) echo "$wf $st on gate/$slug at $sha (T $TCOMMIT)"; return 1 ;;
        "") case " $ran " in *" $wf "*) ;; *) if gh workflow run "$wf" -R "$R" --ref "gate/$slug"; then ran="$ran $wf"; fi ;; esac ;; esac
    done
    [ $ok = 2 ] && break
    sleep 30   # the next read is conditional: while no run changes GitHub answers 304, which costs no quota
  done; echo "CI and Formatting green at $sha (T $TCOMMIT)"
}
game_data() {  # workflow $1 with a step restoring the game data from the fork release asset game-data-<k> on an actions/cache miss, so the gate never downloads openrs2's cache;
  # and the job's timeout on each step, so a slow download never times out in a step that reads the head (cannon's run 41366859771 timed out in 'Compile and run tests')
  # a head changing the revision runs freshCache: no actions/cache restore, no asset (infra() calls that step the head's); openrs2's revision is no other head's input
  local fresh=; if fresh_input; then fresh=1; fi
  FRESH=$fresh K=$(git -C "$repo" rev-parse -q --verify "$TCOMMIT:game.example.yml" | cut -c1-12 || true) python3 -c '
import os, re, sys
y, k = sys.argv[1], os.environ["K"]
def timed(y):
    m = re.search(r"^    timeout-minutes: (\d+)\n", y, re.M)
    return re.sub(r"^(      - name: .*\n)", rf"\g<1>        timeout-minutes: {m.group(1)}\n", y.replace(m.group(0), "", 1), flags=re.M) if m else y
gen = "      - name: Generate cache and gameval sources\n"
if os.environ["FRESH"]:
    print(timed(y.replace("        id: gamecache\n", "        id: gamecache\n        if: false\n", 1))); sys.exit()
if not k or "id: gamecache" not in y or gen not in y:
    print(timed(y)); sys.exit()
step = ("      - name: Game data of the gate (tools/gate/gate.sh gate-ci)\n        id: gamedata\n        if: steps.gamecache.outputs.cache-hit != \x27true\x27\n"
        "        env:\n          GH_TOKEN: ${{ github.token }}\n"
        f"        run: mkdir -p .data && gh release download game-data -R \"$GITHUB_REPOSITORY\" -p game-data-{k}.tar.gz -O - | tar -xz -C .data\n\n")
y = y.replace(gen, step + gen, 1)
y = y.replace("if: steps.gamecache.outputs.cache-hit != \x27true\x27\n        run: ./gradlew :or-cache:freshCache",
              "if: steps.gamecache.outputs.cache-hit != \x27true\x27 && steps.gamedata.outcome != \x27success\x27\n        run: ./gradlew :or-cache:freshCache")
y = y.replace("if: steps.gamecache.outputs.cache-hit == \x27true\x27\n", "if: steps.gamecache.outputs.cache-hit == \x27true\x27 || steps.gamedata.outcome == \x27success\x27\n")
print(timed(y))' "$1"
}
seed() {  # the fork release asset game-data-<k> (k: game.example.yml's blob, which names the revision and so openrs2's cache id) from the image of T, once per k: CI reads it on an actions/cache miss
  local k a f; k=$(git -C "$repo" rev-parse -q --verify "$TCOMMIT:game.example.yml" | cut -c1-12) && [ -n "$k" ] || return 0; a=game-data-$k.tar.gz; f=$state/$a
  gh release view game-data -R "$R" --json assets -q '.assets[].name' 2>/dev/null | grep -x "$a" >/dev/null && return 0
  [ "$(git -C "$repo" rev-parse -q --verify "${HD_TCOMMIT:-$TCOMMIT}:game.example.yml" | cut -c1-12)" = "$k" ] || { echo "or:${T:-} is built on another game.example.yml than $k: no $a seeded from it"; return 0; }   # staging's revision may differ from the PR's
  docker image inspect "or:${T:-}" >/dev/null 2>&1 || { echo "no or:${T:-} to seed $a from: CI waits on it"; return 0; }
  docker run --rm --entrypoint tar "or:$T" -cz -C /app/.data cache/LIVE gamevals-binary/gamevals.dat gamevals-binary/gamevals_generated.dat > "$f.tmp" || { rm -f "$f.tmp"; echo "seeding $a failed"; return 0; }
  mv -f "$f.tmp" "$f"
  gh release view game-data -R "$R" >/dev/null 2>&1 || gh release create game-data -R "$R" --prerelease --title "game data" --notes "The harness gate's game data, one asset per game.example.yml" || true
  gh release upload game-data "$f" -R "$R" || echo "seeding $a failed or another gate's upload stands"; rm -f "$f"
}
failed_step() {  # the first step of run $1 that failed or was stopped (a cancel, ci.yml's timeout), "(no job)" when GitHub started none (one read per such run)
  until gh api "repos/$R/actions/runs/$1/jobs" -q 'if .total_count == 0 then "(no job)" else [.jobs[].steps[] | select(.conclusion == "failure" or .conclusion == "cancelled") | .name][0] // "" end'; do sleep 30; done
}
infra() {  # step $1 reads nothing the head changes: the runner's setup, the cache's download and generation when the head changes no cache input
  case $1 in "Set up job"|"Checkout repository"|"Set up JDK"*|"Set up Gradle"|"Cache game data"|*"(tools/gate/gate.sh gate-ci)"|"Post "*|"Complete job") return 0 ;;
    "Generate cache and gameval sources") ! fresh_input ;;   # it runs on a head's own revision alone
    "Rebuild sources from cached game data") ! cache_input ;;
    "(no job)") ! workflow_input ;;   # a workflow GitHub cannot start is the head's only when the head changes the workflows
    *) return 1 ;; esac
}
cache_input() {  # the head changes a cache input (or BASE...HEAD is unknown): the packing on the revision is the head's
  [ -n "${BASE:-}" ] && [ -n "${HEAD:-}" ] || return 0
  grep -qE 'or-cache/|/pack/|gamevals|raw-cache|game\.example\.yml' <<< "$(git -C "$repo" diff --name-only "$BASE...$HEAD")"   # not a pipe: grep -q ending first would fail git under pipefail
}
workflow_input() {  # the head changes a workflow (or BASE...HEAD is unknown)
  [ -n "${BASE:-}" ] && [ -n "${HEAD:-}" ] || return 0
  grep -q '^\.github/workflows/' <<< "$(git -C "$repo" diff --name-only "$BASE...$HEAD")"
}
fresh_input() {  # the head changes the revision (or BASE...HEAD is unknown): its download is the head's to run
  [ -n "${BASE:-}" ] && [ -n "${HEAD:-}" ] || return 0
  grep -qx 'game.example.yml' <<< "$(git -C "$repo" diff --name-only "$BASE...$HEAD")"
}
ci_step() {  # one classifier of a failed CI step for gate-ci and the carry
  infra "$arg" || exit 1
  R=$(git -C "$repo" remote get-url fork 2>/dev/null | sed -E 's#.*github.com[:/]##; s#\.git$##' || true); answers "$arg"
}
answers() {  # blocks until the source step $1 reads answers: GitHub for the runner's own steps (it answered this read), the release asset for the game data's, openrs2 for the cache's
  case $1 in "Generate cache"*) until openrs2; do sleep 30; done ;;
    "Game data of the gate"*) local k; k=$(git -C "$repo" rev-parse -q --verify "$TCOMMIT:game.example.yml" | cut -c1-12 || true); [ -n "$k" ] || return 0
      until gh release view game-data -R "$R" --json assets -q '.assets[].name' 2>/dev/null | grep -x "game-data-$k.tar.gz" >/dev/null; do seed; sleep 30; done ;; esac
}
openrs2() {  # openrs2 serves the revision's cache: its newest live cache of game.example.yml's revision yields bytes (an outage answers its index 200, the zip 500 or empty)
  local rev id; rev=$(git -C "$repo" show "$TCOMMIT:game.example.yml" 2>/dev/null | sed -nE 's/^revision: *([0-9]+).*/\1/p' | head -1)
  id=$(curl -sf https://archive.openrs2.org/caches.json | python3 -c 'import json,sys; r=int(sys.argv[1]); c=[x for x in json.load(sys.stdin) if x.get("game")=="oldschool" and x.get("environment")=="live" and any(b.get("major")==r for b in x.get("builds") or [])]; print(max(c, key=lambda x: x["timestamp"])["id"] if c else "")' "${rev:-0}" 2>/dev/null) && [ -n "$id" ] || return 1
  [ "$({ curl -sf "https://archive.openrs2.org/caches/runescape/$id/disk.zip" || true; } | head -c 4096 | wc -c)" = 4096 ]
}
read_runs() {  # $runs: "<workflow> <conclusion>/<status> <id> <attempt>" of each run at sha, newest first, read with If-None-Match the last ETag (one read
  # for both workflows; a 304 leaves $runs and costs no quota). A quota refusal holds the row until GitHub's reset, never fails it.
  local code tag reset body s
  while :; do
    { read -r code tag reset; body=$(cat); } < <(gh api -i ${etag:+-H "If-None-Match: $etag"} "$q" 2>/dev/null | python3 -c '
import json, re, sys, time
h, _, b = sys.stdin.read().replace("\r\n", "\n").partition("\n\n"); l = h.splitlines()
m = re.match(r"HTTP/\S+ (\d{3})", l[0] if l else ""); code = m.group(1) if m else "000"
k = {a.strip().lower(): v.strip() for a, _, v in (x.partition(":") for x in l[1:])}
if code in ("403", "429") and (k.get("x-ratelimit-remaining") == "0" or "rate limit" in b.lower()):  # GitHub states its reset: retry-after, else x-ratelimit-reset, else its documented minute
    print("quota -", int(time.time()) + int(k["retry-after"]) if k.get("retry-after", "").isdigit() else k.get("x-ratelimit-reset") or int(time.time()) + 60)
else:
    print(code, k.get("etag", "-"), 0)
    if code == "200":
        for r in json.loads(b)["workflow_runs"]: print(r["name"].replace(" ", "_"), (r["conclusion"] or "") + "/" + r["status"], r.get("id", 0), r.get("run_attempt", 1))
')
    case $code in 200) etag=$tag runs=$body; return ;; 304) return ;;
      quota) echo "GitHub refused $q on quota: held until its reset $(date -ud "@$reset" +%TZ)"; s=$((reset - $(date +%s))); if [ $s -gt 0 ]; then sleep $s; fi ;;
      ""|000|401|5??) sleep 30 ;;   # GitHub did not answer, or refused gh's login (the pass alerts it): a cause outside the tree holds the row, read again
      *) echo "$q: HTTP $code"; return 1 ;; esac
  done
}

case $verb in gate|gate-ci|ci-step) "${verb//-/_}" ;; test) arg= tests "${@:3}" ;; spotless) arg=${TCOMMIT:-} spotless ;;
  *) echo "verbs: test spotless gate gate-ci ci-step" >&2; exit 2 ;; esac
