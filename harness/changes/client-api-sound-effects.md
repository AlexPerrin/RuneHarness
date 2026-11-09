---
slug: client-api-sound-effects
track: client
priority: P2
goal: client-api
---
# playSoundEffect: the volume is ignored and the positional forms raise no AreaSoundEffectPlayed

evidence/client-api/api-probe.tsv (90.3%), mismatch: playSoundEffect(id, volume) plays sound 2268 but not at volume 32 (desktop applies it); playSoundEffect(id, x, y, range) and (id, x, y, range, delay) raise SoundEffectPlayed, not AreaSoundEffectPlayed, for 53,50 range 1. Desktop queues the positional forms as area sounds and sets the volume for the plain one. Done when the host calls the game's area-sound path for the positional overloads and passes the volume, the events match desktop's, and the 3 rows pass on the mobile measure.
