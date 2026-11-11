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

    def test_one_answer_takes_several_options(self):   # "waive both": the second waiver was lost to a one-option answer
        for rid in ("acc-4", "done-stack"):
            hd.main(["criterion", "add", "x", rid, "--kind", "judge", "--text", "t", "--source", "seed"])
        hd.main(["ask", "x", "waive?", "--option", "a:acc-4 later:waive acc-4", "--option", "d:done-stack later:waive done-stack"])
        with self.assertRaises(SystemExit):
            hd.main(["answer", "x", "a,z"])
        hd.main(["answer", "x", "a,d", "waive both"])
        db = store.connect()
        self.assertEqual([r[0] for r in db.execute("SELECT waived FROM criterion ORDER BY id")], [1, 1])

    def test_a_user_act_names_its_act_and_its_answer_is_recorded(self):   # A4
        with self.assertRaises(SystemExit):
            hd.main(["ask", "x", "pin?", "--option", "a:pin it:user-act"])
        hd.main(["ask", "x", "pin the fork?", "--option", "a:pin it:user-act push fork tools pin"])
        hd.main(["answer", "x", "a", "pushed"])
        self.assertEqual(store.connect().execute("SELECT option, words FROM answer").fetchone()[1], "pushed")

    def test_only_the_users_answer_bundles_changes_into_a_feature(self):   # the user decides every bundle
        import os
        self.addCleanup(setattr, hd, "CHANGES", hd.CHANGES); hd.CHANGES = self.dir.name
        for s in ("a", "b"):
            hd.write_change(s, {"slug": s, "track": "fork"}, f"# {s}\n")
        hd.main(["ask", "a", "one PR for friends?", "--option", "y:bundle:feature feat/friends a b", "--option", "n:no:user-act keep apart"])
        hd.main(["answer", "a", "y"])
        self.assertEqual([hd.read_change(s)[0]["feature"] for s in ("a", "b")], ["feat/friends"] * 2)
        self.assertTrue(os.path.exists(os.path.join(self.dir.name, "a.md")))

    def test_new_on_an_existing_change_makes_it_block_the_named_change(self):   # alert 95: --on returned before --blocks
        self.addCleanup(setattr, hd, "CHANGES", hd.CHANGES); hd.CHANGES = self.dir.name
        for s in ("open", "mine"):
            hd.write_change(s, {"slug": s, "track": "fork"}, f"# {s}\n")
        hd.main(["new", "x", "--track", "fork", "--title", "limit", "--body", "b", "--on", "open", "--blocks", "mine"])
        self.assertEqual(hd.read_change("mine")[0]["deps"], ["open"])
        self.assertIn("## limit", hd.read_change("open")[1])

    def test_a_finding_files_a_change_of_the_prs_feature(self):   # a maintainer's word lands on staging, then the PR repackages
        from decide import Change
        self.addCleanup(setattr, hd, "CHANGES", hd.CHANGES); hd.CHANGES = self.dir.name
        self.addCleanup(setattr, hd, "change", hd.change)
        hd.change = {"pr-feat-x-fork": Change("pr-feat-x-fork", "fork", feature="feat/x", members=("m",))}.get
        db = store.connect()
        db.execute("INSERT INTO finding(comment_id, pr, author, body, change) VALUES (77, 5, 'mx', 'why?', 'pr-feat-x-fork')")
        hd.main(["triage", "77", "finding"])
        fm, _ = hd.read_change("fork-5-c77")
        self.assertEqual((fm["track"], fm["feature"]), ("fork", "feat/x"))
        self.assertEqual(db.execute("SELECT change FROM criterion").fetchone()[0], "fork-5-c77")
        self.assertEqual(db.execute("SELECT change, triage FROM finding").fetchone()[:], ("pr-feat-x-fork", "finding"))   # the package's dev replies

    def test_package_applies_each_member_commit_once_onto_upstream_main(self):
        import os, subprocess
        from decide import Change, Cfg, Track
        repo = os.path.join(self.dir.name, "fork")
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        def git(*a, cwd=repo): return subprocess.run(["git", "-C", cwd, *a], check=True, env=env, capture_output=True, text=True).stdout.strip()
        def commit(f, branch, start="main"):
            git("checkout", "-q", "-B", branch, start); Path(repo, f).write_text(f); git("add", f); git("commit", "-qm", f"feat: {f}")
            return git("rev-parse", "HEAD")
        os.makedirs(repo); git("init", "-q", "-b", "main"); git("config", "user.name", "t"); git("config", "user.email", "t@t")
        Path(repo, "base").write_text("base"); git("add", "base"); git("commit", "-qm", "base")
        pin = commit("pin", "local/pin")
        a = commit("a", "dev/a", "local/pin")   # a member branch carrying a pin under it
        b = commit("b", "dev/b", "dev/a")
        git("checkout", "-q", "main")
        for r in ("refs/remotes/fork/local/pin", "refs/remotes/origin/main"):
            git("update-ref", r, pin if "pin" in r else "main")
        T = Track("fork", "x/y", repo, "refs/remotes/origin/main", "o/y", remote="fork", pins=(("local/pin", ""),))
        defs = [Change("a", "fork", feature="feat/x"), Change("b", "fork", feature="feat/x", deps=("a",))]
        P = hd.decide.packages(defs, {"fork": T})[0]
        self.addCleanup(setattr, hd, "change", hd.change); hd.change = {c.slug: c for c in defs + [P]}.get
        self.addCleanup(setattr, hd.act, "cfg", hd.act.cfg); hd.act.cfg = lambda: Cfg(tracks={"fork": T})
        db = store.connect()
        for s, h in (("a", a), ("b", b)):
            db.execute("INSERT INTO ref(repo, name, sha) VALUES ('fork', ?, ?)", (f"refs/remotes/fork/dev/{s}", h))
        hd.main(["package", P.slug])
        clone = os.path.join(repo, ".worktrees", P.slug)
        self.assertEqual(git("log", "--format=%s", "refs/remotes/origin/main..HEAD", cwd=clone).split("\n"), ["feat: b", "feat: a"])   # no pin, member order, not squashed
        hd.main(["package", P.slug])   # again: nothing applied twice
        self.assertEqual(len(git("log", "--format=%s", "refs/remotes/origin/main..HEAD", cwd=clone).split("\n")), 2)

    def test_a_bare_reply_from_an_old_ask_records_the_answer(self):   # ask 2: options carried from v8 with effect 'reply' and no comment id
        db = store.connect()
        db.execute("INSERT INTO ask(change, text, options_json, at) VALUES ('x', 'how?', ?, 't')", (json.dumps([{"id": "a", "text": "fork-only", "effect": "reply"}]),))
        hd.main(["answer", "x", "a", "fork-only"])
        self.assertEqual(db.execute("SELECT option, words FROM answer").fetchone()[1], "fork-only")

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
        defs = {"c": Change("c", "central", deps=("fork", "up")), "fork": Change("fork", "central"), "up": Change("up", "central")}
        self.addCleanup(setattr, hd, "change", hd.change); hd.change = defs.get
        db = store.connect()
        db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('fork', ?, 't', 't', 't'), ('up', ?, 't', 't', 't')", (fork_only, merged))
        db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('fork', 'refs/heads/staging', ?, 't')", (fork_only,))
        self.assertEqual(hd.dep_inputs(db, cfg, defs["c"], merged), ([fork_only], {}))
        # h-fork-candidate-on-staging: a track that deploys the test server proves a change on staging (H4), its head on main (G4)
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-b", "staging", "main"], check=True, env=env)
        subprocess.run(["git", "-C", repo, "merge", "-q", "--no-ff", "--no-edit", "fork-only"], check=True, env=env)
        staging = hd.act.git(repo, "rev-parse", "staging")
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-b", "dev", "main"], check=True, env=env)
        head = commit("head", "dev")
        T = Track("fork", "x/y", repo, "refs/heads/main", "o/y", recipes={"deploy": "fork-1"})
        cfg = Cfg(tracks={"fork": T})
        defs.update(f=Change("f", "fork", deps=("g",)), g=Change("g", "fork"))
        db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('g', ?, 't', 't', 't')", (fork_only,))
        self.assertEqual((T.candidate_base(), hd.candidate_base(T, defs["f"])), ("refs/heads/staging", staging))
        self.assertEqual(hd.dep_inputs(db, cfg, defs["f"], staging), ([], {}))   # on staging already: in the base
        db.execute("INSERT INTO ref(repo, name, sha, tree, seen_at) VALUES ('central', 'refs/heads/staging', 'c1', 'ct', 't')")
        self.assertEqual(hd.dep_inputs(db, cfg, defs["f"], staging, staged=True), ([], {"central": {"head": "c1", "tree": "ct"}}))   # built with the libraries the test server runs
        tree, tcommit = hd.act.candidate(repo, staging, [head])
        files = hd.act.git(repo, "ls-tree", "--name-only", tree).split()
        self.assertEqual(sorted(files), ["base", "fork", "head", "merged"])   # staging's own commit is proved with the head
        self.assertFalse(hd.act.is_ancestor(repo, fork_only, head))   # the PR head holds no staged commit
        self.assertEqual(Track("central", "x/y", repo, "refs/heads/main", "o/y").candidate_base(), "refs/heads/main")   # no deploy: base

    def test_a_staged_library_dep_merges_onto_the_library_staging(self):   # h-dep-composite-merges-staging: tokenLogin only on Central's staging
        import os, subprocess
        from decide import Change, Cfg, Track
        repo = os.path.join(self.dir.name, "central")
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        def git(*a): subprocess.run(["git", "-C", repo, *a], check=True, env=env, capture_output=True)
        def commit(f, branch):
            git("checkout", "-q", "-B", branch, "main"); Path(repo, f).write_text(f); git("add", f); git("commit", "-qm", f)
            return hd.act.git(repo, "rev-parse", "HEAD")
        os.makedirs(repo); git("init", "-q", "-b", "main")
        Path(repo, "base").write_text("base"); git("add", "base"); git("commit", "-qm", "base")
        staging, dep = commit("token", "staging"), commit("dep", "dep")
        cfg = Cfg(tracks={"central": Track("central", "x/y", repo, "refs/heads/main", "o/y")})
        defs = {"f": Change("f", "fork", deps=("d",)), "d": Change("d", "central")}
        self.addCleanup(setattr, hd, "change", hd.change); hd.change = defs.get
        db = store.connect()
        db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES ('d', ?, 't', 't', 't')", (dep,))
        db.execute("INSERT INTO ref(repo, name, sha, tree, seen_at) VALUES ('central', 'refs/heads/staging', ?, 'st', 't')", (staging,))
        lib = hd.dep_inputs(db, cfg, defs["f"], "unused", staged=True)[1]["central"]
        self.assertEqual(sorted(hd.act.git(repo, "ls-tree", "--name-only", lib["tree"]).split()), ["base", "dep", "token"])
        self.assertTrue(hd.act.is_ancestor(repo, staging, lib["head"]) and hd.act.is_ancestor(repo, dep, lib["head"]))
        self.assertEqual(hd.dep_inputs(db, cfg, defs["f"], "unused")[1]["central"]["head"], dep)   # off staging: the head alone
        git("checkout", "-q", "staging"); git("merge", "-q", "--no-edit", "dep")
        db.execute("UPDATE ref SET sha=? WHERE repo='central'", (hd.act.git(repo, "rev-parse", "staging"),))
        self.assertEqual(hd.dep_inputs(db, cfg, defs["f"], "unused", staged=True)[1]["central"]["head"], hd.act.git(repo, "rev-parse", "staging"))   # already in staging


if __name__ == "__main__":
    unittest.main()
