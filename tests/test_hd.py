"""One class per requirement (docs/PRD.md, Acceptance), driven against a dict-backed Fake of Facts in a sandbox root."""
import json, os, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock

os.environ["HD_ROOT"] = tempfile.mkdtemp()
import hd  # noqa: E402  (reads HD_ROOT at import)

A, B, C, D = "a" * 40, "b" * 40, "c" * 40, "d" * 40
TA, TB, TC = "ta" * 20, "tb" * 20, "tc" * 20


class Fake(hd.Facts):
    """Facts from dicts: refs {ref: sha}, anc {(tip, sha)}, trees {commit: tree}, merges {(base, head): result},
    blobs {(ref, path): sha}, rows {cmd: (rc, out)}, unknown {remote}. Records spawns and row runs."""

    def __init__(s, **f):
        super().__init__()
        s.f, s.spawned, s.ran = f, [], []

    def fetch(s, clone, remote): return remote not in s.f.get("unknown", ())
    def rev(s, clone, ref): return None if ref.split("/")[0] in s.f.get("unknown", ()) else s.f.get("refs", {}).get(ref, "")
    def contains(s, clone, tip, sha):
        if tip is None: return None
        return bool(tip and sha) and (tip == sha or (tip, sha) in s.f.get("anc", set()))
    def tree(s, clone, commit): return s.f.get("trees", {}).get(commit)
    def merge(s, clone, base, head, msg): return s.f.get("merges", {}).get((base, head), ("ok", head))
    def blob(s, clone, ref, path): return s.f.get("blobs", {}).get((ref, path), "")
    def proc_start(s, pid): return "1"
    def alive(s, pid, start): return (pid, start) in s.f.get("procs", set())
    def spawn(s, args, log, env=None): s.spawned.append(args); return 4242, "99"
    def run(s, cmd, cwd, env): s.ran.append(cmd); return s.f.get("rows", {}).get(cmd, (0, ""))
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
            (p / "tools" / "track.md").write_text(f"# {track}\n\n## Seed rows\n- ok | always passes | check: true\n- j1 | a judged row | judge: qa-{track}\n")
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
