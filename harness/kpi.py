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
    ("cards withdrawn on an unchanged tree", "0",
     "SELECT count(*) FROM (SELECT c.change, s.tree FROM card c JOIN submission s ON s.change=c.change AND s.head=c.head GROUP BY c.change, s.tree HAVING count(*)>1)"),
    ("publishes not resumed", "0",
     "SELECT count(*) FROM approval a WHERE a.spent_at IS NULL AND EXISTS (SELECT 1 FROM publish_step p WHERE p.card=a.card AND p.done_at IS NULL) AND NOT EXISTS (SELECT 1 FROM job j WHERE j.kind='publish' AND j.key=CAST(a.card AS TEXT) AND j.pid IS NOT NULL AND j.ended_at IS NULL)"),
    ("wrong hook denials (dismissed)", "0", "SELECT count(*) FROM alert WHERE kind='denied' AND disposition='dismissed'"),
    ("open alerts", "0", "SELECT count(*) FROM alert WHERE disposition IS NULL"),
    ("artifacts of closed changes", "0",
     "SELECT count(*) FROM artifact WHERE substr(owner, 1, instr(owner || '@', '@') - 1) IN (SELECT slug FROM change_state WHERE closed_at IS NOT NULL)"),
    ("images recorded", "≤ open heads + staging",
     "SELECT count(DISTINCT key) FROM artifact WHERE kind='image'"),
    ("free space (GB)", "≥ hd.yaml free",
     "SELECT group_concat(path || ' ' || (free / 1000000000), ', ') FROM disk"),
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
