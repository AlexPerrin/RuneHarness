---
slug: fork-players-see-each-other
track: fork
priority: P2
---
# Two players on the live stack at the same tile do not see each other

Run 350 (2026-11-09 UTC, live osrs-openrune:241, APK 53908ce): two mobiles logged in as distinct accounts h06df57e3cm (emulator-5564) and h49acbf16fm (emulator-5566), both at 3221,3218 plane 0 (Lumbridge spawn) from 08:15:31 UTC. Devtools list_players on each lists only its local player (count 1); the official server sends every player within view distance in player info, so each should list the other at distance 0. Done when two clients on the live stack within view list each other (list_players) and the cause is fixed in the fork.
