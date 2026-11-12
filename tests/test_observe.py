"""fetch, landed, candidate and procs over a throwaway git repo."""
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import act  # noqa: E402
import observe  # noqa: E402
import store  # noqa: E402
from decide import Change, Step, Track  # noqa: E402


def sh(path, *args):
    return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, check=True,
                          env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")).stdout.strip()


class Observe(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.dir.name, "repo")
        os.makedirs(self.repo)
        sh(self.repo, "init", "-q", "-b", "live")
        Path(os.path.join(self.repo, "a")).write_text("1\n")
        sh(self.repo, "add", "a")
        sh(self.repo, "commit", "-qm", "base")
        self.T = Track("harness", "x/y", self.repo, "refs/heads/live", "", "harness", {})
        self.db = store.connect(os.path.join(self.dir.name, "hd.db"))
        self.ch = Change("h-one", "harness")

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def test_fetch_records_refs_and_reports_what_moved(self):
        self.assertEqual(observe.fetch(self.db, self.T), {"refs/heads/live"})
        self.assertEqual(observe.fetch(self.db, self.T), set())
        sh(self.repo, "checkout", "-qb", "harness/h-one")
        Path(os.path.join(self.repo, "b")).write_text("2\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "work")
        self.assertEqual(observe.fetch(self.db, self.T), {"refs/heads/harness/h-one"})

    def test_candidate_is_the_head_when_linear_and_a_deterministic_merge_otherwise(self):
        base = sh(self.repo, "rev-parse", "HEAD")
        sh(self.repo, "checkout", "-qb", "harness/h-one")
        Path(os.path.join(self.repo, "b")).write_text("2\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "work")
        head = sh(self.repo, "rev-parse", "HEAD")
        self.assertEqual(act.candidate(self.repo, base, [head])[1], head)
        sh(self.repo, "checkout", "-q", "live")
        Path(os.path.join(self.repo, "c")).write_text("3\n")
        sh(self.repo, "add", "c")
        sh(self.repo, "commit", "-qm", "live moved")
        live = sh(self.repo, "rev-parse", "HEAD")
        t1, c1 = act.candidate(self.repo, live, [head])
        t2, c2 = act.candidate(self.repo, live, [head])
        self.assertEqual((t1, c1), (t2, c2))
        self.assertNotEqual(c1, head)
        self.assertEqual(sh(self.repo, "ls-tree", "--name-only", t1), "a\nb\nc")
        Path(os.path.join(self.repo, "b")).write_text("conflict\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "live edits b")
        with self.assertRaises(act.Conflict) as cm:
            act.candidate(self.repo, sh(self.repo, "rev-parse", "HEAD"), [head])
        self.assertEqual(cm.exception.args[0], ["b"])

    def test_candidate_leaves_out_a_dep_head_a_later_head_carries(self):
        base = sh(self.repo, "rev-parse", "HEAD")
        heads = []
        for name, text in (("d1", "x\n"), ("d2", "y\n")):
            sh(self.repo, "checkout", "-qb", name, base)
            Path(os.path.join(self.repo, "a")).write_text(text)
            sh(self.repo, "commit", "-qam", name)
            heads.append(sh(self.repo, "rev-parse", "HEAD"))
        with self.assertRaises(act.Conflict):
            act.candidate(self.repo, base, heads)
        sh(self.repo, "checkout", "-qb", "head", heads[0])
        with self.assertRaises(subprocess.CalledProcessError):
            sh(self.repo, "merge", "-q", "d2")
        Path(os.path.join(self.repo, "a")).write_text("xy\n")
        sh(self.repo, "commit", "-qam", "resolve")
        head = sh(self.repo, "rev-parse", "HEAD")
        self.assertEqual(act.candidate(self.repo, base, heads + [head])[1], head)

    def test_landed_when_the_head_is_an_ancestor_of_the_target(self):
        sh(self.repo, "checkout", "-qb", "harness/h-one")
        Path(os.path.join(self.repo, "b")).write_text("2\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "work")
        head = sh(self.repo, "rev-parse", "HEAD")
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('h-one', ?, 't', 'c', 't')", (head,))
        observe.fetch(self.db, self.T)
        observe.landed(self.db, self.T, "refs/heads/live", [self.ch])
        self.assertIsNone(self.db.execute("SELECT 1 FROM landed").fetchone())
        sh(self.repo, "checkout", "-q", "live")
        sh(self.repo, "merge", "-q", "--ff-only", head)
        observe.fetch(self.db, self.T)
        observe.landed(self.db, self.T, "refs/heads/live", [self.ch])
        self.assertEqual(self.db.execute("SELECT sha FROM landed WHERE change='h-one'").fetchone()[0], head)

    def test_a_run_whose_agent_was_interrupted_ends_as_a_console_death(self):
        import json
        db = store.connect(str(Path(self.dir.name) / "hd.db"))
        t = Path(self.dir.name) / "agent-a1.jsonl"
        t.write_text(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "working"}]}}) + "\n")
        db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, started_at, agent_id, transcript) VALUES ('c', 'dev', 'code', 'i', 'b', 't', 't', 'a1', ?)", (str(t),))
        db.execute("INSERT INTO session(pid, pid_start, definition, started_at, role) VALUES (1, 1, 'd', 't', 'orchestrator')")
        observe.runs(db)
        self.assertIsNone(db.execute("SELECT ended_at FROM run WHERE id=1").fetchone()[0])   # a working agent is left alone
        with t.open("a") as f:
            f.write(json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "[Request interrupted by user]"}]}}) + "\n")
        self.addCleanup(setattr, act, "stop_scope", act.stop_scope); act.stop_scope = lambda r: None
        observe.runs(db)
        r = db.execute("SELECT ended_at, end_kind FROM run WHERE id=1").fetchone()
        self.assertEqual(r["end_kind"], "console"); self.assertIsNotNone(r["ended_at"])
        self.assertIn("interrupted", db.execute("SELECT detail FROM event WHERE kind='ended'").fetchone()[0])

    def test_a_run_ends_with_its_orchestrator_session_not_with_a_driver(self):   # a usage limit ended the session: four runs held their slots for three days
        db = store.connect(str(Path(self.dir.name) / "hd.db"))
        self.addCleanup(setattr, act, "stop_scope", act.stop_scope); act.stop_scope = lambda r: None
        db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, started_at) VALUES ('c', 'dev', 'code', 'i', 'b', 't', '2026-01-02')")
        db.execute("INSERT INTO session(pid, pid_start, definition, started_at, role) VALUES (999999, 1, 'd', '2026-01-01', 'driver')")
        db.execute("INSERT INTO session(pid, pid_start, definition, started_at, role) VALUES (1, 1, 'd', '2026-01-01', 'orchestrator')")
        self.addCleanup(setattr, observe, "alive", observe.alive); observe.alive = lambda pid, start: pid != 999999
        observe.sessions(db, "d")   # the driver's pid is gone
        observe.runs(db)
        self.assertIsNone(db.execute("SELECT ended_at FROM run").fetchone()[0])
        db.execute("UPDATE session SET ended_at='x' WHERE role='orchestrator'")
        db.execute("INSERT INTO session(pid, pid_start, definition, started_at, role) VALUES (2, 1, 'd', '2026-01-03', 'orchestrator')")   # its successor
        observe.runs(db)
        self.assertEqual(db.execute("SELECT end_kind FROM run").fetchone()[0], "console")

    def test_dead_job_without_result_is_an_attempt(self):
        log = os.path.join(self.dir.name, "gate-x.log")
        Path(log).write_text("Traceback\nMemoryError at 0xdeadbeef1234\n")
        self.db.execute("INSERT INTO job(kind, key, change, pid, pid_start, log, started_at) VALUES ('gate', 'k', 'h-one', 999999, 1, ?, 't')", (log,))
        observe.procs(self.db)
        a = self.db.execute("SELECT * FROM attempt").fetchone()
        self.assertEqual((a["kind"], a["cause"]), ("gate", "MemoryError at 0x"))
        j = self.db.execute("SELECT pid, ended_at FROM job").fetchone()
        self.assertIsNone(j["pid"])
        self.assertIsNotNone(j["ended_at"])


    def test_a_retry_starts_while_its_last_attempt_left_processes_in_the_scope(self):
        observe.fetch(self.db, self.T)
        root = Path(self.dir.name, "root")
        (root / "tracks/harness").mkdir(parents=True)
        (root / "tracks/harness/track.sh").write_text("exit 0\n")
        (root / "tracks/harness/track.sh").chmod(0o755)
        key = f"rs{os.getpid()}:script"; k12 = key.replace(":", "-")[:12]   # unique per process: two gates run this suite at once
        unit = f"hd-h-one-measure-{k12}"
        self.addCleanup(subprocess.run, ["systemctl", "--user", "stop", unit + ".scope"], capture_output=True)
        subprocess.run(["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit, "--", "bash", "-c", "sleep 300 &"], check=True)
        saved = act.ROOT, act.STATE, act.job_env
        act.ROOT, act.STATE, act.job_env = str(root), str(root / "state"), lambda db, ch, T, s, **more: dict(os.environ, **more)
        try:
            act.start(self.db, Step("measure", "t", key=key), self.ch, self.T)
        finally:
            act.ROOT, act.STATE, act.job_env = saved
        try:
            os.waitpid(self.db.execute("SELECT pid FROM job").fetchone()[0], 0)
        except ChildProcessError:   # already reaped by subprocess's cleanup of the dropped Popen (any later Popen in the suite): it exited, so its rc is written
            pass
        self.assertEqual(Path(root, "state/h-one", f"measure-{k12}.rc").read_text(), "0\n")
    def test_disk_free_is_a_fact_and_below_the_level_an_alert_naming_the_compaction(self):
        observe.disk(self.db, 0, (self.dir.name, "/no/such/path"))
        self.assertEqual([r["path"] for r in self.db.execute("SELECT path FROM disk")], [self.dir.name])
        self.assertIsNone(self.db.execute("SELECT 1 FROM alert").fetchone())
        observe.disk(self.db, 10**9, (self.dir.name,))   # a level no disk has
        a = self.db.execute("SELECT kind, subject, detail FROM alert").fetchone()
        self.assertEqual((a["kind"], a["subject"]), ("disk", self.dir.name)); self.assertIn("Optimize-VHD", a["detail"])

    def test_osrs_mcp_containers_above_their_live_sessions_alert(self):
        me = str(os.getpid())
        for labels, n in ((f"{me}\n", 0), (f"{me}\n{me}\n", 1), (f"{me}\n\n", 1)):   # one per session; two for one; an unlabelled one
            self.db.execute("DELETE FROM alert")
            with mock.patch.object(observe.subprocess, "run", return_value=mock.Mock(stdout=labels, returncode=0)):
                observe.mcp(self.db)
            self.assertEqual(self.db.execute("SELECT count(*) FROM alert WHERE kind='fault' AND subject='osrs-mcp'").fetchone()[0], n)
        with mock.patch.object(observe.subprocess, "run", return_value=mock.Mock(stdout="docker could not be found\n", returncode=1)):
            observe.mcp(self.db)   # no daemon: unknown, the earlier alert stands and no new one is counted
        self.assertEqual(self.db.execute("SELECT count FROM alert WHERE subject='osrs-mcp'").fetchone()[0], 1)

    def test_release_removes_a_worktree_and_a_dir_then_drops_their_rows(self):
        wt = os.path.join(self.repo, ".worktrees", "h-one")
        sh(self.repo, "worktree", "add", "-q", "--detach", wt)
        d = os.path.join(self.repo, ".worktrees", "cand"); os.makedirs(d + "/x")
        store.own(self.db, "worktree", wt, "h-one"); store.own(self.db, "dir", d, "job:gate:k")
        for kind, key in (("worktree", wt), ("dir", d), ("dir", d)):   # idempotent: a second release of a gone dir ends at once
            self.assertTrue(act.release(self.db, kind, key))
        self.assertFalse(os.path.exists(wt) or os.path.exists(d))
        self.assertNotIn(wt, sh(self.repo, "worktree", "list"))
        self.assertIsNone(self.db.execute("SELECT 1 FROM artifact").fetchone())

    def test_a_release_refused_because_a_container_holds_it_waits_and_any_other_refusal_alerts(self):
        store.own(self.db, "image", "or:t", "h-one")
        for stderr, alerts in (("conflict: unable to remove repository reference: container abc is using its referenced image", 0), ("Cannot connect to the Docker daemon", 1)):
            with mock.patch.object(act, "absent", side_effect=[False, False]), \
                 mock.patch.object(act.subprocess, "run", return_value=mock.Mock(stderr=stderr)):
                self.assertFalse(act.release(self.db, "image", "or:t"))
            self.assertEqual(self.db.execute("SELECT count(*) FROM alert").fetchone()[0], alerts)
        self.assertIn("Docker daemon", self.db.execute("SELECT detail FROM alert").fetchone()[0])
        self.assertTrue(self.db.execute("SELECT 1 FROM artifact").fetchone())   # the row stays until absence is observed

    def test_a_refused_login_alerts_the_user_and_leaves_the_read_unknown(self):
        with mock.patch.object(observe, "transport", return_value=(401, {}, '{"message":"Bad credentials"}')):
            self.assertIsNone(observe.gh(self.db, "repos/o/r/pulls/1"))
        self.assertIn("gh auth login", self.db.execute("SELECT detail FROM alert WHERE kind='quota' AND subject='github-login'").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
