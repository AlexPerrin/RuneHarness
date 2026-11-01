---
slug: harness-review-in-console
track: harness
title: The user reviews and approves each complete PR as text in the console; no fork
  queue PRs
kind: change
priority: P0
deps: []
created: '2026-11-01T20:04:57Z'
---
The user's word (2026-11-01): "Forget the fork work too complicated, I just want a way to best review an approved change. Just pass as text in console". This reverses the fork queue surface of harness-public-queue-on-fork (ef7e4bc) and supersedes harness-queue-knows-open-pr. Keep the rest of that rework: one carry of the approved state, every step logged, the reply-only one-run rule, the removals (hd-public merged into hd.py, the separate paths, the shortcuts).

Acceptance:
1. The review surface is the orchestrator's console: for each complete upstream PR state, hd prints one card with everything the carry will do, in order: the upstream PR (new, or update of PR N found by its open head branch), the head and its base, and every exact text that will be posted (title, body, comment, each reply with its quoted finding and thread), then the verdict and evidence path. The orchestrator shows it in full.
2. The yes is '! python3 ~/osrs-harness/hd.py approve <slug> <head>', recorded locally, bound to the head and a digest of the card's texts; a change to either withdraws it. No GitHub label, no fork PR, no fork queue branches.
3. The no is '! hd.py close' or the user's word (the card stays hidden at that head).
4. A change whose upstream PR is already at the head with nothing left to post gets no card (fixes the re-queued 367/354/445 and the duplicate-PR plan for PR 445: an open upstream PR is found by its head branch without the owner prefix).
5. Cleanup: close the open fork queue PRs (AlexPerrin/OpenRune-Server#35, #36 and any other queue/ PR) without a comment that links upstream, and delete the queue/ branches and their -base branches on the forks; remove the queue code, its tests and its doc text; the hook's 'approved' label rule goes.
6. Docs (PROBLEM/PRD/ARCHITECTURE, orchestrator.md) state the console card as the approval surface; tests cover the card's contents, a withdrawn approval on a text change, and no card when upstream is already done.
