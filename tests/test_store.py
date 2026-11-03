import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import store  # noqa: E402


class Store(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = store.connect(str(Path(self.dir.name) / "hd.db"))

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def test_migrate_reaches_latest_and_is_idempotent(self):
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], len(store.MIGRATIONS))
        self.assertEqual(store.migrate(self.db), len(store.MIGRATIONS))
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"run", "session", "submission", "criterion", "check_result", "verdict", "job", "card", "approval", "publish_step", "alert"} <= tables)

    def test_one_live_run_per_change(self):
        ins = "INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES ('c', 'dev', 'code', 'i', 'b', 't')"
        self.db.execute(ins)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(ins)

    def test_typed_columns_refuse_unknown_kinds(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES ('c', 'planner', 'code', 'i', 'b', 't')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO answer(ask, option, by, at) VALUES (99, 'a', 'user', 't')")  # no such ask


if __name__ == "__main__":
    unittest.main()
