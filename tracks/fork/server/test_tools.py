"""The contract's script rows against a throwaway git repo: python3 -m unittest tools/server/test_tools.py"""
import json, os, re, shutil, subprocess, sys, tempfile, threading, time, unittest, urllib.parse
from unittest import mock
from pathlib import Path
SUITE_TMP = tempfile.TemporaryDirectory(prefix="tools-suite-", ignore_cleanup_errors=True)   # every temp dir of these tests and of each process they
tempfile.tempdir = os.environ["TMPDIR"] = SUITE_TMP.name                          # start (mktemp) is under it, removed at the end, a failed test's too

for k in [k for k in os.environ if k.startswith("HD_")] + ["SLUG", "HEAD", "T", "G", "TCOMMIT", "BASE", "EVIDENCE", "BUILD", "CLONE", "TRACK", "PUBLIC_BRANCH", "PR", "PINS", "CENTRAL", "TOOLS", "NAMES", "ROWS", "TOOLS_ROOT", "TOOLS_SRC"]:
    os.environ.pop(k, None)   # hd's env of the gate that runs these tests is not the tests': its HD_TREE named another tree's commit in every build
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SRC = "\n".join((HERE.parent / f).read_text() for f in ("track.sh", "build/build.sh", "gate/gate.sh"))   # the track script and the code a build and a gate run
JAV = "central_jav() {" + SRC.split("\ncentral_jav() {")[1].split(" }\n")[0] + " }"   # up's and deploy's fill of Central's jav_config


def git(repo, *a, env=None):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, env={**os.environ, **(env or {})}).stdout.strip()


def change(root, slug):
    p = Path(root) / "harness/changes" / f"{slug}.md"; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("")
    (Path(root) / "harness").mkdir(exist_ok=True)   # a fake hd: stack and job record nothing; candidate answers the snapshot's tree and commit
    (Path(root) / "harness/hd.py").write_text("import os, subprocess, sys\nif sys.argv[1] == 'candidate':\n    snap = sys.argv[sys.argv.index('--head') + 1]\n"
                                              "    print(subprocess.run(['git', '-C', os.environ.get('CLONE', '.'), 'rev-parse', snap + '^{tree}'], capture_output=True, text=True).stdout.strip(), snap)\n")


class Slug(unittest.TestCase):
    def test_a_pattern_in_the_slug_place_is_refused_before_any_state(s):
        root = Path(tempfile.mkdtemp())
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "log", "Have a nice day"], capture_output=True, text=True, env={**os.environ, "HD_ROOT": str(root)})
        s.assertEqual(r.returncode, 2); s.assertIn('no change or goal "Have a nice day"', r.stderr)
        s.assertFalse((root / "state").exists())
        shutil.rmtree(root)



class Log(unittest.TestCase):
    def setUp(s):
        s.root = Path(tempfile.mkdtemp()); change(s.root, "x"); (s.root / "bin").mkdir()

    def tearDown(s):
        shutil.rmtree(s.root)

    def run_log(s, docker, pattern):  # track.sh log against a fake docker on PATH, one state dir across calls
        (s.root / "bin/docker").write_text("#!/bin/sh\n" + docker); (s.root / "bin/docker").chmod(0o755)
        return subprocess.run(["bash", str(HERE.parent / "track.sh"), "log", "x", pattern], capture_output=True, text=True,
                              env={**os.environ, "HD_ROOT": str(s.root), "PATH": f"{s.root / 'bin'}:{os.environ['PATH']}"})

    def test_every_search_reads_the_running_servers_lines(s):  # a '.' search after an ERROR search printed nothing: a marker advanced by each call
        docker = 'case $1 in inspect) exit 0;; logs) [ "$2" = --since ] && exit 0; printf "12:00 [INFO] - Server ready in 8s\\n12:01 [WARN] - slow tick\\n";; esac\n'
        for pattern in ("ERROR|WARN", ".", "."):
            r = s.run_log(docker, pattern); s.assertEqual(r.returncode, 0, r.stderr)
            s.assertIn("slow tick", r.stdout)
        s.assertIn("Server ready", s.run_log(docker, ".").stdout)

    def test_no_container_is_an_error_not_a_clean_log(s):
        r = s.run_log("exit 1\n", "ERROR")
        s.assertEqual(r.returncode, 1); s.assertIn("no container server-x", r.stderr)

class Transcribe(unittest.TestCase):
    def test_every_filter_is_on_and_recordings_finds_the_packet(s):  # RSProx's default filters hid clan packets: recordings CLANSETTINGS found nothing
        import gzip
        root = Path(tempfile.mkdtemp()); change(root, "x"); fake = root / "fake"; fake.mkdir()
        for d in ("txt", "bin"): (root / "rsprox" / d).mkdir(parents=True)
        (root / "rsprox/bin/7.bin").write_bytes(gzip.compress(b"rec"))
        (fake / "javap").write_text("#!/bin/sh\nprintf '  public static final net.rsprox.shared.filters.PropertyFilter CLANSETTINGS_FULL;\\n  public static final net.rsprox.shared.filters.PropertyFilter IF_BUTTON;\\n'\n")
        # the fake transcriber writes its input and the active filter set: the transcript holds a packet only when its filter is true
        (fake / "java").write_text('#!/bin/sh\nh=${1#-Duser.home=}; b=$h/.rsprox/binary; { cat "$b/7.bin"; echo; cat "$h"/.rsprox/filters/*; grep -q "CLANSETTINGS_FULL=true" "$h"/.rsprox/filters/* && echo "clansettings_full"; } > "$b/7.txt"\n')
        for f in ("javap", "java"): (fake / f).chmod(0o755)
        env = {**os.environ, "HD_ROOT": str(root), "RSPROX": str(root / "rsprox/txt"), "PATH": f"{fake}:{os.environ['PATH']}"}
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "transcribe", "x"], capture_output=True, text=True, env=env)
        s.assertEqual(r.returncode, 0, r.stderr)
        t = (root / "rsprox/txt/7.txt").read_text()
        s.assertEqual(t, "rec\nversion=0\ncreationtime=1\nname=All\nactive=true\nCLANSETTINGS_FULL=true\nIF_BUTTON=true\nclansettings_full\n")
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "recordings", "x", "CLANSETTINGS"], capture_output=True, text=True, env=env)
        s.assertEqual(r.stdout, "7.txt\n")
        shutil.rmtree(root)


class NoPowerShell(unittest.TestCase):
    def test_windows_programs_run_from_bash_by_absolute_path(s):  # Windows refuses unsigned .ps1 from the UNC path; a lost PATH loses bare .exe names
        s.assertEqual(list(HERE.parent.rglob("*.ps1")), [])
        src = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
        s.assertNotIn("powershell", src.lower())
        import re
        s.assertEqual(re.findall(r'(?:^|[\s(|;&])[\w.-]+\.exe\b', src), [])


class CacheStore(unittest.TestCase):
    def test_a_store_hit_restores_every_output_of_the_cache_step(s):  # a hit without api/generated fails :api:music:compileKotlin
        line = next(l for l in SRC.splitlines() if "cp -a --parents" in l and "$s.tmp/" in l)
        for out in (".data/cache ", ".data/gamevals ", ".data/gamevals-binary ", "api/generated "):
            s.assertIn(out, line)


class GateSha(unittest.TestCase):
    def test_the_same_t_pushes_the_same_sha(s):  # osrs-harness sweep-85: each gate's commit-tree had a new date, so an unchanged T re-ran fork CI
        d = tempfile.mkdtemp(); repo = f"{d}/r"; os.makedirs(f"{repo}/.github/workflows")
        for f in ("ci", "format"):
            Path(f"{repo}/.github/workflows/{f}.yml").write_text("steps:\n      - uses: gradle/actions/setup-gradle@v4\n")
        git(d, "init", "-q", repo); git(repo, "add", "-A"); git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "t")
        fn = SRC.split("\ngate_sha() {")[1].split("\n}\ngame_data()")[0]
        sh = f"game_data() {{ cat <<< \"$1\"; }}\ngate_sha() {{{fn}\n}}\ngate_sha"
        env = {**os.environ, "repo": repo, "state": d, "TCOMMIT": git(repo, "rev-parse", "HEAD"), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        run = lambda: subprocess.run(["bash", "-c", sh], capture_output=True, text=True, env={**env, "GIT_COMMITTER_DATE": str(time.time_ns())[:10] + " +0000"})
        a = run(); time.sleep(1.1); b = run()
        s.assertEqual(a.returncode, 0, a.stderr); s.assertRegex(a.stdout.strip(), r"^[0-9a-f]{40}$"); s.assertEqual(a.stdout, b.stdout)


class Central(unittest.TestCase):
    def test_build_and_test_include_that_central_at_its_commit(s):  # a server change needing a Central change built, then tested, against the published dev.or2
        src = SRC
        c = src.split("\ncentral() {")[1].split("\n}")[0]
        s.assertIn('read -r cpath ccommit <<< "$CENTRAL"', c)
        s.assertIn('worktree add -q --detach "$cdir" "$ccommit"', c)
        s.assertIn('-v "$cdir:$cdir"', c)
        for verb in ("build", "gradle_check"):
            b = src.split(f"\n{verb}() {{")[1].split("\n}")[0]
            for want in ("central;", '"${cvols[@]}"', 'CDIR="$cdir"', "${CDIR:+ --init-script /central.init.gradle}"):
                s.assertIn(want, b, verb)
        init = (HERE.parent / "build/central.init.gradle").read_text()  # openrune-central is named unlike its project: substituted explicitly
        for m, p in (("openrune-central", "central-app"), ("central-common", "central-common"), ("central-worldlink", "central-worldlink")):
            s.assertIn(f"substitute module('dev.or2:{m}') using project(':{p}')", init)

    def test_a_composite_image_tag_is_a_docker_tag_and_the_pass_key(s):  # run 41: or:<T>+c<tree12> refused by docker build (invalid reference format)
        sys.path.insert(0, str(HERE.parents[2] / "harness")); import decide
        central = tempfile.mkdtemp(); git(central, "init", "-q"); (Path(central) / "a").write_text("a")
        git(central, "add", "."); git(central, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "c"); c = git(central, "rev-parse", "HEAD")
        root = tempfile.mkdtemp(); change(root, "s1")
        r = subprocess.run(["bash", "-c", '. "$1" tree s1 && composite_suffix', "_", str(HERE.parent / "build/build.sh")], capture_output=True, text=True,
                           env={**os.environ, "HD_ROOT": root, "CLONE": central, "CENTRAL": f"{central}:{c}"})
        s.assertEqual(r.returncode, 0, r.stderr)
        T = "a" * 40 + r.stdout.strip()
        s.assertEqual(T, decide.built({"tree": "a" * 40, "composite_json": json.dumps({"central": {"head": c, "tree": git(central, "rev-parse", f"{c}^{{tree}}")}})}))
        s.assertRegex(T, r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")   # docker's tag grammar
        for d in (central, root): shutil.rmtree(d)

    def test_a_dev_tree_keeps_the_build_version(s):  # alert 74: tree()'s read of hd candidate --composite and composite_suffix's loop set v, so every dev build printed 'cached'
        central = tempfile.mkdtemp(); git(central, "init", "-q"); (Path(central) / "a").write_text("a")
        git(central, "add", "."); git(central, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "c"); c = git(central, "rev-parse", "HEAD")
        git(central, "worktree", "add", "-q", str(Path(central) / ".worktrees/s1"))   # the dev's working copy
        root = tempfile.mkdtemp(); change(root, "s1")
        hd = Path(root) / "harness/hd.py"; hd.write_text(f"import sys\nif '--composite' in sys.argv: print('CENTRAL={central}:{c}'); sys.exit()\n" + hd.read_text())
        r = subprocess.run(["bash", "-c", '. "$1" tree s1 && v0=$v && tree && [ "$v" = "$v0" ] && [ -n "$CENTRAL" ] && echo "$v $T"', "_", str(HERE.parent / "build/build.sh")],
                           capture_output=True, text=True, env={**os.environ, "HD_ROOT": root, "CLONE": central, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s.assertRegex(r.stdout, r"^2 [0-9a-f]{40}_c[0-9a-f]{12}\n$")
        for d in (central, root): shutil.rmtree(d)


class BuildLock(unittest.TestCase):
    def test_a_second_build_of_a_slug_waits_then_reuses_the_image(s):  # a dev's build was refused: the pass's build-<slug> container was running
        b = SRC.split("\nbuild() {")[1].split("\n}")[0]
        s.assertIn('{ flock 9; build_locked; } 9> "$state/build.lock"', b)
        s.assertTrue(SRC.split("\nbuild_locked() {")[1].lstrip().startswith('if [ "$(docker image inspect -f \'{{index .Config.Labels "hd.build"}}\' "or:$T"'))

    def test_the_lock_ends_with_the_build(s):  # a gate's 20 minutes of gate-ci held it: rekeyed builds and a dev's build waited behind it
        d = tempfile.mkdtemp(); line = next(l for l in SRC.splitlines() if l.startswith("build() {"))
        r = subprocess.run(["bash", "-c", f"set -e; state={d}; tree() {{ :; }}; build_locked() {{ flock -n {d}/build.lock true && exit 3; :; }}\n{line}\nbuild; flock -n {d}/build.lock echo free"],
                           capture_output=True, text=True)
        s.assertEqual((r.returncode, r.stdout.strip()), (0, "free"))   # held during build_locked, free once build returns, the shell still alive
        shutil.rmtree(d)


class BuildAttempts(unittest.TestCase):
    def setUp(s):
        s.root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, s.root); change(s.root, "x"); (s.root / "bin").mkdir()
        s.repo = s.root / "repo"; s.repo.mkdir(); git(s.repo, "init", "-q"); (s.repo / "game.example.yml").write_text("game: {}\n"); (s.repo / "settings.gradle.kts").write_text(""); (s.repo / "or-cache").mkdir(); (s.repo / "or-cache/x").write_text("")
        git(s.repo, "add", "-A"); git(s.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "t"); s.tc = git(s.repo, "rev-parse", "HEAD")
        # docker: no image cached, the Gradle container fails
        (s.root / "bin/docker").write_text('#!/bin/sh\ncase "$*" in "image inspect"*) exit 1;; *"--name build-x"*) echo "gradle: boom $$"; exit 1;; esac\n'); (s.root / "bin/docker").chmod(0o755)

    def build(s):
        return subprocess.run(["bash", str(HERE.parent / "track.sh"), "build", "x", s.tc], capture_output=True, text=True,
                              env={**os.environ, "HD_ROOT": str(s.root), "CLONE": str(s.repo), "PATH": f"{s.root / 'bin'}:{os.environ['PATH']}", "CENTRAL": ""})

    def test_a_host_fault_records_no_result_and_a_tree_failure_records_its_fail(s):  # osrs-harness sweep-18 N7: docker's 'cannot allocate memory' was recorded as the head's build FAIL
        r = s.build(); b = json.loads((s.root / "state/x/build.json").read_text())
        s.assertEqual((r.returncode, b["ok"]), (1, False)); s.assertIn("gradle: boom", b["detail"])   # the tree's own failure: ok:false
        (s.root / "state/x/build.json").unlink()
        for fault in ("docker: Error response from daemon: cannot allocate memory.", "write /x: no space left on device",
                      'docker: Error response from daemon: Conflict. The container name "/build-x" is already in use by container 26ec02.'):
            (s.root / "bin/docker").write_text(f'#!/bin/sh\necho "$*" >> {s.root}/calls\ncase "$*" in "image inspect"*) exit 1;; *"--name build-x"*) echo \'{fault}\' >&2; exit 125;; esac\n')
            r = s.build()
            s.assertEqual(r.returncode, 75, r.stdout + r.stderr); s.assertIn("the host's fault", r.stdout)
            s.assertFalse((s.root / "state/x/build.json").exists())             # no result: the pass runs it again
        calls = (s.root / "calls").read_text().splitlines()
        s.assertLess(calls.index("rm -f build-x"), next(i for i, c in enumerate(calls) if "--name build-x" in c))   # a killed build's leftover container is removed first
        s.assertIn("--cpus=4 --memory=5g", next(c for c in calls if "--name build-x" in c))

    def test_a_stopped_build_removes_its_container(s):  # osrs-harness answer-4: a stopped deploy's build-integration ran on; the next two failed on its name
        import signal, time
        calls = s.root / "calls"
        (s.root / "bin/docker").write_text(f'#!/bin/sh\necho "$*" >> {calls}\ncase "$*" in "image inspect"*) exit 1;; *"--name build-x"*) exec sleep 60;; esac\n')
        p = subprocess.Popen(["bash", str(HERE.parent / "track.sh"), "build", "x", s.tc], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True,
                             env={**os.environ, "HD_ROOT": str(s.root), "CLONE": str(s.repo), "PATH": f"{s.root / 'bin'}:{os.environ['PATH']}", "CENTRAL": ""})
        while p.poll() is None and "--name build-x" not in (calls.read_text() if calls.exists() else ""):
            time.sleep(0.05)   # a build that ends first fails the test below instead of holding the suite
        os.killpg(p.pid, signal.SIGTERM); p.communicate()                       # a stop: the scope's every process gets SIGTERM
        c = calls.read_text().splitlines()
        s.assertIn("--init", next(l for l in c if "--name build-x" in l))         # the container's init takes the SIGTERM docker run proxies
        s.assertEqual(c[-1], "rm -f build-x")                                     # and the build removes its container as it ends

    def test_an_image_holds_the_game_yml_of_its_tree(s):  # server-token-auth-17: or:2cdbf708b held an older tree's game.yml, kept by clean in the build copy
        (s.root / "bin/docker").write_text(f'#!/bin/bash\necho "$*" >> {s.root}/calls\n' + 'case "$*" in "image inspect"*) exit 1;; *"--name build-x"*) while [ "$1" != -w ]; do shift; done; mkdir -p "$2/server/app/build/libs" "$2/.data/raw-cache" "$2/.data/cache"; touch "$2/server/app/build/libs/server.jar" "$2/.data/game.key";;'
                                           f' "build "*) cp "${{@: -1}}/game.yml" {s.root}/image-game.yml; (cd "${{@: -1}}" && find . | sort) > {s.root}/image-files;; esac\n')   # the image's context, as docker build reads it
        (s.repo / ".gitignore").write_text("game.yml\n"); (s.repo / "game.example.yml").write_text("central:\n  same-instance: true\n"); git(s.repo, "add", "-A"); git(s.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i"); s.tc = git(s.repo, "rev-parse", "HEAD")   # upstream ignores game.yml
        s.build(); (s.root / "repo/.worktrees/x-build/game.yml").write_text("old: tree\n")
        r = s.build(); s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s.assertEqual((s.root / "image-game.yml").read_text(), "central:\n  http-port: 9090\n  same-instance: true\n")   # game.example.yml and the one harness setting: http on upstream's test server port
        s.assertEqual((s.root / "image-files").read_text().split(), [".", "./.data", "./.data/cache", "./game.yml", "./server.jar"])   # release-server.yml's bundle: no raw-cache, and no key (up and deploy give their own)
        s.assertFalse((s.root / "repo/.worktrees/x-build/.image").exists())   # the context is the image's once built: none kept (V9-RETENTION)
        calls = (s.root / "calls").read_text().splitlines()   # no build container live once the image is built: the build cache goes with the last build
        s.assertLess(max(i for i, c in enumerate(calls) if c.startswith("build ")), max(i for i, c in enumerate(calls) if c == "builder prune -f"))

    def test_two_attempts_keep_two_logs_each_named_in_the_output(s):  # a deploy's retry overwrote the first attempt's log: its failure was gone
        outs = [s.build(), s.build()]
        T = git(s.repo, "rev-parse", f"{s.tc}^{{tree}}"); logs = [s.root / f"state/x/build-{T}-{n}.log" for n in (1, 2)]
        for r, log in zip(outs, logs):
            s.assertNotEqual(r.returncode, 0); s.assertIn(f"build failed: {log}", r.stdout)
            s.assertIn("gradle: boom", log.read_text())
        s.assertNotEqual(logs[0].read_text(), logs[1].read_text())



class CacheDownload(unittest.TestCase):
    def test_the_revision_is_downloaded_once_and_every_tree_repacks_it(s):  # 13 builds and deploys downloaded openrs2's 213 MB in a day: the store was keyed by the pack inputs, the /dl copy never filled
        b = (HERE.parent / "build/build.sh").read_text()
        s.assertIn('gk=$(git -C "$repo" rev-parse -q --verify "$tc:game.example.yml" | cut -c1-12', b)   # the gate's release asset key
        c = b.split("s=/store/s$V-$CK d=/store/g-$GK")[1].split(":server:app:shadowJar")[0]
        s.assertLess(c.index("cp -a $d/. ."), c.index(":or-cache:freshCache"))          # a stored revision is restored, never downloaded
        s.assertLess(c.index(":or-cache:freshCache"), c.rindex("mv $d.tmp $d"))           # a download is stored whole
        s.assertLess(c.index("tar -xzf /game-data.tgz"), c.index("cp -a $d/. ."))          # sweep-28: a revision missing from the store comes from the gate's asset, never openrs2 first
        s.assertIn('gh release download game-data -R "$R" -p "game-data-$gk.tar.gz"', b)
        s.assertLess(c.index(":or-cache:buildCache"), c.index(":or-cache:mergePluginGamevals"))   # a stored revision repacks this tree, then merges as release-server.yml: freshCache, mergePluginGamevals, shadowJar
        s.assertLess(c.index(":or-cache:freshCache"), c.index(":or-cache:mergePluginGamevals"))
        s.assertNotIn("/dl", SRC)

    def test_every_pack_starts_from_no_other_trees_incremental_state(s):  # hunter-feat-pr or:0abbfc5be22c: the copy's incremental_server skipped the projanim renumber; Telekinetic Grab threw 'Projectile not found'
        b = (HERE.parent / "build/build.sh").read_text()
        c = b.split("s=/store/s$V-$CK d=/store/g-$GK")[1].split(":server:app:shadowJar")[0]
        packs = [c.index(":or-cache:buildCache"), c.index(":or-cache:freshCache")]
        clears = [i for i in range(len(c)) if c.startswith("rm -f .data/cache/incremental_*", i)]
        s.assertLess(c.index("if [ -d $s ]; then cp -a $s/. .; else"), clears[0])          # the store's pack is this tree's exact inputs': kept whole
        s.assertLess(clears[0], min(packs))                                                  # the copy's state, kept by clean, gone before either pack
        s.assertTrue(c[c.index("cp -a $d/. ."):].startswith("cp -a $d/. . && rm -f .data/cache/incremental_*"))   # the stored revision's too
        s.assertIn('docker build -q --label hd.build=$v', b)                                 # a kept or:<T> or store entry is of this version:
        s.assertIn('[ -d /store/s$v-$ck ]', b)                                               # one packed from carried state is built again


class ShipFailure(unittest.TestCase):
    def test_a_failing_step_names_itself(s):
        f = SRC.split("\ndeploy() {")[1].split("\n}")[0]
        r = subprocess.run(["bash", "-c", "set -euo pipefail\ndeploy() {" + f.split("\n")[0] + "\n" + f.split("\n")[1] + "\n  false\n}\narg=t; deploy"], capture_output=True, text=True)
        s.assertNotEqual(r.returncode, 0); s.assertIn("deploy of t failed: false (exit 1)", r.stdout)

    def test_ready_fails_on_a_container_not_started_since(s):  # sweep-67 P0-a: compose left osrs-openrune running from 17:14:56Z and ready waited on a line that never came
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "docker").write_text(
            '#!/bin/bash\ncase $1 in inspect) case $3 in *StartedAt*) echo 2026-11-02T17:14:56.123Z ;; *) [ -n "${BIG:-}" ] && echo false || echo true ;; esac ;; logs) echo "Server ready in 9s"; [ -z "${BIG:-}" ] || yes x | head -c 300000 ;; esac\n')
        (root / "docker").chmod(0o755)
        f = "ready() {" + SRC.split("\nready() {")[1].split("\n}")[0] + "\n}\n"
        run = lambda since: subprocess.run(["bash", "-c", f"set -euo pipefail\n{f}ready c {since}"], capture_output=True, text=True, env={**os.environ, "PATH": f"{root}:{os.environ['PATH']}"})
        r = run("2026-11-02T18:18:48Z"); s.assertEqual(r.returncode, 1); s.assertIn("c has run since 2026-11-02T17:14:56, not started since", r.stdout)
        s.assertEqual(run("2026-11-02T17:14:56Z").returncode, 0)                  # started in the second it was asked: ready
        s.assertEqual(run("").returncode, 0)                                      # no since: the first start counts
        r = subprocess.run(["bash", "-c", f"set -euo pipefail\n{f}ready c"], capture_output=True, text=True, env={**os.environ, "BIG": "1", "PATH": f"{root}:{os.environ['PATH']}"})
        s.assertEqual((r.returncode, r.stdout), (0, ""))                          # sweep-80 P5-a: logs past 64 KB after the line: grep -q's SIGPIPE read as not ready

    def test_a_file_the_live_stack_runs_from_the_checkout_moves_the_deploy_key(s):  # alert 48: a shipped issuer.py stayed unserved until someone restarted the container
        recipe = lambda: subprocess.run(["bash", str(HERE.parent / "track.sh"), "recipe"], capture_output=True, text=True).stdout
        import hashlib
        files = b"".join((HERE / f).read_bytes() for f in ("docker-compose.yml", "switch.env", "jav_config.ws.template"))
        s.assertIn(f"deploy fork-3-{hashlib.sha256(files).hexdigest()[:12]}\n", recipe())

    def test_a_refused_login_holds_the_ci_read(s):  # a cause outside the tree records no result (PRD H3): two heads went back to dev on a 401
        s.assertIn('""|000|401|5??) sleep 30', SRC)

    def test_ship_recreates_the_stack_and_records_its_containers(s):  # harness-live-http-mount: compose restarted the exited http, whose file mount a WSL restart had turned into a directory
        f = SRC.split("\ndeploy() {")[1].split("\n}")[0]
        s.assertLess(f.index('docker tag "osrs-openrune:$T" "$live_image"'), f.index("--force-recreate --remove-orphans openrune)"))   # the dropped sidecars' containers (issuer, http-desktop, http) go
        s.assertIn('"containers":sys.argv[8].split()', f); s.assertIn("ps -a --format '{{.Name}}'", f)


class DesktopDevtools(unittest.TestCase):
    def test_each_desktop_loads_the_live_clients_devtools_jar(s):  # the client track's build, not a jar staged by hand
        t = SRC
        f = t.split("\ndevtools_jar() {")[1].split("\n}")[0]
        s.assertIn('"$c" build live "$tc"', f); s.assertIn("-u T -u TCOMMIT -u EVIDENCE", f)
        s.assertIn('jar=$root/evidence/live/$(git -C "$crepo" rev-parse "$tc^{tree}").devtools-desktop.jar', f); s.assertIn("c=$root/tracks/client/track.sh", f)
        s.assertIn("  devtools_jar", t.split("\nup() {")[1].split("\n}")[0])
        start = t.split("\ndesktop_start() {")[1].split("\n}")[0]
        s.assertLess(start.index('cp "$jar" "$d/home/.rlcustom/sideloaded-plugins/OpenRune-Developer-Tools.jar"'), start.index("exec setsid"))
        s.assertLess(start.index("EXTRA_PLUGINS"), start.index("exec setsid"))   # the client track's probe jar loads at the start
        live = t.split("\nlive_desktop() {")[1].split("\n}")[0]   # the live stack's Central, game port, cache and modulus; never a stack of the slug's own
        for k in ("srv=osrs-openrune", "http=${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}", "tok=true; ca=$root/state/live/token/tls.pem", "43594", "state/live/tree.json", "devtools_jar"): s.assertIn(k, live)
        s.assertLess(live.index('sign_in "$(account 1)"'), live.index("desktop_start"))   # h-desktops-token-login: the session before the desktop that carries it
        s.assertIn('desktop_login.py" "$dt" token)', live); s.assertNotIn('"$dt" "$(account 1)"', live)   # Play alone: no form typed
        s.assertLess(live.index("live=1"), live.index('flock -s "$root/state/live/stack.lock" true'))   # h-deploy-spares-live-judge: its row holds deploys off, then a started one ends first
        s.assertLess(live.index("stack.lock"), live.index("sign_in"))
        s.assertIn("set -E", live); s.assertIn("live_desktop_down >&2 || true' EXIT", live); s.assertIn("trap - EXIT", live)   # a failed start, set -e inside desktop_start included, names its step and leaves no instance
        k = start.split('until "$desk/jdk/bin/keytool.exe"')[1].split("\n    done")[0]   # the interop error (accept4 failed 110) ends keytool: asked again on a fresh store, any other failure reported
        s.assertIn("grep -q UtilAcceptVsock", k); s.assertIn('cp "$desk/jdk/lib/security/cacerts" "$d/home/token-trust.p12"', k); s.assertIn("return 1", k)


class AccountName(unittest.TestCase):
    def test_each_login_name_fits_the_client_and_is_unique_per_slug_and_client(s):  # the client refuses a login name over 12 characters
        fn = next(l for l in SRC.splitlines() if l.startswith("account()"))
        name = lambda slug, i: subprocess.run(["bash", "-c", f'{fn}\nslug=$1; account $2', "-", slug, str(i)], capture_output=True, text=True).stdout.strip()
        names = {name(slug, i) for slug in ("harness-no-powershell", "harness-server-account-name-length") for i in (1, 5)}
        s.assertEqual(len(names), 4)
        for n in names: s.assertRegex(n, r"^[a-z][a-z0-9]{1,11}$")

    def test_without_an_index_it_is_the_prefix_of_every_name_under_set_u(s):  # up's members update calls account with no argument
        fn = next(l for l in SRC.splitlines() if l.startswith("account()"))
        r = subprocess.run(["bash", "-c", f'set -euo pipefail\n{fn}\nslug=s; echo "$(account) $(account 1) $(account 5)"'], capture_output=True, text=True)
        s.assertEqual(r.returncode, 0, r.stderr)
        prefix, *names = r.stdout.split()
        for n in names: s.assertEqual(n, prefix + n[len(prefix):]); s.assertEqual(len(n), len(prefix) + 1)


class QuestMode(unittest.TestCase):
    def test_up_runs_the_image_config_with_the_changes_quest_mode(s):  # upstream's assume-completed let the range cook before Cook's Assistant; a cannon needs it while main has no Dwarf Cannon quest
        src = SRC
        fns = "\n".join(l for l in src.splitlines() if l.startswith(("quests()", "quest_mode()")) or l.startswith("  y=$(sed"))
        yml = 'game:\n  pvp:\n    mode: "off"\n  quest-requirements:\n    # Bypass quest gates by default.\n    mode: "assume-completed"\n    virtual-lines: []\n  other:\n    mode: "on"\n'   # upstream game.example.yml's shape
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "harness/changes").mkdir(parents=True)
        def run(text, front, env=""):
            (root / "harness/changes/x.md").write_text(f"---\nslug: x\n{front}---\nquest-mode: assume-completed in the body is no setting\n")
            return subprocess.run(["bash", "-c", f"set -euo pipefail\nroot={root}; slug=x\n{fns}\n{env} quests \"$({env} quest_mode)\""], input=text, capture_output=True, text=True,
                                  env={k: v for k, v in os.environ.items() if k != "QUEST_MODE"})
        for front, env, mode in [("", "", "respect-progress"), ("quest-mode: assume-completed\n", "", "assume-completed"), ("quest-mode: respect-progress\n", "", "respect-progress"),
                                 ("quest-mode: assume-completed\n", "QUEST_MODE=respect-progress", "respect-progress"), ("", "QUEST_MODE=assume-completed", "assume-completed")]:
            r = run(yml, front, env); s.assertEqual(r.returncode, 0, r.stderr)
            s.assertEqual([l for l in r.stdout.splitlines() if l.strip().startswith("mode:")], ['    mode: "off"', f'    mode: "{mode}"', '    mode: "on"'])
            s.assertEqual(len(r.stdout.splitlines()), len(yml.splitlines()))
        s.assertIn("respect-progress or assume-completed", run(yml, "quest-mode: off\n").stderr)
        s.assertNotEqual(run("game:\n  name: x\n", "").returncode, 0)
        up = src.split("\nup() {")[1].split("\n}")[0]
        s.assertIn('| quests "$(quest_mode)" | idle_off > "$state/game.yml"', up); s.assertIn('-v "$state/game.yml:/app/game.yml:ro"', up)

    def test_restart_keeps_the_config_and_database_of_up(s):  # a hand-run container lost its game.yml mount at restart; a tmpfs database loses the accounts
        src = SRC
        up = src.split("\nup() {")[1].split("\n}")[0]; restart = src.split("\nrestart() {")[1].split("\n}")[0]
        s.assertIn('-v "$state/postgres:/app/.data/postgres"', up); s.assertNotIn("--tmpfs", up)
        s.assertIn("RESUME=1", restart); s.assertIn("\n  up;", restart); s.assertNotIn("docker run", restart)   # restart is a resumed up of the same database (Central's sessions are in memory)


class IdleLogout(unittest.TestCase):
    def test_a_runs_server_never_idle_logs_out_and_live_keeps_it(s):  # genie-review-355-131: desktops logged out 5 min after their last input and sat at the login screen
        fn = next(l for l in SRC.splitlines() if l.startswith("idle_off()"))
        render = lambda text: subprocess.run(["bash", "-c", f"set -euo pipefail\n{fn}\nidle_off"], input=text, capture_output=True, text=True).stdout
        yml = "gameplay:\n  level-up-popups: false\n  # Log players out when their client reports them idle.\n  idle-logout: true\n  home-teleport: 30\n"   # game.example.yml's shape
        s.assertEqual(render(yml), yml.replace("idle-logout: true", "idle-logout: false"))
        s.assertEqual(render("gameplay:\n  home-teleport: 30\n"), "gameplay:\n  home-teleport: 30\n")   # a tree before the toggle has no idle logout
        ship = SRC.split("\ndeploy() {")[1].split("\n}")[0]
        s.assertNotIn("idle_off", ship)   # live keeps the official idle logout


class Resume(unittest.TestCase):
    def test_down_saves_the_characters_and_resume_up_keeps_them(s):  # each up wiped the account: a long quest review replayed the quest every run
        src = SRC
        fn = lambda name: f"{name}() {{" + src.split(f"\n{name}() {{")[1].split("\n}")[0] + "\n}"
        line = lambda pre: next(l for l in src.splitlines() if l.startswith(pre))
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "bin").mkdir(); (root / "st").mkdir()
        # a fake docker: the server is ready, its characters go offline one per count, and every call is logged
        (root / "bin/docker").write_text(f"""#!/bin/bash
echo "$*" >> {root}/calls
case $1 in inspect) echo true ;; logs) echo "Server ready in 1s" ;;
  run) n=$(cat {root}/online); echo $n; [ $n = 0 ] || echo $((n - 1)) > {root}/online ;; esac
""")
        (root / "bin/docker").chmod(0o755); (root / "online").write_text("2")
        script = "\n".join(["set -euo pipefail", f"hd=:; slug=x; state={root}/st", line("account()"), line("mine="), fn("sql"), line("offline()"), fn("down"),
                            "desktop_stop() { :; }", "down"])
        r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env={**os.environ, "EVIDENCE": "", "PATH": f"{root}/bin:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 0, r.stderr)
        calls = (root / "calls").read_text().splitlines()
        s.assertEqual([c.split()[0] for c in calls if c.startswith(("run", "rm"))], ["run", "run", "run", "rm"])   # removed only once none is online
        wipe = line('  [ -n "${RESUME:-}" ] || rm -rf "$state/postgres"')
        for env, kept in (("", False), ("RESUME=1", True)):
            (root / "st/postgres").mkdir(exist_ok=True); (root / "st/postgres/PG_VERSION").write_text("14")
            subprocess.run(["bash", "-c", f"set -euo pipefail; state={root}/st; {env}\n{wipe}"], check=True)
            s.assertEqual((root / "st/postgres/PG_VERSION").exists(), kept)
        s.assertIn('-v "$state/postgres:/app/.data/postgres"', src.split("\nup() {")[1].split("\n}")[0])


class DesktopInstance(unittest.TestCase):
    """A fake Windows: each process is win/<pid>.jvm (its jps line) and win/<pid>.port (the port it listens on)."""
    def setUp(s):
        s.t = t = Path(tempfile.mkdtemp()); (t / "state").mkdir(); (t / "bin").mkdir(); (t / "sys32").mkdir(); (t / "win").mkdir()
        exe = lambda p, body: (p.write_text("#!/bin/bash\n" + body), p.chmod(0o755))
        exe(t / "sys32/netstat.exe", f'[ -e {t}/interop-fails ] && {{ rm {t}/interop-fails; echo "<3>WSL ERROR: UtilAcceptVsock:273: accept4 failed 110" >&2; exit 1; }}; for f in {t}/win/*.port; do [ -e "$f" ] && echo "  TCP 127.0.0.1:$(cat $f) 0.0.0.0:0 LISTENING $(basename $f .port)"; done; true\n')
        exe(t / "sys32/taskkill.exe", f'echo "$4" >> {t}/killed; [ -e {t}/win/$4.dir ] && chmod u+w "$(cat {t}/win/$4.dir)/held"; rm -f {t}/win/$4.*\n')
        exe(t / "sys32/netsh.exe", 'printf "Start Port    End Port\\r\\n----------    --------\\r\\n     50000       50059     *\\r\\n"\n')
        exe(t / "sys32/robocopy.exe", 'cp -r "$1" "${2//\\\\//}"; exit 1\n')   # 1: files copied
        exe(t / "bin/ps", f'cat {t}/ps 2>/dev/null; true\n')   # the host's processes: none but those a test writes
        exe(t / "bin/wslpath", 'sleep 0.5; echo "$2"\n')   # widens the window between picking an instance and claiming it
        exe(t / "bin/docker", f'[ "$1" = exec ] && exec tar -c -C {t}/served .; exit 1\n')   # the server's served cache
        (t / "served").mkdir(); (t / "served/main_file_cache.dat2").write_text("served")
        d = t / "desk"; (d / "home/.rsprox").mkdir(parents=True); (d / "home/.rlcustom/profiles2").mkdir(parents=True); (d / "jdk/bin").mkdir(parents=True)
        (d / "home/.rlcustom/jagexcache/oldschool/LIVE").mkdir(parents=True); (d / "home/.rlcustom/jagexcache/oldschool/LIVE/main_file_cache.dat2").write_text("template")
        (d / "home/.rlcustom/settings.properties").write_text("a=1\n"); (d / "home/.rlcustom/profiles2/p.properties").write_text("openrunedevtools.port=7780\n")
        exe(d / "jdk/bin/java.exe", f'echo "$$ OsrsTestLauncher $*" > {t}/win/$$.jvm; echo "$JAVA_TOOL_OPTIONS" > {t}/win/$$.opts; echo $((7779 + ${{1##*run}})) > {t}/win/$$.port; pwd > {t}/win/$$.dir; mkdir held; touch held/f; chmod 555 held; exec sleep 30\n')   # a live JVM holds its files
        exe(d / "jdk/bin/javac.exe", f'echo "$*" >> {t}/javac; while [ "$1" != -d ]; do shift; done; touch "${{2//\\\\//}}/OsrsTestLauncher.class"\n')
        exe(d / "jdk/bin/jar.exe", f'echo "$*" >> {t}/jar; touch "${{2//\\\\//}}"\n')
        exe(d / "jdk/bin/jps.exe", f'for f in {t}/win/*.jvm; do [ -e "$f" ] || continue; if [ -e "${{f%.jvm}}.flaky" ]; then rm "${{f%.jvm}}.flaky"; echo "${{f##*/}} -- process information unavailable"; else cat "$f"; fi; done\n')
        (t / "devtools.jar").write_text("jar")
        src = SRC
        s.fns = src[src.index("sys32="):src.index("\nkeys() {")]
        s.env = {**os.environ, "PATH": f"{t / 'bin'}:{os.environ['PATH']}", "WINDOWS_SYSTEM32": str(t / "sys32"), "DESKTOP_DIR": str(d)}

    def tearDown(s):
        for f in s.t.glob("win/*.jvm"): subprocess.run(["kill", f.stem], capture_output=True)
        subprocess.run(["chmod", "-R", "u+w", s.t])
        shutil.rmtree(s.t, ignore_errors=True)

    def proc(s, pid, cls, marker=None, port=None):
        (s.t / f"win/{pid}.jvm").write_text(f"{pid} {cls} -Duser.home=C:\\x" + (f" -Dosrstest.marker=osrs-test-run{marker}" if marker else "") + "\n")
        if port: (s.t / f"win/{pid}.port").write_text(f"{port}\n")

    def sh(s, slug, body, **kw):
        return subprocess.Popen(["bash", "-c", f"set -euo pipefail; root={s.t}; slug={slug}; self={HERE.parent}; state={s.t}/state/{slug}; mkdir -p $state; http=1; game=2; modulus=3; jar={s.t}/devtools.jar; devtoken=tk\n{s.fns}\n{body}"], stdout=subprocess.PIPE, text=True, env=s.env, **kw)

    def killed(s):
        return sorted((s.t / "killed").read_text().split()) if (s.t / "killed").exists() else []

    def test_concurrent_ups_each_create_their_own_instances(s):  # five shared instances: concurrent ups raced and retried for two at once
        ps = [s.sh(f"s{k}", "desktop_start; echo $inst:$dt; desktop_start; echo $inst:$dt") for k in range(3)]
        got = [l for p in ps for l in p.communicate(timeout=60)[0].split()]
        s.assertEqual(len(set(got)), 6, got); s.assertEqual(s.killed(), [])
        for g in got:
            n, port = g[len("desktop"):].split(":")
            s.assertEqual((s.t / f"desk/run/{n}/home/.rlcustom/profiles2/p.properties").read_text(), f"openrunedevtools.port={port}\n")
            s.assertTrue((s.t / f"desk/run/{n}/home/.rlcustom/sideloaded-plugins/OpenRune-Developer-Tools.jar").exists())
            s.assertEqual((s.t / f"desk/run/{n}/home/.rlcustom/jagexcache/oldschool/LIVE/main_file_cache.dat2").read_text(), "served")   # the disk cache its server serves: a login fetches no group
        owners = [(s.t / "desk/run" / g[len("desktop"):].split(":")[0] / "owner").read_text().split() for g in got]
        opts = [f.read_text() for f in s.t.glob("win/*.opts")]
        s.assertEqual(sorted(o.split("-Dosrstest.devtools=")[1].split()[0] for o in opts), sorted(f"{g.split(':')[1]}:{s.t}/desk/run/{g[len('desktop'):].split(':')[0]}\\guard" for g in got))   # each desktop's endpoint reads its instance's guard
        s.assertEqual({(s.t / "desk/run" / g[len("desktop"):].split(":")[0] / "guard").read_text() for g in got}, {"tk"})   # and answers its up's token alone
        s.assertTrue(all("-javaagent:" in o and "HttpServerProvider=DevtoolsOwner" in o for o in opts))
        s.assertEqual(len(list(s.t.glob("desk/rsprox/owner-*.jar"))), 1)   # the owner check's jar in the template, the same for every up
        s.assertEqual(sorted(o[0] for o in owners), ["s0", "s0", "s1", "s1", "s2", "s2"]); s.assertEqual(len({o[1] for o in owners}), 6)   # each claim its own: a process that started on one never acts on the next

    def test_a_session_bridge_older_than_serve_leaves_the_endpoint_open_while_it_lives(s):  # endpoint-owner-2: the orchestrator's bridge, run without serve.py, sends no token: every desktop refused its runs; sweep-50: it kept every later guard off
        import desktop_login as dl
        (s.t / "ps").write_text("10 1 /usr/bin/claude\n11 10 python3 /h/mcp/serve.py osrs-devtools-desktop\n12 11 python3 /h/mcp/devtools_bridge.py desktop http://127.0.0.1:7780/mcp\n"
                                "13 10 python3 /h/mcp/devtools_bridge.py mobile /c/tools/devtools-mcp.sh\n")
        p = s.sh("a", "desktop_start; echo $inst"); a = p.communicate(timeout=60)[0].split()[0][len("desktop"):]
        served = (s.t / "ps").read_text(); (s.t / "ps").write_text(served + "20 1 /usr/bin/claude\n21 20 python3 /h/mcp/devtools_bridge.py desktop http://127.0.0.1:7780/mcp\n")
        p = s.sh("b", "desktop_start; echo $inst", stderr=subprocess.PIPE); out, err = p.communicate(timeout=60); b = out.split()[0][len("desktop"):]
        guard = lambda n: (s.t / f"desk/run/{n}/guard").read_text()
        s.assertEqual((guard(a), guard(b)), ("tk", ""))   # served bridges send the token; while a bridge of no serve.py lives: any caller
        s.assertIn("the desktop bridges 21 predate mcp/serve.py", err)
        s.addCleanup(os.environ.update, {"PATH": os.environ["PATH"]}); os.environ["PATH"] = s.env["PATH"]; os.environ["DESKTOP_DIR"] = s.env["DESKTOP_DIR"]; s.addCleanup(os.environ.pop, "DESKTOP_DIR")
        s.addCleanup(setattr, dl, "claim", None); s.addCleanup(setattr, dl, "devtoken", dl.devtoken); s.addCleanup(setattr, dl.time, "sleep", dl.time.sleep)
        port = 7779 + int(b); dl.claim = dl.owner(port); dl.devtoken = lambda _: "tk"; turns = []
        def sleep(_):   # keep's guard, each turn: the stale session ends, then b's down removes the instance
            turns.append(guard(b))
            if len(turns) == 1: (s.t / "ps").write_text(served)
            else: (s.t / f"desk/run/{b}/owner").write_text("gone")
        dl.time.sleep = sleep
        dl.guarding(port)
        s.assertEqual(turns, ["", "tk"])   # the guard is on once no bridge from before serve.py lives
        s.assertIn("threading.Thread(target=guarding", (HERE / "desktop_login.py").read_text().split('if k:')[1][:200])   # every keeper guards its desktop

    def test_one_up_restart_or_down_of_a_slug_at_a_time(s):  # sweep-42: three overlapping ups and downs of server-clan-channels-4 left a login on an instance it no longer owned
        lock = SRC[SRC.index("case $verb in up|restart|down) ["):]; lock = lock[:lock.index("\n", lock.index("exec flock"))]
        f = s.t / "track.sh"; f.write_text(f"set -euo pipefail\nverb=$1; slug=a; state={s.t}/state\n{lock}\n"
                                           f"echo \"start $$\" >> {s.t}/log; sleep 1; echo \"end $$\" >> {s.t}/log; setsid sleep 30 < /dev/null > /dev/null 2>&1 & echo $! >> {s.t}/started\n")
        ps = [subprocess.Popen(["bash", str(f), "up"], stderr=subprocess.PIPE, text=True)]
        while not (s.t / "log").exists(): pass   # the up holds the lock before the down asks for it
        ps.append(subprocess.Popen(["bash", str(f), "down"], stderr=subprocess.PIPE, text=True))
        errs = [p.communicate(timeout=60)[1] for p in ps]
        log = [l.split() for l in (s.t / "log").read_text().splitlines()]
        s.assertEqual([w for w, _ in log], ["start", "end", "start", "end"]); s.assertEqual(log[0][1], log[1][1])   # the second waited for the first
        s.assertIn("waits for the running up, restart or down of a", "".join(errs))
        s.assertEqual(subprocess.run(["flock", "-n", str(s.t / "state/desktops.lock"), "true"]).returncode, 0)   # a desktop or keeper it started holds no lock
        subprocess.run(["kill", *(s.t / "started").read_text().split()], capture_output=True)   # the sleeps it started, never another's

    def test_a_failed_windows_listing_is_asked_again_and_the_launcher_logs(s):  # a loaded host: netstat.exe through WSL interop failed or hung, up waited forever
        (s.t / "interop-fails").write_text("")
        p = s.sh("a", "desktop_start; echo $inst $dt"); out = p.communicate(timeout=60)[0].split()
        s.assertEqual((p.returncode, out), (0, ["desktop1", "7780"])); s.assertFalse((s.t / "interop-fails").exists())
        s.assertTrue((s.t / "state/a/desktop1.log").exists())   # the launcher's output, read when a desktop never opens its port
        s.assertIn('timeout 20 "$sys32/netstat.exe"', SRC)   # a hung listing ends and is asked again

    def test_a_port_another_program_holds_is_skipped_and_never_stopped(s):  # the user's own RuneLite on a harness port
        s.proc(500, "RuneLite", None, 7780)
        out = s.sh("b", "desktop_start; echo $inst $dt").communicate(timeout=60)[0].split()
        s.assertEqual(out, ["desktop2", "7781"]); s.assertEqual(s.killed(), []); s.assertFalse((s.t / "desk/run/1").exists())

    def test_down_stops_and_removes_exactly_its_own_instances(s):  # an orphan once took a judge's login keys
        for slug in ("a", "b", "a"): s.sh(slug, "desktop_start").communicate(timeout=60)
        s.proc(500, "RuneLite", None, 7790)
        mine = sorted(f.stem for f in s.t.glob("win/*.jvm") if any(f"osrs-test-run{n} " in f.read_text() for n in (1, 3)))
        s.sh("a", "desktops_remove").communicate(timeout=60)
        s.assertEqual(s.killed(), mine)
        s.assertEqual(sorted(p.name for p in (s.t / "desk/run").iterdir()), ["2"])
        s.assertTrue((s.t / "win/500.jvm").exists())

    @unittest.skipUnless(shutil.which("systemd-run") and subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True).stdout.strip() in (b"running", b"degraded"), "no systemd user manager")
    def test_each_desktop_jvm_is_recorded_under_the_runs_slice_until_down(s):  # osrs-harness R5: a run's end stops its Linux processes; a Windows JVM outlives them
        sl = f"hd-run-{os.getpid()}.scope"; s.addCleanup(subprocess.run, ["systemctl", "--user", "stop", sl])   # a failed assert stops it too
        p = subprocess.Popen(["systemd-run", "--user", "--scope", "-q", "--unit", sl[:-6], "bash", "-c", f"set -euo pipefail; root={s.t}; slug=a; self={HERE.parent}; state={s.t}/state/a; mkdir -p $state; http=1; game=2; modulus=3; jar={s.t}/devtools.jar; devtoken=tk\n{s.fns}\ndesktop_start"], env=s.env)
        p.wait(timeout=60)
        mine = sorted(f.stem for f in s.t.glob("win/*.jvm"))
        s.assertEqual((p.returncode, sorted(f.name for f in (s.t / "state/winpids" / sl).iterdir())), (0, mine))
        s.assertEqual((s.t / "state/winpids" / sl / mine[0]).read_text(), "java.exe\n")
        s.sh("a", "desktops_remove").communicate(timeout=60)
        s.assertEqual(list((s.t / "state/winpids" / sl).iterdir()), [])   # down ended them: nothing left for hd to stop

    def test_down_stops_a_jvm_jps_missed_before_it_removes_the_instance(s):  # quest-restlessghost: owner gone, three JVMs left holding run/4
        s.sh("a", "desktop_start").communicate(timeout=60)
        mine = sorted(f.stem for f in s.t.glob("win/*.jvm"))
        for p in mine: (s.t / f"win/{p}.flaky").write_text("")   # jps's first listing shows it as unavailable
        p = s.sh("a", "desktops_remove"); p.communicate(timeout=60)
        s.assertEqual(p.returncode, 0); s.assertEqual(s.killed(), mine); s.assertFalse((s.t / "desk/run/1").exists())

    def test_rsprox_ports_skip_every_range_windows_refuses_a_bind_on(s):  # mirrored WSL reserved the boot's Linux ephemeral range 40525-44620 on Windows: every launcher failed to bind 43600
        base = lambda ranges: subprocess.run(["bash", "-c", s.fns + "\nskip_base"], input=ranges, capture_output=True, text=True, env=s.env)
        s.assertEqual(base("32768 40000\n50000 50059\n").stdout, "0\n")
        s.assertEqual(base("40525 44620\n44621 44700\n50000 50059\n").stdout, f"{44701 - 43600}\n")   # past the first range, then past the next
        s.assertEqual(base("40525 65535\n").returncode, 1)
        p = s.sh("a", "desktop_start; echo $inst $dt"); out = p.communicate(timeout=60)[0].split()
        lo, hi = map(int, Path("/proc/sys/net/ipv4/ip_local_port_range").read_text().split())
        skip = int(next(s.t.glob("win/*.jvm")).read_text().split("-Dosrstest.portskip=")[1].split()[0])
        s.assertEqual(out, ["desktop1", "7780"])
        s.assertTrue(all(q < lo or q > hi for q in (43600 + skip, 43701 + skip)), (skip, lo, hi))
        s.assertTrue(all(q < 50000 or q > 50059 for q in range(43600 + skip, 43752 + skip)))
        s.assertIn("OsrsTestLauncher.java", (s.t / "javac").read_text())   # the tools tree's launcher, which takes any skip
        s.assertNotIn("skip > 50", (HERE / "OsrsTestLauncher.java").read_text())

    def test_a_launcher_whose_start_throws_fails_up_with_its_exception(s):  # RSProx's netty threads kept the failed launcher alive and up waited forever
        (s.t / "desk/jdk/bin/java.exe").write_text("#!/bin/bash\necho 'Exception in thread \"main\" java.net.BindException: Address already in use: bind'; echo '[osrs-test] REFUSING: launcher failed'; exit 2\n")
        p = s.sh("a", "desktop_start", stderr=subprocess.PIPE)
        err = p.communicate(timeout=60)[1]
        s.assertEqual(p.returncode, 1); s.assertIn("BindException", err)
        src = (HERE / "OsrsTestLauncher.java").read_text()
        s.assertIn("catch (Throwable e)", src); s.assertIn('die("launcher failed: " + e)', src)   # the launcher exits on any start exception

    def test_a_desktop_whose_devtools_plugin_cannot_bind_fails_up_with_the_bind_error(s):  # server-clan-guest-3: the client lived on without its endpoint on 7790 and up waited forever
        java = s.t / "desk/jdk/bin/java.exe"
        java.write_text(f'#!/bin/bash\necho "$$ OsrsTestLauncher $*" > {s.t}/win/$$.jvm; mkdir -p home/.runelite/logs; printf "ERROR Failed to start MCP server on port 7780; pick a free port\\njava.net.BindException: Address already in use\\n\\tat x\\n" > home/.runelite/logs/client.log; exec sleep 30\n')
        p = s.sh("a", "desktop_start", stderr=subprocess.PIPE)
        err = p.communicate(timeout=60)[1]
        s.assertEqual(p.returncode, 1); s.assertIn("could not bind 7780", err); s.assertIn("BindException: Address already in use", err); s.assertNotIn("at x", err)

    def test_a_launcher_failing_on_a_429_fails_up_and_a_started_desktop_seeds_the_templates_jars(s):  # h-live-desktop-launcher-429: every start downloaded all of RuneLite, repo.runelite.net answered 429 and the launcher's error dialog kept the start waiting forever
        java = s.t / "desk/jdk/bin/java.exe"; ok = java.read_text()
        java.write_text(f'#!/bin/bash\necho "$$ OsrsTestLauncher $*" > {s.t}/win/$$.jvm; printf "ERROR]    [main]: Launcher.main:416 - unable to download artifacts\\njava.io.IOException: Unable to download x.jar (status code 429)\\n\\tat y\\n"; exec sleep 30\n')
        p = s.sh("a", "desktop_start", stderr=subprocess.PIPE); err = p.communicate(timeout=60)[1]
        s.assertEqual(p.returncode, 1); s.assertIn("the RuneLite launcher failed", err); s.assertIn("status code 429", err); s.assertNotIn("at y", err)
        java.write_text(ok.replace("mkdir held;", "mkdir -p home/.runelite/repository2 home/.rsprox/runelite-launcher; touch home/.runelite/repository2/client.jar home/.rsprox/runelite-launcher/launcher.jar; mkdir held;", 1))
        p = s.sh("b", "desktop_start; echo $inst"); out = p.communicate(timeout=60)[0].split()
        s.assertEqual((p.returncode, out), (0, ["desktop2"]))
        s.assertTrue((s.t / "desk/home/.runelite/repository2/client.jar").exists()); s.assertTrue((s.t / "desk/home/.rsprox/runelite-launcher/launcher.jar").exists())   # the next home is copied with them

    def test_a_launch_wsl_interop_ended_is_launched_again_once_the_interop_answers(s):  # sweep-51 P3-b, sweep-53 P3-c: desktop logs holding only the interop error each failed a whole up
        java = s.t / "desk/jdk/bin/java.exe"; jps = s.t / "desk/jdk/bin/jps.exe"
        java.write_text(java.read_text().replace("#!/bin/bash\n", f'#!/bin/bash\n[ -e {s.t}/vsock ] && {{ rm {s.t}/vsock; touch {s.t}/jps-fails; echo "900 OsrsTestLauncher -Dosrstest.marker=osrs-test-run1" > {s.t}/win/900.jvm; echo "<3>WSL (1 - ) ERROR: UtilAcceptVsock:273: accept4 failed 110" >&2; exit 1; }}; ', 1))
        jps.write_text(jps.read_text().replace("#!/bin/bash\n", f'#!/bin/bash\n[ -e {s.t}/jps-fails ] && {{ rm {s.t}/jps-fails; exit 1; }}; ', 1))   # the interop answers on the second ask
        (s.t / "vsock").write_text("")
        p = s.sh("a", "account() { echo h1; }; desktop_start; echo $inst $dt"); out = p.communicate(timeout=60)[0].split()   # the launch's own lines in its log: the interop error alone
        s.assertEqual((p.returncode, out), (0, ["desktop1", "7780"])); s.assertFalse((s.t / "jps-fails").exists())
        s.assertEqual(s.killed(), ["900"])   # a JVM the ended launch left is stopped before the next
        s.assertEqual(len(list(s.t.glob("win/*.jvm"))), 1)
        java.write_text('#!/bin/bash\necho "<3>WSL (1 - ) ERROR: UtilAcceptVsock:273: accept4 failed 110" >&2; echo "Error: Could not find or load main class OsrsTestLauncher"; exit 1\n')
        p = s.sh("b", "account() { echo h1; }; desktop_start", stderr=subprocess.PIPE); err = p.communicate(timeout=60)[1]
        s.assertEqual(p.returncode, 1); s.assertIn("desktop 2 exited: ", err); s.assertIn("Could not find or load main class", err)   # any other cause fails up

    def test_the_desktop_connects_through_the_readmes_proxy_target_alone(s):  # h-ref-rsprox-targets: upstream README's Client Setup entry, no OPENRUNE_ENDPOINT
        java = s.t / "desk/jdk/bin/java.exe"
        java.write_text(java.read_text().replace("#!/bin/bash\n", f'#!/bin/bash\necho "${{OPENRUNE_ENDPOINT:-none}} $WSLENV" > {s.t}/env; ', 1))   # before its port: desktop_start returns once the port answers
        p = s.sh("a", "desktop_start"); p.communicate(timeout=60)
        s.assertEqual(p.returncode, 0)
        ep, wslenv = (s.t / "env").read_text().split()
        s.assertEqual(ep, "none"); s.assertNotIn("OPENRUNE_ENDPOINT", wslenv.split(":"))
        y = (s.t / "desk/run/1/home/.rsprox/proxy-targets.yaml").read_text().splitlines()
        s.assertEqual(y[:7], ["config:", "  - id: 1", "    name: OpenRune Test - a", "    jav_config_url: https://127.0.0.1:1/jav_config.ws", "    varp_count: 15000", "    revision: 241", "    modulus: 3"])   # the README's entry, its fields in its order
        s.assertIn("    game_server_port: 2", y); s.assertIn("    binary_folder: openrune-qa", y)   # the up's own game port; the recordings' folder
        src = (HERE / "OsrsTestLauncher.java").read_text()
        s.assertNotIn("OPENRUNE_ENDPOINT", src); s.assertIn('getJavConfigUrl().matches("https?://(127\\\\.0\\\\.0\\\\.1|localhost):[0-9]+/jav_config\\\\.ws")', src)   # a non-local target is refused

    def test_a_fresh_home_opens_on_the_welcome_page_and_existing_user_on_the_form(s):  # run 136: the terms page took no key and the Jagex Account prompt ate the typed login; a fixed-coordinate click opened a Jagex page
        src = (HERE / "OsrsTestLauncher.java").read_text()
        s.assertIn("if (!Files.exists(prefs))", src)   # a home that has run keeps its own
        s.assertIn("new ClientPreferences(false, false, 1, Map.of(), null, false, 0.8, 127, 127, 127, 1, false, 25, 0, false,", src)   # acceptedTOSVersion 1
        s.assertIn("toEpochDay() - 11745", src)   # lastJagexAccountPromptRuneDay today
        s.assertNotIn('"click"', (HERE / "desktop_login.py").read_text().split("def try_again")[0])   # no login step clicks a fixed spot but Try again

    def test_a_home_copy_interop_ended_is_copied_again_and_a_failed_one_fails_up(s):  # genie-review-355-134: a WSL interop error left instance 6 with no home, up half-up
        rc = s.t / "sys32/robocopy.exe"
        rc.write_text(f'#!/bin/bash\n[ -e {s.t}/interop-fails ] && {{ rm {s.t}/interop-fails; echo "<3>WSL ERROR: UtilAcceptVsock:273: accept4 failed 110" >&2; exit 1; }}; cp -r "$1" "${{2//\\\\//}}"; exit 1\n')
        (s.t / "interop-fails").write_text("")
        p = s.sh("a", "desktop_start; echo $inst $dt"); out = p.communicate(timeout=60)[0].split()
        s.assertEqual((p.returncode, out), (0, ["desktop1", "7780"])); s.assertFalse((s.t / "interop-fails").exists())
        s.assertTrue((s.t / "desk/run/1/home/.rlcustom/settings.properties").exists())
        rc.write_text("#!/bin/bash\nexit 16\n")
        p = s.sh("b", "desktop_start", stderr=subprocess.PIPE); err = p.communicate(timeout=60)[1]
        s.assertEqual(p.returncode, 1); s.assertIn("robocopy of the desktop home into", err)
        up = SRC.split("\nup() {")[1].split("\n}")[0]
        s.assertLess(up.index("down >/dev/null 2>&1' EXIT"), up.index('docker run -d --name "server-$slug"'))   # any failed step of up downs what it started
        s.assertTrue(up.endswith('trap - EXIT; echo "up: game $game http $http desktops ${desktops[*]}${staff:+ administrators $staff}"'))

    def test_an_up_that_fails_or_is_stopped_names_the_step_it_ended_at(s):  # server-clan-channels-6: two RESUME=1 ups ended after the guard line with no message
        trap = "\n".join(l for l in SRC.split("\nup() {")[1].split("\n}")[0].split("\n") if "' ERR" in l or "' EXIT" in l)
        for step, sig in (("[ -n \"\" ]", "f() { [ -n \"\" ]; echo never; }; "), ("sleep 5", "(sleep 0.5; kill -TERM $$) & ")):
            d = Path(tempfile.mkdtemp()) / "downed"
            p = subprocess.run(["bash", "-c", f"set -euo pipefail; state={d.parent}; slug=x; down() {{ touch {d}; }}\n{trap}\n{sig}{'f' if sig.startswith('f') else step}; echo never"], capture_output=True, text=True, timeout=30)
            s.assertNotIn("never", p.stdout); s.assertIn(f"up ended before it was up, at: {step}", p.stderr); s.assertTrue(d.exists())   # and down ran

    def test_up_records_each_desktop_before_its_login(s):  # a failed login aborts up under set -e; restart and the tools read up.json
        up = SRC.split("\nup() {")[1].split("\n}")[0]
        s.assertLess(up.index('stack desktops="${desktops[*]}"'), up.index('login "$dt"'))
        s.assertLess(up.index("down >/dev/null"), up.index("desktop_start"))


@unittest.skipUnless(shutil.which("javac") and shutil.which("jar"), "no JDK")
class OwnProcesses(unittest.TestCase):
    def test_no_tools_test_stops_processes_by_a_pattern(s):  # hunter-feat-pr-20: a test stopping every "sleep 30" by its pattern stopped a gate's CI wait
        kill = re.compile(r"\b(p" + r"kill|kill" + r"all)\b")
        s.assertEqual([str(f) for f in HERE.parent.glob("**/test_*.py") if kill.search(f.read_text())], [])


def owner_jar(t):  # t/o.jar: server/DevtoolsOwner.java built as track.sh desktop_start builds it
    (t / "c").mkdir(exist_ok=True)
    subprocess.run(["javac", "-nowarn", "--add-exports", "jdk.httpserver/sun.net.httpserver=ALL-UNNAMED", "--add-exports", "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED", "-d", str(t / "c"), str(HERE / "DevtoolsOwner.java")], check=True)
    (t / "m").write_text("Premain-Class: DevtoolsOwner\nCan-Retransform-Classes: true\n"); subprocess.run(["jar", "cfm", str(t / "o.jar"), str(t / "m"), "-C", str(t / "c"), "."], check=True)


class DevtoolsOwner(unittest.TestCase):
    def test_a_desktop_opens_no_url(s):  # runs 123 and 144: Recover Account on a locked account's page opened secure.runescape.com in the user's browser
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t, True); (t / "app").mkdir(); owner_jar(t)
        (t / "Open.java").write_text("""import java.awt.Desktop; import java.io.*; import java.lang.reflect.Field; import java.net.URI;
public class Open { public static void main(String[] a) throws Exception {   // as the game client and LinkBrowser hand a URL to the OS
  Field f = Class.forName("sun.misc.Unsafe").getDeclaredField("theUnsafe"); f.setAccessible(true);
  Desktop d = (Desktop) ((sun.misc.Unsafe) f.get(null)).allocateInstance(Desktop.class);   // a headless JVM has no Desktop to get
  d.browse(new URI("https://secure.runescape.com/m=account-appeals/")); d.mail(); d.open(new File("page.html"));
  try { Runtime.getRuntime().exec(new String[] {"xdg-open", "https://secure.runescape.com/m=weblogin/"}); System.out.println("started"); } catch (IOException e) { System.out.println("no process: " + e.getMessage()); }
  System.out.println("exit " + new ProcessBuilder("sh", "-c", "exit 4").start().waitFor()); } }""")
        subprocess.run(["javac", "-d", str(t / "app"), str(t / "Open.java")], check=True, stderr=subprocess.DEVNULL)
        r = subprocess.run(["java", "-cp", str(t / "app"), "Open"], capture_output=True, text=True, timeout=60, env={**os.environ, "JAVA_TOOL_OPTIONS": f"-javaagent:{t / 'o.jar'}"})
        s.assertEqual(r.stdout.splitlines(), ["[osrs-test] refused URL: https://secure.runescape.com/m=account-appeals/", "[osrs-test] refused URL: mailto:",
            "[osrs-test] refused URL: page.html", "[osrs-test] refused URL: xdg-open https://secure.runescape.com/m=weblogin/", "no process: a test desktop opens no URL", "exit 4"], r.stderr)   # a command with no URL still runs
        r = subprocess.run(["java", "-cp", str(t / "app"), "Open"], capture_output=True, text=True, timeout=60, env={**os.environ, "JAVA_TOOL_OPTIONS": f"-javaagent:{t / 'o.jar'} -Dosrstest.refusals={t / 'refused.log'}"})
        s.assertEqual((t / "refused.log").read_text().splitlines()[0], "[osrs-test] refused URL: https://secure.runescape.com/m=account-appeals/")   # track.sh's log: the client JVM's stdout reaches no log
        s.assertEqual(r.stdout.splitlines(), ["no process: a test desktop opens no URL", "exit 4"], r.stderr)

    def test_the_endpoint_answers_only_its_ups_token(s):  # sweep-43: a run's helper with a default port drove another run's desktop on 7780
        import socket, urllib.error, urllib.request
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t, True); (t / "c").mkdir(); (t / "app").mkdir()
        (t / "Plug.java").write_text("""import com.sun.net.httpserver.HttpServer; import java.net.*;
public class Plug { public static void main(String[] a) throws Exception {   // as the devtools plugin binds its endpoint
  for (String p : a) { HttpServer s = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), Integer.parseInt(p)), 0);
    s.createContext("/mcp", x -> { byte[] b = "{}".getBytes(); x.sendResponseHeaders(200, b.length); x.getResponseBody().write(b); x.close(); }); s.start(); }
  System.out.println("up"); System.out.flush(); Thread.sleep(60000); System.exit(0); } }""")
        owner_jar(t)
        subprocess.run(["javac", "-d", str(t / "app"), str(t / "Plug.java")], check=True)
        ports = []
        for _ in range(2):
            with socket.socket() as k: k.bind(("127.0.0.1", 0)); ports.append(k.getsockname()[1])
        opts = f"-javaagent:{t / 'o.jar'} -Dcom.sun.net.httpserver.HttpServerProvider=DevtoolsOwner --add-exports=jdk.httpserver/sun.net.httpserver=ALL-UNNAMED -Dosrstest.devtools={ports[0]}:{t / 'guard'}"
        (t / "guard").write_text("tk")
        p = subprocess.Popen(["java", "-cp", str(t / "app"), "Plug", *map(str, ports)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env={**os.environ, "JAVA_TOOL_OPTIONS": opts})
        s.addCleanup(p.stdout.close); s.addCleanup(p.wait); s.addCleanup(p.kill); s.assertEqual(p.stdout.readline().strip(), "up")
        def code(port, auth=None):
            try:
                with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/mcp", b"{}", {"Authorization": auth} if auth else {}), timeout=10) as r:
                    return r.status
            except urllib.error.HTTPError as e:
                return e.code
        s.assertEqual([code(ports[0]), code(ports[0], "Bearer other"), code(ports[0], "Bearer tk"), code(ports[1])], [401, 401, 200, 200])   # another port is the JDK's own
        (t / "guard").write_text("")
        s.assertEqual([code(ports[0]), code(ports[0], "Bearer tk")], [200, 200])   # an empty guard, read on each request: any caller
        (t / "guard").write_text("tk")
        s.assertEqual(code(ports[0]), 401)   # the guard back on, the desktop still up

    def test_the_owners_calls_run_one_at_a_time_and_a_notification_passes(s):  # sweep-47 P0-a: the plugin interrupts the active tool on every tools/call, so the keeper's state reads cancelled a run's walk_to
        import socket, threading, urllib.request
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t, True); (t / "c").mkdir(); (t / "app").mkdir()
        (t / "Plug.java").write_text("""import com.sun.net.httpserver.HttpServer; import java.net.*; import java.util.concurrent.*; import java.util.concurrent.atomic.*; import java.util.concurrent.locks.ReentrantLock;
public class Plug { public static void main(String[] a) throws Exception {   // a call waits for the notification; the notification waits for two calls in the handler, or one in it and one queued at the owner's lock
  ReentrantLock one = (ReentrantLock) Class.forName("DevtoolsOwner").getDeclaredField("ONE").get(null); AtomicInteger active = new AtomicInteger(); CountDownLatch go = new CountDownLatch(1);
  HttpServer s = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), Integer.parseInt(a[0])), 0); s.setExecutor(Executors.newFixedThreadPool(4));
  s.createContext("/mcp", x -> { String b = new String(x.getRequestBody().readAllBytes()); int n;
    try { if (b.contains("tools/call")) { n = active.incrementAndGet(); go.await(); active.decrementAndGet(); }
          else { while (active.get() < 2 && !(active.get() == 1 && one.getQueueLength() > 0)) Thread.onSpinWait(); n = active.get(); go.countDown(); } }
    catch (InterruptedException e) { n = -1; }
    byte[] r = String.valueOf(n).getBytes(); x.sendResponseHeaders(200, r.length); x.getResponseBody().write(r); x.close(); }); s.start();
  System.out.println("up"); System.out.flush(); Thread.sleep(60000); System.exit(0); } }""")
        owner_jar(t)
        subprocess.run(["javac", "-d", str(t / "app"), str(t / "Plug.java")], check=True)
        with socket.socket() as k: k.bind(("127.0.0.1", 0)); port = k.getsockname()[1]
        opts = f"-javaagent:{t / 'o.jar'} -Dcom.sun.net.httpserver.HttpServerProvider=DevtoolsOwner --add-exports=jdk.httpserver/sun.net.httpserver=ALL-UNNAMED -Dosrstest.devtools={port}:{t / 'guard'}"
        (t / "guard").write_text("tk")
        p = subprocess.Popen(["java", "-cp", str(t / "app"), "Plug", str(port)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env={**os.environ, "JAVA_TOOL_OPTIONS": opts})
        s.addCleanup(p.stdout.close); s.addCleanup(p.wait); s.addCleanup(p.kill); s.assertEqual(p.stdout.readline().strip(), "up")
        def send(body, out, i):
            with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/mcp", json.dumps(body).encode(), {"Authorization": "Bearer tk"}), timeout=30) as r:
                out[i] = int(r.read())
        out = [None] * 3
        calls = [threading.Thread(target=send, args=({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": "walk_to"}}, out, i)) for i in (0, 1)]
        for c in calls: c.start()
        send({"jsonrpc": "2.0", "method": "notifications/cancelled"}, out, 2)   # answered while a call holds the lock
        for c in calls: c.join()
        s.assertEqual(out, [1, 1, 1])   # each call ran alone in the handler

    def test_every_call_is_answered_within_its_bound(s):  # sweep-47/48: a hover on 7780 had no answer for 20 min through a session's bridge with no whole-call bound
        import socket, threading, time, urllib.request
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t, True); (t / "c").mkdir(); (t / "app").mkdir()
        (t / "Plug.java").write_text("""import com.sun.net.httpserver.HttpServer; import java.net.*; import java.util.concurrent.*;
public class Plug { public static void main(String[] a) throws Exception {   // "hang" never answers (a hung plugin; a stream that never ends), "ok" answers at once
  HttpServer s = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), Integer.parseInt(a[0])), 0); s.setExecutor(Executors.newFixedThreadPool(4));
  s.createContext("/mcp", x -> { String b = new String(x.getRequestBody().readAllBytes());
    if (b.contains("hang")) { System.out.println("hung"); System.out.flush(); x.getResponseHeaders().set("Content-Type", "text/event-stream"); x.sendResponseHeaders(200, 0); while (true) { x.getResponseBody().write(": ping\\n".getBytes()); x.getResponseBody().flush(); try { Thread.sleep(500); } catch (InterruptedException e) { return; } } }
    byte[] r = "{\\"jsonrpc\\":\\"2.0\\",\\"id\\":2,\\"result\\":{}}".getBytes(); x.sendResponseHeaders(200, r.length); x.getResponseBody().write(r); x.close(); }); s.start();
  System.out.println("up"); System.out.flush(); Thread.sleep(120000); System.exit(0); } }""")
        owner_jar(t)
        subprocess.run(["javac", "-d", str(t / "app"), str(t / "Plug.java")], check=True)
        with socket.socket() as k: k.bind(("127.0.0.1", 0)); port = k.getsockname()[1]
        (t / "guard").write_text("")   # as while a stale session's bridge lives: no token
        opts = f"-javaagent:{t / 'o.jar'} -Dcom.sun.net.httpserver.HttpServerProvider=DevtoolsOwner --add-exports=jdk.httpserver/sun.net.httpserver=ALL-UNNAMED -Dosrstest.devtools={port}:{t / 'guard'}"
        p = subprocess.Popen(["java", "-cp", str(t / "app"), "Plug", str(port)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env={**os.environ, "JAVA_TOOL_OPTIONS": opts})
        s.addCleanup(p.stdout.close); s.addCleanup(p.wait); s.addCleanup(p.kill); s.assertEqual(p.stdout.readline().strip(), "up")
        out = {}
        def send(i, name, ms):
            t0 = time.monotonic()
            with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/mcp", json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": {"timeoutMs": ms}}}).encode()), timeout=240) as r:   # the stale bridge's per-read timeout
                out[i] = (json.loads(r.read()), time.monotonic() - t0)
        hung = threading.Thread(target=send, args=(1, "hang", 1000)); hung.start()
        s.assertEqual(p.stdout.readline().strip(), "hung")   # the hung call holds the desktop
        send(2, "ok", 25000); hung.join()   # queued behind the hung call
        s.assertIn("did not answer the call within 21 s", out[1][0]["error"]["message"]); s.assertEqual(out[1][0]["error"]["code"], -32002); s.assertEqual(out[1][0]["id"], 1)   # the bound's own answer, not the bridge's 240 s read timeout: no wall-clock check, which load breaks
        s.assertEqual(out[2][0], {"jsonrpc": "2.0", "id": 2, "result": {}})   # the next call runs once the hung one is answered: held, its own bound would answer an error

    def test_a_login_sends_the_token_of_the_up_owning_the_port(s):
        import desktop_login as d
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t); (t / "run/2").mkdir(parents=True); (t / "state/a").mkdir(parents=True)
        (t / "run/2/owner").write_text("a 1-2\n"); (t / "state/a/up.json").write_text(json.dumps({"desktops": "desktop2:7781", "token": "tk"}))
        with mock.patch.dict(os.environ, {"DESKTOP_DIR": str(t), "HD_ROOT": str(t)}):
            s.assertEqual((d.devtoken(7781), d.devtoken(7782)), ("tk", ""))

    def test_a_mobile_call_reaches_the_mobile_its_serial_names(s):  # fault 307: the mobile backend got no serial, every call refused
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t, True); (t / "mcp").mkdir(); (t / "state/a").mkdir(parents=True)
        root = HERE.parents[2]
        for f in ("devtools_bridge.py", "devtools-snapshot.json"): shutil.copy(root / "mcp" / f, t / "mcp" / f)
        (t / "state/a/serial").write_text("emulator-5556\n")
        (t / "b.sh").write_text('#!/bin/sh\necho "{\\"jsonrpc\\":\\"2.0\\",\\"id\\":1,\\"result\\":{\\"tools\\":[{\\"name\\":\\"$ANDROID_SERIAL\\"}],\\"args\\":$3}}"\n'); (t / "b.sh").chmod(0o755)
        req = lambda i, m, p: json.dumps({"jsonrpc": "2.0", "id": i, "method": m, "params": p})
        out = subprocess.run([sys.executable, str(t / "mcp/devtools_bridge.py"), "mobile", str(t / "b.sh")], text=True, capture_output=True, timeout=60,
                             env={**os.environ, "HOME": str(t)},
                             input="\n".join([req(1, "tools/call", {"name": "get_inventory", "arguments": {}}),
                                              req(2, "tools/call", {"name": "get_inventory", "arguments": {"serial": "emulator-5554"}}),
                                              req(3, "tools/list", {})]) + "\n").stdout.splitlines()
        r = [json.loads(l) for l in out]
        s.assertIn("serial", r[0]["error"]["message"])   # no serial: refused, never any run's mobile
        s.assertEqual(r[1]["result"]["tools"][0]["name"], "emulator-5554"); s.assertEqual(r[1]["result"]["args"], {"name": "get_inventory", "arguments": {}})   # the backend's env, the argument taken off
        s.assertEqual(r[2]["result"]["tools"][0]["name"], "emulator-5556"); s.assertIn("serial", r[2]["result"]["tools"][0]["inputSchema"]["properties"])   # the list from an up's mobile, each tool taking serial

    def test_a_checkout_serves_its_own_state_root(s):  # state-root: a v9 up's desktop answered 401, its session ran the live checkout's bridge and login
        import desktop_login as d
        root = HERE.parents[2]
        s.assertEqual(d.ROOT, str(root))
        mcp = json.loads((root / ".mcp.json").read_text())["mcpServers"]
        s.assertEqual({v["command"] for v in mcp.values()}, {"${CLAUDE_PROJECT_DIR:-.}/mcp/serve.py"})
        s.assertTrue(all((root / "mcp" / c[0]).is_file() for c in json.loads((root / "mcp/servers.json").read_text()).values()))


class DesktopLogin(unittest.TestCase):
    def fake(s, states, widgets=([{"childIndex": 0, "itemId": 6512, "itemQuantity": 1, "selfHidden": True}],), inv=None):  # a devtools endpoint whose game state walks through states, one per read, staying on the last; get_widget of the inventory walks through widgets likewise; inv: container 93's items (None: not loaded)
        import desktop_login as d
        sent, states, widgets = [], list(states), list(widgets)
        def call(port, name, **a):
            sent.append((name, a))
            if name == "press_key" and len(a["key"]) > 1 and a["key"] not in ("ENTER", "ESCAPE", "SPACE", "TAB", "BACKSPACE"):
                raise d.Refused("Unknown key: " + a["key"])  # the endpoint's named keys
            if name == "get_widget":
                w = widgets.pop(0) if len(widgets) > 1 else widgets[0]
                if w is None:
                    raise d.Refused("Widget not found: 149.0")
                return json.dumps({"dynamicChildren": w})
            if name == "get_inventory":
                if inv is None:
                    raise d.Refused("Item container 93 is not loaded")
                return json.dumps({"items": inv})
            if name == "get_timeline":   # one game tick passes between two reads
                return json.dumps({"events": [{"tick": sum(n == "get_timeline" for n, _ in sent)}]})
            return json.dumps({"gameState": states.pop(0) if len(states) > 1 else states[0], "canvasWidth": 1005}) if name == "get_client_state" else "{}"
        s.addCleanup(setattr, d, "call", d.call); s.addCleanup(setattr, d.time, "sleep", d.time.sleep)
        d.call, d.time.sleep = call, lambda _: None
        return d, sent

    def test_login_screen_right_after_enter_is_not_a_result(s):  # a fresh account's first login read LOGIN_SCREEN before the attempt began
        d, _ = s.fake(["LOGIN_SCREEN"] * 4 + ["LOGGING_IN", "LOADING", "LOGGED_IN"])  # the wait, the two frame reads, then right after Enter
        s.assertEqual(d.login(1, "u", "p"), "LOGGED_IN")
        d, _ = s.fake(["LOGIN_SCREEN"] * 4 + ["LOGGING_IN", "LOGIN_SCREEN"])
        s.assertTrue(d.login(1, "u", "p").startswith("FAILED"))

    def test_logged_in_only_once_the_inventory_widget_shows_container_93(s):  # cannon-354-return-after-destroy-3: after up the widget stayed empty over a full container 93
        coins = [{"childIndex": 0, "itemId": 995, "itemQuantity": 5, "selfHidden": False}, {"childIndex": 1, "itemId": 6512, "itemQuantity": 1, "selfHidden": True}]
        held = [{"slot": 0, "itemId": 995, "quantity": 5}]
        d, sent = s.fake(["LOGGED_IN"], widgets=[None, [], coins], inv=held)   # the widget is built after LOGGED_IN
        s.assertEqual(d.login(1, "u", "p"), "LOGGED_IN")
        s.assertEqual(sum(n == "get_widget" for n, _ in sent), 3)
        d, _ = s.fake(["LOGGED_IN"])   # a fresh account: no container, every slot empty
        s.assertEqual(d.token(1), "LOGGED_IN")
        d, _ = s.fake(["LOGGED_IN"], inv=held)
        s.assertEqual(d.login(1, "u", "p"), "FAILED: the inventory widget shows {} but container 93 holds {0: (995, 5)}")
        d, _ = s.fake(["LOGGED_IN"], widgets=[[dict(coins[0], selfHidden=False, hidden=True)]], inv=held)   # another side tab open hides the slots through their parent alone
        s.assertEqual(d.login(1, "u", "p"), "LOGGED_IN")

    def test_no_inventory_widget_ticks_after_logged_in_fails_not_hangs(s):  # sweep-43: LOGGED_IN, container 93 never arrived, the restart waited 20 min
        d, sent = s.fake(["LOGGED_IN"], widgets=[None])
        s.assertEqual(d.token(1), f"FAILED: {d.TICKS} game ticks after LOGGED_IN the inventory widget has no slots: the server sent no inventory (container 93)")
        s.assertEqual(sum(n == "get_timeline" for n, _ in sent), d.TICKS + 2)   # the first read's event may be an earlier login's: counted from the next
        coins = [{"childIndex": 0, "itemId": 995, "itemQuantity": 5, "selfHidden": False}]
        d, _ = s.fake(["LOGGED_IN"], widgets=[None, None, None, coins], inv=[{"slot": 0, "itemId": 995, "quantity": 5}])
        ticks = iter([5, 97, 98]); s.addCleanup(setattr, d, "tick", d.tick); d.tick = lambda port: next(ticks)
        s.assertEqual(d.token(1), "LOGGED_IN")   # sweep-46: the tick goes on across logins (0 -> 5 -> 97); an earlier login's event at 5 is no start

    def test_a_refused_call_raises(s):  # press_key BACK_SPACE was refused as an unknown key and the login went on
        import desktop_login as d, io
        body = json.dumps({"result": {"isError": True, "content": [{"type": "text", "text": "Unknown key: BACK_SPACE"}]}}).encode()
        s.addCleanup(setattr, d.urllib.request, "urlopen", d.urllib.request.urlopen)
        d.urllib.request.urlopen = lambda *a, **k: io.BytesIO(body)
        with s.assertRaisesRegex(d.Refused, "Unknown key"):
            d.call(1, "press_key", key="BACK_SPACE")
        s.assertEqual(d.state(1), {})  # a refused state read is no state yet, read again

    def test_a_key_the_starting_client_did_not_take_is_resent_once_it_answers(s):  # one RESUME=1 up: 'devtools endpoint on 7780: <urlopen error timed out>'
        import desktop_login as d, io
        sent, slow = [], iter([True, True, True])   # the press_key, then two state reads, time out connecting
        def urlopen(req, timeout):
            name = json.loads(req.data)["params"]["name"]; sent.append(name)
            if next(slow, False):
                raise d.urllib.error.URLError(TimeoutError("timed out"))
            return io.BytesIO(json.dumps({"result": {"content": [{"type": "text", "text": '{"gameState": "LOGIN_SCREEN"}'}]}}).encode())
        s.addCleanup(setattr, d.urllib.request, "urlopen", d.urllib.request.urlopen); s.addCleanup(setattr, d.time, "sleep", d.time.sleep)
        d.urllib.request.urlopen, d.time.sleep = urlopen, lambda _: None
        d.call(1, "press_key", key="ESCAPE")
        s.assertEqual(sent, ["press_key", "get_client_state", "get_client_state", "get_client_state", "press_key"])   # resent only after a state read answered
        d.urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(d.urllib.error.URLError(ConnectionRefusedError()))
        with s.assertRaises(d.urllib.error.URLError):   # a refused connection (the desktop gone) is no start: it fails
            d.call(1, "press_key", key="ESCAPE")

    def test_a_call_queued_behind_a_long_call_waits_for_its_answer(s):  # sweep-49 P1-a: a keeper call queued behind a run's walk_to timed out, keep ended as gone and the abandoned ENTER ran later
        import desktop_login as d, http.server, time
        got = []
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(h):
                got.append(json.loads(h.rfile.read(int(h.headers["Content-Length"])))["params"]["name"])
                time.sleep(1)   # the run's long call holds the endpoint: this answer comes after the connect bound
                b = json.dumps({"result": {"content": [{"type": "text", "text": "{}"}]}}).encode()
                h.send_response(200); h.send_header("Content-Length", str(len(b))); h.end_headers(); h.wfile.write(b)
            def log_message(h, *a): pass
        srv = http.server.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
        s.addCleanup(srv.server_close); s.addCleanup(srv.shutdown); s.addCleanup(setattr, d, "CONNECT", d.CONNECT)
        d.CONNECT = 0.2
        s.assertEqual(d.call(srv.server_address[1], "press_key", key="ENTER"), "{}")
        s.assertEqual(got, ["press_key"])   # sent once, answered in its turn, never given up on

    def test_a_refusal_page_returns_not_hangs(s):  # server-token-auth-14: on 'Incorrect username or password.' Enter did nothing and token waited forever
        d, sent = s.fake(["LOGIN_SCREEN"])   # Enter starts no attempt
        s.assertTrue(d.token(1).startswith("FAILED: Enter started no login"))
        s.assertEqual([(n, a) for n, a in sent if n != "get_client_state"], [("press_key", {"key": "ENTER"})])   # h-desktops-token-login: Play alone, no Escape, typing or click (a ban page's top button opens the user's browser)
        d, sent = s.fake(["LOGIN_SCREEN"] * 2 + ["LOGGING_IN", "LOGGED_IN"])   # the session's Play page: Enter logs in
        s.assertEqual(d.token(1), "LOGGED_IN"); s.assertEqual([n for n, a in sent if n in ("press_key", "type_chat", "click")], ["press_key"])
        d, _ = s.fake(["LOGIN_SCREEN"] * 2 + ["LOGGING_IN", "LOGIN_SCREEN"])   # a refusal: back at the login screen
        s.assertEqual(d.token(1), "FAILED: back at the login screen: the server refused the token")
        d, _ = s.fake(["LOGIN_SCREEN"])   # the form's Enter started no attempt
        s.assertTrue(d.login(1, "u", "p").startswith("FAILED: Enter started no login"))

    def test_a_cancelled_call_starts_the_login_again_not_gone(s):  # sweep-47 P0-a: keep read a run's cancel of its type_chat as the endpoint gone and stopped
        d, sent = s.fake(["LOGIN_SCREEN"] * 4 + ["LOGGING_IN", "LOGGED_IN"])
        fake, cut = d.call, [True]
        def call(port, name, **a):
            if name == "type_chat" and cut and cut.pop():
                raise d.Cancelled("type_chat: Cancelled")
            return fake(port, name, **a)
        d.call = call
        s.assertEqual(d.whole(lambda: d.login(1, "u", "p")), "LOGGED_IN")
        s.assertEqual([a["text"] for n, a in sent if n == "type_chat"], ["u", "p"])   # the cancelled user field typed again, then the password
        s.assertEqual(sum(n == "press_key" and a["key"] == "ESCAPE" for n, a in sent), 2)   # the login from its start
        s.assertTrue(issubclass(d.Cancelled, d.Refused))

    def test_a_call_the_endpoint_left_unanswered_starts_the_login_again(s):  # the endpoint answers -32002 past its bound (a run's walk_to held the desktop): the keeper goes on
        import desktop_login as d, io
        s.addCleanup(setattr, d.urllib.request, "urlopen", d.urllib.request.urlopen); s.addCleanup(setattr, d, "devtoken", d.devtoken)
        d.devtoken = lambda _: "tk"
        d.urllib.request.urlopen = lambda req, timeout: io.BytesIO(b'{"jsonrpc":"2.0","id":1,"error":{"code":-32002,"message":"a call ahead held the desktop past 20 s"}}')
        with s.assertRaises(d.Cancelled):
            d.call(7780, "press_key", key="ENTER")

    def test_keep_logs_a_logged_out_desktop_in_again(s):  # genie-review-355-cickwdoqbbpt88aaaabeelmng-1: 20+ min at the login screen after an idle logout
        import desktop_login as d
        def run(states, results, readies):   # the game state per read (then the desktop is gone), act's result per login, ready() per probe
            seen, results, readies = iter(states), iter(results), iter(readies)
            def call(port, name, **a):
                g = next(seen, None)
                if g is None:
                    raise d.urllib.error.URLError(ConnectionRefusedError())   # the desktop stopped
                return json.dumps({"gameState": g})
            s.addCleanup(setattr, d, "call", d.call); s.addCleanup(setattr, d.time, "sleep", d.time.sleep)
            d.call, d.time.sleep = call, lambda _: None
            acts = []
            with s.assertRaises(d.urllib.error.URLError):
                d.keep(1, lambda: acts.append(1) or next(results), lambda since: next(readies))
            return len(acts)
        s.assertEqual(run(["LOGIN_SCREEN", "LOGGED_IN", "LOADING", "LOGGED_IN", "LOGIN_SCREEN", "LOGGED_IN", "LOGIN_SCREEN"], ["LOGGED_IN"] * 2, []), 2)   # each logout
        s.assertEqual(run(["LOGGED_IN"] + ["LOGIN_SCREEN"] * 4, ["FAILED", "LOGGED_IN"], [False, False, True, True]), 2)   # the server was restarting: tried again once it is ready
        s.assertEqual(run(["LOGGED_IN", "LOGIN_SCREEN", "LOGIN_SCREEN", "LOGIN_SCREEN", "LOGGED_IN"], ["FAILED"], [False] * 9), 1)   # the same server refused it: no retry; another's login waits for the next logout
        out = ["LOGGED_IN", "Logout", "LOGIN_SCREEN"]   # act's FAILED left it logged in (sweep-46: no inventory, the keeper then waited for a logout forever); the logout's call, its wait
        s.assertEqual(run(["LOGGED_IN", "LOGIN_SCREEN"] + out, ["FAILED", "LOGGED_IN"], []), 2)   # logged out and in again at once
        s.assertEqual(run(["LOGGED_IN", "LOGIN_SCREEN"] + out * 2 + ["LOGIN_SCREEN"] * 3, ["FAILED"] * 2, [False] * 9), 2)   # twice: it waits for the server like any failure
        up = SRC.split("\nup() {")[1].split("\n}")[0]; down = SRC.split("\ndown() {")[1].split("\n}")[0]
        s.assertGreater(up.index("keep \""), up.rindex('login "$(cut -d: -f2'))   # after up's own logout and login
        s.assertLess(down.index("unkeep"), down.index("desktops_remove"))   # down stops them first
        d = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, d); (d / "desktop_login.py").write_text("import time; time.sleep(60)\n")
        ps = {k: subprocess.Popen(["python3", str(d / "desktop_login.py"), "7781", "keep", f"server-{k}", "h", "h"]) for k in (f"t{os.getpid()}", f"t{os.getpid()}-b")}   # slugs of this test alone
        for q in ps.values(): s.addCleanup(q.kill)
        fn = next(l for l in SRC.splitlines() if l.startswith("unkeep()"))
        for _ in range(2):   # a second down finds none and still goes on: an unkeep that failed under set -e left the server up
            s.assertEqual(subprocess.run(["bash", "-c", f"set -euo pipefail; slug=t{os.getpid()}\n{fn}\nunkeep; echo on"], capture_output=True, text=True).stdout, "on\n")
        s.assertIsNotNone(ps[f"t{os.getpid()}"].wait(10)); s.assertIsNone(ps[f"t{os.getpid()}-b"].poll())   # its own keeper, never another slug's
        down = SRC.split("\ndown() {")[1].split("\n}")[0]   # restart is down and up: down stops the keepers before the desktops and waits for the saves
        s.assertLess(down.index("unkeep"), down.index("desktops_remove")); s.assertLess(down.index("desktops_remove"), down.index("offline"))
        s.assertIn("with locked(port):", (HERE / "desktop_login.py").read_text().split("def keep")[1])   # restart's login and keep's take turns

    def test_acts_only_while_its_instance_owns_the_port(s):  # sweep-42: a login or keeper left by an earlier up drove the desktop another run's up then claimed on its port
        import desktop_login as d, io
        t = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, t); (t / "run/1").mkdir(parents=True); o = t / "run/1/owner"; o.write_text("a 1-1\n")
        s.addCleanup(os.environ.pop, "DESKTOP_DIR", None); os.environ["DESKTOP_DIR"] = str(t)
        s.addCleanup(setattr, d.urllib.request, "urlopen", d.urllib.request.urlopen); s.addCleanup(setattr, d.time, "sleep", d.time.sleep); s.addCleanup(setattr, d, "claim", None)
        sent = []
        def urlopen(req, timeout):
            sent.append(json.loads(req.data)["params"]["name"])
            return io.BytesIO(json.dumps({"result": {"content": [{"type": "text", "text": '{"gameState": "LOGGED_IN"}'}]}}).encode())
        d.urllib.request.urlopen, d.time.sleep = urlopen, lambda _: o.write_text("a 2-2\n")   # while keep waits for a logout, down removes the instance and this slug's next up claims it
        d.claim = d.owner(7780)
        s.assertEqual(json.loads(d.call(7780, "get_client_state"))["gameState"], "LOGGED_IN")
        with s.assertRaises(d.Gone):
            d.keep(7780, lambda: "LOGGED_IN", lambda since: True)
        s.assertEqual(sent, ["get_client_state"] * 3)   # the call, keep's two reads before its wait slept; nothing once the claim changed
        o.unlink()
        with s.assertRaises(d.Gone):
            d.call(7780, "press_key", key="ENTER")
        r = subprocess.run(["python3", str(HERE / "desktop_login.py"), "7780", "logout"], capture_output=True, text=True, env={**os.environ, "DESKTOP_DIR": str(t)})
        s.assertEqual((r.returncode, r.stdout), (1, "FAILED: no desktop instance owns port 7780\n"))   # no instance: it sends nothing

    def test_logout_uses_the_logout_button_not_a_command(s):  # the server has no ::drop; relog hung on it
        d, sent = s.fake(["LOGGED_IN", "LOGIN_SCREEN"])
        s.assertEqual(d.logout(1), "LOGIN_SCREEN")
        s.assertFalse([a for n, a in sent if n == "type_chat"])
        s.assertIn(("invoke_menu_action", {"param0": -1, "param1": d.LOGOUT_BUTTON, "type": "CC_OP", "identifier": 1, "option": "Logout"}), sent)

    def test_up_sets_members_while_its_characters_are_offline(s):  # the logout save wrote members back to false over an update made in game
        up = SRC.split("\nup() {")[1].split("\n}")[0]
        s.assertLess(up.index('desktop_login.py" "$(cut -d: -f2 <<< "$c")" logout'), up.index("  offline\n"))
        s.assertLess(up.index("  offline\n"), up.index("set members = true"))
        s.assertLess(up.index("set members = true"), up.rindex('login "$(cut -d: -f2 <<< "${desktops[$i]}")"'))
        s.assertNotIn("::", (HERE / "desktop_login.py").read_text())

    def test_a_login_that_made_another_account_logs_in_again(s):  # quest-restlessghost-9: a lost key made a stray first account, the rights update missed the real one and the relogin made it with rights ''
        t = SRC; fn = t[t.index("login() {"):t.index("offline() {")]
        for site in ('login "$dt"', 'login "$(cut -d: -f2 <<< "${desktops[$i]}")"'):
            s.assertIn(site, t)   # every login of up (restart is an up)
        s.assertEqual(t.count('desktop_login.py" "$1" token'), 1)   # no login but through it, by token (Play alone)
        made = lambda *rows: subprocess.run(["bash", "-c", f'set -euo pipefail\nf=$(mktemp); trap "rm -f $f" EXIT; printf "%s\\n" {" ".join(repr(r) for r in rows)} > $f\nsql() {{ case $1 in *max*) echo 0 ;; *) head -1 $f; sed -i 1d $f ;; esac; }}   # each read in its own subshell: the rows a file\npython3() {{ echo "py $3"; }}\nself=.\n{fn}\nlogin 7786 h1'],
                                            capture_output=True, text=True).stdout
        s.assertEqual(made("h1"), "py token\n")
        s.assertEqual(made("h1x h1", "h1"), "py token\nlogin on 7786 made another account than h1: logging in again\npy logout\npy token\n")
        s.assertEqual(made("h", "h1"), "py token\nlogin on 7786 made another account than h1: logging in again\npy logout\npy token\n")   # no row of the account yet

class Repo(unittest.TestCase):
    def setUp(s):
        s.repo = tempfile.mkdtemp()
        git(s.repo, "init", "-q", "-b", "main")
        git(s.repo, "config", "user.email", "t@t"); git(s.repo, "config", "user.name", "t")
        s.write(".data/gamevals-binary/max-ids.toml", "[max_ids]\nvarp = 100\narea = 10\n")
        s.write("content/a/gamevals.toml", "[gamevals.varp]\nquest_a = 101\n")
        s.write(".github/pull_request_template.md", "## Summary\n## Checklist\n")
        s.write("mod/src/main/kotlin/A.kt", "fun a() {}\n")
        s.commit("feat: base")
        git(s.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        s.base = git(s.repo, "rev-parse", "HEAD")
        s.hd = tempfile.mkdtemp()
        Path(s.hd, "hd.yaml").write_text("repos:\n  fork:\n    pins:\n      - x\n")   # the pins come from hd.yaml alone, never the env
        s.env = {"CLONE": s.repo, "HD_ROOT": s.hd, "SLUG": "s1", "BASE": s.base}

    def tearDown(s):
        shutil.rmtree(s.repo, ignore_errors=True); shutil.rmtree(s.hd, ignore_errors=True)

    def write(s, path, text):
        p = Path(s.repo) / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        git(s.repo, "add", path)

    def commit(s, msg):
        git(s.repo, "commit", "-q", "-m", msg)
        return git(s.repo, "rev-parse", "HEAD")

    def row(s, script, *args, **env):
        r = subprocess.run([sys.executable, str(HERE / script), *args], capture_output=True, text=True, env={**os.environ, **s.env, **env})
        return r.returncode, r.stdout + r.stderr


class Gamevals(Repo):
    def test_clash_with_a_pin_and_assign(s):
        s.write("content/b/gamevals.toml", "[gamevals.varp]\nquest_b = 102\n")
        pin = s.commit("feat: pin takes 102")
        git(s.repo, "update-ref", "refs/remotes/fork/x", pin)
        git(s.repo, "reset", "-q", "--hard", s.base)
        s.write("content/c/gamevals.toml", "[gamevals.varp]\nquest_c = 102\nquest_d = -1\n")
        head = s.commit("feat: ours takes 102 too")
        rc, out = s.row("gamevals.py", "check", head)
        s.assertEqual(rc, 1); s.assertIn("varp.quest_c = 102 is varp.quest_b on x", out)
        rc, out = s.row("gamevals.py", "assign", s.repo)
        s.assertEqual(rc, 0); s.assertIn("varp.quest_d = 65535", out)
        s.assertIn("quest_d = 65535", (Path(s.repo) / "content/c/gamevals.toml").read_text())

    def test_missing_max_ids_fails_loudly(s):
        git(s.repo, "rm", "-q", ".data/gamevals-binary/max-ids.toml")
        head = s.commit("fix: no maxes")
        rc, out = s.row("gamevals.py", "check", head)
        s.assertEqual(rc, 1); s.assertIn("max-ids.toml missing", out)


class Text(Repo):
    def test_commits_texts_dupes_evidence(s):
        s.write("mod/src/main/kotlin/A.kt", "fun a() { invAdd(x) }\n")
        git(s.repo, "commit", "-q", "-m", "add a thing\n\nClaude-Session: abc\nCo-Authored-By: C <c@c>")
        head = git(s.repo, "rev-parse", "HEAD")
        ev = tempfile.mkdtemp()
        rc, out = s.row("text.py", "commits", HEAD=head)
        s.assertEqual(rc, 1); s.assertIn("not feat: or fix:", out); s.assertIn("Claude-Session trailer", out)
        rc, out = s.row("text.py", "dupes", HEAD=head)
        s.assertEqual(rc, 1); s.assertIn("item flow in mod/src/main/kotlin/A.kt: invAdd", out); s.assertIn("mod moves items with no test", out)
        rc, out = s.row("text.py", "evidence", EVIDENCE=ev)
        s.assertEqual(rc, 1); s.assertIn("accuracy.md missing", out)
        for n, t in (("accuracy.md", "spec"), ("pr-title.txt", "feat: x"), ("pr-body.md", "## Summary\nsee AlexPerrin/OpenRune-Server#9"), ("pr-comment.md", "Updated to " + head[:9])):
            (Path(ev) / n).write_text(t)
        rc, out = s.row("text.py", "texts", EVIDENCE=ev, HEAD=head)
        s.assertEqual(rc, 1); s.assertIn("lacks the template section 'Checklist'", out); s.assertIn("pr-body.md links a fork PR", out)
        (Path(ev) / "pr-body.md").write_text("## Summary\n## Checklist\n")
        rc, out = s.row("text.py", "texts", EVIDENCE=ev, HEAD=head)
        s.assertEqual((rc, out.strip()), (0, "texts: ok"))
        (Path(ev) / "pr-body.md").write_text(""); (Path(ev) / "pr-comment.md").write_text("> why?\n\n@rev because.")   # a reply on an open PR
        s.assertEqual(s.row("text.py", "texts", EVIDENCE=ev, HEAD=head, PR="7")[0], 0)
        (Path(ev) / "pr-reply-IC_1.md").write_text("> q\n\nsee fork PR #12")                                       # a reply the one comment carries
        rc, out = s.row("text.py", "texts", EVIDENCE=ev, HEAD=head, PR="7"); s.assertEqual(rc, 1); s.assertIn("pr-reply-IC_1.md links a fork PR", out)
        (Path(ev) / "pr-reply-IC_1.md").unlink()
        s.assertEqual(s.row("text.py", "evidence", EVIDENCE=ev, PR="7")[0], 0)
        s.assertEqual(s.row("text.py", "evidence", EVIDENCE=ev)[0], 1)
        s.write("mod/src/test/kotlin/ATest.kt", "class ATest\n")
        head = s.commit("fix: test the flow")
        s.assertEqual(s.row("text.py", "dupes", HEAD=head)[0], 0)
        s.write("gen/src/main/kotlin/G.kt", "fun g() { invDel(x) }\n")
        s.write("gen/src/integration/kotlin/GTest.kt", "class GTest\n")
        head = s.commit("fix: an integration dupe test")
        s.assertEqual(s.row("text.py", "dupes", HEAD=head)[0], 0)
        shutil.rmtree(ev)

    def test_a_head_merging_staging_owns_only_what_neither_main_nor_staging_has(s):  # run 369: staging's untested TestCommands.kt counted as a staging repair's own
        git(s.repo, "checkout", "-q", "-b", "staging")
        s.write("cmd/src/main/kotlin/C.kt", "fun c() { invAdd(x) }\n")
        s.commit("staging: a fork-only command")
        git(s.repo, "checkout", "-q", "main")
        s.write("up/U.kt", "upstream moved on\n")
        main = s.commit("feat: upstream")
        git(s.repo, "checkout", "-q", "-b", "repair", "staging"); git(s.repo, "merge", "-q", "--no-edit", main)   # the repair head; staging not moved yet
        head = git(s.repo, "rev-parse", "HEAD")
        s.assertEqual(s.row("text.py", "dupes", HEAD=head, BASE=main), (0, "dupes: ok\n"))
        s.assertEqual(s.row("text.py", "commits", HEAD=head, BASE=main)[0], 0)
        git(s.repo, "checkout", "-q", "-b", "h", main)   # a head off upstream main, untested, still fails
        s.write("mod/src/main/kotlin/A.kt", "fun a() { invDel(x) }\n")
        head = s.commit("feat: a flow")
        rc, out = s.row("text.py", "dupes", HEAD=head, BASE=main)
        s.assertEqual(rc, 1); s.assertIn("mod moves items with no test", out)
        git(s.repo, "checkout", "-q", "staging"); git(s.repo, "merge", "-q", "--no-edit", head)   # staged: a regate still sees it
        s.assertEqual(s.row("text.py", "dupes", HEAD=head, BASE=main)[0], 1)

    def test_commits_after_an_existing_prs_head(s):
        s.write("mod/src/test/kotlin/T.kt", "x\n")
        public = s.commit("test: already public on the PR")
        git(s.repo, "update-ref", "refs/remotes/fork/content/x", public)
        s.write("mod/src/main/kotlin/A.kt", "fun a() { 1 }\n")
        head = s.commit("fix: the review finding")
        rc, out = s.row("text.py", "commits", HEAD=head)
        s.assertEqual(rc, 1); s.assertIn("already public", out)
        rc, out = s.row("text.py", "commits", HEAD=head, PR="9", PUBLIC_BRANCH="content/x")
        s.assertEqual(rc, 0, out)
        git(s.repo, "checkout", "-q", "-b", "side", public); s.write("mod/src/main/kotlin/B.kt", "x\n"); main = s.commit("fix: main moved")
        git(s.repo, "checkout", "-q", "-"); git(s.repo, "merge", "-q", "--no-edit", main)   # the track's `merge main in`: no subject of its own
        rc, out = s.row("text.py", "commits", HEAD=git(s.repo, "rev-parse", "HEAD"), PR="9", PUBLIC_BRANCH="content/x")
        s.assertEqual(rc, 0, out)

    def test_dupes_after_an_existing_prs_head(s):  # cannon-354: the dev ref at #354's live head failed on the whole PR's item flows
        s.write("mod/src/main/kotlin/A.kt", "fun a() { invAdd(x) }\n")
        public = s.commit("feat: already public on the PR")
        git(s.repo, "update-ref", "refs/remotes/fork/content/x", public)
        s.assertEqual(s.row("text.py", "dupes", HEAD=public)[0], 1)
        s.assertEqual(s.row("text.py", "dupes", HEAD=public, PR="9", PUBLIC_BRANCH="content/x"), (0, "dupes: ok\n"))
        s.write("mod/src/main/kotlin/A.kt", "fun a() { invAdd(x) }\nfun b() { invDel(y) }\n")
        head = s.commit("fix: the review finding")
        rc, out = s.row("text.py", "dupes", HEAD=head, PR="9", PUBLIC_BRANCH="content/x")
        s.assertEqual(rc, 1); s.assertIn("item flow in mod/src/main/kotlin/A.kt: invDel\n", out)


class TestVerb(Repo):
    def test_runs_the_touched_modules_tests_and_spotless_with_the_copys_git_readable(s):  # a dev ran gradle by hand; spotless's JGit could not open the worktree
        s.write("mod/build.gradle.kts", "")
        s.write("other/build.gradle.kts", "")
        s.commit("feat: modules"); git(s.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        s.write("mod/src/main/kotlin/A.kt", "fun a() { 1 }\n")
        tc = s.commit("feat: touch mod")
        copy = Path(s.repo) / ".worktrees/s1-build"; git(s.repo, "worktree", "add", "-q", "--detach", str(copy), tc)
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "bin").mkdir(); (root / "st").mkdir(); change(root, "s1")
        # a fake docker: the container's view of the copy's git (as spotless reads it), the gradle tasks, a test report
        (root / "bin/docker").write_text(f"""#!/bin/bash
case " $* " in *" chown "*) exit 0 ;; esac
for a in "$@"; do case $a in *:{copy}/.git:ro) gd=$(sed 's/^gitdir: //' "${{a%%:*}}") ;; esac; done
git --git-dir="$gd" rev-parse HEAD origin/main > {root}/git; git --git-dir="$gd" status --porcelain >> {root}/git
while [ "$1" != _ ]; do shift; done; shift; echo "$@" > {root}/tasks
mkdir -p {copy}/mod/build/test-results/test; echo '<testsuite name="ATest" tests="3" skipped="0" failures="0" errors="0" x>' > {copy}/mod/build/test-results/test/a.xml
""")
        (root / "bin/docker").chmod(0o755)
        src = SRC
        fn = lambda name: f"{name}() {{" + src.split(f"\n{name}() {{")[1].split("\n}")[0] + "\n}"
        line = lambda pre: next(l for l in src.splitlines() if l.startswith(pre))
        script = "\n".join(["set -euo pipefail", f"slug=s1; repo={s.repo}; copy={copy}; state={root}/st; root={root}; T=t1; tc={tc}",
                            line("atomic()"), line("record()"), line("size="), line("fault="), line("ooms()"), fn("hosted"), fn("slot"), line("box()"), line("projects()"), line("projdir()"), "build() { :; }", fn("central"), fn("filestore"), fn("gradle_check"), line("tests()"), "tests"])
        r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env={**os.environ, "EVIDENCE": "", "PATH": f"{root}/bin:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        s.assertEqual((root / "tasks").read_text().split(), [":mod:test", ":mod:spotlessCheck"])
        s.assertEqual((root / "git").read_text().split(), [tc, git(s.repo, "rev-parse", "origin/main")])
        s.assertIn('<testsuite name="ATest" tests="3"', (root / "evidence/s1/test.log").read_text())
        s.assertTrue(json.loads((root / "st/test.json").read_text())["ok"])
        (copy / "other/build/test-results/test").mkdir(parents=True); (copy / "other/build/test-results/test/old.xml").write_text('<testsuite name="Old" tests="1" skipped="0" failures="1" errors="0">')
        r = subprocess.run(["bash", "-c", script + " :other"], capture_output=True, text=True, env={**os.environ, "EVIDENCE": "", "PATH": f"{root}/bin:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 0, r.stderr); s.assertEqual((root / "tasks").read_text().split(), [":other:test", ":other:spotlessCheck"])
        s.assertNotIn("Old", (root / "evidence/s1/test.log").read_text())   # a report this run did not write is never read

    def test_the_spotless_row_fails_on_old_lint_in_a_touched_file(s):  # server-npc-examine-without-overlay failed CI Formatting three times: the ratchet saw a touched file's old lint
        s.write("mod/build.gradle.kts", ""); s.write("mod/src/main/kotlin/B.kt", "fun  b()  {}\n")   # old lint, on main before the change
        s.write("other/build.gradle.kts", "")
        s.commit("feat: modules"); git(s.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        s.write("mod/src/main/kotlin/B.kt", "fun  b()  {}\nfun c() {}\n")
        tc = s.commit("feat: touch B")
        copy = Path(s.repo) / ".worktrees/s1-build"
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "bin").mkdir(); (root / "st").mkdir(); change(root, "s1")
        # a fake gradle in docker: spotlessCheck of a module whose file holds the double space fails, as the ratchet does on a touched file;
        # the slug was never built: its volume is docker's new root-owned one until the verb chowns it to the run's user
        (root / "bin/docker").write_text(f"""#!/bin/bash
case " $* " in *" -v gradle-"?":/gradle "*" chown 1000:1000 /gradle "*) touch {root}/owned; exit 0 ;; esac
[ -e {root}/owned ] || {{ echo "/gradle: Permission denied"; exit 1; }}
while [ "$1" != _ ]; do shift; done; shift; echo "$@" > {root}/tasks
for t; do m=${{t#:}}; m=${{m%:spotlessCheck}}; ! grep -rq 'fun  ' {copy}/$m/src 2>/dev/null || {{ echo "> Task :$m:spotlessCheck FAILED: format violations"; exit 1; }}; done
""")
        (root / "bin/docker").chmod(0o755)
        src = SRC
        fn = lambda name: f"{name}() {{" + src.split(f"\n{name}() {{")[1].split("\n}")[0] + "\n}"
        line = lambda pre: next(l for l in src.splitlines() if l.startswith(pre))
        script = "\n".join(["set -euo pipefail", f"slug=s1; repo={s.repo}; copy={copy}; state={root}/st; root={root}; T=t1; hd=:",
                            line("atomic()"), line("record()"), line("size="), line("fault="), line("ooms()"), fn("hosted"), fn("slot"), line("box()"), line("projects()"), line("projdir()"), "build() { echo build >&2; exit 9; }",
                            f"tree() {{ tc={tc}; }}", fn("central"), fn("filestore"), fn("gradle_check"), fn("spotless"), "spotless"])
        run = lambda: subprocess.run(["bash", "-c", script], capture_output=True, text=True, env={**os.environ, "EVIDENCE": "", "PATH": f"{root}/bin:{os.environ['PATH']}"})
        r = run()
        s.assertEqual(r.returncode, 1, r.stderr + r.stdout)
        s.assertEqual((root / "tasks").read_text().split(), [":mod:spotlessCheck"])   # no test task, only the touched module
        s.assertIn("violations", (root / "evidence/s1/spotless.log").read_text())
        s.assertFalse(json.loads((root / "st/spotless.json").read_text())["ok"])
        tree = git(s.repo, "rev-parse", f"{tc}^{{tree}}")   # a tree for TCOMMIT (as a gate's T once was): the row fails, never "no module touched"
        r = subprocess.run(["bash", "-c", script.replace(tc, tree)], capture_output=True, text=True, env={**os.environ, "EVIDENCE": "", "PATH": f"{root}/bin:{os.environ['PATH']}"})
        s.assertNotEqual(r.returncode, 0); s.assertNotIn("no module touched", r.stdout)
        s.write("mod/src/main/kotlin/B.kt", "fun b() {}\nfun c() {}\n"); tc2 = s.commit("fix: the lint"); script = script.replace(tc, tc2)
        r = run()
        s.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        s.assertTrue(json.loads((root / "st/spotless.json").read_text())["ok"])

    def test_a_pack_directory_is_the_project_settings_names(s):  # quest-ernestthechicken: no module named ran :content:areas:city:draynor:pack:test, a project settings names draynor-pack
        fns = "\n".join(l for l in SRC.splitlines() if l.startswith(("projects()", "projdir()")))
        copy = tempfile.mkdtemp(); s.addCleanup(shutil.rmtree, copy)
        for d in ("content/quest", "content/areas/city/draynor", "content/areas/city/draynor/pack"):
            Path(copy, d).mkdir(parents=True); Path(copy, d, "build.gradle.kts").write_text("")
        files = "content/quest/src/main/kotlin/A.kt content/areas/city/draynor/src/test/kotlin/B.kt content/areas/city/draynor/pack/src/main/resources/c.toml README.md"
        r = subprocess.run(["bash", "-c", f'set -euo pipefail; copy={copy}\n{fns}\nprojects {files}; for p in $(projects {files}); do projdir $p; done'], capture_output=True, text=True)
        s.assertEqual(r.stdout.split(), [":content:areas:city:draynor", ":content:areas:city:draynor:draynor-pack", ":content:quest",
                                         "content/areas/city/draynor", "content/areas/city/draynor/pack", "content/quest"], r.stderr)


class Snapshot(Repo):
    def test_build_snapshot_keeps_tracked_files_under_ignored_paths(s):
        s.write(".gitignore", "generated/\n")
        p = Path(s.repo) / "generated/build.gradle.kts"; p.parent.mkdir(); p.write_text("x\n")
        git(s.repo, "add", "-f", "generated/build.gradle.kts"); s.commit("feat: a tracked file under an ignored path")
        git(s.repo, "worktree", "add", "-q", ".worktrees/s1")
        (Path(s.repo) / ".worktrees/s1/new.kt").write_text("y\n")
        root = tempfile.mkdtemp(); out = Path(root) / "ls"; change(root, "s1")
        (Path(root) / "harness/hd.py").write_text(f"import subprocess,sys\nopen({str(out)!r},'w').write(subprocess.run(['git','-C',{s.repo!r},'ls-tree','-r','--name-only',sys.argv[4]],capture_output=True,text=True).stdout)\nsys.exit(1)\n")
        subprocess.run(["bash", str(HERE.parent / "track.sh"), "build", "s1"], capture_output=True, env={**os.environ, "CLONE": s.repo, "HD_ROOT": root, "T": ""})
        files = out.read_text().split()
        s.assertIn("generated/build.gradle.kts", files); s.assertIn("new.kt", files)
        shutil.rmtree(root)

    def test_tree_is_the_rows_tcommit_and_any_checkout_of_the_clone_names_it(s):  # server-cache-clientscript-name-hash-10: spotless with CLONE the brief's Clone (the dev worktree) failed on 'dev/<slug> is already used'; a T passed as TCOMMIT failed late
        git(s.repo, "worktree", "add", "-q", "-b", "dev/s1", ".worktrees/s1")
        root = tempfile.mkdtemp(); s.addCleanup(shutil.rmtree, root); change(root, "s1")
        (Path(root) / "harness/hd.py").write_text("import sys\nprint('snap-tree', sys.argv[4])\n")
        head, t = git(s.repo, "rev-parse", "HEAD"), git(s.repo, "rev-parse", "HEAD^{tree}")
        tree = lambda clone, *a, **e: subprocess.run(["bash", str(HERE.parent / "track.sh"), "tree", "s1", *a], capture_output=True, text=True, env={**os.environ, "CLONE": clone, "HD_ROOT": root, "T": "", "TCOMMIT": "", **e})
        for clone in (s.repo, f"{s.repo}/.worktrees/s1"):
            r = tree(clone); s.assertEqual((r.returncode, r.stdout.split()[1:]), (0, ["snap-tree"]), r.stderr)   # no TCOMMIT: the dev's working copy
            r = tree(clone, TCOMMIT=head); s.assertEqual(r.stdout.split(), [head, t], r.stderr)   # a row's env
        r = tree(s.repo, t); s.assertEqual(r.returncode, 2); s.assertIn("not a commit", r.stderr)


class GateCi(Repo):
    WF = "jobs:\n  b:\n    steps:\n      - uses: actions/checkout@v7\n      - name: Set up Gradle\n        uses: gradle/actions/setup-gradle@v6\n      - run: ./gradlew test\n"
    RUNS = staticmethod(lambda st: f'HTTP/2.0 200 OK\nEtag: W/"{st or "running"}"\n\n' + json.dumps({"workflow_runs": [{"name": w, "status": "completed" if st else "in_progress", "conclusion": st or None} for w in ("CI", "Formatting")]}))
    GREEN = [RUNS("success")]

    @staticmethod
    def fake_gh(bin, answers):  # `gh api` prints answers[n] at its n-th call (the last repeats), each call's args in bin/calls; sleep is free
        for i, a in enumerate(answers): (bin / f"a{i}").write_text(a)
        (bin / "gh").write_text(f'#!/bin/sh\nd=$(dirname "$0"); echo "$*" >> "$d/calls"; case "$1 $2" in "release view") cat "$d/assets" 2>/dev/null; exit 0 ;; esac; [ "$1" = api ] || exit 0\ncase "$2" in */jobs) cat "$d/step"; exit 0 ;; esac\n'
                                f'n=$(grep -c "^api" "$d/calls"); [ $n -gt {len(answers)} ] && n={len(answers)}; cat "$d/a$((n-1))"; case $(head -1 "$d/a$((n-1))") in *" 200 "*) ;; *) exit 1 ;; esac\n')
        (bin / "sleep").write_text('#!/bin/sh\necho "$1" >> "$(dirname "$0")/sleeps"\n')
        for f in ("gh", "sleep"): (bin / f).chmod(0o755)

    def gate(s, answers, step="", env={}):  # gate-ci of s1 against a fake GitHub (step: a failed run's failed step): (result, gh calls, sleeps)
        for f in ("ci", "format"): s.write(f".github/workflows/{f}.yml", s.WF)
        t = s.commit("ci")
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, answers); (bin / "step").write_text(step + "\n")
        root = tempfile.mkdtemp(); change(root, "s1")
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "gate-ci"], capture_output=True, text=True,
                           env={**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "PATH": f"{bin}:{os.environ['PATH']}", **env})
        out = [(bin / f).read_text().splitlines() if (bin / f).exists() else [] for f in ("calls", "sleeps")]
        for d in (fork, bin, root): shutil.rmtree(d)
        return r, *out

    def test_status_is_one_conditional_read_free_while_unchanged(s):  # 30 s polls of gh run list per workflow per gate drained the 5000/h quota
        r, calls, _ = s.gate([s.RUNS(None), "HTTP/2.0 304 Not Modified\n\n", "HTTP/2.0 304 Not Modified\n\n", s.RUNS("success")])
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        api = [c for c in calls if c.startswith("api")]
        s.assertEqual(len(api), 4); s.assertTrue(all("actions/runs?branch=gate/s1&head_sha=" in c for c in api))
        s.assertNotIn("If-None-Match", api[0]); s.assertTrue(all('If-None-Match: W/"running"' in c for c in api[1:]), api)  # a 304 keeps the ETag
        s.assertFalse([c for c in calls if c.startswith(("run list", "workflow run"))])  # runs were listed: nothing dispatched

    def test_ci_runs_the_prs_own_candidate_not_stagings(s):  # h-fork-candidate-on-staging: proved on staging, the PR's CI on upstream main
        for f in ("ci", "format"): s.write(f".github/workflows/{f}.yml", s.WF)
        pr = s.commit("the PR on main"); s.write("staged.kt", "x")   # gate()'s own commit (TCOMMIT) holds more: staging's
        r, _, _ = s.gate(s.GREEN, env={"PR_TCOMMIT": pr})
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr); s.assertIn(f"(T {pr})", r.stdout)
        r, calls, _ = s.gate(s.GREEN, env={"PR_TCOMMIT": "conflict: a.kt"})
        s.assertEqual(r.returncode, 1); s.assertIn("does not merge with upstream main, conflict: a.kt", r.stdout); s.assertEqual(calls, [])

    def test_a_quota_refusal_holds_the_row_until_githubs_reset(s):  # genie-355-bank-lamp's gate failed 'HTTP 403: API rate limit exceeded'
        r, calls, sleeps = s.gate(['HTTP/2.0 403 Forbidden\nX-Ratelimit-Remaining: 0\nX-Ratelimit-Reset: 9999999999\n\n{"message":"API rate limit exceeded"}', s.RUNS("success")])
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr); s.assertIn("held until its reset", r.stdout)
        s.assertGreater(int(sleeps[0]), 10 ** 9)

    def test_a_failed_run_fails_the_row_and_no_run_dispatches_each_workflow_once(s):
        r, calls, _ = s.gate(['HTTP/2.0 200 OK\nEtag: "0"\n\n{"workflow_runs": []}', 'HTTP/2.0 304 Not Modified\n\n', s.RUNS("failure")])
        s.assertEqual(r.returncode, 1); s.assertIn("CI failure/completed", r.stdout)
        s.assertEqual(sorted(c.split()[2] for c in calls if c.startswith("workflow run")), ["CI", "Formatting"])

    FAILED = staticmethod(lambda att, c="failure": f'HTTP/2.0 200 OK\nEtag: W/"f{att}"\n\n' + json.dumps({"workflow_runs": [
        {"name": "CI", "status": "completed", "conclusion": c, "id": 7, "run_attempt": att}, {"name": "Formatting", "status": "completed", "conclusion": "success", "id": 8}]}))

    def test_a_run_failed_outside_the_head_is_re_run_not_the_heads_fail(s):  # GitHub's checkout failed, not the head: CI runs 41357682052, 41357793032
        r, calls, _ = s.gate([s.FAILED(1), s.FAILED(1), s.RUNS("success")], step="Checkout repository")
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr); s.assertIn("a step the head does not touch: re-run", r.stdout)
        s.assertEqual([c for c in calls if c.startswith("run rerun")], ["run rerun 7 --failed -R " + calls[0].split("repos/")[1].split("/actions")[0]])  # once per attempt

    def test_a_run_stopped_in_the_cache_step_is_re_run_not_the_heads_fail(s):  # ci.yml's 30-min timeout cancelled the openrs2 download: CI runs 41364734674, 41362166155
        r, calls, _ = s.gate([s.FAILED(1, "cancelled"), s.FAILED(1, "cancelled"), s.RUNS("success")], step="Cache game data")
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr); s.assertEqual(len([c for c in calls if c.startswith("run rerun 7")]), 1)

    def test_a_cache_step_failure_is_the_heads_when_the_head_changes_its_input(s):
        base = git(s.repo, "rev-parse", "HEAD"); s.write("game.example.yml", "revision: 242\n"); head = s.commit("moves the revision")
        r, calls, _ = s.gate([s.FAILED(1)], step="Generate cache and gameval sources", env={"BASE": base, "HEAD": head})
        s.assertEqual(r.returncode, 1); s.assertIn("CI failure/completed at 'Generate cache and gameval sources'", r.stdout)
        s.assertFalse([c for c in calls if c.startswith("run rerun")])

    def test_the_carry_asks_the_same_classifier_of_a_failed_upstream_step(s):  # PR 448's freshCache failed upstream; hd's carry judged every failure the head's
        base = git(s.repo, "rev-parse", "HEAD"); s.write("game.example.yml", "revision: 242\n"); head = s.commit("moves the revision")
        root = tempfile.mkdtemp(); change(root, "s1")
        step = lambda st: subprocess.run(["bash", str(HERE.parent / "track.sh"), "ci-step", "s1", st], capture_output=True, text=True,
                                         env={**os.environ, **s.env, "HD_ROOT": root, "BASE": base, "HEAD": head}).returncode
        s.assertEqual([step(x) for x in ("Checkout repository", "Compile and run tests", "Generate cache and gameval sources")], [0, 1, 1])
        shutil.rmtree(root)

    def test_a_run_stopped_in_the_game_data_step_waits_on_the_asset_then_re_runs(s):  # 10 gates re-uploaded the asset at once: goblin's CI 41371460666 found none
        r, calls, _ = s.gate([s.FAILED(1, "cancelled"), s.FAILED(1, "cancelled"), s.RUNS("success")], step="Game data of the gate (tools/gate/gate.sh gate-ci)")
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr); s.assertEqual(len([c for c in calls if c.startswith("run rerun 7")]), 1)

    def test_a_third_attempt_failed_outside_the_head_holds_with_no_result(s):
        r, calls, _ = s.gate([s.FAILED(3)], step="Set up Gradle")
        s.assertEqual(r.returncode, 75, r.stdout + r.stderr); s.assertIn("no result", r.stdout)

    CI = ("jobs:\n  b:\n    timeout-minutes: 30\n    steps:\n      - name: Set up Gradle\n        uses: gradle/actions/setup-gradle@v6\n\n      - name: Cache game data\n        id: gamecache\n        uses: actions/cache@v6\n\n"
          "      - name: Generate cache and gameval sources\n        if: steps.gamecache.outputs.cache-hit != 'true'\n        run: ./gradlew :or-cache:freshCache :or-cache:mergePluginGamevals\n\n"
          "      - name: Rebuild sources from cached game data\n        if: steps.gamecache.outputs.cache-hit == 'true'\n        run: ./gradlew :or-cache:buildCache\n")

    def test_ci_reads_the_game_data_from_the_fork_release_seeded_once_from_the_image(s):  # openrs2 answered HTTP 500 on :or-cache:freshCache: a head's FAIL
        s.write(".github/workflows/ci.yml", s.CI); s.write(".github/workflows/format.yml", s.WF); s.write("game.example.yml", "revision: 241\n"); t = s.commit("ci")
        k = git(s.repo, "rev-parse", f"{t}:game.example.yml")[:12]
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, s.GREEN); root = tempfile.mkdtemp(); change(root, "s1")
        (bin / "docker").write_text('#!/bin/sh\necho "$*" >> "$(dirname "$0")/docker.calls"; [ "$1" = run ] && echo tarball; exit 0\n'); (bin / "docker").chmod(0o755)
        gate = lambda: subprocess.run(["bash", str(HERE.parent / "track.sh"), "gate-ci"], capture_output=True, text=True,
                                      env={**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "T": "tk", "BASE": t, "HEAD": t, "PATH": f"{bin}:{os.environ['PATH']}"})
        r = gate(); s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        calls = (bin / "calls").read_text()
        s.assertIn(f"release upload game-data {root}/state/s1/game-data-{k}.tar.gz", calls); s.assertIn("run --rm --entrypoint tar or:tk", (bin / "docker.calls").read_text())
        y = git(fork, "show", "gate/s1:.github/workflows/ci.yml")
        s.assertLess(y.index(f"-p game-data-{k}.tar.gz"), y.index("Generate cache and gameval sources"))
        s.assertIn("cache-hit != 'true' && steps.gamedata.outcome != 'success'\n        run: ./gradlew :or-cache:freshCache", y)   # openrs2 only when neither holds it
        s.assertIn("cache-hit == 'true' || steps.gamedata.outcome == 'success'", y)
        s.assertNotIn("continue-on-error", y)                                        # no asset fails the runner's step: openrs2 is never downloaded
        s.assertNotIn("--clobber", calls)                                            # concurrent gates: the first upload stands, never replaced under a CI reading it
        job, steps = y.split("    steps:\n")
        s.assertNotIn("timeout-minutes", job)                                        # each step timed alone: a slow download times out in its own step
        s.assertEqual(steps.count("        timeout-minutes: 30\n"), steps.count("      - name: "))
        (bin / "assets").write_text(f"game-data-{k}.tar.gz\n"); (bin / "calls").unlink(); gate()
        s.assertNotIn("release upload", (bin / "calls").read_text())                 # seeded once per game.example.yml
        for d in (fork, bin, root): shutil.rmtree(d)

    def test_a_head_changing_the_revision_runs_fresh_cache(s):  # its download is the head's: no image holds that revision yet
        s.write(".github/workflows/ci.yml", s.CI); s.write(".github/workflows/format.yml", s.WF); s.write("game.example.yml", "revision: 241\n"); b = s.commit("ci")
        s.write("game.example.yml", "revision: 242\n"); t = s.commit("revision")
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, s.GREEN); root = tempfile.mkdtemp(); change(root, "s1")
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "gate-ci"], capture_output=True, text=True,
                           env={**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "BASE": b, "HEAD": t, "PATH": f"{bin}:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        y = git(fork, "show", "gate/s1:.github/workflows/ci.yml")
        s.assertIn("id: gamecache\n        if: false\n", y)                                # no actions/cache restore
        s.assertNotIn("game-data-", y)                                                  # no release asset
        s.assertIn("cache-hit != 'true'\n        run: ./gradlew :or-cache:freshCache", y)  # so freshCache runs, the step infra() calls the head's
        for d in (fork, bin, root): shutil.rmtree(d)

    def test_a_head_changing_a_pack_packs_on_the_restored_revision(s):  # an openrs2 outage (run 41380358897) failed six correct pack and gameval heads in freshCache
        s.write(".github/workflows/ci.yml", s.CI); s.write(".github/workflows/format.yml", s.WF); s.write("game.example.yml", "revision: 241\n"); b = s.commit("ci")
        s.write("content/x/pack/a.toml", "x\n"); s.write("gamevals.toml", "x\n"); s.write("or-cache/CacheTools.kt", "x\n"); t = s.commit("pack")
        k = git(s.repo, "rev-parse", f"{t}:game.example.yml")[:12]
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, s.GREEN); root = tempfile.mkdtemp(); change(root, "s1")
        env = {**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "BASE": b, "HEAD": t, "PATH": f"{bin}:{os.environ['PATH']}"}
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "gate-ci"], capture_output=True, text=True, env=env)
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        y = git(fork, "show", "gate/s1:.github/workflows/ci.yml")
        s.assertNotIn("if: false", y); s.assertIn(f"game-data-{k}.tar.gz", y)            # the revision restored: openrs2 is never the head's
        step = lambda f: subprocess.run(["bash", str(HERE.parent / "track.sh"), "ci-step", "s1", f], capture_output=True, text=True, env={**env, "PATH": f"{bin}:/usr/bin:/bin"}).returncode
        s.assertEqual(step("Rebuild sources from cached game data"), 1)                  # the packing is the head's
        for d in (fork, bin, root): shutil.rmtree(d)

    def test_a_row_without_a_slug_pushes_gate_of_the_env_slug(s):  # its CI moves the runner's ephemeral ports above 43594 before gradle: run 41312919759's boot bind failed
        for f in ("ci", "format"): s.write(f".github/workflows/{f}.yml", s.WF)
        t = s.commit("ci")
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, s.GREEN)
        root = tempfile.mkdtemp(); change(root, "s1")
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "gate-ci"], capture_output=True, text=True,
                           env={**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "PATH": f"{bin}:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 0, r.stderr)
        g = git(fork, "rev-parse", "refs/heads/gate/s1"); s.assertEqual(git(fork, "rev-parse", f"{g}^"), t)
        s.assertEqual(git(fork, "diff", "--name-only", t, g).split(), [".github/workflows/ci.yml", ".github/workflows/format.yml"])
        for f in ("ci", "format"):
            y = git(fork, "show", f"{g}:.github/workflows/{f}.yml")
            s.assertLess(y.index('sudo sysctl -w net.ipv4.ip_local_port_range="49152 65535"'), y.index("./gradlew test"), f)
        s.assertTrue((Path(root) / "state/s1").is_dir())
        for d in (fork, bin, root): shutil.rmtree(d)

    def test_with_central_ci_runs_a_child_of_t_that_builds_that_central_in(s):  # server-token-auth's CI resolved Central 2.0.3 from the network: unpublished
        for f in ("ci", "format"): s.write(f".github/workflows/{f}.yml", s.WF)
        t = s.commit("ci")
        central = tempfile.mkdtemp(); git(central, "init", "-q"); (Path(central) / "settings.gradle.kts").write_text("// central\n")
        git(central, "add", "."); git(central, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "c"); c = git(central, "rev-parse", "HEAD")
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, s.GREEN)
        root = tempfile.mkdtemp(); change(root, "s1")
        r = subprocess.run(["bash", str(HERE.parent / "track.sh"), "gate-ci"], capture_output=True, text=True,
                           env={**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "CENTRAL": f"{central}:{c}", "PATH": f"{bin}:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 0, r.stderr)
        g = git(fork, "rev-parse", "refs/heads/gate/s1")
        s.assertNotEqual(g, t); s.assertEqual(git(fork, "rev-parse", f"{g}^"), t)  # the change's head and T unchanged
        s.assertEqual(git(fork, "rev-parse", f"{g}:.central"), git(central, "rev-parse", f"{c}^{{tree}}"))
        s.assertEqual(git(fork, "show", f"{g}:.central.init.gradle"), (HERE.parent / "build/central.init.gradle").read_text().strip())
        for f in ("ci", "format"):
            y = git(fork, "show", f"{g}:.github/workflows/{f}.yml")
            s.assertLess(y.index("setup-gradle@v6"), y.index('mv .central "$RUNNER_TEMP/central"'), f); s.assertLess(y.index("init.d/central.gradle"), y.index("./gradlew test"), f)
            s.assertIn('echo "CDIR=$RUNNER_TEMP/central" >> "$GITHUB_ENV"', y)
        s.assertEqual(git(fork, "diff", "--name-only", t, g).split(), sorted([".central.init.gradle", ".central/settings.gradle.kts", ".github/workflows/ci.yml", ".github/workflows/format.yml"]))
        for d in (fork, bin, root, central): shutil.rmtree(d)

    def test_two_gates_at_once_each_use_their_own_index(s):  # five gate-ci rows failed on 'gate-index.lock': File exists, one index per repo
        for f in ("ci", "format"): s.write(f".github/workflows/{f}.yml", s.WF)
        t = s.commit("ci")
        fork = tempfile.mkdtemp(); git(fork, "init", "-q", "--bare"); git(s.repo, "remote", "add", "fork", fork)
        bin = Path(tempfile.mkdtemp()); s.fake_gh(bin, s.GREEN)
        root = tempfile.mkdtemp(); change(root, "s1"); change(root, "s2")
        gd = Path(s.repo) / ".git"; (gd / "gate-index.lock").write_text("")  # what the old shared index left for a concurrent gate
        tmp = tempfile.mkdtemp()   # a gate leaves no temp dir behind, killed or not: its index is the change's own state file
        ps = [subprocess.Popen(["bash", str(HERE.parent / "track.sh"), "gate-ci", k], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               env={**os.environ, **s.env, "HD_ROOT": root, "TCOMMIT": t, "PATH": f"{bin}:{os.environ['PATH']}", "TMPDIR": tmp}) for k in ("s1", "s2")]
        for p in ps: s.assertEqual(p.wait(), 0, p.stderr.read())
        s.assertEqual(os.listdir(tmp), []); s.assertTrue((Path(root) / "state/s1/gate-ci.index").exists())
        for k in ("s1", "s2"): s.assertEqual(git(fork, "rev-parse", f"refs/heads/gate/{k}^"), t)
        s.assertEqual(sorted(x.name for x in gd.iterdir() if x.name.startswith("gate-index")), ["gate-index.lock"])
        for d in (fork, bin, root): shutil.rmtree(d)



class JavConfig(unittest.TestCase):
    def test_template_names_local_hosts_only(s):
        import javcheck
        t = (HERE / "jav_config.ws.template").read_text(encoding="utf-8").replace("{{HTTP_BASE}}", "http://127.0.0.1:8080").replace("{{WORLD_HOST}}", "10.0.2.2")
        s.assertEqual(javcheck.foreign(t), [])
        s.assertEqual(javcheck.foreign('x=["https://legal.jagex.com/docs"T] param=19=1-a.apps.googleusercontent.com'), ["1-a.apps.googleusercontent.com", "legal.jagex.com"])


if __name__ == "__main__":
    unittest.main()


class RealmLikeLive(unittest.TestCase):  # Central seeds a dev realm: every login an administrator, unlike live
    t = SRC
    up = t.split("\nup() {")[1].split("\n}")[0]
    fn = next(l for l in t.splitlines() if l.startswith("account()"))

    def test_up_turns_the_dev_realm_off_and_restarts_before_any_login(s):
        line = next(l for l in s.up.splitlines() if "dev_mode = 0" in l)
        s.assertLess(s.up.index(line), s.up.index("desktop_start"))
        call = lambda out: subprocess.run(["bash", "-c", f'set -euo pipefail\nsql() {{ echo "{out}"; }}\ndocker() {{ echo "docker $*" >&2; }}\nready() {{ echo "ready $*" >&2; }}\nslug=s\n{line}'], capture_output=True, text=True)
        r = call("1"); s.assertEqual(r.returncode, 0, r.stderr); s.assertIn("docker restart server-s", r.stderr); s.assertRegex(r.stderr, r"ready server-s \d")
        r = call(""); s.assertEqual(r.returncode, 0, r.stderr); s.assertEqual(r.stderr, "")   # already live (RESUME): no restart

    def test_up_adds_world_256_as_a_copy_of_255(s):  # a world switch's target on the same host and ports; a resumed database keeps its row
        line = next(l for l in s.up.splitlines() if "dev_mode = 0" in l)
        s.assertRegex(line, r"insert into worlds \(world_id, flags, host, .*\) select 256, flags, host, .* from worlds where world_id = 255 on conflict \(world_id\) do nothing returning 1")

    def test_up_sets_the_realm_xp_rates_to_live(s):  # the dev realm seeds player xp at 15000 hundredths: a reward shows 150x
        line = next(l for l in s.up.splitlines() if "dev_mode = 0" in l)
        for col in ("player_xp_rate_in_hundreds", "global_xp_rate_in_hundreds"):
            s.assertIn(f"{col} = 100", line); s.assertIn(f"{col} <> 100", line)   # set, and a 150x realm alone still restarts

    def test_every_account_is_a_player_unless_staff_names_its_desktop(s):  # STAFF=1's account once read rights '' and every cheat was refused
        line = "\n".join(l for l in s.up.splitlines() if l.startswith("  rights=") or "update accounts set rights" in l)
        s.assertLess(s.up.index("  offline"), s.up.index(line))
        login = s.up.rindex('login "$(cut -d: -f2 <<< "${desktops[$i]}")"')
        s.assertLess(s.up.index(line), login); s.assertLess(login, s.up.index("rights <> $rights"))   # read back once the logins ran
        q = lambda staff: subprocess.run(["bash", "-c", f'set -euo pipefail\nsql() {{ echo "$1"; }}\n{s.fn}\nslug=s\n{line.replace(">/dev/null", "")}'],
                                         capture_output=True, text=True, env={**os.environ, **({"STAFF": staff} if staff else {})}).stdout
        name = lambda i: subprocess.run(["bash", "-c", f'{s.fn}\nslug=s; account {i}'], capture_output=True, text=True).stdout.strip()
        staff = next(l for l in s.up.splitlines() if l.startswith("  staff="))
        q = lambda st: subprocess.run(["bash", "-c", f'set -euo pipefail\nsql() {{ echo "$1"; }}\n{s.fn}\nslug=s\n{staff}\n{line.replace(">/dev/null", "")}'],
                                      capture_output=True, text=True, env={**os.environ, **({"STAFF": st} if st else {})}).stdout
        s.assertIn("lower(account_name) in ('') then", q(None))   # no administrator
        s.assertIn(f"lower(account_name) in ('{name(2)}', '') then 'ADMINISTRATOR' else ''", q("2"))
        s.assertIn(f"lower(account_name) in ('{name(1)}', '{name(2)}', '') then 'ADMINISTRATOR'", q("1,2"))   # sweep 44 P2-a: one up, every desktop needing cheats
        s.assertIn(f"like '{name('')}%'", q("2"))


class KeyOnCachedBuild(unittest.TestCase):  # a cached or:<T> left state/<slug>/key empty: docker made the mount sources directories and the server exited at boot
    t = SRC
    fn = "keys() {" + t.split("\nkeys() {")[1].split("\n}")[0] + "\n}"
    mod = next(l for l in t.splitlines() if l.startswith("modulus_of()"))

    def test_up_makes_a_key_pair_before_the_server_runs_and_keeps_an_existing_one(s):
        up = s.t.split("\nup() {")[1].split("\n}")[0]
        s.assertLess(up.index("  keys "), up.index('docker run -d --name "server-$slug"'))
        s.assertNotIn("state/key", s.t.split("\nbuild() {")[1].split("\n}")[0])   # no key comes from a build: one source for every up
        st = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, st)
        (st / "key/game.key").mkdir(parents=True); (st / "key/client.key").mkdir()   # what docker leaves after an up with no key
        run = lambda: subprocess.run(["bash", "-c", f"set -euo pipefail\nstate={st}\n{s.mod}\n{s.fn}\nkeys"], capture_output=True, text=True)
        r = run(); s.assertEqual(r.returncode, 0, r.stderr)
        game, client = (st / "key/game.key").read_text(), (st / "key/client.key").read_text()
        s.assertTrue(game.startswith("-----BEGIN PRIVATE KEY-----"))   # PKCS#8: the server's RsaProvider reads it
        mod = subprocess.run(["openssl", "rsa", "-in", str(st / "key/game.key"), "-noout", "-modulus"], capture_output=True, text=True).stdout.split("=")[1].strip().lower()
        s.assertEqual(client, f"Exponent: 10001\nModulus: {mod}")
        s.assertEqual(len(mod), 256)
        r = run(); s.assertEqual(r.returncode, 0, r.stderr); s.assertEqual((st / "key/game.key").read_text(), game)   # an existing key is kept


class FakeCentral:  # Central's sign-in as sign_in calls it: /oauth2/auth (a code for the posted account, else the dev account), token, sessions, accounts
    def __init__(s, test, d, dev):
        import http.server, ssl
        subprocess.run([sys.executable, str(HERE / "issuer.py"), "key", str(d)], check=True, capture_output=True)
        s.sessions, s.posted = {}, []; codes = {}; fake = s
        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def send(self, status, body=None, location=None):
                b = json.dumps(body).encode() if body is not None else b""
                self.send_response(status); self.send_header("Content-Length", str(len(b)))
                if location: self.send_header("Location", location)
                self.end_headers(); self.wfile.write(b)
            def answer(self):
                u = urllib.parse.urlsplit(self.path); q = dict(urllib.parse.parse_qsl(u.query))
                raw = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
                if u.path == "/oauth2/auth":
                    f = dict(urllib.parse.parse_qsl(raw)) if self.command == "POST" else {}
                    if f: fake.posted.append(f)
                    code = os.urandom(8).hex(); codes[code] = f.get("username", dev); q.update(f)
                    return self.send(302, location=f"{q['redirect_uri']}?code={code}&state={q['state']}")
                if u.path == "/oauth2/token":
                    return self.send(200, {"id_token": "idt-" + codes.pop(dict(urllib.parse.parse_qsl(raw))["code"])})
                if u.path == "/game-session/v1/sessions":
                    sid = os.urandom(8).hex(); fake.sessions[sid] = json.loads(raw)["idToken"][4:]; return self.send(200, {"sessionId": sid})
                if u.path == "/game-session/v1/accounts":
                    acc = fake.sessions[self.headers["Authorization"][7:]]; return self.send(200, [{"accountId": len(acc), "displayName": acc}])
                self.send(404)
            do_GET = do_POST = answer
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); tls.load_cert_chain(d / "tls.pem", d / "tls.key")
        s.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); s.srv.socket = tls.wrap_socket(s.srv.socket, server_side=True)
        threading.Thread(target=s.srv.serve_forever, daemon=True).start(); test.addCleanup(s.srv.shutdown)


class TokenLogin(unittest.TestCase):  # a desktop's token login (auth type 7) through embedded Central's sign-in: server-token-auth verifies the token Central signs
    def test_key_makes_the_secret_game_yml_and_central_share_once(s):
        d = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, d)
        run = lambda: subprocess.run([sys.executable, str(HERE / "issuer.py"), "key", str(d)], capture_output=True, text=True, check=True).stdout
        block = run(); import base64
        s.assertEqual(base64.b64decode(block.split('secret: "')[1].split('"')[0]), base64.b64decode((d / "secret").read_text())); s.assertEqual(len(base64.b64decode((d / "secret").read_text())), 32)
        s.assertTrue((d / "tls.pem").exists() and (d / "tls.key").exists()); s.assertEqual(run(), block)   # made once
        nb = subprocess.run(["openssl", "x509", "-noout", "-checkend", "0", "-startdate", "-in", str(d / "tls.pem")], capture_output=True, text=True, check=True).stdout
        import email.utils, datetime; start = email.utils.parsedate_to_datetime(nb.split("notBefore=")[1].split("\n")[0].replace(" GMT", " +0000"))
        s.assertLess(start, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12))   # fault 332: a WSL clock stepped back must not make the cert "not yet valid"
        s.assertNotIn("def serve", (HERE / "issuer.py").read_text())   # h-ref-sign-in-no-issuer: Central serves the sign-in, no issuer

    def test_up_signs_each_desktop_in_through_its_own_central_and_runs_no_issuer(s):  # h-ref-sign-in-no-issuer: token-<slug> went
        sh = SRC
        up = sh.split("\nup() {")[1].split("\n}")[0]; down = sh.split("\ndown() {")[1].split("\n}")[0]
        s.assertNotIn("token-$slug", up); s.assertNotIn("${SIGN_IN", sh); s.assertNotIn("$sic", sh); s.assertNotIn("{sic", sh); s.assertNotIn("issuer.py serve", sh); s.assertNotIn("issuer.py\" mint", sh)
        s.assertIn('cs="server-$slug"\n', up); s.assertIn('containers="$cs"', up); s.assertIn('docker rm -f $cs', down)   # the record names it; down removes what the record names
        s.assertIn('issuer.py" key "$state/token" >> "$state/game.yml"', up)
        for e in ('-p "$http:8443" -p 9090', "OPENRUNE_SIGN_IN_TOKEN_SECRET", "OPENRUNE_HTTP_TLS_PORT=8443", "OPENRUNE_HTTP_TLS_KEYSTORE=", "OPENRUNE_HTTP_TLS_KEYSTORE_PASSWORD=", "OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file://"):
            s.assertIn(e, up)
        s.assertIn('"-Dosrstest.token=${tok:-false}"', sh); s.assertIn("JX_SESSION_ID:JX_CHARACTER_ID:JX_DISPLAY_NAME", sh); s.assertIn("tok=true;", up)
        loop = up.split("for i in $(seq 1 \"$n\"); do")[1]
        s.assertLess(loop.index('who=$(account "$i"); sign_in "$who"'), loop.index("desktop_start"))   # each desktop its own account's session
        s.assertLess(up.rindex("ready \"server-$slug\""), up.index("sign_in \"$who\""))   # after the realm's restart: Central keeps sessions in memory
        s.assertIn("JX_SESSION_ID=${sid:-harness} JX_CHARACTER_ID=${cid:-1}", sh); s.assertIn('JX_DISPLAY_NAME="${who:-$(account 1)}"', sh)
        body = sh.split("\nlogin() {")[1].split("\nunkeep() {")[0]   # login and keep
        s.assertNotIn('"$2" "$2"', body); s.assertEqual(body.count('desktop_login.py" "$1" token'), 1); s.assertIn('keep "server-$slug" token', body)   # no typed form

    def test_sign_in_opens_a_session_for_the_named_account_else_the_dev_account(s):  # h-central-up-sign-in, h-desktops-token-login
        d = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, d); c = FakeCentral(s, d, "hdev")
        fn = "sign_in() {" + SRC.split("\nsign_in() {")[1].split("\n}")[0] + "\n}"
        sign = lambda who: subprocess.run(["bash", "-c", f"set -euo pipefail\n{fn}\nsign_in {who}; echo $sid $cid"], capture_output=True, text=True, env={**os.environ, "http": str(c.srv.server_port), "ca": str(d / "tls.pem")})
        out = sign(""); s.assertEqual(out.returncode, 0, out.stderr); sid, cid = out.stdout.split()
        s.assertEqual((c.sessions[sid], cid), ("hdev", "4")); s.assertEqual(c.posted, [])   # no account named: the dev account, no password sent
        out = sign("hcd345"); s.assertEqual(out.returncode, 0, out.stderr); sid, cid = out.stdout.split()
        s.assertEqual(c.posted, [{"username": "hcd345", "password": "hcd345", "redirect_uri": "http://127.0.0.1/cb", "state": "up", "client_id": "harness"}]); s.assertEqual((c.sessions[sid], cid), ("hcd345", "6"))

    def test_restart_is_down_and_a_resumed_up_of_the_same_stack(s):  # Central's sessions live in memory: a restarted server knows no desktop's session
        st = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, st)
        (st / "up.json").write_text(json.dumps({"desktops": "desktop1:7780 desktop2:7781 desktop3:7782", "T": "abc_c123", "staff": f"hx3 hx1"}))
        (st / "game.yml").write_text('quest-requirements:\n  mode: "assume-completed"\n')
        fn = "restart() {" + SRC.split("\nrestart() {")[1].split("\n}")[0] + "\n}"
        out = subprocess.run(["bash", "-c", f"set -euo pipefail\nstate={st}\naccount() {{ echo hx$1; }}\nup() {{ echo \"$arg|$T|$STAFF|$QUEST_MODE|$RESUME\"; }}\n{fn}\nrestart"], capture_output=True, text=True)
        s.assertEqual(out.stdout.splitlines()[0], "3|abc_c123|1,3|assume-completed|1", out.stderr)
        (st / "up.json").write_text(json.dumps({"desktops": "desktop1:7780", "staff": ""}))
        out = subprocess.run(["bash", "-c", f"set -euo pipefail\nstate={st}; T=\naccount() {{ echo hx$1; }}\nup() {{ echo \"$arg|${{T-unset}}|$STAFF\"; }}\n{fn}\nrestart"], capture_output=True, text=True)
        s.assertEqual(out.stdout.splitlines()[0], "1|unset|", out.stderr)   # no T recorded: the build's

    def test_central_jav_serves_the_filled_template_from_the_servers_own_central(s):  # central-embedded-jav-config: no up could point a desktop at embedded Central
        import javcheck
        up = SRC.split("\nup() {")[1].split("\n}")[0]
        fill = JAV + "\ncentral_jav"; s.assertIn("\n  central_jav   #", up)
        out = subprocess.run(["bash", "-c", f"http=21813; tpl={HERE}/jav_config.ws.template; state=$(mktemp -d)\n{fill}\ncat $state/jav_config.ws; rm -r $state"], capture_output=True, text=True, check=True).stdout
        s.assertNotIn("{{", out); s.assertEqual(javcheck.foreign(out), [])
        for line in ("codebase=http://127.0.0.1/", "param=17=https://127.0.0.1:21813/worldslist.ws", "param=11=http://127.0.0.1:21813/", "param=12=255", "param=3=true", "param=5=1", "param=25=241"):
            s.assertIn(line + "\n", out)
        s.assertIn('-v "$state/jav_config.ws:/app/jav_config.ws:ro" -e OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file:///app/jav_config.ws)', up)
        s.assertIn('"${sopt[@]}" "or:$T"', up); s.assertNotIn("http-$slug", up)   # no sidecar: every up's own Central serves it
        s.assertIn('javcheck.py" "http://127.0.0.1:$(docker port "server-$slug" 9090', up); s.assertIn("ep=https://127.0.0.1:$http", SRC)   # Central's plain http checked; the desktop's endpoint its https
        s.assertIn('\n  file_central || T=$(central_staged)', up)
        central = (HERE.parent.parent / "central/track.sh").read_text()
        s.assertIn('export CENTRAL="$repo:$h"', central)   # the fork's up merges a head without file:// support with Central's staging

    def test_an_up_whose_central_reads_no_file_jav_config_rebuilds_with_centrals_staging(s):  # h-ref-up-central-jav-config: the published Central fetches jav_config over http alone
        d = Path(tempfile.mkdtemp()); c = d / "central"; c.mkdir(); src = c / "central-app/src/main"; src.mkdir(parents=True)
        g = lambda *a: git(str(c), "-c", "user.name=t", "-c", "user.email=t@t", *a)
        g("init", "-q", "-b", "main"); (src / "A.kt").write_text("http\n"); g("add", "-A"); g("commit", "-qm", "main")
        g("checkout", "-qb", "head"); (src / "B.kt").write_text("x\n"); g("add", "-A"); g("commit", "-qm", "head")   # a Central change without file:// support
        g("checkout", "-qb", "staging", "main"); (src / "A.kt").write_text('if (scheme == "file")\n'); g("add", "-A"); g("commit", "-qm", "file"); file_only = g("rev-parse", "HEAD^{tree}")[:12]
        (src / "S.kt").write_text('post("/game-session/v1/sessions")\n'); g("add", "-A"); g("commit", "-qm", "sign-in")
        (d / "build").mkdir(); (d / "build/build.sh").write_text(f'echo "$T|$CENTRAL|$HD_KEY" > {d}/args; echo \'{{"T": "built"}}\' > {d}/build.json\n')
        (d / "build/build.sh").chmod(0o755)
        fns = SRC[SRC.index("file_central() {"):SRC.index("central_jav() {")]
        run = lambda T, central="": subprocess.run(["bash", "-c", f"set -euo pipefail\ncrepo={c}; self={d}; state={d}; slug=x; T={T}; CENTRAL={central}\n{fns}\nif file_central; then echo file; else central_staged; fi"], capture_output=True, text=True)
        tree = lambda r: g("rev-parse", r + "^{tree}")[:12]
        s.assertEqual(run(f"abc_c{tree('staging')}").stdout, "file\n")                     # built with a file:// Central: as it is
        r = run("abc"); s.assertEqual(r.stdout, "built\n", r.stderr)                          # the published Central: rebuilt with staging's
        r = run(f"abc_c{file_only}"); s.assertEqual(r.stdout, "built\n", r.stderr)                # a file:// Central without the sign-in (h-ref-sign-in-no-issuer): rebuilt too
        s.assertEqual((d / "args").read_text(), f"|{c}:{g('rev-parse', 'staging')}|\n")      # T unset (the build keys its own), no job reported
        r = run(f"abc_c{tree('head')}", f"{c}:{g('rev-parse', 'head')}"); s.assertEqual(r.stdout, "built\n", r.stderr)
        m = (d / "args").read_text().split("|")[1].split(":")[1]
        s.assertEqual(g("rev-parse", m + "^@").split(), [g("rev-parse", "head"), g("rev-parse", "staging")])   # the head merged with staging
        s.assertEqual(g("show", f"{m}:central-app/src/main/B.kt"), "x"); s.assertTrue(run(f"abc_c{tree(m)}").stdout == "file\n")

    def test_a_desktop_home_holds_no_preferences_the_launcher_does_not_write(s):  # fault 179: a static preferences.dat (no Jagex Account prompt day) stopped the launcher's dated one and Existing User landed on the prompt
        s.assertNotIn("preferences.dat", SRC.split("\ndesktop_start() {")[1].split("\n}")[0])

    def test_a_failed_deploy_records_its_failure_and_checks_the_templates_before_the_live_stack(s):  # h-mobile-login-page-9: a javcheck `|| return 6` raised no ERR, so the pass started the deploy 9 times, each recreating the live stack under a mobile's start (gameState 1000)
        ship = SRC.split("\ndeploy() {")[1].split("\n}")[0]
        s.assertLess(ship.index('javcheck.py" "$state/jav_config.ws" || return 6'), ship.index("docker compose"))
        trap = next(l for l in ship.splitlines() if "' EXIT" in l)
        d = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, d); (d / "log").write_text("non-local hosts: auth.jagex.com\n")
        r = subprocess.run(["bash", "-c", f'set -euo pipefail; hd="echo hd"; arg=x; HD_KEY=k; HD_LOG={d}/log\ndeploy() {{\n{trap}\nfalse || return 6; }}\ndeploy'], capture_output=True, text=True)
        s.assertEqual(r.returncode, 6); s.assertIn("hd job deploy k fail return 6 (exit 6): non-local hosts: auth.jagex.com", r.stdout)
        (d / "t").write_text("codebase={{HTTP_BASE}}/\nparam=13=.{{WORLD_HOST}}\n")
        s.assertEqual(subprocess.run(["python3", str(HERE / "javcheck.py"), str(d / "t")], capture_output=True).returncode, 0)
        (d / "t").write_text("param=11=https://auth.jagex.com/\n")
        s.assertEqual(subprocess.run(["python3", str(HERE / "javcheck.py"), str(d / "t")], capture_output=True).returncode, 1)

    def test_live_runs_central_alone_for_every_client(s):  # h-ref-apk-jav-config-central: the APK's sidecar (osrs-openrune-http) went; the APK reads Central's jav_config
        compose = (HERE / "docker-compose.yml").read_text(); ship = SRC.split("\ndeploy() {")[1].split("\n}")[0]
        s.assertEqual(re.findall(r"^  (\w+):$", compose, re.M), ["openrune"])   # one service: no issuer, http-desktop nor http sidecar
        for gone in ("SIDECAR_DATA", "ISSUER_DIR", "OPENRUNE_HTTP_PORT", "osrs-openrune-http", "8083"): s.assertNotIn(gone, compose + (HERE / "switch.env").read_text())
        s.assertNotIn("SIDECAR_DATA", SRC); s.assertNotIn("osrs-openrune-http", SRC); s.assertNotIn("WORLD_HOST}}:", SRC)   # no APK template of its own
        s.assertIn('python3 "$self/server/issuer.py" key "$ISSUER_DIR"; } > "$state/game.yml"', ship); s.assertIn("COPY --chown=1000:1000 game.yml /app/game.yml", ship)
        s.assertIn('curl -fsS -o /dev/null "http://127.0.0.1:${OPENRUNE_CENTRAL_HTTP_PORT:-8084}/.well-known/openid-configuration" || return 6', ship)

    def test_live_serves_centrals_sign_in_to_desktops_over_https(s):  # h-live-central-sign-in: the live stack had no sign-in a desktop could use
        import javcheck
        ship = SRC.split("\ndeploy() {")[1].split("\n}")[0]; compose = (HERE / "docker-compose.yml").read_text()
        s.assertIn('"${OPENRUNE_CENTRAL_HTTP_PORT:-8084}:9090", "${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}:8443"', compose)
        s.assertIn("http=${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}; tpl=$self/server/jav_config.ws.template; central_jav", ship)
        s.assertIn('-in "$ISSUER_DIR/tls.pem" -inkey "$ISSUER_DIR/tls.key" -passout pass:changeit -out "$state/central-tls.p12"', ship)
        s.assertIn("COPY --chown=1000:1000 central-tls.p12 jav_config.ws /app/.data/", ship)
        for e in ('OPENRUNE_SIGN_IN_TOKEN_SECRET="$(cat "$ISSUER_DIR/secret")"', "OPENRUNE_HTTP_TLS_PORT=8443",
                  "OPENRUNE_HTTP_TLS_KEYSTORE=/app/.data/central-tls.p12", "OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file:///app/.data/jav_config.ws"):
            s.assertIn(e, ship)
        s.assertIn('javcheck.py" "http://127.0.0.1:${OPENRUNE_CENTRAL_HTTP_PORT:-8084}/jav_config.ws" || return 6', ship)
        s.assertNotIn("OPENRUNE_SIGN_IN_DEV_ACCOUNT", ship)   # h-mobile-login-page-9: one dev account for every mobile refused parallel mobiles Duplicate; each signs in at Central's form
        s.assertIn('curl -fsS -o /dev/null --cacert "$ISSUER_DIR/tls.pem" "https://127.0.0.1:${OPENRUNE_CENTRAL_HTTPS_PORT:-8443}/.well-known/openid-configuration" || return 6', ship)
        s.assertLess(ship.index("central_jav"), ship.index("docker build"))
        out = subprocess.run(["bash", "-c", f"http=8443 tpl={HERE}/jav_config.ws.template; state=$(mktemp -d)\n{JAV}\ncentral_jav; cat $state/jav_config.ws; rm -r $state"], capture_output=True, text=True, check=True).stdout
        s.assertNotIn("{{", out); s.assertEqual(javcheck.foreign(out), [])
        for line in ("param=11=http://127.0.0.1:8443/", "param=20=http://127.0.0.1:8443/", "param=22=http://127.0.0.1:8443/", "param=28=http://127.0.0.1:8443/", "param=17=https://127.0.0.1:8443/worldslist.ws"):   # 11 and 22 the desktop casts to https; the APK takes them as written
            s.assertIn(line + "\n", out)

    def test_the_launcher_refuses_a_jagex_access_or_refresh_token_in_every_mode(s):
        src = (HERE / "OsrsTestLauncher.java").read_text()
        s.assertIn('"JX_ACCESS_TOKEN", "JX_REFRESH_TOKEN"', src)
        s.assertIn('boolean session = v.equals("JX_SESSION_ID") || v.equals("JX_CHARACTER_ID") || v.equals("JX_DISPLAY_NAME");', src)
        s.assertIn("token && session ? System.getenv(v) == null : System.getenv(v) != null", src)
        s.assertIn('-cp "$t\\\\rsprox\\\\$l;', SRC)   # up runs this tree's launcher, compiled from this source


class StackRecord(unittest.TestCase):  # each step re-derived the stack: down looped in offline() once the container was gone, hd's repair ran a script with no down
    t = SRC
    up = t.split("\nup() {")[1].split("\n}")[0]
    fn = lambda s, name: f"{name}() {{" + s.t.split(f"\n{name}() {{")[1].split("\n}")[0] + "\n}"
    line = lambda s, pre: next(l for l in s.t.splitlines() if l.startswith(pre))

    def test_up_writes_the_record_before_its_first_container(s):
        rec = s.up.index("  stack started=")
        for c in ('docker run -d --name "server-$slug"', "desktop_start"):
            s.assertLess(rec, s.up.index(c))
        for f in ('script="$self/track.sh"', 'containers="$cs"', 'modulus="$modulus"', 'staff="$staff"', 'token="$devtoken"'):
            s.assertIn(f, s.up[rec:s.up.index("\n", s.up.index("\n", rec) + 1)])
        st = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, st)
        run = lambda *a: subprocess.run(["bash", "-c", f"set -euo pipefail\nhd=:; slug=x\nstate={st}\n{s.line('atomic()')}\n{s.fn('stack')}\nstack \"$@\"", "-", *a], capture_output=True, text=True)
        s.assertEqual(run("game:=20001", "desktops=", "script=/x/track.sh").returncode, 0)
        s.assertEqual(run("desktops=desktop1:7780").returncode, 0)
        s.assertEqual(json.loads((st / "up.json").read_text()), {"game": 20001, "desktops": "desktop1:7780", "script": "/x/track.sh"})   # each later step adds, none drops a field

    def down(s, record, inspect):  # down against a fake docker; inspect: what each `docker inspect` answers in turn (the last repeats)
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "bin").mkdir(); (root / "st").mkdir()
        (root / "inspect").write_text("\n".join(inspect) + "\n")
        (root / "bin/docker").write_text(f"""#!/bin/bash
echo "$*" >> {root}/calls
case $1 in inspect) a=$(head -1 {root}/inspect); [ "$(wc -l < {root}/inspect)" -gt 1 ] && sed -i 1d {root}/inspect; echo "$a" ;;
  logs) echo "Server ready in 1s" ;; run) exit 1 ;; ps) cat {root}/names 2>/dev/null ;; rm) : > {root}/names ;; esac
""")
        (root / "bin/docker").chmod(0o755)
        if record: (root / "st/up.json").write_text(json.dumps(record))
        script = "\n".join(["set -euo pipefail", f"hd=:; slug=x; state={root}/st", s.line("account()"), s.line("mine="), s.fn("sql"), s.line("offline()"), s.fn("down"),
                            "unkeep() { :; }; desktops_remove() { :; }", "down"])
        r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60, env={**os.environ, "PATH": f"{root}/bin:{os.environ['PATH']}"})
        return r, root

    def test_down_ends_once_the_server_is_gone_and_removes_the_records_containers(s):  # sweep 48 P1-b: the container gone, sql answered nothing and offline looped forever
        r, root = s.down({"containers": "server-x http-x token-x"}, ["true", "true", "false"])   # running and ready, then gone mid-wait
        s.assertEqual(r.returncode, 0, r.stderr); s.assertEqual(r.stdout.strip(), "down")
        s.assertIn("rm -f server-x http-x token-x", (root / "calls").read_text())
        s.assertFalse((root / "st/up.json").exists())

    def test_a_container_left_keeps_the_record_and_fails(s):
        root = None
        r, root = s.down({"containers": "server-x http-x"}, ["false"])
        s.assertEqual(r.returncode, 0, r.stderr)
        (root / "st/up.json").write_text(json.dumps({"containers": "server-x http-x"}))
        (root / "bin/docker").write_text((root / "bin/docker").read_text().replace("rm) : > ", "rm) cat ").replace("ps) cat", "ps) echo http-x; cat"))
        script = "\n".join(["set -euo pipefail", f"hd=:; slug=x; state={root}/st", s.line("account()"), s.line("mine="), s.fn("sql"), s.line("offline()"), s.fn("down"), "unkeep() { :; }; desktops_remove() { :; }", "down"])
        r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60, env={**os.environ, "PATH": f"{root}/bin:{os.environ['PATH']}"})
        s.assertEqual(r.returncode, 1); s.assertIn("down: http-x not removed", r.stderr); s.assertTrue((root / "st/up.json").exists())

    def test_ship_deploys_the_live_pair_and_refuses_another_key_before_boot_and_tag(s):  # every image since 2026-10-31 18:32Z carried a key no APK had: 'Invalid RSA check'
        ship = s.t.split("\ndeploy() {")[1].split("\n}")[0]
        s.assertNotIn("--from=$live_image", ship); s.assertIn("COPY --chown=1000:1000 key/game.key key/client.key /app/.data/", ship)
        s.assertLess(ship.index('image_key "osrs-openrune:$T"'), ship.index('boot-$T'))
        s.assertLess(ship.index('image_key "osrs-openrune:$T"'), ship.index('docker tag'))
        s.assertIn('"modulus":sys.argv[6]', ship)   # the live stack's record names the modulus the APK's up checks
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root); (root / "bin").mkdir()
        keys = {}
        for n in ("pair", "other"):
            subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:1024", "-out", str(root / f"{n}.key")], check=True, capture_output=True)
            keys[n] = subprocess.run(["openssl", "rsa", "-in", str(root / f"{n}.key"), "-noout", "-modulus"], capture_output=True, text=True).stdout.split("=")[1].strip().lower()
            (root / f"{n}.client").write_text(f"Exponent: 10001\nModulus: {keys[n]}")
        (root / "bin/docker").write_text(f"""#!/bin/bash
img=${{5%%:*}}; img=${{5#*:}}; f=${{@: -1}}; case $f in */game.key) cat {root}/$img.key ;; */client.key) cat {root}/$img.client ;; esac
""")
        (root / "bin/docker").chmod(0o755)
        run = lambda img: subprocess.run(["bash", "-c", f"set -euo pipefail\n{s.line('modulus_of()')}\n{s.fn('image_key')}\nmodulus={keys['pair']}\nimage_key x:{img}"],
                                         capture_output=True, text=True, env={**os.environ, "PATH": f"{root}/bin:{os.environ['PATH']}"})
        r = run("pair"); s.assertEqual(r.returncode, 0, r.stderr + r.stdout); s.assertIn(f"key: the live pair's {keys['pair'][:8]}", r.stdout)
        r = run("other"); s.assertEqual(r.returncode, 4)
        s.assertIn(f"carries game.key {keys['other'][:8]} and client.key {keys['other'][:8]}, not the live pair's {keys['pair'][:8]}", r.stdout)
