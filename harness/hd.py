#!/usr/bin/env python3
"""hd: the commands (docs/ARCHITECTURE.md §8). Each is one function; the loop lives in decide.py and act.py."""
import argparse
import sys

COMMANDS = {
    # name: (who calls it, what it writes)
    "tick":     ("timer, hook", "the pass; --dry-run prints plan() and writes nothing; --db F --offline for the replay"),
    "new":      ("orchestrator, dev, user", "harness/changes/<slug>.md; --on appends to an open change; --from-alert carries the alert's evidence"),
    "fold":     ("orchestrator", "change_state.folded_into"),
    "show":     ("runs, orchestrator", "prints the brief text"),
    "criterion": ("qa (criteria mode), the pass", "criterion"),
    "submit":   ("dev", "submission(head, candidate): the dev ref's tip is done; prints the hand-back line"),
    "verdict":  ("qa", "verdict + verdict_row"),
    "ask":      ("runs", "ask (one open per change)"),
    "answer":   ("orchestrator", "answer; applies the option's effect in the same transaction"),
    "triage":   ("orchestrator", "finding.triage; a finding becomes a criterion on the PR's open change"),
    "hold":     ("orchestrator", "hold"),
    "approve":  ("the user only", "approval"),
    "close":    ("the user only", "change_state.closed_at"),
    "publish":  ("the pass", "publish_step, approval.spent"),
    "job":      ("track scripts", "job result"),
    "step":     ("track scripts", "step_log"),
    "fault":    ("any run", "alert(kind='fault')"),
    "dismiss":  ("orchestrator", "alert.disposition"),
    "stop":     ("orchestrator", "run.ended_at; stops the run's slice"),
    "scope":    ("the hook", "moves the shell into hd-<run>.slice"),
    "regate":   ("orchestrator, a harness dev", "drops job(gate) and check_result at the current candidate"),
    "kpi":      ("anyone", "nothing"),
    "commit":   ("orchestrator", "a pathspec commit as Alex Perrin, pushed"),
    "restart":  ("orchestrator, once hd prints drain and no run of it is live", "session.end_kind='restart'; exits the claude process"),
    "session-ended": ("harness/orchestrator.sh", "exit 1 when the ended session's end_kind is 'exit' (the user's), else 0: loop"),
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hd", description="the harness loop; no argument runs a pass and prints the view")
    sub = p.add_subparsers(dest="cmd")
    for name, (who, what) in COMMANDS.items():
        sub.add_parser(name, help=f"{what} ({who})")
    args = p.parse_args(argv)
    raise NotImplementedError(args.cmd or "view")


if __name__ == "__main__":
    sys.exit(main())
