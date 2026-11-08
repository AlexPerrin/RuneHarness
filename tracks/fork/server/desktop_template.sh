#!/usr/bin/env bash
# desktop_template.sh DESK: the desktops' template (tracks/fork/track.md) from what this host holds: a Temurin 11 Windows JDK (a
# JRE lacks jdk.jartool, which RSProx's RuneLite launcher needs), the RSProx runtime the client repo built, and a first-run
# profile with the plugins that upload data off. Idempotent: `up` runs it when the JDK is missing, one at a time. It writes
# only under DESK; the first desktop of a fresh template downloads RuneLite, and each start copies the jars it verified back into the template home (track.sh desktop_start).
set -euo pipefail
desk=${1:?usage: desktop_template.sh DESK}; runtime=${RSPROX_RUNTIME:-$HOME/osrs-plugins-reverse/re/rsprox/build/osrs-test-runtime}
[ -f "$runtime/shared-1.0.5.jar" ] || { echo "no RSProx runtime at $runtime: the client repo's re/rsprox build" >&2; exit 1; }
mkdir -p "$desk"; exec 9> "${TMPDIR:-/tmp}/desktop-template.lock"; flock 9
if [ ! -x "$desk/jdk/bin/java.exe" ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  q='https://api.adoptium.net/v3/assets/latest/11/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse'
  read -r url sum < <(curl -fsSL "$q" | python3 -c 'import json,sys; p=json.load(sys.stdin)[0]["binary"]["package"]; print(p["link"], p["checksum"])')
  curl -fsSL -o "$tmp/jdk.zip" "$url"; echo "$sum  $tmp/jdk.zip" | sha256sum -c --quiet
  python3 -m zipfile -e "$tmp/jdk.zip" "$tmp/x"; rm -rf "$desk/jdk.tmp"; mv "$tmp"/x/jdk-* "$desk/jdk.tmp"
  find "$desk/jdk.tmp/bin" -name '*.exe' -exec chmod +x {} +; mv -T "$desk/jdk.tmp" "$desk/jdk"
fi
mkdir -p "$desk/rsprox/lib" "$desk/logs" "$desk/run" "$desk/home/.rsprox" "$desk/home/.rlcustom/sideloaded-plugins"
cp -u "$runtime/"*.jar "$desk/rsprox/lib/"
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
echo "template $desk: $(ls "$desk/rsprox/lib" | wc -l) RSProx jars, $("$desk/jdk/bin/java.exe" -version 2>&1 | head -1 | tr -d '\r')"
