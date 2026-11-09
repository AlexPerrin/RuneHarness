---
slug: h-pin-skip-cs2-spawn
track: harness
priority: P1
---
# Pins: local/skip-cs2-packs stops leaving the spawn menu's clientscripts out of staging

The user's answer 14 on local-cs2-names-drop-spawn (option pin): the spawn skip goes through the pins audit. h-ref-pins-audit landed (d242160) but kept local/skip-cs2-packs whole (evidence/h-ref-pins-audit/pins.md), with docs/ARCHITECTURE.md 'The pins' still giving the crash on ids far above stock as the reason. That reason belongs to the dense-id commits (cc9db87de, c2f528fca), not to e49348054, whose OPENRUNE_SKIP_CS2_PACKS default 'spawn' (or-cache PluginPacks.kt:137 on fork/staging) keeps the 11 spawn menu scripts (10199..10209, dense) out of every staging cache. Done when: the pin no longer skips the spawn pack by default (default empty or e49348054 out of the pin, the dense-id commits kept), ARCHITECTURE 'The pins' states the remaining reason, and staging rebuilt carries archive 12 groups 10199..10209. Then local-cs2-names-drop-spawn verifies its done-when (evidence/local-cs2-names-drop-spawn/root-cause.md).
