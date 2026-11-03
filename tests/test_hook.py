"""The hook's JSON in and out: bind, the denials, the scope line, the hand-back."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import hook  # noqa: E402
import store  # noqa: E402


class Hook(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        store.DB = str(Path(self.dir.name) / "hd.db")
        self.db = store.connect()
        self.db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES ('h-one', 'dev', 'code', 'i', 'state/briefs/1.md', 't')")
        hook.act.tick_later = lambda: None
        hook.act.stop_scope = lambda r: None

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def test_approve_and_close_denied_to_every_agent(self):
        out = hook.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": "python3 harness/hd.py approve x abc"}})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(hook.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": "hd show x"}}), {})

    def test_bind_on_the_brief_then_scope_each_command(self):
        self.assertEqual(hook.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": "ls"}, "agent_id": "ag1"}), {})
        hook.pre_tool_use({"tool_name": "Read", "tool_input": {"file_path": "/x/state/briefs/1.md"}, "agent_id": "ag1"})
        r = self.db.execute("SELECT agent_id, started_at FROM run WHERE id=1").fetchone()
        self.assertEqual(r["agent_id"], "ag1")
        self.assertIsNotNone(r["started_at"])
        out = hook.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": "ls"}, "agent_id": "ag1"})
        self.assertTrue(out["hookSpecificOutput"]["updatedInput"]["command"].endswith("hd.py scope 1; ls"))

    def test_handback_ends_the_run_once_and_blocks_a_missing_line(self):
        self.db.execute("UPDATE run SET agent_id='ag1', started_at='t' WHERE id=1")
        out = hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "I am done.", "stop_hook_active": False})
        self.assertEqual(out["decision"], "block")
        out = hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "done\nrun 1: submitted " + "a" * 40, "agent_transcript_path": "/none"})
        self.assertEqual(out, {})
        r = self.db.execute("SELECT * FROM run WHERE id=1").fetchone()
        self.assertEqual((r["end_kind"], r["record"][:18]), ("handback", "run 1: submitted a"))
        self.assertEqual(hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "run 1: PASS"}), {})  # already ended

    def test_unbound_agent_binds_by_its_record_line(self):
        out = hook.subagent_stop({"agent_id": "ag9", "last_assistant_message": "run 1: submitted " + "b" * 40, "agent_transcript_path": "/none"})
        self.assertEqual(out, {})
        r = self.db.execute("SELECT agent_id, end_kind FROM run WHERE id=1").fetchone()
        self.assertEqual((r["agent_id"], r["end_kind"]), ("ag9", "handback"))

    def test_wrong_run_id_is_not_a_record(self):
        self.db.execute("UPDATE run SET agent_id='ag1', started_at='t' WHERE id=1")
        out = hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "run 2: PASS", "stop_hook_active": True})
        self.assertEqual(out, {})
        self.assertEqual(self.db.execute("SELECT end_kind FROM run WHERE id=1").fetchone()[0], "console")


if __name__ == "__main__":
    unittest.main()
