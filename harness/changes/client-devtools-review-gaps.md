---
slug: client-devtools-review-gaps
track: client
title: 'devtools: chathead anim in get_dialogue, jingles in the sound history, interact_object
  clicks offset locs'
kind: change
priority: P1
deps:
- client-devtools-login
created: '2026-11-01T05:30:04Z'
---
The three gaps of harness-devtools-review-gaps are Java in OpenRune-Developer-Tools as built by host/plugins/devtools/build.sh (re/devtools at REV 8304e71: McpTools.java, OpenRuneDevToolsPlugin.java), so they are a local patch carried in the client repo and applied on the pinned REV, like login.patch of client-devtools-login (same build.sh line; depends on it), never pushed or proposed to OpenRune-Developer-Tools; the self-updater stays stubbed. (1) get_dialogue returns the chathead's animation id (the dialogue's head model widget, Widget.getAnimationId, NPC and player heads). (2) the sound history (get_sound_history) records jingles with their id and tick (only SoundEffectPlayed/AreaSoundEffectPlayed are recorded now, OpenRuneDevToolsPlugin.java:311-323). (3) interact_object reaches a loc whose clickable model is offset from its tile (the Lumbridge castle range, loc 114 at 3212,3215: interact_object fails; quest-cooksassistant-6 used invoke_menu_action GAME_OBJECT_FIRST_OPTION, evidence/quest-cooksassistant/handoff.md), e.g. by targeting the loc's clickbox or invoking its menu entry, not its tile point. Both jars carry it (mobile dexed and the desktop classes jar). Proof in game: in a quest dialogue the expression anim id is read; a quest completion's jingle is read with id and tick; interact_object 'Cook' on the Lumbridge range cooks (or gives the pre-quest refusal).
