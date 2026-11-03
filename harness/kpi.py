"""hd kpi: the harness's measurement, one query per metric of the harness goal (docs/PROBLEM.md §6; targets in docs/V9-PROPOSAL.md §2)."""

QUERIES = {
    "runs per upstream change (median)": None,
    "runs ended without own record": None,
    "successor runs": None,
    "harness share of runs / tokens": None,
    "harness changes filed per day": None,
    "harness changes shipped twice": None,
    "builds / gates per tree": None,
    "cards withdrawn on an unchanged tree": None,
    "publishes not resumed": None,
    "pass CPU, nothing moved": None,
    "wrong hook denials": None,
    "peak context p90": None,
}


def report(db) -> str:
    """Each metric, its value and its target, one line each."""
    raise NotImplementedError
