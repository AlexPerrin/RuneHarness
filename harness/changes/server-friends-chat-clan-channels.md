---
slug: server-friends-chat-clan-channels
track: fork
priority: P2
---
Friends chat in the game server, for upstream (the clans core is server-clan-channels, the next change). Blocks the client-api probe's friends chat rows (FriendsChatManager 4, FriendsChatMember 2; client change client-api-probe-reach), which stay unreached because the client never holds a friends chat.

Repro on the test server: log in the tester, open the chat-channel tab and join a friends chat: no channel state arrives, Client.getFriendsChatManager() stays null in the Android host (the host already decodes it: host ChatChannels). Source: the fork has no sender of rsprot's UPDATE_FRIENDCHAT_CHANNEL_FULL_V2/SINGLEUSER (grep -r 'UpdateFriendChatChannel' finds none) and no friends chat content.

Expected (official): joining a friends chat sends the channel (owner, name, kick rank, members with world and rank), with the wiki's total-level-150 rule. Cross-world channels are a stated caveat (OpenRune-Central has no friends chat).

## Answers
- 2026-10-31T01:30:14Z (c) plus (a): build a minimal test-only local/* branch now (a joinable friends chat listing the joiner, one clan whose settings and channel list the tester) that never goes upstream, to unblock client-api-probe-reach; for upstream, wait for Brixx420's work on #73.
- 2026-10-31T01:34:39Z The user, revising the earlier answer: #73 is months old; supersede it, or open our PR over the top of it. Build friends chat and clans for upstream in the game server (friends chat first, clans second, one change per PR); the test-only local/* branch is no longer wanted.
- 2026-10-31T03:19:58Z The user: add the total-level-150 rule in this PR (nothing deferred): let the level-up script call the chat-channel check, so 'Matches the OSRS wiki' can be ticked. Cross-world channels stay a stated caveat (OpenRune-Central has no friends chat). Clans remain the next change.

Carried from v8 at the cutover (2026-11-03): its head is dev/server-friends-chat-clan-channels on the fork; re-judged under v9's criteria.
