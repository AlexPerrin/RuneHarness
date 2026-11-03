"""decide.plan over a hand-built ledger: one class per PRD group it touches."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import decide  # noqa: E402
import store  # noqa: E402
from decide import Cfg, Change, Goal, Track  # noqa: E402

T = Track("harness", "AlexPerrin/osrs-harness", "/nowhere", "refs/heads/v9", "", "harness", {"gate": "harness-1", "ship": "harness-1"})
F = Track("fork", "AlexPerrin/OpenRune-Server", "/nowhere", "refs/remotes/origin/main", "OpenRune/OpenRune-Server", "dev",
          {"build": "fork-1", "gate": "fork-1", "deploy": "fork-1"}, "fork")
CFG = Cfg(agents=2, hold="P2", tracks={"harness": T, "fork": F})
TIP, TREE, TC = "a" * 40, "b" * 40, "c" * 40


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = store.connect(str(Path(self.dir.name) / "hd.db"))
        self.L = store.Ledger(self.db)
        self.ch = Change("h-one", "harness", priority="P2")

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def step(self, ch=None):
        return {a.change: a.step for a in decide.plan(self.L, [ch or self.ch], CFG)}[(ch or self.ch).slug]

    def submit(self):
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('harness', 'refs/heads/harness/h-one', ?)", (TIP,))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('h-one', ?, ?, ?, 't1')", (TIP, TREE, TC))

    def run_row(self, input, **kw):
        cols = dict(change="h-one", role="dev", mode="code", input=input, brief="b", listed_at="t", **kw)
        self.db.execute(f"INSERT INTO run({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))


class Tempo(Base):  # T1, T3, T4
    def test_new_change_lists_one_dev_run_until_a_run_exists_with_that_input(self):
        s = self.step()
        self.assertEqual((s.kind, s.role, s.mode, s.why), ("run", "dev", "code", "new"))
        self.run_row(s.input, ended_at="t", end_kind="stop")
        self.assertEqual(self.step().kind, "wait")

    def test_a_live_run_blocks_the_change(self):
        self.run_row("x")
        self.assertIn("run 1 dev", self.step().why)

    def test_successor_after_console_death_or_handoff(self):
        s = self.step()
        self.run_row(s.input, ended_at="t", end_kind="handoff")
        s2 = self.step()
        self.assertEqual(s2.kind, "run")
        self.assertNotEqual(s.input, s2.input)

    def test_agent_count_and_held_band(self):
        other = [Change(f"h-{i}", "harness") for i in range(3)]
        actions = decide.plan(self.L, other, CFG)
        self.assertEqual([a.step.kind for a in actions], ["run", "run", "wait"])
        held = Change("c-x", "client", priority="P3")
        cfg = Cfg(agents=2, hold="P2", tracks={"harness": T, "client": T})
        self.assertEqual(decide.plan(self.L, [held], cfg), [])
        self.assertEqual(decide.priority(Change("h-x", "harness", priority="P3"), {}), "P1")
        self.assertEqual(decide.priority(Change("a", "client", priority="P3"), {"a": [Change("b", "client", priority="P0")]}), "P0")


class Gate(Base):  # G2, G3, H2
    def test_submission_gates_the_candidate_once(self):
        self.submit()
        s = self.step()
        self.assertEqual((s.kind, s.key), ("gate", f"{TREE}:harness-1"))
        self.db.execute("INSERT INTO job(kind, key, pid, pid_start, started_at) VALUES ('gate', ?, 1, 1, 't')", (s.key,))
        self.assertEqual(self.step().kind, "wait")

    def test_gate_failure_lists_the_dev(self):
        self.submit()
        self.db.execute("INSERT INTO job(kind, key, ok, detail, ended_at) VALUES ('gate', ?, 0, 'tests (1 failed)', 't')", (f"{TREE}:harness-1",))
        s = self.step()
        self.assertEqual((s.kind, s.role), ("run", "dev"))
        self.assertIn("gate failed: tests", s.why)

    def test_three_starts_without_result_park_the_job(self):
        self.submit()
        for _ in range(3):
            self.db.execute("INSERT INTO attempt(kind, key, cause, at) VALUES ('gate', ?, 'oom', 't')", (f"{TREE}:harness-1",))
        self.assertIn("3 starts", self.step().why)

    def test_criteria_added_after_submission_list_the_dev(self):
        self.submit()
        self.db.execute("INSERT INTO criterion(change, rid, kind, text, source, created_at) VALUES ('h-one', 'x', 'judge', 't', 'user', 't2')")
        self.assertIn("criteria added", self.step().why)
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-one', 'refs/heads/v9', 'd', 't')")
        self.assertEqual(self.step().kind, "done")   # landed is done, whatever is seeded later


class Hands(Base):  # H6
    def test_gated_change_ships_then_waits_for_landed(self):
        self.submit()
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('gate', ?, 1, 't')", (f"{TREE}:harness-1",))
        s = self.step()
        self.assertEqual((s.kind, s.key), ("ship", f"refs/heads/v9:{TC}"))
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('ship', ?, 1, 't')", (s.key,))
        self.assertIn("not yet landed", self.step().why)
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-one', 'refs/heads/v9', 'd', 't')")
        self.assertEqual(self.step().kind, "done")

    def test_one_ship_per_branch(self):
        self.submit()
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('gate', ?, 1, 't')", (f"{TREE}:harness-1",))
        self.db.execute("INSERT INTO job(kind, key, pid, pid_start, started_at) VALUES ('ship', 'refs/heads/v9:other', 1, 1, 't')")
        self.assertIn("ship of this branch is running", self.step().why)


class Server(Base):  # G1, H4: criteria before code, the staging merge, one deploy per staging tree
    def setUp(self):
        super().setUp()
        self.ch = Change("genie", "fork")

    def submit(self):
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('fork', 'refs/remotes/fork/dev/genie', ?)", (TIP,))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('genie', ?, ?, ?, 't1')", (TIP, TREE, TC))

    def test_criteria_run_first_then_dev_then_build_gate_judge_merge(self):
        s = self.step()
        self.assertEqual((s.kind, s.role, s.mode), ("run", "qa", "criteria"))
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.assertEqual((self.step().kind, self.step().role), ("run", "dev"))
        self.submit()
        self.assertEqual(self.step().kind, "build")
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('build', ?, 1, 't')", (f"{TREE}:fork-1",))
        self.assertEqual(self.step().kind, "gate")
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('gate', ?, 1, 't')", (f"{TREE}:fork-1",))
        self.db.execute("INSERT INTO criterion(change, rid, kind, text, source, created_at) VALUES ('genie', 'acc-1', 'judge', 'r', 'seed', 't0')")
        s = self.step()
        self.assertEqual((s.kind, s.mode), ("run", "judge"))
        d = store.digest([("acc-1", "r")])
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind) VALUES ('genie','qa','judge','j','b','t','t','handback')")
        self.db.execute("INSERT INTO verdict(change, head, run, ok, criteria_digest, at) VALUES ('genie', ?, 2, 1, ?, 't')", (TIP, d))
        s = self.step()
        self.assertEqual((s.kind, s.key), ("merge", f"staging:{TIP}"))
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('genie', 'refs/heads/staging', 's', 't')")
        self.assertEqual(self.step().why, "texts: pr-title.txt, pr-body.md, pr-comment.md")
        for n in ("pr-title.txt", "pr-body.md", "pr-comment.md"):
            self.db.execute("INSERT INTO text(change, name, sha, body) VALUES ('genie', ?, 'x', 'text')", (n,))
        self.assertEqual(self.step().kind, "card")
        self.db.execute("INSERT INTO card(change, head, steps_json, texts_json, digest) VALUES ('genie', ?, '[{\"name\":\"push\"}]', '{}', 'd')", (TIP,))
        self.assertIn("the user: card 1", self.step().why)
        self.db.execute("INSERT INTO hold(change, head, at) VALUES ('genie', ?, 't')", (TIP,))
        self.assertIn("held", self.step().why)
        self.db.execute("UPDATE hold SET lifted_at='t'")
        self.db.execute("INSERT INTO approval(card, at) VALUES (1, 't')")
        self.db.execute("INSERT INTO publish_step(card, n, name) VALUES (1, 1, 'push')")
        self.assertEqual((self.step().kind, self.step().key), ("publish", "1"))
        self.db.execute("UPDATE publish_step SET done_at='t'")
        self.db.execute("UPDATE approval SET spent_at='t', spent_why='published'")
        self.assertEqual(self.step().why, "maintainers")
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('genie', 'refs/remotes/origin/main', 'm', 't')")
        self.assertEqual(self.step().kind, "done")

    def test_a_finding_needs_a_reply_before_a_new_card(self):
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.submit()
        for k in ("build", "gate"):
            self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES (?, ?, 1, 't')", (k, f"{TREE}:fork-1"))
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('genie', 'refs/heads/staging', 's', 't')")
        for n in ("pr-title.txt", "pr-body.md", "pr-comment.md"):
            self.db.execute("INSERT INTO text(change, name, sha, body) VALUES ('genie', ?, 'x', 'text')", (n,))
        self.db.execute("INSERT INTO finding(comment_id, pr, author, body, triage, change) VALUES (77, 5, 'm', 'why?', 'finding', 'genie')")
        self.assertEqual(self.step().why, "texts: pr-reply-77.md")
        self.db.execute("INSERT INTO text(change, name, sha, body) VALUES ('genie', 'pr-reply-77.md', 'x', '> why?\n\n@m because')")
        self.assertEqual(self.step().kind, "card")

    def test_a_composite_candidate_is_keyed_by_the_library_tree_too(self):
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('fork', 'refs/remotes/fork/dev/genie', ?)", (TIP,))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, composite_json, at) VALUES ('genie', ?, ?, ?, ?, 't1')",
                        (TIP, TREE, TC, json.dumps({"central": {"head": "h", "tree": "c" * 40}})))
        self.assertEqual(self.step().key, f"{TREE}+c{'c' * 12}:fork-1")

    def test_merge_conflict_lists_the_dev(self):
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.submit()
        self.db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t', 'merge-conflict', 'genie', ?)", (TIP[:7] + " content/x.kt",))
        self.assertIn("merge conflict", self.step().why)

    def test_a_job_that_failed_is_not_relaunched(self):
        self.db.execute("INSERT INTO ref(repo, name, sha, tree) VALUES ('fork', 'refs/heads/staging', 's1', 'tr1')")
        self.db.execute("INSERT INTO job(kind, key, ok, detail, ended_at) VALUES ('deploy', 'tr1:fork-1', 0, 'port in use', 't')")
        self.assertEqual([x for x in decide.plan(self.L, [], CFG) if x.change == "fork:staging"], [])

    def test_one_deploy_per_staging_tree(self):
        self.db.execute("INSERT INTO ref(repo, name, sha, tree) VALUES ('fork', 'refs/heads/staging', 's1', 'tr1')")
        a = [x for x in decide.plan(self.L, [], CFG) if x.change == "fork:staging"]
        self.assertEqual((a[0].step.kind, a[0].step.key), ("deploy", "tr1:fork-1"))
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('deploy', 'tr1:fork-1', 1, 't')")
        self.assertEqual([x for x in decide.plan(self.L, [], CFG) if x.change == "fork:staging"], [])


class Goals(Base):  # T8
    def test_measure_when_the_target_tree_moves_then_a_plan_run_when_below_target(self):
        g = Goal("server-content", "fork", 100, "query")
        self.assertEqual(decide.plan(self.L, [], CFG, [g]), [])   # no staging yet: nothing to measure
        self.db.execute("INSERT INTO ref(repo, name, sha, tree) VALUES ('fork', 'refs/heads/staging', 's1', 'tr1')")
        a = [x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"]
        self.assertEqual((a[0].step.kind, a[0].step.key), ("measure", "tr1:query"))
        self.db.execute("INSERT INTO measure(goal, tree, value, at) VALUES ('server-content', 'tr1', 38, 't')")
        a = [x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"]
        self.assertEqual((a[0].step.kind, a[0].step.mode), ("run", "plan"))
        ch = Change("quest-x", "fork", goal="server-content")
        self.assertEqual([x for x in decide.plan(self.L, [ch], CFG, [g]) if x.change == "goal:server-content"], [])  # something open names it
        self.db.execute("UPDATE measure SET value=100")
        self.assertEqual([x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"], [])   # at target


class Snapshots(unittest.TestCase):  # the recorded ledger: the pass plans over it what was recorded (tests/fixtures/<n>.plan)
    def test_plan_over_each_recorded_ledger(self):
        import glob
        import shutil
        import subprocess
        root = Path(__file__).resolve().parents[1]
        for f in glob.glob(str(root / "tests" / "fixtures" / "*.db")):
            with tempfile.TemporaryDirectory() as d:
                copy = Path(d) / "hd.db"
                shutil.copy(f, copy)
                out = subprocess.run([sys.executable, str(root / "harness" / "hd.py"), "tick", "--dry-run", "--offline", "--db", str(copy)],
                                     capture_output=True, text=True)
                self.assertEqual(out.stdout, Path(f[:-3] + ".plan").read_text(), out.stderr)


class Authority(Base):  # A2 (close), A4 (ask)
    def test_closed_is_done_and_open_ask_waits(self):
        self.db.execute("INSERT INTO change_state(slug, closed_at) VALUES ('h-one', 't')")
        self.assertEqual(decide.plan(self.L, [self.ch], CFG), [])
        self.db.execute("DELETE FROM change_state")
        self.db.execute("INSERT INTO ask(change, text, options_json, at) VALUES ('h-one', 'which?', '[]', 't')")
        self.assertIn("question", self.step().why)

    def test_dep_waits_until_landed(self):
        dep = Change("h-dep", "harness")
        ch = Change("h-one", "harness", deps=("h-dep",))
        steps = {a.change: a.step for a in decide.plan(self.L, [ch, dep], CFG)}
        self.assertEqual(steps["h-one"].why, "dep h-dep")
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-dep', 'refs/heads/v9', 'd', 't')")
        steps = {a.change: a.step for a in decide.plan(self.L, [ch, dep], CFG)}
        self.assertEqual(steps["h-one"].kind, "run")


if __name__ == "__main__":
    unittest.main()
