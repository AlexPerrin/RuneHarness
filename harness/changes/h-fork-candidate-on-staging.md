---
slug: h-fork-candidate-on-staging
track: harness
priority: P0
---
# A fork change is built and judged on our fork, with our own patches: its PR is packaged from it and waits in the queue

The user's word (2026-11-07): "keep our local forked version with our own patch, if we can use it for upstream (it aligns with the 1:1 official OSRS GOAL) we'll package as a PR. Our goals are the priority, PRs go to an approval queue."

Today a fork candidate is upstream main + deps + head (decide.candidate_deps, hd submit / dep_inputs), so a judge's `up` runs without what the test server already runs: token login (server-token-auth, staged; its PR waits on card 4's Central hold) is missing, and `up` types the password (52641cb: "fork up keeps the typed form until token login is in the fork's base"). The live fork and the tree a judge proves differ.

Needed: a fork change's candidate starts from the fork's staging tree (base, pins and every staged head, H4) instead of upstream main, so every judge proves the change on what the test server will run, and `up` signs the desktop in by token with Play alone (the issuer sidecar, or Central's sign-in once central-game-session is staged), no typed form. The PR head is unchanged: it stays on upstream main and holds no other PR's commits (G4); whether it merges cleanly onto main is still checked (gate-ci, the scratch merge). A change whose head does not merge onto staging is the dev's step, as for staging today.

Update PRD (H2/H4/G4 wording if needed: proved on the fork, packaged for upstream), ARCHITECTURE (candidate) and the tests. Replay must show only fork candidates' bases moving.

Done when: a fork change's candidate holds staging's token login although its head is on upstream main; that change's `up` reaches LOGGED_IN on a desktop with no key typed but Play; the same head's upstream PR branch holds no staged commit.
