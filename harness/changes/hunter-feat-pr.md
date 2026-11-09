---
slug: hunter-feat-pr
track: fork
priority: P2
pr: 408
public: feat/hunter
draft: true
deps:
- h-fork-build-stale-pack-state
---
## Change
Upstream #408 (draft) is the entire Hunter skill (the user, 2026-10-25: "Scope is entire Hunter Skill"): every Hunter
technique and activity on the OSRS wiki's Hunter page, matching the wiki, nothing left out. Today it carries bird
snares and box traps, bird houses, Herbiboar, butterflies, implings and Hunters' Rumours; still to add: Razor-backed
and other kebbit tracking, deadfalls, net traps, falconry, drift net fishing, pitfalls, and every item of the PR text's
Not done list. Net diff against upstream main is the hunter work only: no unrelated files, no generated .data files,
no test files, no added comments (AGENTS.md read live), gamevals through the gameval conflict check, spotlessCheck
clean. Title: "feat: Hunter skill".

## Definition of done
- the gate passes (accuracy specs in the evidence dir, fork CI and Formatting green on the scratch merge)
- the review passes: scope, upstream style, PR text (pull_request_template.md verbatim, ticks only when true, a plain
  scope list of what is in and what is not, data sources, guesses and gaps), the main hunter activities in game on a
  branch server
- mergeable as it stands except what the user scoped out (answer B, 2026-10-31): every template checklist item ticked
  and true but "Matches the OSRS wiki", which stays unticked while the "Not in this PR" list (drift net fishing, the
  lucky impling jar's loot, the rumour milestones, wild broav, the Chambers of Xeric bats) waits for content upstream
  main lacks; everything else on the wiki Hunter page matches the official game (the user: "dont include any quirks
  in our changes. If it differs from official OSRS, fix it"); no docs/quirks.md entries
- after the user's yes: #408 leaves draft once upstream CI is green

## Answers
- 2026-10-25T23:47:13Z a
- 2026-10-26T02:10:16Z b
- 2026-10-31T03:00:07Z The user: yes, renumber. Renumber the dbrow ids with gates/gameval_ids.py assign on current upstream main, rerun the gate (gameval_ids.py check now catches ids upstream main took after the branch's base), and hand over again so the branch is re-pinned.
- 2026-10-31T04:08:57Z console, under the user's 2026-10-31 rule (a forced dev/* push only when it keeps the live tip's tree): push in two steps. 1) force-push the reword 9f36979bd (same tree as d5ddd96de) to dev/hunter-feat-pr with --force-with-lease=dev/hunter-feat-pr:d5ddd96de314a78e0c074fb899287826b6ef8d5f; the guard allows it. 2) plain push 743965b1e (a fast-forward on top). Then hd handover hunter-feat-pr 743965b1e.
- 2026-10-31T15:23:41Z The user: B. Build the Miscellaneous items (Hunter Kit spell, Leon's Hunter's crossbow and kebbit bolts, sunlight crossbow, Fancy Clothes Store fur trades, meat and fur pouches, Hunter cape teleports) and goat luring (Telekinetic Grab on NPCs and Dark Lure) in #408 now. List drift net fishing, the lucky impling jar's loot, the rumour milestones, wild broav and the Chambers of Xeric bats under 'Not in this PR' as needing content upstream main lacks; 'Matches the OSRS wiki' stays unticked until they land. For the unsourced data, keep the best available (the 10 wiki-mapped Puro-Puro low-tier points, the 200-tick roam, the XP from each creature's own wiki page), each listed as a guess in the PR text. Then finish the texts for the new head and hand over.
- 2026-10-31T16:41:27Z console: no decision needed; run hunter-feat-pr-17 is already renumbering dbrow.hunter_rumour_swamp_lizard with gameval_ids.py assign. Hand over the renumbered commit; that re-pins dev/hunter-feat-pr in integration (it was dropped at tools 4ce9da788).
- 2026-10-31T18:18:56Z The user: find sources first for the unsourced values beyond the three already settled (the ferret and jerboa catch curves, the 50-tick respawns, the 200-tick trap collapse, the goat prod distance and respawn, the stymphike rules): search RSProx recordings, the wiki and Mod posts for each, fix what a source settles, and hd ask about the rest. The definition of done now follows answer B: 'Matches the OSRS wiki' unticked and the 'Not in this PR' list are expected, not findings. The Hunter cape's daily reset is 00:00 UTC.

Carried from v8 at the cutover (2026-11-03): its head is dev/hunter-feat-pr on the fork; re-judged under v9's criteria.
