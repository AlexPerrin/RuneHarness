"""tracks/central/track.sh build: a Central clone whose gradlew is committed 100644 assembles, and a dev with no key builds its dev ref."""
import os, subprocess, tempfile, unittest
from pathlib import Path

TRACK = Path(__file__).resolve().parent.parent / "tracks/central/track.sh"


class Build(unittest.TestCase):
    def test_build_without_key_assembles_dev_ref_with_non_executable_gradlew(s):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); root, repo, bin = d / "root", d / "central", d / "bin"
            (root / "harness/changes").mkdir(parents=True); (root / "harness/changes/x.md").write_text("")
            git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
            repo.mkdir(); git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
            (repo / "gradlew").write_text("echo assembled \"$@\" > out\n"); os.chmod(repo / "gradlew", 0o644)   # upstream's mode
            git("add", "gradlew"); git("commit", "-qm", "c"); git("branch", "dev/x")
            (repo / "gradlew").write_text("exit 1\n"); git("commit", "-qam", "main moves on")   # the dev ref, not HEAD, is built
            bin.mkdir()   # a fake docker: the image's command run here, in the -w dir
            (bin / "docker").write_text('#!/usr/bin/env bash\nwhile [ "$1" != eclipse-temurin:21 ]; do [ "$1" = -w ] && cd "$2"; shift; done; shift\n[ "$1" = chown ] || exec "$@"\n')
            os.chmod(bin / "docker", 0o755)
            env = {k: v for k, v in os.environ.items() if not k.startswith("HD_") and k not in ("TCOMMIT", "SLUG", "T")}
            env.update(HD_ROOT=str(root), HD_REPO=str(repo), PATH=f"{bin}:{env['PATH']}")
            r = subprocess.run(["bash", str(TRACK), "build", "x"], env=env, capture_output=True, text=True)
            s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            s.assertIn("assembled", (repo / ".worktrees/x-build/out").read_text())


if __name__ == "__main__":
    unittest.main()
