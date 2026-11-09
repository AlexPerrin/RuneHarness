---
slug: h-client-build-shares-apk
track: harness
priority: P2
---
# client build.sh: concurrent builds share re/apk (each build copy's re/apk symlinks the main checkout's), so two builds corrupt each other



## alert 67 fault 298 (×1, first 2026-11-08T23:35:08+00:00)
client build.sh: concurrent builds share re/apk (each build copy's re/apk symlinks the main checkout's), so two builds' repacks race: baksmali 'No such file or directory' / 'expected one smali file containing only https connections are permitted, found 0' (repack-15ec37f6.log, repack-ba9d977c.log in evidence/client-api-probe-self-setup, each beside a 'build live' run); no lock around the repack
