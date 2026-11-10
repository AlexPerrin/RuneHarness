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

    def test_approve_or_close_in_a_quoted_argument_is_text_unless_it_runs(self):   # alerts 84, 85
        for cmd in ['grep -n "hd approve <slug>\\|PR rounds" docs/*.md', "hd.py new x --title 'hd close denies text'"]:
            self.assertEqual(hook.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": cmd}}), {})
        for cmd in ['bash -c "hd approve x abc"', "eval 'hd.py close x'"]:
            out = hook.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": cmd}})
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_an_agent_whose_run_ended_by_close_or_stop_is_denied_every_tool(self):
        self.db.execute("UPDATE run SET agent_id='ag1', started_at='t', ended_at='t', end_kind='close' WHERE id=1")
        out = hook.pre_tool_use({"tool_name": "Read", "tool_input": {"file_path": "/x"}, "agent_id": "ag1"})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("run 1 ended: its change was closed", out["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "ok", "stop_hook_active": False}), {})

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
        self.assertIn('"first_edit": null', r["usage_json"])   # the first-edit measure is recorded at the run's end
        self.assertEqual(hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "run 1: PASS"}), {})  # already ended

    def test_handback_as_a_tool_call_ends_the_run_and_a_wrong_line_is_denied(self):
        self.db.execute("UPDATE run SET agent_id='ag1', started_at='t' WHERE id=1")
        out = hook.pre_tool_use({"tool_name": "SubagentHandback", "tool_input": {"message": "done, see above"}, "agent_id": "ag1", "transcript_path": "/x/s.jsonl", "session_id": "s"})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        out = hook.pre_tool_use({"tool_name": "SubagentHandback", "tool_input": {"message": "run 1: handoff"}, "agent_id": "ag1", "transcript_path": "/x/s.jsonl", "session_id": "s"})
        self.assertEqual(out, {})
        r = self.db.execute("SELECT end_kind, record FROM run WHERE id=1").fetchone()
        self.assertEqual((r["end_kind"], r["record"]), ("handoff", "run 1: handoff"))

    def test_a_run_waiting_on_a_background_task_is_left_alone(self):
        self.db.execute("UPDATE run SET agent_id='ag1', started_at='t' WHERE id=1")
        out = hook.subagent_stop({"agent_id": "ag1", "last_assistant_message": "waiting for the build", "stop_hook_active": False,
                                  "background_tasks": [{"id": "b1", "type": "bash", "status": "running"}]})
        self.assertEqual(out, {})
        self.assertIsNone(self.db.execute("SELECT ended_at FROM run WHERE id=1").fetchone()[0])

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
