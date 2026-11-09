"""The client track's check rows against fixture evidence: python3 -m unittest tools/test_track.py"""
import re, os, shutil, subprocess, tempfile, time, unittest
from pathlib import Path
SUITE_TMP = tempfile.TemporaryDirectory(prefix="tools-suite-", ignore_cleanup_errors=True)   # every temp dir of these tests and of each process they
tempfile.tempdir = os.environ["TMPDIR"] = SUITE_TMP.name                          # start (mktemp) is under it, removed at the end, a failed test's too
for k in [k for k in os.environ if k.startswith("HD_")] + ["SLUG", "HEAD", "T", "TCOMMIT", "BASE", "CLONE", "BUILD", "EVIDENCE", "PR", "PUBLIC_BRANCH", "CENTRAL", "FILESTORE"]:
    os.environ.pop(k, None)   # hd's env of the gate that runs these tests is not the tests': its TCOMMIT named the candidate in a fixture repo

TRACK = Path(__file__).resolve().parent / "track.sh"
GATE, BUILD = TRACK.parent / "gate/gate.sh", TRACK.parent / "build/build.sh"   # the code a gate runs, the code a build runs
place = lambda tools: (shutil.copy(TRACK, tools / "track.sh"), shutil.copy(TRACK.parent / "Agent_Lite.ini", tools), shutil.copytree(GATE.parent, tools / "gate"), shutil.copytree(BUILD.parent, tools / "build"))   # the track script with its AVD config, gate and build dirs
MOD = "8555c56c" + "ab" * 124   # the live stack's modulus in these fixtures


def apk(path, modulus=MOD, endpoint=b"http://127.0.0.1:8443/jav_config.ws?m=0&p=jagex.comxxxxxxx"):  # an APK whose game library carries that login modulus and jav_config URL, among the byte tables a real one holds
    import zipfile
    with zipfile.ZipFile(path, "w") as z: z.writestr("lib/arm64-v8a/liblibs.hal.system.osclient.so", b"\x00" + bytes(range(256)).hex().encode()[:256] + b"\x00" + modulus.encode() + b"\x00" + endpoint + b"\x00" + os.urandom(1 << 20))   # bytes after the modulus, as a real one: a reader that stops at the match SIGPIPEs unzip


def live(root, modulus=MOD):  # the live stack's key pair (state/live/key) and its record (state/live/tree.json, the server track's ship)
    d = Path(root) / "state/live"; (d / "key").mkdir(parents=True, exist_ok=True)
    (d / "key/client.key").write_text(f"Exponent: 10001\nModulus: {modulus}"); (d / "tree.json").write_text('{"modulus": "%s"}' % modulus)


GOOD = "".join(f"telemetry: line {i}\n" for i in range(7)) + "patched RSA modulus at file offset 0x1\npatched /jav_config.ws at file offset 0x2\npatched smali/net/openid/appauth/X.smali\n"


class Rows(unittest.TestCase):
    def setUp(s):
        s.ev = Path(tempfile.mkdtemp())
        s.env = {**os.environ, "HD_ROOT": tempfile.mkdtemp(), "EVIDENCE": str(s.ev), "HEAD": "abcdef1234567890", "T": "t"}
        (Path(s.env["HD_ROOT"]) / "harness/changes").mkdir(parents=True); (Path(s.env["HD_ROOT"]) / "harness/changes/x.md").write_text("")
        (Path(s.env["HD_ROOT"]) / "harness/hd.py").write_text("import sys\nif sys.argv[1] == 'candidate': print('t', sys.argv[sys.argv.index('--head') + 1])\n")   # a fake hd: candidate answers the snapshot; job and stack record nothing

    def tearDown(s):
        shutil.rmtree(s.ev, ignore_errors=True)

    def row(s, verb):
        r = subprocess.run([str(TRACK), verb, "x"], env=s.env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_log(s):
        s.assertEqual(s.row("check-log")[0], 1)
        (s.ev / "repack-t.log").write_text(GOOD)
        s.assertEqual(s.row("check-log")[0], 0)
        (s.ev / "repack-u.log").write_text(GOOD.replace("telemetry: line 6\n", ""))   # the newest log is the one checked
        rc, out = s.row("check-log")
        s.assertEqual(rc, 1); s.assertIn("talks to Jagex", out)

    def test_evidence_and_probe(s):
        s.assertEqual(s.row("check-evidence")[0], 1)
        (s.ev / "login.logcat.txt").write_text("x")
        s.assertEqual(s.row("check-evidence")[0], 0)
        s.assertEqual(s.row("check-probe")[0], 1)
        (s.ev / "api-probe.tsv").write_text("# build: 0.1.2-gabcdef12\n# result: pass 1 / 2 = 50.0%\n")
        rc, out = s.row("check-probe"); s.assertEqual((rc, "probe built at" in out), (0, True))
        (s.ev / "api-probe.tsv").write_text("# result: pass 1 / 2 = 50.0%\n")
        rc, out = s.row("check-probe"); s.assertEqual((rc, "no '# build:' line" in out), (1, True))

    def test_measure_falls_back_to_a_live_desktop(s):  # the mobile did not come up: the probe's classes jar loads in one desktop on the live stack, its report comes back, the desktop goes
        repo = Path(tempfile.mkdtemp()); b = repo / ".worktrees/x-build/host/plugins/api-probe"; b.mkdir(parents=True)
        (b / "build.sh").write_text("#!/bin/sh\nmkdir -p $(dirname $0)/build\n"); (b / "build.sh").chmod(0o755)
        fork = s.ev / "fork.sh"; log = s.ev / "fork.log"; inst = s.ev / "run1"
        fork.write_text(f'''#!/bin/sh
echo "$1 $2 $EXTRA_PLUGINS" >> {log}
case "$1" in live-desktop) mkdir -p {inst}/home/.runelite; touch {inst}/owner; echo "# result: pass 1 / 2 = 50.0%" > {inst}/home/.runelite/api-probe.tsv; echo "LIVE_DESKTOP 7780 {inst}" ;; esac''')
        fork.chmod(0o755); s.env.update(HD_REPO=str(repo), FORK_TRACK=str(fork))
        (s.ev / "server").mkdir(); dl = s.ev / "server/desktop_login.py"; dl.write_text("import sys; sys.exit(0)\n")   # the desktop's client answers
        rc, out = s.row("measure-desktop"); s.assertEqual(rc, 0, out)
        s.assertEqual((s.ev / "api-probe.tsv").read_text(), "# result: pass 1 / 2 = 50.0%\n")
        s.assertEqual(log.read_text().splitlines(), ["live-desktop x " + str(b / "build/api-probe-classes.jar"), "live-desktop-down x "])   # started with the probe jar, stopped after
        # the client gone before its report (a probe that stopped it, a crash): the wait ends, the measure fails, the desktop goes
        (s.ev / "api-probe.tsv").unlink(); shutil.rmtree(inst); log.unlink()
        fork.write_text(f'#!/bin/sh\necho "$1 $2" >> {log}\ncase "$1" in live-desktop) mkdir -p {inst}/home; touch {inst}/owner; echo "LIVE_DESKTOP 7780 {inst}" ;; esac'); dl.write_text("import sys; print('FAILED: devtools endpoint on 7780: gone'); sys.exit(1)\n")
        rc, out = s.row("measure-desktop"); s.assertEqual(rc, 1, out); s.assertIn("api-probe: no report: the desktop's client is gone", out)
        s.assertEqual(log.read_text().splitlines()[-1], "live-desktop-down x")

    def test_down_checks_the_restore(s):  # down judges the harness's baseline, not the app's writes after a first login
        st = Path(s.env["HD_ROOT"]) / "state/x"; st.mkdir(parents=True)
        (st / "serial").write_text("emulator-5560\n")
        adb = s.ev / "adb.exe"; log = s.ev / "adb.log"
        adb.write_text(f"""#!/bin/sh
echo "$*" >> {log}
case "$*" in *"echo y"*) [ -n "$NOAPP" ] || echo y ;; *"ls -1"*) printf 'quest-helper.jar\\r\\ngrounditems.jar\\r\\nopponentinfo.jar\\r\\n'; printf "${{EXTRA:-}}" ;; *"emu kill"*) exit 1 ;; esac
""")
        adb.chmod(0o755); s.env["ADB"] = str(adb)
        rc, out = s.row("down"); s.assertEqual((rc, out.strip()), (0, "restored"))
        s.assertIn("emu kill", log.read_text()); s.assertNotIn("settings.properties", log.read_text()); s.assertFalse((st / "serial").exists())
        (st / "serial").write_text("emulator-5560\n"); s.env["EXTRA"] = "probe.jar\\n"
        rc, out = s.row("down"); s.assertEqual(rc, 1); s.assertIn("RESTORE FAILED: plugins dir is not the three defaults", out)
        (st / "serial").write_text("emulator-5560\n"); s.env["NOAPP"] = "1"   # an install that failed made no plugins dir: nothing to restore
        rc, out = s.row("down"); s.assertEqual((rc, out.strip()), (0, "restored"))
        # the change's emulator exited and another change's took its port: down leaves that one running
        sys32 = s.ev / "sys32"; sys32.mkdir(); s.env["WINDOWS_SYSTEM32"] = str(sys32); ns = sys32 / "netstat.exe"
        ns.write_text("#!/bin/sh\necho '  TCP    127.0.0.1:5560   0.0.0.0:0   LISTENING   9999'\n"); ns.chmod(0o755)
        (st / "serial").write_text("emulator-5560\n"); (st / "emulator.winpid").write_text("1234\n"); log.unlink()
        rc, out = s.row("down"); s.assertEqual(rc, 0, out); s.assertIn("had exited", out); s.assertNotIn("emu kill", log.read_text())

    def test_netqa_reads_the_installed_apps_uid(s):  # the app's uid is the install's (10235 on emulator-5560), not a fixed one
        st = Path(s.env["HD_ROOT"]) / "state/x"; st.mkdir(parents=True); (st / "serial").write_text("emulator-5560\n")
        tcp = "0: 0100007F:1F90 0201000A:01BB 01 0:0 0:0 0 {} 0\n"   # a connection to 10.0.1.2:443 owned by that uid
        adb = s.ev / "adb.exe"; adb.write_text(f"""#!/bin/sh
case "$*" in *"pm list packages"*) [ -n "$NOAPP" ] || printf 'package:com.jagex.oldscape.android uid:10235\\r\\n' ;; *"exec-out cat"*) printf '{tcp.format(10235)}{tcp.format(10071).replace("0201000A", "0301000A")}' ;; esac
"""); adb.chmod(0o755); s.env["ADB"] = str(adb)
        r = subprocess.run([str(TRACK), "netqa", "x", "stop"], env=s.env, capture_output=True, text=True)
        s.assertEqual((r.returncode, r.stdout.split("--- dns")[0].strip()), (0, "10.0.1.2:443"), r.stderr)
        s.env["NOAPP"] = "1"
        r = subprocess.run([str(TRACK), "netqa", "x", "stop"], env=s.env, capture_output=True, text=True)
        s.assertEqual(r.returncode, 1); s.assertIn("not installed", r.stderr)

    def fake_windows(s):  # adb, the emulator and netstat as scripts; a started emulator's port lists as LISTENING
        sdk = s.ev / "sdk"; sys32 = s.ev / "sys32"; log = s.ev / "win.log"
        for d in (sdk / "platform-tools", sdk / "emulator", sys32 / "WindowsPowerShell/v1.0", s.ev / "relays"): d.mkdir(parents=True)
        HOSTS = re.search(r'^hosts="([^"]+)"', TRACK.read_text(), re.M).group(1)
        progs = {sdk / "platform-tools/adb.exe": f"""printf "%s\\n" "adb $*" >> {log}
[ -z "$GONE" ] || case "$*" in *boot_completed*|*get-state*) echo "adb.exe: device 'emulator-5560' not found" >&2; exit 1 ;; esac
case "$*" in *wait-for-device*) sleep 0.5 ;; *boot_completed*) echo 1 ;;
  *"dumpsys package"*) n=$(cat "$PENDING" 2>/dev/null || echo 0); [ "$n" = 0 ] || {{ echo $((n - 1)) > "$PENDING"; [ "$n" -gt 2 ] && exit 0; }}
    printf 'Active install sessions:\\n'; [ "$n" = 0 ] || printf '  Session 1:\\n    mAppPackageName=com.jagex.oldscape.andro\\n    id\\n'; printf 'Finalized install sessions:\\n' ;;
  *" install "*) echo "${{INSTALL:-Failure [INSTALL_FAILED_DUPLICATE_PACKAGE]}}" ;; *libosrsrl*) echo 1 ;;
  *"reverse --list"*) [ -n "$NOREVERSE" ] || printf 'emulator-5560 tcp:8443 tcp:8084\nemulator-5560 tcp:43594 tcp:43594\n' ;;
  *dumpsys*) echo '  NetworkAgentInfo{{network{{101}}  ni{{MOBILE[NR] CONNECTED extra: }}' ;;
  *"hello-"*) [ -z "$BOOTS" ] || for h in api.runelite.net static.runelite.net; do echo "$h  16"; done ;;
  *"nc -w 15"*) [ -z "$BOOTS" ] || for h in {HOSTS}; do echo "nc: $h:443: No address associated with hostname"; done ;;
  *"am start"*) [ -z "$BOOTS" ] || [ -n "$NOSTART" ] || echo "Status: ${{AMSTATUS:-ok}}" ;; *"echo y"*) [ -z "$BOOTS" ] || [ -n "$DIES" ] || echo y ;; *"ls -1"*) printf 'grounditems.jar\\nopponentinfo.jar\\nquest-helper.jar\\n' ;; esac""",
                 sdk / "emulator/emulator.exe": f'echo "emulator $*" >> {log}; echo "emulator: booting on $PWD"',
                 sys32 / "netstat.exe": f"sed -n 's/.*-port \\([0-9]*\\).*/  TCP 127.0.0.1:\\1 0.0.0.0:0 LISTENING 7300/p' {log}; echo '  UDP    0.0.0.0:53             *:*                                    3860'; [ -z \"$STALE\" ] || echo '  UDP    127.0.0.2:53           *:*                                    3070'; for a in $(ls {s.ev}/relays); do echo \"  UDP    $a:53           *:*                                    42${{a##*.}}\"; done",
                 sys32 / "WindowsPowerShell/v1.0/powershell.exe": f'echo "powershell $*" >> {log}; case "$*" in *FreePhysicalMemory*) n=$(cat "$FREE" 2>/dev/null || echo 9000000); printf "%s\\r\\n" "${{n%% *}}"; [ -z "$FREE" ] || echo "${{n#* }}" > "$FREE"; exit 0 ;; esac; echo "relay $ALLOW_DNS" >> {log}; echo "#< CLIXML"; touch {s.ev}/relays/$ALLOW_DNS; echo listening',   # a relay's pid: 42 and its last octet
                 sys32 / "taskkill.exe": f'echo "taskkill $*" >> {log}; rm -f {s.ev}/relays/127.0.0.${{3#42}}',
                 sys32 / "nslookup.exe": f'echo "nslookup $*" >> {log}; [ -n "$NODNS" ] || printf "Name:    api.runelite.net\\r\\nAddress:  10.0.2.2\\r\\n"',
                 sys32 / "tasklist.exe": 'case "$*" in *"PID eq 3860"*) printf \'"svchost.exe","3860","SharedAccess"\\r\\n\' ;; *"PID eq 7300"*) printf \'"qemu-system-x86_64.exe","7300","Console"\\r\\n\' ;; esac'}
        for f, body in progs.items(): f.write_text("#!/bin/sh\n" + body + "\n"); f.chmod(0o755)
        apk(s.ev / "t.apk"); live(s.env["HD_ROOT"]); (s.ev / "t.devtools.jar").write_text(""); (s.ev / "repack-t.log").write_text(GOOD)
        docker = s.ev / "docker"; docker.write_text(f'#!/bin/sh\necho "docker $*" >> {log}\ncase "$1" in logs) echo listening ;; esac\n'); docker.chmod(0o755)
        s.env.update(ANDROID_SDK=str(sdk), WINDOWS_SYSTEM32=str(sys32), DOCKER=str(docker)); s.env.pop("ADB", None)
        return log

    def test_a_failed_up_stops_its_emulator(s):  # the serial is known from the start, and down runs on the failure
        log = s.fake_windows()
        rc, out = s.row("up"); s.assertNotEqual(rc, 0); s.assertIn("install failed", out)
        s.assertIn("adb -s emulator-5560 emu kill", log.read_text())
        s.assertFalse((Path(s.env["HD_ROOT"]) / "state/x/serial").exists())

    def test_an_emulator_gone_while_booting_ends_up_and_down_restores_nothing(s):  # run 222 start 5: the emulator shut down mid-boot and up waited on boot_completed for 41 minutes
        log = s.fake_windows(); s.env["GONE"] = "1"
        rc, out = s.row("up"); s.assertNotEqual(rc, 0); s.assertIn("the emulator emulator-5560 exited while booting", out)
        s.assertIn("restored (the emulator emulator-5560 had exited)", out); s.assertNotIn("RESTORE FAILED", out)
        s.assertFalse((Path(s.env["HD_ROOT"]) / "state/x/serial").exists())

    @unittest.skipUnless(shutil.which("systemd-run") and subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True).stdout.strip() in (b"running", b"degraded"), "no systemd user manager")
    def test_the_emulator_is_recorded_under_the_runs_slice_until_down(s):  # osrs-harness R5: a run's end stops its Linux processes; the Windows emulator outlives them
        s.fake_windows(); sl = f"hd-run-{os.getpid()}.scope"; rec = Path(s.env["HD_ROOT"]) / "state/winpids" / sl / "7300"
        adb = s.ev / "sdk/platform-tools/adb.exe"; adb.write_text(adb.read_text() + f'case "$*" in *" install "*) cat {rec} > {s.ev}/seen ;; esac\n')
        subprocess.run(["systemd-run", "--user", "--scope", "-q", "--unit", sl[:-6], str(TRACK), "up", "x"], env=s.env, capture_output=True)
        subprocess.run(["systemctl", "--user", "stop", sl])
        s.assertEqual((s.ev / "seen").read_text(), "qemu-system-x86_64.exe\n")   # recorded once adb saw the emulator
        s.assertFalse(rec.exists())                                              # up failed at its install and its down dropped the record

    def test_install_waits_for_a_pending_install(s):  # INSTALL_FAILED_DUPLICATE_PACKAGE: install once the dump shows no session of the app
        log = s.fake_windows(); s.env["INSTALL"] = "Success"
        pending = s.ev / "pending"; pending.write_text("4"); s.env["PENDING"] = str(pending)   # 2 dumps before the manager is up, 2 with a session
        s.row("up")
        calls = log.read_text().splitlines(); i = next(n for n, c in enumerate(calls) if c.startswith("adb -s emulator-5560 install "))
        s.assertEqual(sum("dumpsys package" in c for c in calls[:i]), 5)

    def test_up_maps_the_apks_loopback_to_the_live_central_and_game(s):  # h-ref-apk-jav-config-central: the APK reads Central's jav_config at 127.0.0.1:8443, no sidecar
        log = s.fake_windows(); s.env.update(INSTALL="Success", BOOTS="1")
        m = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, m); (m / "tools").mkdir(); place(m / "tools")   # a stub login: never the real adb
        (m / "tools/mobile_login.py").write_text("raise SystemExit(1)\n"); subprocess.run(["git", "init", "-q", str(m)], check=True)
        up = lambda: subprocess.run([str(m / "tools/track.sh"), "up", "x"], env=s.env, capture_output=True, text=True)
        up(); calls = log.read_text()
        s.assertIn("adb -s emulator-5560 reverse tcp:8443 tcp:8084\n", calls); s.assertIn("adb -s emulator-5560 reverse tcp:43594 tcp:43594\n", calls)
        s.assertLess(calls.index("reverse tcp:8443"), calls.index("files/plugins"))   # before the app first starts
        s.assertNotIn("am start", calls)   # boot makes files/ itself: the app starts once, in mobile_login
        s.env["NOREVERSE"] = "1"; r = up(); s.assertNotEqual(r.returncode, 0); s.assertIn("adb reverse did not map tcp:8443 to tcp:8084 on emulator-", r.stdout + r.stderr)
        apk(s.ev / "t.apk", endpoint=b"http://10.0.2.2:8080/jav_config.ws?m=0&p=jagex.comxxxxxxxxx")
        rc, out = s.row("up"); s.assertEqual(rc, 1); s.assertIn("does not read jav_config from http://127.0.0.1:8443", out)

    def test_boot_pushes_the_changes_own_devtools_jar(s):  # built with the APK, kept beside it by T; never the main checkout's
        log = s.fake_windows(); s.env.update(INSTALL="Success", BOOTS="1")
        m = Path(tempfile.mkdtemp()); (m / "tools").mkdir(); place(m / "tools")   # a stub login: never the real adb
        (m / "tools/mobile_login.py").write_text("raise SystemExit(1)\n"); subprocess.run(["git", "init", "-q", str(m)], check=True)
        subprocess.run([str(m / "tools/track.sh"), "up", "x"], env=s.env, capture_output=True)
        pushes = [c for c in log.read_text().splitlines() if "push" in c and "devtools.jar" in c]
        s.assertEqual(len(pushes), 1); s.assertIn("t.devtools.jar", pushes[0]); s.assertNotIn("plugins-extra", pushes[0])
        (s.ev / "t.devtools.jar").unlink()
        rc, out = s.row("up"); s.assertEqual(rc, 1); s.assertIn("no APK or devtools jar for t", out)

    def test_down_stops_the_login_of_a_killed_up(s):  # up's caller died mid-login: down leaves no mobile_login.py of the change alive, and stops no other change's
        s.fake_windows(); s.env.update(INSTALL="Success", BOOTS="1")
        m = Path(tempfile.mkdtemp()); (m / "tools").mkdir(); place(m / "tools")
        (m / "tools/mobile_login.py").write_text("import time\ntime.sleep(600)\n"); subprocess.run(["git", "init", "-q", str(m)], check=True)
        other = subprocess.Popen(["python3", str(m / "tools/mobile_login.py"), "x-2"])   # another change's login
        up = subprocess.Popen([str(m / "tools/track.sh"), "up", "x"], env=s.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        alive = lambda p: Path(f"/proc/{p}/stat").exists() and Path(f"/proc/{p}/stat").read_text().split(") ")[1][0] != "Z"
        login = lambda: subprocess.run(["pgrep", "-f", r"mobile_login\.py x$"], capture_output=True, text=True).stdout.split()
        for _ in range(600):
            if login(): break
            time.sleep(0.05)
        p = int(login()[0]); s.assertTrue(alive(p))
        up.kill(); up.wait(); s.assertTrue(alive(p))   # the killed shell ran no trap: the login outlives it
        subprocess.run([str(m / "tools/track.sh"), "down", "x"], env=s.env, capture_output=True)
        for _ in range(200):
            if not alive(p): break
            time.sleep(0.05)
        s.assertFalse(alive(p)); s.assertTrue(alive(other.pid))
        other.kill(); other.wait()
        shutil.rmtree(m, ignore_errors=True)

    def test_up_refuses_an_apk_not_carrying_the_live_modulus_before_boot(s):  # every APK since 2026-10-31 18:32Z met 'Invalid RSA check' as its first sign
        log = s.fake_windows(); live(s.env["HD_ROOT"], "9fe5d348" + "cd" * 124)
        rc, out = s.row("up"); s.assertEqual(rc, 1)
        s.assertIn("refused: t.apk carries modulus 8555c56c, the live stack (state/live/tree.json) 9fe5d348", out)
        s.assertFalse(log.exists())                                             # nothing booted: no Windows program ran
        (Path(s.env["HD_ROOT"]) / "state/live/tree.json").write_text("{}")   # live deployed before its key pair
        rc, out = s.row("up"); s.assertEqual(rc, 1); s.assertIn("the live stack (state/live/tree.json) none, deployed before its key pair", out)

    def test_build_takes_the_live_pair_and_rebuilds_an_apk_of_another_key(s):  # a cached APK of the same T kept a stale modulus
        b = BUILD.read_text()
        s.assertIn("MODULUS=$m SERVER=$server OPENRUNE=1 LOCAL_AUTH=1 tools/repack.sh", b); s.assertIn("\nserver=127.0.0.1:8443 ", b)   # h-ref-apk-jav-config-central: Central's jav_config, no sidecar
        s.assertIn('&& carries "$ev/$T.apk" "$m" && carries "$ev/$T.apk" "http://$server/jav_config.ws"; then', b.split("\nbuild() {")[1].split("\n}")[0])
        fn = "\n".join(l for l in b.splitlines() if l.startswith(("pair=", "modulus()", "carries()")))
        run = lambda f: subprocess.run(["bash", "-c", f"set -euo pipefail\nroot={s.env['HD_ROOT']}\n{fn}\ncarries {f} \"$(modulus)\""], capture_output=True, text=True).returncode
        apk(s.ev / "a.apk"); apk(s.ev / "b.apk", "9fe5d348" + "cd" * 124); live(s.env["HD_ROOT"])
        s.assertEqual((run(s.ev / "a.apk"), run(s.ev / "b.apk")), (0, 1))
        for f in ("repack.sh", "release-dev.sh", "build/build.sh", "track.sh"):   # one source: no default reads another repo's key
            s.assertNotRegex((TRACK.parent / f).read_text(), r"SERVER_TOOLS:-|server-tools/(src|sidecar|scripts)")
        r = (TRACK.parent / "release-dev.sh").read_text()
        s.assertIn('grep -aF "$MODULUS" >/dev/null || die', r); s.assertIn('openssl pkey -in "$pair/game.key"', r)

    def test_build_keeps_the_desktop_devtools_jar(s):  # the classes jar before dexing: the server track's desktops load it
        b = BUILD.read_text().split("\nbuild() {")[1].split("\n}")[0]
        s.assertIn('[ -f "$ev/$T.devtools-desktop.jar" ]', b)
        s.assertIn('cp "$copy/re/devtools-build/devtools.jar" "$ev/$T.devtools-desktop.jar"', b)

    def test_build_copy_owns_its_decoded_apk_tree(s):  # repack.sh rm -rf's and patches re/apk in place: a shared one races
        b = BUILD.read_text().split("\nbuild() {")[1].split("\n}")[0]
        lines = "\n".join(l for l in b.splitlines() if l.strip().startswith(("for e in", "for n in")))
        with tempfile.TemporaryDirectory() as d:
            repo, copy = Path(d, "repo"), Path(d, "copy")
            for n in ("apk", "keys", "host"): (repo / "re" / n).mkdir(parents=True)
            (copy / "re").mkdir(parents=True); (copy / "re/apk").symlink_to(repo / "re/apk")   # a copy made before the change
            subprocess.run(["bash", "-c", f"set -euo pipefail\nrepo={repo}\ncopy={copy}\n{lines}"], check=True)
            s.assertFalse((copy / "re/apk").exists()); s.assertTrue((copy / "re/keys").is_symlink()); s.assertFalse((copy / "re/host").exists())

    def test_up_holds_deploys_off_until_down(s):  # h-deploy-spares-live-judge: a judge's mobile plays on the live stack from up to down
        t = TRACK.read_text(); up = t.split("\nup() {")[1].split("\n}")[0]; down = t.split("\ndown() {")[1].split("\n}")[0]
        s.assertLess(up.index('{"live": 1'), up.index('flock -s "$root/state/live/stack.lock" true')); s.assertLess(up.index("stack.lock"), up.index("  boot"))
        s.assertLess(down.index('$hd stack "$slug" --clear'), down.index("s=$(serial) || return 0"))   # cleared also when no emulator came up

    def test_emulator_has_no_console_window(s):  # started directly, not through cmd's start; its output is the run's log
        log = s.fake_windows(); s.row("up")
        s.assertNotIn("cmd.exe", TRACK.read_text())
        s.assertIn("emulator -avd Agent_Lite", log.read_text())
        s.assertIn("emulator: booting", (Path(s.env["HD_ROOT"]) / "state/x/emulator.log").read_text())

    def test_avd_prepares_the_state_every_start_inherits(s):  # h-mobile-light-avd: one writable boot; no tap of a prompt or the launcher's ANR at any start
        log = s.fake_windows(); home = s.ev / "avd"; s.env["ANDROID_AVD_HOME"] = str(home)
        rc, out = s.row("avd"); s.assertEqual(rc, 1); s.assertIn("no system-images/android-37.0/google_apis/x86_64", out)
        (s.ev / "sdk/system-images/android-37.0/google_apis/x86_64").mkdir(parents=True)
        (s.ev / "sys32/tasklist.exe").write_text(f'#!/bin/sh\ngrep -q "emu kill" {log} || printf \'"qemu-system-x86_64.exe","7300","Console"\\r\\n\'\n')   # gone once killed
        rc, out = s.row("avd"); s.assertEqual(rc, 0, out); calls = log.read_text()
        s.assertEqual((home / "Agent_Lite.avd/config.ini").read_text(), (TRACK.parent / "Agent_Lite.ini").read_text())
        s.assertIn("emulator -avd Agent_Lite -lowram -no-boot-anim -gpu host -port 5560", calls)   # writable: no -read-only
        for c in ("settings put secure immersive_mode_confirmations confirmed", "settings put global hide_error_dialogs 1", "settings put global animator_duration_scale 0",
                  "pm disable-user --user 0 com.google.android.apps.nexuslauncher", "am set-debug-app --persistent com.android.chrome", "--disable-fre", "svc wifi disable"):
            s.assertIn(c, calls)
        s.assertLess(calls.index("--disable-fre"), calls.index("emu kill"))
        s.assertNotIn('"Got it"', (TRACK.parent / "mobile_login.py").read_text())

    def test_login_acts_on_the_screen_it_reads(s):  # the issuer's sign-in by LoginIndex and the focused window; an unknown screen or a refusal is FAILED, never a wait
        import importlib.util; spec = importlib.util.spec_from_file_location("mobile_login", TRACK.parent / "mobile_login.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        app, chrome = m.PKG, "com.android.chrome"
        flow = [("LOGIN_SCREEN", 0, app, {}), ("LOGIN_SCREEN", 12, app, {}),
                ("LOGIN_SCREEN", 30, chrome, {}), ("LOGIN_SCREEN", 10, app, {}), ("LOGGING_IN", 30, app, {}), ("LOGGED_IN", 30, app, {})]
        s.assertEqual([m.step(*f)[:2] for f in flow], [("tap", "Existing User"), ("tap", "Accept"), ("wait",), ("tap", "Play Now"), ("wait",), ("done",)])
        s.assertEqual(m.step("LOGIN_SCREEN", 9, app, {})[0], "fail")                                      # the server's refusal
        s.assertEqual(m.step("LOGIN_SCREEN", 4, app, {})[0], "fail")                                      # a login screen it does not know
        s.assertEqual(m.step("LOGIN_SCREEN", 30, "com.android.settings", {"x": (1, 1)})[0], "fail")       # a window it does not know
        s.assertEqual(m.step("UNKNOWN", -1, m.HOME, {})[0], "wait")                                       # the app's window has not taken focus yet
        s.assertEqual(m.step("LOGIN_SCREEN", 0, "", {})[0], "wait")                                        # no focused window: never the app's canvas tapped blind
        s.assertEqual(m.step("LOGIN_SCREEN", 10, m.HOME, {})[0], "fail")                                  # the app left for the home
        s.assertEqual(m.step("LOGIN_SCREEN", 30, chrome, {"Use without an account": (540, 2085)})[0], "wait")   # no first-run tap: the prepared AVD's Chrome skips it
        s.assertEqual(m.step("LOGIN_SCREEN", 30, chrome, {"ERR_CONNECTION_REFUSED": (1, 1)})[0], "fail")  # the issuer unreachable
        s.assertEqual(m.step("UNKNOWN", -1, app, {}, 1000)[0], "fail")                                   # the app's start error page
        s.assertEqual(m.step("UNKNOWN", -1, app, {}, 5)[0], "wait")                                      # a start state RuneLite has no name for
        form = {"Username": (1, 1), "Password": (1, 2), "Sign in": (1, 3)}; name = m.account("x")
        f = lambda u, uf, p, pf: {"Username": (u, uf, 5, 1), "Password": (p, pf, 5, 2)}
        on = lambda fields, posted=False: m.step("LOGIN_SCREEN", 30, chrome, {**form, **{t: (5, 1) for t, *_ in fields.values() if t}}, None, name, fields, posted)
        s.assertEqual(on(f("", False, "", False))[:2], ("tap", "Username field"))                          # the field itself, never its label
        s.assertEqual(on(f("", True, "", False)), ("type", "Username"))                                     # typed once focused
        s.assertEqual(on(f(name[:4], True, "", False)), ("type", "Username"))                               # still landing: main types once per screen
        s.assertEqual(on(f(name, True, "", False))[:2], ("tap", "Password field"))
        s.assertEqual(on(f(name, False, "", True)), ("type", "Password"))
        s.assertEqual(on(f(name, False, name, True))[:2], ("tap", "Sign in"))                              # both read back holding the name
        s.assertEqual(on(f("", False, name, False))[:2], ("tap", "Username field"))                        # run 289: the name among the labels, the Username empty: not posted
        s.assertEqual(on(f("x", True, "", False))[0], "fail")                                               # a field holding another text
        s.assertEqual(on(f(name, False, name, False), True), ("wait",))                                     # posted: the form leaves next
        s.assertEqual(on(f("", False, name, False), True), ("wait",))                                       # the posted page while the redirect hands over (seen live: Username cleared)
        s.assertEqual(on(f("", False, "", False), True)[0], "fail")                                         # Central's 401 answers its form again
        tip = m.step("LOGIN_SCREEN", 30, chrome, {**form, "Please fill out this field.": (1, 1)}, None, name, f("", True, name, False), True)
        s.assertEqual(tip, ("fail", "Central's form did not post: Please fill out this field."))           # run 289's stuck form
        s.assertEqual(m.step("LOGIN_SCREEN", 30, chrome, form, None, name, {})[0], "fail")                  # a form without its fields
        lab, fields = m.views('<node text="Username " class="android.widget.TextView" bounds="[0,0][10,10]" /><node NAF="true" text="" class="android.widget.EditText" focused="true" bounds="[20,0][40,10]" hint="Username" />')
        s.assertEqual((lab, fields), ({"Username": (5, 5)}, {"Username": ("", True, 30, 5)}))
        s.assertNotEqual(name, m.account("y")); s.assertLessEqual(len(name), 12)                          # one account per slug, a login name's length

    def test_concurrent_boots_take_distinct_ports(s):
        log = s.fake_windows(); (Path(s.env["HD_ROOT"]) / "harness/changes/y.md").write_text("")
        ps = [subprocess.Popen([str(TRACK), "up", g], env=s.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for g in ("x", "y")]
        for p in ps: p.wait()
        s.assertEqual(sorted(re.findall(r"-port (\d+)", log.read_text())), ["5560", "5562"])
        s.assertEqual(log.read_text().count("emu kill"), 2)
        s.assertEqual(sorted(re.findall(r"-dns-server (\S+)", log.read_text())), ["127.0.0.2", "127.0.0.3"])   # each its own relay

    def test_a_boot_waits_for_its_guest_ram_on_windows(s):  # h-mobile-login-page-39-again: emulators past Windows' memory paged the WSL VM out, freezing the server past the app's 10 s timeouts
        log = s.fake_windows(); free = s.ev / "free"; free.write_text("1000000 2097152"); s.env["FREE"] = str(free)   # KB: 976 MB, then 2048 MB (Agent_Lite.ini hw.ramSize)
        rc, out = s.row("up"); s.assertIn("waiting for 2048 MB available on Windows (now 976 MB)", out)
        calls = log.read_text(); s.assertEqual(calls.count("FreePhysicalMemory"), 2); s.assertLess(calls.rindex("FreePhysicalMemory"), calls.index("emulator -avd"))
        free.write_text("oops oops"); rc, out = s.row("up"); s.assertNotEqual(rc, 0); s.assertIn("Windows available memory unread: oops", out)

    def test_a_running_emulator_holds_no_lock(s):  # the port lock ends when adb sees the emulator, not when it exits
        log = s.fake_windows(); emu = s.ev / "sdk/emulator/emulator.exe"
        emu.write_text(emu.read_text() + "exec sleep 5\n")
        subprocess.run([str(TRACK), "up", "x"], env=s.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # returns while it runs
        r = subprocess.run(["flock", "-n", str(Path(s.env["HD_ROOT"]) / "state/emulator-port.lock"), "true"])
        s.assertEqual(r.returncode, 0)

    def test_check_blocked(s):  # up's check: the two RuneLite hosts answer TLS, every other host fails to resolve, no public address connects
        st = Path(s.env["HD_ROOT"]) / "state/x"; st.mkdir(parents=True); (st / "serial").write_text("emulator-5560\n")
        src = TRACK.read_text(); var = lambda n: re.search(rf'^{n}="([^"]+)"', src, re.M).group(1).split()
        hosts, allowed = var("hosts"), var("allowed")
        s.assertEqual(set(allowed), {"api.runelite.net", "static.runelite.net"})
        s.assertTrue({"legal.jagex.com", "oldschool.runescape.com", "sdk.iad-01.braze.com", "cdn.cookielaw.org", "app-measurement.com", "sdk-api-v1.singular.net", "google.com"} <= set(hosts))
        adb = s.ev / "adb.exe"
        adb.write_text(f"""#!/bin/sh
case "$*" in *push*) ;;
  *"hello-"*) for h in {" ".join(allowed)}; do [ "$h" = "$SHUT" ] && echo "$h " || echo "$h  16"; done ;;
  *"8.8.8.8"*) [ -z "$OPEN_ADDR" ] || echo " $OPEN_ADDR" ;;
  *"nc -w"*) for h in {" ".join(hosts)}; do [ "$h" = "$OPEN" ] || echo "nc: $h:443: No address associated with hostname"; done ;; esac
""")
        adb.chmod(0o755); s.env["ADB"] = str(adb)
        rc, out = s.row("check-blocked"); s.assertEqual(rc, 0, out); s.assertIn("allowed: api.runelite.net static.runelite.net; blocked:", out)
        s.assertEqual((st / "hello-api.runelite.net").read_bytes()[:1], b"\x16")   # a real ClientHello is pushed
        s.env["SHUT"] = "static.runelite.net"
        rc, out = s.row("check-blocked"); s.assertEqual(rc, 1); s.assertIn("NOT REACHED (no TLS answer on 443): static.runelite.net", out)
        s.env.pop("SHUT"); s.env["OPEN"] = "auth.jagex.com"
        rc, out = s.row("check-blocked"); s.assertEqual(rc, 1); s.assertIn("NOT BLOCKED (resolves or connects): auth.jagex.com", out)
        s.env.pop("OPEN"); s.env["OPEN_ADDR"] = "8.8.8.8"   # a public address connects with no lookup
        rc, out = s.row("check-blocked"); s.assertEqual(rc, 1); s.assertIn("NOT BLOCKED (resolves or connects): 8.8.8.8", out)

    def test_up_puts_the_mobile_on_the_allowlist(s):  # the allowlist container, the emulator asking it, the wifi path off
        log = s.fake_windows(); s.env["INSTALL"] = "Success"; s.row("up")
        calls = log.read_text()
        s.assertIn("docker run -d --rm --name mobile-allow -p 127.0.0.1:8053:53/tcp -p 127.0.0.1:443:443", calls)
        s.assertIn("-dns-server 127.0.0.2", calls); s.assertIn("shell svc wifi disable", calls)
        s.assertNotIn("private_dns", TRACK.read_text())

    def test_up_proves_the_allowlist_answers_on_the_windows_loopback(s):  # the emulator resolves from Windows: no answer there, the container is replaced once, then the port's holder is named
        log = s.fake_windows(); s.env.update(INSTALL="Success", NODNS="1")
        rc, out = s.row("up"); calls = log.read_text()
        s.assertEqual(rc, 1); s.assertIn("Windows udp 53 held by: svchost.exe (pid 3860, SharedAccess)", out)
        s.assertEqual((calls.count("docker run -d --rm --name mobile-allow"), calls.count("docker rm -f mobile-allow"), calls.count("nslookup api.runelite.net 127.0.0.2")), (2, 1, 2))
        s.assertNotIn("emulator -avd", calls)
        s.env.pop("NODNS"); log.write_text(""); s.row("up"); calls = log.read_text()
        s.assertLess(calls.index("nslookup api.runelite.net 127.0.0.2"), calls.index("emulator -avd")); s.assertNotIn("docker rm", calls)

    def test_the_mobiles_dns_is_its_own_relay_at_an_address_no_windows_process_holds(s):  # ICS holds 0.0.0.0:53, a stale relay 127.0.0.2:53
        log = s.fake_windows(); s.env.update(INSTALL="Success", STALE="1"); st = Path(s.env["HD_ROOT"]) / "state/x"
        s.row("up"); calls = log.read_text()   # up fails at check-blocked (the fake mobile reaches nothing), and its down runs
        s.assertIn("relay 127.0.0.3", calls); s.assertLess(calls.index("nslookup api.runelite.net 127.0.0.3"), calls.index("emulator -avd"))
        s.assertIn("-dns-server 127.0.0.3", calls); s.assertNotIn("127.0.0.1 ", calls.split("emulator -avd")[1].split("\n")[0])
        s.assertIn("taskkill /F /PID 423 /FI IMAGENAME eq powershell.exe", calls); s.assertFalse((st / "allow-relay.winpid").exists())
        s.assertNotIn("3070", calls)   # the stale holder is never stopped

    def test_allow_answers_only_the_allowed_names(s):  # tools/allow.py: DNS and the TLS relay admit api/static.runelite.net alone
        import ssl, struct, sys; sys.path.insert(0, str(TRACK.parent)); import allow
        q = lambda n, t=1: b"\x12\x34\x01\x00\x00\x01\0\0\0\0\0\0" + b"".join(bytes([len(p)]) + p.encode() for p in n.split(".")) + b"\0" + struct.pack(">HH", t, 1)
        a = allow.answer(q("Static.RuneLite.net")); s.assertEqual((a[:2], a[3] & 15, a[7], a[-4:]), (b"\x12\x34", 0, 1, bytes([10, 0, 2, 2])))
        a = allow.answer(q("api.runelite.net", 28)); s.assertEqual((a[3] & 15, a[7]), (0, 0))   # no AAAA: IPv4 alone reaches the relay
        for n in ("auth.jagex.com", "sdk.iad-01.braze.com", "app-measurement.com", "runelite.net", "x.api.runelite.net"):
            a = allow.answer(q(n)); s.assertEqual((a[3] & 15, a[7]), (3, 0), n)   # NXDOMAIN
        def hello(n):
            o = ssl.MemoryBIO(); t = ssl.create_default_context().wrap_bio(ssl.MemoryBIO(), o, server_hostname=n)
            try: t.do_handshake()
            except ssl.SSLWantReadError: return o.read()
        s.assertEqual(allow.sni(hello("api.runelite.net")), "api.runelite.net"); s.assertEqual(allow.sni(hello("auth.jagex.com")), "auth.jagex.com")
        s.assertIsNone(allow.sni(b"GET / HTTP/1.1\r\n")); s.assertIsNone(allow.sni(hello("api.runelite.net")[:40]))
        import socket; x, y = socket.socketpair(); h = hello("static.runelite.net"); x.sendall(h[:100])
        threading = __import__("threading"); threading.Timer(0.2, x.sendall, (h[100:],)).start()
        s.assertEqual(allow.record(y), h); x.close(); y.close()   # a hello split across segments is read whole
        l = socket.create_server(("127.0.0.1", 0)); c = socket.create_connection(l.getsockname())
        t = threading.Thread(target=allow.relay, args=(l.accept()[0],)); t.start()
        c.sendall(hello("auth.jagex.com")); s.assertEqual(c.recv(5), b""); t.join(); c.close(); l.close()   # closed with no connect out
        from unittest import mock; u = socket.create_server(("127.0.0.1", 0)); real, asked = socket.getaddrinfo, []
        def flaky(*a, **k):   # Docker's resolver says "Try again" once, then answers
            asked.append(a[0])
            if len(asked) == 1: raise socket.gaierror(socket.EAI_AGAIN, "Try again")
            return real("127.0.0.1", u.getsockname()[1], socket.AF_INET, socket.SOCK_STREAM)
        l = socket.create_server(("127.0.0.1", 0)); c = socket.create_connection(l.getsockname()); h = hello("api.runelite.net")
        with mock.patch("socket.getaddrinfo", flaky):
            t = threading.Thread(target=allow.relay, args=(l.accept()[0],)); t.start(); c.sendall(h)
            v = u.accept()[0]; s.assertEqual(allow.record(v), h); v.close(); c.close(); t.join(); l.close(); u.close()
        s.assertEqual(asked, ["api.runelite.net", "api.runelite.net"])   # resolved again after EAI_AGAIN, relayed the hello

    def test_network_qa_allows_three_hosts(s):  # the skill's allowed list: the local server and the two RuneLite hosts, nothing else
        skill = (TRACK.parent.parent.parent / ".claude/skills/network-qa/SKILL.md").read_text()
        allowed = skill[skill.index("- Allowed"):skill.index("- Any other host is a FAIL")]
        s.assertEqual(set(re.findall(r"10\.0\.2\.2|127\.0\.0\.1|[\w.-]+\.(?:net|com|io)", allowed)), {"127.0.0.1", "10.0.2.2", "api.runelite.net", "static.runelite.net"})
        for t in ("Braze", "OneTrust", "Google", "singular", "jagex", "runescape"): s.assertNotIn(t, allowed)

    def test_windows_programs_by_absolute_path(s):  # a .ps1 runs as its text (Windows refuses the file from the UNC path); no bare .exe (a lost PATH)
        src = "\n".join(l for l in TRACK.read_text().splitlines() if not l.lstrip().startswith("#"))
        s.assertEqual(re.findall(r'"\$ps"[^\n]*?-(\w*File|EncodedCommand)', src), ["EncodedCommand"]); s.assertEqual(re.findall(r'(?:^|[\s(|;&])[\w.-]+\.exe\b', src), [])

    def test_a_missing_windows_program_names_its_variable(s):
        st = Path(s.env["HD_ROOT"]) / "state/x"; st.mkdir(parents=True); (st / "serial").write_text("emulator-5560\n")
        s.env.pop("ADB", None); s.env["ANDROID_SDK"] = "/nonexistent"
        rc, out = s.row("down"); s.assertEqual(rc, 2); s.assertIn("/nonexistent/platform-tools/adb.exe not found: set ANDROID_SDK", out)

    def test_slug_from_env(s):  # hd rows runs a contract row with no slug argument, SLUG in the env
        s.env["SLUG"] = "x"; (s.ev / "login.logcat.txt").write_text("x")
        r = subprocess.run([str(TRACK), "check-evidence"], env=s.env, capture_output=True, text=True)
        s.assertEqual(r.returncode, 0, r.stderr)

    def test_slug_names_a_change(s):  # `log PATTERN` would read the pattern as the slug
        r = subprocess.run([str(TRACK), "log", "Have a nice day"], env=s.env, capture_output=True, text=True)
        s.assertEqual(r.returncode, 2); s.assertIn('no change or goal "Have a nice day"', r.stderr)
        s.assertFalse((Path(s.env["HD_ROOT"]) / "state").exists())


    def test_repo_from_worktree(s):  # run from a worktree, the script's repo is the main checkout
        m = Path(tempfile.mkdtemp()); w = m / ".worktrees" / "tools-wt"
        g = lambda *a, c=m: subprocess.run(["git", "-C", str(c), *a], check=True, capture_output=True)
        g("init", "-q"); g("config", "user.name", "t"); g("config", "user.email", "t@t"); g("commit", "-q", "--allow-empty", "-m", "c")
        g("update-ref", "refs/remotes/origin/HEAD", "HEAD"); g("worktree", "add", "-q", "--detach", str(w))
        (w / "tools").mkdir(); place(w / "tools")
        apk(s.ev / "t.apk"); live(s.env["HD_ROOT"]); (s.ev / "t.devtools.jar").write_text(""); (s.ev / "t.devtools-desktop.jar").write_text("")
        r = subprocess.run([str(w / "tools" / "track.sh"), "build", "x"], env={**s.env, "HD_REPO": str(m)}, capture_output=True, text=True)
        s.assertIn("cached", r.stdout, r.stderr)
        s.assertTrue((m / ".worktrees" / "x").is_dir()); s.assertFalse((w / ".worktrees").exists())
        shutil.rmtree(m, ignore_errors=True)


class Endpoint(unittest.TestCase):
    def test_the_apk_takes_every_jagex_url_from_openrune_endpoint(s):  # the user's word: one variable points every Jagex endpoint at our server
        import importlib.util
        spec = importlib.util.spec_from_file_location("patch_server", TRACK.parent / "patch_server.py"); ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
        old = next(iter(ps.URLS)); url = ps.padded_url("http://10.0.2.2:8080", "/jav_config.ws?m=0", len(old))
        s.assertTrue(url.startswith(b"http://10.0.2.2:8080/jav_config.ws?m=0&p=jagex.com")); s.assertEqual(len(url), len(old))
        for bad in ("https://oldschool.config.runescape.com:443", "http://auth.jagex.com:80", "10.0.2.2:8080"):
            with s.assertRaises(SystemExit): ps.padded_url(bad, "/slr.ws?order=LPWM", len(old))
        src = (TRACK.parent / "repack.sh").read_text()
        s.assertIn("OPENRUNE_ENDPOINT=${OPENRUNE_ENDPOINT:-http://127.0.0.1:8443}", src); s.assertIn('--endpoint "$OPENRUNE_ENDPOINT"', src)
        s.assertNotRegex(src, r"\$\{?SERVER\b")


if __name__ == "__main__":
    unittest.main()
