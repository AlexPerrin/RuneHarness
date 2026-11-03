---
slug: harness-gate-tools-own-files
track: harness
title: The code a build or gate runs lives in its own files, and the key is their
  hash; no shell parsing
kind: change
priority: P1
deps: []
created: '2026-11-01T21:27:24Z'
---
Root cause behind harness-build-key-tools-files (f05315c), filed under the user's rule that every noted limit is a bug and fixes go to the root cause (2026-11-01). The re-gate storm came from keying builds on the whole tools branch; f05315c fixes it by parsing tools/track.sh (function reachability, command position, here-docs) to hash only what build and gate run. Its own limits show the parse is brittle: an edit to the build/gate dispatch line does not move the hash (a shortcut: comment), top-level variables used only by up are always hashed, and every future track.sh edit risks a miss or a spurious re-gate. Root cause: build/gate code shares one script with up/down/log/desktop code. Acceptance: the build and gate code (and what it calls) move into their own files (e.g. tools/server/gate/, tools/client/gate/), track.sh only dispatches to them; the key is the hash of those files plus the contract's script rows, with no parsing; f05315c's parser and its shortcut are removed; the one-time re-gate on ship happens once; a test shows an up-only edit does not move the key and any gate-file edit does.
