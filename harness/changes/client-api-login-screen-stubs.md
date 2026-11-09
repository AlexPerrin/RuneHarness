---
slug: client-api-login-screen-stubs
track: client
priority: P2
goal: client-api
deps:
- h-mobile-signin-no-redirect
---
# Client login-screen setters still ClientStub throws on Android

Split from client-api-client-stubs (camera taken there). evidence/client-api/api-probe.tsv reads inert with 'ClientStub (throw: UnsupportedOperationException ... not implemented on Android yet)' for setUsername, setPassword, setOtp, setLoginScreen, setShouldRenderLoginScreenFire. Each maps to the game's own login field or function (offsets.md: login page global 0xace678, input field 0xaae4f4, field setters 0x47964c/0x479990; Ghidra on re/ghidra) and the probe reads its effect where it lands (the game field, getUsername, the frame), as desktop's mixins do. Done when every one of these rows passes on the mobile measure with no pass lost.
