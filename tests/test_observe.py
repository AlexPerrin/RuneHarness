"""fetch, landed, candidate and procs over a throwaway git repo."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import act  # noqa: E402
import observe  # noqa: E402
import store  # noqa: E402
from decide import Change, Track  # noqa: E402


def sh(path, *args):
    return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, check=True,
                          env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")).stdout.strip()


class Observe(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.dir.name, "repo")
        os.makedirs(self.repo)
        sh(self.repo, "init", "-q", "-b", "live")
        open(os.path.join(self.repo, "a"), "w").write("1\n")
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
        open(os.path.join(self.repo, "b"), "w").write("2\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "work")
        self.assertEqual(observe.fetch(self.db, self.T), {"refs/heads/harness/h-one"})

    def test_candidate_is_the_head_when_linear_and_a_deterministic_merge_otherwise(self):
        base = sh(self.repo, "rev-parse", "HEAD")
        sh(self.repo, "checkout", "-qb", "harness/h-one")
        open(os.path.join(self.repo, "b"), "w").write("2\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "work")
        head = sh(self.repo, "rev-parse", "HEAD")
        self.assertEqual(act.candidate(self.repo, base, [head])[1], head)
        sh(self.repo, "checkout", "-q", "live")
        open(os.path.join(self.repo, "c"), "w").write("3\n")
        sh(self.repo, "add", "c")
        sh(self.repo, "commit", "-qm", "live moved")
        live = sh(self.repo, "rev-parse", "HEAD")
        t1, c1 = act.candidate(self.repo, live, [head])
        t2, c2 = act.candidate(self.repo, live, [head])
        self.assertEqual((t1, c1), (t2, c2))
        self.assertNotEqual(c1, head)
        self.assertEqual(sh(self.repo, "ls-tree", "--name-only", t1), "a\nb\nc")
        open(os.path.join(self.repo, "b"), "w").write("conflict\n")
        sh(self.repo, "add", "b")
        sh(self.repo, "commit", "-qm", "live edits b")
        with self.assertRaises(act.Conflict) as cm:
            act.candidate(self.repo, sh(self.repo, "rev-parse", "HEAD"), [head])
        self.assertEqual(cm.exception.args[0], ["b"])

    def test_landed_when_the_head_is_an_ancestor_of_the_target(self):
        sh(self.repo, "checkout", "-qb", "harness/h-one")
        open(os.path.join(self.repo, "b"), "w").write("2\n")
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

    def test_dead_job_without_result_is_an_attempt(self):
        log = os.path.join(self.dir.name, "gate-x.log")
        open(log, "w").write("Traceback\nMemoryError at 0xdeadbeef1234\n")
        self.db.execute("INSERT INTO job(kind, key, change, pid, pid_start, log, started_at) VALUES ('gate', 'k', 'h-one', 999999, 1, ?, 't')", (log,))
        observe.procs(self.db)
        a = self.db.execute("SELECT * FROM attempt").fetchone()
        self.assertEqual((a["kind"], a["cause"]), ("gate", "MemoryError at 0x"))
        j = self.db.execute("SELECT pid, ended_at FROM job").fetchone()
        self.assertIsNone(j["pid"])
        self.assertIsNotNone(j["ended_at"])


if __name__ == "__main__":
    unittest.main()
