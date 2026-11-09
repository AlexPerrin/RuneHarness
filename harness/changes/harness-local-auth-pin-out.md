---
slug: harness-local-auth-pin-out
track: harness
priority: P1
---
# staging: local/local-auth leaves the pins so server-token-auth merges

Staging refuses server-token-auth's head e40d5e9: it conflicts in api/net/.../ConnectionHandler.kt with the pin local/local-auth (a8cae0979). Both rewrite tokenLogin and passLogin; the pin is the spike this change replaces (lu- token decoding, the fixed password android-local, SPIKE_ env). The head merges cleanly with upstream main, and it cannot avoid the conflict without carrying spike code into its upstream PR. The user's word in server-token-auth's definition: when it lands, local/local-auth leaves the pins (the user's pin list in hd.yaml). The pin also carries RsaProvider reading .data/rsa.properties (the test server's shared login key), which today's LOCAL_AUTH app builds need: keep that part as its own local/* pin (for example local/shared-rsa-key, a8cae0979's RsaProvider hunk alone off upstream main) unless the client already ships the server's key, and drop local/local-auth from hd.yaml pins, so staging is rebuilt with the head merged. Mechanism gap behind it: a change that supersedes a pin has no step that takes the pin out when the change reaches staging; the conflict lands on the change's dev, who may not edit the user's pin list or push local/* refs. Fix it where staging is built (act.stage / hd.yaml pins), not per change. The user's yes is needed for the pin list edit if the definition's word is not read as covering it.
