"""One class per requirement (docs/PRD.md, Acceptance), driven against a dict-backed Fake of Facts in a sandbox root."""
import hashlib, io, json, os, re, shutil, signal, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

for k in ("SLUG", "HEAD", "T", "TCOMMIT", "BASE", "EVIDENCE", "BUILD", "CLONE", "TRACK", "PUBLIC_BRANCH", "PR", "PINS", "CENTRAL", "TOOLS", "TOOLS_ROOT", "G", "NAMES", "LIVE"):
    os.environ.pop(k, None)                                                   # hd's loop env (Hd.env): the gate's own change never reaches a test's track.sh
NESTED = os.environ.get("HD_SUITE")                                           # "1" for every process this suite starts; "nested" for a test's deliberate inner suite
if NESTED == "1":                                                             # a test's gate ran a row that runs this suite: refuse, never recurse
    raise ImportError("refused: the test suite runs inside itself (HD_SUITE=1); a test's gate never runs the suite")
os.environ["HD_SUITE"] = "1"
SUITE_TMP = tempfile.TemporaryDirectory(prefix="hd-suite-", ignore_cleanup_errors=True)   # R5: every temp dir of the suite (HD_ROOT, each test's, each
tempfile.tempdir = os.environ["TMPDIR"] = SUITE_TMP.name                     # process's) is under it, removed at the suite's end, a failed test's too
os.environ["HD_ROOT"] = tempfile.mkdtemp()
import hd, hook  # noqa: E402  (both read HD_ROOT at import)

A, B, C, D = "a" * 40, "b" * 40, "c" * 40, "d" * 40
TA, TB, TC = "ta" * 20, "tb" * 20, "tc" * 20
PUSHED = f"Pushed {A[:9]}, {B[:9]}, {C[:9]} and {D[:9]}."


class Fake(hd.Facts):
    """Facts from dicts: refs {ref: sha}, anc {(tip, sha)}, trees {commit: tree}, merges {(base, head): result},
    blobs {(ref, path): sha}, commits {head: its commits not in the base}, line {commits of the base's first-parent line}, rows {cmd: (rc, out)}, unknown {remote}. Records spawns and row runs."""

    def __init__(s, **f):
        super().__init__()
        s.f, s.spawned, s.ran, s.envs, s.stopped = f, [], [], [], []

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
    def host(s): return s.f.get("host", (64 * 2**30, 64))  # the host's MemTotal and nproc
    def tools_used(s): return s.f.get("tools_used", set())  # None in f = docker unreachable
    def orchestrators(s): return s.f.get("orchestrators", [(7, "1")])  # [] in f = no orchestrator session
    def definition_at(s, start): return s.f.get("started_on", {}).get(start, "")  # the orchestrator.md blob a session started on
    def release(s, repo, tag): return {"tag": tag} if tag in s.f.get("releases", ()) else {}
    def fetch(s, clone, remote, ref=""): ref and s.ran.append(["fetch", remote, ref]); return remote not in s.f.get("unknown", ())
    def rev(s, clone, ref):
        if ref.split("/")[0] in s.f.get("unknown", ()): return None
        if ref.startswith("harness/") and clone != str(hd.ROOT): return s.f.get("refs", {}).get(f"{clone}:{ref}", "")  # a product repo's tools ref
        if len(ref) == 7: return next((v for v in s.f.get("refs", {}).values() if v.startswith(ref)), "")  # an abbreviated sha
        return s.f.get("refs", {}).get(ref, "")
    def resolutions(s, clone): return [(r, *r.rsplit("/", 1)[1].partition("-")[::2]) for r in sorted(s.f.get("refs", {})) if r.startswith("fork/local/merge/")]
    def worktrees(s, repo): return s.f.get("worktrees", {}).get(repo, [])
    def edits(s, wt): return wt in s.f.get("dirty", ())  # "links": worktrees git refuses to remove unforced, no one's edits
    def contains(s, clone, tip, sha):
        if tip is None: return None
        return bool(tip and sha) and (tip == sha or (tip, sha) in s.f.get("anc", set()))
    def on_line(s, clone, tip, sha): return sha in s.f.get("line", ())
    def unmerged(s, clone, base, head): return frozenset(s.f.get("commits", {}).get(head, {head}) - {base})  # a head's own commits: itself unless a test says
    def tree(s, clone, commit, drop=""): return s.f.get("trees", {}).get(commit)
    def tools_files(s, clone, commit): return s.f.get("tools_files", {}).get(commit, {})
    def merge(s, clone, base, head, msg): return s.f.get("merges", {}).get((base, head), ("ok", head))
    def blob(s, clone, ref, path): return s.f.get("blobs", {}).get((ref, path), "")
    def rebase(s, repo, branch, onto, wt): s.ran.append(["rebase", repo, branch, onto]); return s.f.get("rebases", {}).get(branch, ("conflict", "x"))
    def proc_start(s, pid): return "1"
    def slices(s): return s.f.get("slices", set())                       # the active run slices
    def alive(s, pid, start): return (pid, start) in s.f.get("procs", {(7, "1")})  # the console is alive unless a test says otherwise
    def spawn(s, args, log, env=None): s.spawned.append(args); s.envs.append(env or {}); return 4242, "99"
    def stop(s, pid, start): s.stopped.append(pid); s.f["procs"] = set(s.f.get("procs", {(7, "1")})) - {(pid, start)}
    def run(s, cmd, cwd, env): s.ran.append(cmd); return s.f.get("rows", {}).get(cmd, (1, "false") if cmd.startswith("false") else (0, ""))
    def review_comments(s, repo, pr): return None if s.f.get("comments", {}) is None else s.f.get("comments", {}).get(pr, [])  # None in f = GitHub unreadable
    def pr_comments(s, repo, pr): return None if s.f.get("talk", {}) is None else s.f.get("talk", {}).get(pr, [])
    def open_prs(s, repo): return None if s.f.get("prs", {}) is None else s.f.get("prs", {}).get(repo, [])  # the open upstream PRs; None in f = GitHub unreadable
    def pr(s, repo, n): return s.next(s.f.get("pull", {}), n)    # pull {n: {branch, head, draft, requested}}
    def ci(s, repo, sha): return s.next(s.f, "ci")               # ci [the checks at each read]
    def job(s, repo, j): return s.f.get("jobs", {}).get(j)         # jobs {id: {attempt, step}}
    def next(s, d, k):  # a list answers each read in turn, its last answer from then on
        v = d.get(k)
        return (v.pop(0) if len(v) > 1 else v[0]) if isinstance(v, list) else v


class Sandbox(unittest.TestCase):
    """A temp HD_ROOT with hd.yaml, each repo's tools/track.md seed rows, harness/changes and goals written by helpers."""

    def setUp(s):
        s.root = Path(tempfile.mkdtemp())
        hd.ROOT, hd.STATE, hd.EVID, hd.DEFS = s.root, s.root / "state", s.root / "evidence", s.root / "harness"
        repos = {"client": s.root / "client", "fork": s.root / "fork", "central": s.root / "central", "harness": s.root}
        (s.root / "hd.yaml").write_text(json.dumps({"repos": {"client": {"name": "o/c", "path": str(repos["client"])}, "fork": {"name": "o/f", "path": str(repos["fork"]), "tools": "local/harness", "upstream": "u/f"},
                                                     "central": {"name": "o/z", "path": str(repos["central"]), "tools": "local/harness", "upstream": "u/z"},
                                                     "harness": {"name": "o/h", "path": str(s.root)}}, "agents": 3, "context_limit": 150000, "pins": [],
                                                     "mechanisms": ["loop", "runs", "tree", "dispatch", "carry", "hold"]}))
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
        meta = {"slug": slug, "track": track, "title": slug, "priority": "P2", "deps": [], "created": f"2026-10-31T00:00:{s.seq:02d}Z",
                **({"mechanism": slug} if track == "harness" else {}), **meta}   # a harness change names its own unless told
        (s.root / "harness" / "changes" / f"{slug}.md").write_text("---\n" + "".join(f"{k}: {json.dumps(v)}\n" for k, v in meta.items()) + "---\n" + body)

    def agreed(s, slug, track="server", extra=""):
        hd.write_contract(hd.cfg(), slug, track, "qa-run")
        with open(s.root / "evidence" / slug / "contract.md", "a") as f:
            f.write(extra)
        if (ch := hd.defs("changes").get(slug)) and hd.fids(ch):  # a round's finding rows, as the pass writes them
            with mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch.object(hd, "now", lambda: "2000-01-01T00:00:00Z"):
                hd.finding_rows(slug, ch, hd.fids(ch), {})
        (s.root / "evidence" / slug / "pr-body.md").write_text("body")
        (s.root / "evidence" / slug / "pr-comment.md").write_text(PUSHED)       # names every head a test pushes

    def ctx(s, F):
        return hd.Ctx(F, hd.cfg())

    def state(s, F, slug):
        ctx = s.ctx(F)
        return hd.nxt(ctx, ctx.changes[slug])

    def gated(s, slug, F):
        """Hand over, build and gate at the current head and tree."""
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover([slug, "Limits:", "none"])
        ho = hd.rec(slug, "handover")
        hd.put(slug, "build", {"T": ho["T"], "ok": True})
        hd.put(slug, "gate", {"T": ho["T"], "ok": True})
        hd.put(f"ship-{hd.defs('changes')[slug]['track']}", f"gate-{ho['T']}", {"T": ho["T"], "ok": True})  # a batched change alone in its batch
        return ho

    def approve(s, F, slug, head):
        """The user's yes at head and the card's current texts (as `hd approve` records it at the user step)."""
        ctx = s.ctx(F)
        hd.put(slug, "approval", {"head": head, "texts": hd.digest(json.dumps(hd.public_texts(ctx, ctx.changes[slug])))})

    def verdict(s, slug, head, rows, F):
        f = s.root / "rows.json"
        fr = {r["id"]: "pass" for r in (hd.contract(slug) or {"rows": []})["rows"] if r["id"].startswith("answer-") and " finding " in r["text"][:30]}
        f.write_text(json.dumps({**fr, **rows}))                               # a round's finding rows pass unless a test says
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
    def test_a_shipped_orchestrator_definition_reaches_the_live_session(s):
        blobs = {("HEAD", hd.ORCH): "new"}
        v = hd.tick(s.ctx(Fake(**FACTS, blobs=blobs, started_on={"1": "new"})))
        s.assertFalse(any(a.startswith("orchestrator ") for a in v["alert"]))                # started on the live definition: no step
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS, blobs=blobs, started_on={"1": "old"})
        (s.root / ".claude" / "agents").mkdir(parents=True); (s.root / hd.ORCH).write_text("the live definition\n")
        def hd_(cmd, *a):
            with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(Fake, "console", lambda f: (7, "1"), create=True), \
                    mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                cmd(list(a))
            return out.getvalue()
        v = hd.tick(s.ctx(F))
        s.assertEqual(len([a for a in v["alert"] if a.startswith("orchestrator 7: your definition changed")]), 1)
        s.assertTrue(v["spawn"])                                                              # listed runs are not held behind it
        out = hd_(hd.cmd_tick)
        s.assertIn("spawn: s1-1", out)                                                        # the session goes on: it spawns
        s.assertIn("definition: the live", out); s.assertIn("the live definition", out)       # and is printed the live file in full
        s.assertFalse(any(a.startswith("orchestrator ") for a in hd.tick(s.ctx(F))["alert"]))  # once: it now holds the live blob
        s.assertNotIn("definition:", hd_(hd.cmd_tick))
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(Fake, "console", lambda f: (7, "1"), create=True), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            hook.reread({"hook_event_name": "SessionStart", "source": "compact"})
        s.assertIn("the live definition", json.loads(out.getvalue())["hookSpecificOutput"]["additionalContext"])   # a compaction reads it again
        F.f["started_on"] = {"1": "new"}
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(Fake, "console", lambda f: (7, "1"), create=True), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            hook.reread({"hook_event_name": "SessionStart", "source": "compact"})
        s.assertEqual(out.getvalue(), "")                                                     # started on the live one: nothing to add
        F.f["orchestrators"] = [(8, "2")]
        hd.tick(s.ctx(F))
        s.assertEqual(list((s.root / "state" / "orchestrator-read").glob("*")), [])          # a gone session's read is dropped
        s.assertFalse(hasattr(hd, "cmd_restart"))                                             # no session ends for a definition
        s.assertIn("exec claude --agent orchestrator", (Path(__file__).parent.parent / hd.SUPERVISOR).read_text())
        settings = json.loads((Path(__file__).parent.parent / ".claude" / "settings.json").read_text())
        s.assertEqual(settings["hooks"]["SessionStart"][0]["matcher"], "compact")

    def test_the_user_chats_with_the_orchestrator_no_relay(s):
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertNotIn("message", v)                                                            # no relayed inbox
        s.assertFalse(any("orchestrator session" in a for a in v["alert"]))
        for verb in ("tell", "heard"):
            with s.assertRaises(SystemExit):
                hd.main([verb, "x"])
        root = Path(__file__).parent.parent
        s.assertFalse((root / ".claude" / "skills" / "head").exists())
        brief = (root / ".claude" / "agents" / "orchestrator.md").read_text()
        for step in ("`card`", "`question`", "`alert`", "`! python3 ~/osrs-harness/hd.py approve", "`! python3 ~/osrs-harness/hd.py close", "monitor sweep", "evidence/monitor/sweep-<n>.md", "On session start, also start a monitor sweep"):   # the head skill's steps; the user types the yes and the close
            s.assertIn(step, brief)
        s.assertEqual(re.findall(r"^(\w+):", brief.split("---")[1], re.M), ["name", "description"])   # nothing a reread could not carry
        ask = {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "agent_type": "orchestrator"}
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            s.assertTrue(hook.deny_ask(ask))                                                   # the only spawner never waits on the user
            s.assertFalse(hook.deny_ask({**ask, "agent_id": "a1"}))                            # a subagent's own question is not its
        s.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")
        s.assertIn("AskUserQuestion", json.loads((root / ".claude" / "settings.json").read_text())["hooks"]["PreToolUse"][0]["matcher"])
        v = hd.tick(s.ctx(Fake(**{**FACTS, "orchestrators": []})))
        s.assertTrue(any(a.startswith("user: no orchestrator session") for a in v["alert"]))
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
        s.assertNotIn("##", spawn[0])                                 # spawn by path: nothing of the brief in the orchestrator's context
        s.assertIn(f"Base: origin/HEAD at {B[:9]}", open(run["brief"]).read())   # the dev branches from the base tip the brief names
        with mock.patch.object(hook, "start_pass") as sp:
            hook.bind(payload(run, "ag1", "SubagentStart", s.root))
            F.f["refs"]["origin/client/c1"] = A                       # the dev pushes and hands over
            (s.root / "evidence" / "c1" / "log.txt").write_text("evidence")
            with mock.patch.object(hd, "Facts", lambda: F):
                hd.cmd_handover(["c1", "Limits:", "none"])
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, last="run c1-1: handed over " + A, usage=3, handback="run c1-1: handed over " + A))
            s.assertEqual(sp.call_count, 1)                           # the pass is started, never waited on
        run = [r for r in hd.runs() if r["change"] == "c1"][0]
        s.assertTrue(run["record"]); s.assertEqual(run["usage"]["turns"], 3); s.assertIn("handed over", run["last"])
        v = hd.tick(s.ctx(F)); s.assertEqual(F.spawned[-1][1:], ["gate", "ship-client", A])   # the client's batch, built in its gate
        hd.put("ship-client", f"gate-{F.envs[-1]['T']}", {"ok": True})
        v = hd.tick(s.ctx(F)); s.assertEqual(F.spawned[-1][1:], ["ship", "ship-client", A])
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

    def test_a_reopened_dependency_holds_its_dependents(s):  # planner-24: a joined filing reopened h1 yet c1 ran with nothing to fix
        s.change("h1", track="harness", mechanism="hold"); s.agreed("h1", track="harness"); s.change("c1", "client", deps=["h1"])
        D = Fake(refs={"HEAD": A, "harness/h1": A, "origin/HEAD": B, "origin/client/c1": ""}, trees={A: TA}, merges={(A, A): ("ok", A)})
        with mock.patch.object(hd, "Facts", lambda: D), mock.patch.object(hd, "now", lambda: "2000-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertNotEqual(s.state(D, "c1")["state"], "waiting on h1")             # h1 live and done: c1 goes on
        hd.cmd_new(["p9", "--track", "harness", "--title", "hold drops a run", "--mechanism", "hold"])   # joins h1 after its done head
        s.assertEqual(s.state(D, "h1")["state"], "dev run due: a filing or finding joined after the hand-over (answer-1)")
        s.assertEqual(s.state(D, "c1")["state"], "waiting on h1")                # its step reopened: met only once its dev acts on it
        with mock.patch.object(hd, "Facts", lambda: D), mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertNotEqual(s.state(D, "c1")["state"], "waiting on h1")

    def test_fresh_dev_ref_in_the_base_is_not_done(s):
        s.change("h1", "harness"); s.change("c1", "client", deps=["h1"])
        F = Fake(refs={"HEAD": B, "harness/h1": A, "origin/HEAD": B, "origin/client/c1": ""}, anc={(B, A)}, line={A, B}, trees={A: TA})
        s.assertEqual(s.state(F, "h1")["state"], "contract: seed rows pending")    # cut at A, a base commit; the base moved on to B
        s.assertEqual(s.state(F, "c1")["state"], "waiting on h1")
        hd.write_contract(hd.cfg(), "h1", "harness", "derived")
        (s.root / "evidence" / "h1" / "log.txt").write_text("evidence")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual(s.state(F, "h1")["state"], "done")                          # handed over: its own work

    def test_a_live_run_of_a_done_change_ends_with_its_record(s):
        s.change("h1", "harness"); hd.write_contract(hd.cfg(), "h1", "harness", "derived")
        F = Fake(**{**FACTS, "refs": {"HEAD": B, "harness/h1": A, "origin/HEAD": B}, "anc": {(B, A)}, "line": {A, B}, "trees": {A: TA}})
        hd.tick(s.ctx(F))
        run = [r for r in hd.runs() if r["change"] == "h1"][0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        (s.root / "evidence" / "h1" / "log.txt").write_text("evidence")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
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
            hd.cmd_handover(["h1", "Limits:", "none"])
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
        (repo / "wt" / "f").write_text("x"); s.assertTrue(hd.Facts().edits(str(repo / "wt")))   # an untracked file is
        (repo / "wt" / "f").unlink(); (repo / "wt" / ".gitignore").write_text("x"); s.assertTrue(hd.Facts().edits(str(repo / "wt")))  # a tracked edit is

    def test_maintainer_inline_comment_files_a_round_once_and_later_findings_join_it(s):
        s.change("s1", pr=354, branch="content/cannon"); s.agreed("s1")
        s.change("s1-old", pr=354, deps=["s1"], finding=7)                 # filed by hand: carried
        hd.put("s1-old", "ship", {"head": A, "ok": True})                  # the PR's last round went upstream at A
        com = lambda i, who="a-thoren", **k: {"id": i, "author": who, "bot": False, "reply": None, "path": "N.kt", "line": 265, "body": "reset | the varp?", **k}
        F = Fake(**{**FACTS, "comments": {354: [com(7), com(8), com(9), com(10, reply=9), com(11, "O", reply=9), com(12, "ci", bot=True)]},
                    "prs": {"u/f": [{"number": 354, "branch": "content/cannon", "owner": "o", "head": A, "draft": False}]}})
        hd.tick(s.ctx(F), act=False)
        s.assertFalse((s.root / "harness" / "changes" / "server-354-c8.md").exists())  # a dry run files nothing
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))
        new = {k: v for k, v in hd.defs("changes").items() if k not in ("s1", "s1-old")}
        s.assertEqual(list(new), ["server-354-c8"])                                # one round, once: answered (9, 10), ours, bots, carried skipped
        c = new["server-354-c8"]
        s.assertEqual((c["deps"], c["pr"], c["finding"], c["priority"], c["branch"]), (["s1-old"], 354, [8], "P1", "content/cannon"))  # on the PR's tip
        con = hd.contract("server-354-c8")
        seeds = [l[2:].split(" |")[0] for l in hd.seed_rows(hd.cfg(), "server").splitlines()]
        s.assertEqual(con["agreed"], "derived")                            # its findings are its contract: the dev answers, qa judges once
        s.assertEqual([r["id"] for r in con["rows"]], seeds + ["answer-1"])
        s.assertTrue(con["rows"][-1]["judge"]); s.assertIn("finding 8 by a-thoren on N.kt:265: reset / the varp?", con["rows"][-1]["text"])
        F.f["comments"][354] += [com(13, "eagle"), com(14)]                # later findings join the open round: no change of their own
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))                               # the joins, then the pass's rows for them
        s.assertEqual(sorted(k for k in hd.defs("changes") if k not in ("s1", "s1-old")), ["server-354-c8"])
        s.assertEqual(hd.defs("changes")["server-354-c8"]["finding"], [8, 13, 14])
        s.assertEqual([r["id"] for r in hd.contract("server-354-c8")["rows"]], seeds + ["answer-1", "answer-2", "answer-3"])

    def test_findings_on_a_pr_of_two_roots_join_its_one_open_round(s):
        s.change("cannon-a", pr=354); s.agreed("cannon-a", extra="- answer-1 | a-thoren's mcannonmulti | judge\n")
        s.change("cannon-b", pr=354); s.agreed("cannon-b", extra="- acc-A1 | the reclaim | judge\n")
        talk = lambda i, who, body: {"id": i, "author": who, "body": body}
        F = Fake(**{**FACTS, "comments": {354: []}, "talk": {354: [talk("IC_x", "a-thoren", "mcannonmulti resets"), talk("IC_y", "eagle", "Nulodion's reclaim")]}})
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))
        s.assertEqual(sorted(hd.defs("changes")), ["cannon-a", "cannon-b"])        # no change per finding
        s.assertEqual(hd.defs("changes")["cannon-a"]["finding"], ["IC_x", "IC_y"])   # the open round: the least tip
        rows = hd.contract("cannon-a")["rows"]
        s.assertEqual([r["id"] for r in rows][-2:], ["answer-2", "answer-3"])
        s.assertIn("mcannonmulti resets", rows[-2]["text"]); s.assertIn("Nulodion's reclaim", rows[-1]["text"])

    def test_a_finding_files_until_a_reply_or_comment_of_ours_answers_it(s):
        s.change("s1", pr=354); s.agreed("s1"); s.change("s1-c8", pr=354, deps=["s1"], finding=8)
        com = lambda i, who="a-thoren", reply=8: {"id": i, "author": who, "bot": False, "reply": reply, "path": "N.kt", "line": 265, "body": "and then?"}
        talk = lambda i, who, body: {"id": i, "author": who, "body": body}
        F = Fake(**{**FACTS, "comments": {354: [com(8, reply=None), com(9), com(10, "O"), com(11), com(12, reply=50), com(51, "O", reply=50),
                                                {**com(52, "O", reply=50), "body": "> rename  it\n> now\n\n@rev renamed."}]},
                    "talk": {354: [talk("IC_a", "rev", "the varp\nresets"), talk("IC_b", "O", "> the varp resets\n\n@rev fixed."), talk("IC_c", "rev", "still wrong"),
                                   talk("PRR_d", "rev", "please split it"), talk("PRR_e", "rev", ""), talk("PRR_f", "O", "ours"), talk("PRR_g", "rev", "rename it now, please")]}})
        hd.tick(s.ctx(F)); hd.tick(s.ctx(F))
        s.assertEqual(sorted(hd.defs("changes")), ["s1", "s1-c8"])
        s.assertEqual(hd.defs("changes")["s1-c8"]["finding"], [8, 11, "IC_c", "PRR_d"])   # 9 precedes our reply 10, 12 our 51; IC_a is quoted by ours, PRR_g by our inline reply; no dates
        s.assertIn("> please split it", hd.defs("changes")["s1-c8"]["body"])       # each joined finding's quote in the round's definition
        s.assertEqual(hd.root(F.f["comments"][354], 11), 8)               # its reply goes in thread 8, and answers it only after 11
        ctx = s.ctx(F); ch = {**ctx.changes["s1-c8"]}
        s.assertEqual((hd.answered(ctx, ch, 11), hd.answered(ctx, ch, "IC_c"), hd.answered(ctx, ch, "IC_a"), hd.answered(ctx, ch, "IC_gone")), (False, False, True, False))
        F.f["comments"][354].append(com(13, "O")); F.f["talk"][354].append(talk("IC_h", "O", "> still wrong\n\n@rev now right."))
        s.assertEqual((hd.answered(s.ctx(F), ch, 11), hd.answered(s.ctx(F), ch, "IC_c")), (True, True))
        F.f["talk"] = None; s.assertIsNone(hd.answered(s.ctx(F), ch, 11))      # GitHub unread: unknown

    def test_a_bot_never_files_and_an_unanswered_comment_files_whatever_its_age(s):
        s.change("s1", pr=354); s.agreed("s1")
        talk = lambda i, who, bot=False: {"id": i, "author": who, "bot": bot, "body": "look here"}
        F = Fake(**{**FACTS, "comments": {354: [{"id": 8, "author": "ci-x", "bot": False, "reply": None, "path": "N.kt", "line": 1, "body": "lint"}]},
                    "talk": {354: [talk("IC_a", "rev"), talk("IC_b", "rev"), talk("IC_c", "coderabbitai[bot]", True), talk("IC_d", "helper", True),
                                   talk("PRR_e", "copilot-pull-request-reviewer[bot]", True)]}})
        ctx = s.ctx(F); ctx.cfg["bots"] = ["CI-X"]                                      # hd.yaml's bots: a bot GitHub does not mark
        hd.tick(ctx, act=False); s.assertEqual(sorted(k for k in hd.defs("changes") if k != "s1"), [])
        hd.tick(ctx)
        s.assertEqual((sorted(hd.defs("changes")), hd.defs("changes")["s1"]["finding"]), (["s1"], ["IC_a", "IC_b"]))  # no comment of ours, no date: both join the open round; the rest are bots
        s.change("s2", pr=355); s.agreed("s2"); F.f["talk"][355] = [talk("IC_z", "rev")]; F.f["comments"] = None
        hd.tick(s.ctx(F))
        s.assertNotIn("server-355-cicz", hd.defs("changes"))                                       # the inline comments unread: nothing files

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
        s.assertTrue(run2["step"].endswith("(again after s1-1: its hand-back)"), run2["step"])   # it names its cause
        hook.bind(payload(run2, "ag2", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run2, "ag2", "SubagentStop", s.root, handback="run s1-2: gave up"))
        v = hd.tick(s.ctx(F))
        s.assertEqual([x for x in v["spawn"] if x.startswith("s1-")], [])   # then raised once, never a third
        s.assertTrue(any("ended without a record" in a for a in v["alert"]))
        s.assertTrue(any(x.startswith("planner-") for x in v["spawn"]))  # the alert lists the planner, not the user

    def test_a_listed_spawn_goes_when_its_change_stops_being_due(s):
        s.change("s1", priority="P1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.assertEqual(len(hd.tick(s.ctx(F))["spawn"]), 1)
        hd.cmd_new(["x1", "--track", "harness", "--title", "a fix s1 waits on", "--blocks", "s1", "--mechanism", "loop"])
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(c.startswith("s1 ") and "waiting on x1" in c for c in v["change"]))
        s.assertEqual([x for x in v["spawn"] if x.startswith("s1-")], [])          # the listed run is dropped, not kept
        s.assertEqual(hd.runs()[0]["reason"], "no longer due")
        s.change("s1", priority="P1")                                              # the dep dropped again
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
            hd.cmd_new(["x9", "--track", "harness", "--title", "another run's filing", "--mechanism", "loop"])
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

    def test_a_taskstop_ends_a_run_resumed_after_its_hand_back(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, usage=1, handback="run s1-1: handoff"))
            hook.bind(payload(run, "ag1", "SubagentStart", s.root))                # a SendMessage resumes it
            s.assertIsNone(hd.runs()[0]["ended"])
            stop = {"hook_event_name": "PostToolUse", "tool_name": "TaskStop", "tool_input": {"task_id": "ag1"}}
            hook.end_stopped({**stop, "tool_input": {"task_id": "b1"}})            # a background command's stop is no run's end
            s.assertIsNone(hd.runs()[0]["ended"])
            hook.end_stopped(stop)                                                 # the orchestrator kills it: no SubagentStop follows
        s.assertEqual(hd.runs()[0]["reason"], "stopped by the head")
        hd.tick(s.ctx(F))
        s.assertEqual([r["name"] for r in hd.runs() if not r.get("ended")], ["s1-2"])   # its slot and its change are free: the next run is listed

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

    def test_a_task_stopped_with_taskstop_counts_as_ended(s):
        stop = {"type": "user", "toolUseResult": {"message": "Successfully stopped task: b1", "task_id": "b1", "task_type": "local_bash"}}
        gone = {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "is_error": True,
                "content": "<tool_use_error>No task found with ID: b2</tool_use_error>"}]}}
        started = [{"type": "user", "toolUseResult": {"backgroundTaskId": i}} for i in ("b1", "b2")]
        s.assertEqual(hook.running(started), ["b1", "b2"])
        s.assertEqual(hook.running(started + [stop, gone]), [])            # stopped, or no longer found: both ended

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

    def test_hook_binds_by_brief_path(s):
        s.change("s1"); s.agreed("s1"); s.change("s2"); s.agreed("s2")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s2": A}})
        hd.tick(s.ctx(F))
        r1, r2 = hd.runs()
        hook.bind(payload(r2, "agX", "SubagentStart", s.root))        # the second listed run is spawned first
        s.assertEqual([r.get("agent_id") for r in hd.runs()], [None, "agX"])
        s.assertEqual((hd.runs()[1]["console_pid"], hd.runs()[0]["console_pid"]), (7, None))   # the hook binds the console; the pass records none
        hook.bind(payload(r2, "agX", "PreToolUse", s.root))           # a repeated bind changes nothing
        s.assertEqual(hd.runs()[1]["started"], hd.runs()[1]["started"])
        s.assertEqual(sum(1 for l in open(s.root / "state" / "events.jsonl") if '"started"' in l), 1)


    def test_the_watch_wakes_only_on_a_new_line_it_acts_on(s):
        w = s.root / "state" / "wake.orchestrator"
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s1": A}})
        hd.tick(s.ctx(F))
        s.assertIn("Agent(", w.read_text())                                     # a new spawn wakes the orchestrator
        os.utime(w, ns=(1, 1))
        hd.tick(s.ctx(F))
        s.assertEqual(w.stat().st_mtime_ns, 1)                                  # the same lines again wake nobody
        hd.put("s1", "ask", {"text": "which one?"})
        hd.tick(s.ctx(F))
        s.assertIn("s1: which one?", w.read_text())                             # a question wakes it too: it is the user's chat
        s.assertEqual(sorted(f.name for f in (s.root / "state").glob("wake*")), ["wake.orchestrator"])   # no other session's watch

    def test_a_card_wakes_once_per_head_though_it_drops_out_of_a_pass(s):
        w = s.root / "state" / "wake.orchestrator"
        c1, c2 = "s1: x\nhead aaaaaaaaa\n### body\nb", "s1: x\nhead bbbbbbbbb\n### body\nb"
        hd.wake({"card": [c1]})
        s.assertEqual(w.read_text(), "s1: x\n")                                    # its first line wakes the orchestrator
        os.utime(w, ns=(1, 1))
        hd.wake({"card": []}); hd.wake({"card": [c1]})                             # absent one pass, back at the same head
        s.assertEqual(w.stat().st_mtime_ns, 1)
        hd.wake({"card": [c2]})                                                     # its head moved: a new card
        s.assertNotEqual(w.stat().st_mtime_ns, 1)
        f = s.root / "state" / "seen.orchestrator.json"
        f.write_text(json.dumps({**json.loads(f.read_text()), "message": ["old"], "card": ["old"]}))
        hd.wake({"spawn": []})
        s.assertEqual(sorted(json.loads(f.read_text())), ["alert", "heads", "question", "spawn"])   # a key no longer watched is dropped

    def test_hooks_during_a_long_pass_never_wait_and_their_facts_are_folded(s):
        """The three cancelled-hook cases: a bind (a57c2d6..., cancelled 5 times), a run dropped 'no longer due' while its
        agent works (its dev ref appears), a hand-back landing untracked (stop-unmatched) and the deny rules skipped."""
        import time
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {"origin/HEAD": B}})                    # no dev ref yet: "dev run due"
        hd.tick(s.ctx(F))
        r = hd.runs()[0]
        with hd.lock():                                                    # a pass holds the lock the whole time
            t0 = time.monotonic()
            hook.bind(payload(r, "agX", "SubagentStart", s.root))
            hd.save_run({**r, "ended": hd.now(), "reason": "no longer due"})   # the pass drops the run it read unstarted
            with mock.patch("sys.stdin", io.StringIO(json.dumps({"hook_event_name": "PreToolUse", "agent_id": "agX", "agent_type": "dev",
                                                                  "tool_input": {"command": "python3 hd.py approve s1"}}))), \
                    mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                hook.main()
            s.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")   # the deny rule ran
            s.assertLess(time.monotonic() - t0, 1)                         # neither hook waited on the lock
        s.assertEqual((hd.runs()[0]["agent_id"], hd.runs()[0]["ended"]), ("agX", None))   # the view applies the unfolded fact
        F.f["refs"]["fork/dev/s1"] = A                                     # its agent creates the dev ref: the step's input moves
        v = hd.tick(s.ctx(F))
        saved = json.loads((s.root / "state" / "runs" / f"{r['name']}.json").read_text())
        s.assertEqual((saved["agent_id"], saved["ended"], saved["reason"]), ("agX", None, None))   # folded: the bound run is live, not dropped
        s.assertEqual([x.split(" ")[0] for x in v["run"]], [r["name"]]); s.assertEqual(v["spawn"], [])
        with hd.lock(), mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(r, "agX", "SubagentStop", s.root, usage=1, handback=f"run {r['name']}: handed over {A}"))
        s.assertFalse(any('"stop-unmatched"' in l for l in open(s.root / "state" / "events.jsonl")))
        s.assertTrue(hd.runs()[0]["ended"])
        hd.tick(s.ctx(F))
        s.assertTrue(json.loads((s.root / "state" / "runs" / f"{r['name']}.json").read_text())["ended"])   # the end folded in

    def test_a_runs_own_dev_ref_never_moves_its_input(s):
        """harness-pass-lock-short-1..4: the agent of a listed run creates its dev ref before its bind is folded; the
        run stays and no second run is listed for the change."""
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {"origin/HEAD": B}})                    # no dev ref yet: "dev run due"
        hd.tick(s.ctx(F))
        F.f["refs"]["fork/dev/s1"] = A                                     # its agent commits, unbound
        v = hd.tick(s.ctx(F))
        s.assertEqual([x.split(":")[0] for x in v["spawn"]], ["s1-1"]); s.assertFalse(hd.runs()[0]["ended"])
        hook.bind(payload(hd.runs()[0], "ag1", "SubagentStart", s.root))
        F.f["refs"]["fork/dev/s1"] = C                                     # and commits again, bound
        v = hd.tick(s.ctx(F))
        s.assertEqual(([x.split(" ")[0] for x in v["run"]], v["spawn"], len(hd.runs())), (["s1-1"], [], 1))

    def test_fold_deletes_the_facts_it_folded_and_a_fact_applies_once(s):
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        held = hd.pending_facts()                                          # a reader that read the facts before the fold
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(run, "ag1", "SubagentStop", s.root, handback="run s1-1: handoff"))
        hd.fact(fact="resumed", run=run["name"], agent_id="ag1")
        with hd.lock():
            hd.fold()
        s.assertEqual(list((s.root / "state" / "facts").iterdir()), [])  # the facts held are only those not yet folded
        r = hd.runs()[0]
        s.assertEqual((r["agent_id"], r["ended"]), ("ag1", None))         # bind, end, resumed: applied in order
        for fid, e in held:
            hd.apply_fact(r, fid, e)
        s.assertEqual((r["agent_id"], r["ended"]), ("ag1", None))         # the bind again: already in the record, skipped
        s.change("s2"); s.agreed("s2")
        hd.tick(s.ctx(Fake(**FACTS)))
        old, r2 = s.root / "state" / "facts.jsonl", next(r for r in hd.runs() if r["change"] == "s2")   # the appended file of before: folded once, then gone
        old.write_text(json.dumps({"ts": hd.now(), "fact": "end", "run": r2["name"], "usage": {}, "last": "x", "handed": True, "record": True}) + "\n")
        with hd.lock():
            hd.fold()
        s.assertEqual((old.exists(), bool(hd.runs(r2["name"])[0]["ended"])), (False, True))

    def test_a_fetch_in_flight_is_waited_on_and_its_result_taken(s):
        import threading, time
        (s.root / "state").mkdir(exist_ok=True)
        go, calls = threading.Event(), []
        class Git(hd.Facts):
            def sh(s_, args, cwd=None, env=None, timeout=600):
                if "fetch" in args:
                    calls.append(args); go.wait(5)
                return 0, "", ""
        a, b, got = Git(), Git(), {}
        t = threading.Thread(target=lambda: got.update(a=a.fetch("/c", "origin"))); t.start()
        while not calls:
            time.sleep(0.01)
        u = threading.Thread(target=lambda: got.update(b=b.fetch("/c", "origin"))); u.start()
        time.sleep(0.1)
        s.assertNotIn("b", got)                                            # the second pass waits on the fetch in flight
        go.set(); t.join(); u.join()
        s.assertEqual((got, len(calls)), ({"a": True, "b": True}, 1))     # and takes its result: one fetch
        s.assertTrue(Git().fetch("/c", "origin")); s.assertEqual(len(calls), 2)   # none in flight: a pass fetches

    def test_a_pass_reads_the_world_outside_the_lock_and_holds_it_for_milliseconds(s):
        import fcntl, threading, time
        s.change("s1"); s.agreed("s1")
        def free():
            with open(s.root / "state" / ".lock", "w") as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); return True
                except BlockingIOError:
                    return False
        reads = []; (s.root / "state").mkdir(exist_ok=True)
        class Slow(Fake):
            @hd._read
            def rev(s_, clone, ref):                                       # a slow git read, memoised as the real one is
                time.sleep(0.05); reads.append(free()); return Fake.rev(s_, clone, ref)
        F = Slow(**FACTS)
        t = threading.Thread(target=hd.tick, args=(s.ctx(F),)); t.start()
        time.sleep(0.02)
        s.assertTrue(free())                                               # the pass is reading: the lock is free
        t.join()
        s.assertTrue(reads); s.assertTrue(all(reads))                      # every read ran outside the lock, once
        s.assertEqual([r["name"] for r in hd.runs()], ["s1-1"])

    def test_a_pass_streams_the_events_file(s):
        import tracemalloc
        s.change("s1"); s.agreed("s1")
        (s.root / "state").mkdir(exist_ok=True)
        line = json.dumps({"ts": "2026-11-01T00:00:00Z", "change": "x", "state": "y" * 300}) + "\n"
        with open(s.root / "state" / "events.jsonl", "w") as f:
            f.write(line * 60000)                                          # 20 MB, the rotation size
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        hook.bind(payload(hd.runs()[0], "ag1", "SubagentStart", s.root))
        tracemalloc.start()
        for _ in range(3):
            hd.tick(s.ctx(F)); hd.produced(hd.runs()[0])
        peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
        s.assertLess(peak, 20_000_000)                                     # the file is never held, nor re-read per call

    def test_each_hook_fact_racing_a_pass_folds_over_the_pass_write(s):
        import io, contextlib
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        run = hd.runs()[0]
        hook.bind(payload(run, "ag1", "SubagentStart", s.root))
        (s.root / "state" / "s1").mkdir(exist_ok=True)
        (s.root / "state" / "s1" / "up.json").write_text('{"desktops": "desktop1:7780"}')
        bound = hd.runs()[0]
        def race(call, write):                    # the hook appends its fact; the pass, having read the run before it, saves; then folds
            hd.save_run(bound)
            with mock.patch.object(hook, "start_pass"), contextlib.redirect_stdout(io.StringIO()):
                call()
            hd.save_run({**bound, **write})
            with hd.lock():
                hd.fold()
            return hd.runs()[0]
        r = race(lambda: hook.end_run(payload(run, "ag1", "SubagentStop", s.root, usage=2, handback="run s1-1: handoff")),
                 {"ended": hd.now(), "reason": "stopped"})
        s.assertEqual((r["reason"], r.get("usage")), ("stopped", None))          # the stop wrote nothing over the pass's end
        r = race(lambda: hook.context_limit(payload(run, "ag1", "PostToolUse", s.root, usage=2, context=170000)), {"note": "pass"})
        s.assertEqual((r["note"], bool(r.get("handoff_told"))), ("pass", True))  # told, over the pass's write, not a stale copy
        r = race(lambda: hook.context_limit(payload(run, "ag1", "PostToolUse", s.root, usage=2, context=170000)), {"handoff_told": 1})
        s.assertEqual(r["handoff_told"], 1)                                       # already told by the time the lock was held
        r = race(lambda: hook.idle_desktops({**payload(run, "ag1", "PostToolUse", s.root), "tool_name": "Bash"}),
                 {"ended": hd.now(), "reason": "stopped"})
        s.assertEqual((r["reason"], r.get("play_mark")), ("stopped", None))       # no desktop count written over an ended run

    def test_an_agent_spawned_for_an_ended_run_is_stopped_at_once(s):
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        r = hd.runs()[0]
        hd.save_run({**r, "ended": hd.now(), "reason": "no longer due"})   # the pass ended it before the spawn
        def run(ev, **kw):
            with mock.patch("sys.stdin", io.StringIO(json.dumps({**payload(r, "agL", ev, s.root), **kw}))), \
                 mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                hook.main()
            return json.loads(out.getvalue() or "{}")
        start = run("SubagentStart")
        s.assertFalse(start["continue"]); s.assertIn("s1-1", start["stopReason"]); s.assertIn("no longer due", start["stopReason"])
        pre = run("PreToolUse", tool_name="Bash", tool_input={"command": "ls"})
        s.assertEqual((pre["continue"], pre["hookSpecificOutput"]["permissionDecision"]), (False, "deny"))
        s.assertEqual(run("PreToolUse", tool_name="SubagentHandback", tool_input={"message": "x"}), {})   # its hand-back goes
        x = hd.runs()[0]
        s.assertEqual((x["reason"], x.get("started"), x.get("agent_id")), ("no longer due", None, None))   # the run stays ended
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(r, "agL", "SubagentStop", s.root, handback="x"))
        s.assertEqual(hd.runs()[0]["reason"], "no longer due")
        hd.save_run({**hd.runs()[0], "ended": None, "reason": None})   # a live run: its own agent binds
        hook.bind(payload(r, "agB", "SubagentStart", s.root))
        s.assertNotIn("permissionDecision", run("PreToolUse", agent_id="agB", tool_name="Bash", tool_input={"command": "ls"})["hookSpecificOutput"])   # runs, in its slice

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

    def test_planner_trigger_is_the_subject_an_alert_names(s):
        F = Fake(**FACTS)
        ctx = s.ctx(F)
        planners = lambda: [r for r in hd.runs() if r["role"] == "planner"]
        def alert(a):
            hd.plan(s.ctx(F), {"change": [], "alert": [a], "goal": []}, True)
        for _ in range(3):
            ctx.start("s1", "ship", ["b", "T1"])
        s.assertTrue(hd.rec("s1", "proc-ship")["since"])                          # when its count started
        hd.put("s1", "proc-ship", {**hd.rec("s1", "proc-ship"), "since": "2000"})   # before the planner below
        a = "s1: ship died twice without a result (state/s1/ship.log)"
        s.change("h1", track="harness", body=f"fix: {a}")                         # an open change names the alert
        alert("s1: ship ended 3 times without a result (state/s1/ship.log)")   # reworded and recounted: still carried
        s.assertEqual(planners(), [])
        s.change("h1", track="harness", closed="answer-1: done")
        alert(a)
        p = planners()[0]
        p.update(started=hd.now(), ended=hd.now(), record=True); hd.save_run(p)   # the planner hands back on it
        alert("s1: ship ended 3 times without a result (state/s1/ship.log)")   # the same fault reworded: handled
        s.assertEqual(len(planners()), 1)
        hd.put("s1", "proc-ship", {**hd.rec("s1", "proc-ship"), "since": "9999"})   # its count started over after the hand-back
        alert("s1: ship ended 3 times without a result since 9999 (state/s1/ship.log)")   # it failed again: a new fact
        s.assertEqual(len(planners()), 2)

    def test_a_failed_head_is_the_devs_before_a_regate(s):  # sweep-31 P2-c: a gate key moved under new tools spends no CI on a head its verdict failed
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "fail: no"}, F)
        for name in ("build", "gate"):
            hd.put("s1", name, {"T": "moved", "ok": True})                       # neither matches T's key now
        st = s.state(F, "s1")
        s.assertEqual((st["state"], st["actor"], st["detail"]), ("FAIL 1 rows: dev", "dev", "j1: fail: no"))
        hd.tick(s.ctx(F)); s.assertEqual([x for x in F.spawned if x[1] in ("build", "gate")], [])

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
        hd.cmd_new(["x1", "--track", "harness", "--title", "fix something", "--mechanism", "loop"])   # the planner files a change
        with mock.patch.object(hook, "start_pass"):
            hook.end_run(payload(orc, "agO", "SubagentStop", s.root, handback="run planner-1: filed x1"))
            s.assertTrue([r for r in hd.runs() if r["role"] == "planner"][0]["record"])
            dev = [r for r in hd.runs() if r["role"] == "dev"][0]
            hook.end_run({"hook_event_name": "SubagentStop", "agent_id": "ghost", "agent_type": "dev"})  # no transcript, no id: ends nothing
        s.assertIsNone([r for r in hd.runs() if r["name"] == dev["name"]][0]["ended"])
        hook.bind({"hook_event_name": "PreToolUse", "agent_id": "x", "agent_type": "Explore"})          # not a harness role: no read
        s.assertEqual(len(hd.runs()), 2)                                                            # nothing bound or listed for it


    def test_mcp_server_restarts_on_an_mcp_change_once_none_of_its_calls_is_in_flight(s):
        d = Path(tempfile.mkdtemp()); shutil.copy(Path(__file__).parent.parent / "mcp" / "serve.py", d)
        srv = lambda v: ("import json, sys, time\nfor l in sys.stdin:\n    m = json.loads(l)\n    m['method'] == 'slow' and (print('{\"method\": \"started\"}', flush=True), time.sleep(0.3))\n"
                         f"    if 'id' in m: print(json.dumps({{'id': m['id'], 'result': '{v}' + m['method']}}), flush=True)\n")
        (d / "fake.py").write_text(srv("v1 "))
        (d / "servers.json").write_text(json.dumps({"fake": [sys.executable, str(d / "fake.py")]}))
        p = subprocess.Popen([sys.executable, str(d / "serve.py"), "fake"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        send = lambda *ms: (p.stdin.write("".join(json.dumps(m) + "\n" for m in ms)), p.stdin.flush())
        send({"id": 1, "method": "initialize"}, {"method": "notifications/initialized"})
        s.assertEqual(json.loads(p.stdout.readline()), {"id": 1, "result": "v1 initialize"})
        send({"id": 2, "method": "slow"})                                        # in flight when the ship lands
        s.assertEqual(json.loads(p.stdout.readline()), {"method": "started"})
        (d / "fake.py").write_text(srv("v2 ")); os.utime(d / "fake.py", ns=(1, 1))   # a ship moves mcp/
        send({"id": 3, "method": "tools/call"}, {"id": 4, "method": "tools/list"})
        out = [json.loads(p.stdout.readline()) for _ in range(4)]
        s.assertEqual(out, [{"id": 2, "result": "v1 slow"}, {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}, {"id": 3, "result": "v2 tools/call"},
                            {"id": 4, "result": "v2 tools/list"}])   # the new server's own initialize answer is the session's no more
        p.stdin.close(); p.wait(); p.stdout.close(); shutil.rmtree(d, ignore_errors=True)

class GH:
    """A scripted gh and git for the public act: each call recorded, answered by the first rule whose key it starts with
    (gh: its first three words; git: its words after -C <path>)."""

    def __init__(s, **answers):
        s.calls, s.a = [], {"remote": (0, "fork\tgit@github.com:o/f.git (push)\nfork\tgit@github.com:o/z.git (push)\norigin\tgit@github.com:o/c.git (push)", ""), **answers}

    def __call__(s, *args):
        s.calls.append(args)
        key = args[3] if args[0] == "git" else " ".join(args[1:3])
        v = s.a.get(key, (0, "", ""))
        return v(args) if callable(v) else v

    def did(s, key):
        return [c for c in s.calls if (c[3] if c[0] == "git" else " ".join(c[1:3])) == key]


class R4(Sandbox):
    def ready(s, F, slug="s1", head=A, **meta):
        s.change(slug, **meta); s.agreed(slug)
        s.gated(slug, F); s.verdict(slug, head, {"ok": "pass", "j1": "pass"}, F)
        hd.put("live", "tree", {"tree": "x", "commit": C, "heads": [head]})

    def ship(s, F, g, slug="s1", head=A):
        """hd ship under a scripted gh; its ship.log lines."""
        out = io.StringIO()
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "gh", g), mock.patch.object(hd.time, "sleep", lambda n: None), \
                mock.patch("sys.stdout", out):
            hd.cmd_ship([slug, head])
        return out.getvalue()

    def test_the_card_then_the_carry_only_after_the_yes_at_that_head_and_texts(s):
        F = Fake(**{**FACTS, "refs": dict(FACTS["refs"]), "trees": dict(FACTS["trees"])}); s.ready(F)
        s.assertEqual(s.state(F, "s1")["actor"], "user")                         # gated and judged: a card, nothing queued anywhere
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned, []); s.assertEqual(len(v["card"]), 1)
        s.approve(F, "s1", A)
        s.assertEqual(s.state(F, "s1")["state"], "carrying upstream")
        hd.tick(s.ctx(F)); s.assertEqual(F.spawned[-1], [str(hd.ROOT / "hd.py"), "ship", "s1", A])
        (s.root / "evidence" / "s1" / "pr-body.md").write_text("new body")      # new texts: the yes is withdrawn, the card shown again
        s.assertEqual(s.state(F, "s1")["actor"], "user")
        s.approve(F, "s1", A)
        F.f["refs"]["fork/dev/s1"] = D                                           # a new head: the yes is withdrawn
        F.f["trees"][D] = TC
        s.gated("s1", F); s.verdict("s1", D, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual((s.state(F, "s1")["actor"], s.state(F, "s1")["input"]), ("user", D))
        hd.put("s1", "ship", {"head": D, "ok": True, "detail": "x"})             # the carry's result
        hd.drop("s1", "approval")                                                # spent by the carry
        pr = {"number": 42, "branch": "content/s1", "owner": "o", "head": D, "draft": False}
        F.f["prs"] = {"u/f": [pr]}
        s.assertEqual(s.state(F, "s1")["state"], f"carried at {D[:9]}; waiting on the maintainers")
        pr["draft"] = True                                                       # the user returned it to draft: the record is not trusted
        s.assertEqual((s.state(F, "s1")["actor"], s.state(F, "s1")["input"]), ("user", D))   # a new card, no carry on the old yes
        F.f["prs"] = None
        s.assertEqual(s.state(F, "s1")["actor"], "unknown")

    def test_the_users_hold_hides_the_card_at_its_head_until_a_new_head_or_the_lift(s):
        F = Fake(**{**FACTS, "refs": dict(FACTS["refs"]), "trees": dict(FACTS["trees"])}); s.ready(F)
        def hold(*a):
            with mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
                hd.cmd_hold(["s1", *a])
        hold("not", "yet")
        s.assertNotIn("held", hd.defs("changes")["s1"])                         # a no at a head is state, bound to it as the yes is
        s.assertEqual(hd.rec("s1", "hold")["held"], f"{A}: not yet")
        s.assertEqual((s.state(F, "s1")["state"], s.state(F, "s1")["actor"]), ("held by the user: not yet", "wait"))
        s.assertEqual(hd.tick(s.ctx(F))["card"], [])
        s.assertTrue(hd.rec("s1", "hold"))                                       # at its head the pass keeps it
        F.f["refs"]["fork/dev/s1"] = D; F.f["trees"][D] = TC                     # a new head: the hold lapses, the card shows
        s.gated("s1", F); s.verdict("s1", D, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual((s.state(F, "s1")["actor"], s.state(F, "s1")["input"]), ("user", D))
        hd.tick(s.ctx(F))
        s.assertIsNone(hd.rec("s1", "hold"))                                     # the pass removes the no of a head that is gone
        hold("--all", "after the auth changes")                                  # held at every head until the lift
        s.assertEqual(hd.defs("changes")["s1"]["held"], "all: after the auth changes")
        s.assertEqual(s.state(F, "s1")["actor"], "wait")
        rows = hd.contract("s1")["rows"]
        hold("--lift", "1. Lift the hold")                                      # sweep-24: the user's word on when it ships is no answer row
        s.assertNotIn("held", (s.root / "harness" / "changes" / "s1.md").read_text())
        s.assertEqual(s.state(F, "s1")["actor"], "user")                         # no dev run: the head is unchanged scope
        s.assertEqual(hd.contract("s1")["rows"], rows)
        s.assertTrue(any(e.get("why") == "1. Lift the hold" for e in hd.evs(b'"record": "hold"')))

    def test_a_release_card_and_its_publish_after_the_yes(s):
        s.change("rel", "client", kind="release", version="0.1.3"); hd.write_contract(hd.cfg(), "rel", "client", "derived")
        (s.root / "evidence" / "rel").mkdir(parents=True, exist_ok=True); (s.root / "evidence" / "rel" / "release-notes.md").write_text("notes")
        F = Fake(**FACTS)
        hd.put("rel", "build", {"T": TB, "ok": True}); hd.put("rel", "gate", {"T": TB, "ok": True})
        s.assertEqual(s.state(F, "rel")["actor"], "user")
        c = hd.tick(s.ctx(F))["card"][0]
        s.assertIn(f"1. publish release v0.1.3 of o/c at {B}", c); s.assertIn("### release notes\nnotes", c)
        s.approve(F, "rel", B)
        s.assertEqual(s.state(F, "rel")["state"], "publishing v0.1.3")
        F.f["releases"] = {"v0.1.3"}
        s.assertEqual(s.state(F, "rel")["state"], "done")

    def test_approve_is_recorded_locally_and_refused_off_the_user_step(s):
        F = Fake(**FACTS); s.ready(F)
        g = GH()
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "gh", g), s.assertRaises(SystemExit) as e:
            hd.cmd_approve(["s1", D])
        s.assertIn("nothing to approve", str(e.exception))
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "gh", g), mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_approve(["s1", A])
        s.assertEqual(g.calls, []); s.assertEqual(hd.rec("s1", "approval")["head"], A)   # no GitHub label, no fork PR

    def test_the_card_shows_every_act_and_exact_text_and_finds_an_open_pr_by_its_branch(s):
        F = Fake(**FACTS); s.ready(F)
        ev = s.root / "evidence" / "s1"
        (ev / "pr-title.txt").write_text("feat: x"); (ev / "pr-body.md").write_text("Fixes #354 thanks @rev")
        c = hd.tick(s.ctx(F), act=False)["card"][0]
        for want in (f"head {A}", f"1. push {A} to o:content/s1 (no force)", f"2. open a draft PR on u/f from content/s1 into main (base {B[:9]})",
                     "### title\nfeat: x", "### body\nFixes #354 thanks @rev", f"### comment\n{PUSHED}", "rows pass",
                     f"evidence {s.root / 'evidence' / 's1'}", f"yes: ! python3 {hd.ROOT}/hd.py approve s1 {A}"):
            s.assertIn(want, c)
        F.f["prs"] = {"u/f": [{"number": 445, "branch": "content/s1", "owner": "other", "head": D, "draft": False}]}
        s.assertIn("2. open a draft PR", hd.tick(s.ctx(F), act=False)["card"][0])           # another owner's branch of that name: not ours
        F.f["prs"]["u/f"].append({"number": 446, "branch": "content/s1", "owner": "o", "head": D, "draft": False})
        c = hd.tick(s.ctx(F), act=False)["card"][0]
        s.assertIn("2. update upstream PR 446 of u/f", c); s.assertNotIn("### title", c)     # found by its head branch, no owner prefix: no second PR
        s.assertIn(f"upstream PR 446 is at {D[:9]}", c)

    def test_no_card_when_the_upstream_pr_is_at_the_head_with_nothing_left_to_post(s):
        s.change("s0", pr=7); s.agreed("s0"); s.change("s1", deps=["s0"], pr=7, finding=99); s.agreed("s1")
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> reset it\n\n@rev the official server keeps it.")
        com = {"id": 99, "author": "rev", "bot": False, "reply": None, "path": "N.kt", "line": 3, "body": "reset it?"}
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A, "fork/dev/s1": ""}, "comments": {7: [com]},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s0", "owner": "o", "head": A, "draft": False}]}})
        for k in ("s0", "s1"):
            s.gated(k, F); s.verdict(k, A, {"ok": "pass", "j1": "pass"}, F)
        hd.put("live", "tree", {"tree": "x", "commit": C, "heads": [A]})
        c = hd.tick(s.ctx(F), act=False)["card"]                                  # the reply is left to post: a card
        s.assertEqual(len(c), 1); s.assertIn("### comment\n(finding by rev on N.kt:3: reset it?)\n> reset it\n\n@rev the official", c[0])
        s.assertNotIn("push", c[0]); s.assertIn("4. request review from rev", c[0])   # at the head already, a reply-only change: no push, the reply its one comment
        F.f["comments"][7].append({"id": 100, "author": "O", "bot": False, "reply": 99, "path": "N.kt", "line": 3, "body": "ours"})
        s.assertEqual(hd.tick(s.ctx(F), act=False)["card"], [])                   # ours is in its thread: nothing left, no card
        s.assertTrue(s.state(F, "s1")["state"].startswith(f"carried at {A[:9]}"))
        F.f["prs"]["u/f"][0]["draft"] = True
        s.assertEqual(len(hd.tick(s.ctx(F), act=False)["card"]), 1)              # still draft: left to mark ready

    def test_the_carry_opens_the_draft_waits_for_green_ci_comments_readies_and_records_it(s):
        F = Fake(**FACTS); s.ready(F)
        s.approve(F, "s1", A); texts = hd.rec("s1", "approval")["texts"]
        b = lambda st: [{"name": "build", "url": "https://ci/1", "state": st}]
        F.f.update(pull={42: {"branch": "content/s1", "head": A, "draft": True, "requested": []}}, ci=[b("pending"), b("success")])
        g = GH(**{"pr create": (0, "https://github.com/u/f/pull/42", "")})
        log = s.ship(F, g)
        order = [c[3] if c[0] == "git" else " ".join(c[1:3]) for c in g.calls if c[0] == "gh" or c[3] == "push"]
        s.assertEqual(order, ["push", "pr create", "pr comment", "pr ready"])  # every read goes through Facts, never gh pr view
        steps = [l.split(" ", 1)[1] for l in log.splitlines()]                   # ship.log: each step as it goes, the CI wait naming its checks
        s.assertEqual([x.split(":")[0].split(" ")[0] for x in steps[:4]], ["pushed", "opened", "CI", "CI"]); s.assertIn("CI wait: pending: build https://ci/1", steps)
        s.assertIn(f"CI green at {A[:9]}: build https://ci/1", steps); s.assertTrue(steps[-2].startswith("review request: none listed")); s.assertTrue(steps[-1].startswith(f"carried: upstream PR 42 at {A[:9]}"))
        s.assertEqual(g.did("push")[0][-1], f"{A}:refs/heads/content/s1")       # no force
        s.assertEqual(g.did("pr create")[0][g.did("pr create")[0].index("-R") + 1], "u/f")
        s.assertTrue(g.did("pr comment")[0][-1].startswith(PUSHED))
        s.assertEqual((hd.rec("s1", "opened")["pr"], hd.rec("s1", "ship")["head"]), (42, A))   # a rerun updates PR 42; the pass never carries again
        F.f["prs"] = {"u/f": [{"number": 42, "branch": "content/s1", "owner": "o", "head": A, "draft": True}]}
        ctx = s.ctx(F); s.assertEqual((ctx.changes["s1"]["pr"], ctx.changes["s1"]["opened"]), (42, A))
        s.assertIsNone(hd.rec("s1", "approval"))                                 # the yes is spent by the carry
        hd.put("s1", "approval", {"head": A, "texts": texts})                    # a new yes at the same texts
        s.assertTrue(hd.approved(ctx, ctx.changes["s1"], A))                    # the PR it opened: the yes holds on a rerun
        F.f["ci"] = [b("failure")]; g = GH()
        with s.assertRaises(SystemExit) as e:
            s.ship(F, g)
        s.assertIn("CI failure", str(e.exception))
        s.assertEqual(g.did("pr ready") + g.did("pr create"), [])               # stays draft, no second PR
        s.assertIn("build https://ci/1", str(e.exception))
        F.f["ci"] = [None]; g = GH()
        with s.assertRaises(SystemExit) as e:                                    # a CI read that fails ends the wait, never loops on it
            s.ship(F, g)
        s.assertIn(f"the checks of u/f at {A[:9]} cannot be read", str(e.exception)); s.assertEqual(g.did("pr ready"), [])

    def test_every_carry_stop_is_its_result_and_a_ci_failure_outside_the_head_is_re_run(s):
        F = Fake(**FACTS); s.ready(F); s.approve(F, "s1", A)
        url = "https://github.com/u/f/actions/runs/5/job/6"
        b = lambda st: [{"name": "build", "url": url, "state": st}]
        F.f.update(pull={42: {"branch": "content/s1", "head": A, "draft": True, "requested": []}}, jobs={"6": {"attempt": 1, "step": "Generate cache and gameval sources"}})
        classify = lambda rc: mock.patch.object(hd.subprocess, "run", lambda a, **k: subprocess.CompletedProcess(a, rc, "", ""))
        F.f["ci"] = [b("failure"), b("failure"), b("success")]                   # the re-run's attempt not yet listed: the old failure, waited on
        g = GH(**{"pr create": (0, "https://github.com/u/f/pull/42", "")})
        with classify(0):                                                        # the gate's classifier: a step the head does not read
            log = s.ship(F, g)
        s.assertEqual(g.did("run rerun"), [("gh", "run", "rerun", "5", "--failed", "-R", "u/f")])   # once, never a FAIL
        s.assertIn("failed outside the head", log); s.assertTrue(hd.rec("s1", "ship")["ok"])
        F.f["prs"] = {"u/f": [{"number": 42, "branch": "content/s1", "owner": "o", "head": A, "draft": True}]}
        hd.drop("s1", "ship"); s.approve(F, "s1", A)
        F.f["ci"] = [b("failure")]; g = GH()
        with classify(1), s.assertRaises(SystemExit):                            # a step the head reads: the change's FAIL, its dev step
            s.ship(F, g)
        sh = hd.rec("s1", "ship")
        s.assertEqual((sh["ok"], sh["fault"], g.did("run rerun")), (False, "head", [])); s.assertIn("Generate cache and gameval sources", sh["detail"])
        st = s.state(F, "s1"); s.assertEqual((st["actor"], st["state"]), ("dev", f"FAIL upstream at {A[:9]}: dev"))
        ho = hd.rec("s1", "handover")
        with mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):    # its dev hands the same head over: the cause is outside it, filed
            hd.put("s1", "handover", {k: v for k, v in ho.items() if k != "ts"})
        st = s.state(F, "s1"); s.assertEqual((st["actor"], st["state"]), ("script", "carrying upstream"))   # the upstream check runs again
        F.f["ci"] = [b("failure"), b("success")]; g = GH()
        with classify(1):                                                        # the step it vouched for is re-run, though the classifier reads it
            s.ship(F, g)
        s.assertEqual(len(g.did("run rerun")), 1); s.assertTrue(hd.rec("s1", "ship")["ok"])
        hd.put("s1", "handover", ho); s.approve(F, "s1", A); F.f["ci"] = [b("failure")]
        hd.drop("s1", "ship")
        F.f["jobs"]["6"]["attempt"] = 3; g = GH()
        with classify(0), s.assertRaises(SystemExit):                            # outside the head at its 3rd attempt: the carry's result, no FAIL
            s.ship(F, g)
        s.assertEqual((hd.rec("s1", "ship")["fault"], hd.rec("s1", "approval")), ("carry", None))   # the yes spent: the card again
        st = s.state(F, "s1"); s.assertEqual(st["actor"], "user")
        s.assertIn(f"the last carry at {A[:9]} stopped: CI failed at 'Generate cache and gameval sources' in 3 attempts", hd.tick(s.ctx(F), act=False)["card"][0])
        s.approve(F, "s1", A); F.f["ci"] = [b("success")]
        F.f["prs"] = {"u/f": [{"number": 42, "branch": "content/s1", "owner": "o", "head": A, "draft": True, "title": "t", "body": "old"}]}
        (s.root / "evidence" / "s1" / "pr-body.md").write_text("new body"); s.approve(F, "s1", A)
        g = GH(**{"api -X": (1, "", "GraphQL: Projects (classic) is being deprecated")})
        with s.assertRaises(SystemExit) as e:                                    # a GitHub write refused: recorded, never relaunched by the pass
            s.ship(F, g)
        s.assertIn("Projects (classic)", str(e.exception)); s.assertEqual(hd.rec("s1", "ship")["fault"], "carry")
        s.assertEqual(s.state(F, "s1")["actor"], "user"); hd.tick(s.ctx(F)); s.assertEqual(F.spawned, [])

    def test_a_reply_with_no_commit_is_carried_into_its_thread_with_the_pr_tip(s):
        s.change("s0", pr=7); s.change("s1", deps=["s0"], pr=7, finding=99); s.agreed("s1")
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> reset it\n\n@rev the official server keeps it.")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A, "fork/dev/s1": ""}, "prs": {"u/f": [{"number": 7, "branch": "fix/x", "owner": "o", "head": A, "draft": False}]},
                    "comments": {7: [{"id": 99, "author": "rev", "bot": False, "reply": None, "path": "N.kt", "line": 3, "body": "reset it?"}]}})
        s.assertEqual(s.ctx(F).head(s.ctx(F).changes["s1"]), A)                 # no commit of its own: its PR tip's head
        s.gated("s1", F); s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        hd.put("live", "tree", {"tree": "x", "commit": C, "heads": [A]})
        ctx = s.ctx(F)
        s.assertEqual((hd.outside(ctx, ctx.changes["s0"], A), hd.outside(ctx, ctx.changes["s1"], A)), (["s1"], []))   # one card, at the PR's tip
        s.assertEqual(hd.public_texts(ctx, ctx.changes["s1"]), [["comment", [99], "> reset it\n\n@rev the official server keeps it."], ["review request", None, "rev"]])
        s.approve(F, "s1", A)
        F.f["pull"] = {7: {"branch": "fix/x", "head": A, "draft": False, "requested": ["rev"]}}
        g = GH(); log = s.ship(F, g)
        s.assertEqual(g.did("push") + g.did("pr ready"), [])                  # the PR is at the head: no push, already ready
        s.assertTrue(g.did("pr comment")[0][-1].startswith("> reset it\n\n@rev the official server keeps it."))   # one PR comment, quoting the inline finding
        s.assertEqual([c[4:] for c in g.calls if "POST" in c], [("repos/u/f/pulls/7/requested_reviewers", "-f", "reviewers[]=rev")])   # ready already: review asked
        s.assertIn("review requested from rev", log)
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> reset it\n\n@rev and @other"); hd.drop("s1", "ship")
        s.approve(F, "s1", A)
        g = GH()
        with s.assertRaises(SystemExit) as e:
            s.ship(F, g)
        s.assertIn("name only ['rev']", str(e.exception)); s.assertEqual(g.did("pr comment"), [])
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> keep it\n\n@rev kept"); s.approve(F, "s1", A)
        with s.assertRaises(SystemExit) as e:                                    # a quote that is not the finding's: not an answer
            s.ship(F, GH())
        s.assertIn("must quote [99]", str(e.exception))

    def test_a_round_answered_with_no_code_is_one_dev_and_one_qa_run_with_no_gate(s):
        s.change("s0", pr=7); s.change("s1", deps=["s0"], pr=7, finding=[98, 99]); hd.write_contract(hd.cfg(), "s1", "server", "derived")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A, "fork/dev/s1": ""},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s0", "owner": "o", "head": A, "draft": False}]}})
        s.assertEqual(s.state(F, "s1")["state"], "contract: finding rows 98, 99 added")   # each finding a judged row, by the pass
        with mock.patch.object(hd, "now", lambda: "2000-01-01T00:00:00Z"):
            hd.tick(s.ctx(F))
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["state"]), ("dev", f"dev run due: head {A[:9]} not handed over"))   # the dev answers the round: no contract run
        for f in (98, 99):
            (s.root / "evidence" / "s1" / f"pr-reply-{f}.md").write_text(f"> point {f}\n\n@rev kept.")
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_handover(["s1", "Limits:", "none"])                    # no commit: its head is the PR tip's
        s.assertEqual(s.state(F, "s1")["state"], "review due")             # no build, no gate: one qa judges every row
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertNotIn(s.state(F, "s1")["actor"], ("qa", "dev"))
        s.assertEqual([x for x in F.spawned if x[1] in ("build", "gate")], [])
        s.verdict("s1", A, {"ok": "pass", "j1": "fail: 99 needs code"}, F)  # a finding that needs code: the round's dev stacks a commit
        s.assertEqual(s.state(F, "s1")["actor"], "dev")
        F.f["refs"]["fork/dev/s0"] = C; F.f["trees"][C] = TA; F.f["merges"][(B, C)] = ("ok", C); s.agreed("s0"); s.gated("s0", F)   # the PR tip moves while the dev fixes: still the dev's, no reply run
        s.assertEqual(s.state(F, "s1")["state"], f"dev run due: head {C[:9]} not handed over")

    def test_an_update_with_a_finding_replaces_the_body_comments_every_commit_and_replies_only_the_answer(s):
        F = Fake(**{**FACTS, "comments": {7: [{"id": 99, "author": "rev", "bot": False, "reply": None, "path": "G.kt", "line": 213, "body": "bank?"}]},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s1", "owner": "o", "head": D, "draft": False, "title": "t", "body": "old" + hd.ATTRIBUTION}]}})
        s.ready(F, pr=7, finding=99)                                             # two commits (C, A) pushed on top of the live head D
        ev = s.root / "evidence" / "s1"
        (ev / "pr-body.md").write_text("new body")
        (ev / "pr-comment.md").write_text(f"Pushed {C[:9]} and {A[:9]} on top of {D[:9]} (head {A[:9]}).\n\n- {C[:9]}: one.\n- {A[:9]}: two.")
        (ev / "pr-reply-99.md").write_text("> bank?\n\n@rev it gives the lamp there now." + hd.ATTRIBUTION)   # a text already signed: signed once
        t = {w: x for w, _, x in hd.public_texts(s.ctx(F), s.ctx(F).changes["s1"])}
        s.assertEqual(sorted(t), ["body", "comment", "review request"])   # the title is live already: no title step
        s.assertTrue(C[:9] in t["comment"] and A[:9] in t["comment"])
        s.assertTrue(t["comment"].endswith("\n\n> bank?\n\n@rev it gives the lamp there now."))   # one comment: the push summary, then the reply
        c = hd.tick(s.ctx(F), act=False)["card"][0]
        s.assertIn("update upstream PR 7 of u/f (base main", c); s.assertIn("replacing its body with the one below", c); s.assertIn("### body\nnew body", c)
        s.approve(F, "s1", A)
        F.f.update(pull={7: [{"branch": "content/s1", "head": h, "draft": False, "requested": []} for h in (D, A)]}, ci=[[{"name": "b", "url": "", "state": "success"}]])
        g = GH(**{"api repos/u/f/pulls/comments/99": (0, "rev", "")})
        s.ship(F, g)
        s.assertEqual(g.did("api -X")[0][2:], ("-X", "PATCH", "repos/u/f/pulls/7", "-f", "body=new body" + hd.ATTRIBUTION))   # REST: gh pr edit reads Projects (classic)
        s.assertTrue(g.did("pr comment")[0][-1].startswith(t["comment"])); s.assertEqual(len(g.did("pr comment")), 1)
        s.assertEqual([c[4] for c in g.calls if "POST" in c], ["repos/u/f/pulls/7/requested_reviewers"])   # no thread reply: the comment answers it
        F.f["prs"]["u/f"][0]["body"] = "new body" + hd.ATTRIBUTION                 # the live body matches: no body step
        s.assertNotIn("body", [w for w, _, _ in hd.public_texts(s.ctx(F), s.ctx(F).changes["s1"])])
        live = {"branch": "content/s1", "head": A, "draft": False, "requested": [], "title": "T", "body": "new body" + hd.ATTRIBUTION}
        F.f.update(pull={7: [live, live]}); g = GH()
        with mock.patch.object(hd, "gh", g), mock.patch.object(hd, "log", lambda m: None):
            hd.carry(s.ctx(F), s.ctx(F).changes["s1"], A, [("title", None, "T"), ("body", None, "new body")])
        s.assertEqual(g.did("api -X"), [])                                      # the card's title and body are the live ones: no edit call (PR 448: 11 failed edits)

    def test_a_comment_not_naming_every_pushed_commit_goes_back_to_dev_with_no_card(s):
        F = Fake(**{**FACTS, "commits": {A: {C, A}}, "prs": {"u/f": [{"number": 7, "branch": "content/s1", "owner": "o", "head": D, "draft": False}]}})
        s.ready(F, pr=7)                                                         # the push adds C and A on top of the live head D
        ev = s.root / "evidence" / "s1" / "pr-comment.md"
        ev.write_text(f"Pushed {C[:9]} on top of {D[:9]}.")                      # stale: written before the head moved to A
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["input"]), ("dev", ["comment", A, [A]])); s.assertIn(A[:9], st["detail"])
        s.assertEqual(hd.tick(s.ctx(F), act=False)["card"], [])
        ev.write_text("")                                                        # no comment: no generic text, back to dev
        s.assertEqual(s.state(F, "s1")["input"], ["comment", A, [A, C]])
        ev.write_text(f"Pushed {C[:9]} and {A[:9]}.")
        s.assertEqual(s.state(F, "s1")["actor"], "user")
        s.assertIn(f"### comment\nPushed {C[:9]} and {A[:9]}.", hd.tick(s.ctx(F), act=False)["card"][0])
        s.assertIn(["fetch", "origin", "pull/7/head"], F.ran)                   # the live head D, absent from the clone, is fetched by the PR

    def test_the_rounds_one_comment_answers_every_open_finding_before_its_card(s):
        com = lambda i: {"id": i, "author": "rev", "bot": False, "reply": None, "path": "G.kt", "line": i, "body": f"point {i}"}
        F = Fake(**{**FACTS, "commits": {A: {A}}, "comments": {7: [com(98), com(99)]}, "prs": {"u/f": [{"number": 7, "branch": "content/s1", "owner": "o", "head": D, "draft": False}]}})
        s.ready(F, pr=7, finding=[98, 99])
        ev = s.root / "evidence" / "s1"
        (ev / "pr-reply-98.md").write_text("> point 98\n\n@rev fixed.")                # 99 answered nowhere
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["input"]), ("dev", ["findings", A, [99]])); s.assertEqual(hd.tick(s.ctx(F), act=False)["card"], [])
        (ev / "pr-reply-99.md").write_text("> point 99\n\n@rev fixed too.")
        s.assertEqual(s.state(F, "s1")["actor"], "user")
        s.assertEqual([f for w, f, _ in hd.public_texts(s.ctx(F), s.ctx(F).changes["s1"]) if w == "comment"], [[98, 99]])

    def test_a_fix_filed_on_a_pr_joins_its_open_round(s):
        s.change("s1", pr=7, branch="content/s1"); s.agreed("s1"); s.change("h9", "harness")
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_new(["s1-fix", "--track", "server", "--title", "the dump's accuracy fix", "--pr", "7", "--deps", "h9", "--body", "check it against the dump"])
        g = hd.defs("changes")
        s.assertNotIn("s1-fix", g); s.assertIn("h9", g["s1"]["deps"])                 # no change of its own: the round takes it and its wait
        s.assertIn("filed by s1-fix: the dump's accuracy fix", hd.contract("s1")["rows"][-1]["text"])

    def test_a_new_prs_comment_names_only_its_head(s):
        F = Fake(**{**FACTS, "commits": {A: {C, A}}})                            # main..head holds C and A: a new PR names only A
        s.ready(F)
        ev = s.root / "evidence" / "s1" / "pr-comment.md"
        ev.write_text(f"Opens the PR at {C[:9]}.")
        s.assertEqual(s.state(F, "s1")["input"], ["comment", A, [A]])
        ev.write_text(f"Opens the PR at {A[:9]}.")
        s.assertEqual(s.state(F, "s1")["actor"], "user")

    def test_a_central_change_is_carried_to_centrals_upstream(s):
        s.change("z1", "central"); s.agreed("z1", "central"); s.change("s1", deps=["z1"]); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/z1": D}, "trees": {**FACTS["trees"], D: TC}, "merges": {(B, D): ("ok", D)}})
        s.assertEqual(s.state(F, "s1")["state"], "waiting on z1")
        s.gated("z1", F)                                                         # its test target is its gate: live, the server change goes on
        s.assertNotEqual(s.state(F, "s1")["actor"], "wait")
        s.verdict("z1", D, {"ok": "pass", "j1": "pass"}, F)
        s.approve(F, "z1", D)
        F.f.update(pull={3: {"branch": "content/z1", "head": D, "draft": True, "requested": []}}, ci=[[{"name": "b", "url": "", "state": "success"}]])
        g = GH(**{"pr create": (0, "https://github.com/u/z/pull/3", "")})
        s.ship(F, g, "z1", D)
        s.assertEqual(g.did("push")[0][2], str(s.root / "central"))
        cr = g.did("pr create")[0]; s.assertEqual(cr[cr.index("-R") + 1], "u/z")
        s.ready(F, deps=["z1"])                                                  # the server PR is gated and judged: no card while Central's PR is unmerged
        s.assertEqual((s.state(F, "s1")["state"], s.state(F, "s1")["actor"]), ("waiting on z1's upstream merge", "wait"))
        F.f["anc"] = {(B, D)}                                                    # Central's main holds z1: the hold lifts (the server rebuilds without it)
        s.assertEqual(s.state(F, "s1")["state"], "building tatatatat-cbbbbbbbb")   # the state names the key: the Central part too

    def test_a_card_waiting_on_a_held_dependency_card_is_one_alert_and_holds_no_dev_work(s):
        s.change("z1", "central"); s.agreed("z1", "central"); s.change("c1", "client", deps=["s1"])
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/z1": D}, "trees": {**FACTS["trees"], D: TC}, "merges": {(B, D): ("ok", D)}})
        s.gated("z1", F)
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_hold(["z1", "the", "auth", "bundle"])                         # the user holds Central's card until the auth bundle
        s.ready(F, deps=["z1"])                                                  # gated on the fork, live on the test server
        s.assertEqual((s.state(F, "s1")["state"], s.state(F, "s1")["actor"]), ("waiting on z1's upstream merge; its card is held by the user", "wait"))
        v = hd.tick(s.ctx(F), act=False)
        s.assertEqual([a for a in v["alert"] if "z1's upstream merge" in a],
                      ["user: s1's card waits on z1's upstream merge, whose card the user holds: the auth bundle: lift it (hd hold z1 --lift) or hold this card too"])
        s.assertFalse(any(x.startswith("planner-") for x in v["spawn"]))       # the user's alert: no planner run is listed on it
        s.assertNotEqual(s.state(F, "c1")["actor"], "wait")                     # dev work goes on past the contribution queue: s1 is on the fork
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_hold(["s1", "bundled", "later"])                              # the user holds this card too: the alert's other way out
        s.assertFalse([a for a in hd.tick(s.ctx(F), act=False)["alert"] if "z1's upstream merge" in a])

    def test_a_finding_on_the_pr_conversation_is_answered_by_a_pr_comment_once(s):
        s.change("s0", pr=7); s.agreed("s0"); s.change("s1", deps=["s0"], pr=7, finding="IC_x"); s.agreed("s1")
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> get the cutscene in\n\n@rev it is in.")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A, "fork/dev/s1": ""}, "talk": {7: [{"id": "IC_x", "author": "rev", "body": "get the cutscene in"}]},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s0", "owner": "o", "head": A, "draft": False}]}})
        for k in ("s0", "s1"):
            s.gated(k, F); s.verdict(k, A, {"ok": "pass", "j1": "pass"}, F)
        c = hd.tick(s.ctx(F), act=False)["card"]
        s.assertEqual(len(c), 1); s.assertIn("### comment\n(finding by rev on the PR: get the cutscene in)", c[0]); s.assertNotIn("request review", c[0])   # a conversation commenter is no reviewer
        s.approve(F, "s1", A)
        F.f["pull"] = {7: {"branch": "content/s0", "head": A, "draft": False, "requested": []}}
        g = GH()
        s.ship(F, g)
        s.assertTrue(g.did("pr comment")[0][-1].startswith("> get the cutscene in\n\n@rev it is in." + hd.ATTRIBUTION + "\n<!-- hd:"))   # one comment, marked by head and text
        F.f["talk"][7].append({"id": "IC_y", "author": "O", "body": "> get the cutscene in\n\n@rev it is in." + hd.ATTRIBUTION})
        hd.drop("s1", "ship")
        s.assertEqual(hd.tick(s.ctx(F), act=False)["card"], [])                   # ours is on the PR: nothing left, no card

    def test_hook_denies_approve_and_close_in_subagent_only(s):
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for verb in ("approve s1 " + A, "close s1 done"):
                hook.deny_users_word({"agent_id": "a1", "agent_type": "dev", "tool_input": {"command": "python3 ~/osrs-harness/hd.py " + verb}})
                hook.deny_users_word({"tool_input": {"command": "python3 ~/osrs-harness/hd.py " + verb}})          # no agent: allowed (the user's `!` fires no hook at all)
                hook.deny_users_word({"agent_type": "orchestrator", "tool_input": {"command": "hd " + verb}})      # the orchestrator session: denied
            for c in ("cd x && hd approve s1 " + A, "X=1 ~/osrs-harness/hd.py close s1 done", "bash -c 'hd.py approve s1'"):      # runs it: denied
                hook.deny_users_word({"agent_id": "a1", "agent_type": "dev", "tool_input": {"command": c}})
            for c in ("grep approve notes.md; git push fork HEAD:dev/s1", "grep -n 'hd approve' hook.py",   # only quotes it: allowed
                      "cat > f.md <<'EOF'\nhd close s1 done\nEOF\ngit add f.md", "echo \"hd.py approve\" | wc",
                      "grep -nE 'x|hd.py approve|y' hook.py", "grep -c \"(hd close|z)\" f", "gh pr view 5 --json labels"):
                hook.deny_users_word({"agent_id": "a1", "agent_type": "dev", "tool_input": {"command": c}})
        s.assertEqual(out.getvalue().count('"deny"'), 7)

    def test_dry_run_check_fails_only_on_an_act_main_never_plans(s):
        repo, build = s.root / "live", s.root / "cand"
        (repo / "tools").mkdir(parents=True); build.mkdir()
        shutil.copy(Path(__file__).parent.parent / "tools" / "track.sh", repo / "tools")
        n = repo / "n"; n.write_text("0")
        (repo / "hd.py").write_text(f"import pathlib\np = pathlib.Path({str(n)!r}); k = int(p.read_text()) + 1; p.write_text(str(k))\n"
                                    "if k > 1: print('change: a [server P2]: carrying upstream')\n")   # a's approval lands after main's first read
        check = lambda acts: ((build / "hd.py").write_text("".join(f"print('change: {a} [server P2]: carrying upstream')\n" for a in acts)),
                              subprocess.run([str(repo / "tools" / "track.sh"), "check-dry-run"], env={**os.environ, "BUILD": str(build)}, capture_output=True, text=True))[1]
        s.assertEqual(check(["a"]).returncode, 0)                                # the state moved mid-check: no extra act
        n.write_text("0"); r = check(["a", "b"])                                 # the candidate's code plans b
        s.assertNotEqual(r.returncode, 0); s.assertIn("change: b", r.stdout); s.assertNotIn("change: a", r.stdout)


class R7(Sandbox):
    def test_a_command_missing_an_argument_prints_its_usage(s):
        for argv, u in ((["rows"], "usage: hd rows <slug>[,<slug>...] <tcommit> <build copy>"), (["show"], "usage: hd show <slug> ...")):
            with s.assertRaises(SystemExit) as e:
                hd.main(argv)
            s.assertEqual(str(e.exception.code), u)

    def test_view_has_only_the_seven_sections_and_states_are_facts(s):
        s.change("s1"); s.agreed("s1"); s.change("c1", "client"); hd.put("s1", "ask", {"text": "scope?"})
        v = hd.tick(s.ctx(Fake(**FACTS)))
        s.assertEqual(list(v), ["spawn", "card", "question", "run", "goal", "change", "alert"])
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
    LIVE = hd.P(hd.yaml.safe_load((Path(__file__).resolve().parents[1] / "hd.yaml").read_text())["repos"]["harness"]["path"])

    @unittest.skipUnless((LIVE / "state" / "runs").is_dir(), "no live state on this machine")
    def test_a_pass_on_the_live_state_stays_under_200_mb(s):
        """The pass process's own peak (its builds and gates run in their own scopes), on the live state, dry."""
        code = ("import resource, sys; sys.path.insert(0, sys.argv[1]); import hd; hd.tick(act=False); "
                "print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)")
        out = subprocess.run([sys.executable, "-c", code, str(Path(__file__).resolve().parents[1])], env={**os.environ, "HD_ROOT": str(s.LIVE), "HD_OFFLINE": "1"},
                             capture_output=True, text=True, timeout=600)
        s.assertEqual(out.returncode, 0, out.stderr[-500:])
        s.assertLess(int(out.stdout.split()[-1]), 200 * 1024)            # ru_maxrss in KiB

    def test_a_dry_run_never_reaches_the_network(s):
        """hd tick --dry-run (check-dry-run's, inside a gate): git from the local refs alone, GitHub from the cache alone."""
        s.change("s1"); s.agreed("s1")                                           # a server change: its clone's remotes are fetched by a pass
        net = []
        class Net(Fake):
            fetch, page = hd.Facts.fetch, hd.Facts.page
            def sh(s_, args, cwd=None, env=None, timeout=600):
                if "fetch" in args or "set-head" in args or args[:1] == ["gh"]:
                    net.append(args)
                return super().sh(args, cwd, env, timeout)
        F = Net(**FACTS)
        with mock.patch.dict(os.environ), mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_tick(["--dry-run"])
            F.page("repos/u/f/pulls?state=open&per_page=100")
        s.assertEqual(net, [])
        s.assertTrue(F.fetch("/c", "origin"))                                    # the env is the pass's alone: a real pass still fetches
        s.assertTrue(any("fetch" in a for a in net))

    def test_github_reads_are_conditional_shared_and_held_on_an_exhausted_quota(s):
        """Two passes and a gate over the same state: the first pass reads each GitHub resource once, the second only
        revalidates (304s, no quota), the gate's dry-run reads the cache alone; an exhausted quota is an alert and reads nothing."""
        s.change("s1", pr=7); s.agreed("s1")
        api = {"repos/u/f/pulls?state=open&per_page=100": [{"number": 7, "head": {"ref": "content/s1", "sha": A, "repo": {"owner": {"login": "o"}}}, "draft": False, "title": "t", "body": "b"}],
               "repos/u/f/pulls/7/comments?per_page=100": [{"id": 99, "user": {"login": "rev", "type": "User"}, "in_reply_to_id": None, "path": "N.kt", "line": 3, "body": "reset it?"}],
               "repos/u/f/issues/7/comments?per_page=100": [], "repos/u/f/pulls/7/reviews?per_page=100": []}
        calls, quota = [], {}

        class GitHub(Fake):  # the real GitHub reads of Facts, over a GitHub that answers 304 to a matching If-None-Match
            review_comments, pr_comments, open_prs = hd.Facts.review_comments, hd.Facts.pr_comments, hd.Facts.open_prs
            def sh(s_, args, cwd=None, env=None, timeout=600):
                if args[:2] != ["gh", "api"]:
                    return super().sh(args, cwd, env, timeout)
                url, tag = args[-1], f'"{hashlib.sha1(json.dumps(api[args[-1]]).encode()).hexdigest()}"'
                calls.append((url, "If-None-Match: " + tag in args))
                if quota:
                    return 1, f"HTTP/2.0 403 Forbidden\nX-Ratelimit-Remaining: 0\nX-Ratelimit-Reset: {quota['reset']}\n\n{{\"message\": \"API rate limit exceeded\"}}", ""
                if "If-None-Match: " + tag in args:
                    return 1, "HTTP/2.0 304 Not Modified\n\n", "gh: HTTP 304"
                return 0, f"HTTP/2.0 200 OK\nEtag: {tag}\n\n{json.dumps(api[url])}", ""

        F = Fake(**FACTS); s.gated("s1", F); s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)   # due upstream: the open PRs are read too
        hd.tick(s.ctx(GitHub(**FACTS)))                                         # pass 1: a dry pass and the pass under the lock
        s.assertEqual(sorted(u for u, _ in calls), sorted(api))                 # each resource read once, whatever reads it
        calls.clear(); hd.tick(s.ctx(GitHub(**FACTS)))                          # pass 2, the same state: every read revalidates
        s.assertEqual(sorted(calls), sorted((u, True) for u in api))            # all conditional: GitHub answers 304, no quota spent
        calls.clear()
        with mock.patch.dict(os.environ, {"HD_OFFLINE": "1"}):                   # the gate's dry-runs (check-dry-run): the cache alone
            hd.tick(s.ctx(GitHub(**FACTS)), act=False)
            s.assertEqual(GitHub(**FACTS).review_comments("u/f", 7)[0]["author"], "rev")   # what the passes read
        s.assertEqual(calls, [])
        cr = {"repos/u/f/pulls/7?per_page=100": {"head": {"ref": "content/s1", "sha": A}, "draft": False, "requested_reviewers": [{"login": "rev"}]},
              f"repos/u/f/commits/{A}/check-runs?per_page=100": {"total_count": 1, "check_runs": [{"name": "build", "details_url": "https://ci/1", "status": "completed", "conclusion": "success"}]},
              f"repos/u/f/commits/{A}/status?per_page=100": {"state": "pending", "statuses": []}}
        api.update(cr); g = type("C", (GitHub,), {"pr": hd.Facts.pr, "ci": hd.Facts.ci})(**FACTS)
        s.assertEqual(hd.checks(g, "u/f", 7, A), ("success", "build https://ci/1", ["https://ci/1"]))    # the carry's CI wait: the same cache
        s.assertEqual(sorted(u for u, _ in calls), sorted(cr))
        calls.clear(); hd.checks(g, "u/f", 7, A)                                # its next poll: each read afresh and conditional
        s.assertEqual(sorted(calls), sorted((u, True) for u in cr))
        s.assertEqual(g.pr("u/f", 7)["requested"], ["rev"])
        src = (Path(hd.__file__).read_text()).split("\n")                       # no GitHub read in hd.py bypasses Facts.page
        s.assertEqual([l for l in src if re.search(r'"gh", "(api|pr|release)"', l) and not re.search(r'"-X", "(POST|PATCH)"|"(comment|create|ready)"', l)
                       and "If-None-Match" not in l], [])
        calls.clear()
        quota["reset"] = int(time.time()) + 3600
        shutil.rmtree(hd.STATE / "gh")                                          # nothing cached: every read goes to GitHub
        v = hd.tick(s.ctx(GitHub(**FACTS)))
        s.assertEqual(len(calls), 1, calls)                                     # the first refusal holds every later read
        s.assertTrue(any(a.startswith("github: API quota exhausted") for a in v["alert"]), v["alert"])
        calls.clear(); hd.tick(s.ctx(GitHub(**FACTS)), act=False)
        s.assertEqual(calls, [])                                                # held until GitHub's reset: no read spends a refusal

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

    def test_a_reader_racing_the_writers_never_sees_a_half_written_record(s):
        import threading
        sh = Path(__file__).parent.parent / "tools" / "track.sh"
        rec_fn = re.search(r"^record\(\).*?^}", sh.read_text(), re.S | re.M).group(0)   # the track script's own writer
        loop = f'state={hd.STATE / "s1"}; T=t; {rec_fn}\nfor i in $(seq 40); do record true gate <<< "x$i"; done'
        stop, seen = threading.Event(), []
        def read():
            while not stop.is_set():
                try:
                    seen.append(hd.rec("s1", "gate"))
                except ValueError as e:                                           # an empty or partial file
                    seen.append(e)
        r = threading.Thread(target=read); r.start()
        try:
            subprocess.run(["bash", "-c", loop], check=True)
            for i in range(200):
                hd.put("s1", "gate", {"T": "t", "ok": True, "detail": "y" * 4000})
        finally:
            stop.set(); r.join()
        s.assertEqual([x for x in seen if not (x is None or isinstance(x, dict) and x["T"] == "t")][:1], [])
        s.assertTrue(any(seen))
        s.assertEqual(sorted(f.name for f in (hd.STATE / "s1").iterdir()), ["gate.json"])   # no temp file left behind

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

    def test_a_reader_a_run_spawns_is_part_of_it_and_stops_with_it(s):
        s.change("s1"); s.agreed("s1")
        hd.tick(s.ctx(Fake(**FACTS)))
        run = hd.runs()[0]
        sub = s.root / "state" / "session" / "subagents"
        sub.mkdir(parents=True)
        def agent(aid, kind, prompt, parent=None, **meta):
            (sub / f"agent-{aid}.jsonl").write_text(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
            (sub / f"agent-{aid}.meta.json").write_text(json.dumps({"agentType": kind, **({"parentAgentId": parent} if parent else {}), **meta}))
            return lambda ev, **x: {"hook_event_name": ev, "agent_id": aid, "agent_type": kind, "agent_transcript_path": str(sub / f"agent-{aid}.jsonl"), **x}
        dev = agent("d1", "dev", f"Read and follow {run['brief']}")
        hook.bind(dev("SubagentStart"))
        reader = agent("r1", "reader", "Which packets open the clan chat?", parent="d1")
        fork = agent("f1", "dev", f"Read and follow {run['brief']}", parent="d1")   # a fork carries its parent's brief
        agent("r0", "reader", "done already", parent="d1", finished=True)
        with mock.patch.object(hook, "start_pass") as tick, mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            for a in (reader, fork):
                hook.bind(a("SubagentStart")); hook.bind(a("PreToolUse", tool_name="Bash"))
                hook.hold_handback(a("PreToolUse", tool_name="SubagentHandback"))
                with open(sub / f"agent-{a('x')['agent_id']}.jsonl", "a") as f:   # a background command still runs: no refusal
                    f.write(json.dumps({"type": "user", "toolUseResult": {"backgroundTaskId": "b9"}}) + "\n")
                hook.end_run(a("SubagentStop"))
        s.assertEqual((out.getvalue(), tick.called), ("", False))                    # not held, not refused, no pass
        s.assertEqual([(r["agent_id"], r["ended"]) for r in hd.runs()], [("d1", None)])   # not bound as a run; the parent's run not ended
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            s.assertFalse(hook.stop_orphan(reader("PostToolUse", tool_name="Grep")))  # its run lives: it carries on
            hd.cmd_stop([run["name"]])
            out.truncate(0); out.seek(0)
            s.assertTrue(hook.stop_orphan(reader("PostToolUse", tool_name="Grep")))   # its run ended: it stops at its next call
        s.assertEqual(json.loads(out.getvalue())["continue"], False)
        s.assertFalse(hook.stop_orphan(dev("PreToolUse", tool_name="Bash")))           # a run itself is never stopped here

    def test_a_reader_bash_command_that_writes_is_denied(s):
        def denied(c, kind="reader"):
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                hook.deny_reader_write({"agent_id": "r1", "agent_type": kind, "tool_input": {"command": c}})
            return '"deny"' in out.getvalue()
        for c in ("echo x > f", "grep x f 2>err.txt", "rm -rf d", "git -C r commit -m x", "git push", "git checkout main",
                  "RESUME=1 tools/track.sh up s", "tools/track.sh build s", "~/r/tools/track.sh gate s", "tools/track.sh down s",
                  "docker run img", "cat f | tee out", "ls | xargs rm", "sed -i s/a/b/ f", "gh api -X POST repos/x",
                  "gh api repos/x -f a=b", "gh pr comment 1 -b x", "python3 ~/osrs-harness/hd.py new x", "bash -c 'echo a > b'"):
            s.assertTrue(denied(c), c)
        for c in ("cat f", "grep -n 'a > b' f", "sed -n 1,20p f", "jq . f 2>/dev/null", "git log 2>&1 | head", "git show HEAD:x",
                  "gh api repos/x/pulls", "gh api -X GET repos/x", "tools/track.sh log s", "docker logs c", "hd show x", "awk '$1 > 3' f"):
            s.assertFalse(denied(c), c)
        s.assertFalse(denied("rm -rf d", kind="dev"))                                     # only a reader is held to reading

    def test_a_run_s_bash_commands_run_in_its_slice(s):
        s.change("s1"); s.agreed("s1")
        run = s.started(Fake(**FACTS), "s1")
        p = {**payload(run, "ag-" + run["name"], "PreToolUse", s.root), "tool_name": "Bash", "tool_input": {"command": "make\nmake test", "timeout": 5}}
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            s.hook(p)
        o = json.loads(out.getvalue())["hookSpecificOutput"]
        s.assertNotIn("permissionDecision", o)                                  # the permission rules still judge the command
        s.assertEqual(o["updatedInput"], {"command": f"python3 {Path(hook.__file__).resolve().parent / 'hd.py'} scope {run['name']}\nmake\nmake test", "timeout": 5})
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            s.hook({**p, "tool_input": {"command": "hd approve s1"}})
        s.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")   # one answer: the deny alone
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            s.hook({**p, "agent_id": "main", "agent_type": None})
        s.assertEqual(out.getvalue(), "")                                       # no run, no slice
        sub = s.root / "state" / "subagents"; sub.mkdir()                       # a reader the run spawned, and a fork that reader spawned
        tp = Path(p["agent_transcript_path"]); (sub / f"agent-{p['agent_id']}.meta.json").write_text(json.dumps({"agentType": "dev"}))
        (sub / "agent-rd.meta.json").write_text(json.dumps({"agentType": "Explore", "parentAgentId": p["agent_id"]}))
        (sub / "agent-fk.meta.json").write_text(json.dumps({"agentType": "fork", "parentAgentId": "rd"}))
        for aid, kind in (("rd", "Explore"), ("fk", "fork")):
            (sub / f"agent-{aid}.jsonl").write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "find X"}}) + "\n")
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                s.hook({**p, "agent_id": aid, "agent_type": kind, "agent_transcript_path": str(sub / f"agent-{aid}.jsonl")})
            s.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["updatedInput"]["command"].split("\n")[0].split()[-2:], ["scope", run["name"]])
        (sub / "agent-ot.jsonl").write_text(tp.read_text().splitlines()[0].replace(run["brief"], "x") + "\n")
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            s.hook({**p, "agent_id": "ot", "agent_type": "Explore", "agent_transcript_path": str(sub / "agent-ot.jsonl")})
        s.assertEqual(out.getvalue(), "")                                       # an agent no run spawned has no slice

    def hook(s, p):
        with mock.patch("sys.stdin", io.StringIO(json.dumps(p))):
            hook.main()

    def test_a_failing_test_leaves_no_temp_dir(s):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, "-c", "import sys, tempfile, pathlib; sys.path.insert(0, sys.argv[1]); import test_hd\n"
                                "pathlib.Path(tempfile.mkdtemp(), 'f').write_text('x'); raise AssertionError('a failing test')", str(Path(__file__).parent)],
                               env={**os.environ, "TMPDIR": t, "HD_SUITE": "nested"}, capture_output=True, text=True)
            s.assertIn("a failing test", r.stderr); s.assertEqual(os.listdir(t), [])

    def test_a_stopped_gate_s_test_runner_leaves_no_temp_dir(s):
        unit = re.search(r"^unit='(.*?)'   #", (Path(__file__).parents[1] / "tools" / "track.sh").read_text(), re.M)[1]
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as src:
            Path(src, "test_wait.py").write_text("import pathlib, tempfile, time, unittest\nclass W(unittest.TestCase):\n    def test_w(s):\n"
                                                 "        pathlib.Path(tempfile.mkdtemp(), 'f').write_text('x'); print(tempfile.gettempdir(), flush=True); time.sleep(600)\n")
            p = subprocess.Popen(["bash", "-c", 'exec python3 -c "$1" test_wait.py 3>/dev/null', "_", unit], cwd=src, env={**os.environ, "TMPDIR": t},
                                 stdout=subprocess.PIPE, text=True, start_new_session=True)
            s.assertTrue(p.stdout.readline().startswith(t))                    # the test runs, its temp dir under the runner's root
            os.killpg(p.pid, signal.SIGTERM); p.wait(); p.stdout.close()     # the pass's stop of a gate (Facts.stop)
            s.assertEqual(os.listdir(t), [])

    def test_an_ended_run_s_processes_end_in_the_pass(s):
        s.change("s1"); s.agreed("s1"); s.change("s2"); s.agreed("s2")
        F = Fake(**FACTS)
        a, b = s.started(F, "s1"), s.started(F, "s2")
        hd.write(hd.STATE / "runs" / f"{a['name']}.json", json.dumps({**hd.runs(a["name"])[0], "ended": hd.now(), "reason": "stopped by the head"}))
        F.f["slices"] = {hd.run_slice(a["name"]), hd.run_slice(b["name"])}
        w = hd.STATE / "winpids"
        for r, pid in ((a, "4812"), (b, "5120")):                              # a Windows process a track script started in each slice
            (w / hd.run_slice(r["name"])).mkdir(parents=True); (w / hd.run_slice(r["name"]) / pid).write_text("java.exe\n")
        hd.tick(s.ctx(F))
        s.assertEqual([x for x in F.ran if x[:3] == ["systemctl", "--user", "stop"]], [["systemctl", "--user", "stop", hd.run_slice(a["name"])]])
        s.assertEqual([x[1:] for x in F.ran if x[0].endswith("taskkill.exe")], [["/F", "/PID", "4812", "/FI", "IMAGENAME eq java.exe"]])
        s.assertFalse((w / hd.run_slice(a["name"])).exists()); s.assertTrue((w / hd.run_slice(b["name"]) / "5120").exists())
        F.ran.clear(); F.f["slices"] = {hd.run_slice(b["name"])}; hd.tick(s.ctx(F))
        s.assertEqual([x for x in F.ran if "stop" in x or x[0].endswith("taskkill.exe")], [])   # ended once, stopped once

    @unittest.skipUnless(shutil.which("busctl") and subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True).stdout.strip() in (b"running", b"degraded"), "no systemd user manager")
    def test_hd_stop_ends_a_process_its_run_started_even_reparented(s):
        slug = f"p{os.getpid()}"                                                # concurrent suites never share a slice
        s.change(slug); s.agreed(slug)
        run = s.started(Fake(**FACTS), slug)
        pidf = s.root / "child.pid"
        subprocess.run(["bash", "-c", f'{sys.executable} {Path(hd.__file__).resolve()} scope {run["name"]}\n(setsid sleep 600 >/dev/null 2>&1 & echo $! > {pidf})'], check=True)
        pid = int(pidf.read_text())
        s.assertIn(hd.run_slice(run["name"]), Path(f"/proc/{pid}/cgroup").read_text())
        hd.cmd_stop([run["name"]])
        s.assertFalse(Path(f"/proc/{pid}").exists() and Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z")

    def test_a_suite_s_spawn_stays_in_the_suite_s_cgroup(s):
        pid, start = hd.Facts().spawn(["sleep", "600"], s.root / "spawn.log")    # HD_SUITE is set: no systemd scope of its own
        s.assertEqual(Path(f"/proc/{pid}/cgroup").read_text(), Path("/proc/self/cgroup").read_text())
        hd.Facts().stop(pid, start); os.waitpid(pid, 0)

    def test_dev_files_fix_outside_its_track_without_asking(s):
        s.change("c1", track="client"); s.agreed("c1", "client")
        hd.cmd_new(["h9", "--track", "harness", "--title", "tools fix", "--blocks", "c1", "--mechanism", "runs"])
        hd.cmd_new(["h8", "--track", "harness", "--title", "another", "--blocks", "c1", "--mechanism", "tree"])
        s.assertEqual(hd.defs("changes")["c1"]["deps"], ["h9", "h8"])
        s.assertEqual(hd.defs("changes")["c1"]["body"], "do it")
        s.assertEqual(s.state(Fake(**FACTS), "c1")["state"], "waiting on h9")      # held, no question raised
        with s.assertRaises(SystemExit):
            hd.cmd_new(["h7", "--track", "harness", "--title", "x", "--blocks", "nope"])
        s.assertNotIn("h7", hd.defs("changes"))

    def test_a_dependency_on_a_superseded_change_follows_its_superseder(s):
        s.change("h1", track="harness", mechanism="runs"); s.change("c1", track="client", deps=["h1"]); s.agreed("c1", "client")
        (s.root / "harness" / "goals" / "g1.md").write_text("---\ntrack: client\ntarget: 1\ndeps: [h1]\n---\n## Goal\n")
        hd.cmd_new(["r1", "--track", "harness", "--title", "one rewrite", "--mechanism", "hold", "--supersedes", "h1", "--deps", "h1"])
        s.assertEqual((hd.defs("changes")["c1"]["deps"], hd.defs("goals")["g1"]["deps"], hd.defs("changes")["r1"]["deps"]), (["r1"], ["r1"], []))
        s.assertEqual(s.state(Fake(**FACTS), "c1")["state"], "waiting on r1")      # the open fix still holds it
        hd.cmd_new(["c9", "--track", "client", "--title", "later", "--deps", "h1"])   # a later dependency on h1 names r1
        s.assertEqual(hd.defs("changes")["c9"]["deps"], ["r1"])

    def test_a_blocks_filing_joined_into_an_open_change_holds_on_it(s):
        s.change("h2", track="harness", mechanism="runs"); s.change("c1", track="client"); s.agreed("c1", "client")
        hd.cmd_new(["x9", "--track", "harness", "--title", "runs drop", "--mechanism", "runs", "--blocks", "c1"])
        g = hd.defs("changes")
        s.assertNotIn("x9", g); s.assertEqual(g["c1"]["deps"], ["h2"]); s.assertIn("runs drop", g["h2"]["body"])
        s.assertEqual(s.state(Fake(**FACTS), "c1")["state"], "waiting on h2")
        s.change("h3", track="harness", mechanism="tree", deps=["c1"])
        hd.cmd_new(["x8", "--track", "harness", "--title", "tree drop", "--mechanism", "tree", "--blocks", "c1"])   # h3 waits on it: ordered, its own change, no cycle
        g = hd.defs("changes")
        s.assertEqual(g["c1"]["deps"], ["h2", "x8"]); s.assertNotIn("tree drop", g["h3"]["body"])

    def test_a_dependency_cycle_is_one_alert_and_refused_by_hd_new_and_a_definition_commit(s):
        import io, contextlib
        s.change("c1", deps=["c2"]); s.change("c2", deps=["c3"]); s.change("c3", deps=["c1"]); s.change("c4", deps=["c1"])
        s.change("c5", deps=["c6"]); s.change("c6", deps=["c5"], closed="answer-1: no")   # through a closed change: no cycle
        F = Fake(**FACTS)
        alerts = [a for a in hd.tick(s.ctx(F), act=False)["alert"] if "cycle" in a]
        s.assertEqual(alerts, ["dependency cycle c1 -> c2 -> c3 -> c1: no change in it can move; remove one of its deps"])
        s.assertEqual(s.state(F, "c2")["state"], "in dependency cycle c1 -> c2 -> c3 -> c1")
        s.assertEqual(s.state(F, "c4")["state"], "waiting on c1")                          # outside the cycle: a plain wait
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for c in ("git commit -m x -- harness/changes/c1.md", "git add harness/changes/c3.md && git commit -m y"):
                hook.deny_dep_cycle({"agent_type": "orchestrator", "tool_input": {"command": c}})
            hook.deny_dep_cycle({"agent_type": "dev", "tool_input": {"command": "git commit -m z -- hd.py"}})   # no definition: allowed
        s.assertEqual(out.getvalue().count('"deny"'), 2)
        s.change("c3", deps=[])
        s.assertEqual(hd.cycles(hd.defs("changes")), [])
        for a in (["n1", "--deps", "c4", "--blocks", "c3"], ["n2", "--blocks", "n2"]):   # closes c1 -> c2 -> c3 -> n1 -> c4 -> c1; a self-dep
            with s.assertRaises(SystemExit):
                hd.cmd_new([a[0], "--track", "harness", "--title", "x", "--mechanism", "loop", *a[1:]])
            s.assertNotIn(a[0], hd.defs("changes"))
        s.assertEqual(hd.defs("changes")["c3"]["deps"], [])

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

    def test_dead_script_reruns_then_raised_after_its_third(s):  # sweep-18 N7: a host fault (exit 75, no build.json) is the runner's: re-run, never the head's FAIL
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1", "Limits:", "none"])
        for _ in range(3):
            v = hd.tick(s.ctx(F))                                                # the build ended without build.json (held: the host's fault)
            st = s.state(F, "s1")
            s.assertEqual((st["actor"], st["state"].split()[0], hd.rec("s1", "build")), ("script", "building", None))   # never 'build failed: dev'
        s.assertEqual([a[1] for a in F.spawned], ["build"] * 3)
        s.assertFalse(any("without a result" in a for a in v["alert"]))
        v = hd.tick(s.ctx(F))
        s.assertEqual([a[1] for a in F.spawned], ["build"] * 3)
        s.assertTrue(any("build ended 3 times without a result" in a for a in v["alert"]))
        s.assertFalse(any(r["role"] == "dev" and r["step"].startswith("build failed") for r in hd.runs() if r.get("step")))

    def test_attempts_reset_on_new_args_or_a_landed_result(s):
        F = Fake(**FACTS)
        ctx = s.ctx(F)
        ctx.start("s1", "build", ["b", "T1"]); ctx.start("s1", "build", ["b", "T1"]); ctx.start("s1", "build", ["b", "T1"])
        ctx.start("s1", "build", ["b", "T1"])                                    # ended 3 times on T1: raised, not rerun
        s.assertEqual(len(F.spawned), 3)
        ctx.start("s1", "build", ["b", "T2"])                                    # a new tree: one death is not two
        s.assertEqual(hd.rec("s1", "proc-build")["attempts"], 1)
        hd.put("s1", "build", {"T": "T2", "ok": True})                           # the result lands
        ctx.start("s1", "build", ["b", "T2"])
        s.assertEqual(hd.rec("s1", "proc-build")["attempts"], 1)
        script = s.root / "track.sh"; script.write_text("")
        ctx.start("s1", "build", [str(script), "T3"]); ctx.start("s1", "build", [str(script), "T3"]); ctx.start("s1", "build", [str(script), "T3"])
        n = len(F.spawned); ctx.start("s1", "build", [str(script), "T3"])
        s.assertEqual(len(F.spawned), n)                                         # ended 3 times on T3: raised
        ctx.start("s1", "build", [str(script), "T3"])                            # a second change reaching the same script
        s.assertEqual(sum("ended 3 times" in a for a in ctx.alerts), 1)             # one alert in a pass, not one per caller
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
        s.approve(F, "s1", A)                                                   # the user's yes in the console
        F.f["procs"] = set()                                                    # the orchestrator is gone after the yes
        hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1], [str(hd.ROOT / "hd.py"), "ship", "s1", A])

    def test_missing_script_is_an_alert_not_a_crash(s):
        (s.root / "harness" / "goals" / "g1.md").write_text("---\nslug: g1\ntrack: client\ntarget: 100\n---\ngoal")
        F = Fake(**FACTS)
        F.spawn = lambda args, log, env=None: hd.Facts.spawn(F, [str(s.root / "nope" / "track.sh")] + args[1:], log, env)
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(a.startswith("g1: measure cannot start:") and "No such file" in a for a in v["alert"]))

    def test_a_tools_fix_reruns_a_failed_gate(s):
        s.change("s1"); s.agreed("s1")
        bs, gs = "build() {\n  record true build\n}\n", "gate() { build; }\nrecord() { echo; }\n"
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: {"tools/track.sh": "up() { :; }\n", "tools/build/build.sh": bs, "tools/gate/gate.sh": gs}}})
        rows = [x for r in hd.contract("s1")["rows"] for x in (r["check"], r["gate"]) if x]   # the contract's script rows are in the gate key
        t = s.gated("s1", F)["T"]
        bk = lambda c: f"{t}-{hd.tools_run(F.f['tools_files'][c], 'tools/build/')[:12]}"
        gk = lambda c: f"{bk(c)}-{hd.tools_run(F.f['tools_files'][c], 'tools/gate/', rows)[:12]}"
        hd.put("s1", "build", {"T": bk(B), "ok": True})
        hd.put("s1", "gate", {"T": gk(B), "ok": False, "detail": "FAIL: ci: a tools bug"})
        s.assertEqual(s.state(F, "s1")["actor"], "dev")                      # the failure stands while the tools stand
        F.f["tools_files"][C] = {**F.f["tools_files"][B], "tools/track.sh": "up() { echo up; }\n", "tools/server/README.md": "x"}
        F.f["refs"] = {**F.f["refs"], "local/harness": C}                    # a tools commit outside what build and gate run
        s.assertEqual((bk(B), gk(B)), (bk(C), gk(C)))
        s.assertEqual(s.state(F, "s1")["actor"], "dev")                      # the failure still stands
        F.f["tools_files"][D] = {**F.f["tools_files"][B], "tools/gate/gate.sh": gs.replace("echo;", "echo 2;")}
        F.f["refs"] = {**F.f["refs"], "local/harness": D}                    # the tools fix ships: a gate file
        s.assertEqual(bk(D), bk(B))                                          # a gate edit never rekeys the build
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["state"]), ("script", f"gate on {hd.short(gk(D))}"))
        hd.tick(s.ctx(F))
        s.assertEqual([x[1] for x in F.spawned], ["gate"])                  # the gate re-runs, nothing is rebuilt
        s.assertEqual((F.envs[0]["T"], F.envs[0]["G"]), (bk(D), gk(D)))      # T names the build (the image), G the gate's record
        hd.put("s1", "gate", {"T": F.envs[0]["G"], "ok": True})
        s.assertIn("s1", hd.integration(s.ctx(F))["names"])                  # the re-run gate still admits the hand-over to T_int
        F.f["tools_files"][A] = {**F.f["tools_files"][D], "tools/build/Dockerfile": "FROM b"}
        F.f["refs"] = {**F.f["refs"], "local/harness": A}                    # a build edit rekeys both
        s.assertEqual(s.state(F, "s1")["state"], f"building {hd.short(bk(A))}"); s.assertNotEqual(gk(A), gk(D))

    def test_a_script_alive_under_an_outdated_key_is_stopped_and_replaced(s):  # 10 gates kept their old key while their new builds waited
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: {"tools/gate/gate.sh": "1"}}})
        s.gated("s1", F); hd.drop("s1", "gate"); hd.tick(s.ctx(F))
        hd.put("s1", "build", {"T": F.envs[-1]["T"], "ok": True})               # built; a gate gate.sh's key never rebuilds
        k1 = s.state(F, "s1")["state"]; hd.tick(s.ctx(F))
        p1 = hd.rec("s1", "proc-gate"); F.f["procs"] = {(7, "1"), (p1["pid"], p1["start"])}
        hd.tick(s.ctx(F)); s.assertEqual((len(F.spawned), F.stopped), (2, []))   # alive under the current key: kept
        F.f["tools_files"][C] = {"tools/gate/gate.sh": "2"}; F.f["refs"]["local/harness"] = C   # the gate's code moves: its key does
        st = s.state(F, "s1"); s.assertNotEqual(st["state"], k1)
        hd.tick(s.ctx(F))
        s.assertEqual((F.stopped, [x[1] for x in F.spawned]), ([p1["pid"]], ["build", "gate", "gate"]))   # the outdated gate is stopped, the current one started; no rebuild
        s.assertEqual(hd.rec("s1", "proc-gate")["key"], F.envs[-1]["G"])        # the record names the key of the process holding it
        s.assertEqual(st["state"], f"gate on {hd.short(F.envs[-1]['G'])}")
        ctx = s.ctx(F); F.f["procs"] = {(7, "1"), (4242, "99")}
        ctx.start("s2", "ship", ["hd.py", "ship", "s2", A]); ctx.start("s2", "ship", ["hd.py", "ship", "s2", A])
        s.assertEqual(F.stopped, [p1["pid"]])                                    # a carry has no key: never stopped

    def test_a_gate_running_a_row_whose_key_holds_finishes(s):  # sweep-17 N5: a text.py-only tools ship stopped 11 gates, 8 CI runs ~15 min in
        s.change("s1"); s.agreed("s1", extra="- ci | fork CI | gate: tools/track.sh gate-ci\n- subj | subject | check: tools/server/text.py subject\n")
        f = {"tools/gate/gate.sh": "1", "tools/server/text.py": "t"}
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: f}})
        s.gated("s1", F); hd.drop("s1", "gate"); hd.tick(s.ctx(F))
        hd.put("s1", "build", {"T": F.envs[-1]["T"], "ok": True}); hd.tick(s.ctx(F))
        p1 = hd.rec("s1", "proc-gate"); F.f["procs"] = {(7, "1"), (p1["pid"], p1["start"])}
        s.assertIn(json.loads(F.envs[-1]["ROWKEYS"])["s1/ci"], p1["rows"])
        F.f["tools_files"][C] = {**f, "tools/server/text.py": "t2"}; F.f["refs"]["local/harness"] = C   # one row's file moves
        n = len(F.spawned); hd.tick(s.ctx(F))
        s.assertEqual((F.stopped, len(F.spawned)), ([], n))                      # the running gate's CI row still holds: it finishes
        hd.put("s1", "gate", {"T": p1["key"], "ok": True}); F.f["procs"] = {(7, "1")}
        hd.tick(s.ctx(F)); s.assertEqual((F.spawned[-1][1], len(F.spawned)), ("gate", n + 1))   # then the current gate, its kept rows unrun
        F.f["procs"] = {(7, "1"), (hd.rec("s1", "proc-gate")["pid"], hd.rec("s1", "proc-gate")["start"])}
        F.f["tools_files"][D] = {**f, "tools/gate/gate.sh": "2"}; F.f["refs"]["local/harness"] = D       # a gate.sh edit moves every row
        hd.tick(s.ctx(F)); s.assertEqual(len(F.stopped), 1)                      # no row's key holds: stopped and replaced

    def test_builds_alive_at_once_never_hold_more_than_the_host(s):  # sweep-18 N7: a tools ship moved 12 build keys; 12 builds of 5g/4 CPUs started on 16 CPUs / 19 GB
        slugs = [f"s{i}" for i in range(1, 13)]
        build = "size=(--cpus=4 --memory=5g)   # each build container's share\nbuild() { docker run \"${size[@]}\"; }\n"
        heads = {k: f"{i:02d}" * 20 for i, k in enumerate(slugs, 10)}
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], **{f"fork/dev/{k}": h for k, h in heads.items()}, "local/harness": B}, "tools_files": {B: {"tools/build/build.sh": build}},
                    "trees": {**FACTS["trees"], **{h: "t" + h for h in heads.values()}}, "merges": {(B, h): ("ok", h) for h in heads.values()}}, host=(int(19.5 * 2**30), 16))
        pids = iter(range(5000, 6000))
        def spawn(args, log, env=None):
            pid = next(pids); F.spawned.append(args); F.envs.append(env or {}); F.f["procs"] = set(F.f.get("procs", {(7, "1")})) | {(pid, "99")}; return pid, "99"
        F.spawn = spawn
        nb = lambda: sum(a[1] == "build" for a in F.spawned)
        bs = lambda: [a for a in F.spawned if a[1] == "build"]
        for k in slugs:
            s.change(k); s.agreed(k)
            with mock.patch.object(hd, "Facts", lambda: F):
                hd.cmd_handover([k, "Limits:", "none"])
        hd.tick(s.ctx(F))
        s.assertEqual([a[1] for a in F.spawned], ["build"] * 3)               # one pass: min(19.5 GB // 5g, 16 // 4) = 3, not 12
        s.assertTrue(all(s.state(F, k)["state"].startswith("building") for k in slugs))   # the rest wait: no alert, no dev step
        hd.tick(s.ctx(F)); s.assertEqual(nb(), 3)                    # nothing ended: none starts
        first = hd.rec(bs()[0][2], "proc-build"); s.assertEqual(first["room"], [5 * 2**30, 4.0])
        hd.put(bs()[0][2], "build", {"T": first["key"], "ok": True}); F.f["procs"] -= {(first["pid"], first["start"])}   # one ends, its record landed
        hd.tick(s.ctx(F)); s.assertEqual(nb(), 4)                    # the next one starts on that end
        hd.put("room", "777", {"pid": 777, "start": "99", "mem": 5 * 2**30, "cpus": 4.0, "owner": "", "held": True}); F.f["procs"] |= {(777, "99")}   # a dev's own build's container
        second = hd.rec(bs()[1][2], "proc-build"); F.f["procs"] -= {(second["pid"], second["start"])}
        hd.tick(s.ctx(F)); s.assertEqual(nb(), 4)                    # the dev's container holds the room the ended build left
        hd.put("room", "778", {"pid": 778, "start": "99", "mem": 5 * 2**30, "cpus": 4.0, "owner": f"{bs()[2][2]}/build", "held": True}); F.f["procs"] |= {(778, "99")}
        F.f["procs"] -= {(777, "99")}
        hd.tick(s.ctx(F)); s.assertEqual(nb(), 5)                    # a pass build's own container is counted once, as its build
        s.assertEqual(F.envs[F.spawned.index(bs()[-1])]["HD_PROC"], f"{bs()[-1][2]}/build")      # the owner its containers name

    def test_a_container_waits_on_the_end_of_one_held(s):  # hd room: a dev's build and a gate's check share the host's bound with the pass's builds
        import threading
        class H(hd.Facts):
            def host(s_): return 10 * 2**30, 8
        child = subprocess.Popen([sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE)
        hd.put("room", str(child.pid), {"pid": child.pid, "start": hd.Facts().proc_start(child.pid), "mem": 8 * 2**30, "cpus": 4.0, "owner": "", "held": True})
        ran = []
        def execvp(f, a): ran.append(a); raise SystemExit(0)
        def go():
            with mock.patch.object(hd, "Facts", H), mock.patch.object(hd.os, "execvp", execvp), s.assertRaises(SystemExit):
                hd.cmd_room(["docker", "run", "--cpus=4", "--memory=4g", "img"])
        t = threading.Thread(target=go); t.start()
        while not (s.root / "state" / "room").glob("*.json") or len(list((s.root / "state" / "room").glob("*.json"))) < 2:
            pass                                                               # its waiting entry is written
        s.assertEqual(ran, []); s.assertTrue(t.is_alive())                     # 8g + 4g over 10g: it waits, no container
        child.communicate(b""); t.join()                                       # the held one ends: it runs, nothing timed
        s.assertEqual(ran, [["docker", "run", "--cpus=4", "--memory=4g", "img"]])
        e = hd.rec("room", str(os.getpid())); s.assertEqual((e["held"], e["mem"]), (True, 4 * 2**30))
        s.assertFalse((s.root / "state" / "room" / f"{child.pid}.json").exists())   # the ended one's entry dropped

    def test_a_build_of_a_new_tree_stops_the_gate_of_the_old_one(s):  # server-token-auth's gate.sh ran on while the pass started its new build
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: {"tools/build/build.sh": "1", "tools/gate/gate.sh": "1"}}})
        s.gated("s1", F); hd.drop("s1", "gate"); hd.tick(s.ctx(F))
        hd.put("s1", "build", {"T": F.envs[-1]["T"], "ok": True}); hd.tick(s.ctx(F))
        p1 = hd.rec("s1", "proc-gate"); F.f["procs"] = {(7, "1"), (p1["pid"], p1["start"])}
        F.f["tools_files"][C] = {"tools/build/build.sh": "2", "tools/gate/gate.sh": "1"}; F.f["refs"]["local/harness"] = C   # the build's code moves
        s.assertTrue(s.state(F, "s1")["state"].startswith("building"))
        hd.tick(s.ctx(F))
        s.assertEqual((F.stopped, F.spawned[-1][1]), ([p1["pid"]], "build"))     # the old tree's gate is stopped as the new build starts

    def test_a_deploy_is_keyed_on_the_tools_it_runs(s):  # the integration deploy ran on pre-ship tools, still downloading openrs2
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: {"tools/track.sh": "ship() { :; }", "tools/build/build.sh": "1", "tools/gate/gate.sh": "1"}}})
        ctx = s.ctx(F); ch = ctx.changes["s1"]; k = ctx.deploy_key(ch, "tr")
        F.f["tools_files"][C] = {"tools/track.sh": "ship() { :; }", "tools/build/build.sh": "1", "tools/gate/gate.sh": "2"}; F.f["refs"]["local/harness"] = C
        s.assertEqual(s.ctx(F).deploy_key(ch, "tr"), k)                          # sweep-26 P0-a: a gate-only tools ship is no deploy's
        F.f["tools_files"][D] = {"tools/track.sh": "ship() { echo; }", "tools/build/build.sh": "1", "tools/gate/gate.sh": "2"}; F.f["refs"]["local/harness"] = D
        s.assertNotEqual(s.ctx(F).deploy_key(ch, "tr"), k)                       # a fix of what it runs moves the key: its count starts over
        s.assertTrue(k.startswith("tr-"))

    def test_a_batch_gate_on_a_prefix_still_current_holds(s):  # a member arriving restarted no gate, and the state named the running one
        for k in ("h1", "h2"):
            s.change(k, track="harness"); s.agreed(k, track="harness")
        H1, H2, M2 = "1" * 40, "2" * 40, "m2" * 20
        F = Fake(refs={"HEAD": B, "harness/h1": H1, "harness/h2": H2}, trees={B: "t0", H1: "t1", H2: "t2", M2: "t12"},
                 merges={(B, H1): ("ok", H1), (B, H2): ("ok", H2), (H1, H2): ("ok", M2)})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
        hd.tick(s.ctx(F)); F.f["procs"] = {(7, "1"), (4242, "99")}               # h1 alone: its gate runs
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h2", "Limits:", "none"])
        s.assertEqual([s.state(F, k)["state"] for k in ("h1", "h2")], ["gate on t1", "waiting for the batch ahead (gate on t1)"])
        hd.tick(s.ctx(F)); s.assertEqual((len(F.spawned), F.stopped), (1, []))  # the running gate holds: nothing restarted
        hd.put("ship-harness", "gate-t1", {"ok": True}); F.f["procs"] = {(7, "1")}
        s.assertEqual([s.state(F, k)["state"] for k in ("h1", "h2")], ["shipping", "waiting for the batch ahead (shipping)"])   # whole when its gate started: it ships, h2 joins the next batch (sweep-25: re-gated 4 times)
        hd.drop("ship-harness", "gate-t1"); F.f["procs"] = {(7, "1"), (4242, "99")}
        F.f["refs"]["harness/h1"] = "9" * 40                                     # h1's head moves: the running gate's prefix is gone
        F.f["trees"]["9" * 40] = "t9"; F.f["merges"].update({(B, "9" * 40): ("ok", "9" * 40), (H2, "9" * 40): ("ok", "m9" * 20)}); F.f["trees"]["m9" * 20] = "t92"
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])                            # handed over last: the batch is h2, then h1
        hd.tick(s.ctx(F))
        s.assertEqual((F.stopped, F.envs[-1]["G"]), ([4242], "t92"))           # stopped, the current batch's gate started

    def test_the_tools_key_holds_only_what_build_and_gate_run(s):
        f = {"tools/track.sh": "case $1 in build) exec build/build.sh ;; gate) exec gate/gate.sh ;; esac\nup() { :; }\n", "tools/build/build.sh": "build() { :; }\n",
             "tools/build/Dockerfile": "FROM a", "tools/gate/gate.sh": "gate() { :; }\n", "tools/server/login.py": "x", "tools/server/text.py": "t", "tools/server/test_tools.py": "u"}
        rows = ["tools/server/text.py texts", "tools/track.sh spotless"]
        b = lambda g: hd.tools_run({**f, **g}, "tools/build/")
        k = lambda g, r=rows: hd.tools_run({**f, **g}, "tools/gate/", list(r))
        for g in ({"tools/build/build.sh": "build() { echo; }\n"}, {"tools/build/Dockerfile": "FROM b"}, {"tools/build/new.py": ""}):
            s.assertNotEqual(b({}), b(g), g)                                   # a build file, a new one
        for g in ({"tools/gate/gate.sh": "gate() { echo; }\n"}, {"tools/gate/new.py": ""}, {"tools/server/text.py": "t2"}):
            s.assertNotEqual(k({}), k(g), g); s.assertEqual(b({}), b(g), g)    # a gate file or a file a row names: the gate alone
        for g in ({"tools/track.sh": f["tools/track.sh"].replace("up() { :; }", "up() { echo up; }")}, {"tools/server/login.py": "y"},
                  {"tools/server/test_tools.py": "u2"}):
            s.assertEqual((b({}), k({})), (b(g), k(g)), g)                     # up's code in track.sh (a row's verb runs in gate/), other files
        s.assertNotEqual(k({}), k({}, ["tools/server/text.py texts"]))         # the rows themselves

    def test_a_tools_copy_goes_once_nothing_runs_from_it(s):
        d = s.root / "state" / "tools"
        for n in ("aaa", "bbb", ".ccc.111", ".ddd.222"):
            (d / n / "tools").mkdir(parents=True)
        F = Fake(**FACTS, tools_used={"aaa"}); F.proc_start = lambda pid: "1" if pid == 111 else None   # 111 still copying, 222 died mid-copy
        hd.repairs(s.ctx(F), False); s.assertEqual(len(list(d.iterdir())), 4)                         # a dry run removes nothing
        F.f["tools_used"] = None; hd.repairs(s.ctx(F), True); s.assertEqual(len(list(d.iterdir())), 4)  # docker unreadable: a container's mounts unknown
        F.f["tools_used"] = {"aaa"}; hd.repairs(s.ctx(F), True)
        s.assertEqual(sorted(p.name for p in d.iterdir()), [".ccc.111", "aaa"])

    def test_a_gate_runs_its_rows_from_its_own_tools_copy(s):
        s.change("s1"); s.agreed("s1"); ran = []
        F = Fake(**FACTS); F.run = lambda cmd, cwd, env: (ran.append(cwd), (0, ""))[1]
        ctx = s.ctx(F); con = hd.contract("s1")
        hd.rows(ctx, ctx.changes["s1"], con, A, A, TA, "", gate=True)
        with mock.patch.dict(os.environ, {"TOOLS_ROOT": "/copy"}):
            hd.rows(ctx, ctx.changes["s1"], con, A, A, TA, "", gate=True)
        s.assertEqual(ran, [str(hd.track_root(hd.cfg(), "server"))] * (len(ran) // 2) + ["/copy"] * (len(ran) // 2))   # the hand-over at the checkout; the gate at the copy its script runs from

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
            hd.cmd_handover(["s1", "Limits:", "none"])
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned, [])
        s.assertEqual(sum("docker unreachable" in a for a in v["alert"]), 1)

    def test_docker_down_lists_no_build_run_until_it_answers(s):
        s.change("s1", priority="P1"); s.agreed("s1"); s.change("p1", "harness")
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
        s.assertEqual((s.state(F, "s1")["actor"], F.spawned), ("dev", []))     # the answer releases it, to the dev first (R3)


class R6(Sandbox):
    def test_devtools_servers_start_with_no_client(s):
        import subprocess
        repo = Path(__file__).parent.parent
        home = Path(tempfile.mkdtemp()); (home / "netstat.exe").write_text("#!/bin/sh\n"); (home / "netstat.exe").chmod(0o755)   # nothing listens
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_client_state", "arguments": {"port": 7781}}}]
        servers = json.loads((repo / "mcp" / "servers.json").read_text())
        s.assertEqual({n: (v["command"], v["args"]) for n, v in json.loads((repo / ".mcp.json").read_text())["mcpServers"].items()},
                      {n: ("/home/alex/osrs-harness/mcp/serve.py", [n]) for n in servers})   # each server runs under serve.py
        for name, cmd in servers.items():
            if "devtools" not in name:
                continue
            s.assertTrue(cmd[2].startswith("http://") or os.path.exists(cmd[2]), cmd)   # the backend exists
            r = subprocess.run([str(repo / "mcp" / "devtools_bridge.py"), *cmd[1:]], input="".join(json.dumps(m) + "\n" for m in msgs),
                               env={**os.environ, "HOME": str(home), "WINDOWS_SYSTEM32": str(home)}, capture_output=True, text=True)
            out = sorted((json.loads(l) for l in r.stdout.splitlines()), key=lambda o: o["id"])   # desktop answers each as it comes
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

    def test_desktop_call_answers_when_netstat_never_starts_or_the_call_raises(s):   # cannon-354-reset-ammo-varp-2: get_timeline hung 30 min
        import importlib.util, threading
        spec = importlib.util.spec_from_file_location("bridge", Path(__file__).parent.parent / "mcp" / "devtools_bridge.py")
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        stuck = threading.Event()
        def exec_hangs(*a, **k):
            stuck.wait()                                               # netstat.exe's exec from /mnt/c blocks, before its timeout applies
            return subprocess.CompletedProcess(a[0], 1, "", "")          # then fails: the probe thread reads a real result
        ok = mock.MagicMock(); ok.__enter__.return_value.read.return_value = json.dumps({"result": {"content": [{"type": "text", "text": "{}"}]}}).encode()
        with mock.patch.object(b, "NETSTAT_WAIT", 0.2), mock.patch.object(b.subprocess, "run", exec_hangs), mock.patch.object(b.urllib.request, "urlopen", return_value=ok):
            s.assertIn("result", b.post("http://127.0.0.1:7780/mcp", "tools/call", {"name": "get_timeline", "arguments": {}}))   # it connects
        stuck.set()
        out = []
        call = json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "get_timeline", "arguments": {}}})
        with mock.patch.object(b, "backend", side_effect=ValueError("truncated body")), mock.patch.object(b, "reply", lambda i, **r: out.append((i, r))):
            b.handle("desktop", ["http://127.0.0.1:7780/mcp"], call)
        s.assertEqual((out[0][0], "truncated body" in out[0][1]["error"]["message"]), (7, True))   # an exception is an error answer

    def test_a_desktop_call_is_answered_within_its_bound_when_the_client_hangs(s):   # cannon -4 and goblin -6: get_chat_history showed no result for 20+ min
        import importlib.util, threading, time
        spec = importlib.util.spec_from_file_location("bridge", Path(__file__).parent.parent / "mcp" / "devtools_bridge.py")
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        hung = threading.Event(); s.addCleanup(hung.set)
        body = mock.MagicMock(); body.__enter__.return_value.read.side_effect = lambda: hung.wait() and b""   # each socket read within its timeout, the body never ends
        with mock.patch.object(b, "ANSWER_WAIT", 0.2), mock.patch.object(b, "listening", lambda p: True), mock.patch.object(b.urllib.request, "urlopen", return_value=body) as u:
            t0 = time.monotonic()
            r = b.post("http://127.0.0.1:7780/mcp", "tools/call", {"name": "get_chat_history", "arguments": {}})
            s.assertLess(time.monotonic() - t0, 2); s.assertIn("did not answer within 0.2 s", r["error"]["message"])
            b.post("http://127.0.0.1:7780/mcp", "tools/call", {"name": "wait_for", "arguments": {"timeoutMs": 1000}})
            s.assertEqual(u.call_args.kwargs["timeout"], 1.2)          # a call's own wait is added to its bound

    def test_desktop_screenshot_answers_while_another_call_waits(s):   # central-login-whitelist-binds-3: a screenshot hung 30 min
        import importlib.util, io, threading
        spec = importlib.util.spec_from_file_location("bridge", Path(__file__).parent.parent / "mcp" / "devtools_bridge.py")
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        shot, out = threading.Event(), []
        def backend(cmd, method, params):
            if params["name"] == "wait_for":
                shot.wait(10)                                          # another run's wait, in flight until the screenshot is answered
            return {"result": {"content": [{"type": "text", "text": json.dumps({"gameState": "LOGGED_IN", "name": params["name"]})}]}}
        def reply(i, **r):
            out.append(i); shot.set() if i == 2 else None
        call = lambda i, n: json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": n, "arguments": {}}}) + "\n"
        with mock.patch.object(b, "backend", backend), mock.patch.object(b, "reply", reply), \
             mock.patch.object(b.sys, "argv", ["bridge", "desktop", "http://127.0.0.1:7780/mcp"]), mock.patch.object(b.sys, "stdin", io.StringIO(call(1, "wait_for") + call(2, "screenshot"))):
            b.main()
            for t in threading.enumerate():
                t is threading.current_thread() or t.join(15)
        s.assertEqual(out, [2, 1])                                     # the screenshot first, the wait after

    def test_harness_changes_dispatch_before_product_changes(s):
        s.change("s1", priority="P1"); s.agreed("s1")
        s.change("h1", track="harness", priority="P3"); s.agreed("h1", track="harness")     # a harness change is never below P1
        c = json.loads((s.root / "hd.yaml").read_text()); c["agents"] = 1; (s.root / "hd.yaml").write_text(json.dumps(c))
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(Fake(**FACTS)))["spawn"]], ["h1-1"])
        hd.cmd_new(["h2", "--track", "harness", "--title", "t", "--mechanism", "loop"])
        s.assertIn("priority: P1", (s.root / "harness" / "changes" / "h2.md").read_text())   # hd new without --priority: P1

    def test_pr_changes_before_new_content_and_blockers_raised(s):
        for slug, k in (("q0", {"priority": "P1"}), ("p1", {"priority": "P1", "pr": 354}), ("q3", {"priority": "P3"}), ("q2", {"priority": "P2"})):
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

    def test_a_lower_tier_waits_only_while_a_higher_run_is_due(s):
        for slug, k in (("p1", {"priority": "P1", "deps": ["b4"]}), ("b4", {"priority": "P4"}), ("q3", {"priority": "P3"})):
            s.change(slug, **k); s.agreed(slug)
        F = Fake(**FACTS)
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(c.startswith("p1 ") and "waiting on b4" in c for c in v["change"]))
        s.assertEqual([x.split(":")[0] for x in v["spawn"]], ["b4-1"])   # q3 held while b4, p1's dependency, has a run due at P1
        s.change("b4", priority="P4", closed="answer-1: dropped"); hd.cmd_ask(["p1", "which way?"])
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(c.startswith("p1 ") and "question open" in c for c in v["change"]))
        s.assertIn("q3-1", " ".join(v["spawn"]))                          # p1 only waits on the user: q3 is listed

    def test_a_higher_run_alive_holds_no_lower_tier(s):
        s.change("p0", track="harness", priority="P0"); s.agreed("p0", track="harness")
        s.change("q2", priority="P2"); s.agreed("q2")
        F = Fake(**FACTS)
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]], ["p0-1"])   # p0's run due, not yet listed: q2 held
        hook.bind(payload(next(r for r in hd.runs() if r["name"] == "p0-1"), "ag1", "SubagentStart", s.root))
        s.assertIn("q2-1", " ".join(hd.tick(s.ctx(F))["spawn"]))                          # p0's run alive: q2 is listed

    def test_a_due_run_the_pass_cannot_list_holds_nothing_and_is_an_alert(s):
        s.change("p1", priority="P1"); s.agreed("p1")
        F = Fake(**FACTS)
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]], ["p1-1"])
        r = next(r for r in hd.runs() if r["name"] == "p1-1")
        r.update(started=hd.now(), ended=hd.now(), record=True); hd.save_run(r)   # handed back, yet the facts still want the step
        s.change("q2", priority="P2"); s.agreed("q2")
        v = hd.tick(s.ctx(F))
        s.assertEqual([x.split(":")[0] for x in v["spawn"]], ["q2-1", "planner-1"])   # p1 cannot be listed: q2 is not held below it; the alert lists the planner
        s.assertEqual([a for a in v["alert"] if a.startswith("p1: ")], ["p1: dev run p1-1 handed back its record, yet its step is still due on the same input: no run is listed"])

    def test_the_latest_run_by_listed_time_decides_and_a_hand_off_settles_nothing(s):
        s.change("p1", priority="P1"); s.agreed("p1")
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        inp = next(r for r in hd.runs() if r["name"] == "p1-1")["input"]
        for n, t, k in ((9, "01", {"record": True, "handoff_told": 1}), (10, "02", {"record": False})):   # "-10" sorts before "-9" by name
            hd.save_run({"name": f"p1-{n}", "role": "dev", "change": "p1", "input": inp, "listed": f"2026-11-01T00:{t}:00Z",
                         "started": f"2026-11-01T00:{t}:01Z", "ended": f"2026-11-01T00:{t}:02Z", **k})
        hd.drop("runs", "p1-1")
        v = hd.tick(s.ctx(F))
        s.assertEqual([a for a in v["alert"] if a.startswith("p1: ")], [])
        s.assertIn("p1-11", " ".join(v["spawn"]))                                  # the hand-off then a death: one retry is due

    def test_a_dependency_the_run_filed_leaves_the_step_listable_once_live_though_recorded_shipping(s):
        s.change("p1", priority="P1"); s.agreed("p1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "HEAD": B, "harness/h9": C}, "anc": {(B, C)}})
        hd.tick(s.ctx(F))
        r = next(r for r in hd.runs() if r["name"] == "p1-1")
        r.update(started=hd.now()); hd.save_run(r)
        hd.cmd_new(["h9", "--track", "harness", "--title", "a fix p1 waits on", "--blocks", "p1", "--mechanism", "loop"])
        r.update(ended=hd.now(), record=True); hd.save_run(r)
        s.change("h9", track="harness", priority="P1"); s.change("p1", priority="P1", deps=["h9"])
        hd.put("h9", "handover", {"head": C}); hd.put("h9", "state", {"state": "shipping"})   # on the live branch, not yet recorded done
        v = hd.tick(s.ctx(F))
        s.assertEqual([a for a in v["alert"] if a.startswith("p1: ")], [])
        s.assertIn("p1-2", " ".join(v["spawn"]))

    def test_a_dependency_the_run_filed_settles_the_step_only_until_it_is_shut(s):
        s.change("p1", priority="P1"); s.agreed("p1")
        F = Fake(**FACTS)
        hd.tick(s.ctx(F))
        r = next(r for r in hd.runs() if r["name"] == "p1-1")
        r.update(started=hd.now()); hd.save_run(r)
        hd.cmd_new(["h9", "--track", "harness", "--title", "a fix p1 waits on", "--blocks", "p1", "--mechanism", "loop"])
        r.update(ended=hd.now(), record=True); hd.save_run(r)
        s.change("h9", track="harness", priority="P1", closed="done elsewhere"); s.change("p1", priority="P1", deps=["h9"])
        v = hd.tick(s.ctx(F))
        s.assertEqual([a for a in v["alert"] if a.startswith("p1: ")], [])
        s.assertIn("p1-2", " ".join(v["spawn"]))                                   # the dep shut: the step is listable again

    def test_a_hand_off_is_replaced_in_the_same_pass_past_the_tier_hold_and_the_count(s):
        s.change("p1", priority="P1"); s.agreed("p1")
        s.change("q2", priority="P2"); s.agreed("q2")
        F = Fake(**FACTS)
        q = {"name": "q2-1", "role": "dev", "change": "q2", "input": "[]", "listed": hd.now(), "started": hd.now(), "ended": None}
        hd.save_run(q)                                                 # q2's run, started before p1 opened
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]], ["p1-1"])
        c = json.loads((s.root / "hd.yaml").read_text()); c["agents"] = 2; (s.root / "hd.yaml").write_text(json.dumps(c))
        q.update(ended=hd.now(), handoff_told=160000); hd.save_run(q)  # q2's run hands off at the limit; p1-1 fills the count
        (s.root / "evidence" / "q2").mkdir(parents=True, exist_ok=True)
        (s.root / "evidence" / "q2" / "handoff.md").write_text("proven: A1; next: A2")
        hd.save_run({"name": "x9-1", "role": "dev", "change": "x9", "input": "[]", "listed": hd.now(), "started": hd.now(), "ended": None})
        v = hd.tick(s.ctx(F))
        s.assertEqual(sorted(x.split(":")[0] for x in v["spawn"]), ["p1-1", "q2-2"])   # replaced at once, though P1 is open and 2 runs are alive
        b = open(next(r for r in hd.runs() if r["name"] == "q2-2")["brief"]).read()
        s.assertIn(f"Resume from {s.root / 'evidence' / 'q2' / 'handoff.md'}", b)
        s.assertIn("proven: A1; next: A2", b)
        s.assertIn("q2-2", " ".join(hd.tick(s.ctx(F))["spawn"]))      # kept while unstarted, not dropped as held

    def test_a_listed_run_takes_its_moved_input_and_binds(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]], ["s1-1"])
        old = hd.runs()[0]["input"]
        with open(s.root / "evidence" / "s1" / "contract.md", "a") as f:
            f.write("- joined | a filing joined after the listing | judge: see it\n")   # the contract hash, so the dev step's input, moves
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]], ["s1-1"])   # the same run, not ended and listed again
        r = hd.runs()[0]
        s.assertEqual((len(hd.runs()), r["ended"]), (1, None)); s.assertNotEqual(r["input"], old)
        s.assertIn("a filing joined after the listing", open(r["brief"]).read())         # its brief rewritten: the agent reads the moved row
        hook.bind(payload(r, "ag1", "SubagentStart", s.root))
        s.assertEqual(hd.runs()[0]["agent_id"], "ag1")                                     # its spawn binds, never refused

    def test_a_pr_round_of_n_findings_and_one_head_move_costs_one_dev_one_qa_one_gate_and_one_card(s):
        """R6: a modeled PR carried at A takes N maintainer findings at once, and one more while its dev run is listed: they
        are one round change, whose dev stacks the answers on the PR (one head move, C), gated once and judged by one qa
        run at that last head, then one card whose one comment answers every finding. Every listed run is spawned and does its role's work."""
        N = 3
        s.change("s0", pr=7, branch="content/s0"); s.agreed("s0")
        com = lambda i: {"id": i, "author": "rev", "bot": False, "reply": None, "path": "G.kt", "line": i, "body": f"point {i}"}
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A}, "trees": {A: TA, B: TB, C: TC}, "merges": {(B, A): ("ok", A), (B, C): ("ok", C)},
                    "anc": {(C, A)}, "comments": {7: [com(90 + i) for i in range(N)]}, "talk": {7: []},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s0", "owner": "o", "head": A, "draft": False}]}})
        s.gated("s0", F); s.verdict("s0", A, {"ok": "pass", "j1": "pass"}, F); hd.put("s0", "ship", {"head": A, "ok": True})   # the PR's last round, carried
        def dev(r):  # one commit answering every finding on the PR's head, the push comment and each reply
            F.f["refs"][f"fork/dev/{r['change']}"] = C
            ev = s.root / "evidence" / r["change"]
            (ev / "pr-comment.md").write_text(PUSHED)
            for f in hd.defs("changes")[r["change"]]["finding"]:
                (ev / f"pr-reply-{f}.md").write_text(f"> point {f}\n\n@rev fixed in {C[:9]}.")
            with mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
                hd.cmd_handover([r["change"], "Limits:", "none"])
        judge = lambda r: s.verdict(r["change"], C, {x["id"]: "pass" for x in hd.contract(r["change"])["rows"]}, F)
        joined, gates, cards = False, 0, 0
        for _ in range(12):
            v = hd.tick(s.ctx(F))
            cards = max(cards, len(v["card"]))
            for k in hd.defs("changes"):
                st, ho = s.state(F, k)["state"], hd.rec(k, "handover")
                if st.startswith("building"):
                    hd.put(k, "build", {"T": ho["T"], "ok": True})
                elif st.startswith("gate on"):
                    hd.put(k, "gate", {"T": ho["T"], "ok": True}); gates += 1
            for x in v["spawn"]:
                r = hd.runs(x.split(":")[0])[0]
                if r["role"] == "planner":
                    continue
                if r["role"] == "dev" and not joined:   # one more finding while the dev run is listed: the run takes it
                    joined = True; F.f["comments"][7].append(com(99))
                    continue
                hook.bind(payload(r, "ag-" + r["name"], "SubagentStart", s.root))
                (dev if r["role"] == "dev" else judge)(r)
                with mock.patch.object(hook, "start_pass"):
                    hook.end_run(payload(r, "ag-" + r["name"], "SubagentStop", s.root, handback=f"run {r['name']}: done"))
            if cards:
                break
        rnd = f"server-7-c{90}"
        s.assertEqual(sorted(hd.defs("changes")), ["s0", rnd])                              # one round change, not one per finding
        s.assertEqual(hd.defs("changes")[rnd]["finding"], [90 + i for i in range(N)] + [99])
        rs = [r for r in hd.runs() if r["role"] != "planner"]
        s.assertEqual(sorted((r["change"], r["role"]) for r in rs), [(rnd, "dev"), (rnd, "qa")], [(r["name"], r["step"], r.get("reason"), s.state(F, rnd)) for r in rs])
        s.assertEqual((gates, cards), (1, 1))
        ctx = s.ctx(F); txt = hd.public_texts(ctx, ctx.changes[rnd])
        s.assertEqual([f for w, f, _ in txt if w == "comment"], [[90 + i for i in range(N)] + [99]])   # its one comment answers every finding

    def test_a_listed_run_stays_listed_when_a_higher_change_appears(s):
        s.change("q2", priority="P2"); s.agreed("q2")
        F = Fake(**FACTS)
        s.assertEqual([x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]], ["q2-1"])
        s.change("p1", priority="P1"); s.agreed("p1")
        s.assertEqual(sorted(x.split(":")[0] for x in hd.tick(s.ctx(F))["spawn"]), ["p1-1", "q2-1"])   # the tier hold lists no new run, drops no listed one
        s.assertIsNone(next(r for r in hd.runs() if r["name"] == "q2-1")["ended"])

    def test_a_held_band_lists_no_run_below_it(s):
        s.change("q3", priority="P3"); s.agreed("q3")
        F = Fake(**FACTS)
        s.assertIn("q3-1", " ".join(hd.tick(s.ctx(F))["spawn"]))     # no hold: q3 is listed
        c = json.loads((s.root / "hd.yaml").read_text()); c["hold"] = "P1"; (s.root / "hd.yaml").write_text(json.dumps(c))
        s.assertEqual(hd.tick(s.ctx(F))["spawn"], [])                 # q3's listed run dropped
        s.assertEqual(next(r for r in hd.runs() if r["name"] == "q3-1")["reason"], "held below P1")

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


    def test_a_session_of_no_run_gets_no_context_notice(s):
        import io, contextlib
        tp = s.root / "session.jsonl"
        tp.write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "x",
                      "usage": {"input_tokens": 10, "cache_read_input_tokens": 160000}}}) + "\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for extra in ({}, {"agent_type": "orchestrator"}):                     # the user's chat, the orchestrator, is no run
                hook.context_limit({"hook_event_name": "PostToolUse", "session_id": "m1", "transcript_path": str(tp), **extra})
        s.assertEqual(out.getvalue(), "")


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
    def test_a_dependent_of_a_new_pr_ships_in_that_same_pr(s):
        s.change("s1"); s.agreed("s1"); s.change("s2", deps=["s1"]); s.agreed("s2")
        F = Fake(refs={"origin/HEAD": B, "fork/dev/s1": A, "fork/dev/s2": C}, trees={A: TA, B: TB, C: TC}, commits={A: {A}, C: {C, A}})
        s.assertEqual(s.state(F, "s2")["state"], "waiting on s1")
        s.gated("s1", F); s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertTrue(s.state(F, "s2")["state"].startswith("dev run due"))       # never an upstream merge to wait on
        s.assertEqual(s.ctx(F).changes["s2"]["branch"], "content/s1")          # s1's PR, not yet opened
        s.gated("s2", F)
        st = s.state(F, "s2")
        s.assertEqual((st["actor"], st["state"]), ("dev", "joins s1's PR without its head: dev"))
        F.f["anc"] = {(C, A)}                                                    # s2's commits on top of s1's head: not a stack
        s.verdict("s2", C, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["state"], "gated; the PR waits for s2")
        s.assertEqual(s.state(F, "s2")["actor"], "user")                         # one card, at the PR's tip
        c = hd.tick(s.ctx(F), act=False)["card"]
        s.assertEqual(len(c), 1); s.assertIn("from content/s1 into main", c[0]); s.assertIn("changes s1, s2", c[0])
        s.approve(F, "s2", C)
        g = GH(**{"pr create": (1, "", "stop")})
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "gh", g), mock.patch("sys.stdout", new_callable=io.StringIO), s.assertRaises(SystemExit):
            hd.cmd_ship(["s2", C])
        s.assertEqual(g.did("push")[0][-1], f"{C}:refs/heads/content/s1")       # one new PR on s1's branch holds both
        hd.put("s2", "ship", {"head": C, "ok": True, "detail": "x"})            # carried at s2's head: s1 went with it
        F.f["prs"] = {"u/f": [{"number": 42, "branch": "content/s1", "owner": "o", "head": C, "draft": False}]}
        s.assertTrue(s.state(F, "s1")["state"].startswith(f"carried at {A[:9]}"))

    def test_main_moving_never_regates_a_shipped_pr_and_its_pending_reply_shows_at_once(s):
        s.change("s0", pr=7); s.agreed("s0"); s.change("s1", deps=["s0"], pr=7, finding=99); s.agreed("s1")
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> reset it\n\n@rev kept.")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A, "fork/dev/s1": ""}, "trees": dict(FACTS["trees"]), "merges": dict(FACTS["merges"]),
                    "comments": {7: [{"id": 99, "author": "rev", "bot": False, "reply": None, "path": "N.kt", "line": 3, "body": "reset it?"}]},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s0", "owner": "o", "head": A, "draft": False}]}})
        for k in ("s0", "s1"):
            s.gated(k, F); s.verdict(k, A, {"ok": "pass", "j1": "pass"}, F)
        hd.put("live", "tree", {"tree": "x", "commit": C, "heads": [A]})
        F.f["refs"]["origin/HEAD"] = D; F.f["trees"].update({D: TC, C: "te" * 20}); F.f["merges"][(D, A)] = ("ok", C)   # upstream main moved: a new T
        s.assertEqual(s.state(F, "s0")["state"], "gated; the PR waits for s1")   # no rebuild, no re-gate of the PR's live head
        s.assertEqual(s.state(F, "s1")["actor"], "user")
        s.assertEqual(len(hd.tick(s.ctx(F), act=False)["card"]), 1)             # the reply's card at once

    def test_a_reply_only_change_gets_its_card_with_no_gate_run(s):
        s.change("s0", pr=7); s.change("s1", deps=["s0"], pr=7, finding=99); s.agreed("s1")
        (s.root / "evidence" / "s1" / "pr-comment.md").write_text("> reset it\n\n@rev kept.")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s0": A, "fork/dev/s1": ""},
                    "prs": {"u/f": [{"number": 7, "branch": "content/s0", "owner": "o", "head": A, "draft": False}]}})
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch("sys.stdout", new_callable=io.StringIO):
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)                    # its QA verdict alone: no build, no gate
        c = hd.tick(s.ctx(F))["card"]
        s.assertEqual(len(c), 1); s.assertTrue(c[0].startswith("s1: ")); s.assertNotIn("CI", c[0])
        s.assertEqual([x for x in F.spawned if x[1] in ("build", "gate")], []); s.assertIsNone(hd.rec("s1", "gate"))

    def test_a_dependent_joins_its_dependencys_open_pr(s):
        s.change("s1", pr=9, branch="content/x"); s.agreed("s1"); s.change("s2", deps=["s1"]); s.agreed("s2"); s.change("s3", deps=["s2"])
        ctx = s.ctx(Fake(**FACTS))
        s.assertEqual([(ctx.changes[k].get("pr"), ctx.changes[k].get("branch")) for k in ("s2", "s3")], [(9, "content/x")] * 2)  # a chain is one PR
        s.change("s4", "client", deps=["s1"])                                    # another track: no PR to join
        s.assertNotIn("branch", s.ctx(Fake(**FACTS)).changes["s4"])

    def test_a_pr_with_a_finding_not_in_the_head_gets_no_card(s):
        s.change("s1", pr=9); s.agreed("s1"); s.change("s1-c8", deps=["s1"], pr=9, finding=8)
        F = Fake(refs={"origin/HEAD": B, "fork/dev/s1": A}, trees={A: TA, B: TB})
        s.gated("s1", F); s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["state"], "gated; the PR waits for s1-c8")
        s.assertEqual(hd.tick(s.ctx(F))["card"], [])                             # not a complete PR: not ready

    def test_a_stacked_head_is_refused_at_the_gate(s):
        s.change("s1"); s.agreed("s1"); s.change("s2"); s.agreed("s2")
        F = Fake(refs={"origin/HEAD": B, "fork/dev/s1": A, "fork/dev/s2": C}, trees={A: TA, B: TB, C: TC}, commits={A: {A}, C: {C, A}})
        s.gated("s2", F)
        st = s.state(F, "s2")
        s.assertEqual((st["actor"], st["state"]), ("dev", "stacked on s1: dev"))  # s2's branch carries s1's unmerged commit
        s.assertIn(f"upstream main ({B[:9]})", st["detail"])
        F.f["refs"]["origin/HEAD"] = D; F.f["commits"] = {A: set(), C: {C}}       # s1 merged upstream: s2 holds only its own
        F.f["trees"][D] = "td" * 20; F.f["merges"] = {(D, C): ("ok", C)}
        s.assertNotEqual(s.state(F, "s2")["actor"], "dev")
        F.f["refs"]["origin/HEAD"] = B; F.f["commits"] = {A: {A}, C: {C, A}}
        for slug in ("s1", "s2"):                                                  # one PR: one branch, not a stack
            p_ = s.root / "harness" / "changes" / f"{slug}.md"; p_.write_text(p_.read_text().replace("---\ndo it", 'pr: 9\n---\ndo it'))
        s.assertEqual(s.state(F, "s2")["actor"], "qa")

    def test_the_pass_rebases_a_carried_tools_head_its_branch_moved_past(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        fork = str(s.root / "fork")
        F = Fake(refs={"HEAD": B, "harness/h1": A, f"{fork}:harness/h1": C}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)}, anc={(C, "local/harness")})
        s.gated("h1", F)
        F.f["anc"] = set(); F.f["refs"]["local/harness"] = B                    # another change shipped: local/harness moved past C
        F.f["rebases"] = {"harness/h1": ("conflict", "conflict in tools/x\nCONFLICT (content): Merge conflict in tools/x")}
        st = s.state(F, "h1")
        s.assertEqual(st["actor"], "script"); st["act"]()                        # the pass tries the rebase itself
        st = s.state(F, "h1")
        s.assertEqual((st["actor"], st["state"], st["detail"].split("\n")[0]), ("dev", f"tools conflict in {fork}: dev", "conflict in tools/x"))  # the rebase stopped: the dev's, naming the files
        F.f["refs"]["local/harness"] = D                                         # the branch moves again: the pass tries again
        F.f["rebases"] = {"harness/h1": ("ok", D)}
        st = s.state(F, "h1")
        s.assertEqual(st["actor"], "script"); st["act"]()                        # a clean rebase: no dev run
        s.assertIn(["rebase", fork, "harness/h1", "local/harness"], F.ran)
        F.f["refs"][f"{fork}:harness/h1"] = D; F.f["anc"] = {(D, "local/harness")}
        s.assertEqual((hd.rec("h1", "handover")["tools"], hd.rec("h1", "handover")["T"]), ({"fork": D}, TA + "+" + D[:12]))
        s.assertEqual(s.state(F, "h1")["state"], f"gate on {TA[:9]}")          # the new head is recorded and re-gated in its batch

    def test_the_hand_over_runs_the_carried_tools_heads_tests(s):  # a fork head failing its own tests showed only at the batch gate
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        fork = str(s.root / "fork")
        F = Fake(refs={"HEAD": B, "harness/h1": A, f"{fork}:harness/h1": C}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)}, anc={(C, "local/harness")},
                 rows={"tools/track.sh check-tools": (1, "FAIL: test_x (test_tools.BuildAttempts.test_x)")})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertIn("a carried tools head's tests fail: FAIL: test_x", str(e.exception)); s.assertIsNone(hd.rec("h1", "handover"))
        F.f["rows"] = {}
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual(hd.rec("h1", "handover")["tools"], {"fork": C})

    def test_a_batch_merges_its_members_tools_heads_in_one_go(s):  # one carrying the fork's tools waited for another's ship, then rebased
        for k in ("h1", "h2"):
            s.change(k, track="harness"); s.agreed(k, track="harness")
        fork, H1, H2, M2, T1, T2, TM = str(s.root / "fork"), "1" * 40, "2" * 40, "m2" * 20, "e" * 40, "f" * 40, "9" * 40
        F = Fake(refs={"HEAD": B, "harness/h1": H1, "harness/h2": H2, f"{fork}:harness/h1": T1, f"{fork}:harness/h2": T2}, trees={B: "t0", H1: "t1", H2: "t2", M2: "t12"},
                 merges={(B, H1): ("ok", H1), (B, H2): ("ok", H2), (H1, H2): ("ok", M2), (T1, T2): ("ok", TM)}, anc={(T1, "local/harness"), (T2, "local/harness")})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"]); hd.cmd_handover(["h2", "Limits:", "none"])
        s.assertEqual([s.state(F, k)["state"] for k in ("h1", "h2")], [f"gate on t12+{TM[:5]}"] * 2)   # one batch: both tools heads merged
        hd.tick(s.ctx(F))
        s.assertEqual((F.envs[-1]["NAMES"], F.envs[-1]["TOOLS"]), ("h1,h2", f"{fork}:local/harness:{TM}:o/f"))   # ship fast-forwards the branch to the merge
        F.f["merges"][(T1, T2)] = ("conflict", "CONFLICT (content): tools/x")
        s.assertEqual(s.state(F, "h2")["state"], "waiting for the batch ahead: its fork tools conflict with h1's")

    def test_ready_harness_siblings_ship_in_one_gate_a_failure_bisected_to_its_change(s):
        for k in ("h1", "h2", "h3"):
            s.change(k, track="harness"); s.agreed(k, track="harness")
        H1, H2, H3, M2, M3 = "1" * 40, "2" * 40, "3" * 40, "m2" * 20, "m3" * 20
        F = Fake(refs={"HEAD": B, "harness/h1": H1, "harness/h2": H2, "harness/h3": H3}, trees={B: "t0", H1: "t1", H2: "t2", H3: "t3", M2: "t12", M3: "t123"},
                 merges={(B, H1): ("ok", H1), (B, H2): ("ok", H2), (B, H3): ("ok", H3), (H1, H2): ("ok", M2), (M2, H3): ("ok", M3)})
        with mock.patch.object(hd, "Facts", lambda: F):
            for k in ("h1", "h2", "h3"):
                hd.cmd_handover([k, "Limits:", "none"])
        states = lambda: [s.state(F, k)["state"] for k in ("h1", "h2", "h3")]
        s.assertEqual(states(), ["gate on t123"] * 3)                             # one tree: base, then each in hand-over order
        hd.tick(s.ctx(F))
        s.assertEqual([x[1:] for x in F.spawned], [["gate", "ship-harness", M3]])  # one gate for all three
        s.assertEqual(F.envs[-1]["NAMES"], "h1,h2,h3")
        hd.put("ship-harness", "gate-t1", {"ok": True}); F.f["procs"] = {(7, "1"), (4242, "99")}   # a shorter prefix passes while the batch gates: nothing ships
        s.assertEqual(states(), ["gate on t123"] * 3)
        F.f["procs"] = {(7, "1")}                                                       # no gate running: the longest passing prefix ships, the rest wait
        s.assertEqual(states(), ["shipping"] + ["waiting for the batch ahead (shipping)"] * 2)
        hd.put("ship-harness", "gate-t123", {"ok": False, "detail": "FAIL: tests"})   # the batch fails: the prefix between them
        s.assertEqual(states(), ["gate on t12"] * 2 + ["waiting for the batch ahead (gate on t12)"])
        hd.put("ship-harness", "gate-t12", {"ok": False, "detail": "FAIL: tests"})    # the next longer fails: the longest passing ships
        s.assertEqual(states(), ["shipping", "waiting for the batch ahead (shipping)", "waiting for the batch ahead (shipping)"])
        for k in ("t1", "t12"):
            (s.root / "state" / "ship-harness" / f"gate-{k}.json").unlink()
        hd.put("ship-harness", "gate-t123", {"ok": True})
        hd.tick(s.ctx(F))
        s.assertEqual([x[1:] for x in F.spawned], [["gate", "ship-harness", M3], ["ship", "ship-harness", M3]])  # shipped once
        s.assertEqual(states(), ["shipping"] * 3)
        F.f["procs"] = {(7, "1"), (4242, "99")}; hd.tick(s.ctx(F))                 # the ship runs: no second one starts
        s.assertEqual(len(F.spawned), 2)
        hd.put("ship-harness", "gate-t123", {"ok": False, "detail": "FAIL: tests"})   # a failure: the first half alone, then the culprit
        s.assertEqual(states(), ["gate on t1", "waiting for the batch ahead (gate on t1)", "waiting for the batch ahead (gate on t1)"])
        hd.put("ship-harness", "gate-t1", {"ok": False, "detail": "FAIL: tests"})       # the first alone fails: the live branch's own gate decides
        s.assertEqual(states(), ["gate on the live branch t0"] + ["waiting for the batch ahead (gate on the live branch t0)"] * 2)
        F.f["procs"] = {(7, "1")}; hd.tick(s.ctx(F))
        s.assertEqual((F.spawned[-1][1:], F.envs[-1]["NAMES"]), (["gate", "ship-harness", B], "h1"))   # h1's rows at the base
        hd.put("ship-harness", "gate-t0", {"ok": False, "detail": "FAIL: tests"})       # the live branch fails alone: an alert, no member blamed
        v = hd.tick(s.ctx(F))
        s.assertEqual(states(), ["waiting: the live branch fails its own gate"] * 3)
        s.assertIn("harness: the live branch fails its own gate at t0 (state/ship-harness/gate-t0.json)", v["alert"])
        hd.put("ship-harness", "gate-t0", {"ok": True})                                # it passes alone: h1's failure is h1's
        st = s.state(F, "h1")
        s.assertEqual((st["state"], st["actor"], st["detail"]), ("gate failed: dev", "dev", "FAIL: tests"))
        F.f["procs"] = set(); hd.tick(s.ctx(F))
        dev = [r for r in hd.runs() if r["change"] == "h1"][-1]
        for r in [dev] + [r for r in hd.runs() if r["role"] == "planner"]:   # its dev handed back and the batch gate still fails; the alert's planner too
            r.update(started=hd.now(), ended=hd.now(), record=True); hd.save_run(r)
        hd.tick(s.ctx(F))
        s.assertTrue(any(i.startswith("h1 [harness") and i.endswith("gate failed: dev at t1") for r in hd.runs() if r["role"] == "planner"
                         for i in json.loads(r["input"])))                         # the planner reads the batch's gate, keyed by its tree
        F.f["merges"][(H2, H3)] = ("ok", "m4" * 20); F.f["trees"]["m4" * 20] = "t23"   # h1 leaves the batch: h2, h3 on the base
        s.assertEqual(states()[1:], ["gate on t23", "gate on t23"])
        F.f["merges"][(H2, H3)] = ("conflict", "CONFLICT: x")                       # only with h2: h3 waits for the batch ahead
        s.assertEqual(states()[1:], ["gate on t2", "waiting for the batch ahead: conflicts with h2"])
        F.f["merges"][(B, H3)] = ("conflict", "CONFLICT: y")                        # with the live branch: its dev's
        s.assertEqual((s.state(F, "h3")["state"], s.state(F, "h3")["detail"]), ("tree conflict: dev", "CONFLICT: y"))

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
        import fcntl, threading
        (s.root / "state").mkdir(exist_ok=True); h = open(s.root / "state" / ".lock", "w"); fcntl.flock(h, fcntl.LOCK_EX)   # a pass acting
        t = threading.Thread(target=lambda: setattr(t, "r", ship(T1))); t.start()
        while t.is_alive() and len(subprocess.run(["fuser", str(s.root / "state" / ".lock")], capture_output=True, text=True).stdout.split()) < 2:
            pass                                                                      # until the ship's flock holds the state lock open: it waits on it
        s.assertNotEqual(git("rev-parse", "v8"), T1)                                  # the live branch never moves under an acting pass
        h.close(); t.join(); r = t.r
        s.assertEqual((r.returncode, git("rev-parse", "v8"), git("ls-remote", "origin", "v8").split()[0]), (0, T1, T1), r.stdout + r.stderr)
        hd.put("s1", "gate-k", {"ok": True}); hd.put("s1", "gate-g", {"ok": True})
        r = subprocess.run([str(repo / "tools" / "track.sh"), "ship", "s1", T1], env={**os.environ, "HD_ROOT": str(s.root), "G": "g"}, capture_output=True, text=True)   # a T that already landed: a no-op, its gates spent
        s.assertEqual((r.returncode, git("rev-parse", "v8"), hd.rec("s1", "gate-k")), (0, T1, None), r.stdout + r.stderr)
        s.assertTrue(hd.rec("s1", "gate-g")["ok"])                                    # sweep-21: but the shipped tree's own gate (G), which the live branch's gate reads
        s.assertIn("already on the live branch", r.stdout); s.assertTrue((s.root / "state" / "ship.lock").exists())   # taken under the one ship lock
        git("checkout", "-q", "--detach"); T2 = commit("T2 on T1"); git("checkout", "-q", "v8"); moved = commit("the head's own commit")
        hd.put("s1", "proc-ship", {"pid": 1, "start": "x", "attempts": 1})
        r = ship(T2)                                                                  # the live branch moved past T2's base
        s.assertEqual((r.returncode, git("rev-parse", "v8"), hd.rec("s1", "proc-ship")), (0, moved, None), r.stdout + r.stderr)   # untouched; ship starts afresh on the re-gated T
        shutil.rmtree(tmp, ignore_errors=True)

    def test_a_pass_whose_hd_py_a_ship_moved_acts_nothing(s):
        s.change("s1"); s.agreed("s1")
        code, hd.CODE = hd.CODE, b"the hd.py before the ship"
        try:
            s.assertIsNone(hd.tick(s.ctx(Fake(**FACTS))))                             # it loaded the old code: no run, build or ship from it
        finally:
            hd.CODE = code
        s.assertEqual(hd.runs(), [])
        hd.tick(s.ctx(Fake(**FACTS))); s.assertEqual([r["name"] for r in hd.runs()], ["s1-1"])   # the live code's pass acts

    def test_a_definition_commit_waits_for_the_ship_lock(s):
        import fcntl
        git = lambda *a: subprocess.run(["git", "-C", str(s.root), *a], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "init", "-q", str(s.root)], check=True); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
        (s.root / "harness" / "changes").mkdir(parents=True, exist_ok=True); (s.root / "harness" / "changes" / "d1.md").write_text("a definition")
        (s.root / "other.txt").write_text("an edit of someone else"); git("add", "other.txt")
        subprocess.run(["git", "init", "-q", "--bare", str(s.root / "origin.git")], check=True); git("remote", "add", "origin", str(s.root / "origin.git"))
        (s.root / "state").mkdir(exist_ok=True)
        with open(s.root / "state" / "ship.lock", "w") as h:
            fcntl.flock(h, fcntl.LOCK_EX)                                             # a ship holds the lock
            p = subprocess.Popen([sys.executable, str(Path(hd.__file__)), "commit", "harness/changes/d1.md", "-m", "harness: define d1"],
                                 env={**os.environ, "HD_ROOT": str(s.root)}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            s.assertEqual(git("log", "--format=%s"), "base")                          # nothing commits while it is held
        out = p.communicate()[0]
        s.assertEqual(p.returncode, 0, out)
        s.assertEqual(git("log", "-1", "--format=%an <%ae>%n%B").splitlines()[:3], [f"{hd.AUTHOR[0]} <{hd.AUTHOR[1]}>", "harness: define d1", ""])
        s.assertEqual(git("show", "--name-only", "--format=", "HEAD"), "harness/changes/d1.md")   # pathspec-only: the staged edit stays staged
        s.assertEqual(git("diff", "--cached", "--name-only"), "other.txt")
        s.assertEqual(git("-C", str(s.root / "origin.git"), "rev-parse", git("branch", "--show-current")), git("rev-parse", "HEAD"))   # pushed to origin

    def test_the_suite_ignores_the_gates_tools(s):
        tmp = Path(tempfile.mkdtemp()); fork = tmp / "fork"
        run = lambda *a: subprocess.run(["git", "-C", str(fork), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "init", "-q", "-b", "local/harness", str(fork)], check=True); run("commit", "-q", "--allow-empty", "-m", "base")
        subprocess.run(["git", "init", "-q", "--bare", str(tmp / "fork.git")], check=True); run("remote", "add", "fork", str(tmp / "fork.git"))
        run("checkout", "-q", "--orphan", "harness/s1"); run("commit", "-q", "--allow-empty", "-m", "not a fast-forward"); C = run("rev-parse", "HEAD")
        run("checkout", "-q", "local/harness"); before = run("rev-parse", "local/harness")
        r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_hd.R8.test_ship_fast_forwards_the_live_branch_or_regates"], cwd=Path(__file__).parent.parent,
                           env={**os.environ, "HD_SUITE": "nested", "TOOLS": f"{fork}:local/harness:{C}:AlexPerrin/OpenRune-Server", "T": "t", "TCOMMIT": C}, capture_output=True, text=True)
        s.assertEqual((r.returncode, run("rev-parse", "local/harness"), run("ls-remote", "fork")), (0, before, ""), r.stdout + r.stderr)
        shutil.rmtree(tmp, ignore_errors=True)

    def test_a_carried_heads_tests_run_without_the_gates_env(s):  # the fork's tests read T: the gate's T named their logs
        tmp = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, tmp, True); fork = tmp / "fork"
        run = lambda *a: subprocess.run(["git", "-C", str(fork), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "init", "-q", "-b", "local/harness", str(fork)], check=True); (fork / "tools").mkdir()
        (fork / "tools/test_env.py").write_text("import os, unittest\nclass E(unittest.TestCase):\n    def test(s): s.assertNotIn('T', os.environ)\n")
        run("add", "-A"); run("commit", "-qm", "t"); C = run("rev-parse", "HEAD")
        r = subprocess.run([str(Path(__file__).parent.parent / "tools" / "track.sh"), "check-tools"], capture_output=True, text=True,
                           env={**os.environ, "SLUG": "s1", "T": "t", "TOOLS": f"{fork}:local/harness:{C}:AlexPerrin/OpenRune-Server"})
        s.assertEqual(r.returncode, 0, r.stdout + r.stderr); s.assertIn("OK", r.stdout)

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
        s.assertEqual((r.returncode, run(repo, "rev-parse", "v8"), run(fork, "rev-parse", "local/harness"), hd.rec("s1", "proc-ship")),
                      (0, live, moved, None), r.stdout + r.stderr)   # nothing moved; the pass rebases the carried head, a new key re-gates
        run(wt, "reset", "-q", "--hard", "HEAD~1")
        r = ship()
        s.assertEqual((r.returncode, run(repo, "rev-parse", "v8"), run(fork, "rev-parse", "local/harness")), (0, T, C), r.stdout + r.stderr)
        s.assertEqual((run(fork, "ls-remote", "fork", "local/harness").split()[:1], run(fork, "ls-remote", "origin")), ([C], ""))   # pushed to the fork, never upstream
        run(fork, "checkout", "-q", "harness/s1"); C2 = commit(fork, "a tools-only change"); run(fork, "checkout", "-q", "main")
        tools = lambda c: subprocess.run([str(repo / "tools" / "track.sh"), "ship", "s1", T], env={**os.environ, "HD_ROOT": str(s.root), "TOOLS": f"{fork}:local/harness:{c}:AlexPerrin/OpenRune-Server"}, capture_output=True, text=True)
        r = tools(C2)                                                            # T already on the live branch: its tools head still lands (sweep-24: it looped ship <-> gate)
        s.assertEqual((r.returncode, run(repo, "rev-parse", "v8"), run(fork, "ls-remote", "fork", "local/harness").split()[:1]), (0, T, [C2]), r.stdout + r.stderr)
        hd.put("s1", "gate-x", {"T": "x", "ok": True}); r = tools(C2)
        s.assertIn("already on the live branch, every carried tools head on its branch", r.stdout); s.assertIsNone(hd.rec("s1", "gate-x"))
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
            hd.cmd_handover(["s2", "Limits:", "none"])
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
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.assertIn("x.kt", str(e.exception))
        hd.put("s1", "handover", {"head": A, "T": "old", "commit": "old"})          # a hand-over from before the base moved
        st = s.state(F, "s1")
        s.assertEqual((st["actor"], st["state"]), ("dev", "tree conflict: dev"))

    def test_sibling_doc_facts_merge_in_either_order_and_one_fact_changed_two_ways_conflicts(s):
        # the source docs hold one fact per line (tools/docfmt.py), a blank line between requirements and paragraphs
        root, tmp = Path(__file__).parent.parent, Path(tempfile.mkdtemp())
        docs = ["docs/PROBLEM.md", "docs/PRD.md", "docs/ARCHITECTURE.md"]
        fmt = lambda *a: subprocess.run([sys.executable, str(root / "tools/docfmt.py"), "--check", *a], cwd=root, capture_output=True, text=True)
        s.assertEqual(fmt(*docs).stderr, "")
        (tmp / "wrapped.md").write_text("one fact; another fact.\n")
        s.assertIn("wrapped.md:1: not one fact per line", fmt(str(tmp / "wrapped.md")).stderr)
        git = lambda *a: subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q", "-b", "live"); (tmp / "docs").mkdir()
        for d in docs:
            shutil.copy(root / d, tmp / d)
        git("add", "."); git("commit", "-qm", "base"); base = git("rev-parse", "HEAD")

        def chunks(d):  # the last line of each requirement (PRD) or block outside code (the others)
            L, fence, last, start = (tmp / d).read_text().split("\n"), False, [], None
            for i, l in enumerate(L):
                fence ^= l.startswith("```")
                if fence or l.startswith("```") or not l.strip():
                    start = None; continue
                start = i if start is None else start
                if (i + 1 == len(L) or not L[i + 1].strip()) and not l.startswith("#") and (not d.endswith("PRD.md") or L[start].startswith("### R")):
                    last.append(i)
            return L, last

        def sibling(name, parity, edit=None):  # every other unit's last fact changed and a new fact added after it
            git("checkout", "-q", "-b", name, base)
            for d in docs:
                L, last = chunks(d)
                for k, i in reversed(list(enumerate(last))):
                    if k % 2 == parity:
                        L[i] += f" ({name})"; L.insert(i + 1, f"a fact of {name}.")
                (tmp / d).write_text("\n".join(edit(L) if edit else L))
            git("commit", "-qam", name); return git("rev-parse", "HEAD")
        a, b = sibling("a", 0), sibling("b", 1)
        F = hd.Facts()
        s.assertEqual(len(chunks("docs/PRD.md")[1]), 8)                           # every requirement is a unit of its own
        for first, second in [(a, b), (b, a)]:                                   # the first ships (live = its T), the second's T is merged onto it
            live = F.merge(str(tmp), base, first, "T first")
            s.assertEqual(live[0], "ok")
            s.assertEqual(F.merge(str(tmp), live[1], second, "T second")[0], "ok")
        fact = lambda how: lambda L: [l.replace("A defined change reaches its live target", how, 1) for l in L]
        c, d = sibling("c", 2, fact("A defined change reaches its target")), sibling("d", 2, fact("A change reaches its live target"))
        s.assertEqual(F.merge(str(tmp), c, d, "T same fact")[0], "conflict")   # the same fact changed two ways is the dev's

    def test_neighbouring_doc_fact_lines_merge_line_by_line(s):
        # the PRD.md:164 case: one change edits the 'hd stop' fact, another inserts a fact on the line before it
        root, tmp = Path(__file__).parent.parent, Path(tempfile.mkdtemp())
        s.addCleanup(shutil.rmtree, tmp, True)
        git = lambda *a: subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q", "-b", "live"); (tmp / "docs").mkdir(); shutil.copy(root / "docs/PRD.md", tmp / "docs/PRD.md")
        (tmp / "x.kt").write_text("x\n")
        git("add", "."); git("commit", "-qm", "base"); base = git("rev-parse", "HEAD")
        L = (tmp / "docs/PRD.md").read_text().split("\n")
        stop = next(i for i, l in enumerate(L) if "ends and frees its slot" in l)

        def side(name, edit, kt=None):
            git("checkout", "-q", "-b", name, base)
            (tmp / "docs/PRD.md").write_text("\n".join(edit(list(L))))
            if kt:
                (tmp / "x.kt").write_text(kt)
            git("commit", "-qam", name); return git("rev-parse", "HEAD")
        at = lambda i, f: lambda M: M[:i] + f(M[i]) + M[i + 1:]
        run_stop = side("run-stop", at(stop, lambda l: [l.replace("ends and frees its slot", "ends, frees its slot and its worktree")]))
        pinned = side("pinned", at(stop - 1, lambda l: [l, "   a tools head is pinned per process;"]))
        F = hd.Facts()
        for a, b in [(run_stop, pinned), (pinned, run_stop)]:
            r = F.merge(str(tmp), a, b, "T")
            s.assertEqual(r[0], "ok")
            both = L[:stop] + ["   a tools head is pinned per process;", L[stop].replace("ends and frees its slot", "ends, frees its slot and its worktree")] + L[stop + 1:]
            s.assertEqual(git("show", f"{r[1]}:docs/PRD.md"), "\n".join(both).strip())
        other = side("other", at(stop, lambda l: [l.replace("ends and frees its slot", "ends")]))
        s.assertEqual(F.merge(str(tmp), run_stop, other, "T")[0], "conflict")                  # the same fact changed two ways
        code = side("code", at(stop - 1, lambda l: [l, "   a code fact;"]), "y\n")
        kt = side("kt", lambda M: M, "z\n")
        s.assertEqual(F.merge(str(tmp), code, kt, "T")[0], "conflict")                         # a conflict outside the docs stays the dev's
        s.assertIsNone(hd.merge_lines(["a", "b"], ["x"], ["a", "n", "b"]))                       # an insertion inside the other's changed lines
        s.assertEqual(hd.merge_lines(["a", "b"], ["x", "a", "b"], ["y", "a", "b"]), ["x", "y", "a", "b"])   # two insertions at one point: both

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

    def test_a_tools_ship_keeps_a_gated_head_in_integration(s):  # sweep-31 P1-a: a tools ship dropped every head not yet re-gated from the deploy
        s.change("s1"); s.agreed("s1")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: {"tools/gate/gate.sh": "1"}}})
        t = s.gated("s1", F)["T"]; ctx = s.ctx(F); k = ctx.key(ctx.changes["s1"], t)
        hd.put("s1", "gate", {"T": k, "ok": True})
        F.f["tools_files"][C] = {"tools/gate/gate.sh": "2"}; F.f["refs"]["local/harness"] = C   # the tools ship: a new gate key
        ctx = s.ctx(F)
        s.assertFalse(ctx.gated(ctx.changes["s1"], A))                          # nxt re-gates it
        s.assertIn("s1", hd.integration(ctx)["names"])                          # its passed gate at the same tree still holds in T_int
        hd.put("s1", "gate", {"T": ctx.key(ctx.changes["s1"], t), "ok": False}) # the re-gate fails
        s.assertNotIn("s1", hd.integration(s.ctx(F))["names"])
        hd.put("s1", "gate", {"T": k.replace(t, "other", 1), "ok": True})     # a pass at another tree never holds
        s.assertNotIn("s1", hd.integration(s.ctx(F))["names"])

    def test_merge_ref_stands_in_for_pair_in_integration(s):
        F, R = s.integration_fixture(with_ref=True)
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["commit"], t["names"]), (R, ["local/x", "s1"]))
        v = hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["ship", "integration", R])
        s.assertEqual(F.envs[-1]["T"], "tr" * 20)
        s.assertIn("s1 [server P2]: gated; waiting for the user's yes; test server: deploying trtrtrtrt", v["change"])
        F.f["procs"] = {(7, "1"), (4242, "99")}                                      # the deploy is running: not started again
        hd.tick(s.ctx(F)); s.assertEqual(len([x for x in F.spawned if x[1] == "ship"]), 1)
        F.f["trees"][R] = "tz" * 20                                                  # sweep-26 P0-a: a newer tree mid-deploy (its 213 MB download at 47%)
        v = hd.tick(s.ctx(F)); s.assertEqual((F.stopped, len([x for x in F.spawned if x[1] == "ship"])), ([], 1))   # it runs to its end
        s.assertIn("test server: a deploy runs, then tztztztzt", v["change"][0])
        F.f["trees"][R] = "tr" * 20
        hd.put("live", "tree", {"tree": "tr" * 20, "commit": R, "heads": [A], "names": ["local/x", "s1"]})
        s.assertEqual(s.state(F, "s1")["state"], "gated; waiting for the user's yes")

    def test_a_resolution_follows_the_head_while_it_merges(s):  # server-token-auth: a comment-only head move dropped local/merge/113f93a-a8cae09
        F, R = s.integration_fixture(with_ref=True)
        A2, Q, R2 = "b2" * 20, "q" * 40, "s" * 40
        F.f["refs"].update({"fork/dev/s1": A2, "old-head": A}); F.f["anc"] = {(A2, A)}; F.f["trees"].update({A2: TA, R2: "ts" * 20, Q: "tq" * 20})
        F.f["merges"].update({(Q, A2): ("conflict", "CONFLICT (content): y.kt"), (R, A2): ("ok", R2)})
        s.gated("s1", F)
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A2, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["commit"], t["names"], t["conflicts"]), (R2, ["local/x", "s1"], []))   # the new head merged on the old resolution
        F.f["merges"][(R, A2)] = ("conflict", "CONFLICT (content): y.kt")                    # it no longer applies: the dev's
        s.assertEqual(hd.integration(s.ctx(F))["conflicts"][0]["conflict"], "s1")
        F.f["merges"][(R, A2)] = ("ok", R2); F.f["anc"] = set()                               # a head not on the resolved one: not bound
        s.assertEqual(hd.integration(s.ctx(F))["conflicts"][0]["conflict"], "s1")

    def test_conflict_without_a_resolution_is_the_younger_change_s(s):
        F, R = s.integration_fixture(with_ref=False)
        F.f["trees"]["q" * 40] = "tq" * 20                                          # the base and the pin merge on without s1
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["conflicts"][0]["conflict"], t["conflicts"][0]["with"]), ("s1", ["local/x"]))
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))
        s.assertIn("local/merge/<yours7>-<theirs7>", open(hd.runs()[0]["brief"]).read())
        s.assertEqual([x for x in F.spawned if x[1:3] == ["ship", "integration"]], [])
        s.assertTrue(hd.rec("s1", "state")["state"].startswith("gated; waiting for the user's yes"))   # the card waits on its own gate alone
        s.assertIn("conflicts with the integration tree", hd.rec("s1", "state")["state"])
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))                 # the conflict's dev run stays listed beside the card
        s.approve(F, "s1", A)
        s.assertEqual(s.state(F, "s1")["state"], "carrying upstream")              # nor does the conflict hold the carry

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
        s.assertIn(["ship", "integration", A], [x[1:] for x in F.spawned])         # the P1 deploys
        s.assertTrue(any(x.startswith("lo-") for x in v["spawn"]))                 # the P1 has no run due: the P3's conflict is its dev's

    def test_a_check_row_at_the_hand_over_builds_the_pass_s_key(s):  # a dev's build of server-token-auth ran as <tree>-c<central>, the pass's as <tree>-c<central>-<build>
        s.change("s1"); s.agreed("s1", extra="- t | tests | check: tools/track.sh test\n")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: {"tools/build/build.sh": "1"}}})
        envs = []; run = F.run; F.run = lambda cmd, cwd, env: (envs.append(env), run(cmd, cwd, env))[1]
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1", "Limits:", "none"])
        ctx = s.ctx(F)
        s.assertEqual(envs[-1]["T"], ctx.key(ctx.changes["s1"], TA, build=True))

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

    def test_a_held_change_s_pin_conflict_lists_no_run(s):
        F, R = s.integration_fixture(with_ref=False)
        F.f["merges"][(B, "p" * 40)] = ("conflict", "CONFLICT (content): MusicTabScript.kt")
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        c = json.loads((s.root / "hd.yaml").read_text()); c["hold"] = "P1"; (s.root / "hd.yaml").write_text(json.dumps(c))
        for _ in range(2):                                                           # s1 (P2) is held: its pin step lists nothing, pass after pass
            s.assertFalse([x for x in hd.tick(s.ctx(F))["spawn"] if x.startswith("s1-")])
        s.assertEqual([r for r in hd.runs() if r["change"] == "s1"], [])
        c["hold"] = None; (s.root / "hd.yaml").write_text(json.dumps(c))
        s.assertTrue(any(x.startswith("s1-") for x in hd.tick(s.ctx(F))["spawn"]))  # released: the pin's dev is listed

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

    def test_a_base_move_after_the_hand_over_keeps_a_regated_change_in_t_int(s):
        F, R = s.integration_fixture(with_ref=False)
        E, X = "e" * 40, "x" * 40
        F.f["refs"]["origin/HEAD"] = E                                               # the base moves; T is recomputed and re-gated
        F.f["trees"][X] = "tx" * 20
        F.f["merges"].update({(E, A): ("ok", X), (E, "p" * 40): ("conflict", "CONFLICT (content): ObjTakePlugin.kt")})
        for k in ("build", "gate"):
            hd.put("s1", k, {"T": "tx" * 20, "ok": True})                            # the hand-over keeps the old T
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        s.assertNotEqual(hd.rec("s1", "handover")["T"], "tx" * 20)
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["conflict"], t["change"]["slug"]), ("local/x", "s1"))      # the pin's conflict has its owner
        v = hd.tick(s.ctx(F))
        s.assertTrue(any(x.startswith("s1-") for x in v["spawn"]))
        s.assertEqual([a for a in v["alert"] if a.startswith("pin ")], [])

    def test_a_failed_local_head_is_neither_in_t_int_nor_done_though_deployed(s):  # server-world-entities went done over a FAIL
        s.change("s1", kind="local"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.assertEqual(hd.integration(s.ctx(F))["names"], ["s1"])                    # gated, not judged yet: it deploys
        hd.put("live", "tree", {"tree": "ti" * 20, "commit": A, "heads": [A]})     # another change's deploy carried it
        s.verdict("s1", A, {"ok": "pass", "j1": "fail: no"}, F)
        s.assertEqual(hd.integration(s.ctx(F))["names"], [])                       # a failed head leaves the tree
        s.assertTrue(s.state(F, "s1")["state"].startswith("FAIL 1 rows"))          # live, yet its dev's
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["state"], "done")

    def test_pin_base_conflict_resolved_by_its_merge_ref(s):
        F, R = s.integration_fixture(with_ref=False)
        P_, M2 = "p" * 40, "n" * 40
        F.f["merges"][(B, P_)] = ("conflict", "CONFLICT (content): MusicTabScript.kt")
        (s.root / "state" / "s1" / "verdicts.jsonl").write_text(json.dumps({"ts": "z", "head": A, "contract": hd.contract("s1")["hash"], "rows": {"ok": "pass", "j1": "pass"}, "rules": {}}) + "\n")
        t = hd.integration(s.ctx(F))
        s.assertEqual((t["conflict"], t["change"]["slug"], t["with"]), ("local/x", "s1", []))  # the base alone: owned, not an alert
        F.f["refs"][f"fork/local/merge/{P_[:7]}-{B[:7]}"] = M2; F.f["merges"][(B, M2)] = ("ok", "q" * 40); F.f["merges"][("q" * 40, A)] = ("ok", R)
        s.assertEqual(hd.integration(s.ctx(F))["names"], ["local/x", "s1"])
        F.f["refs"]["origin/HEAD"] = C                                               # the base moves past it: the resolution still serves
        F.f["anc"] = {(C, B)}; F.f["refs"]["old-base"] = B
        F.f["merges"].update({(C, P_): ("conflict", "CONFLICT (content): MusicTabScript.kt"), (C, M2): ("ok", "q" * 40)})
        s.assertEqual(hd.integration(s.ctx(F))["names"], ["local/x", "s1"])
        F.f["merges"][(C, M2)] = ("conflict", "CONFLICT (content): MusicTabScript.kt")  # the resolution itself no longer merges
        s.assertEqual(hd.integration(s.ctx(F))["conflict"], "local/x")
        F.f["anc"] = set(); F.f["merges"][(C, M2)] = ("ok", "q" * 40)                # a base not past the partner: not bound
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
            hd.cmd_handover(["s1", "Limits:", "none"])
        hd.tick(s.ctx(F))
        s.assertEqual(F.spawned[-1][1:], ["build", "s1", A])
        s.assertEqual((F.envs[-1]["SLUG"], F.envs[-1]["T"]), ("s1", TA))
        s.assertTrue((s.root / "state" / "s1" / "proc-build.json").exists())


class EndToEnd(unittest.TestCase):
    """A harness change through the real loop: real git, the real track script, real processes, no fakes."""

    @unittest.skipIf(NESTED, "nested")
    def test_harness_change_defined_to_live(s):
        import select
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
        (root / "harness" / "changes" / "e2e.md").write_text("---\nslug: e2e\ntrack: harness\nmechanism: loop\ntitle: e2e\n---\nadd a line to the README")
        (root / "evidence" / "e2e" / "note.txt").write_text("evidence")
        git("worktree", "add", "-q", str(repo / ".worktrees" / "e2e"), "-b", "harness/e2e", "main")   # the dev's clone
        wt = repo / ".worktrees" / "e2e"
        (wt / "README.md").write_text((wt / "README.md").read_text() + "\ne2e\n")
        subprocess.run(["git", "-C", str(wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-am", "e2e: a line"], check=True)
        head = subprocess.run(["git", "-C", str(wt), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        env = {**os.environ, "HD_ROOT": str(root), "HD_SUITE": "nested"}   # an inner suite: its EndToEnd skips, its gates refuse the suite
        hd_ = lambda *a: subprocess.run([sys.executable, str(src / "hd.py"), *a], env=env, capture_output=True, text=True)
        s.assertIn("contract: seed rows pending", hd_("tick").stdout)
        v = hd_("tick").stdout
        s.assertIn("dev run due", v); s.assertIn("spawn: e2e-1", v)
        r = hd_("handover", "e2e", "Limits:", "none"); s.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        def until(state):   # each pass, then block on the scripts it started: the run's pace never fails the test
            last = None
            while True:
                v = hd_("tick").stdout
                if state in v:
                    return v
                live = [p for f in (root / "state").glob("*/proc-*.json") if hd.Facts().alive((p := json.loads(f.read_text()))["pid"], p["start"])]
                if not live and v == last:
                    break                                                   # nothing runs and the pass moves nothing: stuck
                for p in live:
                    try:
                        fd = os.pidfd_open(p["pid"])
                    except ProcessLookupError:
                        continue
                    select.select([fd], [], []); os.close(fd)               # readable once the process exits
                last = v
            s.fail(f"never reached {state!r}; last view:\n{v}\n{(root / 'state' / 'ship-harness' / 'gate.json').read_text() if (root / 'state' / 'ship-harness' / 'gate.json').exists() else ''}" + "".join(f"\n{f}: {f.read_text()}" for f in sorted((root / 'state').glob('*/gate*.json'))))   # every gate's record: an inner suite's failure names itself
        until("gate on")
        until("shipping")
        until("e2e [harness P1]: done")
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
                                                   "    def test_b(s): sys.stderr.write('noise\\n' * 20)\n"
                                                   "    def test_c(s): import os; os.system('echo FAIL: lint/bad/evil: false # refused: rm -rf / >&2'); print('ERROR: t (x.y)')\n")   # a fixture's own output, through its fds or sys.stdout
        root = Path(tempfile.mkdtemp()); s.addCleanup(shutil.rmtree, root, True)
        r = subprocess.run([str(Path(__file__).parent.parent / "tools" / "track.sh"), "check-tests"], env={**os.environ, "BUILD": str(build), "HD_ROOT": str(root), "SLUG": "g1"}, capture_output=True, text=True)
        s.assertNotEqual(r.returncode, 0)
        l = r.stdout.splitlines()
        s.assertEqual((l[0].split()[:2], [x.split()[0] for x in l[-2:]]), (["FAIL:", "test_a"], ["Ran", "FAILED"]), r.stdout)   # the failed test alone: no fixture output, nothing lost
        s.assertEqual(l[-3], f"failed: test_a (test_x.X.test_a); whole report: {root}/state/g1/tests.txt")   # every failing test named last but the verdict: a record's tail (rows keep 800, a record 2000) keeps it
        s.assertIn("AssertionError: boom", r.stdout)                            # sweep-21: its reason too, the traceback's tail, not its name alone
        s.assertFalse(any(x in r.stdout for x in ("noise", "evil", "ERROR: t")), r.stdout)
        shutil.rmtree(build, ignore_errors=True)

    def test_a_failed_test_s_whole_report_outlives_the_run(s):
        """sweep-29: a failing test's whole message (longer than any record's tail), its output discarded, read after the runner's temp root is gone."""
        wt, root, tmp = (Path(tempfile.mkdtemp()) for _ in range(3))
        for d in (wt, root, tmp):
            s.addCleanup(shutil.rmtree, d, True)
        (wt / "tests").mkdir()
        msg = "first line of the inner record\n" + "".join(f"inner gate record line {i}\n" for i in range(200))   # > 2000 chars, > 6 lines
        (wt / "tests" / "test_y.py").write_text(f"import unittest\nclass Y(unittest.TestCase):\n    def test_long(s): s.fail({msg!r})\n")
        r = subprocess.run([str(Path(__file__).parent.parent / "tools" / "track.sh"), "test", "d1"], cwd=wt, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           env={**os.environ, "HD_ROOT": str(root), "TMPDIR": str(tmp)})
        s.assertNotEqual(r.returncode, 0); s.assertEqual(os.listdir(tmp), [])   # the runner's root is gone
        report = (root / "state" / "d1" / "tests.txt").read_text()
        s.assertIn("FAIL: test_long (test_y.Y.test_long)", report); s.assertIn(msg, report)

    def test_check_docs_and_gate_rows(s):
        import subprocess
        repo = Path(__file__).parent.parent
        s.assertEqual(subprocess.run([str(repo / "tools" / "track.sh"), "check-docs"], cwd=repo, env={**os.environ, "BUILD": str(repo)}, capture_output=True, text=True).returncode, 0)
        root = Path(tempfile.mkdtemp())
        for d in ("harness/changes", "harness/goals", "evidence/g1", "tools"):
            (root / d).mkdir(parents=True)
        (root / "hd.yaml").write_text(json.dumps({"repos": {"client": {"name": "o/c", "path": str(repo)}, "fork": {"name": "o/f", "path": str(repo)}, "harness": {"name": "o/h", "path": str(repo)}}, "agents": 3, "pins": []}))
        (root / "harness" / "changes" / "g1.md").write_text("---\nslug: g1\ntrack: harness\n---\n")
        (root / "evidence" / "g1" / "contract.md").write_text("agreed: x\n- a | fine | check: true\n- b | injected | gate: rm -rf /\n- c | script | gate: tools/track.sh check-docs\n- d | suite | gate: tools/track.sh check-tests\n")
        snap = subprocess.run(["git", "-C", str(repo), "stash", "create"], capture_output=True, text=True).stdout.strip() or "HEAD"
        r = subprocess.run([str(repo / "tools" / "track.sh"), "gate", "g1", snap], cwd=repo, env={**os.environ, "HD_ROOT": str(root), "T": "t", "NAMES": "", "EVIDENCE": str(root / "evidence" / "g1")}, capture_output=True, text=True)
        rec = json.loads((root / "state" / "g1" / "gate.json").read_text())
        s.assertEqual((r.returncode, rec["ok"]), (0, False), r.stderr)
        s.assertIn("FAIL: b: false # refused", rec["detail"]); s.assertIn("ok: a: true", rec["detail"]); s.assertIn("ok: c: tools/track.sh check-docs", rec["detail"])
        s.assertIn("FAIL: d: tools/track.sh check-tests", rec["detail"]); s.assertIn("refused: the test suite runs inside itself", rec["detail"])   # a test's gate cannot recurse
        idx = root / "idx"; g = lambda *a, i=None: subprocess.run(["git", "-C", str(repo), *a], input=i, capture_output=True, text=True, env={**os.environ, "GIT_INDEX_FILE": str(idx)}).stdout.strip()
        g("read-tree", snap); sh = (repo / "tools" / "track.sh").read_text().replace("check_docs() {", "check_docs() { echo the rows of T; exit 1\n", 1)
        g("update-index", "--cacheinfo", f"100755,{g('hash-object', '-w', '--stdin', i=sh)},tools/track.sh"); t2 = g("commit-tree", g("write-tree"), "-p", snap, "-m", "T")
        subprocess.run([str(repo / "tools" / "track.sh"), "gate", "g1", t2], cwd=repo, env={**os.environ, "HD_ROOT": str(root), "T": "t", "NAMES": "", "EVIDENCE": str(root / "evidence" / "g1")}, capture_output=True, text=True)
        s.assertIn("the rows of T", json.loads((root / "state" / "g1" / "gate.json").read_text())["detail"])   # the gate of T runs T's rows, not the live checkout's
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
            hd.cmd_handover(["h1", "Limits:", "none"])
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

    def test_a_seed_row_added_later_applies_at_a_head_not_carried(s):  # spotless joined the server seed rows after contracts were agreed
        s.change("s1", pr=7); s.agreed("s1")
        before = hd.contract("s1")["hash"]
        t = s.root / "fork" / ".worktrees" / "harness" / "tools" / "track.md"
        t.write_text(t.read_text() + "- lint | spotless passes | check: false\n- ok | redefined | check: false\n")
        s.assertEqual(hd.contract("s1")["hash"], before)                       # the file alone: its verdicts stand
        pr = {"number": 7, "branch": "content/s1", "owner": "o", "head": A, "draft": False}
        s.assertEqual(s.state(Fake(**FACTS, prs=None), "s1")["state"], "upstream PR unknown")
        st = s.state(Fake(**FACTS, prs={"u/f": [pr]}), "s1")
        s.assertNotIn("seed rows", st["state"])                                # carried at its head: no new row until it moves
        st = s.state(Fake(**FACTS, prs={"u/f": [{**pr, "head": B}]}), "s1")
        s.assertEqual(st["state"], "contract: seed rows lint added"); st["act"]()   # by id: the file's own ok stands
        con = hd.contract("s1")
        s.assertEqual([r["id"] for r in con["rows"]], ["ok", "j1", "lint"]); s.assertNotEqual(con["hash"], before)
        F = Fake(**FACTS, rows={"false": (1, "nope")})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.assertIn("row lint failed", str(e.exception))

    def test_an_upstream_seed_row_seeds_only_a_change_that_opens_a_pr(s):  # server-world-entities: a local raft gained subject and texts
        s.change("s1", kind="local"); s.agreed("s1")
        t = s.root / "fork" / ".worktrees" / "harness" / "tools" / "track.md"
        t.write_text(t.read_text() + "- subject | feat: subjects | check: false | upstream\n- lint | spotless | check: false\n")
        st = s.state(Fake(**FACTS), "s1")
        s.assertEqual(st["state"], "contract: seed rows lint added"); st["act"]()   # the PR's row is not the local change's
        s.assertNotIn("subject", [r["id"] for r in hd.contract("s1")["rows"]])
        hd.write_contract(hd.cfg(), "s2", "server", "", up=False); hd.write_contract(hd.cfg(), "s3", "server", "")
        s.assertEqual(([r["id"] for r in hd.contract("s2")["rows"]], [r["id"] for r in hd.contract("s3")["rows"]]),
                      (["ok", "j1", "lint"], ["ok", "j1", "subject", "lint"]))

    def test_check_rows_run_before_gate_rows_which_wait_on_them(s):  # a seed spotless appended after ci ran only after a CI round
        s.change("s1"); s.agreed("s1", extra="- ci | fork CI | gate: tools/track.sh gate-ci\n- lint | spotless | check: false\n- late | local | check: true\n")
        F = Fake(**FACTS)
        ch, con = s.ctx(F).changes["s1"], hd.contract("s1")
        s.assertEqual(hd.rows(s.ctx(F), ch, con, A, TA, TA, "", gate=True), ["row lint failed: false"])
        s.assertEqual([c.split()[0] for c in F.ran], ["true", "false", "true"])                      # every check, in file order; no CI round
        F = Fake(**FACTS)
        s.assertEqual(hd.rows(s.ctx(F), ch, {**con, "rows": [r for r in con["rows"] if r["id"] != "lint"]}, A, TA, TA, "", gate=True), [])
        s.assertEqual(F.ran, ["true", "true", "tools/track.sh gate-ci"])     # the gate rows after every check passed

    def test_a_row_whose_files_did_not_change_keeps_its_result(s):  # sweep-17 N5: a one-row tools change re-ran every gate's CI
        s.change("s1"); s.agreed("s1", extra="- ci | fork CI | gate: tools/track.sh gate-ci\n- subj | subject | check: tools/server/text.py subject\n")
        f = {"tools/gate/gate.sh": "1", "tools/server/text.py": "t"}
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: f}})
        ctx = s.ctx(F); ch, con = ctx.changes["s1"], hd.contract("s1"); k1 = ctx.key(ch, "tr", each=True)
        F.f["tools_files"][C] = {**f, "tools/server/text.py": "t2"}; F.f["refs"]["local/harness"] = C
        k2 = s.ctx(F).key(ch, "tr", each=True)
        s.assertEqual((k1["s1/ci"] == k2["s1/ci"], k1["s1/subj"] == k2["s1/subj"]), (True, False))   # a row's key holds that row's files alone
        s.assertNotEqual(ctx.key(ch, "tr"), s.ctx(F).key(ch, "tr"))              # the gate's key moves
        for k in (k1, k2):
            F.ran.clear()
            with mock.patch.dict(os.environ, {"ROWKEYS": json.dumps(k)}):
                s.assertEqual(hd.rows(s.ctx(F), ch, con, A, TA, TA, "", gate=True), [])
        s.assertEqual([c for c in F.ran if c.startswith("tools/")], ["tools/server/text.py subject"])   # only the moved row runs again; CI's result is kept
        F.ran.clear(); hd.rows(s.ctx(F), ch, con, A, TA, TA, "", gate=False)
        s.assertIn("tools/server/text.py subject", F.ran)                        # a hand-over's check rows always run

    def test_a_row_key_holds_the_part_of_gate_sh_it_runs(s):  # sweep-19 N11: a gate.sh edit of one verb re-ran every server CI
        gate = ("#!/usr/bin/env bash\n# gate.sh: verbs\n. build.sh\nprojects() { echo p; }\n"
                "spotless() {  # the check row\n  tree; gradle_check spotless\n}\ntests() { build; gradle_check test; }\n"
                "gradle_check() {\n  projects; docker run x\n}\ngate_ci() {  # CI on gate/<slug>; tests and spotless are not its\n  git push fork gate/$slug; read_runs\n}\n"
                "read_runs() {\n  python3 -c '\nimport json\nprint(1)\n'\n}\n"
                "case $verb in gate|gate-ci) \"${verb//-/_}\" ;; test) arg= tests ;; spotless) spotless ;; esac\n")
        s.change("s1"); s.agreed("s1", extra="- ci | fork CI | gate: tools/track.sh gate-ci\n- lint | spotless | check: tools/track.sh spotless\n- t | tests | gate: tools/track.sh test\n- subj | subject | check: tools/server/text.py subject\n")
        f = {"tools/gate/gate.sh": gate, "tools/build/build.sh": "build() { :; }\n", "tools/server/text.py": "t"}
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "local/harness": B}, "tools_files": {B: f}})
        ch = s.ctx(F).changes["s1"]
        def keys(g):
            F.f["tools_files"][C] = {**f, **g}; F.f["refs"]["local/harness"] = C
            return s.ctx(F).key(ch, "tr", each=True)
        k0 = keys({}); moved = lambda g: sorted(r.split("/")[1] for r, k in keys(g).items() if k != k0[r])
        s.assertEqual(moved({"tools/gate/gate.sh": gate.replace("projects; docker", "projects; docker --rm")}), ["lint", "t"])   # one verb's code: its rows alone, CI's kept
        s.assertEqual(moved({"tools/gate/gate.sh": gate.replace("print(1)", "print(2)")}), ["ci"])                            # CI's code (its python, at column 0): CI alone
        s.assertEqual(moved({"tools/gate/gate.sh": gate.replace("# gate.sh: verbs", "# gate.sh: the verbs")}), [])            # a comment moves none
        s.assertEqual(moved({"tools/gate/gate.sh": gate.replace(". build.sh", ". ../build/build.sh")}), ["ci", "lint", "t"])   # the shared code: every verb's row
        s.assertEqual(moved({"tools/build/build.sh": "build() { echo; }\n"}), ["ci", "j1", "lint", "ok", "subj", "t"])                    # the build: every row
        s.assertEqual(moved({"tools/server/text.py": "t2"}), ["subj"])
        s.assertNotEqual(s.ctx(F).key(ch, "tr"), (lambda: (keys({"tools/gate/gate.sh": gate + "\n"}), s.ctx(F).key(ch, "tr"))[1])())   # the gate's own key: the whole of tools/gate/

    def test_the_live_branch_s_gate_keeps_the_member_s_row_results(s):  # sweep-21: the base's gate overwrote a member's row-gate-tests.json
        s.change("s1"); s.agreed("s1", extra="- t | tests | gate: tools/track.sh test\n")
        F = Fake(**FACTS); ch, con = s.ctx(F).changes["s1"], hd.contract("s1")
        for k in ("member", "base", "member"):
            F.ran.clear()
            with mock.patch.dict(os.environ, {"ROWKEYS": json.dumps({"s1/t": k, "s1/ok": k})}):
                hd.rows(s.ctx(F), ch, con, A, TA, TA, "", gate=True)
            ran = [c for c in F.ran if c.startswith("tools/")]
        s.assertEqual(ran, [])                                                 # the member's gate again: its kept result, unrun

    def test_a_row_held_by_its_source_records_no_result(s):  # openrs2's HTTP 500 and GitHub's quota failed heads they never touched
        s.change("s1"); s.agreed("s1", extra="- ci | fork CI | gate: tools/track.sh gate-ci\n")
        F = Fake(**FACTS, rows={"tools/track.sh gate-ci": (hd.HELD, "CI failed at 'Set up Gradle' in 3 attempts: no result")})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_rows(["s1", A, ""])
        s.assertEqual(e.exception.code, hd.HELD)                               # the gate script records nothing: hd starts it again
        F.f["rows"]["true"] = (1, "nope")
        s.agreed("s1", extra="- ci | fork CI | gate: tools/track.sh gate-ci\n- bad | fails | gate: true\n")
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_rows(["s1", A, ""])
        s.assertEqual(e.exception.code, 1)                                     # a row that failed outright is the head's

    def test_handover_refused_on_failing_script_row(s):
        s.change("s1"); s.agreed("s1", extra="- bad | fails | check: false\n")
        F = Fake(**FACTS, rows={"false": (1, "nope")})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.assertIn("row bad failed", str(e.exception))
        s.assertIsNone(hd.rec("s1", "handover"))

    def test_answer_waives_a_script_row(s):
        s.change("s1"); s.agreed("s1", extra="- bad | fails | check: false\n")
        with s.assertRaises(SystemExit):
            hd.cmd_answer(["s1", "--waive", "j1", "not a script row"])
        hd.cmd_answer(["s1", "--waive", "bad", "no new tests, per decision 7"])
        F = Fake(**FACTS, rows={"false": (1, "nope")})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.assertEqual(F.ran, ["true"])
        s.assertEqual(hd.rec("s1", "handover")["head"], A)

    def test_handover_reads_pushed_ref_takes_no_sha(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.assertEqual(hd.rec("s1", "handover")["head"], A)
        s.assertEqual(hd.rec("s1", "handover")["T"], TA)
        s.assertEqual(F.ran, ["true"])
        with mock.patch.object(hd, "Facts", lambda: Fake(**{**FACTS, "refs": {"origin/HEAD": B}})), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["s1", "Limits:", "none"])
        s.assertIn("does not exist", str(e.exception))

    def test_harness_dev_ref_stays_local(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})  # no remote ref at all
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual(hd.rec("h1", "handover")["head"], A)
        s.assertEqual(hd.TRACK["harness"]["dev"], "harness/{slug}")                 # the local branch, so a rebase needs no force push
        repo = Path(__file__).parent.parent
        for doc in ("tools/track.md", ".claude/agents/dev.md"):
            s.assertIn("never push it", (repo / doc).read_text().replace("\n", " "), doc)

    def test_a_limit_is_fixed_in_its_scope_and_filed_once_per_mechanism(s):
        s.change("h1", track="harness", mechanism="dispatch"); s.agreed("h1", track="harness")
        (s.root / "evidence" / "h1" / "proof.md").write_text("ok")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})
        with s.assertRaises(SystemExit) as e:                                     # a limit in the mechanism it touched: fixed here
            hd.cmd_new(["x1", "--track", "harness", "--title", "dispatch drops a run", "--mechanism", "dispatch", "--limit-of", "h1"])
        s.assertIn("fix it there", str(e.exception)); s.assertNotIn("x1", hd.defs("changes"))
        s.change("h2", track="harness", mechanism="carry")                       # an open change on the other mechanism
        hd.cmd_new(["x2", "--track", "harness", "--title", "carry retries", "--body", "seen twice", "--mechanism", "carry", "--limit-of", "h1"])
        g = hd.defs("changes")
        s.assertNotIn("x2", g); s.assertEqual(g["h2"]["limit-of"], ["h1"]); s.assertIn("carry retries", g["h2"]["body"])
        s.assertEqual(g["h1"]["deps"], ["h2"])                                   # the finder waits on the change that carries its limit
        s.change("h5", track="harness", mechanism="tree"); s.agreed("h5", track="harness")
        hd.cmd_new(["x5", "--track", "harness", "--title", "build host faults", "--mechanism", "hold", "--limit-of", "h5"])
        s.assertEqual(hd.defs("changes")["h5"]["deps"], ["x5"])                  # a new filing holds its finder too
        with s.assertRaises(SystemExit):                                         # converges: h2 now owns h1's mechanism too
            hd.cmd_new(["x3", "--track", "harness", "--title", "back again", "--mechanism", "dispatch", "--limit-of", "h2"])
        s.change("x4", track="harness", mechanism="dispatch")
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["h1", "Limits:", "limit:x4"])                       # a hand-back naming an in-scope limit
        s.assertIn("in this change's scope", str(e.exception)); s.assertIsNone(hd.rec("h1", "handover"))
        for bad, says in ((["done"], "no Limits: section"), (["Limits:"], "no Limits: section"),
                          (["Limits:", "limit:h2", "dispatch", "still", "drops", "a", "run"], "is no `limit:<slug>`")):
            with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
                hd.cmd_handover(["h1", *bad])                                    # no section, or a limit stated in prose: refused
            s.assertIn(says, str(e.exception)); s.assertIsNone(hd.rec("h1", "handover"))
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "fixed", "Limits:", "limit:h2"])
        s.assertEqual(hd.rec("h1", "handover")["head"], A)

    def test_a_superseded_change_ends_its_started_run(s):
        s.change("h1", track="harness", mechanism="hold")
        hd.save_run({"name": "h1-2", "change": "h1", "role": "dev", "input": "", "started": hd.now(), "console_pid": 7, "console_start": "1"})
        hd.cmd_new(["r1", "--track", "harness", "--title", "one rewrite", "--mechanism", "hold", "--supersedes", "h1"])
        hd.tick(s.ctx(Fake(refs={"HEAD": B}, trees={B: TB})))
        r = next(r for r in hd.runs() if r["name"] == "h1-2")
        s.assertEqual((bool(r["ended"]), r["reason"]), (True, "change superseded by r1"))   # held with no runs, a started one too

    def test_planner_merges_changes_on_one_mechanism(s):
        s.change("h1", track="harness"); s.change("h2", track="harness"); s.change("s1")
        with s.assertRaises(SystemExit):
            hd.cmd_new(["r1", "--track", "harness", "--title", "x", "--mechanism", "hold", "--supersedes", "h1,s1"])   # only open harness changes
        hd.cmd_new(["r1", "--track", "harness", "--title", "one rewrite", "--mechanism", "hold", "--supersedes", "h1,h2"])
        g = hd.defs("changes")
        s.assertEqual((g["h1"]["superseded"], g["h2"]["superseded"], g["r1"]["mechanism"]), ("r1", "r1", "hold"))
        s.assertNotIn("closed", g["h1"])                                        # closing is the user's word: held with no runs
        s.assertEqual(s.state(Fake(refs={"HEAD": B}, trees={B: TB}), "h1"), {"state": "superseded by r1: the user's hd close", "actor": "wait"})
        hd.cmd_new(["p9", "--track", "harness", "--title", "hold drops a run", "--mechanism", "hold"])   # a later issue on it joins it
        g = hd.defs("changes")
        s.assertNotIn("p9", g); s.assertIn("hold drops a run", g["r1"]["body"])
        s.assertIn("filed by p9: hold drops a run", (s.root / "evidence" / "r1" / "contract.md").read_text())   # an answer row: scope r1's next hand-over takes
        for bad in ([], ["--mechanism", "r1"]):                                 # a harness filing names one of hd.yaml's mechanisms
            with s.assertRaises(SystemExit) as e:
                hd.cmd_new(["p8", "--track", "harness", "--title", "y", *bad])
            s.assertIn("one of: loop, runs", str(e.exception)); s.assertNotIn("p8", hd.defs("changes"))
        hd.cmd_new(["p7", "--track", "harness", "--title", "after r1", "--mechanism", "hold", "--deps", "r1"])     # a dependency orders it: its own change
        hd.cmd_new(["p6", "--track", "harness", "--title", "before r1", "--mechanism", "hold", "--blocks", "r1"])
        g = hd.defs("changes")
        s.assertEqual((g["p7"]["deps"], g["r1"]["deps"]), (["r1"], ["p6"]))
        alerts = hd.tick(s.ctx(Fake(refs={"HEAD": B}, trees={B: TB})), act=False)["alert"]   # one chain p6 <- r1 <- p7: no merge
        s.assertFalse([a for a in alerts if a.startswith("mechanism hold")], alerts)
        s.change("h3", track="harness", mechanism="hold"); s.change("h4", track="harness", mechanism="")
        alerts = hd.tick(s.ctx(Fake(refs={"HEAD": B}, trees={B: TB})), act=False)["alert"]   # one no dependency orders on the mechanism, one naming none
        s.assertIn("mechanism hold: 4 open changes h3, p6, p7, r1: merge them into one root-cause change", alerts)
        s.assertIn("no mechanism: h4: name each one's", alerts)
        hd.cmd_new(["s9", "--track", "server", "--title", "a quest"])           # a product change needs none
        s.assertEqual(hd.mechanism(hd.defs("changes")["s9"]), "s9")
        repo = Path(__file__).parent.parent
        for role in ("orchestrator", "planner", "dev"):
            s.assertIn("--mechanism <m>", (repo / ".claude" / "agents" / f"{role}.md").read_text(), role)
        live = hd.yaml.safe_load((repo / "hd.yaml").read_text())["mechanisms"]
        for f in (repo / "harness" / "changes").glob("*.md"):                   # every open harness definition names one
            m, _ = hd._frontmatter(f.read_text())
            if m["track"] == "harness" and not m.get("closed") and m.get("mechanism"):
                s.assertIn(m["mechanism"], live, f.name)
        for role in ("dev", "qa", "planner"):
            s.assertIn("root cause", (Path(__file__).parent.parent / ".claude" / "agents" / f"{role}.md").read_text(), role)

    def test_answer_a_verdict_judged_makes_no_dev_run(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        with mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_answer(["s1", "Fix first: the body names both commits"])
        s.assertEqual(s.state(F, "s1")["state"], "dev run due: the user answered after the hand-over (answer-1)")
        with mock.patch.object(hd, "now", lambda: "3000-01-01T00:00:00Z"):
            s.verdict("s1", A, {"ok": "pass", "j1": "pass", "answer-1": "pass"}, F)   # qa judged the answer on this head: no dev run for it
        s.assertEqual(s.state(F, "s1")["state"], "gated; waiting for the user's yes")

    def test_answer_on_done_change_reopens_it_and_on_closed_is_refused(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": A, "harness/h1": A}, trees={A: TA}, merges={(A, A): ("ok", A)})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual(s.state(F, "h1")["state"], "done")
        hd.put("h1", "swept", {"head": A})
        with mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_answer(["h1", "Fix first: also cover the closed case"])
        s.assertEqual(s.state(F, "h1")["state"], "dev run due: the user answered after the hand-over (answer-1)")
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "now", lambda: "3000-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual((s.state(F, "h1")["state"], hd.rec("h1", "swept")), ("done", None))   # its new branches are swept again
        hd.cmd_close(["h1", "dropped"])
        with s.assertRaises(SystemExit) as e:
            hd.cmd_answer(["h1", "one more"])
        s.assertIn("closed: file a change", str(e.exception))

    def test_answer_after_handover_makes_a_dev_run(s):
        s.change("h1", track="harness"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertTrue(s.state(F, "h1")["state"].startswith("gate on"))
        hd.put("h1", "handover", {**hd.rec("h1", "handover"), "ts": "2000-01-01T00:00:00Z"})   # handed over before the answer
        hd.cmd_answer(["h1", "Fix first: reuse the gradle volume"])
        s.assertEqual(s.state(F, "h1")["state"], "dev run due: the user answered after the hand-over (answer-1)")
        hd.tick(s.ctx(F))
        run = [r for r in hd.runs() if r["change"] == "h1"][0]
        s.assertEqual(run["role"], "dev")
        s.assertIn("Fix first: reuse the gradle volume", (s.root / "state" / "briefs" / f"{run['name']}.md").read_text())
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])                                                          # the dev's new hand-over releases the head
        s.assertTrue(s.state(F, "h1")["state"].startswith("gate on"))

    def test_a_filing_joined_after_the_handover_keeps_its_gate(s):  # sweep-15 B1: a join read as the user's word dropped a passing gate
        s.change("h1", track="harness", mechanism="hold"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "now", lambda: "2000-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])
        hd.cmd_new(["p9", "--track", "harness", "--title", "hold drops a run", "--mechanism", "hold"])
        s.assertIn("filed by p9: hold drops a run", hd.contract("h1")["text"])
        s.assertFalse(any(e.get("record") == "answer" for e in hd.evs(b'"record": "answer"')))   # no run's record is outdated by it
        s.assertTrue(s.state(F, "h1")["state"].startswith("gate on"))           # the handed-over head is still gated and shipped
        D = Fake(refs={"HEAD": A, "harness/h1": A}, trees={A: TA}, merges={(A, A): ("ok", A)})
        s.assertEqual(s.state(D, "h1")["state"], "dev run due: a filing or finding joined after the hand-over (answer-1)")   # its scope, on top
        with mock.patch.object(hd, "Facts", lambda: D), mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual(s.state(D, "h1")["state"], "done")

    def test_a_filing_joined_during_the_run_is_late_for_its_handover(s):  # sweep-19 N10: lateness from the run's brief, not its hand-over
        s.change("h1", track="harness", mechanism="hold"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})
        with mock.patch.object(hd, "now", lambda: "2000-01-01T00:00:00Z"):
            hd.tick(s.ctx(F))
        r = [r for r in hd.runs() if r["change"] == "h1"][0]
        r.update(started="2000-01-01T00:00:00Z"); hd.save_run(r)               # the run reads its brief
        hd.cmd_new(["p9", "--track", "harness", "--title", "hold drops a run", "--mechanism", "hold"])   # joined while it runs
        s.assertNotIn("filed by p9", (s.root / "state" / "briefs" / f"{r['name']}.md").read_text())
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])                          # handed over after the join, without it
        D = Fake(refs={"HEAD": A, "harness/h1": A}, trees={A: TA}, merges={(A, A): ("ok", A)})   # its head, done
        s.assertEqual(hd.rec("h1", "handover")["given"], "2000-01-01T00:00:00Z")
        s.assertEqual(s.state(D, "h1")["state"], "dev run due: a filing or finding joined after the hand-over (answer-1)")
        s.assertTrue(any(e.get("action") == "joined" and e.get("by") == "p9" for e in hd.evs(b'"action": "joined"')))   # a plain filing, not a limit

    def test_a_filing_the_running_dev_was_told_is_not_late(s):  # sweep-25 P2-a: the orchestrator's relay counts as taken
        s.change("h1", track="harness", mechanism="hold"); s.agreed("h1", track="harness")
        F = Fake(refs={"HEAD": B, "harness/h1": A}, trees={A: TA, B: TB}, merges={(B, A): ("ok", A)})
        with mock.patch.object(hd, "now", lambda: "2000-01-01T00:00:00Z"):
            hd.tick(s.ctx(F))
        r = [r for r in hd.runs() if r["change"] == "h1"][0]
        hook.bind(payload(r, "ag1", "SubagentStart", s.root))
        hd.cmd_new(["p9", "--track", "harness", "--title", "hold drops a run", "--mechanism", "hold"])   # joined while it runs
        hook.told({"hook_event_name": "PostToolUse", "tool_name": "SendMessage", "tool_input": {"to": "nobody"}})   # no run's agent: nothing
        s.assertNotIn("told", hd.runs()[0])
        with mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:00Z"):
            hook.told({"hook_event_name": "PostToolUse", "tool_name": "SendMessage", "tool_input": {"to": "ag1", "message": "answer-1: hold drops a run"}})
        with mock.patch.object(hd, "Facts", lambda: F), mock.patch.object(hd, "now", lambda: "2999-01-01T00:00:01Z"):
            hd.cmd_handover(["h1", "Limits:", "none"])
        s.assertEqual(hd.rec("h1", "handover")["given"], "2999-01-01T00:00:00Z")
        D = Fake(refs={"HEAD": A, "harness/h1": A}, trees={A: TA}, merges={(A, A): ("ok", A)})   # its head, done: the filing was its
        s.assertEqual(s.state(D, "h1")["state"], "done")

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
        hd.save_run({"name": "s1-4", "change": "s1", "role": "qa", "input": "", "started": hd.now()})   # the qa run judging
        hd.save_run({"name": "s1-3", "change": "s1", "role": "qa", "input": "", "started": hd.now(), "ended": hd.now()})
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        v = hd.verdicts("s1")
        s.assertEqual([x["rows"]["j1"] for x in v], ["fail: wrong", "pass"])
        s.assertEqual([x["run"] for x in v], ["", "s1-4"])                     # the verdict names its started, unended qa run

    def test_text_only_fix_keeps_verdict_valid(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.approve(F, "s1", A)
        s.assertEqual(s.state(F, "s1")["state"], "carrying upstream")
        (s.root / "evidence" / "s1" / "pr-body.md").write_text("fixed body")  # qa fixed the text in place: the verdict holds, the yes does not
        s.assertEqual(s.state(F, "s1")["state"], "gated; waiting for the user's yes")

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
        s.assertEqual(s.state(F, "s1")["state"], "gated; waiting for the user's yes")
        with mock.patch.object(hd, "Facts", lambda: F):
            hd.cmd_answer(["s1", "also do X"])  # the user's word after the hand-over is the dev's first
        s.assertEqual(s.state(F, "s1")["state"], "dev run due: the user answered after the hand-over (answer-1)")
        F2 = Fake(**{**FACTS, "refs": {**FACTS["refs"], "fork/dev/s1": C}})
        s.assertTrue(s.state(F2, "s1")["state"].startswith("dev run due: head ccccccccc"))  # the head moved: the hand-over is stale

    def test_rule_file_move_rejudges_rule_rows_only(s):
        s.change("s1"); s.agreed("s1")
        p = s.root / "evidence" / "s1" / "contract.md"
        p.write_text(p.read_text().replace("rules: ", "rules: AGENTS.md=b1"))
        F = Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): "b1"})
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["state"], "gated; waiting for the user's yes")
        F2 = Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): "b2"})
        st = s.state(F2, "s1")
        s.assertEqual((st["actor"], st["input"][2]), ("qa", ["AGENTS.md"]))
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F2)  # re-judged against b2
        s.assertEqual(s.state(F2, "s1")["state"], "gated; waiting for the user's yes")
        s.assertEqual(s.state(Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): None}), "s1")["actor"], "unknown")

    def test_a_rule_file_absent_upstream_moves_nothing(s):  # central-token-login-op-8: 'absent' in the header, '' from blob()
        s.change("s1"); s.agreed("s1")
        p = s.root / "evidence" / "s1" / "contract.md"
        p.write_text(p.read_text().replace("rules: ", f"rules: AGENTS.md=absent README.md=r1 base={B}"))
        F = Fake(**FACTS, blobs={("origin/HEAD", "AGENTS.md"): "", ("origin/HEAD", "README.md"): "r1", ("origin/HEAD", "base"): ""})
        s.gated("s1", F)
        s.assertEqual(s.state(F, "s1")["state"], "review due")                   # no verdict yet: a review, no rule moved
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        s.assertEqual(s.state(F, "s1")["state"], "gated; waiting for the user's yes")

    def test_a_seeded_check_row_keeps_the_verdict(s):
        s.change("s1"); s.agreed("s1")
        F = Fake(**FACTS)
        s.gated("s1", F)
        s.verdict("s1", A, {"ok": "pass", "j1": "pass"}, F)
        hd.add_seeds("s1", ["- spotless | formatted | check: tools/track.sh check-spotless"])   # a seed check row added later: gated, never judged
        s.assertEqual(hd.judged("s1", A, hd.contract("s1"))[-1]["rows"]["j1"], "pass")
        hd.add_seeds("s1", ["- j2 | another judged row | judge: qa-server"])           # a judged row added: judged again
        s.assertEqual(hd.judged("s1", A, hd.contract("s1")), [])

    def test_no_reviewer_without_judge_rows_and_no_arbitrary_check(s):
        s.change("c1", "client"); s.agreed("c1", "client", extra="- evil | injected | check: rm -rf /\n")
        (s.root / "evidence" / "c1" / "x.txt").write_text("evidence")
        F = Fake(**{**FACTS, "refs": {**FACTS["refs"], "origin/client/c1": A}})
        with mock.patch.object(hd, "Facts", lambda: F), s.assertRaises(SystemExit) as e:
            hd.cmd_handover(["c1", "Limits:", "none"])
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
