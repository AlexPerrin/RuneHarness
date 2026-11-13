---
slug: client-readme-runelight
track: client
priority: P2
deps:
- client-progress-refresh
---
# README: RuneLight presentation for public social-media release (rename from osrs-plugins-reverse), in the style of RuneHarness's README, with logo



The client repo is renamed RuneLight (it was osrs-plugins-reverse). Rewrite its README.md as a professional presentation for a public social-media release, in the style of this harness's README (commit e42dd6b): centred logo (docs/assets/logo.svg), name, one-line tagline, badge row, a short plain-language pitch, a "how it works" section, a status table, requirements and install, building from source, contributing, licences and credits.

- Keep every claim true of the current head: the OSRS build the APK targets, the RuneLite API coverage and packet numbers (from tools/progress.py, so after client-progress-refresh), what works and what does not. Name RuneLight everywhere; fix links, clone URLs, badge URLs and docs that still say osrs-plugins-reverse.
- Keep the legal and safety section prominent: a research and interoperability project for an OpenRune-compatible test server, never Jagex's live servers, not affiliated with or endorsed by Jagex or RuneLite; the privacy patch (no contact with Jagex or RuneScape servers) stated as it is.
- Public hygiene: no personal email, device names, local paths, account names, recorded players' names or chat; no third-party assets beyond what their licences allow (THIRD_PARTY_NOTICES.md).
- Shorter first screen: what it is and a screenshot or diagram above the fold, depth below. Docs under docs/ stay the detail; the README links, not duplicates.
Done when: the README renders on GitHub with the logo, every link resolves, every number matches tools/progress.py output at the head, and a grep for the old name, personal identifiers and local paths finds none.
