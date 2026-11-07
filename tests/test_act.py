"""act's dispatch over a temporary ledger: every Step kind the pass lists is acted on (the publish job once was not)."""
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

    def test_a_pin_leaves_staging_as_the_change_that_supersedes_it_merges(self):
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
        g("checkout", "-qb", "dev/next", "main"); (repo / "n").write_text("n\n"); g("add", "n"); g("commit", "-qm", "next")
        act.stage(db, decide.Change("real", "fork"), T, g("rev-parse", "HEAD"))   # reverted once: a later merge does not revert again
        self.assertEqual(db.execute("SELECT count(*) FROM event WHERE kind='unpinned'").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
