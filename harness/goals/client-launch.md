---
slug: client-launch
track: client
target: 100
deps: [harness-device-network-block, client-devtools-login]
---
## Goal
The path from launching the official OSRS Android app with the RuneLite plugins to being in gameplay on the test
server, as short as it can be: every step on it either removed or reduced to what the app itself must do, and each
step's end waited on as an observed fact. The inventory is `harness/goals/client-launch.json`: one row per step of the
launch path ({unit, source}, source naming the script line or app screen that performs it). A row passes only by a
passing verdict on a live change that names its unit (`units:` of harness/changes/<slug>.md, `goal: client-launch`);
hd hands the passing units to the track's `measure` verb as PASSES, which prints the share of rows passing.

## Measurement
`measure` launches the app on a fresh emulator (track `up`), logs in the tester account on the test server and stops
at gameplay. Each step's start and end are timestamps from the device's own records: logcat lines of the host and the
plugins, and the devtools data tools' game state (LOGGING_IN, LOADING, LOGGED_IN, first game tick). The report
(`evidence/client-launch/measure.json`) holds, per step, its unit, start, end and the fact that ended it, and the total
from the app's process start (logcat `Start proc`) to the first game tick while LOGGED_IN. No estimate, sleep or
timeout enters the number; a step whose end is not a readable fact is reported as such and fails its row.
