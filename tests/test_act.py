"""act's dispatch over a temporary ledger: every Step kind the pass lists is acted on (the publish job once was not)."""
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


if __name__ == "__main__":
    unittest.main()
