---
slug: client-devtools-upstream-main
track: client
priority: P0
deps:
- server-resumed-session-logout
---
# Both clients run upstream OpenRune-Developer-Tools main (de754c1): 120 tools over our pin's 47

host/plugins/devtools/build.sh pins OpenRune/OpenRune-Developer-Tools at REV=8304e71 (47 MCP tools). Upstream main de754c1 (18 commits on) has 120: every one of the 47 plus act, observe, find_path, get_status, get_combat_state, set_prayer, bank_action, shop_action, trade_action, hop_world, logout, item_def/npc_def/object_def, list_quests and more. Move REV to upstream main as the build reads it then. Its UpdateChecker is now notify-only with checkAsync alone, skipping builds versioned -local (ours): the StubMethods list names methods that no longer exist (check, fetchLatestRelease, download, scheduleSwapOnExit), so it stubs checkAsync alone or goes. Its build.gradle adds test deps only; the javac build over src/main/java stays. Regenerate the harness's mcp/devtools-snapshot.json from a live client's tools/list. Done when the APK and the desktop sideloaded jar carry the new REV, the mobile and desktop devtools data tools (get_client_state, get_inventory, list_npcs, get_status) answer on a LOGGED_IN client, and network-qa passes (the update check must reach no host). Note: tracks/fork/track.sh live-desktop fails at sign_in today (the live Central answers no TLS on 8443; hd fault filed by run 215).
