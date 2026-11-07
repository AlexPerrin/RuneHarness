import glob
import shutil
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

    def test_every_migration_upgrades_every_recorded_fixture(self):
        for f in glob.glob(str(Path(__file__).parent / "fixtures" / "*.db")):
            copy = Path(self.dir.name) / Path(f).name
            shutil.copy(f, copy)
            db = store.connect(str(copy))
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], len(store.MIGRATIONS), f)
            self.assertTrue(db.execute("SELECT count(*) FROM run").fetchone()[0] > 0, f)
            db.close()

    def test_the_same_head_with_a_new_candidate_replaces_its_submission(self):   # a dep's head moved: the candidate follows
        self.assertTrue(store.submit(self.db, "c", "h1", "t1", "c1", None, None))
        self.db.execute("UPDATE submission SET at='old'")
        self.assertFalse(store.submit(self.db, "c", "h1", "t1", "c1", None, None))
        self.assertNotEqual(self.db.execute("SELECT at FROM submission").fetchone()[0], "old")   # criteria added before it no longer park the change
        self.assertTrue(store.submit(self.db, "c", "h1", "t2", "c2", None, None))
        rows = self.db.execute("SELECT tree, tcommit FROM submission WHERE change='c'").fetchall()
        self.assertEqual([(r["tree"], r["tcommit"]) for r in rows], [("t2", "c2")])

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

    def test_an_artifact_row_is_refused_outside_the_build_places(self):   # a release removes it: never a path the builds do not write
        store.own(self.db, "worktree", "/r/.worktrees/x-build", "x"); store.own(self.db, "worktree", "/r/.worktrees/x-build", "x")
        store.own(self.db, "dir", store.STATE + "/x/cand-1", "job:gate:k")
        for kind, key in (("worktree", "/home/alex"), ("dir", "/r/.worktrees/../../etc"), ("dir", "rel/.worktrees/x"), ("dir", "/home/x")):
            with self.assertRaises(ValueError):
                store.own(self.db, kind, key, "x")
        self.assertEqual(self.db.execute("SELECT count(*) FROM artifact").fetchone()[0], 2)
        store.alert(self.db, "disk", "/mnt/c", "low")   # the alert kind of the disk fact


if __name__ == "__main__":
    unittest.main()
