---
slug: server-friends-chat-clan-channels
track: server
kind: change
title: 'Friends chat and clan channels: the server sends no friends chat, clan channel
  or clan settings state'
priority: P2
created: '2026-10-25T20:31:36Z'
goal: client-api
deps: [harness-server-build-tree, harness-no-powershell, harness-server-build-musicrepository, harness-desktop-first-login, harness-deploy-survives-tools-ship]
---
Blocks the client-api probe's social rows (clan.ClanSettings 4, ClanChannel 3, ClanChannelMember 3, ClanMember 3, FriendsChatManager 4, FriendsChatMember 2; client change client-api-probe-reach), which stay unreached because the client never holds a friends chat or clan.

Repro on the test server: log in the tester, open the chat-channel tab and join a friends chat (or any clan): no channel state arrives, Client.getFriendsChatManager()/getClanChannel()/getClanSettings() stay null in the Android host (the host already decodes them: host ChatChannels). Source: the fork has no sender of rsprot's UPDATE_FRIENDCHAT_CHANNEL_FULL_V2/SINGLEUSER, CLANCHANNEL_FULL/DELTA or CLANSETTINGS_FULL/DELTA (grep -r 'ClanChannelFull|ClanSettingsFull|UpdateFriendChatChannel' finds none) and no friends chat or clan content.

Expected (official): joining a friends chat sends the channel (owner, name, kick rank, members with world and rank); a clan member gets CLANSETTINGS_FULL and CLANCHANNEL_FULL for their clan (and the guest clan when they join one). Minimum to unblock the client: a joinable friends chat with the joining player as a member, and one clan whose settings and channel list the tester.

## Answers
- 2026-10-31T01:30:14Z (c) plus (a): build a minimal test-only local/* branch now (a joinable friends chat listing the joiner, one clan whose settings and channel list the tester) that never goes upstream, to unblock client-api-probe-reach; for upstream, wait for Brixx420's work on #73.
- 2026-10-31T01:34:39Z The user, revising the earlier answer: #73 is months old; supersede it, or open our PR over the top of it. Build friends chat and clans for upstream in the game server (friends chat first, clans second, one change per PR); the test-only local/* branch is no longer wanted.
- 2026-10-31T03:19:58Z The user: add the total-level-150 rule in this PR (nothing deferred): let the level-up script call the chat-channel check, so 'Matches the OSRS wiki' can be ticked. Cross-world channels stay a stated caveat (OpenRune-Central has no friends chat). Clans remain the next change.
