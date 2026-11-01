---
slug: harness-no-powershell
track: harness
title: Device and desktop bring-up run from bash, with no PowerShell scripts
kind: change
priority: P0
deps: []
created: '2026-11-01T00:33:03Z'
---
The user's word: prefer less complexity, roll into bash. Windows refuses the track scripts' PowerShell files under the user's RemoteSigned policy. They load from the \\wsl.localhost UNC path, so Windows treats them as remote, and they are unsigned. The client's tools/up.ps1 blocks every client up and measure (harness-client-measure-repo-root-2, evidence/harness-client-measure-repo-root/measure-client-api.log). The server's tools/server/desktop.ps1 blocks the desktop clients in track.sh up (server-world-entities-2, evidence/server-world-entities/in-game.md). Move each script's steps into the track scripts' bash, calling the Windows programs (adb.exe, emulator.exe, the desktop client) directly through WSL interop. Delete the .ps1 files, and use no -ExecutionPolicy flag. Keep up.ps1's behaviour: boot on a free even port, wait for sys.boot_completed, install the APK, grant Chrome local network access, back up the device, put devtools and the three default plugins in place, print SERIAL, and on down check the restore and stop the emulator. Do the same for desktop.ps1. Carry the commits on the client's client/harness-v8 and the fork's local/harness. Prove it with one real client up/down and one server up with the desktop clients. One test per requirement touched.
