"""One class per requirement (docs/PRD.md, Acceptance), driven against a dict-backed Fake of Facts in a sandbox root."""
import io, json, os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

for k in ("SLUG", "HEAD", "T", "TCOMMIT", "BASE", "EVIDENCE", "BUILD", "CLONE", "TRACK", "PUBLIC_BRANCH", "PR", "PINS", "CENTRAL", "TOOLS"):
    os.environ.pop(k, None)                                                   # hd's loop env (Hd.env): the gate's own change never reaches a test's track.sh
os.environ["HD_ROOT"] = tempfile.mkdtemp()
import hd, hook  # noqa: E402  (both read HD_ROOT at import)

A, B, C, D = "a" * 40, "b" * 40, "c" * 40, "d" * 40
TA, TB, TC = "ta" * 20, "tb" * 20, "tc" * 20


class Fake(hd.Facts):
    """Facts from dicts: refs {ref: sha}, anc {(tip, sha)}, trees {commit: tree}, merges {(base, head): result},
    blobs {(ref, path): sha}, line {commits of the base's first-parent line}, rows {cmd: (rc, out)}, unknown {remote}. Records spawns and row runs."""

    def __init__(s, **f):
        super().__init__()
        s.f, s.spawned, s.ran, s.envs = f, [], [], []

    def sh(s, args, cwd=None, env=None, timeout=600):
        if args[3:] == ["config", "user.email"]:
            return 0, hd.AUTHOR[1] + "\n", ""                                  # every repo has the noreply identity; a read, not an act
        s.ran.append(args)
        if args[3:5] == ["worktree", "remove"] and args[-1] not in s.f.get("dirty", ()) and ("--force" in args or args[-1] not in s.f.get("links", ())):
            s.f["worktrees"][args[2]] = [w for w in s.f["worktrees"][args[2]] if w[0] != args[-1]]
        if args[3:5] == ["branch", "-D"]:
            s.f["refs"].pop(args[5] if args[2] == str(hd.ROOT) or not args[5].startswith("harness/") else f"{args[2]}:{args[5]}", None)
        if len(args) > 2 and args[1] == "down" and s.f.get("down_works", True):
            s.f.get("containers", {}).pop(f"server-{args[2]}", None)
        return 0, "", ""
    def containers(s): return s.f.get("containers", {})  # None in f = docker unreachable
    def orchestrator(s): return s.f.get("orchestrator", 1)  # None in f = no orchestrator session
    def release(s, repo, tag): return {"tag": tag} if tag in s.f.get("releases", ()) else {}
    def fetch(s, clone, remote): return remote not in s.f.get("unknown", ())
    def rev(s, clone, ref):
        if ref.split("/")[0] in s.f.get("unknown", ()): return None
        if ref.startswith("harness/") and clone != str(hd.ROOT): return s.f.get("refs", {}).get(f"{clone}:{ref}", "")  # a product repo's tools ref
        return s.f.get("refs", {}).get(ref, "")
    def worktrees(s, repo): return s.f.get("worktrees", {}).get(repo, [])
    def edits(s, wt): return wt in s.f.get("dirty", ())  # "links": worktrees git refuses to remove unforced, no one's edits
    def contains(s, clone, tip, sha):
        if tip is None: return None
        return bool(tip and sha) and (tip == sha or (tip, sha) in s.f.get("anc", set()))
    def on_line(s, clone, tip, sha): return sha in s.f.get("line", ())
    def tree(s, clone, commit, drop=""): return s.f.get("trees", {}).get(commit)
    def merge(s, clone, base, head, msg): return s.f.get("merges", {}).get((base, head), ("ok", head))
    def blob(s, clone, ref, path): return s.f.get("blobs", {}).get((ref, path), "")
    def rebase(s, repo, branch, onto, wt): s.ran.append(["rebase", repo, branch, onto]); return s.f.get("rebases", {}).get(branch, ("conflict", "x"))
    def proc_start(s, pid): return "1"
    def alive(s, pid, start): return (pid, start) in s.f.get("procs", {(7, "1")})  # the console is alive unless a test says otherwise
    def spawn(s, args, log, env=None): s.spawned.append(args); s.envs.append(env or {}); return 4242, "99"
    def run(s, cmd, cwd, env): s.ran.append(cmd); return s.f.get("rows", {}).get(cmd, (1, "false") if cmd.startswith("false") else (0, ""))
    def review_comments(s, repo, pr): return s.f.get("comments", {}).get(pr, [])


class Sandbox(unittest.TestCase):
    """A temp HD_ROOT with hd.yaml, each repo's tools/track.md seed rows, harness/changes and goals written by helpers."""

    def setUp(s):
        s.root = Path(tempfile.mkdtemp())
        hd.ROOT, hd.STATE, hd.EVID, hd.DEFS = s.root, s.root / "state", s.root / "evidence", s.root / "harness"
        repos = {"client": s.root / "client", "fork": s.root / "fork", "central": s.root / "central", "harness": s.root}
        (s.root / "hd.yaml").write_text(json.dumps({"repos": {"client": {"name": "o/c", "path": str(repos["client"])}, "fork": {"name": "o/f", "path": str(repos["fork"]), "tools": "local/harness", "upstream": "u/f"},
                                                     "central": {"name": "o/z", "path": str(repos["central"]), "tools": "local/harness", "upstream": "u/z"},
                                                     "harness": {"name": "o/h", "path": str(s.root)}}, "agents": 3, "context_limit": 150000, "pins": []}))
        for track, p in (("client", repos["client"]), ("server", repos["fork"] / ".worktrees" / "harness"), ("central", repos["central"] / ".worktrees" / "harness"), ("harness", s.root)):
            (p / "tools").mkdir(parents=True, exist_ok=True)
            (p / "tools" / "track.md").write_text(f"# {track}\n\n## Seed rows\n- ok | always passes | check: true\n" + (f"- j1 | a judged row | judge: qa-{track}\n" if track in ("server", "central") else ""))
        (s.root / "harness" / "changes").mkdir(parents=True)
        (s.root / "harness" / "goals").mkdir(parents=True)
        s.seq = 0
        s.console = mock.patch.object(hd.Facts, "console", lambda f: (7, "1")); s.console.start()

    def tearDown(s):
        s.console.stop()
        shutil.rmtree(s.root, ignore_errors=True)

    def change(s, slug, track="server", body="do it", **meta):
        s.seq += 1
        meta = {"slug": slug, "track": track, "title": slug, "priority": "P2", "deps": [], "created": f"2026-10-31T00:00:{s.seq:02d}Z", **meta}
        (s.root / "harness" / "changes" / f"{slug}.md").write_text("---\n" + "".join(f"{k}: {json.dumps(v)}\n" for k, v in meta.items()) + "---\n" + body)

    def agreed(s, slug, track="server", extra=""):
        hd.write_contract(hd.cfg(), slug, track, "qa-run")
        with open(s.root / "evidence" / slug / "contract.md", "a") as f:
            f.write(extra)
        (s.root / "evidence" / slug / "pr-body.md").write_text("body")

    def ctx(s, F):
        return hd.Ctx(F, hd.cfg())

    def state(s, F, slug):
        return hd.nxt(s.ctx(F), hd.defs("changes")[slug])

    def gated(s, slug, F):
        """Hand over, build and gate at the current head and tree."""
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover([slug])
        ho = hd.rec(slug, "handover")
        hd.put(slug, "build", {"T": ho["T"], "ok": True})
        hd.put(slug, "gate", {"T": ho["T"], "ok": True})
        return ho

    def verdict(s, slug, head, rows, F):
        f = s.root / "rows.json"
        f.write_text(json.dumps(rows))
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_verdict([slug, head, str(f)])


FACTS = dict(refs={"origin/HEAD": B, "fork/dev/s1": A, "origin/client/c1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})


def payload(run, agent_id, event, root, last=None, usage=None, context=1000, handback=None):
    """A hook payload with a transcript whose first message is the one-line prompt naming the brief."""
    tp = root / "state" / f"transcript-{agent_id}.jsonl"
    lines = [{"type": "user", "message": {"role": "user", "content": f"Read and follow {run['brief']}"}}]
    for i in range(usage or 0):
        lines.append({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": f"turn {i}"}],
                                                        "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": context, "cache_creation_input_tokens": 0}}})
    if handback:
        lines.append({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "SubagentHandback", "input": {"message": handback}}]}})
    tp.write_text("".join(json.dumps(l) + "\n" for l in lines))
    p = {"hook_event_name": event, "agent_id": agent_id, "agent_type": run["role"], "agent_transcript_path": str(tp)}
    if last:
        p["last_assistant_message"] = last
    return p


class R1(Sandbox):
    def goal(s, slug="client-api", track="client", target=100, deps=()):
        (s.root / "harness" / "goals" / f"{slug}.md").write_text(f"---\nslug: {slug}\ntrack: {track}\ntarget: {target}\ndeps: {list(deps)}\n---\nthe goal")

    def test_a_goal_without_target_is_skipped_not_a_crash(s):
        (s.root / "harness" / "goals" / "ask.md").write_text("---\nslug: ask\ntrack: harness\n---\nthe user's words")
        hd.defs.bad.clear()
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertEqual(v["goal"], [])
        s.assertTrue(any("ask.md: a goal needs a track and a numeric target" in a for a in v["alert"]))

    def test_a_goal_dep_not_live_holds_its_measure(s):
        s.change("s1"); s.agreed("s1"); s.goal(deps=["s1"])
        F = Fake(**FACTS)
        v = hd.tick(s.ctx(F))
        s.assertEqual(v["goal"], ["client-api: waiting on s1"])
        s.assertEqual([x for x in F.spawned if x[1] == "measure"], [])
        hd.put("live", "tree", {"tree": "ti" * 20, "commit": C, "heads": [A]})     # the dep is live: the goal is measured
        hd.tick(s.ctx(F))
        s.assertEqual([x[1:] for x in F.spawned if x[1] == "measure"], [["measure", "client-api", B]])

    def test_target_move_lists_measure_once(s):
        s.goal()
        F = Fake(**FACTS)
        v = hd.tick(s.ctx(F))
        s.assertEqual(v["goal"], ["client-api: measuring on tbtbtbtbtbtb"])
        s.assertEqual([x[1:] for x in F.spawned], [["measure", "client-api", B]])
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 93.2, "report": "api-probe.tsv"})
        v = hd.tick(s.ctx(F))
        s.assertEqual(len(F.spawned), 1)                               # measured on this tree: nothing runs again
        s.assertTrue(v["goal"][0].startswith("client-api: 93.2 / 100 on tbtbtbtbtbtb"))
        F2 = Fake(**{**FACTS, "refs": {**FACTS["refs"], "origin/HEAD": C}, "trees": {**FACTS["trees"], C: TC}})
        hd.tick(s.ctx(F2))
        s.assertEqual([x[1:] for x in F2.spawned], [["measure", "client-api", C]])   # the target moved: measured again, once

    def test_live_server_tree_is_part_of_the_client_target(s):
        s.goal()
        F = Fake(**FACTS)
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 93.2, "report": "r"})
        hd.tick(s.ctx(F)); s.assertEqual(F.spawned, [])
        hd.put("live", "tree", {"tree": "ti" * 20, "commit": C, "heads": [A]})    # a server change went live on the test server
        v = hd.tick(s.ctx(F))
        s.assertEqual([x[1:] for x in F.spawned], [["measure", "client-api", B]])
        s.assertEqual(v["goal"], ["client-api: measuring on tbtbtbtbtbtb"])

    def test_server_head_live_on_test_server_unblocks_client_dep(s):
        s.change("s1"); s.agreed("s1"); s.change("c1", "client", deps=["s1"])
        F = Fake(**FACTS)
        s.assertEqual(s.state(F, "c1")["state"], "waiting on s1")
        hd.put("live", "tree", {"tree": "ti" * 20, "commit": C, "heads": [A]})     # live on the test server, not merged upstream
        s.assertNotEqual(s.state(F, "c1")["actor"], "wait")

    def test_below_target_with_nothing_open_lists_the_planner(s):
        s.goal()
        F = Fake(**FACTS)
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 93.2, "report": "r"})
        v = hd.tick(s.ctx(F))
        s.assertIn("planning due", v["goal"][0])
        s.assertTrue(any(x.startswith("planner-") for x in v["spawn"]))
        s.change("c1", "client", goal="client-api")                    # a change serves the goal: no planning
        hd.tick(s.ctx(F))
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 93.2, "report": "r"})
        v = hd.tick(s.ctx(F))
        s.assertNotIn("planning due", v["goal"][0])
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 100, "report": "r"})
        s.assertNotIn("planning due", hd.tick(s.ctx(F))["goal"][0])   # met: measured, nothing planned


    def test_a_passing_verdict_on_a_live_change_marks_the_units_it_names(s):
        s.goal("server-content", "server")
        s.change("s1", goal="server-content", units=["quest:cooksassistant"]); s.agreed("s1")
        F = Fake(**FACTS)
        measured = lambda: [e["PASSES"] for x, e in zip(F.spawned, F.envs) if x[1] == "measure"]
        s.gated("s1", F)
        hd.put("live", "tree", {"tree": "ti" * 20, "commit": C, "heads": [A]})     # live, no verdict yet: nothing passes
        hd.tick(s.ctx(F)); s.assertEqual(measured(), [""])
        hd.put("server-content", "measure", {"tree": TB, "value": 0, "report": "r"})
        s.verdict("s1", A, {"ok": "fail: no", "j1": "pass"}, F)
        hd.tick(s.ctx(F)); s.assertEqual(measured(), [""])                         # a failing verdict marks nothing
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        hd.tick(s.ctx(F)); s.assertEqual(measured(), ["", "quest:cooksassistant"])  # the key moved: measured once more, with the unit

    def test_server_content_inventory_rows_are_kinds_of_its_goal(s):
        g = Path(__file__).parent.parent / "harness" / "goals"
        rows = json.loads((g / "server-content.json").read_text())
        kinds = re.findall(r"^\| (\w+) \| \w+", (g / "server-content.md").read_text(), re.M)[1:]   # past the header
        s.assertTrue(rows); s.assertEqual(len({r["unit"] for r in rows}), len(rows))
        s.assertEqual(sorted({r["unit"].split(":")[0] for r in rows}), sorted(kinds))
        s.assertTrue(all(set(r) == {"unit", "source"} and r["source"].startswith("dbrow.") for r in rows))

class R2(Sandbox):
    def test_main_relays_to_the_orchestrator_session(s):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            hd.cmd_tell(["also", "measure", "the", "client"]); hd.cmd_tell(["second"])
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertEqual(v["message"], ["1: also measure the client", "2: second"])       # listed until handled
        s.assertFalse(any("orchestrator session" in a for a in v["alert"]))
        with contextlib.redirect_stdout(io.StringIO()):
            hd.cmd_heard(["1"])
        v = hd.tick(s.ctx(Fake(**{**FACTS, "orchestrator": None})))
        s.assertEqual(v["message"], ["2: second"])
        s.assertTrue(any(a.startswith("user: no orchestrator session") for a in v["alert"]))   # main tells the user to start it
        s.assertFalse(any(x.startswith("planner-") for x in v["spawn"]))                       # the user's to fix, no planner

    def test_defined_to_live_with_no_person(s):
        s.change("s1"); hd.put("live", "tree", {"tree": TB, "commit": B, "heads": [A]})  # the dependency is live on the test server
        s.change("c1", "client", deps=["s1"])
        F = Fake(**{**FACTS, "refs": {"origin/HEAD": B, "fork/dev/s1": A, "origin/client/c1": ""}})
        views = [hd.tick(s.ctx(F))]                                   # contract derived (no qa run)
        views.append(hd.tick(s.ctx(F)))                               # dev listed
        spawn = [x for x in views[-1]["spawn"] if x.startswith("c1-")]
        s.assertEqual(len(spawn), 1)                                  # (s1, not done upstream, gets its own qa run)
        run = [r for r in hd.runs() if r["change"] == "c1"][0]
        s.assertEqual((run["role"], run["started"]), ("dev", None))
        s.assertIn("Read and follow", spawn[0])
        s.assertNotIn("##", spawn[0])                                 # spawn by path: nothing of the brief in main's context
        s.assertIn(f"Base: origin/HEAD at {B[:9]}", open(run["brief"]).read())   # the dev branches from the base tip the brief names
        with mock.patch.object(hook, "start_pass") as sp:
            hook.bind(payload(run, "ag1", "SubagentStart", s.root))
            F.f["refs"]["origin/client/c1"] = A                       # the dev pushes and hands over
            (s.root / "evidence" / "c1" / "log.txt").write_text("evidence")
            with mock.patch.object(hd, "Facts", lambda: F):
                hd.cmd_handover(["c1"])
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="run c1-1: handed over " + A, usage=3, handback="run c1-1: handed over " + A))
            s.assertEqual(sp.call_count, 1)                           # the pass is started, never waited on
        run = [r for r in hd.runs() if r["change"] == "c1"][0]
        s.assertTrue(run["record"]); s.assertEqual(run["usage"]["turns"], 3); s.assertIn("handed over", run["last"])
        v = hd.tick(s.ctx(F)); s.assertEqual(F.spawned[-1][1:], ["build", "c1", A])
        hd.put("c1", "build", {"T": TA, "ok": True})
        v = hd.tick(s.ctx(F)); s.assertEqual(F.spawned[-1][1:], ["gate", "c1", A])
        hd.put("c1", "gate", {"T": TA, "ok": True})
        v = hd.tick(s.ctx(F)); s.assertEqual(F.spawned[-1][1:], ["ship", "c1", A])
        F.f["anc"] = {(B, A)}                                          # the ship pushed the merge: master holds the head
        v = hd.tick(s.ctx(F))
        s.assertIn("c1 [client P2]: done", v["change"])
        for view in views + [v]:
            s.assertEqual((view["card"], view["question"]), ([], []))  # no person anywhere on the path
        s.assertIsNone(hd.rec("c1", "approval"))

    def test_a_change_the_user_closes_takes_no_step_and_leaves_t_int(s):
        s.change("s1"); s.agreed("s1"); s.change("s2", deps=["s1"])
        F = Fake(**FACTS)
        (s.root / "evidence" / "s1" / "log.txt").write_text("evidence")
        s.gated("s1", F)
        s.assertEqual(hd.integration(s.ctx(F))["names"], ["s1"])
        hd.tick(s.ctx(F))
        listed = [r for r in hd.runs() if r["change"] == "s1"]
        s.assertEqual(len(listed), 1)                                 # a qa run listed, not yet spawned
        hd.cmd_close(["s1", "done", "upstream"])
        s.assertIn("closed: 'answer-1: done upstream'", (s.root / "harness" / "changes" / "s1.md").read_text())
        s.assertIn("- answer-1 |", hd.contract("s1")["text"])
        v = hd.tick(s.ctx(F))
        s.assertIn("s1 [server P2]: closed: answer-1: done upstream", v["change"])
        s.assertFalse([x for x in v["spawn"] if x.startswith("s1-")])  # the listed run ends; none is listed again
        s.assertEqual(hd.runs()[0]["reason"], "change closed")
        s.assertEqual(hd.integration(s.ctx(F))["names"], [])         # nothing open: no T_int beyond what is live
        s.assertNotEqual(s.state(F, "s2")["state"], "waiting on s1")  # a closed dependency holds nothing
        s.assertNotIn("s1 [server P2]: closed: answer-1: done upstream", hd.tick(s.ctx(F))["change"])  # shown once
        with s.assertRaises(SystemExit):
            hd.cmd_close(["s1", "again"])

    def test_fresh_dev_ref_in_the_base_is_not_done(s):
        s.change("h1", "harness"); s.change("c1", "client", deps=["h1"])
        F = Fake(refs={"HEAD": B, "harness/h1": A, "origin/HEAD": B, "origin/client/c1": ""}, anc={(B, A)}, line={A, B}, trees={A: TA})
        s.assertEqual(s.state(F, "h1")["state"], "contract: seed rows pending")    # cut at A, a base commit; the base moved on to B
        s.assertEqual(s.state(F, "c1")["state"], "waiting on h1")
        hd.write_contract(hd.cfg(), "h1", "harness", "derived")
        (s.root / "evidence" / "h1" / "log.txt").write_text("evidence")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1"])
        s.assertEqual(s.state(F, "h1")["state"], "done")                          # handed over: its own work

    def test_a_live_run_of_a_done_change_ends_with_its_record(s):
        s.change("h1", "harness"); hd.write_contract(hd.cfg(), "h1", "harness", "derived")
        F = Fake(**{**FACTS, "refs": {"HEAD": B, "harness/h1": A, "origin/HEAD": B}, "anc": {(B, A)}, "line": {A, B}, "trees": {A: TA}})
        hd.tick(s.ctx(F))
        run = [r for r in hd.runs() if r["change"] == "h1"][0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        (s.root / "evidence" / "h1" / "log.txt").write_text("evidence")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1"])
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="handed over"))   # a plain-text stop: still live
        s.assertFalse(hd.runs()[0]["ended"])
        v = hd.tick(s.ctx(F))
        r = hd.runs()[0]
        s.assertEqual((r["reason"], r["record"], bool(r["ended"])), ("change done", True, True))
        s.assertEqual(v["run"], [])                                                         # its slot is free
        s.assertTrue(any('"action": "ended"' in l and '"change done"' in l for l in open(s.root / "state" / "events.jsonl")))

    def test_a_done_change_leaves_no_worktree_or_local_branch(s):
        s.change("h1", "harness"); hd.write_contract(hd.cfg(), "h1", "harness", "derived")
        r, f = str(s.root), str(s.root / "fork")
        F = Fake(refs={"HEAD": A, "harness/h1": A, "harness/h2": B, f"{f}:harness/h1": "X", "origin/HEAD": B, "local/harness": "C"},
                 anc={("local/harness", "X"), ("C", "X"), ("X", "local/harness")}, trees={A: TA},
                 worktrees={r: [(r, "v8"), (f"{r}/.worktrees/h1", "harness/h1"), (f"{r}/.worktrees/h1-build", ""), (f"{r}/.claude/worktrees/ag", "harness/h1"), (f"{r}/.worktrees/h2", "harness/h2")],
                            f: [(f, ""), (f"{f}/.worktrees/harness", "local/harness"), (f"{f}/.worktrees/h1", "harness/h1"), (f"{f}/.worktrees/h1-build", "")]})
        (s.root / "evidence" / "h1" / "log.txt").write_text("evidence")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1"])
        s.assertEqual(s.state(F, "h1")["state"], "done")
        hd.tick(s.ctx(F))
        s.assertEqual(F.f["worktrees"], {r: [(r, "v8"), (f"{r}/.worktrees/h2", "harness/h2")], f: [(f, ""), (f"{f}/.worktrees/harness", "local/harness")]})
        s.assertEqual(sorted(F.f["refs"]), ["HEAD", "harness/h2", "local/harness", "origin/HEAD"])   # remote refs are never touched
        s.assertEqual([a[2] for a in F.ran if a[3:5] == ["branch", "-D"]], [f, r])                # the dev ref last
        s.assertEqual(s.state(F, "h1")["state"], "done")                                          # the swept head stays done
        n = len(F.ran); hd.tick(s.ctx(F)); s.assertEqual(len(F.ran), n)                          # swept once

    def test_closed_change_branches_go_an_unheld_one_stays_a_failed_removal_raised_once(s):
        s.change("s1", closed="answer-1: dropped"); s.change("c1", "client")
        f, c = str(s.root / "fork"), str(s.root / "client")
        F = Fake(refs={"origin/HEAD": B, "dev/s1": "D", "origin/client/c1": A, "client/c1": "E"}, anc={(B, A)}, trees={A: TA},
                 worktrees={f: [(f, ""), (f"{f}/.worktrees/s1", "dev/s1")]}, dirty={f"{f}/.worktrees/s1"})
        s.assertEqual(s.state(F, "c1")["state"], "done")
        alerts = [any("cannot remove" in a for a in hd.tick(s.ctx(F))["alert"]) for _ in range(3)]
        s.assertEqual(alerts, [False, True, False])
        s.assertIn("client/c1", F.f["refs"]); s.assertIn(f"{c}: client/c1 at E is held by no live branch", hd.rec("c1", "repair-close")["left"])
        F.f["dirty"] = set(); hd.tick(s.ctx(F))
        s.assertNotIn("dev/s1", F.f["refs"]); s.assertTrue(hd.rec("s1", "swept"))                # closed: removed whatever it holds

    def test_a_worktree_whose_only_untracked_entry_is_a_symlink_holds_no_edits(s):
        c = str(s.root / "client"); wt = f"{c}/.claude/worktrees/c1"
        s.change("c1", "client")
        F = Fake(refs={"origin/HEAD": B, "origin/client/c1": A, "client/c1": A}, anc={(B, A)}, trees={A: TA}, worktrees={c: [(c, ""), (wt, "client/c1")]}, links={wt})
        hd.tick(s.ctx(F))
        s.assertIn(["git", "-C", c, "worktree", "remove", "--force", wt], F.ran); s.assertTrue(hd.rec("c1", "swept"))
        import subprocess
        repo = s.root / "real"; repo.mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, check=True)
        git("init", "-q"); (repo / ".gitignore").write_text("re/\n"); (repo / "re").mkdir()
        git("add", "."); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i")
        git("worktree", "add", "-q", "--detach", str(repo / "wt")); os.symlink(repo / "re", repo / "wt" / "re"); real = hd.Facts()
        s.assertFalse(real.edits(str(repo / "wt")))                                    # untracked symlinks only: no one's edits
        (repo / "wt" / "f").write_text("x"); s.assertTrue(real.edits(str(repo / "wt")))   # an untracked file is
        (repo / "wt" / "f").unlink(); (repo / "wt" / ".gitignore").write_text("x"); s.assertTrue(real.edits(str(repo / "wt")))  # a tracked edit is

    def test_maintainer_inline_comment_files_a_change_once(s):
        s.change("s1", pr=354, branch="content/cannon"); s.agreed("s1")
        s.change("s1-old", pr=354, deps=["s1"], finding=7)                 # filed by hand: carried
        com = lambda i, who="a-thoren", **k: {"id": i, "author": who, "bot": False, "reply": None, "path": "N.kt", "line": 265, "body": "reset | the varp?", **k}
        F = Fake(**{**FACTS, "comments": {354: [com(7), com(8), com(9, reply=8), com(10, "O"), com(11, "ci", bot=True)]}})
        hd.tick(s.ctx(F), act=False)
        s.assertFalse((s.root / "harness" / "changes" / "s1-c8.md").exists())  # a dry run files nothing
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))
        new = {k: v for k, v in hd.defs("changes").items() if k not in ("s1", "s1-old")}
        s.assertEqual(list(new), ["s1-c8"])                                # one change, once: replies, ours, bots, carried skipped
        c = new["s1-c8"]
        s.assertEqual((c["deps"], c["pr"], c["finding"], c["priority"], c["branch"]), (["s1"], 354, 8, "P1", "content/cannon"))
        con = hd.contract("s1-c8")
        s.assertIsNone(con["agreed"])                                      # the inherited contract is agreed again by qa
        s.assertEqual([r["id"] for r in con["rows"]], [r["id"] for r in hd.contract("s1")["rows"]] + ["finding"])
        s.assertEqual(con["rows"][-1]["judge"], "judge"); s.assertIn("reset / the varp?", con["rows"][-1]["text"])

    def test_spawn_listed_exactly_while_agent_step_unmet_and_no_run_alive(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 1)
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 1)            # the same listing, not a second run
        s.assertEqual(len(hd.runs()), 1)
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        v = hd.tick(s.ctx(F))
        s.assertEqual((v["spawn"], len(v["run"])), ([], 1))           # alive: listed under run, not spawn
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, handback="run s1-1: gave up"))
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 1)            # one retry on the same input
        run2 = hd.runs()[1]
        hook.bind(payload(run2, "ag2", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run2, "ag2", "SubagentStop", s.root, handback="run s1-2: gave up"))
        v = hd.tick(s.ctx(F))
        s.assertEqual([x for x in v["spawn"] if x.startswith("s1-")], [])   # then raised once, never a third
        s.assertTrue(any("ended without a record" in a for a in v["alert"]))
        s.assertTrue(any(x.startswith("planner-") for x in v["spawn"]))  # the alert lists the planner, not the user

    def test_a_listed_spawn_goes_when_its_change_stops_being_due(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 1)
        hd.cmd_new(["x1", "--track", "harness", "--title", "a fix s1 waits on", "--blocks", "s1"])
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(c.startswith("s1 ") and "waiting on x1" in c for c in v["change"]))
        s.assertEqual([x for x in v["spawn"] if x.startswith("s1-")], [])          # the listed run is dropped, not kept
        s.assertEqual(hd.runs()[0]["reason"], "no longer due")
        s.change("s1")                                                             # the dep dropped again
        v = hd.tick(s.ctx(F))
        s.assertEqual([x.split(":")[0] for x in v["spawn"] if x.startswith("s1-")], ["s1-2"])   # due again: listed afresh
        s.assertFalse(any("ended without a record" in a for a in v["alert"]))     # an unspawned run is no failed attempt

    def test_two_passes_list_a_run_once(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        waited = s.ctx(F)                       # a pass that read the state, then waited on the lock
        hd.tick(s.ctx(F))                       # the pass holding the lock lists s1-1
        hd.tick(waited)
        s.assertEqual([r["name"] for r in hd.runs() if r["change"] == "s1"], ["s1-1"])
        s.assertEqual(sum(1 for l in open(s.root / "state" / "events.jsonl") if '"listed"' in l and '"s1-1"' in l), 1)

    def test_a_run_ends_at_its_last_stop_and_is_alive_while_resumed(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hd.cmd_new(["x9", "--track", "harness", "--title", "another run's filing"])
            hd.cmd_ask(["s1", "which?"]); hd.cmd_answer(["s1", "this one"])   # an answered ask, then work goes on
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="Waiting for the build to finish.", usage=2))   # an idle turn
            r = hd.runs()[0]
            s.assertEqual((r["ended"], r["last"], r["usage"]["turns"]), (None, "Waiting for the build to finish.", 2))   # live, usage and last kept
            v = hd.tick(s.ctx(F))
            s.assertEqual(([x for x in v["spawn"] if x.startswith("s1-")], len(hd.runs())), ([], 1))   # alive between the stop and the resume: no second run
            hook.bind(payload(run, "ag1", "PreToolUse", s.root))          # the build notification resumes it
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="I'll hand back.", usage=5, handback="run s1-1: handoff"))
        r = hd.runs()[0]
        s.assertTrue(r["ended"]); s.assertEqual((r["last"], r["usage"]["turns"]), ("run s1-1: handoff", 5))   # the hand-back's stop ends it
        s.assertFalse(r["record"])                                        # nothing newer than the answer: no record

    def test_an_idle_stop_is_refused_while_its_own_background_work_runs(s):
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        p = payload(run, "ag1", "SubagentStop", s.root, last="Waiting on the build.", usage=1)
        tp = Path(p["agent_transcript_path"])
        with open(tp, "a") as f:
            f.write(json.dumps({"type": "user", "toolUseResult": {"stdout": "", "backgroundTaskId": "b1"}}) + "\n")
        with mock.patch.object(hook, "start_pass"), mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            hook.end_run(p)
        s.assertEqual(json.loads(out.getvalue())["decision"], "block")        # the build still runs: the stop is refused
        with open(tp, "a") as f:
            f.write(json.dumps({"type": "attachment", "attachment": {"prompt": "<task-notification>\n<task-id>b1</task-id>"}}) + "\n")
        with mock.patch.object(hook, "start_pass"), mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            hook.end_run(p)
        s.assertEqual((out.getvalue(), hd.runs()[0]["ended"]), ("", None))   # its end reported: an idle stop, the run live

    def test_a_hand_back_waits_for_its_subagents_and_keeps_their_answers(s):
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        p = payload(run, "ag1", "SubagentStop", s.root, usage=1, handback="run s1-1: handoff")
        tp = Path(p["agent_transcript_path"])
        with open(tp, "a") as f:
            f.write(json.dumps({"type": "user", "toolUseResult": {"isAsync": True, "status": "async_launched", "agentId": "c1"}}) + "\n")
        pre = dict(p, hook_event_name="PreToolUse", tool_name="SubagentHandback", tool_input={"message": "run s1-1: handoff"})
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            hook.hold_handback(pre)
        s.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")   # its subagent still runs
        (tp.parent / "agent-c1.jsonl").write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "SubagentHandback", "input": {"message": "the basement is under the manor"}}]}}) + "\n")
        with open(tp, "a") as f:
            f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "<task-notification>\n<task-id>c1</task-id>"}}) + "\n")
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            hook.hold_handback(pre)
        s.assertEqual(out.getvalue(), "")                                  # its end reported: the hand-back goes
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(p)
        s.assertTrue(hd.runs()[0]["ended"])
        s.assertEqual((s.root / "evidence" / "s1" / "subagent-c1.md").read_text(), "the basement is under the manor\n")   # its answer kept

    def test_hook_binds_by_brief_path_and_wakes_main(s):
        s.change("s1"); s.agreed("s1"); s.change("s2"); s.agreed("s2")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s2": A}})
        hd.tick(s.ctx(F))
        r1, r2 = hd.runs()
        wake = (s.root / "state" / "wake").read_text()
        hook.bind(payload(r2, "agX", "SubagentStart", s.root))        # the second listed run is spawned first
        s.assertEqual([r.get("agent_id") for r in hd.runs()], [None, "agX"])
        s.assertEqual((hd.runs()[1]["console_pid"], hd.runs()[0]["console_pid"]), (7, None))   # the hook binds the console; the pass records none
        s.assertNotEqual((s.root / "state" / "wake").read_text(), wake)  # a state change touches the wake file
        hook.bind(payload(r2, "agX", "PreToolUse", s.root))           # a repeated bind changes nothing
        s.assertEqual(hd.runs()[1]["started"], hd.runs()[1]["started"])
        s.assertEqual(sum(1 for l in open(s.root / "state" / "events.jsonl") if '"started"' in l), 1)


    def test_runs_spawned_together_each_bind_their_own_brief(s):
        """SubagentStart carries only the session's transcript_path; each agent's prompt is in <session>/subagents/."""
        for c in ("s1", "s2", "s3"):
            s.change(c); s.agreed(c)
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s2": A, "fork/dev/s3": A}})
        hd.tick(s.ctx(F))
        runs = sorted(hd.runs(), key=lambda r: r["name"])
        session = s.root / "state" / "session.jsonl"
        session.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "drive"}}) + "\n")
        (s.root / "state" / "session" / "subagents").mkdir(parents=True)
        def p(r, aid, ev, prompt=True):
            if prompt:
                (s.root / "state" / "session" / "subagents" / f"agent-{aid}.jsonl").write_text(
                    json.dumps({"type": "user", "message": {"role": "user", "content": f"Read and follow {r['brief']}"}}) + "\n")
            return {"hook_event_name": ev, "agent_id": aid, "agent_type": r["role"], "transcript_path": str(session)}
        hook.bind(p(runs[2], "a3", "SubagentStart"))                  # spawned in one message: started in any order
        hook.bind(p(runs[0], "a1", "SubagentStart", prompt=False))    # its prompt not written yet: binds nothing
        hook.bind(p(runs[1], "a2", "SubagentStart"))
        s.assertEqual([r.get("agent_id") for r in sorted(hd.runs(), key=lambda r: r["name"])], [None, "a2", "a3"])
        hook.bind(p(runs[0], "a1", "PreToolUse"))                     # its first tool call binds it
        bound = sorted(hd.runs(), key=lambda r: r["name"])
        s.assertEqual([r["agent_id"] for r in bound], ["a1", "a2", "a3"])
        s.assertTrue(bound[2]["transcript"].endswith("subagents/agent-a3.jsonl"))
        with mock.patch.object(hook, "start_pass"):
            with open(s.root / "state" / "session" / "subagents" / "agent-a3.jsonl", "a") as t:   # a3 hands back
                t.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "SubagentHandback", "input": {"message": "run s3-1: handoff"}}]}}) + "\n")
            hook.end_run(p(runs[2], "a3", "SubagentStop", prompt=False))   # the first to stop ends its own run only
        s.assertEqual([bool(r["ended"]) for r in sorted(hd.runs(), key=lambda r: r["name"])], [False, False, True])

    def test_planner_listed_once_per_unanswered_alert(s):
        s.change("s1", deps=["gone"])                                            # an alert: s1's dependency has no definition
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        orc = [r for r in hd.runs() if r["role"] == "planner"][0]
        hook.bind(payload(orc, "agO", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(orc, "agO", "SubagentStop", s.root, handback="run planner-1: nothing to file"))
        s.change("s2", deps=["lost"])                                            # a second alert: the first is answered
        hd.tick(s.ctx(F))
        orc2 = [r for r in hd.runs() if r["role"] == "planner"][1]
        s.assertEqual(json.loads(orc2["input"])[0:1], ["s2: dependency lost has no definition"])
        hook.bind(payload(orc2, "agO2", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(orc2, "agO2", "SubagentStop", s.root))           # an idle stop: still live
            s.assertIsNone(hd.runs()[-1]["ended"])
            hd.cmd_stop([orc2["name"]])                                           # stopped without a hand-back: no record
        s.assertEqual([r["record"] for r in hd.runs() if r["role"] == "planner"], [True, False])   # the hand-back is the record
        s.change("h1", track="harness", deps=["s2"], body="s2: dependency lost has no definition")   # an open change carries the alert
        hd.tick(s.ctx(F))
        s.assertEqual(len([r for r in hd.runs() if r["role"] == "planner"]), 2)
        s.change("h0", track="harness", closed="answer-1: done")               # a close leaves s1's answered alert answered
        hd.tick(s.ctx(F))
        s.assertEqual(len([r for r in hd.runs() if r["role"] == "planner"]), 2)

    def test_planner_listed_on_significant_facts_only(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        for _ in range(60):                                                     # many events, nothing significant
            hd.event(change="s1", action="noise")
        hd.tick(s.ctx(F))
        s.assertEqual([r for r in hd.runs() if r["role"] == "planner"], [])
        g = {**hd.rec("s1", "gate"), "ok": False, "detail": "FAIL: tests"}
        hd.put("s1", "gate", g)                                                 # a gate failure goes back to its dev run
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))
        s.assertEqual([r for r in hd.runs() if r["role"] == "planner"], [])   # while it is the dev's, no planner
        dev = [r for r in hd.runs() if r["change"] == "s1"][-1]
        s.assertEqual(dev["role"], "dev")
        dev.update(started=hd.now(), ended=hd.now(), record=True)
        hd.save_run(dev)                                                        # its dev handed back and the gate still fails
        hd.tick(s.ctx(F))
        orc = [r for r in hd.runs() if r["role"] == "planner"]
        s.assertEqual(len(orc), 1)
        s.assertIn(f"s1 [server P2]: gate failed: dev at {g['T'][:9]}", json.loads(orc[0]["input"]))
        orc[0].update(started=hd.now(), ended=hd.now(), record=True)
        hd.save_run(orc[0])                                                     # the planner hands back on it
        s.change("h0", track="harness", closed="answer-1: done")               # a close does not re-raise it
        hd.tick(s.ctx(F))
        s.assertEqual(len([r for r in hd.runs() if r["role"] == "planner"]), 1)

    def test_a_run_reads_its_change_once(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        ho = s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "fail: no"}, F)
        hd.put("s1", "build", {"T": ho["T"], "ok": False, "detail": "> Task :gradle noise"})   # a failed build with its log tail
        (s.root / "evidence" / "s1" / "handoff.md").write_text("done: half")
        hd.tick(s.ctx(F))
        b = open([r for r in hd.runs() if r["change"] == "s1"][-1]["brief"]).read()
        for once in ("## Definition", "## Contract", "## Hand-off", "## Last verdict", "- ok | always passes", "done: half"):
            s.assertEqual(b.count(once), 1, once)
        s.assertNotIn("hd.py show", b)                                  # the brief alone: hd show is not read again
        s.assertNotIn("gradle noise", b)                                # the build line is its verdict and key, the log in its file
        s.assertIn(f"build: failed at {ho['T']} (log {hd.STATE / 's1' / 'build.log'})", b)
        root = Path(__file__).parent.parent
        for f in ["tools/track.md", *map(str, root.glob(".claude/agents/*.md"))]:   # the roles say the same
            s.assertNotIn("run `hd show", (root / f).read_text().replace("\n", " "), f)

    def test_planner_record_and_unmatched_stop(s):
        s.change("s1"); s.agreed("s1"); s.change("s0", deps=["gone"])       # an alert lists the planner
        F = Fake(**FACTS)
        v = hd.tick(s.ctx(F))
        orc = [r for r in hd.runs() if r["role"] == "planner"][0]
        hook.bind(payload(orc, "agO", "SubagentStart", s.root))
        hd.cmd_new(["x1", "--track", "harness", "--title", "fix something"])   # the planner files a change
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(orc, "agO", "SubagentStop", s.root, handback="run planner-1: filed x1"))
            s.assertTrue([r for r in hd.runs() if r["role"] == "planner"][0]["record"])
            dev = [r for r in hd.runs() if r["role"] == "dev"][0]
            hook.end_run({"hook_event_name": "SubagentStop", "agent_id": "ghost", "agent_type": "dev"})  # no transcript, no id: ends nothing
        s.assertIsNone([r for r in hd.runs() if r["name"] == dev["name"]][0]["ended"])
        hook.bind({"hook_event_name": "PreToolUse", "agent_id": "x", "agent_type": "Explore"})          # not a harness role: no read
        s.assertEqual(len(hd.runs()), 2)                                                            # nothing bound or listed for it


class R4(Sandbox):
    def test_upstream_and_release_run_only_after_approval_at_head(s):
        s.change("s1"); s.agreed("s1"); s.change("rel", "client", kind="release", version="0.1.3")
        hd.write_contract(hd.cfg(), "rel", "client", "derived")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s1": A}})
        s.gated("s1", F); s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        hd.put("live", "tree", {"tree": "x", "commit": C, "heads": [A]})
        v = hd.tick(s.ctx(F))
        s.assertEqual([a for a in F.spawned if "hd-public" in a[0]], [])
        s.assertEqual(len(v["card"]), 1); s.assertIn("approve s1 " + A, v["card"][0])
        hd.put("s1", "approval", {"head": C, "body": "x"})                        # a yes at another head is no yes
        hd.tick(s.ctx(F)); s.assertEqual([a for a in F.spawned if "hd-public" in a[0]], [])
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_approve(["s1", A])
        hd.tick(s.ctx(F))
        s.assertEqual([a[-3:] for a in F.spawned if "hd-public" in " ".join(a)], [["upstream", "s1", A]])
        st = s.state(F, "rel")                                                   # the release: gate ok, no judge rows → its card
        hd.put("rel", "build", {"T": TB, "ok": True}); hd.put("rel", "gate", {"T": TB, "ok": True})
        s.assertEqual(s.state(F, "rel")["actor"], "user")
        hd.put("rel", "approval", {"head": B, "body": "x"})
        s.assertEqual(s.state(F, "rel")["state"], "publishing v0.1.3")
        F.f["releases"] = {"v0.1.3"}
        s.assertEqual(s.state(F, "rel")["state"], "done")

    def test_a_central_change_goes_upstream_to_central_only_after_the_yes(s):
        s.change("z1", "central"); s.agreed("z1", "central"); s.change("s1", deps=["z1"]); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/z1": D}, "trees": {**FACTS["trees"], D: TC}, "merges": {(B, D): ("ok", D)}})
        s.assertEqual(s.state(F, "s1")["state"], "waiting on z1")
        s.gated("z1", F)                                                         # its test target is its gate: live, the server change goes on
        s.assertNotEqual(s.state(F, "s1")["actor"], "wait")
        s.verdict("z1", D, {"ok": "pass", "j1": "pass"}, F)
        v = hd.tick(s.ctx(F))
        s.assertEqual(s.state(F, "z1")["state"], "gated; waiting for the user's yes")
        s.assertEqual([a for a in F.spawned if "hd-public" in " ".join(a)], [])
        s.assertIn("u/z branch content/z1", [c for c in v["card"] if "z1" in c][0])
        hd.put("z1", "approval", {"head": D, "body": "x"})
        hd.tick(s.ctx(F))
        s.assertEqual([a[-3:] for a in F.spawned if "hd-public" in " ".join(a)], [["upstream", "z1", D]])
        import importlib.util
        spec = importlib.util.spec_from_loader("hd_public", importlib.machinery.SourceFileLoader("hd_public", str(Path(__file__).parent.parent / "hd-public")))
        pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
        pub.ROOT, pub.STATE, pub.EVID, pub.DEFS = s.root, s.root / "state", s.root / "evidence", s.root / "harness"
        calls = []
        def fake_sh(*args, inp=None):
            calls.append(args)
            return (1, "", "stop") if args[:3] == ("gh", "pr", "create") else (0, "[]", "")
        import hashlib
        hd.put("z1", "approval", {"head": D, "body": hashlib.sha256(b"body").hexdigest()[:16]})
        with mock.patch.object(pub, "sh", fake_sh), s.assertRaises(SystemExit):
            pub.upstream("z1", D)
        s.assertEqual(calls[0][:3], ("git", "-C", str(s.root / "central")))     # the Central clone pushes to its fork
        s.assertIn("u/z", calls[1]); s.assertIn("u/z", calls[2])                 # the PR is on Central's upstream

    def test_approve_refused_off_the_user_step(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_approve(["s1", A])
        s.assertIn("nothing to approve", str(e.exception))
        s.assertIsNone(hd.rec("s1", "approval"))

    def test_hook_denies_approve_and_close_in_subagent_only(s):
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for verb in ("approve s1 " + A, "close s1 done"):
                hook.deny_users_word({"agent_id": "a1", "agent_type": "dev", "tool_input": {"command": "python3 ~/osrs-harness/hd.py " + verb}})
                hook.deny_users_word({"tool_input": {"command": "python3 ~/osrs-harness/hd.py " + verb}})          # main: allowed
                hook.deny_users_word({"agent_type": "orchestrator", "tool_input": {"command": "hd " + verb}})      # the orchestrator session: denied
            for c in ("cd x && hd approve s1 " + A, "X=1 ~/osrs-harness/hd.py close s1 done"):      # runs it: denied
                hook.deny_users_word({"agent_id": "a1", "agent_type": "dev", "tool_input": {"command": c}})
            for c in ("grep approve notes.md; git push fork HEAD:dev/s1", "grep -n 'hd approve' hook.py",   # only quotes it: allowed
                      "cat > f.md <<'EOF'\nhd close s1 done\nEOF\ngit add f.md", "echo \"hd.py approve\" | wc"):
                hook.deny_users_word({"agent_id": "a1", "agent_type": "dev", "tool_input": {"command": c}})
        s.assertEqual(out.getvalue().count('"deny"'), 6)

    def test_public_act_runs_as_hd_when_the_user_exists(s):
        ctx = s.ctx(Fake(**FACTS))
        with mock.patch.object(hd.pwd, "getpwnam", lambda n: object()):
            s.assertEqual(ctx.public("upstream", "s1", A)[:4], ["sudo", "-n", "-u", "hd"])
        ctx = s.ctx(Fake(**FACTS))
        with mock.patch.object(hd.pwd, "getpwnam", mock.Mock(side_effect=KeyError)):
            s.assertTrue(ctx.public("upstream", "s1", A)[0].endswith("hd-public"))
            s.assertTrue(any(a.startswith("user: R4") for a in ctx.alerts))


    def test_hd_public_order_and_stop_on_red_ci(s):
        import importlib.util
        spec = importlib.util.spec_from_loader("hd_public", importlib.machinery.SourceFileLoader("hd_public", str(Path(__file__).parent.parent / "hd-public")))
        pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
        pub.ROOT, pub.STATE, pub.EVID, pub.DEFS = s.root, s.root / "state", s.root / "evidence", s.root / "harness"
        s.change("s1"); (s.root / "evidence" / "s1").mkdir(parents=True)
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("Updated to " + A[:9])
        calls, ci = [], ["pending", "success"]
        def fake_sh(*args, inp=None):
            calls.append(args[:3])
            if args[:3] == ("gh", "pr", "list"): return 0, "[]", ""
            if args[:3] == ("gh", "pr", "create"): return 0, "https://github.com/u/f/pull/42", ""
            if args[:3] == ("gh", "pr", "view") and "headRefOid,statusCheckRollup" in args:
                st = ci.pop(0)
                return 0, json.dumps({"headRefOid": A, "statusCheckRollup": [{"status": "COMPLETED" if st != "pending" else "IN_PROGRESS", "conclusion": st.upper()}]}), ""
            if args[:3] == ("gh", "pr", "view"): return 0, json.dumps({"comments": []}), ""
            return 0, "", ""
        with mock.patch.object(pub, "sh", fake_sh), mock.patch.object(pub.time, "sleep", lambda n: None):
            with s.assertRaises(SystemExit) as e:
                pub.upstream("s1", A)
            s.assertIn("no approval", str(e.exception))
            hd.put("s1", "approval", {"head": A, "body": "x"})
            with s.assertRaises(SystemExit) as e:
                pub.upstream("s1", A)
            s.assertIn("no approval", str(e.exception))                       # the body changed since the yes
            import hashlib
            hd.put("s1", "approval", {"head": A, "body": hashlib.sha256(b"").hexdigest()[:16]})
            with s.assertRaises(SystemExit) as e:
                pub.upstream("s1", A)
        s.assertEqual(e.exception.code, 0)
        s.assertEqual(calls[0][:3], ("git", "-C", str(s.root / "fork")))
        s.assertEqual([c[1:] for c in calls[1:]], [("pr", "list"), ("pr", "create"), ("pr", "view"), ("pr", "view"), ("pr", "view"), ("pr", "comment"), ("pr", "ready")])
        calls.clear(); ci[:] = ["failure"]
        with mock.patch.object(pub, "sh", fake_sh), s.assertRaises(SystemExit) as e:
            pub.upstream("s1", A)
        s.assertIn("stays draft, no comment", str(e.exception))
        s.assertNotIn(("gh", "pr", "comment"), calls); s.assertNotIn(("gh", "pr", "ready"), calls)


class R7(Sandbox):
    def test_view_has_only_the_seven_sections_and_states_are_facts(s):
        s.change("s1"); s.agreed("s1"); s.change("c1", "client"); hd.put("s1", "ask", {"text": "scope?"})
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertEqual(list(v), ["spawn", "card", "question", "message", "run", "goal", "change", "alert"])
        for line in v["change"]:
            state = line.split("]: ", 1)[1]
            s.assertTrue(" " in state or state == "done", line)                 # a sentence of facts, never a bare step name
        s.assertEqual(v["question"], ["s1: scope?"])
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(hd, "tick", lambda act: v):
            hd.cmd_tick([])
        for line in out.getvalue().splitlines():
            s.assertTrue(line.split(":")[0] in v, line)

    def test_show_prints_the_change_its_contract_and_every_verdict(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.verdict("s1", A, {"ok": "pass", "j1": "fail: no"}, F); s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hd.cmd_show(["s1"])
        o = out.getvalue()
        s.assertEqual((o.count("## verdict"), "## Contract" in o, "- ok | always passes" in o), (2, True, True))


class R5(Sandbox):
    def started(s, F, slug):
        hd.tick(s.ctx(F))
        run = [r for r in hd.runs() if r["change"] == slug][-1]
        hook.bind(payload(run, "ag-" + run["name"], "SubagentStart", s.root))
        return run

    def test_console_gone_ends_runs_and_brings_down_in_one_pass(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, containers={"server-s1": "running", "osrs-openrune": "running"})
        run = s.started(F, "s1")
        F.f["procs"] = set()                                                    # the console is gone
        v = hd.tick(s.ctx(F))
        r = [x for x in hd.runs() if x["name"] == run["name"]][0]
        s.assertEqual(r["reason"], "console died")
        s.assertEqual([a[1:] for a in F.ran if a[1:2] == ["down"]], [["down", "s1"]])
        s.assertNotIn("server-s1", F.f["containers"]); s.assertIn("osrs-openrune", F.f["containers"])
        s.assertTrue(any('"action": "down"' in l for l in open(s.root / "state" / "events.jsonl")))
        F.f["procs"] = {(7, "1")}
        s.assertEqual(len([x for x in hd.tick(s.ctx(F))["spawn"] if x.startswith("s1-")]), 1)   # listed again for a live console

    def test_a_run_the_head_stops_ends_and_frees_its_slot(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        run = s.started(F, "s1")
        hd.cmd_stop([run["name"]])
        r = [x for x in hd.runs() if x["name"] == run["name"]][0]
        s.assertEqual(r["reason"], "stopped by the head"); s.assertTrue(r["ended"])
        s.assertNotIn(run["name"], " ".join(hd.tick(s.ctx(F))["run"]))
        with s.assertRaises(SystemExit):
            hd.cmd_stop([run["name"]])                                          # an ended run is not stopped twice

    def test_dev_files_fix_outside_its_track_without_asking(s):
        s.change("c1", track="client"); s.agreed("c1", "client")
        hd.cmd_new(["h9", "--track", "harness", "--title", "tools fix", "--blocks", "c1"])
        hd.cmd_new(["h8", "--track", "harness", "--title", "another", "--blocks", "c1"])
        s.assertEqual(hd.defs("changes")["c1"]["deps"], ["h9", "h8"])
        s.assertEqual(hd.defs("changes")["c1"]["body"], "do it")
        s.assertEqual(s.state(Fake(**FACTS), "c1")["state"], "waiting on h9")      # held, no question raised
        with s.assertRaises(SystemExit):
            hd.cmd_new(["h7", "--track", "harness", "--title", "x", "--blocks", "nope"])
        s.assertNotIn("h7", hd.defs("changes"))

    def test_repair_logged_only_on_observed_effect_and_raised_once(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, containers={"server-s1": "running"}, down_works=False)
        hd.put("s1", "ask", {"text": "?"})                                       # no run is listed while a question is open
        v1 = hd.tick(s.ctx(F)); v2 = hd.tick(s.ctx(F)); v3 = hd.tick(s.ctx(F))
        s.assertFalse(any('"action": "down"' in l for l in open(s.root / "state" / "events.jsonl")))
        s.assertEqual([any("down had no effect" in a for a in v["alert"]) for v in (v1, v2, v3)], [False, True, False])
        s.assertEqual(hd.rec("s1", "repair-down")["attempts"], 3)
        F.f["down_works"] = True
        hd.tick(s.ctx(F))
        s.assertIsNone(hd.rec("s1", "repair-down"))                             # the effect observed: the count is gone, one event
        s.assertEqual(sum('"action": "down"' in l for l in open(s.root / "state" / "events.jsonl")), 1)

    def test_dead_script_reruns_once_then_raised(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))                                     # the build died without build.json: once more
        s.assertEqual([a[1] for a in F.spawned], ["build", "build"])
        v = hd.tick(s.ctx(F))
        s.assertEqual([a[1] for a in F.spawned], ["build", "build"])
        s.assertTrue(any("build died twice" in a for a in v["alert"]))

    def test_attempts_reset_on_new_args_or_a_landed_result(s):
        F = Fake(**FACTS)
        ctx = s.ctx(F)
        ctx.start("s1", "build", ["b", "T1"]); ctx.start("s1", "build", ["b", "T1"])
        ctx.start("s1", "build", ["b", "T1"])                                    # died twice on T1: raised, not rerun
        s.assertEqual(len(F.spawned), 2)
        ctx.start("s1", "build", ["b", "T2"])                                    # a new tree: one death is not two
        s.assertEqual(hd.rec("s1", "proc-build")["attempts"], 1)
        hd.put("s1", "build", {"T": "T2", "ok": True})                           # the result lands
        ctx.start("s1", "build", ["b", "T2"])
        s.assertEqual(hd.rec("s1", "proc-build")["attempts"], 1)
        script = s.root / "track.sh"; script.write_text("")
        ctx.start("s1", "build", [str(script), "T3"]); ctx.start("s1", "build", [str(script), "T3"])
        n = len(F.spawned); ctx.start("s1", "build", [str(script), "T3"])
        s.assertEqual(len(F.spawned), n)                                         # died twice on T3: raised
        pf = hd.STATE / "s1" / "proc-build.json"
        os.utime(script, ns=(pf.stat().st_mtime_ns + 10**9,) * 2)                # the script is fixed
        ctx.start("s1", "build", [str(script), "T3"])
        s.assertEqual(hd.rec("s1", "proc-build")["attempts"], 1)

    def test_yes_then_console_gone_still_ships(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        hd.put("live", "tree", {"tree": "x", "commit": C, "heads": [A]})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_approve(["s1", A])
        F.f["procs"] = set()                                                    # main is gone after the yes
        hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["upstream", "s1", A])
        s.assertTrue(F.spawned[-1][0].endswith("hd-public"))

    def test_missing_script_is_an_alert_not_a_crash(s):
        (s.root / "harness" / "goals" / "g1.md").write_text("---\nslug: g1\ntrack: client\ntarget: 100\n---\ngoal")
        F = Fake(**FACTS)
        F.spawn = lambda args, log, env=None: hd.Facts.spawn(F, [str(s.root / "nope" / "track.sh")] + args[1:], log, env)
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(a.startswith("g1: measure cannot start:") and "No such file" in a for a in v["alert"]))

    def test_a_tools_fix_reruns_a_failed_gate(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        hd.put("s1", "gate", {**hd.rec("s1", "gate"), "ok": False, "detail": "FAIL: ci: a tools bug"})
        s.assertEqual(s.state(F, "s1")["actor"], "dev")                      # the failure stands while the tools stand
        F.f["refs"] = {**F.f["refs"], "local/harness": B}                    # the tools fix ships
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["state"]), ("script", f"building {hd.rec('s1', 'build')['T'][:9]}"))
        hd.tick(s.ctx(F))
        s.assertEqual([x[1] for x in F.spawned], ["build"])                 # build and gate re-run under the new tools
        s.assertEqual(F.envs[0]["T"], f"{hd.rec('s1', 'handover')['T']}-{B[:12]}")
        hd.put("s1", "gate", {"T": F.envs[0]["T"], "ok": True})
        s.assertIn("s1", hd.integration(s.ctx(F))["names"])                  # the re-run gate still admits the hand-over to T_int

    def test_track_root_and_repair_on_the_tools_branch_worktree(s):
        c = hd.cfg()
        c["repos"]["client"]["tools"] = "client/harness-v8"
        s.assertEqual(hd.track_root(c, "client"), s.root / "client" / ".worktrees" / "harness-v8")
        s.assertEqual(hd.track_root(c, "server"), s.root / "fork" / ".worktrees" / "harness")
        F = Fake(**FACTS)
        hd.repairs(hd.Ctx(F, c), True)
        s.assertIn(["git", "-C", str(s.root / "client"), "worktree", "add", str(s.root / "client" / ".worktrees" / "harness-v8"), "client/harness-v8"], F.ran)

    def test_a_repo_without_the_noreply_identity_gets_it(s):
        repo = s.root / "central"; repo.mkdir(exist_ok=True); subprocess.run(["git", "init", "-q", str(repo)], check=True)
        c = hd.cfg(); c["repos"] = {"central": {**c["repos"]["central"], "path": str(repo)}}
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        with mock.patch.dict(os.environ, {**env, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}, clear=True):
            hd.repairs(hd.Ctx(hd.Facts(), c), True)
            r = subprocess.run(["git", "-C", str(repo), "commit-tree", "-m", "snapshot", "4b825dc642cb6eb9a060e54bf8d69288fbee4904"], capture_output=True, text=True)
            s.assertEqual(r.returncode, 0, r.stderr)                            # a commit with no per-run env
            s.assertEqual(subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%an <%ae>|%cn <%ce>", r.stdout.strip()], capture_output=True, text=True).stdout.strip(),
                          "|".join(["%s <%s>" % hd.AUTHOR] * 2))

    def test_docker_down_is_one_alert_and_no_script_starts(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, containers=None)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned, [])
        s.assertEqual(sum("docker unreachable" in a for a in v["alert"]), 1)

    def test_docker_down_lists_no_build_run_until_it_answers(s):
        s.change("s1"); s.agreed("s1"); s.change("p1", "harness")
        F = Fake(**FACTS)
        s.assertTrue([x for x in hd.tick(s.ctx(F))["spawn"] if x.startswith("s1-")])   # listed while docker answers
        F.f["containers"] = None
        v = hd.tick(s.ctx(F))
        s.assertFalse([x for x in v["spawn"] if x.startswith("s1-")])                  # the unspawned run ends, none is listed
        s.assertTrue([x for x in v["spawn"] if x.startswith("p1-")])                   # a harness run needs no docker
        s.assertEqual(sum("Docker Desktop is down" in a for a in v["alert"]), 1)
        F.f["containers"] = {}
        s.assertTrue([x for x in hd.tick(s.ctx(F))["spawn"] if x.startswith("s1-")])   # listed again once docker answers

    def test_second_ask_refused_while_one_open(s):
        s.change("s1")
        hd.cmd_ask(["s1", "which scope?"])
        with s.assertRaises(SystemExit) as e:
            hd.cmd_ask(["s1", "which scope?"])
        s.assertIn("already open", str(e.exception))
        hd.cmd_answer(["s1", "scope B"])
        s.assertIsNone(hd.rec("s1", "ask"))
        hd.cmd_ask(["s1", "another?"])                                          # after the answer, a new question may open

    def test_open_question_holds_gate_and_ship_until_answered(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F); hd.drop("s1", "gate")                                 # built, its gate due
        hd.cmd_ask(["s1", "hold before ship?"])
        hd.tick(s.ctx(F))
        s.assertEqual((s.state(F, "s1")["state"], F.spawned), ("question open: hold before ship?", []))
        hd.cmd_answer(["s1", "go"])
        hd.tick(s.ctx(F))
        s.assertEqual([a[1] for a in F.spawned], ["gate"])                      # the answer releases it


class R6(Sandbox):
    def test_devtools_servers_start_with_no_client(s):
        import subprocess
        repo = Path(__file__).parent.parent
        home = Path(tempfile.mkdtemp()); (home / "netstat.exe").write_text("#!/bin/sh\n"); (home / "netstat.exe").chmod(0o755)   # nothing listens
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_client_state", "arguments": {"port": 7781}}}]
        for name, srv in json.loads((repo / ".mcp.json").read_text())["mcpServers"].items():
            if "devtools" not in name:
                continue
            s.assertTrue(srv["args"][1].startswith("http://") or os.path.exists(srv["args"][1]), srv)   # the backend exists
            r = subprocess.run([str(repo / "mcp" / "devtools_bridge.py"), *srv["args"]], input="".join(json.dumps(m) + "\n" for m in msgs),
                               env={**os.environ, "HOME": str(home), "WINDOWS_SYSTEM32": str(home)}, capture_output=True, text=True)
            out = [json.loads(l) for l in r.stdout.splitlines()]
            s.assertEqual([("result" in o, "error" in o) for o in out], [(True, False), (True, False), (False, True)], r.stderr)
            s.assertIn("get_client_state", [t["name"] for t in out[1]["result"]["tools"]])
        shutil.rmtree(home, ignore_errors=True)

    def test_desktop_walk_to_reaches_a_far_tile_in_minimap_clicks(s):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bridge", Path(__file__).parent.parent / "mcp" / "devtools_bridge.py")
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        pos, water, clicks = [3222, 3218], {(3100, 3200)}, []
        ok = lambda v: {"result": {"content": [{"type": "text", "text": json.dumps(v)}]}}
        def backend(cmd, method, params):                              # a desktop at camera yaw 0, its minimap centred at 689,84
            n, a = params["name"], params["arguments"]
            if n == "dump_interface":
                return ok({"components": [{"contentType": 1338, "hidden": False, "bounds": {"x": 613, "y": 8, "width": 152, "height": 152}}]})
            if n == "get_client_state":
                return ok({"worldX": pos[0], "worldY": pos[1], "cameraYaw": 0})
            if n == "click":
                t = (pos[0] + round((a["x"] - 689) / 4), pos[1] - round((a["y"] - 84) / 4))
                s.assertLessEqual(max(abs(t[0] - pos[0]), abs(t[1] - pos[1])), b.STEP)   # every click on the minimap
                clicks.append(t)
                if t not in water:
                    pos[:] = t
                return ok("Clicked")
            if n == "wait_for":
                return ok({"met": a["condition"] == "idle" or max(abs(a["x"] - pos[0]), abs(a["y"] - pos[1])) <= a["range"]})
        with mock.patch.object(b, "backend", backend):
            r = b.walk(["http://127.0.0.1:7781/mcp"], {"name": "walk_to", "arguments": {"x": 3147, "y": 3178, "port": 7781}})
            s.assertEqual((pos, r["result"].get("isError")), ([3147, 3178], None), r)
            s.assertEqual(len(clicks), 7)                              # 75 tiles, 12 a click
            r = b.walk(["http://127.0.0.1:7781/mcp"], {"name": "walk_to", "arguments": {"x": 3100, "y": 3200}})
            s.assertTrue(r["result"]["isError"])                      # a tile it cannot reach: stops where it stood, says so
            s.assertIn("stuck", r["result"]["content"][0]["text"])

    def test_desktop_answer_names_a_dropped_session_and_a_hung_netstat_never_blocks(s):  # quest-sheepshearer-3: a call hung 30 min, then an idle logout
        import importlib.util, subprocess as sp
        spec = importlib.util.spec_from_file_location("bridge", Path(__file__).parent.parent / "mcp" / "devtools_bridge.py")
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        game = ["LOGGED_IN"]
        def backend(cmd, method, params):
            if params["name"] == "get_client_state":
                s.assertEqual(params["arguments"], {"port": 7786})
                return {"result": {"content": [{"type": "text", "text": json.dumps({"gameState": game[0]})}]}}
            return {"result": {"content": [{"type": "text", "text": "[]"}]}}
        out = []
        call = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_npcs", "arguments": {"port": 7786}}})
        with mock.patch.object(b, "backend", backend), mock.patch.object(b, "reply", lambda i, **r: out.append(r)):
            b.handle("desktop", ["http://127.0.0.1:7780/mcp"], call)
            game[0] = "LOGIN_SCREEN"
            b.handle("desktop", ["http://127.0.0.1:7780/mcp"], call)
        s.assertEqual(len(out[0]["result"]["content"]), 1)              # logged in: the answer as it came
        s.assertIn("7786 is at LOGIN_SCREEN", out[1]["result"]["content"][1]["text"])
        def hang(*a, **k):
            s.assertIn("timeout", k); raise sp.TimeoutExpired(a[0], k["timeout"])
        with mock.patch.object(b.subprocess, "run", hang), mock.patch.object(b.urllib.request, "urlopen", side_effect=OSError("refused")):
            s.assertIn("no desktop client answers", b.post("http://127.0.0.1:7780/mcp", "tools/call", {"name": "x", "arguments": {}})["error"]["message"])

    def test_harness_changes_dispatch_before_product_changes(s):
        s.change("s1", priority="P0"); s.agreed("s1")
        s.change("h1", track="harness", priority="P3"); s.agreed("h1", track="harness")
        c = json.loads((s.root / "hd.yaml").read_text()); c["agents"] = 1; (s.root / "hd.yaml").write_text(json.dumps(c))
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(Fake(**FACTS)))["spawn"]], ["h1-1"])

    def test_pr_changes_before_new_content_and_blockers_raised(s):
        for slug, k in (("q0", {"priority": "P0"}), ("p1", {"priority": "P1", "pr": 354}), ("q3", {"priority": "P3"}), ("q2", {"priority": "P2"})):
            s.change(slug, **k); s.agreed(slug)
        s.change("c3", track="client", priority="P3", deps=["q2"]); s.agreed("c3", track="client")
        c = json.loads((s.root / "hd.yaml").read_text()); c["agents"] = 1; (s.root / "hd.yaml").write_text(json.dumps(c))
        F = Fake(**FACTS)
        first = lambda: [x.split(" ")[0] for x in hd.tick(s.ctx(F), act=False)["change"]]
        s.assertEqual(first(), ["p1", "q2", "c3", "q0", "q3"])          # a PR's change, or a blocker (q2 holds c3), before new content, whatever its priority
        hd.put("p1", "state", {"state": "test server deploy blocked by q3's conflict"})
        v = hd.tick(s.ctx(F))
        s.assertEqual([x.split(" ")[0] for x in v["change"]][:2], ["p1", "q3"])   # the blocker rises to its blocked change's P1
        s.assertIn("q3 [server P1]", " ".join(v["change"]))
        s.assertEqual([x.split(":")[0] for x in v["spawn"]], ["p1-1"])

    def test_same_tree_never_builds_or_gates_twice(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        for _ in range(3):
            hd.tick(s.ctx(F))
        s.assertEqual(F.spawned, [])                                   # build and gate at T exist: no script runs again
        hd.put("s1", "gate", {"T": "other", "ok": True})               # a gate of another tree is no gate of this one
        hd.tick(s.ctx(F))
        s.assertEqual([x[1] for x in F.spawned], ["gate"])

    def test_same_head_and_contract_never_judges_twice(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        for _ in range(2):
            v = hd.tick(s.ctx(F))
        s.assertEqual([r for r in hd.runs() if r["role"] == "qa"], [])

    def test_agent_count_bounds_listing(s):
        for i in range(4):
            s.change(f"s{i}"); s.agreed(f"s{i}")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], **{f"fork/dev/s{i}": A for i in range(4)}}})
        v = hd.tick(s.ctx(F))
        s.assertEqual(len(v["spawn"]), 3)
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 3)

    def test_planner_listed_when_every_slot_is_taken(s):
        for i in range(3):
            s.change(f"s{i}"); s.agreed(f"s{i}")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], **{f"fork/dev/s{i}": A for i in range(3)}}})
        hd.tick(s.ctx(F))                                              # three dev runs fill the three slots
        s.change("s9", deps=["gone"])                                  # an alert
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("planner-") for x in v["spawn"]))
        s.assertEqual(len([r for r in hd.runs() if not r.get("ended") and r["role"] != "planner"]), 3)

    def test_unchanged_facts_append_no_event(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        n = sum(1 for _ in open(s.root / "state" / "events.jsonl"))
        for _ in range(3):
            hd.tick(s.ctx(F))
        s.assertEqual(sum(1 for _ in open(s.root / "state" / "events.jsonl")), n)

    def test_context_limit_hands_off_and_lists_successor(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hook.context_limit(payload(run, "ag1", "PostToolUse", s.root, usage=2, context=1000))
        s.assertEqual(out.getvalue(), "")                              # under the limit: silent
        with contextlib.redirect_stdout(out):
            hook.context_limit(payload(run, "ag1", "PostToolUse", s.root, usage=3, context=160000))
            hook.context_limit(payload(run, "ag1", "PostToolUse", s.root, usage=4, context=170000))
        s.assertEqual(out.getvalue().count("handoff.md"), 1)           # told once
        s.assertIn("push it to fork dev/s1", out.getvalue())           # its work in progress committed and pushed first
        told = out.getvalue()
        s.assertIn("start no new work", told)                          # the told run starts nothing new
        s.assertTrue(told.index("push it") < told.index("SendMessage") < told.index("`down s1`") < told.index("handoff.md"))   # a clean hand-off, in order
        s.assertTrue(hd.runs()[0]["handoff_told"])
        (s.root / "evidence" / "s1" / "handoff.md").write_text("done: half; next: the rest")
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, usage=4, context=170000, handback="run s1-1: handoff"))
        r = hd.runs()[0]
        s.assertEqual((r["record"], r["usage"]["turns"], r["usage"]["cache_read"] > 0, bool(r["transcript"])), (False, 4, True, True))
        v = hd.tick(s.ctx(F))
        s.assertEqual(len(v["spawn"]), 1)                              # the successor, with the hand-off in its brief
        s.assertIn("done: half; next: the rest", open(hd.runs()[1]["brief"]).read())
        s.assertIn(f"its work in progress: {A}", open(hd.runs()[1]["brief"]).read())   # the brief names the commit

    def test_idle_desktops_are_told_once_until_played_again(s):
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        import io, contextlib
        call = lambda tool="Bash": hook.idle_desktops({**payload(run, "ag1", "PostToolUse", s.root), "tool_name": tool})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for _ in range(20):
                call()
        s.assertEqual(out.getvalue(), "")                              # no desktops up: silent
        (s.root / "state" / "s1").mkdir(exist_ok=True)
        (s.root / "state" / "s1" / "up.json").write_text('{"desktops": "desktop1:7780"}')
        with contextlib.redirect_stdout(out):
            for _ in range(hook.IDLE_CALLS + 5):
                call()
        s.assertEqual(out.getvalue().count("`down s1`"), 1)            # a stretch without play: told once
        with contextlib.redirect_stdout(out):
            call("mcp__osrs-devtools-desktop__get_inventory")          # playing again starts the count again
            for _ in range(hook.IDLE_CALLS - 1):
                call()
        s.assertEqual(out.getvalue().count("`down s1`"), 1)
        with contextlib.redirect_stdout(out):
            call()
        s.assertEqual(out.getvalue().count("`down s1`"), 2)

    def test_three_context_limits_without_a_handover_are_raised(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        for i in range(3):
            s.assertFalse(any("context limit" in a for a in hd.tick(s.ctx(F))["alert"]))
            r = hd.runs()[-1]
            r.update(started=hd.now(), ended=hd.now(), handoff_told=160000)
            hd.save_run(r)
            (s.root / "evidence" / "s1" / "handoff.md").write_text(f"part {i}")
        s.assertTrue(any(a.startswith("s1: 3 runs reached the context limit") for a in hd.tick(s.ctx(F))["alert"]))
        p = next(r for r in hd.runs() if r["role"] == "planner")      # the planner hands back on the alert
        for r in hd.runs():
            r.update(listed="2000-01-01T00:00:00Z")
            if r is p or r["name"] == p["name"]:
                r.update(started="2001-01-01T00:00:00Z", ended="2001-01-01T00:00:00Z", record=True)
            hd.save_run(r)
        v = hd.tick(s.ctx(F))
        s.assertFalse(any("context limit" in a for a in v["alert"]))   # the count restarts at the planner's look
        s.assertEqual(sum(r["role"] == "planner" for r in hd.runs()), 1)   # and the planner is not listed again
        for i in range(4):                                             # the first is the run listed before the look
            r = [r for r in hd.runs() if r["role"] == "dev"][-1]
            r.update(started=hd.now(), ended=hd.now(), handoff_told=160000)
            hd.save_run(r)
            (s.root / "evidence" / "s1" / "handoff.md").write_text(f"later {i}")
            v = hd.tick(s.ctx(F))
        s.assertTrue(any(a.startswith("s1: 3 runs reached the context limit") for a in v["alert"]))   # three new limits re-raise it


    def test_main_past_context_limit_is_told_once_to_hand_off(s):
        import io, contextlib
        def main_payload(session, context):
            tp = s.root / f"main-{session}.jsonl"
            tp.write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "x",
                          "usage": {"input_tokens": 10, "cache_read_input_tokens": context}}}) + "\n")
            return {"hook_event_name": "PostToolUse", "session_id": session, "transcript_path": str(tp)}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hook.context_limit(main_payload("m1", 1000))
            s.assertEqual(out.getvalue(), "")                          # under the limit: silent
            hook.context_limit(main_payload("m1", 160000))
            hook.context_limit(main_payload("m1", 170000))
            s.assertEqual(out.getvalue().count("start prompt"), 1)  # told once
            hook.context_limit(main_payload("m2", 160000))
        s.assertEqual(out.getvalue().count("start prompt"), 2)      # a fresh main session is told for itself
        with contextlib.redirect_stdout(out):                          # the orchestrator is no main
            hook.context_limit({**main_payload("m3", 160000), "agent_type": "orchestrator"})
        s.assertEqual(out.getvalue().count("start prompt"), 2)


    def test_malformed_definition_is_one_alert(s):
        s.change("s1"); s.agreed("s1")
        (s.root / "harness" / "changes" / "bad.md").write_text("---\ntitle: [unclosed\n---\n")
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertTrue(any(a.startswith("definition skipped: bad.md") for a in v["alert"]))
        s.assertEqual(len([x for x in v["spawn"] if x.startswith("s1-")]), 1)   # the pass went on for the others (the alert also lists the planner)
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertEqual(sum(a.startswith("definition skipped") for a in v["alert"]), 1)   # once per pass, not growing

    def test_event_log_rotates(s):
        with mock.patch.object(hd, "event", hd.event):
            hd.event(action="x")
            big = s.root / "state" / "events.jsonl"
            big.write_text("x" * 20_000_001)
            hd.event(action="y")
        s.assertTrue((s.root / "state" / "events.1.jsonl").exists())
        s.assertFalse(big.exists())


class R8(Sandbox):
    def test_the_pass_rebases_a_carried_tools_head_its_branch_moved_past(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        fork = str(s.root / "fork")
        F = Fake(refs={"HEAD": B, "harness/h1": A, f"{fork}:harness/h1": C}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)}, anc={(C, "local/harness")})
        s.gated("h1", F)
        F.f["anc"] = set()                                                       # another change shipped: local/harness moved past C
        F.f["merges"][("local/harness", C)] = ("conflict", "CONFLICT (content): tools/x")
        st = s.state(F, "h1")
        s.assertEqual((st["actor"], st["detail"]), ("dev", "CONFLICT (content): tools/x"))   # a conflict is the dev's
        del F.f["merges"][("local/harness", C)]; F.f["rebases"] = {"harness/h1": ("ok", D)}
        st = s.state(F, "h1")
        s.assertEqual(st["actor"], "script"); st["act"]()                        # no conflict: the pass rebases, no dev run
        s.assertIn(["rebase", fork, "harness/h1", "local/harness"], F.ran)
        F.f["refs"][f"{fork}:harness/h1"] = D; F.f["anc"] = {(D, "local/harness")}
        s.assertEqual((hd.rec("h1", "handover")["tools"], hd.rec("h1", "handover")["T"]), ({"fork": D}, TA + "+" + D[:12]))
        s.assertEqual(s.state(F, "h1")["state"], f"building {TA[:9]}")         # the new head is recorded and re-built, re-gated

    def test_a_server_build_includes_its_central_dependencies(s):
        s.change("z1", "central"); s.agreed("z1", "central"); s.change("s1", deps=["z1"]); s.agreed("s1"); s.change("s2"); s.agreed("s2")
        E = "e" * 40
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/z1": D, "fork/dev/s2": C}, "trees": {**FACTS["trees"], D: TC, C: TC, E: "te" * 20},
                    "merges": {(B, D): ("ok", E), (B, A): ("ok", A), (B, C): ("ok", C)}})
        s.gated("z1", F)
        ho = s.gated("s1", F)
        s.assertEqual(ho["T"], TA + "-c" + E[:12])                               # Central's base and z1 merged join s1's key
        s.assertEqual(s.ctx(F).env(hd.defs("changes")["s1"], A, A, ho["T"])["CENTRAL"], f"{s.root / 'central'}:{E}")
        s.assertEqual(s.ctx(F).env(hd.defs("changes")["s2"], C, C, TC)["CENTRAL"], "")   # no Central dependency: the published Central
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["central"], t["tree"]), (E, TA + "-c" + E[:12]))    # the test server carries the Central its heads need

    def test_a_game_client_is_named_mobile_or_desktop(s):  # the three source docs, the track rules and the roles
        import re
        root = Path(__file__).parent.parent
        for f in ["docs/PROBLEM.md", "docs/PRD.md", "docs/ARCHITECTURE.md", "tools/track.md", "CLAUDE.md", *map(str, root.glob(".claude/agents/*.md"))]:
            s.assertIsNone(re.search(r"(?i)\bdevices?\b|device_login|\bclient windows?\b|\b(?:desktop|logged-in|N) clients\b", (root / f).read_text()), f)

    def test_ship_fast_forwards_the_live_branch_or_regates(s):
        import subprocess
        tmp = Path(tempfile.mkdtemp()); origin, repo = tmp / "origin.git", tmp / "live"
        git = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "v8", str(repo)], check=True)
        (repo / "tools").mkdir(); shutil.copy(Path(__file__).parent.parent / "tools" / "track.sh", repo / "tools")
        git("add", "."); git("commit", "-qm", "base"); git("remote", "add", "origin", str(origin)); git("push", "-q", "origin", "v8")
        commit = lambda msg: (git("commit", "-q", "--allow-empty", "-m", msg), git("rev-parse", "HEAD"))[1]
        git("checkout", "-q", "--detach"); T1 = commit("T1"); git("checkout", "-q", "v8")
        (repo / "harness" / "changes").mkdir(parents=True); (repo / "harness" / "changes" / "new.md").write_text("an uncommitted definition")
        ship = lambda tc: subprocess.run([str(repo / "tools" / "track.sh"), "ship", "s1", tc], env={**os.environ, "HD_ROOT": str(s.root)}, capture_output=True, text=True)
        r = ship(T1)
        s.assertEqual((r.returncode, git("rev-parse", "v8"), git("ls-remote", "origin", "v8").split()[0]), (0, T1, T1), r.stdout + r.stderr)
        git("checkout", "-q", "--detach"); T2 = commit("T2 on T1"); git("checkout", "-q", "v8"); moved = commit("the head's own commit")
        hd.put("s1", "proc-ship", {"pid": 1, "start": "x", "attempts": 1})
        r = ship(T2)                                                                  # the live branch moved past T2's base
        s.assertEqual((r.returncode, git("rev-parse", "v8"), hd.rec("s1", "proc-ship")), (0, moved, None), r.stdout + r.stderr)   # untouched; ship starts afresh on the re-gated T
        shutil.rmtree(tmp, ignore_errors=True)

    def test_the_suite_ignores_the_gates_tools(s):
        tmp = Path(tempfile.mkdtemp()); fork = tmp / "fork"
        run = lambda *a: subprocess.run(["git", "-C", str(fork), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "init", "-q", "-b", "local/harness", str(fork)], check=True); run("commit", "-q", "--allow-empty", "-m", "base")
        subprocess.run(["git", "init", "-q", "--bare", str(tmp / "fork.git")], check=True); run("remote", "add", "fork", str(tmp / "fork.git"))
        run("checkout", "-q", "--orphan", "harness/s1"); run("commit", "-q", "--allow-empty", "-m", "not a fast-forward"); C = run("rev-parse", "HEAD")
        run("checkout", "-q", "local/harness"); before = run("rev-parse", "local/harness")
        r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_hd.R8.test_ship_fast_forwards_the_live_branch_or_regates"], cwd=Path(__file__).parent.parent,
                           env={**os.environ, "TOOLS": f"{fork}:local/harness:{C}:AlexPerrin/OpenRune-Server", "T": "t", "TCOMMIT": C}, capture_output=True, text=True)
        s.assertEqual((r.returncode, run("rev-parse", "local/harness"), run("ls-remote", "fork")), (0, before, ""), r.stdout + r.stderr)
        shutil.rmtree(tmp, ignore_errors=True)

    def test_ship_moves_nothing_when_a_tools_branch_moved(s):
        import subprocess
        tmp = Path(tempfile.mkdtemp()); origin, repo, fork = tmp / "origin.git", tmp / "live", tmp / "fork"
        run = lambda d, *a: subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        commit = lambda d, msg: (run(d, "commit", "-q", "--allow-empty", "-m", msg), run(d, "rev-parse", "HEAD"))[1]
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        for d, b in ((repo, "v8"), (fork, "main")):
            subprocess.run(["git", "init", "-q", "-b", b, str(d)], check=True); commit(d, "base")
        (repo / "tools").mkdir(); shutil.copy(Path(__file__).parent.parent / "tools" / "track.sh", repo / "tools")
        run(repo, "add", "."); run(repo, "commit", "-qm", "tools"); run(repo, "remote", "add", "origin", str(origin)); run(repo, "push", "-q", "origin", "v8")
        for name, url in (("origin", tmp / "OpenRune" / "OpenRune-Server.git"), ("fork", tmp / "AlexPerrin" / "OpenRune-Server.git")):   # upstream is origin
            subprocess.run(["git", "init", "-q", "--bare", str(url)], check=True); run(fork, "remote", "add", name, str(url))
        run(fork, "branch", "local/harness"); wt = fork / ".worktrees" / "harness"; run(fork, "worktree", "add", "-q", str(wt), "local/harness")
        run(fork, "checkout", "-q", "-b", "harness/s1", "local/harness"); C = commit(fork, "carried fix"); run(fork, "checkout", "-q", "main")
        run(repo, "checkout", "-q", "--detach"); T = commit(repo, "T"); run(repo, "checkout", "-q", "v8"); live = run(repo, "rev-parse", "v8")
        ship = lambda: subprocess.run([str(repo / "tools" / "track.sh"), "ship", "s1", T], env={**os.environ, "HD_ROOT": str(s.root), "TOOLS": f"{fork}:local/harness:{C}:AlexPerrin/OpenRune-Server"}, capture_output=True, text=True)
        moved = commit(wt, "another change shipped to local/harness")
        hd.put("s1", "gate", {"T": "t", "ok": True}); hd.put("s1", "proc-ship", {"pid": 1, "start": "x", "attempts": 1})
        r = ship()
        s.assertEqual((r.returncode, run(repo, "rev-parse", "v8"), run(fork, "rev-parse", "local/harness"), hd.rec("s1", "gate"), hd.rec("s1", "proc-ship")),
                      (0, live, moved, None, None), r.stdout + r.stderr)   # nothing moved; the gate re-runs and check-tools sends the dev to merge
        run(wt, "reset", "-q", "--hard", "HEAD~1")
        r = ship()
        s.assertEqual((r.returncode, run(repo, "rev-parse", "v8"), run(fork, "rev-parse", "local/harness")), (0, T, C), r.stdout + r.stderr)
        s.assertEqual((run(fork, "ls-remote", "fork", "local/harness").split()[:1], run(fork, "ls-remote", "origin")), ([C], ""))   # pushed to the fork, never upstream
        shutil.rmtree(tmp, ignore_errors=True)

    def test_harness_build_refuses_without_the_loops_env(s):
        import subprocess
        script = Path(__file__).parent.parent / "tools" / "track.sh"
        r = subprocess.run([str(script), "build", "s1", "HEAD"], env={**os.environ, "HD_ROOT": str(s.root)}, capture_output=True, text=True)
        s.assertEqual((r.returncode, hd.rec("s1", "build")), (2, None), r.stdout + r.stderr)   # no record written, no copy moved

    def test_harness_key_leaves_out_definitions(s):
        import subprocess
        repo = Path(tempfile.mkdtemp())
        git = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q"); (repo / "hd.py").write_text("v1"); git("add", "."); git("commit", "-qm", "code")
        c1 = git("rev-parse", "HEAD")
        (repo / "harness" / "changes").mkdir(parents=True); (repo / "harness" / "changes" / "x.md").write_text("a definition")
        git("add", "."); git("commit", "-qm", "harness: change x"); c2 = git("rev-parse", "HEAD")
        (repo / "hd.py").write_text("v2"); git("commit", "-qam", "code moves"); c3 = git("rev-parse", "HEAD")
        s.change("h1", track="harness")
        ctx = hd.Ctx(hd.Facts(), {**hd.cfg(), "repos": {**hd.cfg()["repos"], "harness": {"name": "o/h", "path": str(repo)}}})
        k = [ctx.tree(hd.defs("changes")["h1"], c) for c in (c1, c2, c3)]
        s.assertEqual((k[0] == k[1], k[1] == k[2]), (True, False))                 # a definition commit keeps the key; code moves it
        s.assertNotEqual(hd.Facts().tree(str(repo), c1), hd.Facts().tree(str(repo), c2))   # other tracks: the plain tree sha
        shutil.rmtree(repo, ignore_errors=True)

    def test_tree_is_merge_of_base_deps_head(s):
        s.change("s1"); s.agreed("s1"); s.change("s2", deps=["s1"]); s.agreed("s2")
        hd.put("live", "tree", {"tree": "x", "commit": D, "heads": [A]})            # s1 live on the test server, not upstream
        E = "e" * 40
        F = Fake(refs={"origin/HEAD": B, "fork/dev/s1": A, "fork/dev/s2": C}, trees={E: "te" * 20}, merges={(B, A): ("ok", D), (D, C): ("ok", E)})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s2"])
        s.assertEqual((hd.rec("s2", "handover")["commit"], hd.rec("s2", "handover")["T"]), (E, "te" * 20))   # base, then s1, then s2
        s.change("h1", "harness"); s.change("s3", deps=["h1"]); s.agreed("s3")       # a harness dep is in another repo: not merged
        F.f["refs"].update({"harness/h1": "h" * 40, "fork/dev/s3": C}); F.f["merges"][(B, C)] = ("ok", E)
        s.assertEqual(s.ctx(F).T(hd.defs("changes")["s3"], C), ("ok", E))

    def test_t_commit_is_dated_from_its_newest_parent(s):
        import subprocess
        repo = Path(tempfile.mkdtemp()) / "r"
        git = lambda d, *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True,
                                           check=True, env={**os.environ, "GIT_AUTHOR_DATE": d, "GIT_COMMITTER_DATE": d}).stdout.strip()
        subprocess.run(["git", "init", "-q", "-b", "v8", str(repo)], check=True)
        git("@1700000000 +0000", "commit", "-q", "--allow-empty", "-m", "root")
        git("@1700000100 +0000", "commit", "-q", "--allow-empty", "-m", "base"); base = git("", "rev-parse", "HEAD")
        git("", "checkout", "-q", "HEAD~1"); git("@1700000200 +0000", "commit", "-q", "--allow-empty", "-m", "head"); head = git("", "rev-parse", "HEAD")
        T1, T2 = (hd.Facts().merge(str(repo), base, head, "T") for _ in range(2))
        s.assertEqual(T1, T2)                                                       # the same inputs give the same commit
        s.assertEqual(git("", "show", "-s", "--format=%at %ct", T1[1]), "1700000200 1700000200")

    def test_conflict_lists_dev(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "merges": {(B, A): ("conflict", "CONFLICT (content): Merge conflict in x.kt")}})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1"])
        s.assertIn("x.kt", str(e.exception))
        hd.put("s1", "handover", {"head": A, "T": "old", "commit": "old"})          # a hand-over from before the base moved
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["state"]), ("dev", "tree conflict: dev"))

    def integration_fixture(s, with_ref):
        P_, Q, M, R = "p" * 40, "q" * 40, "m" * 40, "r" * 40
        s.change("s1"); s.agreed("s1")
        c = json.loads((s.root / "hd.yaml").read_text()); c["pins"] = ["local/x"]; (s.root / "hd.yaml").write_text(json.dumps(c))
        refs = {"origin/HEAD": B, "fork/dev/s1": A, "fork/local/x": P_}
        if with_ref:
            refs[f"fork/local/merge/{A[:7]}-{P_[:7]}"] = M
        F = Fake(refs=refs, trees={A: TA, R: "tr" * 20}, merges={(B, A): ("ok", A), (B, P_): ("ok", Q), (Q, A): ("conflict", "CONFLICT (content): y.kt"), (Q, M): ("ok", R)})
        s.gated("s1", F)
        return F, R

    def test_merge_ref_stands_in_for_pair_in_integration(s):
        F, R = s.integration_fixture(with_ref=True)
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["commit"], t["names"]), (R, ["local/x", "s1"]))
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["ship", "integration", R])
        s.assertEqual(F.envs[-1]["T"], "tr" * 20)
        s.assertIn("s1 [server P2]: test server: deploying trtrtrtrt", v["change"])
        F.f["procs"] = {(7, "1"), (4242, "99")}                                      # the deploy is running: not started again
        hd.tick(s.ctx(F)); s.assertEqual(len([x for x in F.spawned if x[1] == "ship"]), 1)
        hd.put("live", "tree", {"tree": "tr" * 20, "commit": R, "heads": [A], "names": ["local/x", "s1"]})
        s.assertEqual(s.state(F, "s1")["state"], "live on the test server; waiting for the user's yes")

    def test_conflict_without_a_resolution_is_the_younger_change_s(s):
        F, R = s.integration_fixture(with_ref=False)
        F.f["trees"]["q" * 40] = "tq" * 20                                          # the base and the pin merge on without s1
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["conflicts"][0]["conflict"], t["conflicts"][0]["with"]), ("s1", ["local/x"]))
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))
        s.assertIn("local/merge/<yours7>-<theirs7>", open(hd.runs()[0]["brief"]).read())
        s.assertEqual([x for x in F.spawned if x[1] == "ship"], [])

    def test_a_lower_priority_conflict_leaves_the_higher_priority_tree_to_deploy(s):
        s.change("lo", priority="P3"); s.agreed("lo"); s.change("hi", priority="P1"); s.agreed("hi")   # the P3 is the older
        F = Fake(refs={"origin/HEAD": B, "fork/dev/lo": C, "fork/dev/hi": A}, trees={A: TA, B: TB, C: TC},
                 merges={(B, A): ("ok", A), (B, C): ("ok", C), (A, C): ("conflict", "CONFLICT (content): q.kt"), (C, A): ("conflict", "CONFLICT (content): q.kt")})
        for slug, h in (("lo", C), ("hi", A)):
            s.gated(slug, F)
            (s.root / "state" / slug / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": h, "contract": hd.contract(slug)["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["names"], [(c["conflict"], c["with"]) for c in t["conflicts"]]), (["hi"], [("lo", ["hi"])]))   # priority first, the P3 left out
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["ship", "integration", A])              # the P1 deploys
        s.assertTrue(any(x.startswith("lo-") for x in v["spawn"]))                 # the P3 resolves its own conflict

    def test_tree_of_a_snapshot(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "trees": {**FACTS["trees"], D: "td" * 20}, "merges": {(B, C): ("ok", D)}})
        import io, contextlib
        out = io.StringIO()
        with mock.patch.object(hd, "Facts", lambda: F), contextlib.redirect_stdout(out):
            hd.cmd_tree(["s1", C])                                                   # a working-copy snapshot, not the dev ref
        s.assertEqual(out.getvalue().split(), [D, "td" * 20])

    def test_pin_conflict_is_the_oldest_gated_change_s_dev(s):
        F, R = s.integration_fixture(with_ref=False)
        c = json.loads((s.root / "hd.yaml").read_text()); c["pins"] = ["local/x", "local/y"]; (s.root / "hd.yaml").write_text(json.dumps(c))
        F.f["refs"]["fork/local/y"] = "y" * 40; F.f["merges"][("q" * 40, "y" * 40)] = ("conflict", "CONFLICT (content): z.kt")
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))
        s.assertIn(f"local/merge/{'y' * 7}-{B[:7]}", open(hd.runs()[0]["brief"]).read())
        s.assertEqual([a for a in v["alert"] if a.startswith("pin ")], [])

    def test_pin_conflict_owned_by_a_change_at_the_deploy_step(s):
        s.change("s0"); s.agreed("s0")                                               # older, gated, its review due: not at the deploy
        F, R = s.integration_fixture(with_ref=False)
        F.f["refs"]["fork/dev/s0"] = C; F.f["trees"][C] = TC
        s.gated("s0", F)
        F.f["merges"][(B, "p" * 40)] = ("conflict", "CONFLICT (content): MusicTabScript.kt")
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        s.assertEqual(s.state(F, "s0")["state"], "review due")
        s.assertEqual(hd.integration(s.ctx(F))["change"]["slug"], "s1")
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))

    def test_pin_base_conflict_resolved_by_its_merge_ref(s):
        F, R = s.integration_fixture(with_ref=False)
        P_, M2 = "p" * 40, "n" * 40
        F.f["merges"][(B, P_)] = ("conflict", "CONFLICT (content): MusicTabScript.kt")
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["conflict"], t["change"]["slug"], t["with"]), ("local/x", "s1", []))  # the base alone: owned, not an alert
        F.f["refs"][f"fork/local/merge/{P_[:7]}-{B[:7]}"] = M2; F.f["merges"][(B, M2)] = ("ok", "q" * 40); F.f["merges"][("q" * 40, A)] = ("ok", R)
        s.assertEqual(hd.integration(s.ctx(F))["names"], ["local/x", "s1"])
        F.f["refs"]["origin/HEAD"] = C                                               # the base moves: the resolution no longer binds
        F.f["merges"][(C, P_)] = ("conflict", "CONFLICT (content): MusicTabScript.kt")
        s.assertEqual(hd.integration(s.ctx(F))["conflict"], "local/x")

    def test_every_pin_conflict_in_one_pass(s):
        F, R = s.integration_fixture(with_ref=False)
        P_, Y = "p" * 40, "y" * 40
        c = json.loads((s.root / "hd.yaml").read_text()); c["pins"] = ["local/x", "local/y"]; (s.root / "hd.yaml").write_text(json.dumps(c))
        F.f["refs"]["fork/local/y"] = Y
        F.f["merges"][(B, P_)] = ("conflict", "CONFLICT (content): MusicTabScript.kt"); F.f["merges"][(B, Y)] = ("conflict", "CONFLICT (content): z.kt")
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual([(x["conflict"], x["change"]["slug"]) for x in t["conflicts"]], [("local/x", "s1"), ("local/y", "s1")])
        v = hd.tick(s.ctx(F))
        s.assertEqual(len([x for x in v["spawn"] if x.startswith("s1-")]), 1)       # one dev run for both
        brief = open(hd.runs()[0]["brief"]).read()
        for ref in (f"local/merge/{P_[:7]}-{B[:7]}", f"local/merge/{Y[:7]}-{B[:7]}", "MusicTabScript.kt", "z.kt",
                    f"base {B[:7]}, then local/x {P_[:7]}, local/y {Y[:7]}, s1 {A[:7]}"):
            s.assertIn(ref, brief)

    def test_artefacts_named_by_change(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["build", "s1", A])
        s.assertEqual((F.envs[-1]["SLUG"], F.envs[-1]["T"]), ("s1", TA))
        s.assertTrue((s.root / "state" / "s1" / "proc-build.json").exists())


class EndToEnd(unittest.TestCase):
    """A harness change through the real loop: real git, the real track script, real processes, no fakes."""

    @unittest.skipIf(os.environ.get("HD_E2E"), "nested")
    def test_harness_change_defined_to_live(s):
        import subprocess, time
        src = Path(__file__).resolve().parent.parent
        snap = subprocess.run(["git", "-C", str(src), "stash", "create"], capture_output=True, text=True).stdout.strip() or "HEAD"
        tmp = Path(tempfile.mkdtemp()); origin, repo, root = tmp / "origin.git", tmp / "harness", tmp / "root"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(src), str(repo)], check=True)
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout.strip()
        git("checkout", "-q", "-B", "main", snap); git("remote", "set-url", "origin", str(origin)); git("push", "-q", "origin", "main")
        for d in ("harness/changes", "harness/goals", "evidence/e2e"):
            (root / d).mkdir(parents=True)
        (root / "hd.yaml").write_text(json.dumps({"repos": {"client": {"name": "o/c", "path": str(repo)}, "fork": {"name": "o/f", "path": str(repo)}, "harness": {"name": "o/h", "path": str(repo)}}, "agents": 3, "pins": []}))
        (root / "harness" / "changes" / "e2e.md").write_text("---\nslug: e2e\ntrack: harness\ntitle: e2e\n---\nadd a line to the README")
        (root / "evidence" / "e2e" / "note.txt").write_text("evidence")
        git("worktree", "add", "-q", str(repo / ".worktrees" / "e2e"), "-b", "harness/e2e", "main")   # the dev's clone
        wt = repo / ".worktrees" / "e2e"
        (wt / "README.md").write_text((wt / "README.md").read_text() + "\ne2e\n")
        subprocess.run(["git", "-C", str(wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-am", "e2e: a line"], check=True)
        head = subprocess.run(["git", "-C", str(wt), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        env = {**os.environ, "HD_ROOT": str(root), "HD_E2E": "1"}
        hd_ = lambda *a: subprocess.run([sys.executable, str(src / "hd.py"), *a], env=env, capture_output=True, text=True)
        s.assertIn("contract: seed rows pending", hd_("tick").stdout)
        v = hd_("tick").stdout
        s.assertIn("dev run due", v); s.assertIn("spawn: e2e-1", v)
        r = hd_("handover", "e2e"); s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        def until(state):
            for _ in range(90):
                v = hd_("tick").stdout
                if state in v:
                    return v
                time.sleep(1)
            s.fail(f"never reached {state!r}; last view:\n{v}\n{(root / 'state' / 'e2e' / 'gate.json').read_text() if (root / 'state' / 'e2e' / 'gate.json').exists() else ''}")
        until("gate on")
        until("shipping")
        until("e2e [harness P2]: done")
        s.assertEqual(subprocess.run(["git", "-C", str(origin), "merge-base", "--is-ancestor", head, "main"]).returncode, 0)   # live on the target
        events = (root / "state" / "events.jsonl").read_text()
        s.assertEqual((events.count('"state": "shipping"'), events.count('"state": "done"')), (1, 1))                        # edges only
        for d in ("e2e", "e2e-build"):
            subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(repo / ".worktrees" / d)], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


class Tools(unittest.TestCase):
    """The harness track script against this repo itself."""

    def test_check_tests_keeps_the_verdict_and_failures(s):
        import subprocess
        build = Path(tempfile.mkdtemp()); (build / "tests").mkdir()
        (build / "tests" / "test_x.py").write_text("import unittest, sys\nclass X(unittest.TestCase):\n    def test_a(s): s.fail('boom')\n"
                                                   "    def test_b(s): sys.stderr.write('noise\\n' * 20)\n")
        r = subprocess.run([str(Path(__file__).parent.parent / "tools" / "track.sh"), "check-tests"], env={**os.environ, "BUILD": str(build)}, capture_output=True, text=True)
        s.assertNotEqual(r.returncode, 0)
        s.assertEqual([l.split()[0] for l in r.stdout.splitlines()], ["FAIL:", "Ran", "FAILED"], r.stdout)   # no noise, nothing lost
        shutil.rmtree(build, ignore_errors=True)

    def test_check_docs_and_gate_rows(s):
        import subprocess
        repo = Path(__file__).parent.parent
        s.assertEqual(subprocess.run([str(repo / "tools" / "track.sh"), "check-docs"], cwd=repo, env={**os.environ, "BUILD": str(repo)}, capture_output=True, text=True).returncode, 0)
        root = Path(tempfile.mkdtemp())
        for d in ("harness/changes", "harness/goals", "evidence/g1", "tools"):
            (root / d).mkdir(parents=True)
        (root / "hd.yaml").write_text(json.dumps({"repos": {"client": {"name": "o/c", "path": str(repo)}, "fork": {"name": "o/f", "path": str(repo)}, "harness": {"name": "o/h", "path": str(repo)}}, "agents": 3, "pins": []}))
        (root / "harness" / "changes" / "g1.md").write_text("---\nslug: g1\ntrack: harness\n---\n")
        (root / "evidence" / "g1" / "contract.md").write_text("agreed: x\n- a | fine | check: true\n- b | injected | check: rm -rf /\n- c | script | gate: tools/track.sh check-docs\n")
        snap = subprocess.run(["git", "-C", str(repo), "stash", "create"], capture_output=True, text=True).stdout.strip() or "HEAD"
        r = subprocess.run([str(repo / "tools" / "track.sh"), "gate", "g1", snap], cwd=repo, env={**os.environ, "HD_ROOT": str(root), "T": "t", "EVIDENCE": str(root / "evidence" / "g1")}, capture_output=True, text=True)
        rec = json.loads((root / "state" / "g1" / "gate.json").read_text())
        s.assertEqual((r.returncode, rec["ok"]), (0, False), r.stderr)
        s.assertIn("FAIL: b: false # refused", rec["detail"]); s.assertIn("ok: a: true", rec["detail"]); s.assertIn("ok: c: tools/track.sh check-docs", rec["detail"])
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(repo / ".worktrees" / "g1-build")], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


class R3(Sandbox):
    def test_no_contract_lists_contract_step_not_dev(s):
        s.change("s1")
        F = Fake(**FACTS)
        st = s.state(F, "s1")
        s.assertEqual(st["actor"], "script")
        st["act"]()
        s.assertIn("- ok | always passes", (s.root / "evidence" / "s1" / "contract.md").read_text())
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["mode"]), ("qa", "contract"))
        s.change("c1", "client")
        st = s.state(F, "c1"); st["act"]()
        s.assertEqual(s.state(F, "c1")["actor"], "dev")  # derived contract: straight to the dev

    def test_a_contract_row_needs_no_dependent_change(s):  # the contract writer proves a change through its own build and its dependencies
        qa = (Path(__file__).parent.parent / ".claude" / "agents" / "qa.md").read_text().replace("\n", " ")
        s.assertIn("a proof that needs a change depending on this one is that change's row", qa)

    def test_merged_change_is_done_before_any_contract(s):
        s.change("s1")
        F = Fake(**{**FACTS, "anc": {(B, A)}})                          # upstream main holds the head: nothing to contract
        s.assertEqual(s.state(F, "s1")["state"], "done")

    def test_harness_change_carries_its_tools_commits(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        fork = str(s.root / "fork")
        F = Fake(refs={"HEAD": B, "harness/h1": A, f"{fork}:harness/h1": C}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["h1"])
        s.assertIn("does not descend from local/harness", str(e.exception))      # it must land as a fast-forward
        F.f["anc"] = {(C, "local/harness")}
        ho = s.gated("h1", F)
        s.assertEqual((ho["tools"], ho["T"]), ({"fork": C}, TA + "+" + C[:12]))  # build and gate are keyed by the carried head too
        hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1], "ship"); s.assertEqual(F.envs[-1]["TOOLS"], f"{fork}:local/harness:{C}:o/f")
        F.f["refs"][f"{fork}:harness/h1"] = D
        s.assertEqual(s.state(F, "h1")["actor"], "dev")                          # a moved tools ref is handed over again
        F.f["refs"][f"{fork}:harness/h1"] = C; F.f["anc"].add((B, A))
        s.assertEqual(s.state(F, "h1")["state"], "shipping")                     # main holds the head, the tools branch not yet
        F.f["anc"].add(("local/harness", C))
        s.assertEqual(s.state(F, "h1")["state"], "done")

    def test_handover_refused_on_failing_script_row(s):
        s.change("s1"); s.agreed("s1", extra="- bad | fails | check: false\n")
        F = Fake(**FACTS, rows={"false": (1, "nope")})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1"])
        s.assertIn("row bad failed", str(e.exception))
        s.assertIsNone(hd.rec("s1", "handover"))

    def test_answer_waives_a_script_row(s):
        s.change("s1"); s.agreed("s1", extra="- bad | fails | check: false\n")
        with s.assertRaises(SystemExit):
            hd.cmd_answer(["s1", "--waive", "j1", "not a script row"])
        hd.cmd_answer(["s1", "--waive", "bad", "no new tests, per decision 7"])
        F = Fake(**FACTS, rows={"false": (1, "nope")})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        s.assertEqual(F.ran, ["true"])
        s.assertEqual(hd.rec("s1", "handover")["head"], A)

    def test_handover_reads_pushed_ref_takes_no_sha(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        s.assertEqual(hd.rec("s1", "handover")["head"], A)
        s.assertEqual(hd.rec("s1", "handover")["T"], TA)
        s.assertEqual(F.ran, ["true"])
        with mock.patch.object(hd, "Facts", lambda: Fake(**{**FACTS, "refs": {"origin/HEAD": B}})), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1"])
        s.assertIn("does not exist", str(e.exception))

    def test_harness_dev_ref_stays_local(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})  # no remote ref at all
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1"])
        s.assertEqual(hd.rec("h1", "handover")["head"], A)
        s.assertEqual(hd.TRACK["harness"]["dev"], "harness/{slug}")                 # the local branch, so a rebase needs no force push
        repo = Path(__file__).parent.parent
        for doc in ("tools/track.md", ".claude/agents/dev.md"):
            s.assertIn("never push it", (repo / doc).read_text().replace("\n", " "), doc)

    def test_verdict_refused_when_row_missing(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with s.assertRaises(SystemExit) as e:
            s.verdict("s1", A, {"ok": "pass"}, F)
        s.assertIn("rows missing: j1", str(e.exception))
        with s.assertRaises(SystemExit) as e:
            s.verdict("s1", A, {"ok": "pass", "j1": "maybe"}, F)
        s.assertIn("'pass', 'fail", str(e.exception))
        s.assertEqual(hd.verdicts("s1"), [])

    def test_an_unjudged_row_never_passes(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        with s.assertRaises(SystemExit) as e:                                    # a PASS verdict judges every row
            s.verdict("s1", A, {"ok": "pass", "j1": "not-judged"}, F)
        s.assertIn("not judged: j1", str(e.exception))
        s.assertEqual(hd.verdicts("s1"), [])
        s.verdict("s1", A, {"ok": "fail: no", "j1": "not-judged"}, F)          # a FAIL verdict may leave rows open
        hd.tick(s.ctx(F))
        b = open([r for r in hd.runs() if r["change"] == "s1"][-1]["brief"]).read()
        s.assertIn("Open rows (the judge's, not judged at that head): j1", b)
        s.assertIn("not-judged", (Path(__file__).parent.parent / ".claude/agents/qa.md").read_text())

    def test_verdicts_append(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.verdict("s1", A, {"ok": "pass", "j1": "fail: wrong"}, F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        v = hd.verdicts("s1")
        s.assertEqual([x["rows"]["j1"] for x in v], ["fail: wrong", "pass"])

    def test_text_only_fix_keeps_verdict_valid(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["actor"], "ship-test")
        (s.root / "evidence" / "s1" / "pr-body.md").write_text("fixed body")  # qa fixed the text in place
        s.assertEqual(s.state(F, "s1")["actor"], "ship-test")

    def test_gate_bound_to_tree(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.assertEqual(s.state(F, "s1")["actor"], "qa")
        F2 = Fake(**{**FACTS, "refs": {**FACTS["refs"], "origin/HEAD": C}, "trees": {**FACTS["trees"], C: TC, D: "td" * 20}, "merges": {(C, A): ("ok", D)}})
        s.assertEqual(s.state(F2, "s1")["state"], "building tdtdtdtdt")  # the base moved: T moved: build and gate again

    def test_verdict_bound_to_head_and_contract(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["actor"], "ship-test")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_answer(["s1", "also do X"])  # the contract grew: the verdict no longer covers it
        s.assertEqual(s.state(F, "s1")["state"], "review due")
        F2 = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s1": C}})
        s.assertTrue(s.state(F2, "s1")["state"].startswith("dev run due: head ccccccccc"))  # the head moved: the hand-over is stale

    def test_rule_file_move_rejudges_rule_rows_only(s):
        s.change("s1"); s.agreed("s1")
        p = s.root / "evidence" / "s1" / "contract.md"
        p.write_text(p.read_text().replace("rules: ", "rules: AGENTS.md=b1"))
        F = Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): "b1"})
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["actor"], "ship-test")
        F2 = Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): "b2"})
        st = s.state(F2, "s1")
        s.assertEqual((st["actor"], st["input"][2]), ("qa", ["AGENTS.md"]))
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F2)  # re-judged against b2
        s.assertEqual(s.state(F2, "s1")["actor"], "ship-test")
        s.assertEqual(s.state(Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): None}), "s1")["actor"], "unknown")

    def test_no_reviewer_without_judge_rows_and_no_arbitrary_check(s):
        s.change("c1", "client"); s.agreed("c1", "client", extra="- evil | injected | check: rm -rf /\n")
        (s.root / "evidence" / "c1" / "x.txt").write_text("evidence")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "origin/client/c1": A}})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["c1"])
        s.assertIn("row evil failed", str(e.exception))
        s.assertTrue(all(c.startswith(("true", "false")) for c in F.ran), F.ran)  # the injected line never reaches the shell as a command
        (s.root / "evidence" / "c1" / "contract.md").write_text((s.root / "evidence" / "c1" / "contract.md").read_text().replace("- evil | injected | check: rm -rf /\n", ""))
        s.gated("c1", F)
        s.assertEqual(s.state(F, "c1")["state"], "shipping")  # no judge rows: no reviewer

    def test_failed_fetch_leaves_every_change_where_it_was(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, unknown={"fork"})
        v = hd.tick(s.ctx(F))
        s.assertEqual(s.state(F, "s1")["actor"], "unknown")
        s.assertEqual(v["spawn"], [])
        s.assertEqual(F.spawned, [])
        s.assertIsNone(hd.rec("s1", "handover"))


if __name__ == "__main__":
    unittest.main()
