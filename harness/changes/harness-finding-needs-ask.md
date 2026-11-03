---
slug: harness-finding-needs-ask
track: harness
title: A maintainer comment that asks nothing files no change and lists no dev run
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T16:39:58Z'
limit-of:
- server-354-cickwdoqbbpt88aaaabifocug
---
a-thoren's #354 comment IC_kwDOQBbPT88AAAABiFocug ('good pushback on my comments! I'll make sure to test this further in the coming days') became change server-354-cickwdoqbbpt88aaaabifocug (16:38:01Z) and listed dev run -1, though it reports no defect and asks for nothing; per the one-comment-per-carry rule a reply would also post to Discord for nothing. Triage must tell a finding (a defect or request) from an acknowledgement. Evidence: harness/changes/server-354-cickwdoqbbpt88aaaabifocug.md

Also (filed): A merged upstream PR is done though the change holds no pr: or opened.json
#445 (quest-cooksassistant, head 07f01dc9a) was MERGED upstream at 2026-11-02T16:34:49Z (gh pr view 445: state MERGED, headRefOid 07f01dc9a). The next pass did not see it as done: the change went to 'building', re-gated (cecb4f1bf) and at 17:09:29Z showed the user a card to push the head and open a new draft PR on OpenRune/OpenRune-Server. harness/changes/quest-cooksassistant.md has no pr: and state/quest-cooksassistant/ has no opened.json (the PR was carried before those records), so Ctx.done's PR read (e6a91f3/a7ef444) finds no PR number. Find the PR by its head branch (content/quest-cooksassistant) or head sha when the record is missing; a change whose head is in a merged PR is done. Evidence: state/events.jsonl (quest-cooksassistant 16:35:44Z-17:09:29Z)

Also (server-354-cickwdoqbbpt88aaaabifocug): A maintainer comment that asks nothing files no change and lists no dev run
server-354-cickwdoqbbpt88aaaabifocug answers a-thoren's IC_kwDOQBbPT88AAAABiFocug, an acknowledgement that reports no defect and asks nothing. The PR's live head is already the dep's carried head 8b6054f4c, so the change has no commit to carry; a pr-comment/pr-reply would post to Discord for nothing, against one-comment-per-carry. Triage must not file a change for it (or must close it with no carry).
