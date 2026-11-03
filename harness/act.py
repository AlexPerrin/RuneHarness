"""Step → the world (docs/V9-PROPOSAL.md §3.4, §3.6): start scripts, compute trees, write briefs, wake the orchestrator."""


class Conflict(Exception):
    """merge-tree conflict; args[0] is the list of files."""


def tree(repo, base: str, heads: list) -> tuple:
    """T: fold `git merge-tree --write-tree` over base + each dep head (closure, deps first) + head, then
    `git commit-tree` with GIT_COMMITTER_DATE = the newest parent's committer date → (tree, tcommit).
    Deterministic, so the CI child of T is the same sha and its green run answers again. Raises Conflict(files)."""
    raise NotImplementedError


def key(kind: str, tree: str, repo) -> str:
    """f"{tree}:{recipe}" where recipe = `tracks/<repo>/track.sh recipe <kind>`. No hashing of
    tools files: a fixed checker re-runs by `hd regate`."""
    raise NotImplementedError


def start(db, step, ch) -> None:
    """systemd-run --user --scope --unit hd-<slug>-<kind>-<key12> -- tracks/<repo>/track.sh <verb> <slug> <key>;
    INSERT artefact(kind, key, change, pid, pid_start, scope, log, started_at). The script's last act is
    `hd artefact <kind> <key> ok|fail <detail>`; the wrapper writes its exit to state/<slug>/<kind>.rc."""
    raise NotImplementedError


def integrate(db, ch, head: str) -> None:
    """In <fork>/.worktrees/integration: git merge --no-ff --no-edit <head>, push fork integration; a conflict →
    git merge --abort and event(kind='merge-conflict', detail=files), which dev_due reads. Also merges upstream
    main into integration when ref upstream/main moved; a conflict there is alert('pin-conflict')."""
    raise NotImplementedError


def revert(db, ch) -> None:
    """A closed change: git revert -m 1 <its merge commit> on integration; a conflict is an alert."""
    raise NotImplementedError


def brief(db, ch, step) -> str:
    """Write state/briefs/<run id>.md: definition, rows with their latest results and verdict marks, answers and
    findings since the last handover, build/gate detail and log paths, the hand-off file, the clone/build
    copy/evidence paths, the exact hand-back line expected. Returns the path."""
    raise NotImplementedError


def wake(db) -> None:
    """Rewrite state/wake.orchestrator with the head lines new since the last wake (spawn, card, question, triage,
    alert); unchanged content → no write."""
    raise NotImplementedError


def tick(db, dry_run: bool = False, offline: bool = False) -> list:
    """One pass: observe (unless offline) → decide.plan → act (unless dry_run). Returns the action list.
    A second tick while one runs exits at once (flock on state/tick.lock)."""
    raise NotImplementedError
