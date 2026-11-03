"""The card and the publish (docs/ARCHITECTURE.md §7).

The card is the recorded list of acts and exact texts the user approves. The publish executes publish_step rows in
order, skipping those done, with the card's texts — never anything re-read from the live PR or evidence/.
"""


def card(db, ch, head: str):
    """steps: push (unless the PR is at head) → pr (open-draft | edit title/body that differ) → ci (if pushed or
    draft) → comment (pr-comment.md + each pr-reply-<id>.md, quoting, @author once) → ready.
    release: build-asset → notes → publish. texts {title, body, comment}; digest = sha256(steps + texts).
    INSERT OR IGNORE card; INSERT publish_step rows with done_at NULL. Returns the card row."""
    raise NotImplementedError


def render(card_row) -> str:
    """The card as `hd` prints it: each act in order, each exact text, the verdict, the evidence path, the yes /
    no / close commands."""
    raise NotImplementedError


def approve(db, slug: str, head: str) -> None:
    """hd approve (the user only): refuses unless the card at (slug, head) is the latest and not held;
    INSERT approval(card)."""
    raise NotImplementedError


def publish(db, card_id: int) -> None:
    """hd publish (started by the pass as job kind 'publish'): for each publish_step with done_at NULL, in order,
    execute with the card's texts; on success UPDATE done_at, result_json.
    ci: poll observe.checks() until every check at head concluded; a failure → event('ci-failed'), the approval
        kept, stop (dev_due reads it).
    a GitHub write refused → approval.spent_why, stop (card_due makes a new card naming the refusal).
    a GitHub read unknown (quota) → stop with no step done; the pass starts it again later.
    after the last step: approval.spent_at = now, spent_why = 'published'."""
    raise NotImplementedError
