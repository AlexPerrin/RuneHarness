---
slug: goblin-367-rsprox-dump
track: server
pr: 367
branch: content/goblin-diplomacy
title: '#367: back to draft while the Goblin Diplomacy RSProx dump is reviewed; accuracy
  check against it and fix'
kind: change
priority: P2
deps:
- harness-build-gate-keyed-process
- harness-deploy-survives-tools-ship
finding:
- IC_kwDOQBbPT88AAAABeeLlXg
- IC_kwDOQBbPT88AAAABhyfg1w
- IC_kwDOQBbPT88AAAABhyf-LQ
- IC_kwDOQBbPT88AAAABhzI4JQ
created: '2026-11-01T20:43:57Z'
---
The user's word (2026-11-01): "367 should go in draft for (https://github.com/OpenRune/OpenRune-Server/pull/367#issuecomment-6562504919). Draft comment explaining (reviewing dump), then run an accuracy check and fix if needed."

Context on PR 367 (content/goblin-diplomacy, head 019e5a1c4, ready since today): a-thoren asked for the cutscene ('Nice job but I'd really like to get the cutscene in as well'); eaglepurerocketgrape uploaded an RSProx recording of Goblin Diplomacy to the OpenRune Discord (issuecomment-6562504919); a-thoren posted a Discord invite (issuecomment at 2026-11-01T20:05:01Z). Agents cannot read Discord: the user downloads the dump into evidence/goblin-367-rsprox-dump/rsprox/ (that file existing is the fact this change's dev step waits on).

Steps, in order:
1. Public (the user's yes on its card): convert PR 367 to draft, and one comment quoting eaglepurerocketgrape's comment, thanking them and @ eaglepurerocketgrape and a-thoren, saying the PR goes back to draft while we review the Goblin Diplomacy recording against the quest, including the cutscene, and that it returns to ready with the result. No promise of a separate PR; no fork link.
2. Dev (once the dump is in evidence/goblin-367-rsprox-dump/rsprox/): transcribe it with 'track.sh transcribe' (all filters), then check the whole quest at 019e5a1c4 against it (dialogue, cutscene camera/anims/npcs/timings, varps, items, xp) with the wiki; every divergence is fixed on content/goblin-diplomacy as new commits (no force-push), cutscene included; recording details that hold other players' names stay local.
3. QA judges it; the card then is the complete update (push, comment naming the head and summarising what the dump changed, ready).

Step 1 done by the user (2026-11-01): PR 367 converted to draft and the comment posted (issuecomment-6563660994, with the Claude Code attribution). The harness does not repeat it.

Also: #367's one review round. Its head stacks on goblin-diplomacy-review-367-fftgsrq's 019e5a1c4, which it supersedes with the four finding changes goblin-diplomacy-review-367-fftgsrq-c*: answer each finding of its `finding` with a commit on the head where it needs code and pr-reply-<finding>.md quoting it.
