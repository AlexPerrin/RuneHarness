#!/usr/bin/env python3
"""MCP stdio front for the devtools bridges, so a session connects whether or not a client is running.

  mcp/devtools_bridge.py <name> <backend> [args...]   (a backend http://127.0.0.1:<port>/mcp is POSTed to directly)

`initialize` is answered here; `tools/list` and every other request run `<backend> --call <method> <params>` one at a
time (the Android bridge takes it), or are POSTed to the desktop client's devtools endpoint (the bring-up's ports 7780+;
a tool's optional `port` argument picks the client, default the URL's), so a client started after the session is used
on its next call.
A live tools list is cached in ~/.cache/osrs-devtools/tools-<name>.json; without a live client the cache, else
mcp/devtools-snapshot.json, answers it. A call with no client returns the backend's error, not a dead server.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

NETSTAT = os.environ.get("WINDOWS_SYSTEM32", "/mnt/c/Windows/System32") + "/netstat.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = json.load(open(os.path.join(HERE, "devtools-snapshot.json")))


def reply(msg_id, **body):
    print(json.dumps({"jsonrpc": "2.0", "id": msg_id, **body}, separators=(",", ":")), flush=True)


def post(url, method, params):
    """The desktop devtools endpoint's JSON-RPC reply (JSON or SSE framed); the tool's `port` argument picks the client."""
    port = (params.get("arguments") or {}).pop("port", None)
    if port:
        url = re.sub(r":\d+/", f":{int(port)}/", url, count=1)
    # mirrored WSL drops a connect to a closed Windows port instead of refusing it: ask netstat, as the bring-up does
    port = re.search(r":(\d+)/", url).group(1)
    try:
        ports = subprocess.run([NETSTAT, "-anp", "TCP"], capture_output=True, text=True).stdout
    except OSError:
        ports = ""
    if not re.search(rf":{port}\s+\S+\s+LISTENING", ports):
        return {"error": {"code": -32000, "message": f"no desktop client listens on {url} (tools/track.sh up <slug> starts one)"}}
    req = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                 {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            body = r.read().decode()
    except OSError as e:
        return {"error": {"code": -32000, "message": f"no desktop client answers on {url} ({e})"}}
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
    """The tools list; a desktop tool takes an optional `port`, the devtools port of the client it acts on."""
    t = tools(name, cmd)
    if cmd[0].startswith("http"):
        for x in t.get("tools", []):
            x.setdefault("inputSchema", {"type": "object"}).setdefault("properties", {})["port"] = {
                "type": "integer", "description": "devtools port of the desktop client (up.json clients), default " + re.search(r":(\d+)/", cmd[0]).group(1)}
    return t


def handle(name, cmd, line):
    try:
        msg = json.loads(line)
    except ValueError:
        return
    if "id" not in msg:   # notifications need no answer
        return
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        reply(msg["id"], result={**SNAPSHOT["initialize"], "protocolVersion": params.get("protocolVersion")
                                 or SNAPSHOT["initialize"]["protocolVersion"]})
    elif method == "tools/list":
        reply(msg["id"], result=listed(name, cmd))
    elif method == "ping":
        reply(msg["id"], result={})
    else:
        r = backend(cmd, method, params)
        reply(msg["id"], **({"result": r["result"]} if "result" in r else {"error": r.get("error")}))


def main():
    name, cmd = sys.argv[1], sys.argv[2:]
    for line in sys.stdin:
        if line.strip():
            handle(name, cmd, line)


if __name__ == "__main__":
    main()
