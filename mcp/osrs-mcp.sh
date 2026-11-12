#!/usr/bin/env bash
# Launches OpenRune's osrs-mcp (OSRS Wiki, gameval and decoded-cache lookups; no live-server
# control) over stdio, inside Docker so OpenRune's code stays sandboxed. Only the jars, the
# gamevals, the decoded cache and game.yml are mounted, read-only; the server's keys are not.
# Build the jars first: openrune/scripts/openrune.sh gradle :tools:osrs-mcp:installDist --no-configuration-cache
set -euo pipefail
SRC="$(cd "${SERVER_TOOLS:-$HOME/src/openrune-work/server-tools}/src" && pwd)"
LIB="$SRC/tools/osrs-mcp/build/install/osrs-mcp/lib"
[[ -d $LIB ]] || { echo "osrs-mcp not built: see the header of $0" >&2; exit 1; }
# The container dies with this client: the server never exits on its own (it awaits cancellation, not stdin's end), so
# this shell ends it when the client's stdin closes (the client gone however it went) or when the shell is signalled.
# A client runs one: a start removes its predecessors (labelled with the client's pid: serve.py's parent, MCP_CLIENT).
name=osrs-mcp-$$ client=${MCP_CLIENT:-$PPID}
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap 'cleanup; exit 143' TERM INT HUP; trap cleanup EXIT
docker ps -aq --filter "label=osrs-mcp.client=$client" </dev/null | xargs -r docker rm -f >/dev/null 2>&1 || true
# a background job's stdin is /dev/null unless it is passed on (<&0); cat's end is the client's stdin closing
{ cat; cleanup; } <&0 | docker run --rm -i --init --name "$name" --label "osrs-mcp.client=$client" -u 1000:1000 \
    -v "$LIB":/w/lib:ro \
    -v "$SRC/.data/gamevals-binary":/w/.data/gamevals-binary:ro \
    -v "$SRC/.data/cache":/w/.data/cache:ro \
    -v "$SRC/game.yml":/w/game.yml:ro \
    --tmpfs /w/logs:uid=1000 \
    -e RSPS_ROOT=/w -e LOG_DIR=/w/logs -w /w \
    eclipse-temurin:21 java -cp '/w/lib/*' org.rsmod.tools.mcp.wiki.MainKt &
wait $!
