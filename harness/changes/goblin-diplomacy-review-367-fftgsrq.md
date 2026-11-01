---
slug: goblin-diplomacy-review-367-fftgsrq
track: server
kind: change
priority: P1
branch: content/goblin-diplomacy
pr: 367
finding: IC_kwDOQBbPT88AAAABfTgSRQ
folded:
- IC_kwDOQBbPT88AAAABhguqsg
created: '2026-10-25T12:42:01Z'
title: 'goblin-diplomacy-review-367: finding by a-thoren on PR #367'
deps: [harness-subject-row-range, harness-dupe-tests-row-scope, harness-server-build-tree, harness-no-powershell, harness-server-build-musicrepository, harness-desktop-first-login]
---
## Change
Answer the maintainer's comment on PR #367 with a commit on top of the PR head and a reply in pr-comment.md.

> Nice job but I'd really like to get the cutscene in as well. 
> 
> I did a quick search on rsprox and this dump should have the info needed
> 
> <img width="1281" height="550" alt="image" src="https://github.com/user-attachments/assets/0b5eadf9-524c-43e3-947d-e1c1c3e7d0f2" />

## Definition of done
- the finding is addressed on the PR branch
- the reply names each fix

## Answers
- 2026-10-31T15:27:55Z The user: fold a-thoren's later comment 'should this still be in draft?' into this change (change goblin-diplomacy-review-367-fhguqsg is closed). pr-comment.md opens with a line answering it: the PR stays draft until these fixes are pushed, and is marked ready once they are pushed and CI is green.
- 2026-10-31T17:56:02Z The user: C. Keep the current head's generals: Bentnoze (2957,3512) and Wartface (2956,3512), wanderRange 2. List the spawn tiles and range under Unsourced as a reconstruction from RSProx 3243 and 3931, noting that they miss the recorded x 2960-2961 (about 5% of recorded steps) to keep the table between them as rarely as recorded. Then rewrite pr-body.md and pr-comment.md and hand over.
- 2026-10-31T17:56:35Z The user, replacing the 15:27 answer about the opener: the user answered 'should this still be in draft?' on #367 themselves. pr-comment.md has no draft line; it covers only the fixes.
- 2026-10-31T18:15:29Z The user chose that the gate judges formatting on the change's own files. The fork's Formatting job already does that (spotless ratchets from main, and the fork's main is upstream main 31241beef), so PrayerRepository.kt is not checked in CI; the failure was only Maven Central's HTTP 429. The console re-ran Formatting on gate/goblin-diplomacy-review-367-fftgsrq and dropped the gate record so the pass re-gates 77ac377e4. No commit is needed.
