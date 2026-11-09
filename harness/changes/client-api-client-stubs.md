---
slug: client-api-client-stubs
track: client
priority: P2
goal: client-api
---
# Client setters still ClientStub throws on Android: camera, login screen, display/engine

evidence/client-api/api-probe.tsv (90.3%) reads inert with 'ClientStub (throw: UnsupportedOperationException ... not implemented on Android yet)' for 25 Client/GameEngine methods. Camera: setCameraMouseButtonMask, setCameraPitchRelaxerEnabled, setCameraSpeed, setFreeCameraSpeed, setInvertPitch, setInvertYaw, setOculusOrbNormalSpeed. Login screen: setUsername, setPassword, setOtp, setLoginScreen, setShouldRenderLoginScreenFire. Display/engine: changeMemoryMode, setGpuFlags, setScalingFactor, setStretchedIntegerScaling, setStretchedKeepAspectRatio, setUnlockedFps, setUnlockedFpsTarget, setCompass, setMinimapTileDrawer, GameEngine.initialize, resizeCanvas, setConfiguration, unblockStartup.

Each maps to the game's own field or function (Ghidra on re/ghidra, offsets.md) and the probe reads its effect where it lands (the game field, a getter, the frame), as desktop's mixins do; where the Android game has the state under another form (touch camera, its own fps cap), the setter drives that. Done when every one of these rows passes on the mobile measure with no pass lost. Split per mechanism (camera / login screen / display-engine) if one run cannot carry all three; file the split with hd new --goal client-api.
