#!/usr/bin/env python3
"""MCP stdio front for the devtools bridges, so a session connects whether or not a client is running.

  mcp/devtools_bridge.py <name> <backend> [args...]   (a backend http://127.0.0.1:<port>/mcp is POSTed to directly)

`initialize` is answered here; `tools/list` and every other request run `<backend> --call <method> <params>` one at a
time (the Android bridge takes it), or are POSTed to the desktop client's devtools endpoint (the bring-up's ports 7780+;
a tool's `port` argument names the client, and a call naming none is refused: one bridge serves every run; each call carries the
token of the up owning that desktop, the only caller its endpoint answers), so a client started after the session is used
on its next call. Desktop requests run each in its own thread: one session's runs share this process, and a call
answers as soon as its client does, never queued behind another run's long walk_to or wait_for.
A desktop walk_to walks to its tile at any distance in minimap clicks of at most STEP tiles (walk below).
A live tools list is cached in ~/.cache/osrs-devtools/tools-<name>.json; without a live client the cache, else
mcp/devtools-snapshot.json, answers it. A call with no client returns the backend's error, not a dead server.
A desktop call's answer names a dropped session (the client back at the login screen) after its own content.
Every request with an id is answered: the netstat probe is bounded, its start included, a desktop call is bounded whole
(ANSWER_WAIT past its own timeoutMs, its token read included), and an exception is an error.
"""
import json
import math
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request

NETSTAT = os.environ.get("WINDOWS_SYSTEM32", "/mnt/c/Windows/System32") + "/netstat.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = json.load(open(os.path.join(HERE, "devtools-snapshot.json")))
OUT = threading.Lock()


def reply(msg_id, **body):
    with OUT:
        print(json.dumps({"jsonrpc": "2.0", "id": msg_id, **body}, separators=(",", ":")), flush=True)


NETSTAT_WAIT = 20   # seconds netstat has to answer before the call connects without its word
ANSWER_WAIT = 30   # seconds past a call's own timeoutMs a desktop has to answer it: the plugin bounds its client-thread and frame waits at 5 s each


def listening(port):
    """netstat's word on whether a Windows process listens on the port: True, False, or None when it says nothing (it
    failed, or hung: a loaded host's WSL interop can block netstat.exe's start, the exec from /mnt/c, before any
    subprocess timeout applies, so the probe runs in its own thread and the call waits NETSTAT_WAIT at most)."""
    out = []
    def probe():
        try:
            ns = subprocess.run([NETSTAT, "-anp", "TCP"], capture_output=True, text=True, timeout=NETSTAT_WAIT)
        except (OSError, subprocess.TimeoutExpired):
            return
        if ns.returncode == 0:
            out.append(bool(re.search(rf":{port}\s+\S+\s+LISTENING", ns.stdout)))
    t = threading.Thread(target=probe, daemon=True)
    t.start()
    t.join(NETSTAT_WAIT)
    return out[0] if out else None


def token(port):
    """The devtools token of the up that owns the desktop instance on that port: the instance's owner file names its slug, and
    that change's up.json holds the token its endpoint requires (it answers no other caller)."""
    try:
        with open(f"{os.environ.get('DESKTOP_DIR', '/mnt/c/osrs-test')}/run/{int(port) - 7779}/owner") as f:
            slug = f.read().split(" ")[0]
        with open(os.path.join(os.path.dirname(HERE), "state", slug, "up.json")) as f:
            return json.load(f).get("token", "")
    except (OSError, ValueError):
        return ""


def post(url, method, params):
    """The desktop devtools endpoint's JSON-RPC reply (JSON or SSE framed); the tool's `port` argument picks the client."""
    port = (params.get("arguments") or {}).pop("port", None)
    if port:
        url = re.sub(r":\d+/", f":{int(port)}/", url, count=1)
    # mirrored WSL drops a connect to a closed Windows port instead of refusing it: ask netstat, as the bring-up does
    port = re.search(r":(\d+)/", url).group(1)
    if listening(port) is False:
        return {"error": {"code": -32000, "message": f"no desktop client listens on {url} (tools/track.sh up <slug> starts one)"}}
    # the whole call is bounded, its token read on /mnt/c included, not each socket read (a body read is many): a hung
    # client or a hung file read answers no call past it
    limit = ANSWER_WAIT + ((params.get("arguments") or {}).get("timeoutMs") or 0) / 1000
    out = []
    def fetch():
        try:
            req = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                         {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                                          "Authorization": f"Bearer {token(port)}"})
            with urllib.request.urlopen(req, timeout=limit) as r:
                out.append(r.read().decode())
        except urllib.error.HTTPError as e:   # the client's own error answer (401: another up's desktop), passed on as it said it
            out.append(e.read().decode())
        except OSError as e:
            out.append(e)
    t = threading.Thread(target=fetch, daemon=True)
    t.start()
    t.join(limit)
    if not out:
        return {"error": {"code": -32000, "message": f"the desktop client on {url} did not answer within {limit:g} s: it is hung (tools/track.sh restart or down/up <slug>)"}}
    if isinstance(out[0], OSError):
        return {"error": {"code": -32000, "message": f"no desktop client answers on {url} ({out[0]})"}}
    body = out[0]
    return json.loads(next((l[5:] for l in reversed(body.splitlines()) if l.startswith("data:")), body))


def backend(cmd, method, params):
    """The backend's JSON-RPC reply to one request, or an error when it printed none."""
    if cmd[0].startswith("http"):
        return post(cmd[0], method, params)
    p = subprocess.run([*cmd, "--call", method, json.dumps(params)], capture_output=True, text=True, timeout=240)
    for line in reversed(p.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    sys.stderr.write(p.stderr[-400:])
    return {"error": {"code": -32000, "message": (p.stderr.strip() or "no reply from the client bridge")[-300:]}}


STEP = 12   # tiles per click: inside the minimap circle (48 px from its centre) clear of its orbs
TOPLEVELS = (161, 164, 548)   # resizable classic, resizable modern, fixed: the interface holding the minimap


def text(r):
    """The JSON a devtools tool result carries; its error raised."""
    if "result" not in r or r["result"].get("isError"):
        raise RuntimeError(json.dumps(r.get("result") or r.get("error")))
    t = r["result"]["content"][0]["text"]
    return json.loads(t) if t[:1] in "{[" else t


def minimap(call):
    """The centre of the minimap's draw area: the visible component of content type 1338 (the client draws the map in it)."""
    for i in TOPLEVELS:
        try:
            cs = text(call("dump_interface", {"interfaceId": i}))["components"]
        except RuntimeError:
            continue
        for c in cs:
            if c.get("contentType") == 1338 and not c.get("hidden"):
                b = c["bounds"]
                return b["x"] + b["width"] // 2, b["y"] + b["height"] // 2
    raise RuntimeError("no minimap on screen")


def walk(cmd, params):
    """walk_to over any distance: clicks on the minimap of at most STEP tiles toward the tile, each until the player has
    moved closer to the clicked tile and is idle again. The client's own walk_to clicks the viewport, where a far tile lies
    under the chatbox or the side panels, or a minimap point the client cannot find; a minimap click reaches every direction."""
    a = params.get("arguments") or {}
    port = {"port": a["port"]} if "port" in a else {}
    call = lambda tool, args: backend(cmd, "tools/call", {"name": tool, "arguments": {**args, **port}})
    x, y, stuck, seen = a["x"], a["y"], False, []
    try:
        cx, cy = minimap(call)
        while True:
            st = text(call("get_client_state", {}))
            px, py = st["worldX"], st["worldY"]
            d = max(abs(x - px), abs(y - py))
            stuck = stuck or (px, py) in seen   # back on a tile the walk clicked from: going round in circles
            seen.append((px, py))
            if d == 0 or stuck:
                break
            k = min(1, STEP / d)
            sx, sy = px + round((x - px) * k), py + round((y - py) * k)
            # the tile's offset on the minimap: 4 px a tile (shortcut: the default minimap zoom; read the client's zoom
            # once a session changes it), turned by the camera yaw as the client turns the map (2048 units a turn)
            t = (st.get("cameraYaw") or 0) * math.pi / 1024
            dx, dy = (sx - px) * 4, (sy - py) * 4
            text(call("click", {"x": round(cx + dx * math.cos(t) + dy * math.sin(t)), "y": round(cy - (dy * math.cos(t) - dx * math.sin(t)))}))
            sd = max(abs(sx - px), abs(sy - py))
            stuck = not text(call("wait_for", {"condition": "at_tile", "x": sx, "y": sy, "range": sd - 1, "timeoutMs": 60000}))["met"]
            if not stuck:
                text(call("wait_for", {"condition": "idle", "timeoutMs": 60000}))
    except RuntimeError as e:
        return {"result": {"content": [{"type": "text", "text": f"walk_to {x},{y}: {e}"}], "isError": True}}
    msg = f"walk_to {x},{y}: at {px},{py}, {d} tiles away; clicked from " + " ".join(f"{p[0]},{p[1]}" for p in seen[:-1]) + (" (stuck: no closer, or back where it clicked before)" if stuck else "")
    return {"result": {"content": [{"type": "text", "text": msg}], **({"isError": True} if stuck else {})}}


DROPPED = ("LOGIN_SCREEN", "LOGIN_SCREEN_AUTHENTICATOR", "CONNECTION_LOST")


def session(cmd, port, r):
    """A desktop call's result, flagged when the session behind it has dropped (the server's idle logout, a disconnect):
    an empty answer from a logged-out client reads like an empty scene."""
    try:
        g = text(backend(cmd, "tools/call", {"name": "get_client_state", "arguments": dict(port)})).get("gameState")
    except (RuntimeError, AttributeError):
        return r
    if g not in DROPPED:
        return r
    note = {"type": "text", "text": f"desktop {port['port']} is at {g}: its session dropped; log it in again "
            "(tools/server/desktop_login.py <port> <account> <account>, the accounts in up.json)"}
    return {"result": {**r["result"], "content": [*r["result"].get("content", []), note]}}


def tools(name, cmd):
    cache = os.path.expanduser(f"~/.cache/osrs-devtools/tools-{name}.json")
    live = backend(cmd, "tools/list", {})
    if "result" in live:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w") as f:
            json.dump(live["result"], f)
        return live["result"]
    try:
        return json.load(open(cache))
    except (OSError, ValueError):
        return {"tools": SNAPSHOT["tools"]}


def listed(name, cmd):
    """The tools list; a desktop tool takes `port`, the devtools port of the client it acts on."""
    t = tools(name, cmd)
    if cmd[0].startswith("http"):
        for x in t.get("tools", []):
            x.setdefault("inputSchema", {"type": "object"}).setdefault("properties", {})["port"] = {
                "type": "integer", "description": "devtools port of your desktop (your change's up.json desktops); a call naming none is refused"}
            if x["name"] == "walk_to":
                x["description"] = ("Walk to the tile at world x,y on the current plane, at any distance: minimap clicks of at most "
                                    f"{STEP} tiles until the player stands on it; an error names where it stopped when a click moves it no closer.")
    return t


def handle(name, cmd, line):
    try:
        msg = json.loads(line)
    except ValueError:
        return
    if "id" not in msg:   # notifications need no answer
        return
    try:
        answer(name, cmd, msg)
    except Exception as e:   # every request is answered: an exception left in a call's thread would leave it hanging
        reply(msg["id"], error={"code": -32000, "message": f"{type(e).__name__}: {e}"})


def answer(name, cmd, msg):
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        reply(msg["id"], result={**SNAPSHOT["initialize"], "protocolVersion": params.get("protocolVersion")
                                 or SNAPSHOT["initialize"]["protocolVersion"]})
    elif method == "tools/list":
        reply(msg["id"], result=listed(name, cmd))
    elif method == "ping":
        reply(msg["id"], result={})
    else:
        desk = cmd[0].startswith("http") and method == "tools/call"
        port = {"port": a["port"]} if "port" in (a := params.get("arguments") or {}) else {}
        if desk and not port:   # the URL's port is any run's desktop, never the caller's by default
            return reply(msg["id"], error={"code": -32602, "message": "name your desktop's devtools `port` (your change's up.json desktops)"})
        r = walk(cmd, params) if desk and params.get("name") == "walk_to" else backend(cmd, method, params)
        if desk and params.get("name") != "get_client_state" and "result" in r:
            r = session(cmd, port, r)
        reply(msg["id"], **({"result": r["result"]} if "result" in r else {"error": r.get("error")}))


def main():
    name, cmd = sys.argv[1], sys.argv[2:]
    for line in sys.stdin:
        if line.strip():
            if cmd[0].startswith("http"):
                threading.Thread(target=handle, args=(name, cmd, line)).start()
            else:
                handle(name, cmd, line)


if __name__ == "__main__":
    main()
