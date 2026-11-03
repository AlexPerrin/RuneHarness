"""Claude Code hooks (docs/ARCHITECTURE.md §11): bind and end runs, two denials, the scope line, the context limit.

stdin: the hook's JSON. stdout: the hook's JSON answer. Wired in .claude/settings.json.
"""
import json
import sys


def subagent_start(event: dict) -> dict:
    """UPDATE run SET agent_id, started_at WHERE brief = the path the prompt names AND started_at IS NULL."""
    raise NotImplementedError


def pre_tool_use(event: dict) -> dict:
    """Bash in an agent: `hd approve` / `hd close` → deny (the user's own commands); else prepend
    `hd scope <run>` so the command runs in the run's systemd slice."""
    raise NotImplementedError


def post_tool_use(event: dict) -> dict:
    """transcript bytes past context_limit → additionalContext: the hand-off steps and the `run <id>: handoff` line."""
    raise NotImplementedError


def subagent_stop(event: dict) -> dict:
    """last line == the run's expected record (or `run <id>: handoff|filed …|ask …`) → UPDATE run ended_at,
    end_kind, record, usage, transcript and start `hd tick` without waiting; else continue (an idle turn)."""
    raise NotImplementedError


HANDLERS = {
    "SubagentStart": subagent_start,
    "PreToolUse": pre_tool_use,
    "PostToolUse": post_tool_use,
    "SubagentStop": subagent_stop,
}


def main() -> None:
    event = json.load(sys.stdin)
    handler = HANDLERS.get(event.get("hook_event_name", ""))
    print(json.dumps(handler(event) if handler else {}))


if __name__ == "__main__":
    main()
