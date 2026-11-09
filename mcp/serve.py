#!/usr/bin/env python3
"""Runs one stdio MCP server, `mcp/serve.py <name>`, its command line mcp/servers.json's <name>, so a shipped mcp/ change
reaches a running session.

Each request from the session is passed to the server; once a file in mcp/ has changed (this script, the server's own
code, its data, its command line), the next request is held, the server's requests in flight are answered, the server is stopped and
this script runs again as itself: the new server is given the session's `initialize` (its answer dropped, the session
already has one), the held request and whatever was read past it, and the session is told its tools list changed.
"""
import json
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
REPLAY, QUIET = "MCP_SERVE_REPLAY", "MCP_SERVE_QUIET"   # the bytes the exec'd script starts from; the replayed initialize's id


def files():
    return sorted((f.name, f.stat().st_mtime_ns) for f in os.scandir(HERE) if f.is_file())


def main():
    seen, buf = files(), os.environ.pop(REPLAY, "").encode()
    init, live, quiet = [], set(), set()   # the session's initialize lines; ids in flight; ids whose answer is dropped
    done = threading.Condition()
    cmd = json.load(open(os.path.join(HERE, "servers.json")))[sys.argv[1]]
    cmd[0] = os.path.join(HERE, cmd[0])   # a relative program is this mcp/'s own: each checkout serves its own state root
    child = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def out():
        for line in child.stdout:
            try:
                i = json.loads(line).get("id")
            except (ValueError, AttributeError):
                i = None
            with done:
                if i in quiet:
                    quiet.discard(i)
                else:
                    os.write(1, line)
                live.discard(i)
                done.notify_all()
    threading.Thread(target=out, daemon=True).start()
    if QUIET in os.environ:   # a restart in a session: its tools may have changed
        quiet.add(json.loads(os.environ.pop(QUIET)))
        os.write(1, b'{"jsonrpc":"2.0","method":"notifications/tools/list_changed"}\n')
    while True:
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            try:
                msg = json.loads(line)
            except ValueError:
                msg = None
            msg = msg if isinstance(msg, dict) else {}
            if files() != seen:
                with done:
                    done.wait_for(lambda: not live)
                child.terminate(); child.wait()
                env = {**os.environ, REPLAY: b"".join(l + b"\n" for l in [*init, line]).decode() + buf.decode()}
                if init:
                    env[QUIET] = json.dumps(json.loads(init[0])["id"])
                os.execve(sys.executable, [sys.executable, os.path.join(HERE, "serve.py"), *sys.argv[1:]], env)
            if msg.get("method") in ("initialize", "notifications/initialized"):
                init.append(line)
            if "id" in msg and "method" in msg:
                with done:
                    live.add(msg["id"])
            child.stdin.write(line + b"\n"); child.stdin.flush()
        chunk = os.read(0, 65536)   # unbuffered: what the session sent past the held request stays for the exec'd script
        if not chunk:
            break
        buf += chunk
    child.stdin.close(); child.wait()


if __name__ == "__main__":
    main()
