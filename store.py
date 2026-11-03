"""The ledger: the one SQLite file every decision reads (docs/V9-PROPOSAL.md §3.2).

Only this module opens the database. Observations (ref, gh, landed, stack) and commitments (handover, verdict,
answer, approval, carry_step) are rows written once by the actor that made them; decide.py reads them through
Ledger and never recomputes them from the world.
"""
import os
import sqlite3

DB = os.environ.get("HD_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "hd.db"))

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
  mode        TEXT NOT NULL CHECK (mode IN ('code','contract','judge','plan')),
  input       TEXT NOT NULL,
  brief       TEXT NOT NULL,
  agent_id    TEXT UNIQUE,
  listed_at   TEXT NOT NULL, started_at TEXT, ended_at TEXT,
  end_kind    TEXT CHECK (end_kind IN ('handback','stop','close','console','handoff')),
  record      TEXT,
  usage_json  TEXT, transcript TEXT
);
CREATE UNIQUE INDEX run_live ON run(change) WHERE ended_at IS NULL;

CREATE TABLE handover (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT NOT NULL,
  tree TEXT NOT NULL, tcommit TEXT NOT NULL, central TEXT, tools_json TEXT,
  limits_json TEXT NOT NULL, run INTEGER REFERENCES run(id), at TEXT NOT NULL,
  UNIQUE (change, head)
);

CREATE TABLE row (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, rid TEXT NOT NULL,
  kind   TEXT NOT NULL CHECK (kind IN ('check','gate','judge')),
  text   TEXT NOT NULL, cmd TEXT,
  source TEXT NOT NULL CHECK (source IN ('seed','accuracy','answer','finding','user')),
  source_id INTEGER,
  upstream_only INTEGER NOT NULL DEFAULT 0, waived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE (change, rid)
);
CREATE TABLE row_result (
  row_id INTEGER REFERENCES row(id), tree TEXT NOT NULL, ok INTEGER NOT NULL, note TEXT, at TEXT NOT NULL,
  PRIMARY KEY (row_id, tree)
);
CREATE TABLE verdict (
  id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT NOT NULL,
  run INTEGER NOT NULL REFERENCES run(id), ok INTEGER NOT NULL,
  rows_digest TEXT NOT NULL, at TEXT NOT NULL
);
CREATE TABLE verdict_row (
  verdict INTEGER REFERENCES verdict(id), row_id INTEGER REFERENCES row(id),
  result TEXT NOT NULL CHECK (result IN ('pass','fail','not-judged')), note TEXT,
  PRIMARY KEY (verdict, row_id)
);

CREATE TABLE artefact (
  kind TEXT NOT NULL CHECK (kind IN ('build','gate','deploy','ship','test')),
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
CREATE TABLE carry_step (
  card INTEGER REFERENCES card(id), n INTEGER, name TEXT NOT NULL, done_at TEXT, result_json TEXT,
  PRIMARY KEY (card, n)
);
CREATE TABLE hold (id INTEGER PRIMARY KEY, change TEXT NOT NULL, head TEXT, why TEXT, at TEXT NOT NULL, lifted_at TEXT);

CREATE TABLE finding (
  comment_id INTEGER PRIMARY KEY, repo TEXT, pr INTEGER, author TEXT, body TEXT, url TEXT, seen_at TEXT,
  triage TEXT CHECK (triage IN ('finding','ask','ack')), triaged_at TEXT,
  change TEXT, row_id INTEGER REFERENCES row(id)
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

# One function per schema version; migrate() applies those above PRAGMA user_version in order, each in a transaction.
MIGRATIONS = [SCHEMA_1]


def connect(path: str = DB) -> sqlite3.Connection:
    """Open the ledger (WAL, foreign keys on), creating and migrating it when needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    migrate(db)
    return db


def migrate(db: sqlite3.Connection) -> int:
    """Apply every migration above the file's user_version; returns the version reached."""
    version = db.execute("PRAGMA user_version").fetchone()[0]
    for n, sql in enumerate(MIGRATIONS[version:], start=version + 1):
        db.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version={n};\nCOMMIT;")  # one transaction per migration
        version = n
    return version


class Ledger:
    """Read-only view of the store for decide.py: one method per fact the guards ask (§3.3).

    Every method is a single query; none runs a subprocess or reads the clock.
    """

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def closed(self, slug: str):
        return self.db.execute("SELECT closed_at, folded_into FROM change_state WHERE slug=?", (slug,)).fetchone()

    def ref(self, repo: str, name: str):
        row = self.db.execute("SELECT sha FROM ref WHERE repo=? AND name=?", (repo, name)).fetchone()
        return row["sha"] if row else None

    def landed(self, slug: str, target: str):
        return self.db.execute("SELECT sha FROM landed WHERE change=? AND target=?", (slug, target)).fetchone()

    def open_ask(self, slug: str):
        return self.db.execute(
            "SELECT a.* FROM ask a LEFT JOIN answer n ON n.ask=a.id WHERE a.change=? AND n.ask IS NULL", (slug,)
        ).fetchone()

    def handover(self, slug: str, head: str):
        return self.db.execute("SELECT * FROM handover WHERE change=? AND head=?", (slug, head)).fetchone()

    def rows(self, slug: str):
        return self.db.execute("SELECT * FROM row WHERE change=? AND waived=0 ORDER BY id", (slug,)).fetchall()

    def last_verdict(self, slug: str, head: str):
        return self.db.execute(
            "SELECT * FROM verdict WHERE change=? AND head=? ORDER BY id DESC LIMIT 1", (slug, head)
        ).fetchone()

    def artefact(self, kind: str, key: str):
        return self.db.execute("SELECT * FROM artefact WHERE kind=? AND key=?", (kind, key)).fetchone()

    def live_run(self, slug: str):
        return self.db.execute("SELECT * FROM run WHERE change=? AND ended_at IS NULL", (slug,)).fetchone()

    def run_for(self, slug: str, input: str):
        return self.db.execute("SELECT * FROM run WHERE change=? AND input=? ORDER BY id DESC LIMIT 1", (slug, input)).fetchone()

    def card(self, slug: str, head: str, digest: str):
        return self.db.execute("SELECT * FROM card WHERE change=? AND head=? AND digest=?", (slug, head, digest)).fetchone()

    def approval(self, card_id: int):
        return self.db.execute("SELECT * FROM approval WHERE card=? AND spent_at IS NULL", (card_id,)).fetchone()

    def undone_steps(self, card_id: int):
        return self.db.execute("SELECT * FROM carry_step WHERE card=? AND done_at IS NULL ORDER BY n", (card_id,)).fetchall()

    def hold(self, slug: str, head: str):
        return self.db.execute(
            "SELECT * FROM hold WHERE change=? AND lifted_at IS NULL AND (head IS NULL OR head=?)", (slug, head)
        ).fetchone()

    def last_event(self, slug: str):
        return self.db.execute("SELECT * FROM event WHERE change=? ORDER BY id DESC LIMIT 1", (slug,)).fetchone()
