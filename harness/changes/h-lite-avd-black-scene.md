---
slug: h-lite-avd-black-scene
track: harness
priority: P2
---
# Agent_Lite mobile draws a black game scene

The user (2026-11-09, watching emulator-5560 of run 376, client-api-probe-self-setup): Agent_Lite:5560 shows a black screen, but the RuneLite buttons, the tick counter (top right) and the combat dummy's health overlay draw, and the dummy's health decreases, so the game runs and combat happens; only the game scene is black. The emulator runs Agent_Lite (h-mobile-light-avd) with -lowram -gpu host, graphics backend gfxstream (state/client-api-probe-self-setup/emulator.log). Expected: the scene draws as on a full mobile; a mobile up checks the scene draws (a screenshot is the evidence of how something is drawn).
