---
slug: h-desktop-no-browser
track: harness
priority: P0
---
# A test desktop cannot open a browser

Twice the user's browser opened runescape.com while a judge tested server-token-auth's ban and lock criteria (runs 123 and 144): the client's refusal pages have a top button (View Appeal Options, Recover Account) that opens secure.runescape.com, and a click or key reached it. Privacy says no desktop contacts Jagex or RuneScape; this reached them through the user's own browser. The clicks are gone from desktop_login.py, but any agent's devtools call can still reach those buttons.

Needed: no JVM of a test desktop can hand a URL to the OS. DevtoolsOwner is already a -javaagent in every JVM of an instance (tracks/fork/track.sh, JAVA_TOOL_OPTIONS), so use it: refuse java.awt.Desktop.browse and RuneLite's LinkBrowser, and whatever fallback they have (rundll32, cmd start, Runtime.exec of a URL), logging each refused URL to the desktop log. Read how the patched client actually opens a URL first; do not assume. Applies to `up` and live-desktop, never the user's own RuneLite.

Done when, on a live desktop on a locked account's page, activating Recover Account logs a refused URL and starts no browser process, and a test covers the refusal. Prove it only after the refusal is in place, with the refusal log as the fact.
