import os, stat, subprocess, tempfile, unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "mcp", "osrs-mcp.sh")
# stands in for docker: logs its arguments; `run` is a server that echoes its stdin and, like osrs-mcp, never exits on
# its own; `rm -f` ends it; `ps` names the client's predecessor
DOCKER = """#!/bin/bash
echo "$*" >> "$D/log"
case $1 in
  run) echo $$ > "$D/server"; cat; exec sleep 1000 ;;
  rm) [ -f "$D/server" ] && kill "$(cat "$D/server")" 2>/dev/null; exit 0 ;;
  ps) echo old1 ;;
esac
"""


class Launcher(unittest.TestCase):
    def run_launcher(self, d):
        os.makedirs(f"{d}/src/tools/osrs-mcp/build/install/osrs-mcp/lib")
        open(f"{d}/docker", "w").write(DOCKER)
        os.chmod(f"{d}/docker", os.stat(f"{d}/docker").st_mode | stat.S_IXUSR)
        env = {**os.environ, "SERVER_TOOLS": d, "PATH": f"{d}:{os.environ['PATH']}", "D": d, "MCP_CLIENT": "4242"}
        p = subprocess.Popen(["bash", SCRIPT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
        out, _ = p.communicate("from-client\n", timeout=20)   # the client writes, then closes its end
        return p.pid, out, open(f"{d}/log").read().splitlines()

    def test_the_server_gets_its_clients_stdin_and_ends_when_it_closes(self):
        with tempfile.TemporaryDirectory() as d:
            pid, out, log = self.run_launcher(d)
            self.assertEqual(out, "from-client\n")
            self.assertIn(f"rm -f osrs-mcp-{pid}", log)   # the server ignores EOF: the launcher removed it

    def test_a_start_removes_the_clients_predecessor(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, log = self.run_launcher(d)
            self.assertEqual(log[:2], ["ps -aq --filter label=osrs-mcp.client=4242", "rm -f old1"])
            self.assertIn("--label osrs-mcp.client=4242", log[2])


if __name__ == "__main__":
    unittest.main()
