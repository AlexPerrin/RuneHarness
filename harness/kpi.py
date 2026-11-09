"""hd kpi: the harness goal's numbers (docs/PROBLEM.md §6), one query per metric. Targets in docs/V9-PROPOSAL.md §2."""
import json
import os
import re
import statistics

QUERIES = [
    ("runs per change (median)", "≤5",
     "SELECT n FROM (SELECT count(*) n FROM run GROUP BY change ORDER BY n) LIMIT 1 OFFSET (SELECT (count(DISTINCT change)-1)/2 FROM run)"),
    ("runs ended without own record", "<5%",
     "SELECT printf('%d of %d', sum(end_kind IN ('console','stop') AND record IS NULL), count(*)) FROM run WHERE ended_at IS NOT NULL"),
    ("successor runs", "0",
     "SELECT count(*) FROM run r WHERE EXISTS (SELECT 1 FROM run p WHERE p.change=r.change AND p.id<r.id AND p.input=r.input AND p.end_kind IN ('console','handoff'))"),
    ("dev runs that resubmitted the same head", "0",
     "SELECT printf('%d of %d', sum(NOT EXISTS (SELECT 1 FROM event e WHERE e.kind='submitted' AND e.run=r.id)), count(*)) FROM run r WHERE r.role='dev' AND r.record LIKE '%: submitted %'"),   # hd submit's 'submitted' event marks a new head or candidate
    ("harness share of runs", "<15%",
     "SELECT printf('%d of %d', sum(change IN (SELECT value FROM json_each(:harness))), count(*)) FROM run"),
    ("jobs per tree (build, gate)", "1.0",
     "SELECT printf('%.2f', 1.0*count(*)/max(1, count(DISTINCT substr(key,1,40)))) FROM job WHERE kind IN ('build','gate')"),
    ("ships per change > 1", "0",
     "SELECT count(*) FROM (SELECT change FROM job WHERE kind='ship' AND ok=1 GROUP BY change HAVING count(*)>1)"),
    ("cards withdrawn on an unchanged tree", "0",
     "SELECT count(*) FROM (SELECT c.change, s.tree FROM card c JOIN submission s ON s.change=c.change AND s.head=c.head GROUP BY c.change, s.tree HAVING count(*)>1)"),
    ("publishes not resumed", "0",
     "SELECT count(*) FROM approval a WHERE a.spent_at IS NULL AND EXISTS (SELECT 1 FROM publish_step p WHERE p.card=a.card AND p.done_at IS NULL) AND NOT EXISTS (SELECT 1 FROM job j WHERE j.kind='publish' AND j.key=CAST(a.card AS TEXT) AND j.pid IS NOT NULL AND j.ended_at IS NULL)"),
    ("wrong hook denials (dismissed)", "0", "SELECT count(*) FROM alert WHERE kind='denied' AND disposition='dismissed'"),
    ("open alerts", "0", "SELECT count(*) FROM alert WHERE disposition IS NULL"),
    ("artifacts of closed changes", "0",
     "SELECT count(*) FROM artifact WHERE substr(owner, 1, instr(owner || '@', '@') - 1) IN (SELECT slug FROM change_state WHERE closed_at IS NOT NULL)"),
    ("images recorded", "≤ open heads + staging",
     "SELECT count(DISTINCT key) FROM artifact WHERE kind='image'"),
    ("free space (GB)", "≥ hd.yaml free",
     "SELECT group_concat(path || ' ' || (free / 1000000000), ', ') FROM disk"),
    ("peak context p90 (tokens)", "≤200k",
     "SELECT coalesce(json_extract(usage_json,'$.context_tokens'),0) FROM run WHERE usage_json IS NOT NULL ORDER BY 1 LIMIT 1 OFFSET (SELECT max(0, count(*)*9/10-1) FROM run WHERE usage_json IS NOT NULL)"),
]


EDITS = ("Edit", "Write", "NotebookEdit")
BASH_WRITE = re.compile(r"\bsed\s+(-\w+\s+)*-i|\bcat\s+>|<<-?\s*['\"]?\w+['\"]?\s*>\s*\S|>\s*\S+\s*<<|\.write\(|\btee\b")
RULES = re.compile(r"state/briefs/|harness/changes/|track\.md|\.claude/agents/|SKILL\.md")
SHOW = re.compile(r"\bhd(\.py)?\s+show\b")
SEARCH = {"grep", "rg", "find", "fd", "ag"}
READ = {"cat", "sed", "head", "tail", "ls", "wc", "less", "tree", "awk", "nl", "stat", "diff"}
CATS = ("search", "read", "show", "git", "brief", "other")
TRACKS = ("fork", "client", "central", "harness")


def category(name, inp) -> str:
    """One tool call's category (docs/V9-BRIEF.md method): brief and rules, `hd show`, search, read, git, other."""
    text = inp.get("command", "") if name == "Bash" else str(inp.get("file_path") or inp.get("path") or "")
    if name in ("Read", "Bash") and RULES.search(text):
        return "brief"
    if name in ("Grep", "Glob"):
        return "search"
    if name == "Read":
        return "read"
    if name != "Bash":
        return "other"
    if SHOW.search(text):
        return "show"
    for seg in re.split(r"&&|\|\||;|\n", text):   # the first command past the cd/export prefix names the call
        w = seg.split()
        if w and w[0] not in ("cd", "export", "set"):
            w = os.path.basename(w[0])
            return "search" if w in SEARCH else "read" if w in READ else "git" if w == "git" else "other"
    return "other"


def is_edit(name, inp) -> bool:
    return name in EDITS or name == "Bash" and bool(BASH_WRITE.search(inp.get("command", "").split("\n")[0]))


def measure(path):
    """A run's orientation from its transcript: calls before the first edit (None without one), by category, the context
    tokens at that call, and its `hd show` calls over the whole run; None without a readable transcript."""
    m = {"calls": None, **{c: 0 for c in CATS}, "tokens": None, "shows": 0}
    try:
        f = open(path, errors="replace")
    except OSError:
        return None
    with f:
        for line in f:
            try:
                msg = json.loads(line).get("message", {}) if '"tool_use"' in line else {}
            except ValueError:   # a line cut by a live write
                continue
            for b in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                name, inp = b.get("name"), b.get("input") or {}
                c = category(name, inp)
                m["shows"] += c == "show"
                if m["calls"] is not None:
                    continue
                if is_edit(name, inp):
                    m["calls"] = sum(m[k] for k in CATS)
                    u = msg.get("usage") or {}
                    m["tokens"] = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                else:
                    m[c] += 1
    return m


def first_edit(db):
    """{track: [measure]} over the ended dev code runs: the one recorded at the run's end, else read from its transcript."""
    track = {c.slug: c.track for c in __import__("act").changes()}
    out = {}
    for r in db.execute("SELECT change, usage_json, transcript FROM run WHERE role='dev' AND mode='code' AND ended_at IS NOT NULL"):
        m = json.loads(r["usage_json"] or "{}").get("first_edit") or (measure(r["transcript"]) if r["transcript"] else None)
        if m:
            pre = r["change"].split("-")[0]   # a change whose definition is gone: its track by its slug's prefix
            out.setdefault(track.get(r["change"]) or {"h": "harness"}.get(pre, pre if pre in TRACKS else "?"), []).append(m)
    return out


def first_edit_rows(db) -> list:
    """KPIs 1-5 of the first edit per track: calls (median/mean), mean calls by category, tokens (median/mean), the
    search-or-read share, the runs calling `hd show` after their brief and how often."""
    med = lambda xs: statistics.median(xs) if xs else "-"
    avg = lambda xs: round(statistics.mean(xs), 1) if xs else "-"
    rows, data = [], first_edit(db)
    for t in TRACKS + tuple(sorted(set(data) - set(TRACKS))):
        ms = data.get(t, [])
        e = [m for m in ms if m["calls"] is not None]
        calls, tok = [m["calls"] for m in e], [m["tokens"] for m in e if m["tokens"] is not None]
        cats = " ".join(f"{c} {avg([m[c] for m in e])}" for c in CATS)
        share = f"{100 * sum(m['search'] + m['read'] for m in e) // max(1, sum(calls))}%"
        shows = [m["shows"] for m in ms if m["shows"]]
        rows += [f"first edit {t}: {len(e)} of {len(ms)} runs; calls median {med(calls)} mean {avg(calls)} (target ≤10); {cats}",
                 f"  tokens median {med(tok)} mean {avg(tok)}; search or read {share}; hd show in {len(shows)} of {len(ms)} runs, mean {avg(shows)}"]
    return rows


def feature_rows(db, changes) -> list:
    """Per feature (the user's PR bundle): the runs of its member changes and its packages, and its cards."""
    by = {}
    for c in changes:
        if c.feature:
            by.setdefault(c.feature, []).append(c.slug)
    rows = []
    for f, slugs in sorted(by.items()):
        q = ",".join("?" * len(slugs))
        runs = db.execute(f"SELECT count(*) FROM run WHERE change IN ({q}) AND end_kind IS NOT 'withdrawn'", slugs).fetchone()[0]
        cards = db.execute("SELECT count(*) FROM card WHERE change=?", (f,)).fetchone()[0]
        rows.append(f"feature {f}: {runs} runs over {len(slugs)} changes and packages, {cards} cards")
    return rows


def report(db) -> str:
    import act
    harness = json.dumps([c.slug for c in act.changes() if c.track == "harness"])
    out = []
    for name, target, sql in QUERIES:
        row = db.execute(sql, {"harness": harness} if ":harness" in sql else {}).fetchone()
        out.append(f"{name:<40} {str(row[0]) if row else '-':<12} target {target}")
    out += first_edit_rows(db) + feature_rows(db, act.changes())
    return "\n".join(out)
