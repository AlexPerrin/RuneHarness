"""hd kpi: the harness's measurement, one query per row of docs/V9-PROPOSAL.md §5."""

QUERIES = {
    "runs per upstream change (median)": None,
    "runs ended without own record": None,
    "successor runs": None,
    "harness share of runs / tokens": None,
    "harness changes filed per day": None,
    "harness changes shipped twice": None,
    "builds / gates per tree": None,
    "cards withdrawn on an unchanged tree": None,
    "carries not resumed": None,
    "pass CPU, nothing moved": None,
    "wrong hook denials": None,
    "peak context p90": None,
}


def report(db) -> str:
    """Each metric, its value and its target, one line each."""
    raise NotImplementedError
