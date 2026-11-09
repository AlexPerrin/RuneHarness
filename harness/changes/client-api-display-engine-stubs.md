---
slug: client-api-display-engine-stubs
track: client
priority: P2
goal: client-api
deps:
- h-mobile-loading-stall
---
# Client display/engine setters still ClientStub throws on Android

Split from client-api-client-stubs (camera taken there). evidence/client-api/api-probe.tsv reads inert with 'ClientStub (throw: UnsupportedOperationException ... not implemented on Android yet)' for changeMemoryMode, setGpuFlags, setScalingFactor, setStretchedIntegerScaling, setStretchedKeepAspectRatio, setUnlockedFps, setUnlockedFpsTarget, setCompass, setMinimapTileDrawer, GameEngine.initialize, resizeCanvas, setConfiguration, unblockStartup. Each maps to the game's own field or function (Ghidra on re/ghidra, offsets.md) and the probe reads its effect where it lands (the game field, a getter, the frame), as desktop's mixins do; where the Android game has the state under another form (its own fps cap, its own compass sprite), the setter drives that. Done when every one of these rows passes on the mobile measure with no pass lost.
