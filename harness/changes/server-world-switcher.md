---
slug: server-world-switcher
track: fork
priority: P2
deps:
- h-up-second-world
---
# World Switcher: the logout tab's button opens the world switcher and a world's Switch hops through LOGOUT_TRANSFER

Blocks client-api-world-hop: Client.openWorldHopper and hopToWorld drive the game's own world switch (desktop: CC_OP on Logout's World Switcher button, then on Worldswitcher.BUTTONS with the world id), and both effects are the server's, so on the test server neither is observable.

Repro on the test server: logged in, open the logout tab and tap World Switcher: nothing opens. Source: in the fork (staging 7fba4ff1f) LogoutTabScript handles only component.logout:logout; nothing handles the World Switcher button or interface worldswitcher (69), and nothing sends LOGOUT_TRANSFER. The world list (worldslist.ws, param 17) has world 255 only, so there is no other world to hop to.

Expected (official; check against an RSProx recording of a hop): the logout tab's World Switcher button (IF_BUTTON) opens worldswitcher (69) in the logout tab's slot; a world's Switch op (IF_BUTTON on 69's list, sub = world id) is answered with LOGOUT_TRANSFER(host, world, flags) unless the player may not log out (combat), after which the client reconnects to that world. Client side (Android, static RE, evidence/client-api-world-hop/re-notes.md): server packet 0x23 in the dispatcher 0x441dd4 reads u16 world, i32 flags, host, calls setWorld 0x432748 and sets game state 45. Minimum to unblock the client: the button opens 69, Switch to a listed world sends LOGOUT_TRANSFER, and a second world in the world list served by the same test server (e.g. 256 at the same host) so a hop has a target.
