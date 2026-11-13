"""tracks/filestore/track.sh: a FileStore head whose gradlew is committed 100644 builds, and its publish is the Maven directory
the fork's build with FILESTORE resolves dev.or2 from (tracks/fork/build/build.sh filestore(), build/filestore.init.gradle)."""
import os, subprocess, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TRACK, BUILD = HERE / "tracks/filestore/track.sh", HERE / "tracks/fork/build/build.sh"


class Track(unittest.TestCase):
    def setUp(s):
        d = Path(tempfile.mkdtemp()); s.addCleanup(subprocess.run, ["rm", "-rf", str(d)])
        s.root, s.repo, bin = d / "root", d / "filestore", d / "bin"
        (s.root / "harness/changes").mkdir(parents=True); (s.root / "harness/changes/x.md").write_text("")
        (s.root / "harness/hd.py").write_text("import sys\nopen(sys.argv[0] + '.calls', 'a').write(' '.join(sys.argv[1:]) + '\\n')\n")   # a fake hd: the calls
        git = lambda *a: subprocess.run(["git", "-C", str(s.repo), *a], check=True, capture_output=True, text=True).stdout.strip()
        s.repo.mkdir(); git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
        # upstream's gradlew, mode 100644: publish writes the all POM where the build script reads HOSTING_DIRECTORY
        (s.repo / "gradlew").write_text('echo "$@" > out; [ "$*" = "${*%publish}" ] || { mkdir -p "$HOSTING_DIRECTORY/dev/or2/all/3.0.7"; touch "$HOSTING_DIRECTORY/dev/or2/all/3.0.7/all-3.0.7.pom"; }\n')
        os.chmod(s.repo / "gradlew", 0o644)
        git("add", "gradlew"); git("commit", "-qm", "c"); git("branch", "dev/x"); s.head = git("rev-parse", "HEAD")
        bin.mkdir()   # a fake docker: the container's -e and -w applied, its command run here
        (bin / "docker").write_text('#!/usr/bin/env bash\ncase " $* " in *" chown "*) exit 0 ;; esac\n'
                                    'while [[ $1 != eclipse-temurin:* ]]; do case $1 in -w) cd "$2" ;; -e) [[ $2 == *=* ]] && export "$2" ;; esac; shift; done; shift; exec "$@"\n')
        os.chmod(bin / "docker", 0o755)
        s.env = {k: v for k, v in os.environ.items() if not k.startswith("HD_") and k not in ("TCOMMIT", "SLUG", "T", "HEAD", "HOSTING_DIRECTORY")}
        s.env.update(HD_ROOT=str(s.root), HD_REPO=str(s.repo), PATH=f"{bin}:{s.env['PATH']}")

    def test_build_assembles_with_a_non_executable_gradlew(s):
        r = subprocess.run(["bash", str(TRACK), "build", "x"], env=s.env, capture_output=True, text=True)
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s.assertIn("assemble", (s.repo / ".worktrees/x-build/out").read_text())

    def test_the_fork_build_resolves_filestore_from_the_heads_publish(s):
        fn = lambda name, src=BUILD.read_text(): f"{name}() {{" + src.split(f"\n{name}() {{")[1].split("\n}")[0] + "\n}"
        script = "\n".join(["set -euo pipefail", f"slug=x; self={BUILD.parent}; hd=:", fn("filestore"), "filestore", 'echo "$fdir"; printf "%s\\n" "${fvols[@]}"'])
        r = subprocess.run(["bash", "-c", script], env={**s.env, "FILESTORE": f"{s.repo}:{s.head}"}, capture_output=True, text=True)
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m2 = s.repo / ".worktrees/x-filestore/.m2"
        s.assertTrue((m2 / "dev/or2/all/3.0.7/all-3.0.7.pom").exists())   # the head published, not included (its accessors clash with the fork's)
        s.assertIn(f"{m2}\n", r.stdout); s.assertIn(f"{m2}:{m2}:ro", r.stdout)   # FDIR is that directory, mounted read-only

    def test_up_builds_on_staging_and_passes_the_desktop_count_on(s):   # every fork up logs in by token
        d = s.root.parent; t = d / "tracks"; (t / "filestore").mkdir(parents=True); (t / "fork").mkdir()
        (t / "filestore/track.sh").write_text(TRACK.read_text())   # beside a fake fork track: its calls and the env they carry
        (t / "fork/track.sh").write_text('echo "$1 $3 TCOMMIT=$TCOMMIT CENTRAL=${CENTRAL:-} FILESTORE=$FILESTORE" >> "$(dirname "$0")/calls"\n')
        repos = {}
        for name in ("fork", "central"):
            r = repos[name] = d / name; r.mkdir(); g = lambda *a: subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True, text=True).stdout.strip()
            g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t"); g("commit", "-q", "--allow-empty", "-m", "c"); g("branch", "staging")
        sha = lambda r: subprocess.run(["git", "-C", str(r), "rev-parse", "staging"], capture_output=True, text=True).stdout.strip()
        for n, mode in (("1", "1"), ("", ""), ("2", "2")):
            (t / "fork/calls").unlink(missing_ok=True)
            r = subprocess.run(["bash", str(t / "filestore/track.sh"), "up", "x", *([n] if n else [])], capture_output=True, text=True,
                               env={**s.env, "FORK_REPO": str(repos["fork"]), "CENTRAL_REPO": str(repos["central"])})
            s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            build, up = (t / "fork/calls").read_text().splitlines()
            s.assertEqual(build, f"build {sha(repos['fork'])} TCOMMIT={sha(repos['fork'])} CENTRAL={repos['central']}:{sha(repos['central'])} FILESTORE={s.repo}:{s.head}")
            s.assertTrue(up.startswith(f"up {mode} TCOMMIT"), up)

    def test_test_gives_the_tools_tests_the_fork_staging_revisions_cache(s):   # upstream's tools tests read ../data/cache, git-ignored
        fork = s.root.parent / "fork"; fork.mkdir(); g = lambda *a: subprocess.run(["git", "-C", str(fork), *a], check=True, capture_output=True, text=True).stdout.strip()
        g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t"); (fork / "game.example.yml").write_text("revision: 241\n")
        g("add", "."); g("commit", "-qm", "c"); g("branch", "staging"); gk = g("rev-parse", "staging:game.example.yml")[:12]
        copy = s.repo / "copy"; (copy / "data/cache").mkdir(parents=True); (copy / "data/cache/stale").write_text("")
        (copy / "gradlew").write_text('echo "$@" > out\n')
        bin = Path(s.env["PATH"].split(":")[0])   # the fake docker: the store copy logged, failing with NOSTORE
        (bin / "docker").write_text((bin / "docker").read_text().replace('case " $* " in', f'case " $* " in *" /store/"*) echo "$*" >> {s.root}/store; [ -z "${{NOSTORE:-}}" ]; exit ;;', 1))
        env = {**s.env, "FORK_REPO": str(fork), "BUILD": str(copy)}
        r = subprocess.run(["bash", str(TRACK), "test", "x"], env=env, capture_output=True, text=True)
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        call = (s.root / "store").read_text()
        s.assertIn(f"-v or-cache-store-{gk}:/store:ro -v {copy}/data/cache:/cache ", call)   # copied from the store, never mounted into the tests
        s.assertTrue(call.rstrip().endswith(f"cp -a /store/g-{gk}/.data/cache/LIVE/. /cache/"), call)
        s.assertEqual(list((copy / "data/cache").iterdir()), [])   # an earlier cache gone
        s.assertIn("test", (copy / "out").read_text())
        (copy / "out").unlink()
        r = subprocess.run(["bash", str(TRACK), "test", "x"], env={**env, "NOSTORE": "1"}, capture_output=True, text=True)
        s.assertEqual(r.returncode, 1); s.assertIn(f"no cache of revision {gk}", r.stderr); s.assertFalse((copy / "out").exists())


if __name__ == "__main__":
    unittest.main()
