#!/usr/bin/env bash
# desktop_template.sh DESK COMMIT: the desktops' template (tracks/fork/track.md): a Temurin 11 Windows JDK (a JRE lacks
# jdk.jartool, which RSProx's RuneLite launcher needs), RSProx at blurite/rsprox COMMIT built in docker into DESK/rsprox/lib-<COMMIT12>
# (a new lib beside the old, whose jars running desktops hold open), and a first-run
# profile with the plugins that upload data off. Idempotent: `up` runs it when the JDK is missing, one at a time. It writes
# only under DESK; the first desktop of a fresh template downloads RuneLite, and each start copies the jars it verified back into the template home (track.sh desktop_start).
set -euo pipefail
desk=${1:?usage: desktop_template.sh DESK COMMIT}; commit=${2:?usage: desktop_template.sh DESK COMMIT}; lib=$desk/rsprox/lib-${commit:0:12}; self=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$desk"; exec 9> "${TMPDIR:-/tmp}/desktop-template.lock"; flock 9
if [ ! -x "$desk/jdk/bin/java.exe" ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  q='https://api.adoptium.net/v3/assets/latest/11/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse'
  read -r url sum < <(curl -fsSL "$q" | python3 -c 'import json,sys; p=json.load(sys.stdin)[0]["binary"]["package"]; print(p["link"], p["checksum"])')
  curl -fsSL -o "$tmp/jdk.zip" "$url"; echo "$sum  $tmp/jdk.zip" | sha256sum -c --quiet
  python3 -m zipfile -e "$tmp/jdk.zip" "$tmp/x"; rm -rf "$desk/jdk.tmp"; mv "$tmp"/x/jdk-* "$desk/jdk.tmp"
  find "$desk/jdk.tmp/bin" -name '*.exe' -exec chmod +x {} +; mv -T "$desk/jdk.tmp" "$desk/jdk"
fi
mkdir -p "$desk/rsprox" "$desk/logs" "$desk/run" "$desk/home/.rsprox" "$desk/home/.rlcustom/sideloaded-plugins"
if [ ! -d "$lib" ]; then   # upstream's Gradle build in a JDK 11 container, its runtime classpath exported by rsprox-runtime.init.gradle.kts
  src=$(mktemp -d); trap 'docker run --rm -v "$src:/s" eclipse-temurin:11 rm -rf /s/build /s/.gradle >/dev/null 2>&1; rm -rf "$src"' EXIT
  curl -fsSL "https://codeload.github.com/blurite/rsprox/tar.gz/$commit" | tar -xz -C "$src" --strip-components=1
  docker run --rm -v "$src:/src" -v "$self/rsprox-runtime.init.gradle.kts:/init.gradle.kts:ro" -v rsprox-gradle:/root/.gradle -w /src eclipse-temurin:11 \
    bash -c "./gradlew --no-daemon -q --init-script /init.gradle.kts assemble osrsTestRuntime && chown -R $(id -u):$(id -g) build" >&2
  rm -rf "$lib.tmp"; cp -r "$src/build/osrs-test-runtime" "$lib.tmp"; mv -T "$lib.tmp" "$lib"
fi
[ -d "$desk/home/.rlcustom/profiles2" ] || cat > "$desk/home/.rlcustom/settings.properties" <<'PROPS'
runelite.discordplugin=false
runelite.loottrackerplugin=false
runelite.xptrackerplugin=false
runelite.xpupdaterplugin=false
runelite.crowdsourcingplugin=false
runelite.grandexchangeplugin=false
runelite.chatcommandsplugin=false
runelite.hiscoreplugin=false
runelite.worldhopperplugin=false
runelite.defaultworldplugin=false
runelite.twitchplugin=false
runelite.partyplugin2=false
runelite.openrunedevtoolsplugin=true
openrunedevtools.autoUpdate=false
openrunedevtools.port=7780
PROPS
echo "template $desk: $(ls "$lib" | wc -l) RSProx jars, $("$desk/jdk/bin/java.exe" -version 2>&1 | head -1 | tr -d '\r')"
