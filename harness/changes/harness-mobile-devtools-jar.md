---
slug: harness-mobile-devtools-jar
track: harness
title: The change's own devtools jar on the mobile and the desktop, built in the build
  copy
kind: change
priority: P0
deps: []
created: '2026-11-01T03:29:58Z'
---
client tools/track.sh (client/harness-v8) never builds the devtools plugin: build() symlinks the main checkout's re/devtools and re/devtools-build into the build copy and does not run host/plugins/devtools/build.sh, and boot() pushes the main checkout's re/host/plugins-extra/devtools.jar. So a change to the devtools plugin (client-devtools-login carries host/plugins/devtools/login.patch, applied on the pinned REV) never reaches its own mobile, and running build.sh in a build copy would rewrite the shared re/devtools checkout and jars every other run uses. Make build run host/plugins/devtools/build.sh in the build copy with its own re/devtools (a git worktree of the main re/devtools at REV; build.sh accepts a .git file since client-devtools-login), re/devtools-build and re/host/plugins-extra (lombok and asm may stay shared, read-only), keep the jars beside the APK in evidence/<slug>/ keyed by T, and make boot push that devtools.jar. Proof: up on client-devtools-login's head lists the login tool in tools/list (tools/devtools_mcp.py --call tools/list). One test per requirement touched.
