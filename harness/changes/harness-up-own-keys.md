---
slug: harness-up-own-keys
track: harness
title: up makes its own server keys; no run copies another run's keys
kind: change
priority: P1
deps:
- harness-tests-no-real-tools-env
created: '2026-11-01T05:28:23Z'
---
harness-desktop-walk-to-long-1 and harness-up-keeps-account-state-1 each brought a server up on another change's image and had to copy that run's RSA keys into state/<slug>/key: without them Docker created root-owned directories and the server failed to start. Expected: up for any slug (including a harness change that borrows a built image) creates or fetches the keys it needs itself, and never leaves root-owned directories in state/. Proof: up <new-slug> with an existing image starts the server with no keys copied by hand. One test per requirement touched.
