---
slug: harness-client-track-slug-env
track: harness
title: The client track.sh reads the slug only from $2, so hd's check rows run with
  an empty slug and every client hand-over is refused
kind: change
priority: P2
deps: []
created: '2026-11-01T03:23:06Z'
---
hd rows runs each contract row as 'tools/track.sh check-log' etc. at the track root with SLUG in the env (hd.py Ctx.env), but the client repo's tools/track.sh (client/harness-v8 9ec03a8, line 23: slug=${2:-}) reads the slug only from its second argument, so every check: row prints 'no change or goal "": tools/track.sh <verb> <slug> [arg]' and exits 2. Evidence: 'hd handover client-login-index-log' at a32dd7022 refused on repack-log, device-evidence, probe and network-qa with that line, while the same verbs run by hand with the slug pass (check-log, check-evidence, check-probe with HEAD set, check-netqa, check-state-doc with BUILD). harness-gate-ci-slug fixed the server track.sh the same way; the client one needs slug=${2:-${SLUG:-}} (and the state/evidence dirs then follow). One test per requirement touched.
