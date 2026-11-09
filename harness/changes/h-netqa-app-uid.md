---
slug: h-netqa-app-uid
track: harness
priority: P2
---
# client track.sh netqa filters the app's sockets by hard-coded uid 10071; the installed app's appId is 10235 on emulator-5560, so netqa stop prints no sockets



## alert 62 fault 247 (×2, first 2026-11-08T04:30:46+00:00)
osrs-devtools-mobile MCP fails every call with 'devtools-mcp: set ANDROID_SERIAL to your emulator': the bridge launches tools/devtools-mcp.sh with no serial and no per-call way to name one; worked around by running the backend with --call directly
