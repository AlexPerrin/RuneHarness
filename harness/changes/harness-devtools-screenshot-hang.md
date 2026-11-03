---
slug: harness-devtools-screenshot-hang
track: harness
title: The desktop devtools screenshot answers or fails, never hangs
kind: change
priority: P1
deps: []
created: '2026-11-01T11:45:15Z'
---
central-login-whitelist-binds-3: the osrs-devtools-desktop MCP screenshot call hung until the tool's 30-minute timeout; the run took the screenshot through the desktop's devtools HTTP endpoint directly. Expected: the bridge's screenshot (mcp/devtools_bridge.py) returns the image or an error the run can act on as soon as the client's endpoint answers or refuses, with no 30-minute stall. One test per requirement touched.
