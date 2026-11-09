"""Features (A1, G4): a change is our work, a feature is the user's PR; one package per repo, one card per feature."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import decide  # noqa: E402
import publish  # noqa: E402
import store  # noqa: E402
from decide import Cfg, Change, Track  # noqa: E402

FORK = Track("fork", "x/s", "/nowhere", "refs/remotes/origin/main", "Up/s", "dev", {"build": "s-1", "gate": "s-1", "deploy": "s-1"}, "fork")
CEN = Track("central", "x/c", "/nowhere", "refs/remotes/origin/main", "Up/c", "dev", {"gate": "c-1"}, "fork")
HAR = Track("harness", "x/h", "/nowhere", "refs/heads/main", "", "harness", {"gate": "h-1"})
CFG = Cfg(agents=9, tracks={"fork": FORK, "central": CEN, "harness": HAR})
FEAT = "content/friends"
PF, PC = "pr-content-friends-fork", "pr-content-friends-central"


class Feature(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = store.connect(str(Path(self.dir.name) / "hd.db"))
        self.L = store.Ledger(self.db)
        self.members = [Change("s-b", "fork", deps=("s-a",), feature=FEAT, priority="P3"), Change("s-a", "fork", feature=FEAT),
                        Change("c-a", "central", feature=FEAT, priority="P1")]
        self.n = 0

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def defs(self):
        return self.members + decide.packages(self.members, CFG.tracks)

    def steps(self):
        return {a.change: a.step for a in decide.plan(self.L, self.defs(), CFG)}

    def C(self):
        return decide.Ctx(self.L, CFG, {c.slug: c for c in self.defs()})

    def head(self, slug, repo, sha, at="t1"):
        self.db.execute("INSERT OR REPLACE INTO ref(repo, name, sha) VALUES (?, ?, ?)", (repo, f"refs/remotes/fork/dev/{slug}", sha))
        self.db.execute("INSERT INTO submission(change, head, tree, tcommit, at) VALUES (?, ?, ?, ?, ?)", (slug, sha, "t" + sha, sha, at))

    def live(self, slug, repo, sha):
        self.head(slug, repo, sha)
        for target in ("refs/heads/staging", "live"):
            self.db.execute("INSERT OR REPLACE INTO landed(change, target, sha, at) VALUES (?, ?, 's', 't2')", (slug, target))

    def package(self, slug, repo, sha, recipe):
        """The package's dev ran hd package and hd submit: its head, the members it holds, its gate, its texts."""
        self.head(slug, repo, sha, at="t3")
        self.db.execute("INSERT INTO event(at, kind, change, detail) VALUES ('t3', 'packaged', ?, ?)",
                        (slug, f"{decide.members_digest(self.C(), self.C().defs[slug])} {sha[:7]}"))
        for k in ("build", "gate"):
            self.db.execute("INSERT OR REPLACE INTO job(kind, key, ok, ended_at) VALUES (?, ?, 1, 't')", (k, f"t{sha}:{recipe}"))
        for n in ("pr-title.txt", "pr-body.md", "pr-comment.md"):
            self.db.execute("INSERT OR REPLACE INTO text(change, name, sha, body, at) VALUES (?, ?, ?, ?, '1')", (slug, n, sha, f"{n} text"))

    def card(self):
        C = self.C()
        pkgs = [{"slug": p.slug, "track": p.track, "head": decide.tip(C, p), "pr": decide.pr_of(C, p), "texts": self.L.texts(p.slug)}
                for p in decide.feature_pkgs(C, FEAT)]
        return publish.card(self.db, FEAT, pkgs, CFG.tracks, decide.card_head(C, decide.feature_pkgs(C, FEAT)))

    def test_one_package_per_repo_its_members_in_dependency_order(self):
        p = {x.slug: x for x in decide.packages(self.members, CFG.tracks)}
        self.assertEqual(p[PF].members, ("s-a", "s-b"))
        self.assertEqual((p[PC].members, p[PC].priority, p[PF].priority), (("c-a",), "P1", "P2"))
        self.assertEqual(decide.packages([Change("h", "harness", feature=FEAT), Change("s", "fork")], CFG.tracks), [])   # no upstream, or no feature: no PR

    def test_a_change_carries_no_upstream_work_and_its_package_waits_for_every_member_live(self):
        s = self.steps()
        self.assertEqual((s["s-a"].role, s["s-a"].mode), ("qa", "criteria"))
        self.assertEqual(s[PF].why, "member s-a: criteria before code")
        for m, repo in (("s-a", "fork"), ("s-b", "fork"), ("c-a", "central")):
            self.live(m, repo, m * 8)
        s = self.steps()
        self.assertEqual([s[m].kind for m in ("s-a", "s-b", "c-a")], ["done"] * 3)   # done on staging and live: no texts, no card
        self.assertEqual((s[PF].role, s[PF].mode, s[PF].why), ("dev", "code", "new"))   # the package's dev: hd package, then the texts

    def test_sister_prs_share_one_card_and_one_approval_publishes_both(self):
        for m, repo in (("s-a", "fork"), ("s-b", "fork"), ("c-a", "central")):
            self.live(m, repo, m * 8)
        self.package(PF, "fork", "f" * 40, "s-1")
        self.assertEqual(self.steps()[PF].why, f"sister {PC}: new")   # the fork's PR waits for Central's
        self.package(PC, "central", "e" * 40, "c-1")
        s = self.steps()
        lead = s[PF] if s[PF].kind == "card" else s[PC]
        self.assertEqual(lead.kind, "card")
        self.assertEqual(sorted(x.kind for x in (s[PF], s[PC])), ["card", "wait"])
        cid = self.card()
        c = self.db.execute("SELECT * FROM card WHERE id=?", (cid,)).fetchone()
        steps = json.loads(c["steps_json"])
        self.assertEqual(sorted((x["name"], x["track"]) for x in steps[-4:]), [("comment", "central"), ("comment", "fork"), ("ready", "central"), ("ready", "fork")])
        self.assertEqual({x["name"] for x in steps[:-4]}, {"push", "pr", "ci"})   # every PR open and green before any comment or ready
        self.assertIn(f"approve {FEAT} {c['head'][:7]}", self.db.execute("SELECT detail FROM event WHERE kind='card'").fetchone()[0])
        self.assertIn("the user: card", self.steps()[PF].why + self.steps()[PC].why)
        self.db.execute("INSERT INTO hold(change, at) VALUES ('c-a', 't')")   # the Central upstream hold, a standing hold on a member
        self.assertIn("held", self.steps()[PF].why + self.steps()[PC].why)
        self.db.execute("UPDATE hold SET lifted_at='t'")
        self.db.execute("INSERT INTO approval(card, at) VALUES (?, 't')", (cid,))
        s = self.steps()
        self.assertEqual([(x.kind, x.key) for x in s.values() if x.kind == "publish"], [("publish", str(cid))])   # one publish for both PRs
        self.db.execute("UPDATE publish_step SET done_at='t'")
        self.db.execute("UPDATE approval SET spent_at='t', spent_why='published'")
        self.assertEqual({self.steps()[p].why for p in (PF, PC)}, {"maintainers"})
        pr = {"number": 7, "state": "open", "draft": False, "head": {"sha": "f" * 40}, "title": "t", "body": "b", "merged_at": None}
        self.db.execute("INSERT INTO gh(url, body) VALUES (?, ?)", (store.pulls_on("Up/s", FEAT), json.dumps([pr])))
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES (?, 'refs/remotes/origin/main', 'm', 't4')", (PC,))   # Central's PR merged first: no new card
        self.assertEqual((self.steps()[PC].kind, self.steps()[PF].why), ("done", "maintainers"))

    def test_a_member_added_after_the_publish_repackages_with_one_comment(self):
        self.members = self.members[:2]
        for m in ("s-a", "s-b"):
            self.live(m, "fork", m * 8)
        self.package(PF, "fork", "f" * 40, "s-1")
        cid = self.card()
        self.db.execute("INSERT INTO approval(card, at, spent_at, spent_why) VALUES (?, 't', 't', 'published')", (cid,))
        self.db.execute("UPDATE publish_step SET done_at='t'")
        pr = {"number": 9, "state": "open", "draft": False, "head": {"sha": "f" * 40}, "title": "pr-title.txt text",
              "body": "pr-body.md text", "merged_at": None}
        self.db.execute("INSERT INTO gh(url, body) VALUES (?, ?)", (store.pulls_on("Up/s", FEAT), json.dumps([pr])))
        self.assertEqual(self.steps()[PF].why, "maintainers")
        self.members.append(Change("s-fix", "fork", feature=FEAT))   # a maintainer's finding, filed with the feature
        self.assertIn("member s-fix", self.steps()[PF].why)
        self.live("s-fix", "fork", "9" * 40)
        s = self.steps()[PF]
        self.assertEqual((s.role, s.kind), ("dev", "run"))
        self.assertIn("members moved since the package", s.why)
        self.package(PF, "fork", "d" * 40, "s-1")
        self.assertEqual(self.steps()[PF].kind, "card")
        c = self.db.execute("SELECT * FROM card WHERE id=?", (self.card(),)).fetchone()
        self.assertEqual([x["name"] for x in json.loads(c["steps_json"])], ["push", "ci", "comment"])   # the open PR: a new head, one comment
        self.assertEqual(c["pr"], 9)

    def test_a_member_on_a_fork_only_change_reaches_no_pr(self):   # G4 per PR: no commit of another PR, nor a fork-only one
        self.members = [Change("s-a", "fork", feature=FEAT, deps=("s-local",)), Change("s-local", "fork"), Change("s-o", "fork", feature="content/other")]
        for m in ("s-a", "s-local"):
            self.live(m, "fork", m * 8)
        self.assertIn("s-local, which names no feature", self.steps()[PF].why)
        self.members[0] = Change("s-a", "fork", feature=FEAT, deps=("s-o",))
        self.live("s-o", "fork", "o" * 40)
        self.assertIn("s-o of content/other, not yet merged upstream", self.steps()[PF].why)
        self.db.execute("INSERT INTO landed(change, target, sha, at) VALUES ('pr-content-other-fork', 'refs/remotes/origin/main', 'm', 't4')")
        self.assertEqual(self.steps()[PF].why, "new")

    def test_kpi_reports_runs_and_cards_per_feature(self):
        import kpi
        for slug in ("s-a", PF, "other"):
            self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES (?, 'dev', 'code', 'i', 'b', 't')", (slug,))
        self.db.execute("INSERT INTO card(change, head, steps_json, texts_json, digest) VALUES (?, 'h', '[]', '{}', 'd')", (FEAT,))
        self.assertEqual(kpi.feature_rows(self.db, self.defs()), [f"feature {FEAT}: 2 runs over 5 changes and packages, 1 cards"])

    def test_the_package_candidate_is_on_upstream_main_alone(self):   # its CI on upstream main, never staging (G4)
        p = decide.packages(self.members, CFG.tracks)
        self.assertEqual({FORK.candidate_base(x) for x in p}, {FORK.base})
        self.assertEqual(FORK.candidate_base(self.members[0]), decide.STAGING)
        self.assertEqual(FORK.done_ref(p[0]), FORK.base)


if __name__ == "__main__":
    unittest.main()
