---
slug: h-appended-input-reruns-dev
track: harness
priority: P2
---
# A section appended to a change by hd new --on is a new input: the dev runs again

fork-android-rsprot-242 stays parked on 'run 423 ended (handback) with this input: new' after the user's hd new --on appended 'Build the 242 tables and land' (efa5d2b). decide.py's code-run input is digest(t, why, answers, landed) (decide.py ~313): answers, deps landing, verdicts and failures are new facts, the change's own definition is not, so a user's word added with hd new --on (the driver's 'a word for a change') never reaches a parked run. Done when an appended section (or any edit of the change's body) changes the dev run's input so parked() no longer parks it, with a decide test over a snapshot where a hand-back is parked and a section is appended; fork-android-rsprot-242 then gets its dev run.
