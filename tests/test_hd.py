"""One class per requirement (docs/PRD.md, Acceptance), driven against a dict-backed Fake of Facts in a sandbox root."""
import json, os, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock

os.environ["HD_ROOT"] = tempfile.mkdtemp()
import hd, hook  # noqa: E402  (both read HD_ROOT at import)

A, B, C, D = "a" * 40, "b" * 40, "c" * 40, "d" * 40
TA, TB, TC = "ta" * 20, "tb" * 20, "tc" * 20


class Fake(hd.Facts):
    """Facts from dicts: refs {ref: sha}, anc {(tip, sha)}, trees {commit: tree}, merges {(base, head): result},
    blobs {(ref, path): sha}, rows {cmd: (rc, out)}, unknown {remote}. Records spawns and row runs."""

    def __init__(s, **f):
        super().__init__()
        s.f, s.spawned, s.ran, s.envs = f, [], [], []

    def sh(s, args, cwd=None, env=None, timeout=600):
        s.ran.append(args)
        if len(args) > 2 and args[1] == "down" and s.f.get("down_works", True):
            s.f.get("containers", {}).pop(f"server-{args[2]}", None)
        return 0, "", ""
    def containers(s): return s.f.get("containers", {})  # None in f = docker unreachable
    def fetch(s, clone, remote): return remote not in s.f.get("unknown", ())
    def rev(s, clone, ref): return None if ref.split("/")[0] in s.f.get("unknown", ()) else s.f.get("refs", {}).get(ref, "")
    def contains(s, clone, tip, sha):
        if tip is None: return None
        return bool(tip and sha) and (tip == sha or (tip, sha) in s.f.get("anc", set()))
    def tree(s, clone, commit): return s.f.get("trees", {}).get(commit)
    def merge(s, clone, base, head, msg): return s.f.get("merges", {}).get((base, head), ("ok", head))
    def blob(s, clone, ref, path): return s.f.get("blobs", {}).get((ref, path), "")
    def proc_start(s, pid): return "1"
    def console(s): return 7, "1"
    def alive(s, pid, start): return (pid, start) in s.f.get("procs", {(7, "1")})  # the console is alive unless a test says otherwise
    def spawn(s, args, log, env=None): s.spawned.append(args); s.envs.append(env or {}); return 4242, "99"
    def run(s, cmd, cwd, env): s.ran.append(cmd); return s.f.get("rows", {}).get(cmd, (1, "false") if cmd.startswith("false") else (0, ""))
    def events_count(s): return 0


class Sandbox(unittest.TestCase):
    """A temp HD_ROOT with hd.yaml, each repo's tools/track.md seed rows, harness/changes and goals written by helpers."""

    def setUp(s):
        s.root = Path(tempfile.mkdtemp())
        hd.ROOT, hd.STATE, hd.EVID, hd.DEFS = s.root, s.root / "state", s.root / "evidence", s.root / "harness"
        repos = {"client": s.root / "client", "fork": s.root / "fork", "harness": s.root}
        (s.root / "hd.yaml").write_text(json.dumps({"repos": {"client": {"name": "o/c", "path": str(repos["client"])}, "fork": {"name": "o/f", "path": str(repos["fork"]), "tools": "local/harness"},
                                                     "upstream": {"name": "u/f"}, "harness": {"name": "o/h", "path": str(s.root)}}, "agents": 3, "context_limit": 150000, "pins": []}))
        for track, p in (("client", repos["client"]), ("server", repos["fork"] / ".worktrees" / "harness"), ("harness", s.root)):
            (p / "tools").mkdir(parents=True, exist_ok=True)
            (p / "tools" / "track.md").write_text(f"# {track}\n\n## Seed rows\n- ok | always passes | check: true\n" + (f"- j1 | a judged row | judge: qa-{track}\n" if track == "server" else ""))
        (s.root / "harness" / "changes").mkdir(parents=True)
        (s.root / "harness" / "goals").mkdir(parents=True)
        s.seq = 0

    def tearDown(s):
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


def payload(run, agent_id, event, root, last=None, usage=None, context=1000):
    """A hook payload with a transcript whose first message is the one-line prompt naming the brief."""
    tp = root / "state" / f"transcript-{agent_id}.jsonl"
    lines = [{"type": "user", "message": {"role": "user", "content": f"Read and follow {run['brief']}"}}]
    for i in range(usage or 0):
        lines.append({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": f"turn {i}"}],
                                                        "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": context, "cache_creation_input_tokens": 0}}})
    tp.write_text("".join(json.dumps(l) + "\n" for l in lines))
    p = {"hook_event_name": event, "agent_id": agent_id, "agent_type": run["role"], "agent_transcript_path": str(tp)}
    if last:
        p["last_assistant_message"] = last
    return p


class R1(Sandbox):
    """R1 against v7's cause: the client goal stayed six days stale behind one open upstream PR (§4.19)."""

    def goal(s, slug="client-api", track="client", target=100):
        (s.root / "harness" / "goals" / f"{slug}.md").write_text(f"---\nslug: {slug}\ntrack: {track}\ntarget: {target}\n---\nthe goal")

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

    def test_below_target_with_nothing_open_lists_the_orchestrator(s):
        s.goal()
        F = Fake(**FACTS)
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 93.2, "report": "r"})
        v = hd.tick(s.ctx(F))
        s.assertIn("planning due", v["goal"][0])
        s.assertTrue(any(x.startswith("orchestrator-") for x in v["spawn"]))
        s.change("c1", "client", goal="client-api")                    # a change serves the goal: no planning
        hd.tick(s.ctx(F))
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 93.2, "report": "r"})
        v = hd.tick(s.ctx(F))
        s.assertNotIn("planning due", v["goal"][0])
        hd.put("client-api", "measure", {"tree": TB + "+none", "value": 100, "report": "r"})
        s.assertNotIn("planning due", hd.tick(s.ctx(F))["goal"][0])   # met: measured, nothing planned


class R2(Sandbox):
    """R2 against v7's causes: spawns waited on an unwoken main (§4.5), hand-backs filled main (§1b), an agent's exit
    waited on the pass (§4.23), the run record came from a prompt protocol (ISSUES)."""

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
        with mock.patch.object(hook, "start_pass") as sp:
            hook.bind(payload(run, "ag1", "SubagentStart", s.root))
            F.f["refs"]["origin/client/c1"] = A                       # the dev pushes and hands over
            (s.root / "evidence" / "c1" / "log.txt").write_text("evidence")
            with mock.patch.object(hd, "Facts", lambda: F):
                hd.cmd_handover(["c1"])
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="run c1-1: handed over " + A, usage=3))
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
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="run s1-1: gave up"))
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 1)            # one retry on the same input
        run2 = hd.runs()[1]
        hook.bind(payload(run2, "ag2", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run2, "ag2", "SubagentStop", s.root, last="run s1-2: gave up"))
        v = hd.tick(s.ctx(F))
        s.assertEqual([x for x in v["spawn"] if x.startswith("s1-")], [])   # then raised once, never a third
        s.assertTrue(any("ended without a record" in a for a in v["alert"]))
        s.assertTrue(any(x.startswith("orchestrator-") for x in v["spawn"]))  # the alert lists the orchestrator, not the user

    def test_hook_binds_by_brief_path_and_wakes_main(s):
        s.change("s1"); s.agreed("s1"); s.change("s2"); s.agreed("s2")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s2": A}})
        hd.tick(s.ctx(F))
        r1, r2 = hd.runs()
        wake = (s.root / "state" / "wake").read_text()
        hook.bind(payload(r2, "agX", "SubagentStart", s.root))        # the second listed run is spawned first
        s.assertEqual([r.get("agent_id") for r in hd.runs()], [None, "agX"])
        s.assertNotEqual((s.root / "state" / "wake").read_text(), wake)  # a state change touches the wake file
        hook.bind(payload(r2, "agX", "PreToolUse", s.root))           # a repeated bind changes nothing
        s.assertEqual(hd.runs()[1]["started"], hd.runs()[1]["started"])
        s.assertEqual(sum(1 for l in open(s.root / "state" / "events.jsonl") if '"started"' in l), 1)


    def test_orchestrator_record_and_unmatched_stop(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(Fake, "events_count", lambda s: 60):        # fifty events since the last orchestrator run
            v = hd.tick(s.ctx(F))
        orc = [r for r in hd.runs() if r["role"] == "orchestrator"][0]
        hook.bind(payload(orc, "agO", "SubagentStart", s.root))
        hd.cmd_new(["x1", "--track", "harness", "--title", "fix something"])   # the orchestrator files a change
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(orc, "agO", "SubagentStop", s.root))
            s.assertTrue([r for r in hd.runs() if r["role"] == "orchestrator"][0]["record"])
            dev = [r for r in hd.runs() if r["role"] == "dev"][0]
            hook.end_run({"hook_event_name": "SubagentStop", "agent_id": "ghost", "agent_type": "dev"})  # no transcript, no id: ends nothing
        s.assertIsNone([r for r in hd.runs() if r["name"] == dev["name"]][0]["ended"])
        hook.bind({"hook_event_name": "PreToolUse", "agent_id": "x", "agent_type": "Explore"})          # not a harness role: no read
        s.assertEqual(len(hd.runs()), 2)                                                            # nothing bound or listed for it


class R5(Sandbox):
    """R5 against v7's causes: a volume repaired 68 times with no effect (§4.22), servers and clients outliving their
    runs (ISSUES), runs hanging after the console died (§4.5), a question asked three times (§4.20)."""

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

    def test_repair_logged_only_on_observed_effect_and_raised_once(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, containers={"server-s1": "running"}, down_works=False)
        hd.put("s1", "ask", {"text": "?"})                                       # no run is listed while a question is open
        v1 = hd.tick(s.ctx(F)); v2 = hd.tick(s.ctx(F)); v3 = hd.tick(s.ctx(F))
        s.assertFalse(any('"action": "down"' in l for l in open(s.root / "state" / "events.jsonl")))
        s.assertEqual([any("down had no effect" in a for a in v["alert"]) for v in (v1, v2, v3)], [False, True, False])
        s.assertEqual(hd.rec("s1", "repair-down")["attempts"], 3)

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

    def test_docker_down_is_one_alert_and_no_script_starts(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, containers=None)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned, [])
        s.assertEqual(sum("docker unreachable" in a for a in v["alert"]), 1)

    def test_second_ask_refused_while_one_open(s):
        s.change("s1")
        hd.cmd_ask(["s1", "which scope?"])
        with s.assertRaises(SystemExit) as e:
            hd.cmd_ask(["s1", "which scope?"])
        s.assertIn("already open", str(e.exception))
        hd.cmd_answer(["s1", "scope B"])
        s.assertIsNone(hd.rec("s1", "ask"))
        hd.cmd_ask(["s1", "another?"])                                          # after the answer, a new question may open


class R6(Sandbox):
    """R6 against v7's causes: one run read 205M tokens (§4.3), 764 of 1,174 events were repeats (§4.22), ~7 builds of one
    tree per round (§4.13), spawn briefs pasted into main (§1b)."""

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
        s.assertTrue(hd.runs()[0]["handoff_told"])
        (s.root / "evidence" / "s1" / "handoff.md").write_text("done: half; next: the rest")
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="run s1-1: handoff", usage=4, context=170000))
        r = hd.runs()[0]
        s.assertEqual((r["record"], r["usage"]["turns"], r["usage"]["cache_read"] > 0, bool(r["transcript"])), (False, 4, True, True))
        v = hd.tick(s.ctx(F))
        s.assertEqual(len(v["spawn"]), 1)                              # the successor, with the hand-off in its brief
        s.assertIn("done: half; next: the rest", open(hd.runs()[1]["brief"]).read())


    def test_malformed_definition_is_one_alert(s):
        s.change("s1"); s.agreed("s1")
        (s.root / "harness" / "changes" / "bad.md").write_text("---\ntitle: [unclosed\n---\n")
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertTrue(any(a.startswith("definition skipped: bad.md") for a in v["alert"]))
        s.assertEqual(len([x for x in v["spawn"] if x.startswith("s1-")]), 1)   # the pass went on for the others (the alert also lists the orchestrator)
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
    """R8 against v7's causes: identical trees rebuilt, 53 of 60 pins owned by no change, rerere resolutions replayed
    wrongly, 15 integrator runs (§4.12, §4.13)."""

    def test_tree_is_merge_of_base_deps_head(s):
        s.change("s1"); s.agreed("s1"); s.change("s2", deps=["s1"]); s.agreed("s2")
        hd.put("live", "tree", {"tree": "x", "commit": D, "heads": [A]})            # s1 live on the test server, not upstream
        E = "e" * 40
        F = Fake(refs={"origin/HEAD": B, "fork/dev/s1": A, "fork/dev/s2": C}, trees={E: "te" * 20}, merges={(B, A): ("ok", D), (D, C): ("ok", E)})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s2"])
        s.assertEqual((hd.rec("s2", "handover")["commit"], hd.rec("s2", "handover")["T"]), (E, "te" * 20))   # base, then s1, then s2

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
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["conflict"], t["with"]), ("s1", ["local/x"]))
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))
        s.assertIn("local/merge/<yours7>-<theirs7>", open(hd.runs()[0]["brief"]).read())
        s.assertEqual([x for x in F.spawned if x[1] == "ship"], [])

    def test_artefacts_named_by_change(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1"])
        hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["build", "s1", A])
        s.assertEqual((F.envs[-1]["SLUG"], F.envs[-1]["T"]), ("s1", TA))
        s.assertTrue((s.root / "state" / "s1" / "proc-build.json").exists())


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

    def test_handover_refused_on_failing_script_row(s):
        s.change("s1"); s.agreed("s1", extra="- bad | fails | check: false\n")
        F = Fake(**FACTS, rows={"false": (1, "nope")})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1"])
        s.assertIn("row bad failed", str(e.exception))
        s.assertIsNone(hd.rec("s1", "handover"))

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

    def test_verdict_refused_when_row_missing(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with s.assertRaises(SystemExit) as e:
            s.verdict("s1", A, {"ok": "pass"}, F)
        s.assertIn("rows missing: j1", str(e.exception))
        with s.assertRaises(SystemExit) as e:
            s.verdict("s1", A, {"ok": "pass", "j1": "maybe"}, F)
        s.assertIn("'pass' or 'fail", str(e.exception))
        s.assertEqual(hd.verdicts("s1"), [])

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
