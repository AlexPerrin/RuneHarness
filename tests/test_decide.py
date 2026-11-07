"""decide.plan over a hand-built ledger: one class per PRD group it touches."""
import json
import sys
import tempfile
import unittest
from unittest import mock
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
        cols = {**dict(change="h-one", role="dev", mode="code", input=input, brief="b", listed_at="t"), **kw}
        self.db.execute(f"INSERT INTO run({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))


class Tempo(Base):  # T1, T3, T4
    def test_new_change_lists_one_dev_run_until_a_run_exists_with_that_input(self):
        s = self.step()
        self.assertEqual((s.kind, s.role, s.mode, s.why), ("run", "dev", "code", "new"))
        self.run_row(s.input, ended_at="t", end_kind="stop")
        self.assertEqual(self.step().kind, "wait")

    def test_a_run_stopped_once_started_gets_a_successor(self):   # a wedged run did not do the work; a withdrawn listing above stays parked
        s = self.step()
        self.run_row(s.input, started_at="t", ended_at="t", end_kind="stop")
        self.assertEqual(self.step().kind, "run")

    def test_a_live_run_blocks_the_change(self):
        self.run_row("x")
        self.assertIn("run 1 dev", self.step().why)

    def test_successor_after_console_death_or_handoff(self):   # for every run kind: the rule is the plan's, not a guard's
        s = self.step()
        self.run_row(s.input, ended_at="t", end_kind="handoff")
        self.assertEqual(self.step().kind, "run")
        self.run_row(s.input, ended_at="t", end_kind="console", role="qa", mode="criteria")
        self.assertEqual(self.step().kind, "run")
        self.run_row(s.input, ended_at="t", end_kind="handback", record="run 3: submitted x")
        self.assertIn("ended (handback) with this input", self.step().why)

    def test_a_dep_landing_after_a_failed_verdict_rejudges_the_same_head_once(self):   # the failure was the dep's: a dev can only resubmit it
        ch = Change("h-one", "harness", priority="P2", deps=["h-dep"])
        self.submit()
        self.run_row("i1", ended_at="t", end_kind="stop"); self.run_row("i2", ended_at="t", end_kind="stop")
        self.db.execute("INSERT INTO verdict(change, head, run, ok, criteria_digest, at) VALUES ('h-one', ?, 1, 0, 'd', '2')", (TIP,))
        C = mock.Mock(L=self.L)
        v = self.L.last_verdict("h-one", TIP)
        self.assertFalse(decide.outdated(C, ch, v))
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-dep', 'refs/heads/v9', 's', '3')")
        self.assertTrue(decide.outdated(C, ch, v))
        self.db.execute("INSERT INTO verdict(change, head, run, ok, criteria_digest, at) VALUES ('h-one', ?, 2, 0, 'd', '4')", (TIP,))
        self.assertFalse(decide.outdated(C, ch, self.L.last_verdict("h-one", TIP)))   # judged again and failed: a dev's now

    def test_a_fork_only_change_on_a_track_without_staging_is_done_by_its_verdict(self):   # central-rights-test-mod: nothing to land on
        C = Track("central", "x/c", "/nowhere", "refs/remotes/origin/main", "Up/c", "dev", {"build": "c-1", "gate": "c-1"}, "fork")
        cfg = Cfg(agents=2, tracks={"fork": F, "central": C})
        lib = Change("c-fix", "central", upstream=False); ch = Change("s-one", "fork", deps=("c-fix",))
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('central', 'refs/remotes/fork/dev/c-fix', 'h1')")
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('c-fix', 'h1', 't1', 'h1', 't')")
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES ('c-fix', 'qa', 'judge', 'i', 'b', 't')")
        self.db.execute("INSERT INTO verdict(change, head, run, ok, criteria_digest, at) VALUES ('c-fix', 'h1', 1, 1, 'd', 't')")
        steps = {a.change: a.step for a in decide.plan(self.L, [ch, lib], cfg)}
        self.assertEqual(steps["c-fix"].kind, "done")
        self.assertNotIn("dep c-fix", steps["s-one"].why)      # its dependent is not held by it

    def test_a_client_changes_server_dep_must_be_live_on_the_test_server(self):   # the mobile reaches only the live stack
        cfg = Cfg(agents=2, tracks={"fork": F, "client": Track("client", "x/c", "/nowhere", "refs/remotes/origin/main", "", "client", {"gate": "client-1"}, "origin")})
        srv = Change("s-fix", "fork", upstream=False); ch = Change("c-one", "client", deps=("s-fix",))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('s-fix', 'h1', 't1', 'h1', 't')")
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('s-fix', 'refs/heads/staging', 's1', 't')")
        self.assertEqual({a.change: a.step for a in decide.plan(self.L, [ch, srv], cfg)}["c-one"].why, "dep s-fix not live on the test server")
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('s-fix', 'live', 'tr', 't')")
        self.assertEqual({a.change: a.step for a in decide.plan(self.L, [ch, srv], cfg)}["c-one"].kind, "run")

    def test_a_client_change_waits_for_its_server_deps_own_deps_live(self):   # run 185: its dep ran live without the dep's dep
        cfg = Cfg(agents=2, tracks={"fork": F, "client": Track("client", "x/c", "/nowhere", "refs/remotes/origin/main", "", "client", {"gate": "client-1"}, "origin")})
        base = Change("s-base", "fork", upstream=False); srv = Change("s-fix", "fork", upstream=False, deps=("s-base",))
        ch = Change("c-one", "client", deps=("s-fix",))
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('s-fix', 'live', 'tr', 't')")
        step = lambda: {a.change: a.step for a in decide.plan(self.L, [ch, srv, base], cfg)}["c-one"]
        self.assertEqual(step().why, "dep s-base not live on the test server")
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('s-base', 'live', 'tr', 't')")
        s1 = step()
        self.assertEqual(s1.kind, "run")
        self.db.execute("DELETE FROM landed WHERE change='s-base'")
        self.assertNotEqual(decide.dev_due(decide.Ctx(self.L, cfg, {c.slug: c for c in (ch, srv, base)}), ch).input, s1.input)   # the dep's dep landing re-runs a parked dev

    def test_a_dep_on_another_track_waits_for_its_landing_not_its_submission(self):
        dep = Change("h-fix", "harness")
        ch = Change("c-one", "client", deps=("h-fix",))
        cfg = Cfg(agents=2, tracks={"harness": T, "client": Track("client", "x/c", "/nowhere", "refs/remotes/origin/main", "", "client", {"gate": "client-1"}, "origin")})
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('h-fix', 'd1', 'td', 'cd', 't')")
        s = {a.change: a.step for a in decide.plan(self.L, [ch, dep], cfg)}["c-one"]
        self.assertEqual((s.kind, s.why), ("wait", "dep h-fix (harness) not landed"))
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-fix', 'refs/heads/v9', 'd1', 't')")
        self.assertEqual({a.change: a.step for a in decide.plan(self.L, [ch, dep], cfg)}["c-one"].kind, "run")

    def test_a_dep_landing_is_a_new_input_for_the_dev(self):   # a dev that filed its blocker runs again once the blocker lands
        dep = Change("h-dep", "harness")
        ch = Change("h-one", "harness", deps=("h-dep",))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('h-dep', 'd1', 'td', 'cd', 't')")
        s1 = {a.change: a.step for a in decide.plan(self.L, [ch, dep], CFG)}["h-one"]
        self.run_row(s1.input, ended_at="t", end_kind="handback", record="run 1: filed h-dep")
        self.assertIn("ended (handback)", {a.change: a.step for a in decide.plan(self.L, [ch, dep], CFG)}["h-one"].why)
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-dep', 'refs/heads/v9', 'd1', 't')")
        s2 = {a.change: a.step for a in decide.plan(self.L, [ch, dep], CFG)}["h-one"]
        self.assertEqual(s2.kind, "run"); self.assertNotEqual(s1.input, s2.input)

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
            self.db.execute("INSERT INTO attempt(kind, key, cause, at) VALUES ('gate', ?, 'oom', 't1')", (f"{TREE}:harness-1",))
        self.assertIn("3 starts", self.step().why)
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('ship', 'refs/heads/v9:fix', 1, 't2')")   # a harness fix shipped
        self.assertEqual(self.step().kind, "gate")

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

    def test_a_head_merges_into_staging_after_its_deps(self):   # staging runs the head, not the candidate that carried the dep
        dep = Change("base", "fork")
        self.ch = Change("genie", "fork", deps=("base",))
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.submit()
        for k in ("build", "gate"):
            self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES (?, ?, 1, 't')", (k, f"{TREE}:fork-1"))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('base', 'd1', 'td', 'd1', 't')")
        step = lambda: {a.change: a.step for a in decide.plan(self.L, [self.ch, dep], CFG)}["genie"]
        self.assertEqual(step().why, "dep base not yet on staging")
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('base', 'refs/heads/staging', 's', 't')")
        self.assertEqual(step().kind, "merge")

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
        self.assertEqual(self.step().key, f"{TREE}_c{'c' * 12}:fork-1")

    def test_merge_conflict_lists_the_dev(self):
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.submit()
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('fork', 'refs/heads/staging', 'aaaaaaa1')")
        self.db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t', 'merge-conflict', 'genie', ?)", (TIP[:7] + " aaaaaaa content/x.kt",))
        self.assertIn("merge conflict", self.step().why)

    def test_a_conflict_is_merged_again_once_staging_moves(self):   # alert 45: a reverted pin let the head merge
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('genie','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.submit()
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('fork', 'refs/heads/staging', 'bbbbbbb2')")
        self.db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t', 'merge-conflict', 'genie', ?)", (TIP[:7] + " aaaaaaa content/x.kt",))
        self.assertNotEqual(self.step().role, "dev")

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

    def test_a_track_without_deploy_skips_staging_and_its_conflict(self):   # staging exists only to deploy
        lab = Track("lab", "AlexPerrin/lab", "/nowhere", "refs/remotes/origin/main", "Up/lab", "dev", {"gate": "lab-1"}, "fork")
        cfg = Cfg(agents=2, hold="P2", tracks={**CFG.tracks, "lab": lab})
        ch = Change("hello", "lab")
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at, ended_at, end_kind, record) VALUES ('hello','qa','criteria','x','b','t','t','handback','run 1: criteria agreed')")
        self.db.execute("INSERT INTO ref(repo, name, sha) VALUES ('lab', 'refs/remotes/fork/dev/hello', ?)", (TIP,))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('hello', ?, ?, ?, 't1')", (TIP, TREE, TC))
        self.db.execute("INSERT INTO job(kind, key, ok, ended_at) VALUES ('gate', ?, 1, 't')", (f"{TREE}:lab-1",))
        self.db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t', 'merge-conflict', 'hello', ?)", (TIP[:7] + " README.md",))
        step = lambda: {a.change: a.step for a in decide.plan(self.L, [ch], cfg)}["hello"]
        self.assertEqual(step().why, "texts: pr-title.txt, pr-body.md, pr-comment.md")
        for n in ("pr-title.txt", "pr-body.md", "pr-comment.md"):
            self.db.execute("INSERT INTO text(change, name, sha, body) VALUES ('hello', ?, 'x', 'text')", (n,))
        self.assertEqual(step().kind, "card")


class Goals(Base):  # T8
    def test_measure_when_the_target_tree_moves_then_a_plan_run_when_below_target(self):
        g = Goal("server-content", "fork", 100, "query")
        self.assertEqual(decide.plan(self.L, [], CFG, [g]), [])   # no staging yet: nothing to measure
        self.db.execute("INSERT INTO ref(repo, name, sha, tree) VALUES ('fork', 'refs/heads/staging', 's1', 'tr1')")
        a = [x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"]
        self.assertEqual((a[0].step.kind, a[0].step.key), ("measure", "tr1:query"))
        for _ in range(3):
            self.db.execute("INSERT INTO attempt(kind, key, cause, at) VALUES ('measure', 'tr1:query', 'boom', 't')")
        a = [x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"]
        self.assertIn("3 starts", a[0].step.why)   # parked like any job
        self.db.execute("DELETE FROM attempt")
        self.db.execute("INSERT INTO measure(goal, tree, value, at) VALUES ('server-content', 'tr1', 38, 't')")
        a = [x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"]
        self.assertEqual((a[0].step.kind, a[0].step.mode), ("run", "plan"))
        ch = Change("quest-x", "fork", goal="server-content")
        self.assertEqual([x for x in decide.plan(self.L, [ch], CFG, [g]) if x.change == "goal:server-content"], [])  # something open names it
        self.db.execute("UPDATE measure SET value=100")
        self.assertEqual([x for x in decide.plan(self.L, [], CFG, [g]) if x.change == "goal:server-content"], [])   # at target


class Snapshots(unittest.TestCase):  # the recorded ledger with the definitions then (tests/fixtures/ledger-<n>.db, defs-<n>/): the pass plans what was recorded (ledger-<n>.plan)
    def test_plan_over_each_recorded_ledger(self):
        import glob
        import shutil
        import subprocess
        root = Path(__file__).resolve().parents[1]
        for f in glob.glob(str(root / "tests" / "fixtures" / "*.db")):
            with tempfile.TemporaryDirectory() as d:
                copy = Path(d) / "hd.db"
                shutil.copy(f, copy)
                defs = f[:-3].replace("ledger-", "defs-")
                out = subprocess.run([sys.executable, str(root / "harness" / "hd.py"), "tick", "--dry-run", "--offline", "--db", str(copy), "--defs", defs],
                                     capture_output=True, text=True)
                self.assertEqual(out.stdout, Path(f[:-3] + ".plan").read_text(), out.stderr)


class Retention(Base):  # H7: an artifact lives while an owner fact holds; the step that falsifies it releases it
    def released(self, ch=None, cfg=CFG):
        return [a.step.key for a in decide.plan(self.L, [ch or self.ch], cfg) if a.step.kind == "release"]

    def own(self, kind, key, owner):
        store.own(self.db, kind, key, owner)

    def test_a_new_head_releases_the_old_trees_artifacts_unless_a_run_or_card_names_them(self):
        self.submit()
        self.own("image", f"or:{TREE}", f"h-one@{TREE}")
        self.assertEqual(self.released(), [])   # the current head's
        self.db.execute("UPDATE ref SET sha='e' WHERE repo='harness'")
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('h-one', 'e', 'f', 'e', 't2')")
        self.run_row("x")
        self.assertEqual(self.released(), [])   # a live run of the change may still use it
        self.db.execute("UPDATE run SET ended_at='t', end_kind='handback'")
        self.db.execute("INSERT INTO card(change, head, steps_json, texts_json, digest) VALUES ('h-one', ?, '[]', '{}', 'd')", (TIP,))
        self.assertEqual(self.released(), [])   # the latest card names it
        self.db.execute("DELETE FROM card")
        self.assertEqual(self.released(), [f"image:or:{TREE}"])

    def test_close_merge_and_withdraw_release_the_changes_clones(self):
        self.own("worktree", "/r/.worktrees/h-one", "h-one")
        self.assertEqual(self.released(), [])
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('h-one', 'refs/heads/v9', 'd', 't')")   # merged: done
        self.assertEqual(self.released(), ["worktree:/r/.worktrees/h-one"])
        self.db.execute("DELETE FROM landed"); self.db.execute("INSERT INTO change_state(slug, closed_at) VALUES ('h-one', 't')")
        self.assertEqual(self.released(), ["worktree:/r/.worktrees/h-one"])
        self.db.execute("DELETE FROM change_state")
        self.assertEqual([a.step.key for a in decide.plan(self.L, [], CFG)], ["worktree:/r/.worktrees/h-one"])   # its definition withdrawn

    def test_a_jobs_container_goes_when_the_job_ends_a_kill_included(self):
        self.own("container", "build-h-one", "job:build:k")
        self.db.execute("INSERT INTO job(kind, key, pid, pid_start, started_at) VALUES ('build', 'k', 1, 1, 't')")
        self.assertEqual(self.released(), [])
        self.db.execute("UPDATE job SET pid=NULL, ended_at='t'")   # observe.procs: the pid gone
        self.assertEqual(self.released(), ["container:build-h-one"])

    def test_an_artifact_goes_only_when_every_owner_is_gone(self):
        self.submit()
        self.own("image", f"or:{TREE}", "other@x"); self.own("image", f"or:{TREE}", f"h-one@{TREE}")
        self.assertEqual(self.released(), [])
        self.own("image", "osrs-openrune:s1", "staging@s1")
        self.own("image", "or:s1_cabc", "staging@s1_cabc")   # a deploy's T with a Central built in: the job key and the ref name the plain tree
        self.db.execute("INSERT INTO ref(repo, name, sha, tree) VALUES ('fork', 'refs/heads/staging', 'x', 's1')")
        self.assertEqual(self.released(), [])   # staging's tree
        self.db.execute("UPDATE ref SET tree='s2' WHERE name='refs/heads/staging'")
        self.assertEqual(sorted(self.released()), ["image:or:s1_cabc", "image:osrs-openrune:s1"])

    def test_below_the_disk_level_no_build_starts(self):
        self.submit()
        self.db.execute("INSERT INTO disk(path, free, at) VALUES ('/mnt/c', ?, 't')", (40 * 10**9,))
        self.assertEqual(self.step().kind, "gate")   # no level set
        cfg = Cfg(agents=2, hold="P2", tracks=CFG.tracks, free=50)
        s = {a.change: a.step for a in decide.plan(self.L, [self.ch], cfg)}["h-one"]
        self.assertEqual(s.kind, "wait"); self.assertIn("disk: /mnt/c 40 GB free, below 50 GB", s.why)


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

    def test_a_library_dep_holds_a_card_never_a_ship(self):   # G4: h-central-up-sign-in sat gated behind an upstream merge
        lib, ship = Change("c-lib", "central"), Change("h-one", "harness", deps=("c-lib",))
        cfg = Cfg(agents=2, hold="P2", tracks={**CFG.tracks, "central": Track("central", "o/c", "/c", "refs/remotes/origin/main", "o/c")})
        C = decide.Ctx(self.L, cfg, {c.slug: c for c in (lib, ship)})
        self.assertIsNone(decide.upstream_dep_wait(C, ship))
        self.assertIn("not yet landed", decide.upstream_dep_wait(C, Change("c-two", "central", deps=("c-lib",))).why)


if __name__ == "__main__":
    unittest.main()
