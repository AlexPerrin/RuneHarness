---
slug: h-up-second-world
track: harness
priority: P2
---
# the fork's up serves a second world (256) beside 255, so a world switch has a target

server-world-switcher (run 347) answers a world's Switch (IF_BUTTON1 on worldswitcher:buttons, sub = world id) with LOGOUT_TRANSFER(host, id, properties) read from the worlds table (Central's central/world/find_all_for_list.sql: enabled rows), and sends nothing for a world not in it. Its criterion acc-6 needs the change's up to serve two worlds on one test server; Central seeds only 255 (central/seed/dev_world.sql) and the dev may not write the database. Needed: tracks/fork/track.sh up inserts world 256 as a copy of 255's row (host, flags, activity, location, realm_id; sort_order 1; enabled 1; ON CONFLICT DO NOTHING) beside the realms update on the fresh database, before the realm restart, so Central's worldslist.ws lists 255 and 256 and a desktop that receives LOGOUT_TRANSFER to 256 reconnects to the same server (same host, the up's port mapping). Test-only: nothing in the fork. Done when: on an up of server-world-switcher, a desktop's worldslist has 255 and 256, and Switch to 256 logs the desktop back in (get_client_state world 256).
