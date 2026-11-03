"""world → ledger (docs/ARCHITECTURE.md §5). Each function writes observation rows bound to what it observed
(sha, pid, comment id) and nothing else."""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from store import ROOT, alert, event, now


def pid_start(pid) -> int:
    """The process's start time from /proc: with the pid, the identity of a process."""
    try:
        return int(open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[19])
    except OSError:
        return 0


def alive(pid, start) -> bool:
    return bool(pid) and pid_start(pid) == start


def fetch(db, T) -> set:
    """git fetch --prune every remote; for-each-ref → UPSERT ref rows; returns the names whose sha changed."""
    subprocess.run(["git", "-C", T.path, "fetch", "--all", "--prune", "-q"], capture_output=True)
    out = subprocess.run(["git", "-C", T.path, "for-each-ref", "--format=%(objectname) %(refname) %(tree)", "refs/heads", "refs/remotes"],
                         capture_output=True, text=True).stdout
    have = {r["name"]: r["sha"] for r in db.execute("SELECT name, sha FROM ref WHERE repo=?", (T.name,))}
    moved = set()
    for line in out.splitlines():
        sha, name, tree = (line.split() + [None])[:3]
        if have.get(name) != sha:
            moved.add(name)
            db.execute("INSERT INTO ref(repo, name, sha, seen_at, tree) VALUES (?,?,?,?,?) ON CONFLICT(repo, name) DO UPDATE SET sha=excluded.sha, seen_at=excluded.seen_at, tree=excluded.tree",
                       (T.name, name, sha, now(), tree))
    for name in set(have) - {l.split()[1] for l in out.splitlines()}:
        db.execute("DELETE FROM ref WHERE repo=? AND name=?", (T.name, name))
        moved.add(name)
    return moved


def landed(db, T, target: str, changes: list) -> None:
    """For each open change of the track with a submission and no landed row for target: its head an ancestor of
    target's sha → INSERT landed."""
    sha = db.execute("SELECT sha FROM ref WHERE repo=? AND name=?", (T.name, target)).fetchone()
    if not sha:
        return
    for ch in changes:
        if db.execute("SELECT 1 FROM landed WHERE change=? AND target=?", (ch.slug, target)).fetchone():
            continue
        head = db.execute("SELECT head FROM submission WHERE change=? ORDER BY id DESC LIMIT 1", (ch.slug,)).fetchone()
        if head and subprocess.run(["git", "-C", T.path, "merge-base", "--is-ancestor", head["head"], sha["sha"]]).returncode == 0:
            db.execute("INSERT INTO landed(change, target, sha, at) VALUES (?,?,?,?)", (ch.slug, target, sha["sha"], now()))
            event(db, "landed", ch.slug, None, f"{head['head'][:7]} on {target}")


def procs(db) -> None:
    """A job whose (pid, pid_start) is gone: a result recorded by the script → ended_at; else an attempt row with the
    log's last line as cause (hex runs dropped), the pid cleared so the pass may start it again."""
    for j in db.execute("SELECT * FROM job WHERE pid IS NOT NULL AND ended_at IS NULL").fetchall():
        if alive(j["pid"], j["pid_start"]):
            continue
        rc = j["log"][:-4] + ".rc"
        code = int(Path(rc).read_text() or -1) if os.path.exists(rc) else -1
        db.execute("UPDATE job SET ended_at=?, exit=?, pid=NULL WHERE kind=? AND key=?", (now(), code, j["kind"], j["key"]))
        if j["ok"] is None:
            tail = Path(j["log"]).read_text(errors="replace").strip().splitlines()[-1:] if os.path.exists(j["log"]) else []
            cause = re.sub(r"[0-9a-f]{7,}", "", tail[0] if tail else "no output").strip()[:200]
            db.execute("INSERT INTO attempt(kind, key, cause, exit, at) VALUES (?,?,?,?,?)", (j["kind"], j["key"], cause, code, now()))
            event(db, "attempt", j["change"], None, f"{j['kind']} {j['key'][:12]} exit {code}: {cause}")


def sessions(db, definition: str) -> None:
    """A live session whose pid is gone ended by a crash, with its started runs (they die with their console);
    a live session whose definition differs from HEAD's is drained."""
    for s in db.execute("SELECT * FROM session WHERE ended_at IS NULL").fetchall():
        if not alive(s["pid"], s["pid_start"]):
            db.execute("UPDATE session SET ended_at=?, end_kind='crash' WHERE id=?", (now(), s["id"]))
            for r in db.execute("SELECT id, change FROM run WHERE started_at IS NOT NULL AND ended_at IS NULL").fetchall():
                db.execute("UPDATE run SET ended_at=?, end_kind='console' WHERE id=?", (now(), r["id"]))
                event(db, "ended", r["change"], r["id"], "console died")
        elif s["definition"] != definition and not s["drain_at"]:
            db.execute("UPDATE session SET drain_at=?, drain_why='definition moved' WHERE id=?", (now(), s["id"]))
            event(db, "drain", None, None, "the orchestrator's definition moved: spawn nothing, hd restart once no run is live")


def alerts(db) -> None:
    """UPSERT alert rows from the anomaly queries (ARCHITECTURE §12)."""
    for r in db.execute("SELECT kind, key, count(*) n, max(cause) cause FROM attempt GROUP BY kind, key HAVING n>=3"):
        alert(db, "attempts", f"{r['kind']}:{r['key']}", f"×{r['n']} {r['cause']}")
    for r in db.execute("""SELECT change, count(*) n FROM run WHERE end_kind IN ('console','stop') AND record IS NULL
                           GROUP BY change HAVING n>=2"""):
        alert(db, "run-lost", r["change"], f"{r['n']} runs ended without a record")
    for r in db.execute("""SELECT r.change, count(*) n FROM run r
                           WHERE r.listed_at > coalesce((SELECT max(at) FROM submission s WHERE s.change=r.change), '')
                           GROUP BY r.change HAVING n>5"""):
        alert(db, "runs-per-head", r["change"], f"{r['n']} runs since the last submission")
    for r in db.execute("""SELECT a.id, a.change FROM ask a LEFT JOIN answer n ON n.ask=a.id WHERE n.ask IS NULL
                           AND (SELECT count(*) FROM submission s WHERE s.change=a.change AND s.at>a.at) >= 2"""):
        alert(db, "ask-stale", str(r["id"]), f"ask {r['id']} of {r['change']} open across two submissions")
    for a in db.execute("SELECT * FROM alert WHERE disposition IS NULL AND NOT EXISTS (SELECT 1 FROM event e WHERE e.kind='alert' AND e.detail LIKE 'alert ' || alert.id || ' %')").fetchall():
        event(db, "alert", a["change"], None, f"alert {a['id']} {a['kind']} {a['subject']}: {a['detail']}   → hd new --track harness --from-alert {a['id']} --title \"…\" | hd dismiss {a['id']} \"<why>\"")


# --- the evidence texts ------------------------------------------------------------------------------------------

TEXTS = ("pr-title.txt", "pr-body.md", "pr-comment.md")


def texts(db, slug: str) -> None:
    """evidence/<slug>/pr-title.txt, pr-body.md, pr-comment.md, pr-reply-<id>.md → text rows by content sha; a file gone, its row gone."""
    d = os.path.join(ROOT, "evidence", slug)
    names = [n for n in (os.listdir(d) if os.path.isdir(d) else []) if n in TEXTS or (n.startswith("pr-reply-") and n.endswith(".md"))]
    have = {r["name"]: r["sha"] for r in db.execute("SELECT name, sha FROM text WHERE change=?", (slug,))}
    for n in names:
        body = Path(d, n).read_text(errors="replace")
        sha = hashlib.sha1(body.encode()).hexdigest()
        if have.get(n) != sha:
            db.execute("INSERT INTO text(change, name, sha, body, at) VALUES (?,?,?,?,?) ON CONFLICT(change, name) DO UPDATE SET sha=excluded.sha, body=excluded.body, at=excluded.at",
                       (slug, n, sha, body, now()))
    for n in set(have) - set(names):
        db.execute("DELETE FROM text WHERE change=? AND name=?", (slug, n))


# --- GitHub ------------------------------------------------------------------------------------------------------

def transport(method: str, url: str, data=None, headers=()) -> tuple:
    """One GitHub call through gh (its token): (status, headers, body). Tests replace this function."""
    cmd = ["gh", "api", "-i", "-X", method, url] + [a for h in headers for a in ("-H", h)]
    if data is not None:
        cmd += ["--input", "-"]
    r = subprocess.run(cmd, input=json.dumps(data) if data is not None else None, capture_output=True, text=True)
    head, _, body = r.stdout.replace("\r\n", "\n").partition("\n\n")
    lines = head.splitlines()
    m = re.match(r"HTTP/\S+ (\d{3})", lines[0] if lines else "")
    return int(m.group(1)) if m else 0, {k.strip().lower(): v.strip() for k, _, v in (l.partition(":") for l in lines[1:])}, body


def wait(seconds):
    time.sleep(seconds)


def gh(db, url: str):
    """GET with If-None-Match from the stored ETag: 304 → the stored body (no quota spent); 200 → UPSERT; a quota
    refusal → alert('quota') and None; any other answer → None (unknown: the step holds)."""
    row = db.execute("SELECT etag, body FROM gh WHERE url=?", (url,)).fetchone()
    status, h, body = transport("GET", url, headers=(f"If-None-Match: {row['etag']}",) if row and row["etag"] else ())
    if status == 304 and row:
        return json.loads(row["body"])
    if status == 200:
        db.execute("INSERT INTO gh(url, etag, status, body, at) VALUES (?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET etag=excluded.etag, status=excluded.status, body=excluded.body, at=excluded.at",
                   (url, h.get("etag"), status, body, now()))
        return json.loads(body)
    if status in (403, 429) and (h.get("x-ratelimit-remaining") == "0" or "rate limit" in body.lower()):
        alert(db, "quota", "github", f"refused {url}; reset {h.get('x-ratelimit-reset', '?')}")
    return None


def pr(db, T, ch, ours=()) -> None:
    """The PR's state and comments: the gh row (the Ledger reads it), finding rows for comments by others, and a landed
    row on the upstream base once merged (a squash or rebase merge is seen only here)."""
    p = gh(db, f"repos/{T.upstream}/pulls/{ch.pr}")
    if p is None:
        return
    if p.get("merged_at") and not db.execute("SELECT 1 FROM landed WHERE change=? AND target=?", (ch.slug, T.base)).fetchone():
        db.execute("INSERT INTO landed(change, target, sha, at) VALUES (?,?,?,?)", (ch.slug, T.base, p.get("merge_commit_sha") or p["head"]["sha"], now()))
        event(db, "landed", ch.slug, None, f"PR {T.upstream}#{ch.pr} merged")
    for url in (f"repos/{T.upstream}/issues/{ch.pr}/comments", f"repos/{T.upstream}/pulls/{ch.pr}/comments"):
        for c in gh(db, url) or []:
            if c["user"]["type"] == "Bot" or c["user"]["login"] in ours:
                continue
            if db.execute("INSERT OR IGNORE INTO finding(comment_id, repo, pr, author, body, url, seen_at, change) VALUES (?,?,?,?,?,?,?,?)",
                          (c["id"], T.upstream, ch.pr, c["user"]["login"], c["body"], c["html_url"], now(), ch.slug)).rowcount:
                event(db, "triage", ch.slug, None, f"#{ch.pr} comment {c['id']} by {c['user']['login']}: {c['body'][:200]!r}   → hd triage {c['id']} finding|ask|ack")


def checks(db, upstream, sha) -> list | None:
    """The latest check run per name at sha plus the commit statuses, as {name, status, conclusion}; None when unknown."""
    runs = gh(db, f"repos/{upstream}/commits/{sha}/check-runs?per_page=100")
    st = gh(db, f"repos/{upstream}/commits/{sha}/status")
    if runs is None or st is None:
        return None
    seen, out = set(), []
    for r in runs["check_runs"]:   # newest first
        if r["name"] not in seen:
            seen.add(r["name"])
            out.append({"name": r["name"], "status": r["status"], "conclusion": r["conclusion"]})
    for s in st["statuses"]:
        if s["context"] not in seen:
            seen.add(s["context"])
            out.append({"name": s["context"], "status": "completed" if s["state"] != "pending" else "in_progress", "conclusion": s["state"]})
    return out


def stacks(db, tracks) -> None:
    """A change's running stack (its stack row, mirrored from up.json) with no live run of the change is brought down:
    `track.sh down <slug>` in the scope hd-down-<slug>, once at a time (the scope's name)."""
    for s in db.execute("SELECT s.change FROM stack s WHERE NOT EXISTS (SELECT 1 FROM run r WHERE r.change=s.change AND r.ended_at IS NULL)").fetchall():
        unit = f"hd-down-{s['change']}"
        if subprocess.run(["systemctl", "--user", "is-active", "-q", unit + ".scope"]).returncode == 0:
            continue
        script = tracks_script(db, tracks, s["change"])
        if script:
            subprocess.Popen(["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit, "--", "bash", script, "down", s["change"]],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, HD_ROOT=ROOT), start_new_session=True)
            event(db, "down", s["change"], None, "its run ended with the stack up: track.sh down started")


def tracks_script(db, tracks, slug):
    row = db.execute("SELECT script FROM stack WHERE change=?", (slug,)).fetchone()
    return row["script"] if row and row["script"] and os.path.exists(row["script"]) else None
