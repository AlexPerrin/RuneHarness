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

    def test_the_orchestrator_sees_each_live_run_and_the_alerts(self):  # T5
        import contextlib, io, os
        db = store.connect()
        t = Path(self.dir.name) / "agent.jsonl"; t.write_text("{}")
        os.utime(t, (1, os.path.getmtime(t) - 1800))
        db.execute("INSERT INTO session(pid, pid_start, definition, started_at, role) VALUES (?, 1, 'd', 't', 'orchestrator')", (os.getpid(),))
        db.execute("INSERT INTO run(id, change, role, mode, input, brief, agent_id, listed_at, started_at, transcript) VALUES (7, 'c', 'dev', 'code', 'i', 'b', 'a1', 't', 't', ?)", (str(t),))
        db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t', 'alert', 'c', 'alert 1 fault')")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hd.view(db, hd.act.cfg())
        self.assertIn("alert    c", out.getvalue()); self.assertIn("agent a1: last moved 30 min ago, " + str(t), out.getvalue())

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

    def test_a_deploy_ok_marks_the_library_heads_it_built_in_live(self):   # h-live-sign-in-needs-central: a Central change never reached live
        import argparse, os, subprocess
        from unittest import mock
        repo = Path(self.dir.name) / "c"; g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "a"); a1 = g("rev-parse", "HEAD")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "b"); b1 = g("rev-parse", "HEAD")
        db = store.connect()
        db.execute("INSERT INTO job(kind, key, started_at) VALUES ('deploy', 'tr1:fork-1', '2026-01-01T00:00:00')")
        db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('c-in', ?, 't', ?, 't'), ('c-out', ?, 't', 'x', 't')", (a1, a1, ("e" if b1[0] == "f" else "f") + b1[1:]))   # an unknown head: never b1 itself
        defs = [hd.act.Change("c-in", "central"), hd.act.Change("c-out", "central")]
        with mock.patch.object(hd.act, "changes", return_value=defs), mock.patch.dict(os.environ, {"CENTRAL": f"{repo}:{b1}"}):
            hd.cmd_job(argparse.Namespace(kind="deploy", key="tr1:fork-1", result="ok", detail=""))
        self.assertEqual([r[0] for r in store.connect().execute("SELECT change FROM landed WHERE target='live'")], ["c-in"])   # c-out's head is not in the built head

    def test_a_malformed_ask_is_refused_before_any_row(self):   # alert 20: options split on a ':' inside the text left an unanswerable question
        import argparse, sqlite3
        hd.store.connect().execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES ('x', 'dev', 'code', 'i', 'b', 't')")
        with self.assertRaises(SystemExit):
            hd.cmd_ask(argparse.Namespace(slug="x", text="q?", option=["a:mark it upstream: false", "b:close it"]))
        with self.assertRaises(SystemExit):   # a dep with no target would write a blank dep into the definition
            hd.cmd_ask(argparse.Namespace(slug="x", text="q?", option=["a:wait on it:dep", "b:close it:close"]))
        self.assertEqual(hd.store.connect().execute("SELECT count(*) FROM ask").fetchone()[0], 0)

    def test_criterion_add_on_an_existing_rid_corrects_it_and_drops_its_results(self):  # G1
        hd.main(["criterion", "add", "x", "stays", "--kind", "judge", "--text", "t", "--cmd", "playable", "--source", "accuracy"])
        db = store.connect()
        cid = db.execute("SELECT id FROM criterion").fetchone()[0]
        db.execute("INSERT INTO check_result(criterion_id, tree, ok, at) VALUES (?, 'tree', 1, 't')", (cid,))
        hd.main(["criterion", "add", "x", "stays", "--kind", "judge", "--text", "t2", "--cmd", "qa-server", "--source", "accuracy"])
        self.assertEqual([tuple(r) for r in db.execute("SELECT id, text, cmd FROM criterion")], [(cid, "t2", "qa-server")])
        self.assertEqual(db.execute("SELECT count(*) FROM check_result").fetchone()[0], 0)

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

    def test_a_fork_only_dep_done_on_staging_joins_a_candidate_off_main(self):   # central-rights-test-mod dropped from central-game-session's
        import os, subprocess
        from decide import Change, Cfg, Track
        repo = os.path.join(self.dir.name, "repo")
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        def commit(f, branch, new=False):
            subprocess.run(["git", "-C", repo, "checkout", "-q"] + (["-b"] if new else []) + [branch], check=True, env=env)
            Path(repo, f).write_text(f)
            subprocess.run(["git", "-C", repo, "add", f], check=True, env=env)
            subprocess.run(["git", "-C", repo, "commit", "-qm", f], check=True, env=env)
            return hd.act.git(repo, "rev-parse", "HEAD")
        os.makedirs(repo); subprocess.run(["git", "-C", repo, "init", "-q", "-b", "main"], check=True)
        Path(repo, "base").write_text("base"); subprocess.run(["git", "-C", repo, "add", "base"], check=True)
        subprocess.run(["git", "-C", repo, "commit", "-qm", "base"], check=True, env=env)
        fork_only = commit("fork", "fork-only", new=True)
        merged = commit("merged", "main")   # an upstream dep already on main
        cfg = Cfg(tracks={"central": Track("central", "x/y", repo, "refs/heads/main", "o/y")})
        defs = {"c": Change("c", "central", deps=("fork", "up")), "fork": Change("fork", "central", upstream=False), "up": Change("up", "central")}
        self.addCleanup(setattr, hd, "change", hd.change); hd.change = defs.get
        db = store.connect()
        db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('fork', ?, 't', 't', 't'), ('up', ?, 't', 't', 't')", (fork_only, merged))
        db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('fork', 'refs/heads/staging', ?, 't')", (fork_only,))
        self.assertEqual(hd.dep_inputs(db, cfg, defs["c"]), ([fork_only], {}))


if __name__ == "__main__":
    unittest.main()
