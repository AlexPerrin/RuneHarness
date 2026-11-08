---
slug: h-candidate-fork-only-dep
track: harness
priority: P1
---
# A fork-only dep done on staging still joins a candidate built off upstream main

hd submit (harness/hd.py cmd_submit) skips a candidate dep once it is landed on track(d).done_ref(d). For a fork-only dep (upstream: false) done_ref is refs/heads/staging, but the candidate's base is T.base (central: refs/remotes/origin/main), which never carries a fork-only fix. So central-rights-test-mod (done: landed on Central staging at 94a6b3d, upstream: false) is dropped from central-game-session's candidate: hd candidate central-game-session gives tree 4cc039f = db30e21's own tree, whose central-common RightsTest still uses Rights.MODERATOR, and tracks/central/track.sh test fails (':central-common:compileTestKotlin' Unresolved reference 'MODERATOR'). The user's answer 10 (add the dep) cannot take effect. Fix: skip a dep only when its head is already in the candidate's base (is_ancestor(head, base), or landed on T.base), so a fork-only dep's head merges into every candidate off main; the same test for the composite branch. Repro: python3 harness/hd.py candidate central-game-session; git -C ~/src/OpenRune-Central-Server grep MODERATOR <tree> -- central-common/src/test.
