#!/usr/bin/env python3
"""hd: the commands (docs/ARCHITECTURE.md §8). Each is one function; the loop lives in decide.py and act.py."""
import argparse
import json
import os
import signal
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import act  # noqa: E402
import decide  # noqa: E402
import observe  # noqa: E402
import publish  # noqa: E402
import store  # noqa: E402
from store import ROOT, STATE, Ledger, event, now  # noqa: E402

CHANGES = os.path.join(ROOT, "harness", "changes")


def ancestors() -> set:
    pids, pid = set(), os.getpid()
    while pid > 1:
        pids.add(pid)
        try:
            pid = int(open(f"/proc/{pid}/status").read().split("PPid:")[1].split()[0])
        except (OSError, IndexError):
            break
    return pids


def session_of(db):
    """The live session row among the calling process's ancestors, if any."""
    pids = ancestors()
    for s in db.execute("SELECT * FROM session WHERE ended_at IS NULL"):
        if s["pid"] in pids:
            return s
    return None


def change(slug) -> decide.Change:
    path = os.path.join(CHANGES, f"{slug}.md")
    if not os.path.exists(path):
        sys.exit(f"hd: no change {slug}")
    return act.parse_change(path)


def track(ch, cfg=None):
    return (cfg or act.cfg()).tracks[ch.track]


def live_run(db, slug):
    return db.execute("SELECT * FROM run WHERE change=? AND ended_at IS NULL", (slug,)).fetchone()


def write_change(ch_slug, fm: dict, body: str):
    import yaml
    os.makedirs(CHANGES, exist_ok=True)
    open(os.path.join(CHANGES, f"{ch_slug}.md"), "w").write("---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n" + body)


def read_change(slug):
    import yaml
    _, fm, body = open(os.path.join(CHANGES, f"{slug}.md")).read().split("---\n", 2)
    return yaml.safe_load(fm), body


# --- the view --------------------------------------------------------------------------------------------------

DRIVER_KINDS = ('card', 'question', 'triage', 'alert', 'state', 'landed', 'attempt', 'ended')


def view(db, cfg):
    """The session's view, by role (ARCHITECTURE §8): the orchestrator's drain or spawns, ended runs and the runs line;
    the driver's cards, questions, triage lines, alerts, states, runs and goals. A session-less caller reads as a driver."""
    s = session_of(db)
    role = s["role"] if s else "driver"
    seen = s["seen_event"] if s else 0
    out = []
    if role == "orchestrator":
        if s["drain_at"]:
            out.append(f"drain    {s['drain_why']}: spawn nothing; `hd restart` once no run of yours is live")
        else:
            for r in db.execute("SELECT * FROM run WHERE started_at IS NULL AND ended_at IS NULL ORDER BY id"):
                head = open(os.path.join(ROOT, r["brief"])).readline().split("step: ", 1)
                pri = change(r["change"]).priority if os.path.exists(os.path.join(CHANGES, f"{r['change']}.md")) else "goal"
                out.append(f'spawn    Agent({r["role"]}, "Read and follow {r["brief"]}")   {r["change"]}  {pri}  {r["role"]}: {head[-1].strip()}')
    kinds = ("ended",) if role == "orchestrator" else DRIVER_KINDS
    for e in db.execute(f"SELECT * FROM event WHERE id>? AND kind IN ({','.join('?' * len(kinds))}) ORDER BY id", (seen, *kinds)):
        out.append(f"{e['kind']:<9}{e['change'] or '':<24} {e['detail']}")
    live = db.execute("SELECT * FROM run WHERE ended_at IS NULL AND started_at IS NOT NULL ORDER BY id").fetchall()
    out.append(f"runs     {len(live)}/{cfg.agents} live: " + ", ".join(f"{r['id']} {r['role']} {r['change']}" for r in live))
    if role == "driver":
        goals = [(g, Ledger(db).measure(g.slug)) for g in act.goals()]
        out.append("goals    " + "   ".join(f"{g.slug} {m['value']:g}% @{m['tree'][:12]}" if m else f"{g.slug} unmeasured" for g, m in goals))
    last = db.execute("SELECT max(id) m FROM event").fetchone()["m"] or 0
    if s:
        db.execute("UPDATE session SET seen_event=? WHERE id=?", (last, s["id"]))
    print("\n".join(out))


# --- commands --------------------------------------------------------------------------------------------------

def cmd_view(a):
    act.tick()
    view(store.connect(), act.cfg())


def cmd_tick(a):
    actions = act.tick(a.db, a.dry_run, a.offline, a.defs)
    if a.dry_run:
        for x in actions:
            print(f"{x.change:<28} {x.step.kind}: {x.step.why}")


def cmd_new(a):
    db = store.connect()
    path = os.path.join(CHANGES, f"{a.slug}.md")
    if a.on:
        fm, body = read_change(a.on)
        write_change(a.on, fm, body.rstrip() + f"\n\n## {a.title}\n{a.body}\n")
        event(db, "new", a.on, None, f"appended: {a.title}")
        act.tick_later()
        return print(f"appended to {a.on}")
    if os.path.exists(path):
        sys.exit(f"hd: {a.slug} exists")
    body = f"# {a.title}\n\n{a.body}\n"
    if a.from_alert:
        al = db.execute("SELECT * FROM alert WHERE id=?", (a.from_alert,)).fetchone()
        body += f"\n## alert {al['id']} {al['kind']} {al['subject']} (×{al['count']}, first {al['first_at']})\n{al['detail']}\n"
        db.execute("UPDATE alert SET disposition='filed', change=?, by='orchestrator', at=? WHERE id=?", (a.slug, now(), al["id"]))
    fm = {"slug": a.slug, "track": a.track, "priority": a.priority}
    if a.goal:
        fm["goal"] = a.goal
    if a.units:
        fm["units"] = a.units
    if a.deps:
        fm["deps"] = a.deps
    if a.pr:
        fm["pr"] = a.pr
    if a.upstream is False:
        fm["upstream"] = False
    write_change(a.slug, fm, body)
    for b in a.blocks or ():
        bfm, bbody = read_change(b)
        bfm["deps"] = sorted(set(bfm.get("deps") or []) | {a.slug})
        write_change(b, bfm, bbody)
    event(db, "new", a.slug, None, f"{a.track} {a.priority}: {a.title}")
    act.tick_later()
    print(f"filed {a.slug}")


def cmd_fold(a):
    db = store.connect()
    fm, body = read_change(a.slug)
    tfm, tbody = read_change(a.into)
    write_change(a.into, tfm, tbody.rstrip() + f"\n\n## folded from {a.slug}\n{body.strip()}\n")
    db.execute("INSERT INTO change_state(slug) VALUES (?) ON CONFLICT DO NOTHING", (a.into,))
    db.execute("INSERT INTO change_state(slug, folded_into) VALUES (?,?) ON CONFLICT(slug) DO UPDATE SET folded_into=excluded.folded_into", (a.slug, a.into))
    event(db, "fold", a.slug, None, f"into {a.into}")
    act.tick_later()


def cmd_show(a):
    db = store.connect()
    cfg, ch = act.cfg(), change(a.slug)
    C = decide.Ctx(Ledger(db), cfg, {c.slug: c for c in act.changes()})
    step = decide.next(C, ch)
    r = live_run(db, a.slug)
    print(act.brief_text(db, ch, track(ch, cfg), step, r["id"] if r else None))
    for e in db.execute("SELECT * FROM event WHERE change=? ORDER BY id DESC LIMIT 12", (a.slug,)).fetchall()[::-1]:
        print(f"{e['at']}  {e['kind']:<9}{e['detail']}")


def cmd_criterion(a):
    db = store.connect()
    db.execute("INSERT INTO criterion(change, rid, kind, text, cmd, source, source_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
               (a.slug, a.rid, a.kind, a.text, a.cmd, a.source, a.source_id, now()))
    print(f"criterion {a.slug}/{a.rid} ({a.kind})")


def cmd_submit(a):
    db = store.connect()
    cfg, ch = act.cfg(), change(a.slug)
    T = track(ch, cfg)
    ref = T.dev_ref(ch)
    if T.remote:   # a pushed track: the fork holds the head the harness builds; the local branch must be pushed
        subprocess.run(["git", "-C", T.path, "fetch", "-q", T.remote, f"+refs/heads/{T.prefix}/{a.slug}:{ref}"], capture_output=True)
        local = act.git(T.path, "rev-parse", "--verify", "-q", f"refs/heads/{T.prefix}/{a.slug}", check=False)
        pushed = act.git(T.path, "rev-parse", "--verify", "-q", ref, check=False)
        if local and local != pushed:
            sys.exit(f"hd submit: {T.prefix}/{a.slug} is at {local[:7]} locally and {pushed[:7] or 'absent'} on {T.remote}: git push {T.remote} {T.prefix}/{a.slug} first")
    head = act.git(T.path, "rev-parse", "--verify", "-q", ref, check=False)
    if not head:
        sys.exit(f"hd submit: no commit on {ref}")
    base = act.git(T.path, "rev-parse", T.base)
    if act.is_ancestor(T.path, head, base):
        sys.exit(f"hd submit: {ref} at {head[:7]} adds nothing to {T.base}: commit your work on it first")
    heads, composite = [], {}
    for dep in ch.deps:
        s = db.execute("SELECT head FROM submission WHERE change=? ORDER BY id DESC LIMIT 1", (dep,)).fetchone()
        d = change(dep)
        if not s or db.execute("SELECT 1 FROM landed WHERE change=? AND target=?", (dep, track(d, cfg).done_ref(d))).fetchone():
            continue
        if d.track == ch.track:
            heads.append(s["head"])
        elif d.track in ("central", "filestore"):   # a library head built into the candidate as a Gradle composite
            dT = track(d, cfg)
            composite[d.track] = {"head": s["head"], "tree": act.git(dT.path, "rev-parse", s["head"] + "^{tree}")}
    try:
        tree, tcommit = act.candidate(T.path, base, heads + [head])
    except act.Conflict as c:
        sys.exit(f"hd submit: the candidate conflicts in {' '.join(c.args[0])}: merge {T.base} into your branch")
    r = live_run(db, a.slug)
    new = store.submit(db, a.slug, head, tree, tcommit, json.dumps(composite) if composite else None, r["id"] if r else None)
    db.execute("INSERT INTO ref(repo, name, sha, seen_at) VALUES (?,?,?,?) ON CONFLICT(repo, name) DO UPDATE SET sha=excluded.sha, seen_at=excluded.seen_at",
               (T.name, ref, head, now()))
    if new:
        event(db, "submitted", a.slug, r["id"] if r else None, f"{head[:7]} candidate {tcommit[:7]} tree {tree[:12]}")
    act.tick_later()
    print(f"run {r['id']}: submitted {head}" if r else f"submitted {head}")


def cmd_verdict(a):
    db = store.connect()
    r = live_run(db, a.slug)
    if not r or r["role"] != "qa":
        sys.exit("hd verdict: no live qa run of this change")
    sub = db.execute("SELECT head FROM submission WHERE change=? AND head LIKE ? ORDER BY id DESC LIMIT 1", (a.slug, a.head + "%")).fetchone()
    if not sub:
        sys.exit(f"hd verdict: no submission of {a.slug} at {a.head}")
    head = sub["head"]
    data = json.load(open(a.file))
    crit = {c["rid"]: c for c in Ledger(db).criteria(a.slug, "judge")}
    rows = data.get("rows", data)
    missing = set(rows) - set(crit)
    if missing:
        sys.exit(f"hd verdict: no judged criterion {', '.join(sorted(missing))}")
    results = {rid: (rows.get(rid, "not-judged") or "not-judged") for rid in crit}
    bad = [rid for rid, v in results.items() if v.partition(":")[0].strip() not in ("pass", "fail", "not-judged")]
    if bad:
        sys.exit(f"hd verdict: a result is pass, fail: <note> or not-judged, not {', '.join(repr(results[b]) for b in bad)}")
    fails = [rid for rid, v in results.items() if not v.startswith("pass")]
    d = store.digest([(c["rid"], c["text"]) for c in crit.values()])
    db.execute("BEGIN")
    vid = db.execute("INSERT INTO verdict(change, head, run, ok, criteria_digest, at) VALUES (?,?,?,?,?,?)",
                     (a.slug, head, r["id"], int(not fails), d, now())).lastrowid
    for rid, v in results.items():
        res, _, note = v.partition(":")
        db.execute("INSERT INTO verdict_row(verdict, criterion_id, result, note) VALUES (?,?,?,?)", (vid, crit[rid]["id"], res.strip(), note.strip() or None))
    db.execute("COMMIT")
    a.head = head
    line = f"run {r['id']}: PASS" if not fails else f"run {r['id']}: FAIL {len(fails)} criteria"
    event(db, "verdict", a.slug, r["id"], f"{'PASS' if not fails else 'FAIL ' + ', '.join(fails)} at {a.head[:7]}")
    print(line)


EFFECTS = ("dep", "waive", "accept-difference", "close", "reply", "move-repo")   # what hd answer applies (ARCHITECTURE §8)


def cmd_ask(a):
    db = store.connect()
    if Ledger(db).open_ask(a.slug):
        sys.exit("hd ask: a question of this change is already open")
    opts = [dict(zip(("id", "text", "effect"), (p.strip() for p in o.split(":", 2)))) for o in a.option]
    bad = [o for o in opts if len(o) < 3 or not all(o.values()) or o["effect"].split()[0] not in EFFECTS]
    if bad:   # refused before any row: a malformed question would never show and never answer
        sys.exit(f"hd ask: each --option is id:text:effect with the effect one of {', '.join(EFFECTS)}; no ':' in the text. Bad: {bad}")
    r = live_run(db, a.slug)
    aid = db.execute("INSERT INTO ask(change, text, options_json, run, at) VALUES (?,?,?,?,?)",
                     (a.slug, a.text, json.dumps(opts), r["id"] if r else None, now())).lastrowid
    event(db, "question", a.slug, r["id"] if r else None,
          f'{a.text}  ' + "  ".join(f"({o['id']}) {o['text']} [{o['effect']}]" for o in opts) + f"   → hd answer {a.slug} <id> \"<words>\"")
    print(f"run {r['id']}: ask" if r else f"ask {aid}")


def cmd_answer(a):
    db = store.connect()
    q = Ledger(db).open_ask(a.slug)
    if not q:
        sys.exit("hd answer: no open question")
    opt = next((o for o in json.loads(q["options_json"]) if o["id"] == a.option), None)
    if not opt:
        sys.exit(f"hd answer: options are {[o['id'] for o in json.loads(q['options_json'])]}")
    effect, _, arg = opt["effect"].partition(" ")
    if effect == "close":
        sys.exit("hd answer: a close is the user's own: ! hd close")
    db.execute("BEGIN")
    db.execute("INSERT INTO answer(ask, option, words, by, at) VALUES (?,?,?,?,?)", (q["id"], a.option, a.words, "user", now()))
    if effect == "dep":
        fm, body = read_change(a.slug)
        fm["deps"] = sorted(set(fm.get("deps") or []) | {arg})
        write_change(a.slug, fm, body)
    elif effect == "waive":
        db.execute("UPDATE criterion SET waived=1 WHERE change=? AND rid=?", (a.slug, arg))
    elif effect == "reply":
        d = os.path.join(ROOT, "evidence", a.slug)
        os.makedirs(d, exist_ok=True)
        f = db.execute("SELECT * FROM finding WHERE comment_id=?", (int(arg),)).fetchone()
        quoted = "\n".join("> " + l for l in f["body"].strip().splitlines())
        open(os.path.join(d, f"pr-reply-{arg}.md"), "w").write(f"{quoted}\n\n@{f['author']} {a.words or ''}\n")
    elif effect == "accept-difference":
        db.execute("INSERT INTO criterion(change, rid, kind, text, source, source_id, created_at) VALUES (?,?,?,?,?,?,?)",
                   (a.slug, f"accepted-{q['id']}", "judge", f"accepted difference: {arg}", "answer", q["id"], now()))
    db.execute("COMMIT")
    event(db, "answer", a.slug, None, f"ask {q['id']}: option {a.option} ({opt['effect']}) {a.words or ''}")
    act.tick_later()


def cmd_hold(a):
    db = store.connect()
    if a.lift:
        db.execute("UPDATE hold SET lifted_at=? WHERE change=? AND lifted_at IS NULL", (now(), a.slug))
    else:
        head = None if a.all else (db.execute("SELECT head FROM submission WHERE change=? ORDER BY id DESC LIMIT 1", (a.slug,)).fetchone() or {"head": None})["head"]
        db.execute("INSERT INTO hold(change, head, why, at) VALUES (?,?,?,?)", (a.slug, head, a.why, now()))
    event(db, "hold", a.slug, None, "lifted" if a.lift else f"held {'all heads' if a.all else 'this head'}: {a.why or ''}")
    act.tick_later()


def cmd_approve(a):
    db = store.connect()
    cid = publish.approve(db, a.slug, a.head)
    print(f"approved card {cid}")
    act.tick_later()


def cmd_publish(a):
    """The publish job: the card's undone steps with its texts (started by the pass; HD_SLUG names the change)."""
    db = store.connect()
    c = db.execute("SELECT * FROM card WHERE id=?", (a.card,)).fetchone()
    ch = change(c["change"])
    T = track(ch)
    publish.publish(db, a.card, T, T.path)
    left = Ledger(db).undone_steps(a.card)
    db.execute("""INSERT INTO job(kind, key, change, ok, detail, ended_at) VALUES ('publish', ?, ?, ?, ?, ?)
                  ON CONFLICT(kind, key) DO UPDATE SET ok=excluded.ok, detail=excluded.detail, ended_at=excluded.ended_at""",
               (str(a.card), c["change"], int(not left), f"{len(left)} steps left" if left else "published", now()))
    act.tick_later()


def cmd_triage(a):
    """A maintainer's word: finding → a judged criterion on the PR's open change (or a new change for a done one);
    ask → an ask of the user whose answer's words become the reply; ack → nothing more."""
    db = store.connect()
    f = db.execute("SELECT * FROM finding WHERE comment_id=?", (a.comment_id,)).fetchone()
    if not f:
        sys.exit(f"hd triage: no comment {a.comment_id}")
    slug = f["change"]
    if a.verdict == "finding" and (not slug or Ledger(db).landed(slug, track(change(slug)).done_ref(change(slug)))):
        ch = next((c for c in act.changes() if c.pr == f["pr"] and not Ledger(db).closed(c.slug) and not Ledger(db).landed(c.slug, track(c).done_ref(c))), None)
        if not ch:
            d = change(slug) if slug else None
            slug = f"{d.track if d else 'fork'}-{f['pr']}-c{f['comment_id']}"
            write_change(slug, {"slug": slug, "track": d.track if d else "fork", "priority": "P1", "pr": f["pr"], "public": d.public if d else ""},
                         f"# PR #{f['pr']}: {f['author']}'s finding {f['comment_id']}\n\n{f['body']}\n")
            event(db, "new", slug, None, f"from finding {f['comment_id']} on PR #{f['pr']}")
        else:
            slug = ch.slug
    cid = None
    if a.verdict == "finding":
        cid = db.execute("INSERT INTO criterion(change, rid, kind, text, cmd, source, source_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
                         (slug, f"finding-{f['comment_id']}", "judge", f"{f['author']}: {f['body'][:500]}", "pr-text", "finding", f["comment_id"], now())).lastrowid
    elif a.verdict == "ask":
        db.execute("INSERT INTO ask(change, text, options_json, at) VALUES (?,?,?,?)",
                   (slug, f"{f['author']} on PR #{f['pr']}: {f['body'][:500]}", json.dumps([{"id": "r", "text": "reply with your words", "effect": f"reply {f['comment_id']}"}]), now()))
        event(db, "question", slug, None, f"{f['author']} on PR #{f['pr']}: {f['body'][:300]!r}   → hd answer {slug} r \"<the reply>\"")
    db.execute("UPDATE finding SET triage=?, triaged_at=?, change=?, criterion_id=? WHERE comment_id=?", (a.verdict, now(), slug, cid, f["comment_id"]))
    event(db, "triaged", slug, None, f"comment {f['comment_id']}: {a.verdict}")
    act.tick_later()


def cmd_close(a):
    db = store.connect()
    db.execute("INSERT INTO change_state(slug, closed_at, closed_words) VALUES (?,?,?) ON CONFLICT(slug) DO UPDATE SET closed_at=excluded.closed_at, closed_words=excluded.closed_words",
               (a.slug, now(), a.words))
    r = live_run(db, a.slug)
    if r:
        db.execute("UPDATE run SET ended_at=?, end_kind='close' WHERE id=?", (now(), r["id"]))
        act.stop_scope(r["id"])
        event(db, "ended", a.slug, r["id"], f"run {r['id']}: closed with its change")
    for j in db.execute("SELECT * FROM job WHERE change=? AND pid IS NOT NULL AND ended_at IS NULL", (a.slug,)).fetchall():
        subprocess.run(["systemctl", "--user", "stop", j["scope"] + ".scope"], capture_output=True)
        db.execute("UPDATE job SET ended_at=?, pid=NULL, exit=-1, detail='closed' WHERE kind=? AND key=?", (now(), j["kind"], j["key"]))
    event(db, "closed", a.slug, None, a.words)
    act.tick_later()


def cmd_job(a):
    db = store.connect()
    db.execute("""INSERT INTO job(kind, key, change, ok, detail, ended_at) VALUES (?,?,?,?,?,?)
                  ON CONFLICT(kind, key) DO UPDATE SET ok=excluded.ok, detail=excluded.detail, ended_at=excluded.ended_at""",
               (a.kind, a.key, os.environ.get("HD_SLUG"), int(a.result == "ok"), a.detail, now()))
    event(db, "job", os.environ.get("HD_SLUG"), None, f"{a.kind} {decide.short(a.key)} {a.result} {a.detail or ''}")
    if a.kind == "deploy" and a.result == "ok":   # the test server now runs staging as it was when the deploy began: those heads are live
        j = db.execute("SELECT started_at FROM job WHERE kind='deploy' AND key=?", (a.key,)).fetchone()
        for r in db.execute("""SELECT change FROM landed WHERE target=? AND at<=? AND change NOT IN (SELECT change FROM landed WHERE target='live')""",
                            (decide.STAGING, j["started_at"] or now())).fetchall():
            db.execute("INSERT INTO landed(change, target, sha, at) VALUES (?,?,?,?)", (r["change"], "live", a.key.split(":")[0], now()))
            event(db, "landed", r["change"], None, "live: the test server runs it")
    act.tick_later()


def cmd_gate(a):
    """Run every scripted criterion of the change in the candidate dir; check_result per criterion at the key's tree;
    then the gate job's result."""
    db = store.connect()
    tree = a.key.split(":")[0].split("_")[0]   # T less its composite suffix: the submission's tree
    ch = change(a.slug)
    T = track(ch)
    s = db.execute("SELECT * FROM submission WHERE change=? AND tree=? ORDER BY id DESC LIMIT 1", (a.slug, tree)).fetchone() \
        or {"tree": tree, "tcommit": os.environ.get("HD_TCOMMIT", ""), "head": os.environ.get("HD_HEAD", "")}
    env = act.job_env(db, ch, T, s, BUILD=a.dir)
    fails = []
    for c in Ledger(db).criteria(a.slug, "script"):
        print(f"== {c['rid']}: {c['cmd']}", flush=True)
        r = subprocess.run(c["cmd"], shell=True, cwd=a.dir, capture_output=True, text=True, env=env)
        sys.stdout.write(r.stdout + r.stderr)
        note = (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or [""])[-1][:200]
        if r.returncode == 75:   # the criterion's source is down: no result, the pass starts the gate again
            print(f"== {c['rid']}: no result ({note})")
            sys.exit(75)
        db.execute("INSERT OR REPLACE INTO check_result(criterion_id, tree, ok, note, at) VALUES (?,?,?,?,?)",
                   (c["id"], tree, int(r.returncode == 0), note if r.returncode else None, now()))
        if r.returncode:
            fails.append(f"{c['rid']} ({note})")
    db.execute("""INSERT INTO job(kind, key, change, ok, detail, ended_at) VALUES ('gate',?,?,?,?,?)
                  ON CONFLICT(kind, key) DO UPDATE SET ok=excluded.ok, detail=excluded.detail, ended_at=excluded.ended_at""",
               (a.key, a.slug, int(not fails), "; ".join(fails) or None, now()))
    event(db, "job", a.slug, None, f"gate {decide.short(a.key)} {'ok' if not fails else 'fail ' + '; '.join(fails)}")
    act.tick_later()
    sys.exit(1 if fails else 0)


def cmd_candidate(a):
    cfg, ch = act.cfg(), change(a.slug)
    T = track(ch, cfg)
    head = act.git(T.path, "rev-parse", a.head or T.dev_ref(ch))
    try:
        print(*act.candidate(T.path, a.base or act.git(T.path, "rev-parse", T.base), [head]))
    except act.Conflict as c:
        sys.exit(f"conflict: {' '.join(c.args[0])}")


def cmd_stack(a):
    """The change's running stack, mirrored from the track script's record (up.json) so the pass can recover it."""
    db = store.connect()
    if a.clear:
        db.execute("DELETE FROM stack WHERE change=?", (a.slug,))
        return
    d = json.load(open(a.file))
    db.execute("""INSERT INTO stack(change, script, containers_json, desktops_json, token, modulus, started_at) VALUES (?,?,?,?,?,?,?)
                  ON CONFLICT(change) DO UPDATE SET script=excluded.script, containers_json=excluded.containers_json,
                  desktops_json=excluded.desktops_json, token=excluded.token, modulus=excluded.modulus, started_at=excluded.started_at""",
               (a.slug, d.get("script"), json.dumps(d.get("containers", "").split()), json.dumps(d.get("desktops", "").split()),
                d.get("token"), d.get("modulus"), d.get("started")))


def cmd_measure(a):
    """A goal script's result (its last act, with `hd job measure <key> ok`)."""
    db = store.connect()
    db.execute("INSERT OR REPLACE INTO measure(goal, tree, value, report, at) VALUES (?,?,?,?,?)", (a.goal, a.tree, a.value, a.report, now()))
    event(db, "measure", a.goal, None, f"{a.value:g}% at {a.tree[:12]}")


def cmd_step(a):
    db = store.connect()
    if a.state == "start":
        db.execute("INSERT INTO step_log(change, script, step, started_at, detail) VALUES (?,?,?,?,?)", (a.slug, a.script, a.step, now(), a.detail))
    else:
        db.execute("UPDATE step_log SET done_at=?, detail=coalesce(?, detail) WHERE id=(SELECT max(id) FROM step_log WHERE change=? AND script=? AND step=?)",
                   (now(), a.detail, a.slug, a.script, a.step))


def cmd_fault(a):
    db = store.connect()
    store.alert(db, "fault", str(a.run), a.what)
    observe.alerts(db)
    act.wake(db)


def cmd_dismiss(a):
    db = store.connect()
    db.execute("UPDATE alert SET disposition='dismissed', why=?, by='orchestrator', at=? WHERE id=?", (a.why, now(), a.id))


def cmd_stop(a):
    db = store.connect()
    db.execute("UPDATE run SET ended_at=?, end_kind='stop' WHERE id=? AND ended_at IS NULL", (now(), a.run))
    r = db.execute("SELECT change FROM run WHERE id=?", (a.run,)).fetchone()
    act.stop_scope(a.run)
    event(db, "ended", r["change"] if r else None, a.run, "stopped by the orchestrator")
    act.tick_later()


def cmd_scope(a):
    """Move the calling shell into hd-run-<id>.scope (created with a placeholder sleep). Silent when the user manager
    refuses the move: the orchestrator was not started by harness/orchestrator.sh."""
    unit = f"hd-run-{a.run}.scope"
    cg = subprocess.run(["systemctl", "--user", "show", "-p", "ControlGroup", "--value", unit], capture_output=True, text=True).stdout.strip()
    if not cg:
        subprocess.Popen(["systemd-run", "--user", "--scope", "--quiet", "--unit", unit[:-6], "--", "sleep", "infinity"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(50):
            cg = subprocess.run(["systemctl", "--user", "show", "-p", "ControlGroup", "--value", unit], capture_output=True, text=True).stdout.strip()
            if cg:
                break
    try:
        open(f"/sys/fs/cgroup{cg}/cgroup.procs", "w").write(str(os.getppid()))
    except OSError:
        pass


def cmd_regate(a):
    db = store.connect()
    s = db.execute("SELECT tree FROM submission WHERE change=? ORDER BY id DESC LIMIT 1", (a.slug,)).fetchone()
    if not s:
        sys.exit("hd regate: no submission")
    db.execute("DELETE FROM job WHERE kind IN ('build', 'gate') AND key LIKE ? AND ended_at IS NOT NULL", (s["tree"] + ":%",))   # ended ones; a running job keeps its row   # a fixed tool re-runs the build and the gate at the same tree
    db.execute("DELETE FROM attempt WHERE kind IN ('build', 'gate') AND key LIKE ?", (s["tree"] + ":%",))
    db.execute("DELETE FROM check_result WHERE tree=?", (s["tree"],))
    event(db, "regate", a.slug, None, s["tree"][:12])
    act.tick_later()


def cmd_kpi(a):
    import kpi
    print(kpi.report(store.connect()))


def cmd_commit(a):
    """A pathspec commit on the live branch, pushed; under state/ship.lock so no ship's candidate is computed on a tip
    this commit then moves."""
    import fcntl
    cfg = act.cfg()
    T = cfg.tracks["harness"]
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "ship.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        act.git(ROOT, "add", "--", *a.paths)
        act.git(ROOT, "commit", "-q", "--author", act.AUTHOR, "-m", a.message + "\n\n" + act.TRAILER, "--", *a.paths)
        print(act.git(ROOT, "log", "-1", "--format=%h %s"))
        act.git(ROOT, "push", "-q", "origin", f"HEAD:{T.base}")


def cmd_restart(a):
    db = store.connect()
    s = session_of(db)
    if not s:
        sys.exit("hd restart: not inside an orchestrator session")
    if db.execute("SELECT 1 FROM run WHERE started_at IS NOT NULL AND ended_at IS NULL").fetchone():
        sys.exit("hd restart: a run is live; wait for its hand-back")
    db.execute("UPDATE session SET ended_at=?, end_kind='restart' WHERE id=?", (now(), s["id"]))
    event(db, "session", None, None, f"session {s['id']} restarted: {s['drain_why'] or 'asked'}")
    os.kill(s["pid"], signal.SIGTERM)


def cmd_session_ended(a):
    db = store.connect()
    observe.sessions(db, act.definition_blob())
    s = db.execute("SELECT end_kind FROM session WHERE ended_at IS NOT NULL ORDER BY id DESC LIMIT 1").fetchone()
    sys.exit(1 if s and s["end_kind"] == "exit" else 0)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hd", description="the harness loop; no argument runs a pass and prints the view")
    sub = p.add_subparsers(dest="command")   # not "cmd": `criterion add --cmd` is an option
    s = sub.add_parser("tick"); s.add_argument("--dry-run", action="store_true"); s.add_argument("--db"); s.add_argument("--offline", action="store_true"); s.add_argument("--defs")
    s = sub.add_parser("new"); s.add_argument("slug"); s.add_argument("--track", required=True); s.add_argument("--title", required=True)
    s.add_argument("--body", default=""); s.add_argument("--priority", default="P2", type=lambda p: act.tier(p)); s.add_argument("--deps", nargs="*")
    s.add_argument("--blocks", nargs="*"); s.add_argument("--on"); s.add_argument("--pr", type=int); s.add_argument("--from-alert", type=int)
    s.add_argument("--no-upstream", dest="upstream", action="store_false", default=True); s.add_argument("--goal"); s.add_argument("--units", nargs="*")
    s = sub.add_parser("measure"); s.add_argument("goal"); s.add_argument("tree"); s.add_argument("value", type=float); s.add_argument("report", nargs="?")
    s = sub.add_parser("fold"); s.add_argument("slug"); s.add_argument("--into", required=True)
    s = sub.add_parser("show"); s.add_argument("slug")
    s = sub.add_parser("criterion"); s.add_argument("add"); s.add_argument("slug"); s.add_argument("rid"); s.add_argument("--kind", choices=("script", "judge"), required=True)
    s.add_argument("--text", required=True); s.add_argument("--cmd"); s.add_argument("--source", default="accuracy"); s.add_argument("--source-id", type=int)
    s = sub.add_parser("submit"); s.add_argument("slug")
    s = sub.add_parser("verdict"); s.add_argument("slug"); s.add_argument("head"); s.add_argument("file")
    s = sub.add_parser("ask"); s.add_argument("slug"); s.add_argument("text"); s.add_argument("--option", action="append", required=True)
    s = sub.add_parser("answer"); s.add_argument("slug"); s.add_argument("option"); s.add_argument("words", nargs="?")
    s = sub.add_parser("hold"); s.add_argument("slug"); s.add_argument("why", nargs="?"); s.add_argument("--all", action="store_true"); s.add_argument("--lift", action="store_true")
    s = sub.add_parser("approve"); s.add_argument("slug"); s.add_argument("head")
    s = sub.add_parser("publish"); s.add_argument("card", type=int)
    s = sub.add_parser("triage"); s.add_argument("comment_id", type=int); s.add_argument("verdict", choices=("finding", "ask", "ack"))
    s = sub.add_parser("close"); s.add_argument("slug"); s.add_argument("words")
    s = sub.add_parser("job"); s.add_argument("kind"); s.add_argument("key"); s.add_argument("result", choices=("ok", "fail")); s.add_argument("detail", nargs="?")
    s = sub.add_parser("gate"); s.add_argument("slug"); s.add_argument("key"); s.add_argument("dir")
    s = sub.add_parser("candidate"); s.add_argument("slug"); s.add_argument("--base"); s.add_argument("--head")
    s = sub.add_parser("stack"); s.add_argument("slug"); s.add_argument("file", nargs="?"); s.add_argument("--clear", action="store_true")
    s = sub.add_parser("step"); s.add_argument("slug"); s.add_argument("script"); s.add_argument("step"); s.add_argument("state", choices=("start", "done")); s.add_argument("detail", nargs="?")
    s = sub.add_parser("fault"); s.add_argument("run", type=int); s.add_argument("what")
    s = sub.add_parser("dismiss"); s.add_argument("id", type=int); s.add_argument("why")
    s = sub.add_parser("stop"); s.add_argument("run", type=int)
    s = sub.add_parser("scope"); s.add_argument("run", type=int)
    s = sub.add_parser("regate"); s.add_argument("slug")
    sub.add_parser("kpi")
    s = sub.add_parser("commit"); s.add_argument("paths", nargs="+"); s.add_argument("-m", "--message", required=True)
    sub.add_parser("restart")
    s = sub.add_parser("session-ended"); s.add_argument("pid", nargs="?")
    a = p.parse_args(argv)
    globals()[f"cmd_{(a.command or 'view').replace('-', '_')}"](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
