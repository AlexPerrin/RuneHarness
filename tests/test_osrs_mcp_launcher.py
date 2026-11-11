import os, stat, subprocess, tempfile, unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "mcp", "osrs-mcp.sh")


class Launcher(unittest.TestCase):
    def test_the_server_gets_its_clients_stdin(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(f"{d}/src/tools/osrs-mcp/build/install/osrs-mcp/lib")
            docker = f"{d}/docker"   # stands in for docker: prints what its stdin carries
            open(docker, "w").write("#!/bin/sh\n[ \"$1\" = rm ] && exit 0\ncat\n")
            os.chmod(docker, os.stat(docker).st_mode | stat.S_IXUSR)
            env = {**os.environ, "SERVER_TOOLS": d, "PATH": f"{d}:{os.environ['PATH']}"}
            out = subprocess.run(["bash", SCRIPT], input="from-client\n", capture_output=True, text=True, env=env, timeout=20)
            self.assertEqual(out.stdout, "from-client\n")


if __name__ == "__main__":
    unittest.main()
