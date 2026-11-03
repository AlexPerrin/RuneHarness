"""world → ledger (docs/ARCHITECTURE.md §5). Each function writes observation rows bound to what it observed
(sha, pid, comment id) and nothing else."""
import os
import re
import subprocess
from pathlib import Path

from store import alert, event, now


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
    out = subprocess.run(["git", "-C", T.path, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/remotes"],
                         capture_output=True, text=True).stdout
    have = {r["name"]: r["sha"] for r in db.execute("SELECT name, sha FROM ref WHERE repo=?", (T.name,))}
    moved = set()
    for line in out.splitlines():
        sha, name = line.split()
        if have.get(name) != sha:
            moved.add(name)
            db.execute("INSERT INTO ref(repo, name, sha, seen_at) VALUES (?,?,?,?) ON CONFLICT(repo, name) DO UPDATE SET sha=excluded.sha, seen_at=excluded.seen_at",
                       (T.name, name, sha, now()))
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


# --- GitHub and docker: phase 2 ----------------------------------------------------------------------------------

def gh(db, url: str):
    """GET with If-None-Match from gh.etag; 304 → the stored body; 200 → UPSERT; quota → alert('quota'), None."""
    raise NotImplementedError  # shortcut: phase 2 (publish)


def docker(db) -> set:
    raise NotImplementedError  # shortcut: phase 2 (stack recovery)
