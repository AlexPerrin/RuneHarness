---
slug: h-devtools-mobile-serial
track: harness
priority: P2
---
# osrs-devtools-mobile MCP refuses every call with 'set ANDROID_SERIAL to your emulator': the bridge's mobile backend gets no serial and no tool argument names one



## alert 69 fault 307 (×1, first 2026-11-09T02:24:04+00:00)
osrs-devtools-mobile MCP refuses every call with 'set ANDROID_SERIAL to your emulator': the bridge's mobile backend gets no serial and no tool argument names one, so a run cannot reach its own mobile through the MCP (worked around by calling tools/devtools-mcp.sh --call directly with ANDROID_SERIAL)
