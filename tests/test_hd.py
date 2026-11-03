"""hd's commands over a temporary ledger: the dispatch and the writes that take no git or GitHub."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import hd  # noqa: E402
import store  # noqa: E402


class Hd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        store.DB = str(Path(self.dir.name) / "hd.db")
        hd.act.tick_later = lambda: None

    def tearDown(self):
        self.dir.cleanup()

    def test_the_view_by_role_the_orchestrator_spawns_and_stops_the_driver_reads_cards(self):
        import contextlib, io, os
        db = store.connect()
        db.execute("INSERT INTO session(pid, pid_start, definition, started_at, role) VALUES (?, 1, 'd', 't', 'driver')", (os.getpid(),))
        db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t', 'card', 'c', 'card c @abc'), ('t', 'ended', 'c', 'run 1: closed with its change')")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hd.view(db, hd.act.cfg())
        self.assertIn("card     c", out.getvalue()); self.assertIn("ended    c", out.getvalue()); self.assertIn("goals    ", out.getvalue())
        self.assertEqual(db.execute("SELECT seen_event FROM session").fetchone()[0], 2)
        db.execute("UPDATE session SET role='orchestrator', seen_event=0")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hd.view(db, hd.act.cfg())
        self.assertNotIn("card", out.getvalue()); self.assertIn("ended    c", out.getvalue()); self.assertNotIn("goals", out.getvalue())

    def test_criterion_add_with_a_cmd_option(self):
        hd.main(["criterion", "add", "x", "acc-1", "--kind", "judge", "--text", "the rule", "--cmd", "accuracy", "--source", "accuracy"])
        hd.main(["criterion", "add", "x", "lint", "--kind", "script", "--text", "lint passes", "--cmd", "make lint", "--source", "seed"])
        rows = store.connect().execute("SELECT rid, kind, cmd, source FROM criterion ORDER BY id").fetchall()
        self.assertEqual([tuple(r) for r in rows], [("acc-1", "judge", "accuracy", "accuracy"), ("lint", "script", "make lint", "seed")])

    def test_a_deploy_ok_marks_the_staged_changes_live(self):
        import argparse, os
        db = store.connect()
        db.execute("INSERT INTO job(kind, key, started_at) VALUES ('deploy', 'tr1:fork-1', '2026-01-01T00:00:00')")
        db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('s-a', 'refs/heads/staging', 's', '2025-12-31T00:00:00'), ('s-b', 'refs/heads/staging', 's', '2026-01-02T00:00:00')")
        hd.cmd_job(argparse.Namespace(kind="deploy", key="tr1:fork-1", result="ok", detail=""))
        self.assertEqual([r[0] for r in store.connect().execute("SELECT change FROM landed WHERE target='live'")], ["s-a"])   # s-b landed after the deploy began

    def test_a_malformed_ask_is_refused_before_any_row(self):   # alert 20: options split on a ':' inside the text left an unanswerable question
        import argparse, sqlite3
        hd.store.connect().execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES ('x', 'dev', 'code', 'i', 'b', 't')")
        with self.assertRaises(SystemExit):
            hd.cmd_ask(argparse.Namespace(slug="x", text="q?", option=["a:mark it upstream: false", "b:close it"]))
        self.assertEqual(hd.store.connect().execute("SELECT count(*) FROM ask").fetchone()[0], 0)

    def test_ask_then_answer_waives_a_criterion(self):
        hd.main(["criterion", "add", "x", "dupes-3", "--kind", "judge", "--text", "t", "--source", "seed"])
        hd.main(["ask", "x", "shop sell path?", "--option", "a:dep server-shop:dep server-shop", "--option", "b:waive dupes-3:waive dupes-3"])
        db = store.connect()
        self.assertEqual(json.loads(db.execute("SELECT options_json FROM ask").fetchone()[0])[1]["effect"], "waive dupes-3")
        with self.assertRaises(SystemExit):
            hd.main(["ask", "x", "another?", "--option", "a:x:none"])   # one open question per change
        hd.main(["answer", "x", "b", "the lamp cannot be sold"])
        self.assertEqual(db.execute("SELECT waived FROM criterion WHERE rid='dupes-3'").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT by, words FROM answer").fetchone()[1], "the lamp cannot be sold")

    def test_fault_raises_an_alert_and_dismiss_disposes_of_it(self):
        hd.main(["fault", "7", "hd criterion add is unusable"])
        db = store.connect()
        a = db.execute("SELECT id, kind, subject, disposition FROM alert").fetchone()
        self.assertEqual((a["kind"], a["subject"], a["disposition"]), ("fault", "7", None))
        hd.main(["dismiss", str(a["id"]), "fixed"])
        self.assertEqual(db.execute("SELECT disposition, why FROM alert").fetchone()[1], "fixed")


if __name__ == "__main__":
    unittest.main()
