---
slug: harness-dropped-change-superseded
track: harness
title: 'a change the user''s answer drops, its scope filed into another change, stays
  due: no record supersedes it'
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T18:26:27Z'
---
Alert (planner-33): server-js5-idle-relogin: dev run server-js5-idle-relogin-4 handed back its record, yet its step is still due on the same input: no run is listed. Evidence: run -3 asked (16:21:09Z) whether to drop the JS5 idle fix ff2b6e614 (the idle close is not the login failure's cause); the user answered '(b) Drop the idle-drop fix' (18:19:24Z); run -4 joined the finding into harness-desktop-one-login-path (commit 0cc6d59, event joined) and handed back 'filed harness-desktop-one-login-path'. produced() counts the join as its record, but nothing changes the change's facts: no dep event, no superseded mark, so nxt() still says 'dev run due: head ff2b6e614 not handed over' on input ["", "3429f63d42ad", 0] and unlistable() raises the alert. Root cause against the workflow (a change ends done or closed by the user): the user's drop answer moves the change's whole scope to another change, but the record path has no form for it. hd new --supersedes is the one mechanism that holds a replaced change with no runs until the user closes it, yet it accepts only open harness changes (cmd_new: 'supersedes only open harness changes') and sets into=None, so it cannot apply to a filing that joins an open change, nor to a server change. Fix in that one rule, no new one: --supersedes accepts any open change on any track, and composes with a join (the join target is the carrier; retarget() moves waits on the superseded change to it, mark() and the superseded event as now); the dev role (and the hand-back 'filed <slug>') states that a change whose answer drops it is superseded by the filing that carries its scope. Acceptance: a test where a server change's own run files a join with --supersedes <its slug> leaves that change superseded, no run listed and no unlistable alert; server-js5-idle-relogin is marked superseded by harness-desktop-one-login-path (deps on it retarget there) and shown to the user for hd close. One test per requirement touched.
