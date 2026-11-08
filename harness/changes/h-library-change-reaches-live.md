---
slug: h-library-change-reaches-live
track: harness
priority: P1
---
# A Central or FileStore change reaches the live stack only when a staged fork change depends on it

The deploy builds staging with the library heads of the fork changes landed on staging (store.staging_composite from their submissions' composite_json); a central change with no fork dependent (central-game-session today) is never in a deploy, so its live landing (hd job deploy ok, from the job env's CENTRAL) never comes and every change off the server tracks that depends on it waits on 'dep <x> not live on the test server' forever: client-android-central-sign-in, h-live-central-sign-in-deployed. Fix at the mechanism: a library change that passed its gate and verdict (or is done on its staging) joins staging's composite on its own, so the next deploy carries it.
