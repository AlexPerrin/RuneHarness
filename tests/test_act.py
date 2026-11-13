"""act's dispatch over a temporary ledger: every Step kind the pass lists is acted on (the publish job once was not)."""
import dataclasses
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import act  # noqa: E402
import decide  # noqa: E402
import store  # noqa: E402


class Act(unittest.TestCase):
    def test_upstream_seeds_go_to_the_package_and_in_game_ones_to_the_change(self):   # a change carries no upstream criteria
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        db = store.connect(str(Path(d.name) / "hd.db"))
        T = decide.Track("fork", "a/b", "/nowhere", "refs/heads/main", "up/b")
        act.seed(db, decide.Change("m", "fork", feature="feat/x"), T)
        act.seed(db, decide.Change("pr-feat-x-fork", "fork", feature="feat/x", members=("m",)), T)
        rids = lambda c: {r[0] for r in db.execute("SELECT rid FROM criterion WHERE change=?", (c,))}
        self.assertTrue({"accuracy", "playable", "gamevals", "spotless"} <= rids("m"))
        self.assertFalse({"claims", "texts", "ci", "dupes", "style"} & rids("m"))
        self.assertTrue({"claims", "texts", "ci", "dupes", "style", "spotless"} <= rids("pr-feat-x-fork"))
        self.assertFalse({"accuracy", "playable", "gamevals"} & rids("pr-feat-x-fork"))

    def test_every_step_kind_the_pass_lists_is_acted_on(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.addCleanup(setattr, act, "STATE", act.STATE); self.addCleanup(setattr, store, "DB", store.DB)
        store.DB = str(Path(d.name) / "hd.db"); act.STATE = d.name   # the ledger and the tick lock of this test alone
        calls = []
        for name in ("start", "brief", "stage", "wake", "release"):
            self.addCleanup(setattr, act, name, getattr(act, name))
            setattr(act, name, lambda *a, _n=name, **k: calls.append((_n, a[1].kind if _n == "start" else None)))
        for mod, name, fake in ((act.publish, "card", lambda *a, **k: calls.append(("card", None))), (act, "changes", lambda: [decide.Change("x", "fork")]),
                                (act, "goals", lambda: []), (decide, "plan", None)):
            self.addCleanup(setattr, mod, name, getattr(mod, name))
            if fake:
                setattr(mod, name, fake)
        kinds = ["run", "build", "gate", "ship", "deploy", "measure", "publish", "merge", "card", "release", "wait"]
        decide.plan = lambda *a, **k: [decide.Action("x", decide.Step(kind=k, why=k, role="dev", mode="code", key="t:r")) for k in kinds]
        act.tick(store.DB, offline=True)
        self.assertEqual(calls, [("brief", None)] + [("start", k) for k in ("build", "gate", "ship", "deploy", "measure", "publish")] + [("stage", None), ("card", None), ("release", None), ("wake", None)])

    def test_a_rerun_clears_the_failed_job_and_an_alert_is_raised_once(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.addCleanup(setattr, act, "STATE", act.STATE); self.addCleanup(setattr, store, "DB", store.DB)
        store.DB = str(Path(d.name) / "hd.db"); act.STATE = d.name
        for mod, name, fake in ((act, "wake", lambda *a, **k: None), (act, "changes", lambda: [decide.Change("x", "fork")]),
                                (act, "goals", lambda: []), (decide, "plan", None)):
            self.addCleanup(setattr, mod, name, getattr(mod, name))
            if fake:
                setattr(mod, name, fake)
        db = store.connect(store.DB)
        db.execute("INSERT INTO job(kind, key, change, ok, detail, ended_at) VALUES ('gate', 'tr:fork-1', 'x', 0, 'ci (401)', 't')")
        decide.plan = lambda *a, **k: [decide.Action("x", decide.Step("rerun", "r", key="gate tr:fork-1")),
                                       decide.Action("x", decide.Step("alert", "twice", key="gate:tr:fork-1"))]
        act.tick(store.DB, offline=True)
        act.tick(store.DB, offline=True)
        self.assertIsNone(db.execute("SELECT 1 FROM job").fetchone())
        self.assertEqual(store.Ledger(db).rerun("x", "gate", "tr:fork-1"), "ci (401)")
        self.assertEqual([tuple(r) for r in db.execute("SELECT subject, count FROM alert")], [("gate:tr:fork-1", 1)])

    def test_a_brief_names_the_previous_run_and_what_failed_after_it(self):
        db = store.connect(":memory:")
        T = decide.Track("harness", "a/b", "/nowhere", "refs/heads/main", prefix="harness")
        ch = decide.Change("x", "harness", body="b")
        db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('x','dev','code','i','b','t','2000-01-01','handback','run 1: submitted abc')")
        store.event(db, "job", "x", None, "gate abc fail tests (1 failed)")
        text = act.brief_text(db, ch, T, decide.Step("run", "gate failed twice", role="dev", mode="code"), 2)
        self.assertIn("## the previous run: dev code, ended handback: run 1: submitted abc", text)
        self.assertIn("after it: job gate abc fail tests (1 failed)", text)

    def test_a_pass_that_raises_leaves_a_fault_alert_not_a_traceback(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.addCleanup(setattr, act, "STATE", act.STATE); self.addCleanup(setattr, store, "DB", store.DB)
        store.DB = str(Path(d.name) / "hd.db"); act.STATE = d.name
        for mod, name, fake in ((act, "wake", lambda *a, **k: None), (act, "changes", lambda: []), (act, "goals", lambda: []), (decide, "plan", None)):
            self.addCleanup(setattr, mod, name, getattr(mod, name))
            if fake:
                setattr(mod, name, fake)
        def boom(*a, **k):
            raise ValueError("'1' is not in list")
        decide.plan = boom
        self.assertEqual(act.tick(store.DB, offline=True), [])
        a = store.connect(store.DB).execute("SELECT kind, subject, detail FROM alert").fetchone()
        self.assertEqual((a["kind"], a["subject"]), ("fault", "pass")); self.assertIn("ValueError", a["detail"])

    def test_a_deploy_holds_the_live_stack_lock_from_its_pass(self):   # h-deploy-spares-live-judge: an up after this pass waits the deploy out
        import fcntl, os
        from unittest import mock
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.addCleanup(setattr, act, "STATE", act.STATE); act.STATE = d.name
        db = store.connect(str(Path(d.name) / "hd.db")); seen = {}
        def popen(cmd, **k):
            probe = open(Path(d.name) / "live" / "stack.lock")
            try:
                fcntl.flock(probe, fcntl.LOCK_SH | fcntl.LOCK_NB); seen["held"] = False
            except BlockingIOError:
                seen["held"] = True
            seen["fds"] = k.get("pass_fds")
            return mock.Mock(pid=1)
        with mock.patch.object(act, "job_env", lambda *a, **k: {}), mock.patch.object(act.subprocess, "run"), \
             mock.patch.object(act.subprocess, "Popen", popen), mock.patch.object(act.observe, "pid_start", lambda p: 0):
            act.start(db, decide.Step("deploy", "staging moved", key="tr1:fork-1"), decide.Change("staging", "fork"),
                      decide.Track("fork", "o/fork", "/nonexistent", "refs/heads/main", upstream="o/r", recipes={"deploy": "fork-1"}))
        self.assertTrue(seen["held"]); self.assertEqual(len(seen["fds"]), 1)
        probe = open(Path(d.name) / "live" / "stack.lock"); fcntl.flock(probe, fcntl.LOCK_SH | fcntl.LOCK_NB)   # the pass's own copy is gone: only the deploy's held it

    def test_a_released_clone_leaves_its_uncommitted_work_as_evidence(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.addCleanup(setattr, act, "ROOT", act.ROOT); act.ROOT = d.name
        db = store.connect(str(Path(d.name) / "hd.db"))
        repo = Path(d.name, "r"); wt = repo / ".worktrees" / "s"
        g = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)
        repo.mkdir(); g("init", "-q"); (repo / "f").write_text("a\n"); g("add", "-A"); g("commit", "-qm", "c"); g("worktree", "add", "-q", "--detach", str(wt))
        (wt / "f").write_text("b\n")
        store.own(db, "worktree", str(wt), "s")
        act.release(db, "worktree", str(wt))
        self.assertFalse(wt.exists())
        self.assertIn("+b", Path(d.name, "evidence/s/clone.diff").read_text())

    def test_a_pin_leaves_staging_as_the_change_that_supersedes_it_merges_or_hd_yaml_drops_it_and_follows_its_moved_tip(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        db = store.connect(str(Path(d.name) / "hd.db"))
        repo, bare = Path(d.name, "r"), Path(d.name, "fork.git")
        g = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        repo.mkdir(); g("init", "-q", "-b", "main"); g("config", "user.name", "t"); g("config", "user.email", "t@t")
        (repo / "f").write_text("a\n"); (repo / "k").write_text("1\n"); g("add", "-A"); g("commit", "-qm", "base"); g("remote", "add", "fork", str(bare))
        g("checkout", "-qb", "local/spike"); (repo / "f").write_text("spike\n"); g("commit", "-qam", "spike")
        g("checkout", "-qb", "local/other", "main"); (repo / "k").write_text("2\n"); g("commit", "-qam", "other")
        g("checkout", "-qb", "dev/real", "main"); (repo / "f").write_text("real\n"); g("commit", "-qam", "real"); head = g("rev-parse", "HEAD")
        g("checkout", "-q", "--detach", "main"); g("push", "-q", "fork", "local/spike", "local/other")
        g("fetch", "-q", "fork")
        T = decide.Track("fork", "x/y", str(repo), "refs/heads/main", "up/y", remote="fork", pins=(("local/spike", "real"), ("local/other", "")))
        act.stage(db, decide.Change("real", "fork"), T, head)
        wt = repo / ".worktrees" / "staging"
        self.assertEqual(((wt / "f").read_text(), (wt / "k").read_text()), ("real\n", "2\n"))   # the superseded pin out, the other kept
        self.assertEqual([r["kind"] for r in db.execute("SELECT kind FROM event ORDER BY id")], ["unpinned", "merged"])
        g("checkout", "-q", "local/other"); (repo / "k").write_text("3\n"); g("commit", "-qam", "other moved"); g("push", "-q", "fork", "local/other"); g("fetch", "-q", "fork")
        g("checkout", "-qb", "dev/next", "main"); (repo / "n").write_text("n\n"); g("add", "n"); g("commit", "-qm", "next")
        act.stage(db, decide.Change("next", "fork"), T, g("rev-parse", "HEAD"))   # reverted once: a later merge does not revert again
        self.assertEqual(db.execute("SELECT count(*) FROM event WHERE kind='unpinned'").fetchone()[0], 1)
        self.assertEqual(((wt / "f").read_text(), (wt / "k").read_text()), ("real\n", "3\n"))   # the moved pin merged again, the reverted one stays out
        g("checkout", "-qb", "dev/third", "main"); (repo / "t").write_text("t\n"); g("add", "t"); g("commit", "-qm", "third")
        act.stage(db, decide.Change("third", "fork"), dataclasses.replace(T, pins=(("local/spike", "real"),)), g("rev-parse", "HEAD"))
        self.assertEqual(((wt / "k").read_text(), (wt / "t").read_text()), ("1\n", "t\n"))   # a pin dropped from hd.yaml leaves staging at the next merge
        self.assertEqual(db.execute("SELECT count(*) FROM event WHERE kind='unpinned'").fetchone()[0], 3)   # both merges of the dropped pin


class Kpi(unittest.TestCase):
    def test_orientation_before_the_first_edit_of_a_transcript(self):   # KPIs 1-5 of h-orientation-before-first-edit
        import json
        import kpi
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        p = Path(d.name) / "t.jsonl"
        use = lambda tokens, *calls: json.dumps({"message": {"usage": {"input_tokens": 1, "cache_read_input_tokens": tokens},
                                                             "content": [{"type": "tool_use", "name": n, "input": i} for n, i in calls]}})
        bash = lambda c: ("Bash", {"command": c})
        p.write_text("\n".join([
            use(10, ("Read", {"file_path": "/h/state/briefs/7.md"}), bash("cat /h/tracks/fork/track.md")),
            '{"type": "user"}',
            use(20, bash("cd /c && grep -rn foo src"), ("Grep", {"pattern": "x"}), ("Read", {"file_path": "/c/A.kt"}),
                bash("cd /c; sed -n 1,9p A.kt"), bash("python3 /h/harness/hd.py show s"), bash("git -C /c log -3"), bash("make")),
            use(30, bash("cat > /c/new.txt <<'EOF'"), ("Edit", {}), bash("hd show s"))]))
        m = kpi.measure(str(p))
        self.assertEqual((m["calls"], m["brief"], m["search"], m["read"], m["show"], m["git"], m["other"]), (9, 2, 2, 2, 1, 1, 1))
        self.assertEqual((m["tokens"], m["shows"]), (31, 2))   # the context at the edit; hd show over the whole run
        p.write_text(use(5, ("Read", {"file_path": "/x"}), bash("sed -i s/a/b/ f")))
        self.assertEqual(kpi.measure(str(p))["calls"], 1)   # a Bash write is the first edit
        p.write_text(use(5, ("Read", {"file_path": "/x"})))
        self.assertIsNone(kpi.measure(str(p))["calls"])
        self.assertIsNone(kpi.measure(str(Path(d.name) / "none")))


if __name__ == "__main__":
    unittest.main()
