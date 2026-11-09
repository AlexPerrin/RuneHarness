"""The card and the publish (docs/ARCHITECTURE.md §7).

The card is the recorded list of acts and exact texts the user approves: one per feature, covering its sister PRs.
The publish executes publish_step rows in order, skipping those done, with the card's texts, never anything re-read
from the live PR or evidence/.
"""
import json
import subprocess

import observe
import store
from store import OWNER, event, now


def answered(db, upstream: str, number: int) -> set:
    """Ids (REST id and node id) of others' comments on the PR older than our latest comment there: answered already.
    Read from the gh rows observe.pr keeps for the PR's issue and review comments."""
    cs = []
    for url in (f"repos/{upstream}/issues/{number}/comments", f"repos/{upstream}/pulls/{number}/comments"):
        row = db.execute("SELECT body FROM gh WHERE url=?", (url,)).fetchone()
        cs += json.loads(row["body"]) if row and row["body"] else []
    last = max((c["created_at"] for c in cs if c["user"]["login"] == OWNER), default="")
    return {str(x) for c in cs if c["user"]["login"] != OWNER and c["created_at"] < last for x in (c["id"], c.get("node_id"))}


def card(db, feature: str, pkgs: list, tracks: dict, head: str, refusal: str = "") -> int:
    """One card for the feature's packages (sister PRs, one per repo), each pkg {slug, track, head, pr, texts}: per
    package push (unless its PR is at its head) → pr (open a draft) | edit (title or body differ) → ci (if pushed or
    draft); then each package's comment (pr-comment.md, then each pr-reply-<id>.md not yet answered) and ready (if new
    or draft). INSERT OR IGNORE the card and its publish_step rows; returns the card id."""
    steps, t, tail = [], {}, []
    for p in pkgs:
        T, pr, texts, k = tracks[p["track"]], p["pr"], p["texts"], {"track": p["track"], "slug": p["slug"]}
        x = {"title": texts.get("pr-title.txt", "").strip(), "body": texts.get("pr-body.md", ""), "comment": texts.get("pr-comment.md", "").strip()}
        done = answered(db, T.upstream, pr["number"]) if pr else set()
        replies = sorted(n for n in texts if n.startswith("pr-reply-") and n[9:-3] not in done)   # a finding we already answered gets no second reply
        if replies:
            x["comment"] += "\n\n" + "\n\n".join(texts[n].strip() for n in replies)
        t[p["slug"]] = x
        pushed = not pr or pr["head"] != p["head"]
        if pushed:
            steps.append({"name": "push", "head": p["head"], "branch": feature, **k})
        if not pr:
            steps.append({"name": "pr", "branch": feature, **k})
        elif (x["title"] and x["title"] != pr["title"]) or (x["body"].strip() and x["body"].strip() != (pr["body"] or "").strip()):
            steps.append({"name": "edit", "pr": pr["number"], **k})
        if pushed or not pr or pr["draft"]:
            steps.append({"name": "ci", "head": p["head"], **k})
        if x["comment"]:
            tail.append({"name": "comment", "findings": [n[9:-3] for n in replies], "pr": pr and pr["number"], **k})
        if not pr or pr["draft"]:
            tail.append({"name": "ready", "pr": pr and pr["number"], **k})
    steps += tail   # every PR exists and its CI is green before any comment or ready: sister PRs go out together
    if refusal:
        t["refusal"] = refusal   # a new card names what GitHub refused last time
    digest = store.digest(steps, t)
    row = db.execute("SELECT id FROM card WHERE change=? AND head=? AND digest=?", (feature, head, digest)).fetchone()
    if row:
        db.execute("UPDATE card SET shown_at=? WHERE id=?", (now(), row["id"]))   # the same card, re-shown after moved texts
        return row["id"]
    one = pkgs[0]["pr"] if len(pkgs) == 1 else None
    cid = db.execute("INSERT INTO card(change, head, pr, steps_json, texts_json, digest, shown_at) VALUES (?,?,?,?,?,?,?)",
                     (feature, head, one and one["number"], json.dumps(steps), json.dumps(t), digest, now())).lastrowid
    for n, s in enumerate(steps, 1):
        db.execute("INSERT INTO publish_step(card, n, name) VALUES (?,?,?)", (cid, n, s["name"]))
    event(db, "card", feature, None, render(db, db.execute("SELECT * FROM card WHERE id=?", (cid,)).fetchone(), tracks))
    return cid


def render(db, c, tracks) -> str:
    """The card as `hd` prints it: each act in order with its repo, each exact text, each package's verdict and
    evidence, the commands."""
    steps, t = json.loads(c["steps_json"]), json.loads(c["texts_json"])
    first, prs = {}, {s["slug"]: s["pr"] for s in steps if s.get("pr")}
    for s in steps:
        first.setdefault(s["slug"], s)
    targets = [tracks[s["track"]].upstream + (f"#{prs[slug]}" if slug in prs else " (new PR)") for slug, s in first.items()]
    out = [f"{c['change']} @{c['head'][:7]}  " + ", ".join(targets)
           + (f"   (the last publish was refused: {t['refusal']})" if t.get("refusal") else "")]
    for n, s in enumerate(steps, 1):
        x = t[s["slug"]]
        line = {"push": lambda: f"push {s['head'][:7]} → fork {s['branch']}",
                "pr": lambda: f"open draft PR {s['branch']} → main   ── title ──  {x['title']}\n── body ──\n{x['body'].rstrip()}",
                "edit": lambda: f"edit title/body   ── title ──  {x['title']}\n── body ──\n{x['body'].rstrip()}",
                "ci": lambda: f"CI at {s['head'][:7]}",
                "comment": lambda: f"comment   ── text ──\n{x['comment']}",
                "ready": lambda: "ready for review"}[s["name"]]()
        out.append(f"  {n} {tracks[s['track']].upstream}: {line}")
    for slug in first:
        v = db.execute("SELECT * FROM verdict WHERE change=? ORDER BY id DESC LIMIT 1", (slug,)).fetchone()
        out.append(f"  {slug}: verdict {'PASS' if v and v['ok'] else 'FAIL' if v else 'none (no judged criteria)'}"
                   f"{' (run ' + str(v['run']) + ')' if v else ''}   evidence/{slug}/")
    out.append(f"  yes: ! python3 harness/hd.py approve {c['change']} {c['head'][:7]}   no: hd hold {c['change']} \"<why>\"   close: ! python3 harness/hd.py close {c['change']} \"<why>\"")
    return "\n".join(out)


def approve(db, slug: str, head: str) -> int:
    """The user's approval of the feature's latest card: at head, not held; INSERT approval."""
    c = db.execute("SELECT * FROM card WHERE change=? ORDER BY id DESC LIMIT 1", (slug,)).fetchone()
    if not c or not c["head"].startswith(head):
        raise SystemExit(f"hd approve: the latest card of {slug} is at {c['head'][:7] if c else 'none'}, not {head}")
    if store.Ledger(db).hold(slug, c["head"]):
        raise SystemExit(f"hd approve: {slug} is held; hd hold {slug} --lift first")
    if db.execute("SELECT 1 FROM approval WHERE card=?", (c["id"],)).fetchone():
        raise SystemExit(f"hd approve: card {c['id']} is already approved")
    db.execute("INSERT INTO approval(card, at) VALUES (?,?)", (c["id"], now()))
    event(db, "approval", slug, None, f"card {c['id']} at {c['head'][:7]} approved by the user")
    return c["id"]


class Refused(Exception):
    """GitHub refused a write: the approval is spent and a new card names it."""


def publish(db, card_id: int, tracks: dict) -> None:
    """Each publish_step with done_at NULL, in order, with the card's texts, on its package's repo. ci: wait until every
    check at the head concluded; a failure → event('ci-failed') on the package, the approval kept, stop. A write
    refused → approval spent, stop. A read unknown (quota) → stop with no step done. After the last step:
    approval.spent_why = 'published'."""
    c = db.execute("SELECT * FROM card WHERE id=?", (card_id,)).fetchone()
    steps, t = json.loads(c["steps_json"]), json.loads(c["texts_json"])
    prs = {s["slug"]: s["pr"] for s in steps if s.get("pr")}
    for row in db.execute("SELECT * FROM publish_step WHERE card=? AND done_at IS NOT NULL", (card_id,)):   # resumed: the PRs it opened
        r = json.loads(row["result_json"] or "{}")
        if "pr" in r:
            prs[steps[row["n"] - 1]["slug"]] = r["pr"]
    try:
        for row in db.execute("SELECT * FROM publish_step WHERE card=? AND done_at IS NULL ORDER BY n", (card_id,)).fetchall():
            s = steps[row["n"] - 1]
            T, x = tracks[s["track"]], t[s["slug"]]
            up, pr = T.upstream, prs.get(s["slug"])
            if s["name"] == "push":
                r = subprocess.run(["git", "-C", T.path, "push", "-q", T.remote, f"{s['head']}:refs/heads/{s['branch']}"], capture_output=True, text=True)
                if r.returncode:
                    raise Refused(f"push {s['head'][:7]} to {s['branch']}: {r.stderr.strip()[-200:]}")
                result = {"pushed": s["head"]}
            elif s["name"] == "pr":
                r = write("POST", f"repos/{up}/pulls", {"title": x["title"], "body": x["body"], "draft": True,
                                                        "head": f"{OWNER}:{s['branch']}", "base": "main"})
                prs[s["slug"]] = r["number"]
                if c["pr"] is None and len({z["slug"] for z in steps}) == 1:
                    db.execute("UPDATE card SET pr=? WHERE id=?", (r["number"], card_id))
                result = {"pr": r["number"], "url": r.get("html_url")}
            elif s["name"] == "edit":
                write("PATCH", f"repos/{up}/pulls/{pr}", {"title": x["title"], "body": x["body"]})
                result = {"edited": pr}
            elif s["name"] == "ci":
                result = ci(db, s["head"], T)
                if result is None:
                    return   # unknown: the pass starts the publish again
                if not result["ok"]:
                    event(db, "ci-failed", s["slug"], None, f"{s['head'][:7]} {result['failed']}")
                    return
            elif s["name"] == "comment":
                r = write("POST", f"repos/{up}/issues/{pr}/comments", {"body": x["comment"]})
                result = {"comment": r.get("id")}
            elif s["name"] == "ready":
                p = read(f"repos/{up}/pulls/{pr}")
                if p is None:
                    return   # unknown: nothing spent, the pass starts the publish again
                write("POST", "graphql", {"query": "mutation($id: ID!) { markPullRequestReadyForReview(input: {pullRequestId: $id}) { pullRequest { isDraft } } }",
                                          "variables": {"id": p["node_id"]}})
                result = {"ready": pr}
            db.execute("UPDATE publish_step SET done_at=?, result_json=? WHERE card=? AND n=?", (now(), json.dumps(result), card_id, row["n"]))
            event(db, "published", c["change"], None, f"step {row['n']} {s['name']} on {up} done: {json.dumps(result)}")
    except Refused as e:
        db.execute("UPDATE approval SET spent_at=?, spent_why=? WHERE card=?", (now(), f"refused: {e}", card_id))
        event(db, "refused", c["change"], None, str(e))
        return
    db.execute("UPDATE approval SET spent_at=?, spent_why='published' WHERE card=?", (now(), card_id))
    done = ", ".join(f"{tracks[s['track']].upstream}#{prs.get(s['slug'])}" for s in {s["slug"]: s for s in steps}.values())
    event(db, "published", c["change"], None, f"card {card_id} published: {done} at {c['head'][:7]}")


def ci(db, head, T) -> dict | None:
    """Wait until every check at the head has concluded (the PR's checks run upstream); None when GitHub cannot be read."""
    while True:
        runs = observe.checks(db, T.upstream, head)
        if runs is None:
            return None
        if runs and all(r["status"] == "completed" for r in runs):
            failed = [r["name"] for r in runs if r["conclusion"] not in ("success", "skipped", "neutral")]
            return {"ok": not failed, "failed": failed, "checks": [r["name"] for r in runs]}
        observe.wait(30)


def read(url):
    """A read; None when GitHub did not answer it (a refusal is only for writes)."""
    status, _, body = observe.transport("GET", url)
    return json.loads(body) if status == 200 else None


def write(method, url, data):
    status, _, body = observe.transport(method, url, data)
    if status not in (200, 201):
        raise Refused(f"{method} {url}: HTTP {status} {body[:200]}")
    return json.loads(body) if body else {}
