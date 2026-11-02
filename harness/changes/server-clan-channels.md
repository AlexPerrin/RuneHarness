---
slug: server-clan-channels
track: server
kind: change
title: 'Clans: the server sends no clan channel or clan settings state'
priority: P2
branch: content/server-clan-channels
created: '2026-10-31T03:20:17Z'
deps:
- harness-no-powershell
- server-friends-chat-clan-channels
- harness-server-build-musicrepository
- harness-desktop-first-login
- harness-split-pr-waits-dep-merge
---
Split from server-friends-chat-clan-channels (the user, 2026-10-31: friends chat first, clans second, one change per PR, for upstream; #73 is months old: supersede it or open our PR over it). Blocks the client-api probe's clan rows (clan.ClanSettings 4, ClanChannel 3, ClanChannelMember 3, ClanMember 3; client change client-api-probe-reach).

Expected (official): a clan member gets CLANSETTINGS_FULL and CLANCHANNEL_FULL for their clan (and the guest clan when they join one), with deltas on change. Minimum to unblock the client: one clan whose settings and channel list the tester. Build on the friends chat change's chat-channel tab.

## Answers
- 2026-10-31T18:03:38Z The user: five PRs as proposed. This change is the clans core only: clan store in the database, founding as on the wiki (Clan Hub clerk, 5 founders with 25 hours played), up to 500 members, CLANSETTINGS_FULL and CLANCHANNEL_FULL at login with deltas on join, leave and rank change, // clan chat, the side panel (leave or rejoin the channel, leave the clan), the members list (rank changes, kick) and owner resign. Cross-world clans are a stated caveat. Guest clans, the settings interfaces, broadcasts and Clan Hall/coffer/events are filed as their own changes (server-clan-guest, server-clan-settings, server-clan-broadcasts, server-clan-hall), each after the one before it.
- 2026-10-31T18:08:05Z The user: put as much in the core as it needs to be a complete, mergeable clans feature; the clan settings interfaces move into this change (server-clan-settings is closed). Anything else the core cannot work without (from guest clans, broadcasts or Clan Hall) also belongs here; say in the PR text what stays for the later changes.
