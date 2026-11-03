"""The card and the publish (docs/ARCHITECTURE.md §7).

The card is the recorded list of acts and exact texts the user approves. The publish executes publish_step rows in
order, skipping those done, with the card's texts, never anything re-read from the live PR or evidence/.
"""
import json
import os
import subprocess

import observe
import store
from store import ROOT, event, now

OWNER = "AlexPerrin"   # our GitHub login: the PR head's owner, the comments that are ours


def card(db, ch, T, head: str, pr: dict | None, texts: dict, refusal: str = "") -> int:
    """Steps from the PR's state and the texts: push (unless the PR is at head) → pr (open a draft) | edit (title or body
    differ) → ci (if pushed or draft) → comment (pr-comment.md, then each pr-reply-<id>.md) → ready (if draft or new).
    INSERT OR IGNORE card and its publish_step rows; returns the card id."""
    public = ch.public or f"content/{ch.slug}"
    steps, t = [], {"title": texts.get("pr-title.txt", "").strip(), "body": texts.get("pr-body.md", "")}
    comment = texts.get("pr-comment.md", "").strip()
    replies = sorted(k for k in texts if k.startswith("pr-reply-"))
    if replies:
        comment += "\n\n" + "\n\n".join(texts[k].strip() for k in replies)
    t["comment"] = comment
    if refusal:
        t["refusal"] = refusal   # a new card names what GitHub refused last time
    pushed = not pr or pr["head"] != head
    if pushed:
        steps.append({"name": "push", "head": head, "branch": public})
    if not pr:
        steps.append({"name": "pr", "branch": public})
    else:
        if (t["title"] and t["title"] != pr["title"]) or (t["body"].strip() and t["body"].strip() != (pr["body"] or "").strip()):
            steps.append({"name": "edit", "pr": pr["number"]})
    if pushed or not pr or pr["draft"]:
        steps.append({"name": "ci", "head": head})
    if comment:
        steps.append({"name": "comment", "findings": [k[9:-3] for k in replies]})
    if not pr or pr["draft"]:
        steps.append({"name": "ready"})
    digest = store.digest(steps, t)
    row = db.execute("SELECT id FROM card WHERE change=? AND head=? AND digest=?", (ch.slug, head, digest)).fetchone()
    if row:
        db.execute("UPDATE card SET shown_at=? WHERE id=?", (now(), row["id"]))   # the same card, re-shown after moved texts
        return row["id"]
    cid = db.execute("INSERT INTO card(change, head, pr, steps_json, texts_json, digest, shown_at) VALUES (?,?,?,?,?,?,?)",
                     (ch.slug, head, pr["number"] if pr else None, json.dumps(steps), json.dumps(t), digest, now())).lastrowid
    for n, s in enumerate(steps, 1):
        db.execute("INSERT INTO publish_step(card, n, name) VALUES (?,?,?)", (cid, n, s["name"]))
    event(db, "card", ch.slug, None, render(db, db.execute("SELECT * FROM card WHERE id=?", (cid,)).fetchone(), T))
    return cid


def render(db, c, T) -> str:
    """The card as `hd` prints it: each act in order, each exact text, the verdict, the evidence path, the commands."""
    steps, t = json.loads(c["steps_json"]), json.loads(c["texts_json"])
    target = f"PR {T.upstream}#{c['pr']}" if c["pr"] else f"new PR on {T.upstream}"
    out = [f"{c['change']} @{c['head'][:7]}  {target}" + (f"   (the last publish was refused: {t['refusal']})" if t.get("refusal") else "")]
    for n, s in enumerate(steps, 1):
        line = {"push": lambda: f"push {c['head'][:7]} → fork {s['branch']}",
                "pr": lambda: f"open draft PR {s['branch']} → main   ── title ──  {t['title']}\n── body ──\n{t['body'].rstrip()}",
                "edit": lambda: f"edit title/body   ── title ──  {t['title']}\n── body ──\n{t['body'].rstrip()}",
                "ci": lambda: f"CI at {c['head'][:7]}",
                "comment": lambda: f"comment   ── text ──\n{t['comment']}",
                "ready": lambda: "ready for review"}[s["name"]]()
        out.append(f"  {n} {line}")
    v = db.execute("SELECT * FROM verdict WHERE change=? AND head=? ORDER BY id DESC LIMIT 1", (c["change"], c["head"])).fetchone()
    out.append(f"  verdict {'PASS' if v and v['ok'] else 'FAIL' if v else 'none (no judged criteria)'}{' (run ' + str(v['run']) + ')' if v else ''}   evidence/{c['change']}/")
    out.append(f"  yes: ! python3 harness/hd.py approve {c['change']} {c['head'][:7]}   no: hd hold {c['change']} \"<why>\"   close: ! python3 harness/hd.py close {c['change']} \"<why>\"")
    return "\n".join(out)


def approve(db, slug: str, head: str) -> int:
    """hd approve (the user only): the latest card of the change must be at head and not held; INSERT approval."""
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


def publish(db, card_id: int, T, path: str) -> None:
    """Each publish_step with done_at NULL, in order, with the card's texts. ci: wait until every check at head concluded;
    a failure → event('ci-failed'), the approval kept, stop. A write refused → approval spent, stop. A read unknown
    (quota) → stop with no step done. After the last step: approval.spent_why = 'published'."""
    c = db.execute("SELECT * FROM card WHERE id=?", (card_id,)).fetchone()
    steps, t, up = json.loads(c["steps_json"]), json.loads(c["texts_json"]), T.upstream
    pr = c["pr"]
    try:
        for row in db.execute("SELECT * FROM publish_step WHERE card=? AND done_at IS NULL ORDER BY n", (card_id,)).fetchall():
            s = steps[row["n"] - 1]
            if s["name"] == "push":
                r = subprocess.run(["git", "-C", path, "push", "-q", T.remote, f"{s['head']}:refs/heads/{s['branch']}"], capture_output=True, text=True)
                if r.returncode:
                    raise Refused(f"push {s['head'][:7]} to {s['branch']}: {r.stderr.strip()[-200:]}")
                result = {"pushed": s["head"]}
            elif s["name"] == "pr":
                r = write("POST", f"repos/{up}/pulls", {"title": t["title"], "body": t["body"], "draft": True,
                                                        "head": f"{OWNER}:{s['branch']}", "base": "main"})
                pr = r["number"]
                db.execute("UPDATE card SET pr=? WHERE id=?", (pr, card_id))
                record_pr(c["change"], pr, s["branch"])
                result = {"pr": pr, "url": r.get("html_url")}
            elif s["name"] == "edit":
                write("PATCH", f"repos/{up}/pulls/{pr}", {"title": t["title"], "body": t["body"]})
                result = {"edited": pr}
            elif s["name"] == "ci":
                result = ci(db, c, T, pr)
                if result is None:
                    return   # unknown: the pass starts the publish again
                if not result["ok"]:
                    event(db, "ci-failed", c["change"], None, f"{c['head'][:7]} {result['failed']}")
                    return
            elif s["name"] == "comment":
                r = write("POST", f"repos/{up}/issues/{pr}/comments", {"body": t["comment"]})
                result = {"comment": r.get("id")}
            elif s["name"] == "ready":
                p = read(f"repos/{up}/pulls/{pr}")
                if p is None:
                    return   # unknown: nothing spent, the pass starts the publish again
                node = p["node_id"]
                write("POST", "graphql", {"query": "mutation($id: ID!) { markPullRequestReadyForReview(input: {pullRequestId: $id}) { pullRequest { isDraft } } }",
                                          "variables": {"id": node}})
                result = {"ready": pr}
            db.execute("UPDATE publish_step SET done_at=?, result_json=? WHERE card=? AND n=?", (now(), json.dumps(result), card_id, row["n"]))
            event(db, "published", c["change"], None, f"step {row['n']} {s['name']} done: {json.dumps(result)}")
    except Refused as e:
        db.execute("UPDATE approval SET spent_at=?, spent_why=? WHERE card=?", (now(), f"refused: {e}", card_id))
        event(db, "refused", c["change"], None, str(e))
        return
    db.execute("UPDATE approval SET spent_at=?, spent_why='published' WHERE card=?", (now(), card_id))
    event(db, "published", c["change"], None, f"card {card_id} published: PR {up}#{pr} at {c['head'][:7]}")


def ci(db, c, T, pr) -> dict | None:
    """Wait until every check at the head has concluded (the PR's checks run upstream); None when GitHub cannot be read."""
    while True:
        runs = observe.checks(db, T.upstream, c["head"])
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


def record_pr(slug: str, pr: int, branch: str) -> None:
    """The opened PR in the change's definition (`pr`, `public`), committed: the pass reads it from there."""
    import yaml
    path = os.path.join(ROOT, "harness", "changes", f"{slug}.md")
    _, fm, body = open(path).read().split("---\n", 2)
    y = yaml.safe_load(fm)
    y["pr"], y["public"] = pr, branch
    open(path, "w").write("---\n" + yaml.safe_dump(y, sort_keys=False) + "---\n" + body)
    subprocess.run(["git", "-C", ROOT, "add", "--", path], capture_output=True)
    subprocess.run(["git", "-C", ROOT, "commit", "-q", "--author", "Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>",
                    "-m", f"change: {slug} is PR #{pr}\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>", "--", path], capture_output=True)


def write(method, url, data):
    status, _, body = observe.transport(method, url, data)
    if status not in (200, 201):
        raise Refused(f"{method} {url}: HTTP {status} {body[:200]}")
    return json.loads(body) if body else {}
