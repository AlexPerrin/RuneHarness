---
slug: client-loading-fullscreen-rotate
track: client
title: 'Loading screen: click View full screen; rotate left for landscape, right back
  to portrait'
kind: change
priority: P2
goal: client-launch
units:
- launch:loading-fullscreen
deps: [harness-device-network-block]
created: '2026-11-01T00:55:42Z'
closed: 'answer-4: The user closed this client change: the prompt is SystemUI''s immersive-mode confirmation, which no client code can accept; the fix moved to harness-immersive-confirm.'
---
The user's words: "Click View full screen during loading screen, cosmetic fix rotate left for landscape (rotate right back to portrait)". Cosmetic client fix in the official Android app with the RuneLite plugins. During the loading screen, the View full screen option is clicked (taken). Rotating the device left turns the game to landscape, and rotating right turns it back to portrait, with the layout drawn correctly each way. If the intended behaviour is unclear (who clicks View full screen, the app or the user, and what is broken today), ask with hd ask before building. Proof: on the emulator, through the devtools data tools; a screenshot only as evidence of how the screen is drawn in each orientation.
