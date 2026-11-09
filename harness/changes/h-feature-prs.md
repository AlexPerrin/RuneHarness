---
slug: h-feature-prs
track: harness
priority: P2
---
# PRs bundled by feature: a change is our work, a feature is the user's PR

The user (2026-11-09): the harness's first job is to coordinate OUR goals; contributing upstream is second. Today a change is both the unit of work and the unit of upstream contribution, so narrow changes each carry PR texts, upstream criteria, a card and a publish, same-track changes wait on each other's upstream merge (G4, decide.upstream_dep_wait), and bundling is done by holding cards and rebuilding PRs by hand. Refactor so the user decides how PRs are bundled, by feature (e.g. Central's auth rework, friends, clans, worlds).

Rewrite of the upstream path: PROBLEM.md, PRD.md (A1, G4 restated per PR, a requirement that the user decides every bundle) and ARCHITECTURE.md first, per the iteration protocol; fewer concepts, not more.

## The user's decisions
1. A change names its PR by a `feature:` key in its front matter (matching upstream's conventions). One PR per (feature, repo).
2. A PR carries several commits: its member changes' commits, not squashed into one.
3. No ready flag: the card's approval is the user's decision. The harness packages a feature and shows its card; the user approves, holds or closes it.
4. Sister PRs (one feature across repos, e.g. Central + server) are published together on one approval.

## The model
- A change is our work: done when landed on staging and live. It has no PR texts, no upstream criteria (claims, one-change, texts, no-deferral, net-change), no card, no publish of its own. A change with no `feature:` is fork-only. The per-change `upstream:`, `pr:` and `public:` keys and upstream_dep_wait go.
- A feature is the set of open and landed changes naming it. Packaging: per repo, a package branch = upstream main + the member changes' commits in dependency order, no local or pinned commit (G4 at the PR level); one candidate, gate and qa on the package for upstream's rules (CI on upstream main, the live AGENTS.md/CONTRIBUTING/template, dupes, spotless, the PR texts judged against the package's net diff); one card covering every sister PR of the feature; approve; publish (the existing approval and publish-step log).
- A member added or changed after a publish repackages: a new head, a new card whose one comment covers the net change.
- A maintainer finding on a feature's PR files a change with that `feature:`; it lands on staging, then the PR repackages.
- A conflict applying a member to upstream main is the package's dev step.
- The orchestrator or a plan run may propose a feature for a change as a question; only the user sets it.

## Migration
- Open upstream PRs become features: #408 (Hunter, hunter-feat-pr), #354 (cannon), #367 (Goblin Diplomacy), #450 (training bow); the feature's PR number is observed by its branch.
- Today's held cards end as cards; their changes stay on staging and take a feature, e.g. session reliability (server-reconnect, server-resumed-session-logout, live-session-drops-after-login); Central auth + its server sister (central-token-login-op, central-embedded-jav-config, central-game-session, central-sign-in-first-account, server-token-auth); friends (fork-presence-push-not-delivered, fork-private-filter-reverts-at-login, fork-friend-add-updates-list, with Central's central-friend-del-no-offline-push); world switcher (server-world-switcher). The user confirms each grouping (a question per proposed feature); the standing holds stay until then.

Done when: a change carries no upstream work of its own; a feature with members on staging in two repos is packaged, judged and shown as one card, and one approval publishes both PRs; adding a member to a published feature yields a new card with one comment; the docs state the model; `hd kpi` reports runs and cards per feature.

Unchecked: whether member changes built on staging (pins and local branches under them) apply cleanly to upstream main; the first package shows it.
