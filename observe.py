"""world → ledger (docs/V9-PROPOSAL.md §3.5). The only module besides act.py and carry.py that runs git, gh or docker.

Each function writes observation rows bound to what it observed (sha, etag, comment id) and nothing else.
"""


def fetch(db, repo) -> set:
    """git fetch --prune <remote>; git for-each-ref → UPSERT ref rows; returns the names whose sha changed."""
    raise NotImplementedError


def landed(db, repo, target: str, changes: list) -> None:
    """Only when `target` moved: for each open change of the repo without a landed row for target,
    git merge-base --is-ancestor <dev head> <target sha> → INSERT landed. A squash or rebase merge upstream is
    seen through pr_state().merged_at instead."""
    raise NotImplementedError


def procs(db) -> None:
    """artefact rows with a pid and no ended_at whose (pid, pid_start) is gone: read state/<change>/<kind>.rc;
    a result row written by the script → nothing; else ended_at, exit, INSERT attempt(cause = last log line with
    hex runs dropped). Exit 75 = a cause outside the head: ok stays NULL and the pass starts it again."""
    raise NotImplementedError


def gh(db, url: str):
    """GET with If-None-Match from gh.etag over one keep-alive connection: 304 → the stored body; 200 → UPSERT;
    403 on quota → alert('quota') and None (unknown: the step holds)."""
    raise NotImplementedError


def pr_state(db, repo, pr: int):
    """state, draft, head sha, merged_at, base — from gh()."""
    raise NotImplementedError


def checks(db, repo, sha: str) -> list:
    """the latest run per check name at sha plus commit statuses — from gh()."""
    raise NotImplementedError


def comments(db, repo, pr: int) -> None:
    """review and issue comments of the PR: not a bot, not ours → INSERT OR IGNORE finding."""
    raise NotImplementedError


def docker(db) -> set:
    """running container names (stack recovery, hd room)."""
    raise NotImplementedError


def alerts(db) -> None:
    """UPSERT alert rows from the anomaly queries (§3.13): attempts, run-lost, runs-per-head, ask-stale, denied,
    ci-runner, kpi, pin-conflict, quota. Dedup on (kind, subject): count += 1, last_at = now."""
    raise NotImplementedError
