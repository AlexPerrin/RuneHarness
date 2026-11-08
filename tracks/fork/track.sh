#!/usr/bin/env bash
# tracks/fork/track.sh <verb> <slug> [arg]: the server track (docs/ARCHITECTURE.md §11). Env from hd (act.start): HD_ROOT HD_DB
# HD_SLUG HD_KEY HD_TREE HD_TCOMMIT HD_HEAD HD_BASE HD_REPO HD_CLONE HD_LOG HD_RC HD_BUILDS and the short names the scripts and
# criteria read: SLUG HEAD T TCOMMIT BASE CLONE BUILD EVIDENCE CENTRAL. build and tree are build/build.sh's (the code a build
# runs), test, spotless, gate, gate-ci and ci-step gate/gate.sh's (the code a gate runs). Verbs:
#   up [N]            server-<slug> from or:<T>, its embedded Central serving the up's jav_config from file:// (an or:<T> whose Central reads
#                     none: first rebuilt with that Central merged with Central's staging, as the deploy's composite) on the change's ports (quest mode: QUEST_MODE, else the change's front
#                     matter quest-mode, else respect-progress; or assume-completed), N desktops logged in by token (auth type 7) with
#                     Play alone, no form typed: token-<slug> (server/issuer.py) is the issuer of compact signed tokens whose secret
#                     game.yml's token-login block holds and jav_config params 11 and 22 name (https: the client takes no other), each
#                     desktop's JX_SESSION_ID a session the issuer minted for its own account (the build is on staging, whose server
#                     takes token logins),
#                     each loading the live client's devtools jar (CLIENT_TRACK: the client track's script, its build of slug live);
#                     a fresh database, or with RESUME=1 the accounts as the change's last down saved them; the realm as live
#                     (dev_mode off, xp at 1x), every account a member at rank 0, or with STAFF=N[,M...] those desktops' administrators;
#                     idle logout off (live keeps it); each desktop logged in again after any logout until down (keep); a failed
#                     up takes down what it started; one up, restart or down of a slug at a time (a second waits)
#   up token          up 1; with SIGN_IN=central (tracks/central/track.sh up <slug> token, one desktop) the head's
#                     Central signs in instead of the issuer: server-<slug> alone, its Central serving jav_config (its file the template, rendered),
#                     OIDC and game-session over https on the http port (the issuer's secret and certificate) and http on a docker
#                     port, the desktop's JX_SESSION_ID a real session of account 1 (sign_in); restart refused (sessions are in memory)
#   token [TOKEN]     the token the desktop's next login sends (none: a fresh valid one); server/issuer.py mint makes expired
#                     ones (--exp -5), another account's, and forged ones (another key DIR)
#   live-desktop      one desktop on the live stack (EXTRA_PLUGINS: more jars it loads), signed in through the live Central's sign-in
#                     as this slug's own account (its first sign-in registers it) and logged in by token with Play alone; prints LIVE_DESKTOP <devtools port> <instance dir>
#   live-desktop-down stops that desktop and removes its instance
#   restart           logs up's desktops out, restarts server-<slug>, its game.yml and database kept, and logs them in again
#   down              stops the desktops, waits until the server has saved and dropped their characters or is gone, removes the stack record's containers
#                     and then the record (state/<slug>/up.json: up writes it before its first container; hd's repair reads its script and containers)
#   deploy TCOMMIT    staging's tree to the live test server: build, the deploy image with the live stack's key pair (state/live/key, the
#                     modulus every APK carries) and the issuer's secret, its key checked, boot check, deploy, or roll back; state/live/tree.json
#                     records the live stack; the job's result by `hd job deploy`
#   recipe            one version per verb the pass keys a job by (build, gate, deploy): bump a verb's when its output changes; deploy's carries the digest of the files the live stack runs from this checkout
#   log <slug> PATTERN  the lines of the change's server container matching PATTERN (slug `live`: the live server)
#   recordings <slug> REGEX  the RSProx transcripts holding a packet type or text (any case: CLANSETTINGS finds clansettings_delta)
#   transcribe <slug> [ID...]  rewrites those recordings' transcripts (none: every one) with every RSProx filter on (its defaults
#                     hide clan and friends-chat packets): RSPROX/../bin/<id>.bin (gzip) to RSPROX/<id>.txt, RSProx 1.0.5 in RSPROX_RUNTIME
# Windows locations, run through WSL interop (override in the environment):
#   WINDOWS_SYSTEM32  /mnt/c/Windows/System32   netstat.exe, taskkill.exe, robocopy.exe
#   DESKTOP_DIR       /mnt/c/osrs-test          the desktops' template; each up's instances are DESKTOP_DIR/run/N (jdk/bin/java.exe, jps.exe)
set -euo pipefail
verb=$1; slug=${2:-${SLUG:-}}; arg=${3:-}   # a criterion passes no slug: hd exports SLUG
self=$(cd "$(dirname "$0")" && pwd)
root=${HD_ROOT:-$(cd "$self/../.." && pwd)}; hd="python3 $root/harness/hd.py"
repo=${HD_REPO:-$(dirname "$(git -C "${CLONE:-$HOME/src/OpenRune-Server}" rev-parse --path-format=absolute --git-common-dir)")}   # the main checkout, also when CLONE names a worktree of it (a brief's clone)
case $verb in recipe) printf 'build fork-1\ngate fork-1\ndeploy fork-1-%s\n' "$(cd "$self/server" && cat issuer.py docker-compose.yml switch.env jav_config.ws.template | sha256sum | cut -c1-12)"; exit 0 ;; esac   # the stack runs these files from this checkout: a shipped one moves the deploy's key
[ -f "$root/harness/changes/$slug.md" ] || [ -f "$root/harness/goals/$slug.md" ] || case $slug in live|staging) ;; *) echo "no change or goal \"$slug\": tracks/fork/track.sh <verb> <slug> [arg]" >&2; exit 2 ;; esac
case $verb in build|tree) exec "$self/build/build.sh" "$@" ;; test|spotless|gate|gate-ci|ci-step) exec "$self/gate/gate.sh" "$@" ;; esac
state=$root/state/$slug; mkdir -p "$state"
live_image=osrs-openrune:241; compose_dir=$self/server
export SIDECAR_DATA=${SIDECAR_DATA:-$HOME/src/openrune-work/server-tools/sidecar/data}; sidecar_data=$SIDECAR_DATA  # compose mounts ${SIDECAR_DATA}
atomic() { cat > "$1.$$.tmp"; if [ -s "$1.$$.tmp" ]; then mv -f "$1.$$.tmp" "$1"; else rm -f "$1.$$.tmp"; return 1; fi; }   # a state record whole or not at all: hd reads it at any moment
stack() {  # stack KEY=VALUE...: sets each field of the stack record state/<slug>/up.json (KEY:=JSON for a number); one record up writes and every later step reads; mirrored into the ledger's stack row
  python3 -c 'import json, sys
try: d = json.load(open(sys.argv[1]))
except (OSError, ValueError): d = {}
for a in sys.argv[2:]:
    k, v = a.split("=", 1); d[k.rstrip(":")] = json.loads(v) if k.endswith(":") else v
print(json.dumps(d))' "$state/up.json" "$@" | atomic "$state/up.json"; $hd stack "$slug" "$state/up.json"; }
modulus_of() { openssl rsa -noout -modulus 2>/dev/null | cut -d= -f2 | tr A-F a-f; }   # stdin a private key: its public modulus, lowercase hex as client.key and the APK carry it
ready() {  # ready <container> [since]: blocks until "Server ready in" or the container stops; fails at once on one not (re)started since
  local s; s=$(docker inspect -f '{{.State.StartedAt}}' "$1" 2>/dev/null | cut -c1-19)
  [ -z "${2:-}" ] || [[ ! "$s" < "${2:0:19}" ]] || { echo "$1 has run since $s, not started since $2"; return 1; }
  while ! docker logs ${2:+--since "$2"} "$1" 2>&1 | grep "Server ready in" >/dev/null; do   # grep reads to the end: -q's early exit SIGPIPEs docker logs under pipefail
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" = true ] || { echo "$1 is not running"; return 1; }; sleep 5
  done
}
port() { echo $(( 20000 + 16#$(printf %s "$slug" | sha1sum | cut -c1-3) * 2 + $1 )); }   # game +0, http +1; shortcut: two slugs may hash alike, pick from up.json when it happens
quest_mode() { m=${QUEST_MODE:-$(awk '/^---$/{n++; next} n==1 && /^quest-mode:/{print $2}' "$root/harness/changes/$slug.md" 2>/dev/null)}; echo "${m:-respect-progress}"; }   # QUEST_MODE, else the change's front matter quest-mode, else respect-progress
idle_off() { sed -E 's/^([[:space:]]*idle-logout:[[:space:]]*).*/\1false/'; }   # stdin game.yml with idle logout off: a run's desktops idle while its agent reads (live keeps the image's); a tree without the key has no idle logout
quests() { case $1 in respect-progress|assume-completed) ;; *) echo "quest-mode \"$1\": respect-progress or assume-completed" >&2; return 1 ;; esac   # quests MODE: stdin game.yml with quest-requirements mode MODE
  y=$(sed -E "/^[[:space:]]*quest-requirements:/,/^[[:space:]]*mode:/ s/(mode:[[:space:]]*).*/\1\"$1\"/"); grep -q "mode: \"$1\"" <<< "$y" || { echo "game.yml has no quest-requirements mode" >&2; return 1; }; printf '%s\n' "$y"; }
account() { echo "h$(printf %s "$slug" | sha1sum | cut -c1-9)${1:-}"; }   # the Nth desktop's login name and password (no N: the prefix of this slug's names): 11 characters (a login name takes 12 at most), listed in the slug's up.json
mine="select c.id from account_characters c join accounts a on a.id = c.account_id where lower(a.account_name) like '$(account)%'"   # this slug's characters
sql() { local pg; pg=$(docker logs "server-$slug" 2>&1 | grep -oE 'jdbc:postgresql://localhost:[0-9]+' | tail -1 | grep -oE '[0-9]+$')
  docker run --rm --network "container:server-$slug" postgres:16-alpine psql -h 127.0.0.1 -p "$pg" -U postgres -d postgres -tAq -c "$1"; }
login() {  # login <devtools port> <account>: logs that desktop in as the account (a FAILED login fails up and restart: one whose inventory widget does not show container 93 too); a lost key types another name, whose first login makes a stray account (the rights update then missed the real row): until this login made no row but the account's, out and in again
  local m; while :; do m=$(sql "select coalesce(max(id), 0) from accounts")
    python3 "$self/server/desktop_login.py" "$1" token   # Play alone; prints LOGGED_IN or FAILED: reason
    [ "$(sql "select string_agg(lower(account_name), ' ') from accounts where id > $m or lower(account_name) = '$2'")" = "$2" ] && return
    echo "login on $1 made another account than $2: logging in again"; python3 "$self/server/desktop_login.py" "$1" logout; done; }
keep() {  # keep <devtools port> <account>: from now until down, that desktop logged out (a disconnect, a restart, a logout) logs in again
  setsid python3 "$self/server/desktop_login.py" "$1" keep "server-$slug" token < /dev/null >> "$state/keep-$1.log" 2>&1 & }
unkeep() { pkill -f "^python3 [^ ]*/desktop_login\.py [0-9]+ keep server-$slug " || true; }   # this slug's keepers stopped, by their command line (no pid file a reused pid could match): a logout that is meant stays out
offline() { until [ "$(docker inspect -f '{{.State.Running}}' "server-$slug" 2>/dev/null)" != true ] || [ "$(sql "select count(*) from main.character_progress where online_central_world_id is not null and character_id in ($mine)")" = 0 ]; do sleep 1; done; }   # each character saved at its logout, or the server gone: none is saved after

sys32=${WINDOWS_SYSTEM32:-/mnt/c/Windows/System32}; desk=${DESKTOP_DIR:-/mnt/c/osrs-test}
need() { [ -x "$1" ] || { echo "$1 not found: set $2" >&2; exit 2; }; }   # need <program> <the variable that locates it>
# a loaded host's WSL interop can leave a Windows program hanging (accept4 failed 110): each listing ends, failed, and is asked again
tcp() { timeout 20 "$sys32/netstat.exe" -ano -p TCP | tr -d '\r' | awk '$4=="LISTENING"{n=split($2,a,":");print a[n], $5}'; }   # "<port> <Windows PID>" of each Windows listening socket
# RSProx binds jav_config on 43600+skip and proxies on 43701+skip; a bind in a range Windows reserves fails (WSL's mirrored
# networking reserves the Linux ephemeral range, which moves each boot; Windows' own excluded ranges): stdin "<lo> <hi>" per range
skip_base() { awk '{lo[NR] = $1; hi[NR] = $2} END {for (b = 0; 43751 + b <= 65535; b++) {ok = 1; for (r in lo) if (lo[r] <= 43751 + b && hi[r] >= 43600 + b) {ok = 0; b = hi[r] - 43600; break}; if (ok) {print b; exit}}; exit 1}'; }   # the least skip whose 51 instances' ports avoid every range
# a Windows process a run started through WSL interop outlives the run's Linux processes: each is recorded, its Windows pid
# and image, under the run's systemd slice (osrs-harness R5: hd ends them with the run); its down drops the record
winpid() { local sl; sl=$(grep -o 'hd-run-[0-9]*\.scope' /proc/self/cgroup) || return 0; mkdir -p "$root/state/winpids/$sl" && echo "$2" > "$root/state/winpids/$sl/$1"; }   # hd stop ends them with the run
marked() { "$desk/jdk/bin/jps.exe" -v | tr -d '\r' | awk -v m="-Dosrstest.marker=osrs-test-run$1" '{for (f = 3; f <= NF; f++) if ($f == m) {print $1, $2; next}}'; }   # "<Windows PID> <main class>" of instance N's JVMs: only desktop_start sets the marker
# The desktops: each up creates its own instances. DESKTOP_DIR is the template (JDK, RSProx and its launcher, a staged
# home); instance N is the dir DESKTOP_DIR/run/N, claimed by its mkdir and naming its up's slug in run/N/owner, with its
# own home copied from the template's (devtools plugin: the live client's build; disk cache: the server's), devtools port 7779+N answering only the up's
# token (up.json "token", sent as Authorization: Bearer <token>) and RSProx ports
# moved up by skip_base + N-1. Every JVM of instance N carries -Dosrstest.marker=osrs-test-runN;
# nothing without it is ever stopped (the user's own RuneLite). down stops and removes the instances its slug owns.
desktop_start() {  # sets inst dt (desktopN, its devtools port)
  local i d dp w t l o busy ex base ep p b pid
  need "$sys32/netstat.exe" WINDOWS_SYSTEM32; need "$sys32/netsh.exe" WINDOWS_SYSTEM32; need "$sys32/robocopy.exe" WINDOWS_SYSTEM32; need "$sys32/taskkill.exe" WINDOWS_SYSTEM32; [ -x "$desk/jdk/bin/java.exe" ] || "$self/server/desktop_template.sh" "$desk" >&2; need "$desk/jdk/bin/java.exe" DESKTOP_DIR; need "$desk/jdk/bin/jps.exe" DESKTOP_DIR; [ -f "$desk/home/.rlcustom/settings.properties" ] || { echo "no staged home in $desk/home" >&2; return 1; }
  mkdir -p "$desk/run"; until busy=$(tcp); do sleep 1; done; busy=$(cut -d' ' -f1 <<< "$busy")
  until ex=$(timeout 20 "$sys32/netsh.exe" interface ipv4 show excludedportrange protocol=tcp); do sleep 1; done
  base=$({ cat /proc/sys/net/ipv4/ip_local_port_range; tr -d '\r' <<< "$ex" | awk '$1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/ {print $1, $2}'; } | skip_base) || { echo "no RSProx ports outside the reserved ranges" >&2; return 1; }
  for i in $(seq 1 51); do d=$desk/run/$i; dp=$((7779 + i))
    grep -qx "$dp" <<< "$busy" || ! mkdir "$d" 2>/dev/null || break; d=   # mkdir is the claim: no two ups get one N
  done
  [ -n "$d" ] || { echo "no free desktop instance" >&2; return 1; }
  echo "$slug $$-$(date +%s%N)" > "$d/owner"; w=$(wslpath -w "$d")   # the slug and this claim: desktop_login.py acts only while the text it started with is there
  until [ -f "$d/home/.rlcustom/settings.properties" ]; do   # a WSL interop error can end robocopy before it copied (below 8): copied again until the home is there
    "$sys32/robocopy.exe" "$(wslpath -w "$desk/home")" "$w\\home" /E /MT:16 /NFL /NDL /NJH /NJS /NP /XD screenshots logs /XF 'main_file_cache.*' > /dev/null || [ $? -lt 8 ] || { echo "robocopy of the desktop home into $d failed" >&2; return 1; }   # robocopy: below 8 is success
  done
  # the disk cache is the one the server serves: a login then fetches no group over JS5, which its interfaces' onLoad scripts would run before
  mkdir -p "$d/home/.rlcustom/jagexcache/oldschool/LIVE" && docker exec "${srv:-server-$slug}" tar -c -C /app/.data/cache/LIVE . | tar -x -C "$d/home/.rlcustom/jagexcache/oldschool/LIVE"   # docker cp fails writing the dat2 to a Windows drive in one piece
  sed -i "s/^openrunedevtools\.port=.*/openrunedevtools.port=$dp/" "$d"/home/.rlcustom/settings.properties $(ls "$d"/home/.rlcustom/profiles2/*.properties 2>/dev/null)   # a fresh template has no profile yet: RuneLite imports settings.properties
  mkdir -p "$d/home/.rlcustom/sideloaded-plugins" && cp "$jar" "$d/home/.rlcustom/sideloaded-plugins/OpenRune-Developer-Tools.jar"
  for x in ${EXTRA_PLUGINS:-}; do cp "$x" "$d/home/.rlcustom/sideloaded-plugins/"; done   # more plugin jars (the client track's probe), loaded at this start
  ep=http${sic:+s}://127.0.0.1:$http   # OPENRUNE_ENDPOINT: the launcher takes jav_config from it alone, and jav_config names every other endpoint
  printf '%s\n' "- name: OpenRune Test - $slug" "  jav_config_url: $ep/jav_config.ws" "  modulus: $modulus" "  revision: 241.1" \
    "  game_server_port: $game" "  runelite_bootstrap_commithash: e617bef1a7f5c39fbe8768994d27d638941efd5d" "  binary_folder: openrune-qa" > "$d/home/.rsprox/proxy-targets.yaml"
  t=$(wslpath -w "$desk"); l=launcher-$(sha1sum < "$self/server/OsrsTestLauncher.java" | cut -c1-12)   # this tools tree's launcher, compiled once into the template
  [ -f "$desk/rsprox/$l/OsrsTestLauncher.class" ] || { rm -rf "$desk/rsprox/$l.$$" && mkdir -p "$desk/rsprox/$l.$$" \
    && "$desk/jdk/bin/javac.exe" -nowarn -cp "$t\\rsprox\\lib\\*" -d "$t\\rsprox\\$l.$$" "$(wslpath -w "$self/server/OsrsTestLauncher.java")" >&2 \
    && { mv -T "$desk/rsprox/$l.$$" "$desk/rsprox/$l" 2>/dev/null || rm -rf "$desk/rsprox/$l.$$"; }; }   # a concurrent up may have placed it first
  o=owner-$(sha1sum < "$self/server/DevtoolsOwner.java" | cut -c1-12)   # the endpoint's owner check, its jar built once into the template
  [ -f "$desk/rsprox/$o.jar" ] || { rm -rf "$desk/rsprox/$o.$$" && mkdir -p "$desk/rsprox/$o.$$/c" && printf 'Premain-Class: DevtoolsOwner\nCan-Retransform-Classes: true\n' > "$desk/rsprox/$o.$$/m" \
    && "$desk/jdk/bin/javac.exe" -nowarn --add-exports jdk.httpserver/sun.net.httpserver=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED -d "$t\\rsprox\\$o.$$\\c" "$(wslpath -w "$self/server/DevtoolsOwner.java")" >&2 \
    && "$desk/jdk/bin/jar.exe" cfm "$t\\rsprox\\$o.$$\\o.jar" "$t\\rsprox\\$o.$$\\m" -C "$t\\rsprox\\$o.$$\\c" . \
    && mv -f "$desk/rsprox/$o.$$/o.jar" "$desk/rsprox/$o.jar"; rm -rf "$desk/rsprox/$o.$$"; }   # a concurrent up may have placed the same jar first
  [ -f "$desk/rsprox/$o.jar" ] || { echo "no devtools owner check $desk/rsprox/$o.jar" >&2; return 1; }
  # every JVM of the instance: the devtools endpoint on $dp answers only a request carrying the token in its guard file (server/DevtoolsOwner.java),
  # this up's, or any caller while a live session's bridge predates serve.py (desktop_login.py guard, and its keeper while the desktop is up)
  python3 "$self/server/desktop_login.py" "$dp" guard "$devtoken" >&2
  jo=" -javaagent:$t\\rsprox\\$o.jar -Dcom.sun.net.httpserver.HttpServerProvider=DevtoolsOwner --add-exports=jdk.httpserver/sun.net.httpserver=ALL-UNNAMED -Dosrstest.devtools=$dp:$w\\guard -Dosrstest.refusals=$(wslpath -w "$state/refused-urls.log")"   # no URL reaches the OS: each refused one is a line of that log
  jx=JAVA_TOOL_OPTIONS:OPENRUNE_ENDPOINT
  if [ -n "${tok:-}" ]; then  # the client's Jagex session variables; the JDK's CAs plus the issuer's certificate (RSProx fetches RuneLite over public https)
    jx+=:JX_SESSION_ID:JX_CHARACTER_ID:JX_DISPLAY_NAME; cp "$desk/jdk/lib/security/cacerts" "$d/home/token-trust.p12"; cp "$ca" "$d/home/token-tls.pem"
    "$desk/jdk/bin/keytool.exe" -importcert -noprompt -alias harness-issuer -storepass changeit -keystore "$w\\home\\token-trust.p12" -file "$w\\home\\token-tls.pem" >/dev/null
    jo+=" -Djavax.net.ssl.trustStore=$w\\home\\token-trust.p12 -Djavax.net.ssl.trustStorePassword=changeit"
  fi
  pid=
  until tcp | grep "^$dp " >/dev/null; do   # the devtools endpoint answers, the desktop died, or its plugin could not bind the port (the client lives on without it)
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
      ! grep -q 'UtilAcceptVsock' "$state/desktop$i.log" || grep -qv 'UtilAcceptVsock' "$state/desktop$i.log" && { echo "desktop $i exited: $(grep -m1 -E 'REFUSING|Exception' "$state/desktop$i.log" || tail -3 "$state/desktop$i.log")" >&2; return 1; }
      # WSL interop ended the launch before Windows ran it (its log holds that error alone): launched again once the interop answers, any JVM it left stopped first
      until "$desk/jdk/bin/jps.exe" > /dev/null 2>&1; do sleep 1; done
      for p in $(marked "$i" | cut -d' ' -f1); do "$sys32/taskkill.exe" /F /T /PID "$p" > /dev/null 2>&1 || true; rm -f "$root"/state/winpids/*/"$p"; done
      pid=
    fi
    if [ -z "$pid" ]; then
      (cd "$d" && JAVA_TOOL_OPTIONS="-Duser.home=$w\\home -Dosrstest.marker=osrs-test-run$i$jo" WSLENV=${WSLENV:+$WSLENV:}$jx \
        OPENRUNE_ENDPOINT=$ep JX_SESSION_ID=${sid:-harness} JX_CHARACTER_ID=${cid:-1} JX_DISPLAY_NAME="${who:-$(account 1)}" \
        exec setsid "$desk/jdk/bin/java.exe" "-Dosrstest.marker=osrs-test-run$i" "-Dosrstest.portskip=$((base + i - 1))" "-Dosrstest.target=OpenRune Test - $slug" \
        "-Dosrstest.token=${tok:-false}" -cp "$t\\rsprox\\$l;$t\\rsprox\\lib\\*" OsrsTestLauncher) < /dev/null > "$state/desktop$i.log" 2>&1 &   # nothing may hold the caller's pipe
      pid=$!
    fi
    b=$(grep -m1 -A1 "Failed to start MCP server on port $dp" "$d/home/.runelite/logs/client.log" 2>/dev/null | tr '\n' ' ') || true   # logs/ is never copied into a claim: the line is this start's
    [ -z "$b" ] || { echo "desktop $i: its devtools plugin could not bind $dp: $b" >&2; return 1; }
    for p in $(marked "$i" | cut -d' ' -f1); do winpid "$p" "java.exe"; done; sleep 2
  done
  for p in $(marked "$i" | cut -d' ' -f1); do winpid "$p" "java.exe"; done
  inst=desktop$i; dt=$dp
}
desktops_remove() {  # stops every JVM carrying the marker of an instance this slug owns, then removes the instance, its owner last (a failed down re-runs)
  local o d i p; need "$sys32/taskkill.exe" WINDOWS_SYSTEM32; need "$desk/jdk/bin/jps.exe" DESKTOP_DIR
  for o in "$desk"/run/*/owner; do
    [ -f "$o" ] && [ "$(cut -d' ' -f1 "$o")" = "$slug" ] || continue; d=${o%/owner}; i=${d##*/}
    # jps can list a live JVM as "process information unavailable": a file it still holds keeps the loop stopping marked JVMs
    until [ -z "$(marked "$i")" ] && find "$d" -mindepth 1 -maxdepth 1 ! -name owner -exec rm -rf {} + 2>/dev/null; do
      for p in $(marked "$i" | cut -d' ' -f1); do "$sys32/taskkill.exe" /F /T /PID "$p" > /dev/null 2>&1 || true; rm -f "$root"/state/winpids/*/"$p"; done; sleep 1
    done
    rm -rf "$d"
  done
}

devtools_jar() {  # sets jar: the devtools classes jar of the client track's build of slug live (origin/HEAD of the client), cached by its T
  local c=$root/tracks/client/track.sh crepo tc
  crepo=$(python3 -c 'import os, sys, yaml; p = os.path.expanduser(yaml.safe_load(open(sys.argv[1]))["repos"]["client"]["path"]); print(p if os.path.isabs(p) else os.path.normpath(os.path.join(sys.argv[2], p)))' "$root/hd.yaml" "$root")
  tc=$(git -C "$crepo" rev-parse "origin/HEAD^{commit}")
  flock "$root/state/client-live.lock" env -u T -u TCOMMIT -u EVIDENCE HD_ROOT="$root" HD_REPO="$crepo" "$c" build live "$tc" >&2   # one build copy for every up
  jar=$root/evidence/live/$(git -C "$crepo" rev-parse "$tc^{tree}").devtools-desktop.jar
  [ -f "$jar" ] || { echo "no desktop devtools jar $jar" >&2; return 1; }
}

keys() {  # the change's key pair in $state/key, made by up alone: whichever change built or:<T>, no key is copied from a build
  k=$state/key; [ -f "$k/game.key" ] && [ -f "$k/client.key" ] && return
  rm -rf "$k" 2>/dev/null || docker run --rm -v "$state:/s" postgres:16-alpine rm -rf /s/key; mkdir "$k"   # the root-owned directories docker made for missing mount sources go too
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:1024 -out "$k/game.key" 2>/dev/null   # PKCS#8, as the server's generateRsa writes
  printf 'Exponent: 10001\nModulus: %s' "$(modulus_of < "$k/game.key")" > "$k/client.key"
}
sign_in() {  # sign_in [ACCOUNT]: sets sid cid, a session of Central's sign-in as the client's launcher makes it (auth -> token -> sessions), and its account:
  # ACCOUNT's by its password (its name; Central registers an account that never played), else Central's dev account
  local b=https://127.0.0.1:$http c=(curl -fsS --cacert "$ca") a=(-G) code idt
  [ -z "${1:-}" ] || a=(--data-urlencode "username=$1" --data-urlencode "password=$1")
  code=$("${c[@]}" -o /dev/null -w '%{redirect_url}' "${a[@]}" -d redirect_uri=http://127.0.0.1/cb -d state=up -d client_id=harness "$b/oauth2/auth" | sed -nE 's/.*[?&]code=([^&]+).*/\1/p')
  idt=$("${c[@]}" -d grant_type=authorization_code -d "code=$code" -d client_id=harness "$b/oauth2/token" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id_token"])')
  sid=$("${c[@]}" -H 'Content-Type: application/json' -d "{\"idToken\":\"$idt\"}" "$b/game-session/v1/sessions" | python3 -c 'import json,sys;print(json.load(sys.stdin)["sessionId"])')
  cid=$("${c[@]}" -H "Authorization: Bearer $sid" "$b/game-session/v1/accounts" | python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["accountId"])')
}
crepo=${CENTRAL_REPO:-$HOME/src/OpenRune-Central-Server}
file_central() { local c; c=$(grep -oE '_c[0-9a-f]{12}' <<< "$T") && git -C "$crepo" grep -q 'scheme == "file"' "${c#_c}" -- central-app/src/main; }   # or:<T>'s Central (its _c<tree12>; none: the published one, which fetches jav_config over http alone) reads a file:// jav_config
central_staged() {  # the T of or:<T>'s tree built with Central's staging, the Central the deploy runs (with CENTRAL: that head merged with it), on stdout
  local h p c t; h=$(git -C "$crepo" rev-parse refs/heads/staging)
  if [ -n "${CENTRAL:-}" ]; then IFS=: read -r p c <<< "$CENTRAL"
    t=$(git -C "$crepo" merge-tree --write-tree "$c" "$h") || { echo "Central $c does not merge with Central's staging: merge it there first" >&2; return 1; }
    h=$(git -C "$crepo" -c user.name="Alex Perrin" -c user.email=44126061+AlexPerrin@users.noreply.github.com commit-tree "$t" -p "$c" -p "$h" -m "up: $c with staging"); fi
  (unset T; CENTRAL="$crepo:$h" HD_KEY= "$self/build/build.sh" build "$slug" >&2)   # TCOMMIT (the pass's) or the dev's working copy, as the up's own build; cached by its _c<tree12>
  python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["T"])' "$state/build.json"; }
central_jav() {  # $state/jav_config.ws for the game's own Central: $tpl filled as the sidecar fills it, its base http(s, with $sic)://127.0.0.1:$http
  sed -E "s#\{\{HTTP_BASE\}\}#http${sic:+s}://127.0.0.1:$http#g; s#\{\{WORLD_HOST\}\}#127.0.0.1#g; s#\{\{WORLD_ID\}\}#255#g; s#\{\{WORLD_FLAGS\}\}#1#g; s#\{\{MEMBERS_WORLD\}\}#true#g; s#^param=17=.*#param=17=http${sic:+s}://127.0.0.1:$http/worldslist.ws#" "$tpl" > "$state/jav_config.ws"; }
up() {
  tok=true; sic=; sid=; cid=; who=; ca=$state/token/tls.pem; n=${arg:-1}; [ "$n" != token ] || n=1; [ "${SIGN_IN:-}" != central ] || sic=1
  [ -z "$sic" ] || [ "$n" = 1 ] || { echo "SIGN_IN=central signs one desktop in" >&2; return 2; }; T=${T:-$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["T"])' "$state/build.json")}
  [ -n "$sic" ] || file_central || T=$(central_staged)
  docker image inspect "or:$T" >/dev/null 2>&1 || { echo "no image or:$T: build first"; return 1; }
  devtools_jar   # the jar every desktop of this up loads
  game=$(port 0); http=$(port 1)
  down >/dev/null   # a previous up's desktops and containers
  set -E; trap 'why="$BASH_COMMAND (status $?)"' ERR   # the step set -e ends at, in the function it failed in (it may print nothing)
  trap 'echo "up ended before it was up, at: ${why:-$BASH_COMMAND} (the server log: $state/failed-up.log)" >&2; { docker logs "server-$slug" > "$state/failed-up.log" 2>&1; [ -z "${inst:-}" ] || cp "$desk/run/${inst#desktop}/home/.runelite/logs/client.log" "$state/failed-up-client.log"; } 2>/dev/null || true; down >/dev/null 2>&1' EXIT   # a failed or stopped up names the step it ended at and keeps the server's log, then leaves no half-up instance: its desktops and containers go
  docker run --rm --entrypoint cat "or:$T" /app/game.yml | quests "$(quest_mode)" | idle_off > "$state/game.yml"   # upstream's default assume-completed skips every quest check
  keys   # never a missing mount source: docker would make it a directory
  modulus=$(modulus_of < "$state/key/game.key"); devtoken=$(openssl rand -hex 16)   # the up's devtools token: its desktops' endpoints answer no other caller
  staff=$(for i in $(tr , ' ' <<< "${STAFF:-}"); do account "$i"; done | paste -sd' ')   # STAFF=1,2: those desktops' accounts administrators
  cs="server-$slug"; [ -n "$sic" ] || cs+=" token-$slug"
  stack started="$(date -u +%FT%TZ)" script="$self/track.sh" repo="$repo" containers="$cs" signin="${sic:+central}" \
    modulus="$modulus" game:="$game" http:="$http" desktops= accounts= staff="$staff" token="$devtoken"   # before its first container: down and hd's repair act on what it names
  tpl=$self/server/jav_config.ws.template
  sopt=()   # server-<slug>'s own mounts, ports and environment
  if [ -n "$sic" ]; then  # Central's sign-in: game.yml trusts the issuer's secret; Central signs with it and serves https with its certificate
    python3 "$self/server/issuer.py" key "$state/token" >> "$state/game.yml"
    openssl pkcs12 -export -in "$state/token/tls.pem" -inkey "$state/token/tls.key" -passout pass:changeit -out "$state/token/tls.p12"
    sopt=(-p "$http:8443" -p 8080 -v "$state/token/tls.p12:/app/.data/central-tls.p12:ro"
      -e "OPENRUNE_SIGN_IN_TOKEN_SECRET=$(cat "$state/token/secret")" -e "OPENRUNE_SIGN_IN_DEV_ACCOUNT=$(account 1)" -e OPENRUNE_HTTP_TLS_PORT=8443
      -e OPENRUNE_HTTP_TLS_KEYSTORE=/app/.data/central-tls.p12 -e OPENRUNE_HTTP_TLS_KEYSTORE_PASSWORD=changeit)
  else  # the issuer: game.yml trusts its key; param 11 sends the desktop's game-session calls to it
    python3 "$self/server/issuer.py" key "$state/token" >> "$state/game.yml"; rm -f "$state/token/token"   # no token a past `token` wrote: each desktop's own session
    docker run -d --name "token-$slug" -p 8080 -v "$self/server/issuer.py:/issuer.py:ro" -v "$state/token:/t:ro" python:3.13-alpine python3 /issuer.py serve /t >/dev/null
    sed -E "s#^param=(11|22)=.*#param=\1=https://127.0.0.1:$(docker port "token-$slug" 8080 | head -1 | cut -d: -f2)/#" "$tpl" > "$state/jav_config.ws.template"; tpl=$state/jav_config.ws.template   # 11 Jagex auth, 22 RuneScape auth: the client casts both to https
  fi
  central_jav   # the game's own Central serves /jav_config.ws on the up's http port (8080; https on 8443 with its sign-in), the template filled as the sidecar fills it
  sopt+=(-v "$state/jav_config.ws:/app/jav_config.ws:ro" -e OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file:///app/jav_config.ws); [ -n "$sic" ] || sopt+=(-p "$http:8080")
  [ -n "${RESUME:-}" ] || rm -rf "$state/postgres"; mkdir -p -m 700 "$state/postgres"   # fresh, or RESUME: the last down's (owner uid 1000, the server's)
  docker run -d --name "server-$slug" --cpus=4 --memory=4g -p "$game:43594" -v "$state/postgres:/app/.data/postgres" \
    -v "$state/key/game.key:/app/.data/game.key:ro" -v "$state/key/client.key:/app/.data/client.key:ro" -v "$state/game.yml:/app/game.yml:ro" "${sopt[@]}" "or:$T" >/dev/null
  ready "server-$slug"
  # Central seeds a dev realm (every login an administrator, xp at 150x); the server reads its realm at boot: as live, then restarted
  if [ -n "$(sql "update realms set dev_mode = 0, player_xp_rate_in_hundreds = 100, global_xp_rate_in_hundreds = 100 where dev_mode <> 0 or player_xp_rate_in_hundreds <> 100 or global_xp_rate_in_hundreds <> 100 returning 1")" ]; then since=$(date -u +%FT%TZ); docker restart "server-$slug" >/dev/null; ready "server-$slug" "$since"; fi
  if [ -z "$sic" ]; then python3 "$self/server/javcheck.py" "http://127.0.0.1:$http/jav_config.ws"   # no desktop is pointed at a foreign host
  else python3 "$self/server/javcheck.py" "http://127.0.0.1:$(docker port "server-$slug" 8080 | head -1 | cut -d: -f2)/jav_config.ws"; sign_in; fi   # Central's, over its http port; the session after the realm's restart (Central keeps sessions in memory)
  desktops=(); accounts=()
  for i in $(seq 1 "$n"); do
    [ -n "$sic" ] || { who=$(account "$i"); sid=$(python3 "$self/server/issuer.py" mint "$state/token" "$who" --exp 31536000); cid=$(python3 -c 'import sys, zlib; print(zlib.crc32(sys.argv[1].encode()) & 0x7FFFFFFF)' "$who"); }   # the session the issuer answers with this desktop's account
    desktop_start
    desktops+=("$inst:$dt"); accounts+=("$(account "$i")")
    stack desktops="${desktops[*]}" accounts="${accounts[*]}"   # before the login: restart and the devtools tools find each desktop
    login "$dt" "$(account "$i")"      # creates the account on first login; prints LOGGED_IN or FAILED: reason
  done
  # members and rights are read at login and members written by the save at logout: log out, wait until no character of this up is online, update, log in
  for c in "${desktops[@]}"; do python3 "$self/server/desktop_login.py" "$(cut -d: -f2 <<< "$c")" logout; done
  offline
  sql "update account_characters set members = true where id in ($mine)" >/dev/null
  rights="case when lower(account_name) in ($(for a in $staff; do printf "'%s', " "$a"; done)'') then 'ADMINISTRATOR' else '' end"   # players as on live; the record's staff administrators
  sql "update accounts set rights = $rights where lower(account_name) like '$(account)%'" >/dev/null
  for i in "${!desktops[@]}"; do login "$(cut -d: -f2 <<< "${desktops[$i]}")" "${accounts[$i]}"; done
  [ "$(sql "select count(*) from accounts where lower(account_name) like '$(account)%' and rights <> $rights")" = 0 ] || { echo "up: the accounts' rights did not hold after the login"; return 1; }   # read back once the logins ran: up fails rather than leave a cheat silently refused
  for i in "${!desktops[@]}"; do keep "$(cut -d: -f2 <<< "${desktops[$i]}")" "${accounts[$i]}"; done
  trap - EXIT; echo "up: game $game http $http desktops ${desktops[*]}${staff:+ administrators $staff}"
}
restart() {  # the server container restarted with its game.yml and database; the desktops of up logged out first (a server dropping a client leaves the disconnected dialog, which no key closes) and logged in again
  d=$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(d["desktops"], "|", d["accounts"], "|", d.get("signin", ""))' "$state/up.json")
  [ -z "$(cut -d'|' -f3 <<< "$d" | tr -d ' ')" ] || { echo "restart: Central keeps the desktop's sign-in session in memory, which a restart loses: down and up again" >&2; return 1; }
  d=${d%|*}
  read -ra ds <<< "${d%%|*}"; read -ra as <<< "${d#*|}"
  unkeep; for c in "${ds[@]}"; do python3 "$self/server/desktop_login.py" "$(cut -d: -f2 <<< "$c")" logout; done; offline
  since=$(date -u +%FT%TZ); docker restart "server-$slug" >/dev/null; ready "server-$slug" "$since"
  for i in "${!ds[@]}"; do login "$(cut -d: -f2 <<< "${ds[$i]}")" "${as[$i]}"; keep "$(cut -d: -f2 <<< "${ds[$i]}")" "${as[$i]}"; done
  echo "restarted: quest-requirements $(sed -n '/quest-requirements:/,/mode:/p' "$state/game.yml" | grep -o 'mode:.*')"
}
down() {
  unkeep   # no keeper logs in a desktop down stops
  (desktops_remove) || true   # a missing program still lets the containers go
  if [ "$(docker inspect -f '{{.State.Running}}' "server-$slug" 2>/dev/null)" = true ] && docker logs "server-$slug" 2>&1 | grep "Server ready in" >/dev/null; then offline; fi   # the server drops each disconnected character and saves it: RESUME starts there
  cs=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["containers"])' "$state/up.json" 2>/dev/null) || cs="server-$slug http-$slug token-$slug"   # a stack up before its record named its containers: the names every up gives
  docker rm -f $cs >/dev/null 2>&1 || true
  left=$(docker ps -a --format '{{.Names}}') || { echo "down: docker does not answer: the record stays" >&2; return 1; }
  left=$(grep -xF "${cs// /$'\n'}" <<< "$left" || true); [ -z "$left" ] || { echo "down: $left not removed: the record stays" >&2; return 1; }
  rm -f "$state/up.json"; $hd stack "$slug" --clear; echo "down"
}
image_key() {  # image_key IMAGE: its game.key and client.key carry the live pair's $modulus, else both named and refused
  local g c; g=$(docker run --rm --entrypoint cat "$1" /app/.data/game.key | modulus_of || true); c=$(docker run --rm --entrypoint cat "$1" /app/.data/client.key | sed -n 's/^Modulus: //p' || true)
  [ "$g" = "$modulus" ] && [ "$c" = "$modulus" ] || { echo "key: $1 carries game.key ${g:0:8} and client.key ${c:0:8}, not the live pair's ${modulus:0:8}"; return 4; }
  echo "key: the live pair's ${modulus:0:8}"
}
deploy() {  # staging's tree → the live test server; a failing step names itself and records the job failed
  set -E; trap 'echo "deploy of ${T:-$arg} failed: $BASH_COMMAND (exit $?)"; [ -z "${HD_KEY:-}" ] || $hd job deploy "$HD_KEY" fail "$BASH_COMMAND"' ERR
  arg=${TCOMMIT:-$arg}; "$self/build/build.sh" build staging "$arg"; T=${T:-$(git -C "$repo" rev-parse "$arg^{tree}")}
  slug=staging; state=$root/state/live; mkdir -p "$state"
  # the issuer (compose's ISSUER_DIR): its secret in the image's game.yml; the APK's sign-in and tokens for the tester account it has always played
  export ISSUER_DIR=$state/token; { docker run --rm --entrypoint cat "or:$T" /app/game.yml; echo; python3 "$self/server/issuer.py" key "$ISSUER_DIR"; } > "$state/game.yml"
  [ -s "$ISSUER_DIR/account" ] || echo tester > "$ISSUER_DIR/account"
  sed -E "s#^param=(11|20|22|28)=.*#param=\1=http://{{WORLD_HOST}}:${OPENRUNE_CENTRAL_HTTP_PORT:-8084}/#" "$self/server/jav_config.ws.template" > "$ISSUER_DIR/jav_config.ws.template"   # the APK's sign-in: Central's plain http (LOCAL_AUTH takes http; discovery answers the request's Host)
  # Central's sign-in for desktops, as up's SIGN_IN=central: the issuer's secret and account, https with its certificate, its own jav_config
  sic=1; http=${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}; tpl=$self/server/jav_config.ws.template; central_jav
  openssl pkcs12 -export -in "$ISSUER_DIR/tls.pem" -inkey "$ISSUER_DIR/tls.key" -passout pass:changeit -out "$state/central-tls.p12"
  [ -f "$state/key/game.key" ] && [ -f "$state/key/client.key" ] || { echo "no live key pair in $state/key"; return 4; }
  modulus=$(modulus_of < "$state/key/game.key")   # the live stack's pair, seeded once with the key every APK carries: no image passes its key to the next
  cat > "$state/Dockerfile" <<EOF
FROM or:$T
COPY --chown=1000:1000 key/game.key key/client.key /app/.data/
COPY --chown=1000:1000 game.yml /app/game.yml
COPY --chown=1000:1000 central-tls.p12 jav_config.ws /app/.data/
ENV OPENRUNE_SIGN_IN_TOKEN_SECRET="$(cat "$ISSUER_DIR/secret")" OPENRUNE_SIGN_IN_DEV_ACCOUNT="$(cat "$ISSUER_DIR/account")" OPENRUNE_HTTP_TLS_PORT=8443 \
    OPENRUNE_HTTP_TLS_KEYSTORE=/app/.data/central-tls.p12 OPENRUNE_HTTP_TLS_KEYSTORE_PASSWORD=changeit OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file:///app/.data/jav_config.ws
EOF
  $hd own image "osrs-openrune:$T" "staging@$T"   # released once staging moves on (the live tag keeps the running one)
  docker build -q -f "$state/Dockerfile" -t "osrs-openrune:$T" "$state" >/dev/null
  [ -n "$(docker ps -q -f name=^build-)" ] || docker builder prune -f >/dev/null 2>&1 || true   # no build live: the build cache goes
  image_key "osrs-openrune:$T"   # before its boot and before the live tag moves
  owner=staging@$T; [ -z "${HD_KEY:-}" ] || owner=job:deploy:$HD_KEY; $hd own container "boot-$T" "$owner"   # the boot check's container goes with the deploy, a kill included
  docker rm -f "boot-$T" >/dev/null 2>&1 || true
  docker run -d --name "boot-$T" --tmpfs /app/.data/postgres:uid=1000,gid=1000,mode=0700 "osrs-openrune:$T" >/dev/null
  ready "boot-$T" || { docker rm -f "boot-$T" >/dev/null; return 5; }; docker rm -f "boot-$T" >/dev/null
  # recreated, never restarted: a container's file bind mount does not outlive a WSL restart (Docker Desktop remounts it as a directory);
  # the sidecars and the issuer first, so a stack that cannot start leaves the game server as it was
  (cd "$compose_dir" && docker compose --env-file switch.env up -d --no-deps --force-recreate http http-desktop issuer) >/dev/null
  prev=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("tree","none"))' "$state/tree.json" 2>/dev/null || echo none)
  $hd own image "osrs-openrune:rollback-${prev:0:12}" "staging@$T"; docker tag "$live_image" "osrs-openrune:rollback-${prev:0:12}"; docker tag "osrs-openrune:$T" "$live_image"
  since=$(date -u +%FT%TZ)
  (cd "$compose_dir" && docker compose --env-file switch.env up -d --no-deps --force-recreate openrune) >/dev/null
  if ready osrs-openrune "$since"; then  # the record names the stack's containers: hd deploys again while one is not running
    python3 -c 'import json,sys;print(json.dumps({"tree":sys.argv[1],"commit":sys.argv[2],"heads":sys.argv[3].split(),"names":sys.argv[4].split(),"rollback":sys.argv[5],"modulus":sys.argv[6],"key":sys.argv[7],"containers":sys.argv[8].split()}))' \
      "$T" "$arg" "${HEADS:-}" "${NAMES:-}" "rollback-${prev:0:12}" "$modulus" "${KEY:-$T}" "$(cd "$compose_dir" && docker compose --env-file switch.env ps -a --format '{{.Name}}')" | atomic "$state/tree.json"; echo "live: $T"
    for c in osrs-openrune-http osrs-openrune-http-desktop; do python3 "$self/server/javcheck.py" "http://127.0.0.1:$(docker port "$c" 8080 | head -1 | cut -d: -f2)/jav_config.ws" || return 6; done
    python3 "$self/server/javcheck.py" "http://127.0.0.1:${OPENRUNE_CENTRAL_HTTP_PORT:-8084}/jav_config.ws" || return 6   # Central's, for desktops
    curl -fsS -o /dev/null --cacert "$ISSUER_DIR/tls.pem" "https://127.0.0.1:${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}/.well-known/openid-configuration" || return 6   # its sign-in over https
    curl -fsS -o /dev/null "http://127.0.0.1:${OPENRUNE_CENTRAL_HTTP_PORT:-8084}/.well-known/openid-configuration" || return 6   # and over http, the APK's
    [ -z "${HD_KEY:-}" ] || $hd job deploy "$HD_KEY" ok "live: $T"
  else
    docker tag "osrs-openrune:rollback-${prev:0:12}" "$live_image"; (cd "$compose_dir" && docker compose --env-file switch.env up -d --no-deps openrune) >/dev/null
    echo "deploy of $T failed: rolled back to ${prev:0:12}"; return 1
  fi
}
token() {  # [TOKEN]: the token the desktop's next login sends, or a valid one for the first desktop's account
  printf '%s\n' "${1:-$(python3 "$self/server/issuer.py" mint "$state/token" "$(account 1)")}" > "$state/token/token"; echo "token: $state/token/token"
}
log() {  # the container's whole log (up makes it fresh), never since an earlier call: a second search read only lines after the first
  c=server-$slug; [ "$slug" = live ] && c=osrs-openrune
  docker inspect "$c" > /dev/null 2>&1 || { echo "no container $c: up first" >&2; return 1; }   # no server is not a clean log
  docker logs "$c" 2>&1 | grep -E "${arg:-.}" || true; }
rsprox=${RSPROX:-$HOME/osrs-plugins-reverse/re/ref/rsprox/txt}
recordings() { grep -liE "$arg" "$rsprox"/*.txt 2>/dev/null | xargs -rn1 basename || echo "no transcript holds /$arg/"; }
transcribe() {  # a fresh RSProx home: one filter set, active, naming every PropertyFilter true; the index's settings and caches
  local cp=${RSPROX_RUNTIME:-$HOME/osrs-plugins-reverse/re/rsprox/build/osrs-test-runtime} h b id fail=0; h=$(mktemp -d); mkdir -p "$h/.rsprox/binary" "$h/.rsprox/filters"
  { printf 'version=0\ncreationtime=1\nname=All\nactive=true\n'
    javap -cp "$cp/shared-1.0.5.jar" net.rsprox.shared.filters.PropertyFilter | sed -nE 's/.*public static final net\.rsprox\.shared\.filters\.PropertyFilter ([A-Z0-9_]+);/\1=true/p'; } > "$h/.rsprox/filters/filters-all.txt"
  grep -q '=true' "$h/.rsprox/filters/filters-all.txt" || { echo "no PropertyFilter in $cp/shared-1.0.5.jar" >&2; rm -rf "$h"; return 1; }
  for d in settings caches; do [ -e "$rsprox/../home/.rsprox/$d" ] && ln -s "$(realpath "$rsprox/../home/.rsprox/$d")" "$h/.rsprox/$d"; done
  for b in $([ $# -gt 0 ] && printf "$rsprox/../bin/%s.bin " "$@" || echo "$rsprox"/../bin/*.bin); do id=$(basename "$b" .bin)
    gunzip -c "$b" > "$h/.rsprox/binary/$id.bin" 2>/dev/null || cp "$b" "$h/.rsprox/binary/$id.bin"
    java -Duser.home="$h" -cp "$cp/*" net.rsprox.proxy.cli.TranscribeCommandKt -name "$id" > "$h/$id.log" 2>&1 && [ -s "$h/.rsprox/binary/$id.txt" ] \
      && mv "$h/.rsprox/binary/$id.txt" "$rsprox/$id.txt" && echo "$id.txt" || { echo "$id: failed, $h/$id.log" >&2; fail=1; }
    rm -f "$h/.rsprox/binary/$id.bin"; done
  [ $fail = 1 ] || rm -rf "$h"; return $fail
}

live_desktop() {  # one desktop logged in on the LIVE stack (its Central's https jav_config and sign-in, game port and cache: srv), for the client track's probe; prints LIVE_DESKTOP <devtools port> <instance dir>
  srv=osrs-openrune; http=${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}; game=${OPENRUNE_GAME_PORT:-43594}; tok=true; sic=1; ca=$root/state/live/token/tls.pem
  modulus=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["modulus"])' "$root/state/live/tree.json"); devtoken=$(openssl rand -hex 16)
  devtools_jar; stack token="$devtoken" desktops= accounts=; trap 'live_desktop_down >&2 || true' ERR
  sign_in "$(account 1)"; desktop_start; stack desktops="$inst:$dt" accounts="$(account 1)"   # the account is this slug's own, never the tester's (the live Central's dev account)
  login_live=$(python3 "$self/server/desktop_login.py" "$dt" token) || true; echo "$login_live" >&2
  [[ $login_live == *LOGGED_IN* ]] || return 1
  trap - ERR; echo "LIVE_DESKTOP $dt $desk/run/${inst#desktop}"
}
live_desktop_down() { unkeep; desktops_remove; rm -f "$state/up.json"; $hd stack "$slug" --clear; echo "down"; }
case $verb in up|restart|down) [ "${DESKTOPS_LOCK:-}" = "$slug" ] || {   # one up, restart or down of a slug at a time: none acts on desktops another is starting or removing
    flock -n "$state/desktops.lock" true || echo "$verb $slug waits for the running up, restart or down of $slug" >&2
    DESKTOPS_LOCK=$slug exec flock -o "$state/desktops.lock" bash "$0" "$@"; } ;; esac   # -o: no desktop or keeper it starts holds the lock
case $verb in up|restart|down|deploy|log|recordings) "$verb" ;; live-desktop) live_desktop ;; live-desktop-down) live_desktop_down ;; token) token "$arg" ;;
  transcribe) transcribe "${@:3}" ;;
  *) echo "verbs: recipe build up restart down live-desktop live-desktop-down test spotless gate gate-ci ci-step tree deploy log recordings transcribe token" >&2; exit 2 ;; esac
