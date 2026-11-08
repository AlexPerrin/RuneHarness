"""publish() over a fake GitHub transport: the card's acts and texts, the approval, a publish killed after step n resumes
at n+1 with the card's texts, a refused write spends the approval."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import observe  # noqa: E402
import publish  # noqa: E402
import store  # noqa: E402
from decide import Change, Track  # noqa: E402

F = Track("fork", "AlexPerrin/OpenRune-Server", "/nowhere", "refs/remotes/origin/main", "OpenRune/OpenRune-Server", "dev", {}, "fork")
HEAD = "a" * 40
PR = {"number": 5, "state": "open", "draft": True, "head": "b" * 40, "title": "old", "body": "old body", "merged_at": None}
TEXTS = {"pr-title.txt": "feat: x\n", "pr-body.md": "## Summary\nnew body\n", "pr-comment.md": "Head `aaaaaaa`: did x\n",
         "pr-reply-77.md": "> why?\n\n@m because\n"}


class Fake:
    """Answers GitHub writes; fails every call once `die_after` calls were served."""
    def __init__(self, die_after=None, refuse=None, checks=("completed", "success")):
        self.calls, self.die_after, self.refuse, self.checks = [], die_after, refuse, checks

    def __call__(self, method, url, data=None, headers=()):
        if self.die_after is not None and len(self.calls) >= self.die_after:
            raise RuntimeError("killed")
        self.calls.append((method, url, data))
        if self.refuse and url.endswith(self.refuse):
            return 422, {}, '{"message": "Validation Failed"}'
        if url.endswith("/check-runs?per_page=100"):
            return 200, {"etag": "e1"}, json.dumps({"check_runs": [{"name": "build", "status": self.checks[0], "conclusion": self.checks[1]}]})
        if url.endswith("/status"):
            return 200, {"etag": "e2"}, json.dumps({"statuses": []})
        if url.endswith("/pulls/5"):
            return 200, {"etag": "e3"}, json.dumps({"node_id": "N5"})
        if url.endswith("/pulls") and method == "POST":
            return 201, {}, json.dumps({"number": 9, "html_url": "u", "node_id": "N9"})
        if url.endswith("/pulls/9"):
            return 200, {}, json.dumps({"node_id": "N9"})
        return 201 if method == "POST" else 200, {}, json.dumps({"id": 1})


class Publish(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = store.connect(str(Path(self.dir.name) / "hd.db"))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('genie', ?, 't', 'c', 't')", (HEAD,))
        observe.wait = lambda s: None
        self.pushes = []
        publish.subprocess.run = lambda cmd, **k: (self.pushes.append(cmd), type("R", (), {"returncode": 0, "stderr": ""})())[1]   # the push

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def test_card_lists_the_acts_and_texts_for_an_existing_draft_pr(self):
        cid = publish.card(self.db, Change("genie", "fork", pr=5, public="content/genie"), F, HEAD, PR, TEXTS)
        c = self.db.execute("SELECT * FROM card WHERE id=?", (cid,)).fetchone()
        self.assertEqual([s["name"] for s in json.loads(c["steps_json"])], ["push", "edit", "ci", "comment", "ready"])
        t = json.loads(c["texts_json"])
        self.assertEqual(t["title"], "feat: x")
        self.assertTrue(t["comment"].startswith("Head `aaaaaaa`: did x\n\n> why?"))
        self.assertEqual(publish.card(self.db, Change("genie", "fork", pr=5), F, HEAD, PR, TEXTS), cid)   # same digest, same card
        rendered = publish.render(self.db, c, F)
        self.assertIn("PR OpenRune/OpenRune-Server#5", rendered)
        self.assertIn("hd.py approve genie aaaaaaa", rendered)

    def test_a_finding_we_already_answered_gets_no_second_reply(self):   # A3: #367 re-posted three answered replies
        cs = [{"id": 77, "node_id": "IC_77", "user": {"login": "m"}, "created_at": "2026-11-01T00:00:00Z"},
              {"id": 78, "node_id": "IC_78", "user": {"login": publish.OWNER}, "created_at": "2026-11-02T00:00:00Z"},
              {"id": 79, "node_id": "IC_79", "user": {"login": "m"}, "created_at": "2026-11-03T00:00:00Z"}]
        self.db.execute("INSERT INTO gh(url, body) VALUES (?, ?)", ("repos/OpenRune/OpenRune-Server/issues/5/comments", json.dumps(cs)))
        texts = dict(TEXTS, **{"pr-reply-79.md": "> new?\n\n@m fixed\n"})
        cid = publish.card(self.db, Change("genie", "fork", pr=5), F, HEAD, PR, texts)
        c = self.db.execute("SELECT * FROM card WHERE id=?", (cid,)).fetchone()
        self.assertEqual([s.get("findings") for s in json.loads(c["steps_json"]) if s["name"] == "comment"], [["79"]])
        self.assertNotIn("why?", json.loads(c["texts_json"])["comment"])

    def test_new_pr_card(self):
        cid = publish.card(self.db, Change("genie", "fork"), F, HEAD, None, TEXTS)
        c = self.db.execute("SELECT * FROM card WHERE id=?", (cid,)).fetchone()
        self.assertEqual([s["name"] for s in json.loads(c["steps_json"])], ["push", "pr", "ci", "comment", "ready"])

    def test_approve_needs_the_latest_card_at_that_head(self):
        cid = publish.card(self.db, Change("genie", "fork", pr=5), F, HEAD, PR, TEXTS)
        with self.assertRaises(SystemExit):
            publish.approve(self.db, "genie", "b" * 7)
        self.assertEqual(publish.approve(self.db, "genie", HEAD[:7]), cid)
        with self.assertRaises(SystemExit):
            publish.approve(self.db, "genie", HEAD[:7])

    def test_killed_after_a_step_resumes_with_the_cards_texts(self):
        ch = Change("genie", "fork", pr=5, public="content/genie")
        cid = publish.card(self.db, ch, F, HEAD, PR, TEXTS)
        publish.approve(self.db, "genie", HEAD[:7])
        observe.transport = Fake(die_after=1)   # the edit happens, the ci read dies
        with self.assertRaises(RuntimeError):
            publish.publish(self.db, cid, F, "/nowhere")
        done = [r["name"] for r in self.db.execute("SELECT name FROM publish_step WHERE card=? AND done_at IS NOT NULL ORDER BY n", (cid,))]
        self.assertEqual(done, ["push", "edit"])
        fake = observe.transport = Fake()
        publish.publish(self.db, cid, F, "/nowhere")
        self.assertEqual([m for m, _, _ in fake.calls], ["GET", "GET", "POST", "GET", "POST"])   # checks, status, comment, pr node, ready
        self.assertEqual(fake.calls[2][2]["body"], json.loads(self.db.execute("SELECT texts_json FROM card WHERE id=?", (cid,)).fetchone()[0])["comment"])
        self.assertEqual(self.db.execute("SELECT spent_why FROM approval WHERE card=?", (cid,)).fetchone()[0], "published")

    def test_ci_failure_keeps_the_approval_and_records_the_failure(self):
        cid = publish.card(self.db, Change("genie", "fork", pr=5), F, HEAD, PR, TEXTS)
        publish.approve(self.db, "genie", HEAD[:7])
        observe.transport = Fake(checks=("completed", "failure"))
        publish.publish(self.db, cid, F, "/nowhere")
        self.assertIsNone(self.db.execute("SELECT spent_at FROM approval WHERE card=?", (cid,)).fetchone()[0])
        self.assertEqual(self.db.execute("SELECT detail FROM event WHERE kind='ci-failed'").fetchone()[0], "aaaaaaa ['build']")
        self.assertEqual(len(store.Ledger(self.db).undone_steps(cid)), 3)

    def test_a_rejected_push_spends_the_approval_and_the_next_card_names_it(self):
        ch = Change("genie", "fork", pr=5, public="content/genie")
        cid = publish.card(self.db, ch, F, HEAD, PR, TEXTS)
        publish.approve(self.db, "genie", HEAD[:7])
        publish.subprocess.run = lambda cmd, **k: type("R", (), {"returncode": 1, "stderr": "! [rejected] non-fast-forward"})()
        observe.transport = Fake()
        publish.publish(self.db, cid, F, "/nowhere")
        why = self.db.execute("SELECT spent_why FROM approval WHERE card=?", (cid,)).fetchone()[0]
        self.assertIn("non-fast-forward", why)
        cid2 = publish.card(self.db, ch, F, HEAD, PR, TEXTS, refusal=why)
        self.assertNotEqual(cid2, cid)
        self.assertIn("refused", publish.render(self.db, self.db.execute("SELECT * FROM card WHERE id=?", (cid2,)).fetchone(), F))

    def test_a_read_that_fails_spends_nothing(self):
        cid = publish.card(self.db, Change("genie", "fork", pr=5), F, HEAD, PR, TEXTS)
        publish.approve(self.db, "genie", HEAD[:7])
        fake = Fake()
        real = fake.__call__
        def flaky(method, url, data=None, headers=()):
            return (503, {}, "") if url.endswith("/pulls/5") and method == "GET" else real(method, url, data, headers)
        observe.transport = flaky
        publish.publish(self.db, cid, F, "/nowhere")
        self.assertIsNone(self.db.execute("SELECT spent_at FROM approval WHERE card=?", (cid,)).fetchone()[0])
        self.assertEqual(len(store.Ledger(self.db).undone_steps(cid)), 1)   # ready is left for the next publish

    def test_a_refused_write_spends_the_approval(self):
        cid = publish.card(self.db, Change("genie", "fork", pr=5), F, HEAD, PR, TEXTS)
        publish.approve(self.db, "genie", HEAD[:7])
        observe.transport = Fake(refuse="/issues/5/comments")
        publish.publish(self.db, cid, F, "/nowhere")
        self.assertTrue(self.db.execute("SELECT spent_why FROM approval WHERE card=?", (cid,)).fetchone()[0].startswith("refused: POST"))


if __name__ == "__main__":
    unittest.main()
