---
slug: harness-live-deploy-on-tools-change
track: harness
title: the live stack is redeployed only when the integration tree moves, never when
  the deploy's own tools change what the image carries
kind: change
priority: P1
mechanism: tree
limit-of:
- harness-mobile-login-by-facts
deps: []
created: '2026-11-02T15:39:38Z'
---
Root cause (workflow: a shipped change reaches its live target): hd.py's server step deploys live only when state/live/tree.json's tree differs from the integration tree (rec('live','tree').tree != tint['tree']); deploy_key already hashes tools/track.sh, tools/build/, tools/server/ but only for the retry count. So a tools ship that changes what the live image must carry never reaches live: harness-server-stack-one-record shipped 15:29Z (fork tools: ship's image COPYs state/live/key, the pair every APK's modulus comes from), yet osrs-openrune:241 (built 06:09Z) still carries client.key aa54f50c while state/live/key is 8555c56c and tree.json has no modulus, so the client track's up refuses every APK ('deployed before its key pair') and no mobile can log in to live (harness-mobile-login-by-facts' LOGGED_IN proof). Fix: live's record keeps the deploy key (tree + tools hash) and the step deploys when that key differs, not the tree alone. Acceptance: after a fork tools ship that changes tools/track.sh's ship, the next pass deploys live with no tree change; tree.json then carries the modulus and the client up on live reaches LOGGED_IN.
