---
slug: quest-completion-recorded-ticks
track: server
title: 'Quest manager: write the end stage in the quest''s commit tick, grant the
  rewards and completion on the following ticks'
kind: change
priority: P2
deps: []
created: '2026-11-02T04:22:33Z'
closed: 'answer-2: answer-1: brown''s completion goes on the hand-in tick inside #367; no shared quest-manager PR'
---
Found by goblin-367-rsprox-dump-10 (PR #367, eaglepurerocketgrape's P2 IC_kwDOQBbPT88AAAABeeLlXg on the hand-in commit).

Root cause: content/quest/.../manager/Quest.kt setQuestStage(access, maxSteps) (completeQuest) grants the item rewards, the xp, the quest points, the completion message, the jingle and the quest scroll in the same call that writes the end stage. A quest cannot write its end stage in its commit step (with the items it takes) and have the completion follow on later ticks, so a quest either completes in its commit tick (rewards and scroll too early) or writes its end stage late (after the commit, in a second step).

Official (Goblin Diplomacy RSProx recording 2026-10-16, rev 241, evidence/goblin-367-rsprox-dump/rsprox-pages.txt): tick 1796 gobdip_main 5 -> 6 with the brown mail removed and the fade out; 1798 gold bar added and Crafting 0 -> 200 xp; 1799 qp +5, quests_completed_count +1, "Congratulations, you've completed a quest: Goblin Diplomacy", jingle and the quest scroll. GD's head ea08bce28 writes gobdip_main 6 together with the rewards and the scroll at 1798 (completeQuest after the scene), two ticks late, because of this coupling.

Fix in the quest manager (shared code, its own upstream PR off main): completing a quest writes the end stage at once and runs the completion (item rewards and xp, then on the next tick qp, quests_completed_count, message, jingle, scroll) as a queued step that cannot be lost: a long queue accelerated on logout, so a disconnect, logout or server shutdown after the end stage still grants it exactly once; a no-room reward is decided before the end stage is written (the caller keeps what it would have taken). Every quest using completeQuest keeps working; the default delay matches the recordings (verify against at least one other recorded quest completion with tools/track.sh recordings). Engine facts relied on: walk clicks are ignored while delayed (MoveGameClickHandler), clearPendingAction asserts !isDelayed, and processPendingLogout waits while isAccessProtected or a non-discardable queue remains.

Then goblin-367-rsprox-dump moves brown's completion into commitHandIn (the commit tick, with the mail and Grubfoot's look) and answers IC_kwDOQBbPT88AAAABeeLlXg naming that head.
