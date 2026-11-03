---
slug: harness-deprecate-head
track: harness
title: The user chats with the orchestrator; skill head and main's relay are removed
kind: change
priority: P1
deps: []
created: '2026-11-01T12:24:50Z'
---
The user's words: 'No deprecate this /head function' (after: 'If this session relays to orchestrator whats the point, I can just chat with orchestrator'). Main only relays (hd tell), so it adds a window and a hop and nothing else. Expected: the user chats with the orchestrator session directly; it shows cards, questions and alerts itself and acts on the user's other words at once. The user's yes and close stay out of any agent's reach: the user types them, `! python3 ~/osrs-harness/hd.py approve <slug> <head>` / `close`, in the orchestrator window (first observe that a `!` command fires no PreToolUse, so hook.py's deny_users_word still holds the orchestrator's own tool calls). Removed: .claude/skills/head, hd tell / hd heard / state/inbox.*, the `message` view, main's context-limit notice in hook.py, the head wake-watch, every 'main' reference in CLAUDE.md, the orchestrator brief and docs (PROBLEM P11 and the main paragraph, PRD R2, ARCHITECTURE's Main and the hd tell row); the orchestrator brief gains the card/question/alert steps of the head skill. One test per requirement touched (R2, R4, R6).
