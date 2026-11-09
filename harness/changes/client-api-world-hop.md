---
slug: client-api-world-hop
track: client
priority: P2
goal: client-api
---
# Client.hopToWorld, openWorldHopper and changeWorld do nothing on Android

evidence/client-api/api-probe.tsv (90.3%): hopToWorld and openWorldHopper are ClientStub throws, changeWorld changes none of AndroidClient's 67 fields and makes no native call (world 255 before and after). Desktop hops through the game's own world-switch path. Done when the three drive the Android game's world switch (Ghidra: the login-screen world switcher and the in-game hop), the probe checks the effect (the hopper opened; the client sent the hop to the asked world), and the rows pass on the mobile measure. If the test server's single world makes the effect unobservable, file the server blocker with the repro (hd new <slug> --track fork --blocks client-api-world-hop).
