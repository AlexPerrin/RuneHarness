"""The ledger: the one SQLite file every decision reads (docs/ARCHITECTURE.md §2).

Only this module opens the database. Observations (ref, landed, gh, stack) and commitments (submission, verdict,
answer, approval, publish_step) are rows written once by the actor that made them; decide.py reads them through
Ledger and never recomputes them from the world.
"""
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
DB = os.environ.get("HD_DB", os.path.join(STATE, "hd.db"))
RECORD = re.compile(r"^run (\d+): (submitted [0-9a-f]{7,40}|PASS|FAIL \d+ criteria|criteria agreed|filed \S+|ask|handoff)$")  # the hand-back line

SCHEMA_1 = """
CREATE TABLE change_state (
  slug        TEXT PRIMARY KEY,
  closed_at   TEXT, closed_words TEXT,
  folded_into TEXT REFERENCES change_state(slug)
);

CREATE TABLE run (
  id          INTEGER PRIMARY KEY,
  change      TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('dev','qa')),
  mode        TEXT NOT NULL CHECK (mode IN ('code','criteria','judge','plan')),
  input       TEXT NOT NULL,
  brief       TEXT NOT NULL,
  agent_id    TEXT UNIQUE,
  listed_at   TEXT NOT NULL, started_at TEXT, ended_at TEXT,
  end_kind    TEXT CHECK (end_kind IN ('handback','stop','close','console','handoff')),
  record      TEXT,
  usage_json  TEXT, transcript TEXT
);
CREATE UNIQUE INDEX run_live ON run(change) WHERE ended_at IS NULL;

CREATE TABLE session (
  id INTEGER PRIMARY KEY, pid INTEGER NOT NULL, pid_start INTEGER NOT NULL, session_id TEXT UNIQUE,
  definition TEXT NOT NULL,
  started_at TEXT NOT NULL,
  drain_at TEXT, drain_why TEXT,
  ended_at TEXT, end_kind TEXT CHECK (end_kind IN ('restart','exit','crash')),
  seen_event INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX session_live ON session(pid) WHERE ended_at IS NULL;

CREATE TABLE submission (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT NOT NULL,
  tree TEXT NOT NULL, tcommit TEXT NOT NULL, composite_json TEXT,
  run INTEGER REFERENCES run(id), at TEXT NOT NULL,
  UNIQUE (change, head)
);

CREATE TABLE criterion (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, rid TEXT NOT NULL,
  kind   TEXT NOT NULL CHECK (kind IN ('script','judge')),
  text   TEXT NOT NULL, cmd TEXT,
  source TEXT NOT NULL CHECK (source IN ('seed','accuracy','answer','finding','user')),
  source_id INTEGER,
  upstream_only INTEGER NOT NULL DEFAULT 0, waived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE (change, rid)
);
CREATE TABLE check_result (
  criterion_id INTEGER REFERENCES criterion(id), tree TEXT NOT NULL, ok INTEGER NOT NULL, note TEXT, at TEXT NOT NULL,
  PRIMARY KEY (criterion_id, tree)
);
CREATE TABLE verdict (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT NOT NULL,
  run INTEGER NOT NULL REFERENCES run(id), ok INTEGER NOT NULL,
  criteria_digest TEXT NOT NULL, at TEXT NOT NULL
);
CREATE TABLE verdict_row (
  verdict INTEGER REFERENCES verdict(id), criterion_id INTEGER REFERENCES criterion(id),
  result TEXT NOT NULL CHECK (result IN ('pass','fail','not-judged')), note TEXT,
  PRIMARY KEY (verdict, criterion_id)
);

CREATE TABLE job (
  kind TEXT NOT NULL CHECK (kind IN ('build','gate','deploy','ship','publish','test')),
  key  TEXT NOT NULL,
  change TEXT, ok INTEGER, detail TEXT,
  pid INTEGER, pid_start INTEGER, scope TEXT, log TEXT,
  started_at TEXT, ended_at TEXT, exit INTEGER,
  PRIMARY KEY (kind, key)
);
CREATE TABLE attempt (id INTEGER PRIMARY KEY, kind TEXT, key TEXT, cause TEXT, exit INTEGER, at TEXT);
CREATE TABLE step_log (id INTEGER PRIMARY KEY, change TEXT, script TEXT, step TEXT, started_at TEXT, done_at TEXT, detail TEXT);

CREATE TABLE ask (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, text TEXT NOT NULL,
  options_json TEXT NOT NULL, run INTEGER REFERENCES run(id), at TEXT NOT NULL
);
CREATE TABLE answer (
  ask INTEGER PRIMARY KEY REFERENCES ask(id), option TEXT NOT NULL, words TEXT, by TEXT NOT NULL, at TEXT NOT NULL
);

CREATE TABLE card (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT NOT NULL, pr INTEGER,
  steps_json TEXT NOT NULL, texts_json TEXT NOT NULL, digest TEXT NOT NULL, shown_at TEXT,
  UNIQUE (change, head, digest)
);
CREATE TABLE approval (card INTEGER PRIMARY KEY REFERENCES card(id), at TEXT NOT NULL, spent_at TEXT, spent_why TEXT);
CREATE TABLE publish_step (
  card INTEGER REFERENCES card(id), n INTEGER, name TEXT NOT NULL, done_at TEXT, result_json TEXT,
  PRIMARY KEY (card, n)
);
CREATE TABLE hold (id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT, why TEXT, at TEXT NOT NULL, lifted_at TEXT);

CREATE TABLE finding (
  comment_id INTEGER PRIMARY KEY, repo TEXT, pr INTEGER, author TEXT, body TEXT, url TEXT, seen_at TEXT,
  triage TEXT CHECK (triage IN ('finding','ask','ack')), triaged_at TEXT,
  change TEXT, criterion_id INTEGER REFERENCES criterion(id)
);

CREATE TABLE ref    (repo TEXT, name TEXT, sha TEXT NOT NULL, seen_at TEXT, PRIMARY KEY (repo, name));
CREATE TABLE landed (change TEXT, target TEXT, sha TEXT, at TEXT, PRIMARY KEY (change, target));
CREATE TABLE gh     (url TEXT PRIMARY KEY, etag TEXT, status INTEGER, body TEXT, at TEXT);
CREATE TABLE stack  (change TEXT PRIMARY KEY, script TEXT, containers_json TEXT, desktops_json TEXT,
                     token TEXT, modulus TEXT, started_at TEXT);
CREATE TABLE measure (goal TEXT, tree TEXT, value REAL, report TEXT, at TEXT, PRIMARY KEY (goal, tree));

CREATE TABLE event (id INTEGER PRIMARY KEY, at TEXT NOT NULL, kind TEXT NOT NULL, change TEXT, run INTEGER, detail TEXT);
CREATE INDEX event_change ON event(change, id);

CREATE TABLE alert (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('attempts','run-lost','runs-per-head','ask-stale','denied','fault','ci-runner','kpi','pin-conflict','quota')),
  subject TEXT NOT NULL,
  detail TEXT NOT NULL,
  first_at TEXT NOT NULL, last_at TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 1,
  disposition TEXT CHECK (disposition IN ('filed','dismissed')), change TEXT, why TEXT, by TEXT, at TEXT,
  UNIQUE (kind, subject)
);
"""

SCHEMA_2 = "ALTER TABLE ref ADD COLUMN tree TEXT;"   # a ref's tree: the key of a deploy of staging, read without git
SCHEMA_3 = "CREATE TABLE text (change TEXT, name TEXT, sha TEXT NOT NULL, body TEXT NOT NULL, at TEXT, PRIMARY KEY (change, name));"  # evidence/<slug>/pr-*.md observed

SCHEMA_4 = """  -- job kinds gain measure (a goal's script); SQLite rebuilds the table for a new CHECK
CREATE TABLE job_4 (
  kind TEXT NOT NULL CHECK (kind IN ('build','gate','deploy','ship','publish','test','measure')),
  key  TEXT NOT NULL, change TEXT, ok INTEGER, detail TEXT, pid INTEGER, pid_start INTEGER, scope TEXT, log TEXT,
  started_at TEXT, ended_at TEXT, exit INTEGER, PRIMARY KEY (kind, key));
INSERT INTO job_4 SELECT * FROM job; DROP TABLE job; ALTER TABLE job_4 RENAME TO job;"""

# One function per schema version; migrate() applies those above PRAGMA user_version in order, each in a transaction.
SCHEMA_5 = "ALTER TABLE session ADD COLUMN role TEXT NOT NULL DEFAULT 'orchestrator' CHECK (role IN ('orchestrator','driver'));"   # the user's chat is the driver (§12)

SCHEMA_6 = """  -- retention (docs/ARCHITECTURE.md §2): every build artifact's owners; the free space of the build disks; alert kind disk
CREATE TABLE artifact (
  kind  TEXT NOT NULL CHECK (kind IN ('image','volume','container','worktree','dir')),
  key   TEXT NOT NULL,    -- the docker name or the absolute path
  owner TEXT NOT NULL,    -- <slug> | <slug>@<T> | job:<kind>:<key> | run:<id>: released once no owner of (kind, key) is live
  at    TEXT NOT NULL,
  PRIMARY KEY (kind, key, owner));
CREATE TABLE disk (path TEXT PRIMARY KEY, free INTEGER NOT NULL, at TEXT NOT NULL);
CREATE TABLE alert_6 (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('attempts','run-lost','runs-per-head','ask-stale','denied','fault','ci-runner','kpi','pin-conflict','quota','disk')),
  subject TEXT NOT NULL, detail TEXT NOT NULL,
  first_at TEXT NOT NULL, last_at TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 1,
  disposition TEXT CHECK (disposition IN ('filed','dismissed')), change TEXT, why TEXT, by TEXT, at TEXT,
  UNIQUE (kind, subject));
INSERT INTO alert_6 SELECT * FROM alert; DROP TABLE alert; ALTER TABLE alert_6 RENAME TO alert;"""

SCHEMA_7 = "ALTER TABLE stack ADD COLUMN live INTEGER NOT NULL DEFAULT 0;"   # the stack plays on the live test server (a mobile, live-desktop): no deploy under it

SCHEMA_8 = """  -- run end_kind gains withdrawn: a listing its change no longer plans, ended before it started (frees its slot, parks nothing)
CREATE TABLE run_8 (
  id          INTEGER PRIMARY KEY,
  change      TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('dev','qa')),
  mode        TEXT NOT NULL CHECK (mode IN ('code','criteria','judge','plan')),
  input       TEXT NOT NULL,
  brief       TEXT NOT NULL,
  agent_id    TEXT UNIQUE,
  listed_at   TEXT NOT NULL, started_at TEXT, ended_at TEXT,
  end_kind    TEXT CHECK (end_kind IN ('handback','stop','close','console','handoff','withdrawn')),
  record      TEXT,
  usage_json  TEXT, transcript TEXT
);
INSERT INTO run_8 SELECT * FROM run; DROP TABLE run; ALTER TABLE run_8 RENAME TO run;
CREATE UNIQUE INDEX run_live ON run(change) WHERE ended_at IS NULL;"""

SCHEMA_9 = "ALTER TABLE submission ADD COLUMN head_tree TEXT;"   # the head's own tree: the PR's gate (CI on base) tests it, the candidate's tree does not carry it (decide.key)

MIGRATIONS = [SCHEMA_1, SCHEMA_2, SCHEMA_3, SCHEMA_4, SCHEMA_5, SCHEMA_6, SCHEMA_7, SCHEMA_8, SCHEMA_9]


OWNER = "AlexPerrin"   # our GitHub login: the fork, the PR heads' owner, the comments that are ours


def pulls_on(upstream, branch) -> str:
    return f"repos/{upstream}/pulls?head={OWNER}:{branch}&state=all"


def submit(db, slug, head, tree, tcommit, composite, run, head_tree=None) -> bool:
    """Record a head's candidate; the same head submitted again with another candidate (a dep's head moved, the base
    moved under it) replaces it: the candidate is a function of base, deps and head at submission. True when recorded."""
    old = db.execute("SELECT tree FROM submission WHERE change=? AND head=?", (slug, head)).fetchone()
    if old and old["tree"] == tree:   # the dev stands by this head: criteria added since are for this submission to answer
        db.execute("UPDATE submission SET at=?, run=coalesce(?, run) WHERE change=? AND head=?", (now(), run, slug, head))
        return False
    db.execute("""INSERT INTO submission(change, head, tree, tcommit, composite_json, run, at, head_tree) VALUES (?,?,?,?,?,?,?,?)
                  ON CONFLICT(change, head) DO UPDATE SET tree=excluded.tree, tcommit=excluded.tcommit,
                  composite_json=excluded.composite_json, run=excluded.run, at=excluded.at, head_tree=excluded.head_tree""",
               (slug, head, tree, tcommit, composite, run, now(), head_tree))
    return True


def regate_failed(db, tree) -> bool:
    """The same head submitted again after its tree's gate failed: what failed was outside the tree (evidence/<slug>/
    replay.md, a tool), so the gate's results go and it runs again. A passed or running gate stays. True when cleared."""
    k = tree + "%"   # a key is T:<recipe>, T = the tree with its composite suffix (decide.built), so the prefix is the tree alone
    if not db.execute("SELECT 1 FROM job WHERE kind='gate' AND key LIKE ? AND ok=0 AND ended_at IS NOT NULL", (k,)).fetchone():
        return False
    db.execute("DELETE FROM job WHERE kind='gate' AND key LIKE ? AND ended_at IS NOT NULL", (k,))
    db.execute("DELETE FROM attempt WHERE kind='gate' AND key LIKE ?", (k,))
    db.execute("DELETE FROM check_result WHERE tree=?", (tree,))
    return True


def rerun(db, slug, kind, key, detail) -> None:
    """A failed build, gate or ship once more at the same key (decide.dev_due): its result and attempts go, the event
    'rerun' keeps the first failure for the comparison with the second."""
    db.execute("DELETE FROM job WHERE kind=? AND key=? AND ended_at IS NOT NULL", (kind, key))
    db.execute("DELETE FROM attempt WHERE kind=? AND key=?", (kind, key))
    if kind == "gate":
        db.execute("DELETE FROM check_result WHERE tree=?", (key.split(":")[0].split("_")[0],))
    event(db, "rerun", slug, None, f"{kind} {key} {detail or ''}")


def own(db, kind: str, key: str, owner: str) -> None:
    """An artifact's owner row (the track scripts through `hd own`, act for the clones it makes). A path is refused
    outside the places builds write (a worktree under .worktrees/, a dir there or under state/): a release removes it."""
    if kind in ("worktree", "dir") and not (os.path.isabs(key) and os.path.normpath(key) == key and ("/.worktrees/" in key or (kind == "dir" and key.startswith(STATE + "/")))):
        raise ValueError(f"{kind} {key}: not under a .worktrees/ or state/ directory")
    db.execute("INSERT OR IGNORE INTO artifact(kind, key, owner, at) VALUES (?,?,?,?)", (kind, key, owner, now()))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(*parts) -> str:
    """A short stable digest of any JSON-able parts: run inputs, card digests, criteria sets."""
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:12]


def connect(path: str = None) -> sqlite3.Connection:
    """Open the ledger (WAL, foreign keys on), creating and migrating it when needed."""
    path = path or DB
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    db = sqlite3.connect(path, isolation_level=None, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    migrate(db)
    return db


def migrate(db: sqlite3.Connection) -> int:
    """Apply every migration above the file's user_version; returns the version reached."""
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version < len(MIGRATIONS):
        db.execute("PRAGMA foreign_keys=OFF")   # a table rebuild drops a referenced table; the references are checked after
    for n, sql in enumerate(MIGRATIONS[version:], start=version + 1):
        db.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version={n};\nCOMMIT;")  # one transaction per migration
        version = n
    if db.execute("PRAGMA foreign_key_check").fetchone():
        raise sqlite3.IntegrityError("migration left a broken reference")
    db.execute("PRAGMA foreign_keys=ON")
    return version


def event(db, kind: str, change=None, run=None, detail=None) -> int:
    return db.execute("INSERT INTO event(at, kind, change, run, detail) VALUES (?,?,?,?,?)",
                      (now(), kind, change, run, detail)).lastrowid


def alert(db, kind: str, subject: str, detail: str) -> None:
    """UPSERT an alert on (kind, subject): a recurrence counts up and refreshes last_at and detail."""
    db.execute("""INSERT INTO alert(kind, subject, detail, first_at, last_at) VALUES (?,?,?,?,?)
                  ON CONFLICT(kind, subject) DO UPDATE SET count=count+1, last_at=excluded.last_at, detail=excluded.detail""",
               (kind, subject, detail, now(), now()))


class Ledger:
    """Read-only view of the store for decide.py: one method per fact the guards ask (ARCHITECTURE §3).

    Every method is a single query; none runs a subprocess or reads the clock.
    """

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def one(self, sql, *args):
        return self.db.execute(sql, args).fetchone()

    def all(self, sql, *args):
        return self.db.execute(sql, args).fetchall()

    def closed(self, slug):
        return self.one("SELECT closed_at, folded_into FROM change_state WHERE slug=? AND (closed_at IS NOT NULL OR folded_into IS NOT NULL)", slug)

    def ref(self, repo, name):
        row = self.one("SELECT sha FROM ref WHERE repo=? AND name=?", repo, name)
        return row["sha"] if row else None

    def ref_tree(self, repo, name):
        row = self.one("SELECT tree FROM ref WHERE repo=? AND name=?", repo, name)
        return row["tree"] if row else None

    def landed(self, slug, target):
        return self.one("SELECT sha FROM landed WHERE change=? AND target=? AND at >= coalesce((SELECT max(s.at) FROM submission s WHERE s.change=landed.change), '')", slug, target)   # void once a newer head is submitted (M1)

    def open_ask(self, slug):
        return self.one("SELECT a.* FROM ask a LEFT JOIN answer n ON n.ask=a.id WHERE a.change=? AND n.ask IS NULL", slug)

    def answers_since(self, slug, at):
        return self.all("SELECT n.* FROM answer n JOIN ask a ON a.id=n.ask WHERE a.change=? AND n.at>? ORDER BY n.at", slug, at)

    def appended_since(self, slug, at):
        """The sections hd new --on appended to the change after `at`: the user's word on the change itself."""
        return self.all("SELECT * FROM event WHERE change=? AND kind='new' AND detail LIKE 'appended:%' AND at>? ORDER BY id", slug, at)

    def submission(self, slug, head):
        s = self.one("SELECT * FROM submission WHERE change=? AND head=?", slug, head)
        return self.following(s) if s else None

    def following(self, s):
        """A staged candidate's composite (every entry carries deps, hd.dep_inputs) follows the libraries' staging: each
        library whose merged-in dep heads have all landed on staging takes staging's head; a dep still unpublished pins it."""
        comp = json.loads(s["composite_json"] or "{}")
        if not comp or any("deps" not in v for v in comp.values()):
            return s   # shortcut: a staged candidate submitted with no library staging has no marker and stays as built; store the marker on an empty composite if one appears
        try:
            live = json.loads(self.staging_composite("refs/heads/staging") or "{}")
        except ValueError:
            return s   # two library heads on staging: the deploy's fault, the candidate keeps what it was built with
        for lib, v in live.items():
            if all(self.landed(d, "refs/heads/staging") for d in comp.get(lib, {}).get("deps", [])):
                comp[lib] = dict(v, deps=[])
        return dict(s, composite_json=json.dumps(comp))

    def criteria(self, slug, kind=None):
        sql = "SELECT * FROM criterion WHERE change=? AND waived=0" + (" AND kind=?" if kind else "") + " ORDER BY id"
        return self.all(sql, slug, *([kind] if kind else []))

    def criteria_after(self, slug, at):
        return self.one("SELECT count(*) n FROM criterion WHERE change=? AND waived=0 AND created_at>?", slug, at)["n"]

    def check_results(self, tree):
        return {r["criterion_id"]: r for r in self.all("SELECT * FROM check_result WHERE tree=?", tree)}

    def staging_composite(self, staging) -> str | None:
        """The library heads the test server runs with: a library's own staging (its checked changes merged there,
        act.stage), else the heads staging's server changes were built with (a staging build has no dependency on its own,
        and a head that needs an unpublished Central builds only with it). Two of those heads are a conflict to merge first."""
        comp = {}
        for lib in ("central", "filestore"):
            r = self.one("SELECT sha, tree FROM ref WHERE repo=? AND name=?", lib, staging)
            if r:
                comp[lib] = {"head": r["sha"], "tree": r["tree"]}
        own = set(comp)
        for r in self.all("SELECT change FROM landed WHERE target=?", staging):
            s = self.one("SELECT composite_json FROM submission WHERE change=? ORDER BY id DESC LIMIT 1", r["change"])
            if self.closed(r["change"]) or not s or not s["composite_json"]:
                continue
            for lib, v in json.loads(s["composite_json"]).items():
                if lib not in own and comp.setdefault(lib, v)["head"] != v["head"]:
                    raise ValueError(f"staging holds two {lib} heads, {comp[lib]['head'][:7]} and {v['head'][:7]}: its deploy needs them merged")
        return json.dumps(comp) if comp else None

    def last_verdict(self, slug, head):
        return self.one("SELECT * FROM verdict WHERE change=? AND head=? ORDER BY id DESC LIMIT 1", slug, head)

    def job(self, kind, key):
        return self.one("SELECT * FROM job WHERE kind=? AND key=?", kind, key)

    def jobs_in_flight(self, kind, prefix=""):
        return self.all("SELECT * FROM job WHERE kind=? AND key LIKE ? AND pid IS NOT NULL AND ended_at IS NULL", kind, prefix + "%")

    def attempts(self, kind, key, since=""):
        """Starts of a key without a result since `since` (the harness's last landing: a fix that landed lets a job run again)."""
        return self.one("SELECT count(*) n FROM attempt WHERE kind=? AND key=? AND at>?", kind, key, since)["n"]

    def harness_shipped_at(self, harness):
        """When a harness change last shipped (a fix landed), not any commit of its branch."""
        row = self.one("SELECT max(ended_at) t FROM job WHERE kind='ship' AND ok=1 AND key LIKE ?", harness.base + ":%")
        return row["t"] or ""

    def live_run(self, slug):
        return self.one("SELECT * FROM run WHERE change=? AND ended_at IS NULL", slug)

    def live_users(self):
        """Changes playing on the live test server now: a stack row marked live whose change has a live run or a job in flight."""
        return [r["change"] for r in self.all("""SELECT s.change FROM stack s WHERE s.live AND (
            EXISTS (SELECT 1 FROM run r WHERE r.change=s.change AND r.ended_at IS NULL)
            OR EXISTS (SELECT 1 FROM job j WHERE j.change=s.change AND j.pid IS NOT NULL AND j.ended_at IS NULL)) ORDER BY s.change""")]

    def live_runs(self):
        return self.all("SELECT * FROM run WHERE ended_at IS NULL ORDER BY id")

    def last_run(self, slug):
        return self.one("SELECT * FROM run WHERE change=? ORDER BY id DESC LIMIT 1", slug)

    def run_for(self, slug, input):
        return self.one("SELECT * FROM run WHERE change=? AND input=? ORDER BY id DESC LIMIT 1", slug, input)

    def runs_with_record(self, slug, mode, record):
        return self.one("SELECT * FROM run WHERE change=? AND mode=? AND record LIKE ? ORDER BY id DESC LIMIT 1", slug, mode, "%" + record)

    def card(self, slug, head, digest):
        return self.one("SELECT * FROM card WHERE change=? AND head=? AND digest=?", slug, head, digest)

    def approval(self, card_id):
        return self.one("SELECT * FROM approval WHERE card=? AND spent_at IS NULL", card_id)

    def undone_steps(self, card_id):
        return self.all("SELECT * FROM publish_step WHERE card=? AND done_at IS NULL ORDER BY n", card_id)

    def hold(self, slug, head):
        return self.one("SELECT * FROM hold WHERE change=? AND lifted_at IS NULL AND (head IS NULL OR head=?)", slug, head)

    def pr(self, upstream, number):
        """The PR as last observed: number, state, draft, head, title, body, merged_at; None before the first read."""
        row = self.one("SELECT body FROM gh WHERE url=?", f"repos/{upstream}/pulls/{number}")
        if not row:
            return None
        p = json.loads(row["body"])
        return {"number": p["number"], "state": p["state"], "draft": p["draft"], "head": p["head"]["sha"], "title": p["title"],
                "body": p["body"] or "", "merged_at": p["merged_at"], "merge_commit": p.get("merge_commit_sha")}

    def pr_on_branch(self, upstream, branch):
        """The feature's PR, observed by its branch (observe.prs): the open one, else the latest; None before any."""
        row = self.one("SELECT body FROM gh WHERE url=?", pulls_on(upstream, branch))
        ps = json.loads(row["body"]) if row and row["body"] else []
        p = next((p for p in ps if p["state"] == "open"), ps[0] if ps else None)
        return p and (self.pr(upstream, p["number"]) or {"number": p["number"], "state": p["state"], "draft": p["draft"], "head": p["head"]["sha"],
                                                          "title": p["title"], "body": p["body"] or "", "merged_at": p.get("merged_at"), "merge_commit": None})

    def texts(self, slug):
        return {r["name"]: r["body"] for r in self.all("SELECT name, body FROM text WHERE change=?", slug)}

    def findings(self, slug):
        return self.all("SELECT * FROM finding WHERE change=? AND triage='finding' ORDER BY comment_id", slug)

    def measure(self, goal, tree=None):
        if tree:
            return self.one("SELECT * FROM measure WHERE goal=? AND tree=?", goal, tree)
        return self.one("SELECT * FROM measure WHERE goal=? ORDER BY at DESC LIMIT 1", goal)

    def latest_card(self, slug):
        return self.one("SELECT * FROM card WHERE change=? ORDER BY id DESC LIMIT 1", slug)

    def rerun(self, slug, kind, key):
        """The first failure's detail of a rerun of (kind, key), or None when it never ran again."""
        p = f"{kind} {key} "
        r = self.one("SELECT detail FROM event WHERE change=? AND kind='rerun' AND substr(detail, 1, ?)=? ORDER BY id DESC LIMIT 1", slug, len(p), p)
        return r["detail"][len(p):] if r else None

    def last_event(self, slug, kind=None):
        sql = "SELECT * FROM event WHERE change=?" + (" AND kind=?" if kind else "") + " ORDER BY id DESC LIMIT 1"
        return self.one(sql, slug, *([kind] if kind else []))

    def artifacts(self):
        """(kind, key, [owners]) of every recorded artifact."""
        return [(r["kind"], r["key"], r["owners"].split("\n")) for r in
                self.all("SELECT kind, key, group_concat(owner, char(10)) owners FROM artifact GROUP BY kind, key ORDER BY kind, key")]

    def disk_below(self, gb):
        return self.all("SELECT * FROM disk WHERE free < ? ORDER BY path", gb * 10**9)

    def live_session(self):
        return self.one("SELECT * FROM session WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1")
