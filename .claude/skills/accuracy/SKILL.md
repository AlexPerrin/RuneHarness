---
name: accuracy
description: "Judge a server feature against the official game: write the accuracy spec from RSProx recordings and the wiki before code (the contract run), and check behaviour against it (dev before hand-over, qa in its verdict). Judges the contract rows accuracy, rsprox and unsourced."
---
# Accuracy (judgment; the facts come from scripts and tools)

## Sources, in order (v7 cause: 6 specs claimed "no recording" for packets the filters hid)
1. RSProx recordings and the OSRS wiki together (with the cache and Mod posts). Disagreement: cite both, follow the newer.
2. LostCity and other reference implementations: evidence for a guess, never a source; "per LostCity <file>" in the spec.
3. The RuneLite plugins that read the mechanic.
Facts: `tracks/server.sh recordings <packet|text>` (the index, every packet filter on), `osrs-mcp` (`wiki_page`,
`wiki_search`, `cache_search`, `gameval_search`). Recordings hold other players' names and chat: cite ids and packets
only, never commit or quote them.

## The spec (`evidence/<slug>/accuracy.md`, written in the contract run)
- Upstream first: an open PR or issue for the same content means theirs wins.
- One rule per mechanic: source, behaviour, what the recording shows (anims, spot anims, sounds, messages, dialogue
  order, varps per stage, interfaces, tick timings); a guess marked as such; a reconstruction named unsourced.
- Every mechanic the wiki page lists is a rule (v7 cause: the deferred cutscene cost 23 runs).
- Each rule becomes one contract row `- acc-<n> | <rule> | judge: accuracy`.

## The check (dev before hand-over; qa once, every row)
1. Re-read each source; never trust the spec's quotes.
2. Compare the branch against the recordings tick by tick, from the same build (`tracks/server.sh up`).
3. A divergence is fixed, never a caveat or a quirk entry; one the server cannot fix is `hd ask`, once.
4. Record per rule: matches, diverges (evidence), guess. A late find is also a contract miss: add the row.
