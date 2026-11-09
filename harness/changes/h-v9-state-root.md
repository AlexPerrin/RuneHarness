---
slug: h-v9-state-root
track: harness
priority: P2
---
# v9 devtools bridge and desktop_login use the live checkout's state root, not the v9 root



## alert 4 fault 13 (×1, first 2026-11-03T04:30:39+00:00)
v9 .mcp.json runs the live checkout's mcp/devtools_bridge.py (/home/alex/osrs-harness/mcp), whose token() reads /home/alex/osrs-harness/state/<slug>/up.json, v8's tree: every osrs-devtools-desktop call on a v9 up's desktop gets 'answers only the up that started it' (401); also track.sh up exports no HD_ROOT, so desktop_login.py defaults to ~/osrs-harness (worked around by HD_ROOT=v9 root on up)
