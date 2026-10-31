#!/usr/bin/env python3
"""hook.py: the one hook program, wired in .claude/settings.json (docs/ARCHITECTURE.md). Reads the event JSON on stdin.

SubagentStart   bind the listed run: the brief path in the agent's first message names it; record agent_id and transcript.   R2
PreToolUse      the one rule: `hd approve` is denied inside a subagent (authority is otherwise by credential).             R4
PostToolUse     the context size (the transcript's last assistant usage) past cfg.context_limit → tell the run once to
                write evidence/<slug>/handoff.md and hand back.                                                            R6
SubagentStop    end the run: ended, usage {turns, input, output, cache_read, cache_creation}, last message, record (the
                role's record newer than the start), then start the pass without waiting
                (`systemctl --user start --no-block hd-tick.service`).                                                     R5 R6
"""
import json, sys


def bind(payload): ...
def deny_approve(payload): ...
def context_limit(payload): ...
def end_run(payload): ...


def main():
    payload = json.load(sys.stdin)
    {"SubagentStart": bind, "PreToolUse": deny_approve, "PostToolUse": context_limit, "SubagentStop": end_run}[payload["hook_event_name"]](payload)


if __name__ == "__main__":
    main()
