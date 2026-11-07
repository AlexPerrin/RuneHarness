---
slug: h-central-up-desktop-jav
track: harness
priority: P1
---
# tracks/central/track.sh up: a fresh desktop logs in through embedded Central's own jav_config

central-embedded-jav-config (dev/central-embedded-jav-config d18c771 on fork) lets embedded Central serve a local jav_config set by OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file:///... (javcheck passes, run 136). Its login and acc-4 cannot be judged: (1) tracks/central/track.sh up 1 fails at desktop_login.py on a fresh desktop home ('Enter started no login ... the disconnected dialog'): 2c957da removed the fixed-coordinate terms Accept / Existing User clicks with nothing reading the page in their place (alerts 38, 41, 42); (2) up passes the server no environment and publishes no Central http port, so no desktop can be pointed at embedded Central. h-central-up-sign-in does (2) for 'up token' but deps on central-embedded-jav-config and h-desktops-token-login waits on central-game-session, a cycle. Needed, with no token login: tracks/central/track.sh up <slug> mounts the filled tracks/fork/server/jav_config.ws.template into server-<slug>, sets OPENRUNE_JAV_CONFIG_URL_TEMPLATE to it, publishes Central's http port, runs no http-<slug>, points the desktop's OPENRUNE_ENDPOINT at http://127.0.0.1:<central http>/, and desktop_login.py leaves a fresh home's terms page by the component it reads (devtools dump_interface/click_component, never fixed coordinates nor anything opening a Jagex page) so the typed login reaches LOGGED_IN. Judge: up 1 with the head of central-embedded-jav-config on a fresh C:\osrs-test home reaches LOGGED_IN with no http-<slug> container.

## alert 42 fault 136 (×1, first 2026-11-07T03:31:04+00:00)
central-embedded-jav-config judge: tracks/central/track.sh up 1 fails twice at desktop_login.py (FAILED: Enter started no login ... the disconnected dialog) on the sidecar's typed login, the fresh-home form-login defect of dfdd60b/2c957da; and fork up sets no server env nor publishes Central's http port, so no up can point a desktop at embedded Central (acc-4) until h-central-up-sign-in lands. login and acc-4 left not-judged.
