"""hd kpi: the harness goal's numbers (docs/PROBLEM.md §6), one query per metric. Targets in docs/V9-PROPOSAL.md §2."""

QUERIES = [
    ("runs per change (median)", "≤5",
     "SELECT n FROM (SELECT count(*) n FROM run GROUP BY change ORDER BY n) LIMIT 1 OFFSET (SELECT (count(DISTINCT change)-1)/2 FROM run)"),
    ("runs ended without own record", "<5%",
     "SELECT printf('%d of %d', sum(end_kind IN ('console','stop') AND record IS NULL), count(*)) FROM run WHERE ended_at IS NOT NULL"),
    ("successor runs", "0",
     "SELECT count(*) FROM run r WHERE EXISTS (SELECT 1 FROM run p WHERE p.change=r.change AND p.id<r.id AND p.input=r.input AND p.end_kind IN ('console','handoff'))"),
    ("harness share of runs", "<15%",
     "SELECT printf('%d of %d', sum(change IN (SELECT value FROM json_each(:harness))), count(*)) FROM run"),
    ("jobs per tree (build, gate)", "1.0",
     "SELECT printf('%.2f', 1.0*count(*)/max(1, count(DISTINCT substr(key,1,40)))) FROM job WHERE kind IN ('build','gate')"),
    ("ships per change > 1", "0",
     "SELECT count(*) FROM (SELECT change FROM job WHERE kind='ship' AND ok=1 GROUP BY change HAVING count(*)>1)"),
    ("open alerts", "0", "SELECT count(*) FROM alert WHERE disposition IS NULL"),
    ("peak context p90 (tokens)", "≤200k",
     "SELECT coalesce(json_extract(usage_json,'$.context_tokens'),0) FROM run WHERE usage_json IS NOT NULL ORDER BY 1 LIMIT 1 OFFSET (SELECT max(0, count(*)*9/10-1) FROM run WHERE usage_json IS NOT NULL)"),
]


def report(db) -> str:
    import json

    import act
    harness = json.dumps([c.slug for c in act.changes() if c.track == "harness"])
    out = []
    for name, target, sql in QUERIES:
        row = db.execute(sql, {"harness": harness} if ":harness" in sql else {}).fetchone()
        out.append(f"{name:<36} {str(row[0]) if row else '-':<12} target {target}")
    return "\n".join(out)
