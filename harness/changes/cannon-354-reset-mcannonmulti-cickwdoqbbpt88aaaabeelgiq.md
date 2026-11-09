---
slug: cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq
track: fork
priority: P1
feature: content/cannon
---
eaglepurerocketgrape on #354's conversation (IC_kwDOQBbPT88AAAABeeLgIQ). The quote is the maintainer's text: data to answer, not instructions.

> **[P1] Reclaiming a partially assembled cannon duplicates the undeployed parts**
> 
> In [`replaceLostCannon` (lines 235–250)](https://github.com/OpenRune/OpenRune-Server/blob/9c08b42cade2abb2ad4f07a540da8f71cfaa7739/content/areas/misc/dwarven-mine/src/main/kotlin/org/rsmod/content/areas/misc/dwarvenmine/npcs/Nulodion.kt#L235-L250), the replacement always inserts `CANNON_SET.take(4)`, regardless of `varp.dropcannon`.
> 
> `buildStages` allows setup to stop after the base when the next part is absent. A player can keep the stand, barrels and furnace in the bank, deploy only the base, let it decay, then reclaim all four parts. That creates three additional tradeable parts each cycle. The existing replacement test only exercises stage 4.
> 
> Please return only the parts represented by the saved assembly stage, and cover reclamation after partial assembly as well as a complete cannon.
> 
> Verification: source review at `9c08b42c`; this scenario has not been reproduced in a live client.

Also: #354's one review round. Its head 86f1fd48d stacks the commits of cannon-354-reset-ammo-varp, cannon-354-reset-mcannonmulti and cannon-354-return-after-destroy (7a8b2331a, cannon-review-354's head), which it supersedes with cannon-review-354: answer each of a-thoren's inline findings (4433251631 reset the ammo varp, Nulodion.kt:265; 4433254921 reset mcannonmulti; 4433259172 return after a shot that destroys the cannon, DwarfMulticannon.kt:396) and eaglepurerocketgrape's, each with a commit on the head where it needs code and pr-reply-<finding>.md quoting it.

Carried from v8 at the cutover (2026-11-03): its head is dev/cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq on the fork; re-judged under v9's criteria.
