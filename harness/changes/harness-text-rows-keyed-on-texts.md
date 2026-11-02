---
slug: harness-text-rows-keyed-on-texts
track: harness
title: A row that reads the public texts is keyed on them, and the texts row checks
  every text posted
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T19:41:31Z'
---
Sweep 74 P3-a: every row's key is the tree plus the tools files (hd.py:1234-1253 key, ROWKEYS hd.py:1724, :1839); rows() keeps a stored result on a key match (hd.py:3181-3185); but text.py texts and evidence read $EVIDENCE/*.md outside the tree, so their result stays ok however the texts change. goblin-367: state/goblin-367-rsprox-dump/row-check-texts.json 'texts: ok' at 18:50:57Z; goblin-367-rsprox-dump-19 wrote three evidence/goblin-367-rsprox-dump/pr-reply-*.md at 19:30:25Z; the change went 'gated; waiting for the user's yes' at 19:30:43Z (events.jsonl:11001) with no new gate (proc-gate.json 18:50:51Z), so the card carries replies no row checked (clean on reading). Also text.py:53-66 (server tools) checks only pr-title.txt, pr-body.md, pr-comment.md for fork-PR links while public_texts (hd.py:2864-2868) posts one_comment([push, *replies]) with every pr-reply-*.md. Key such rows on the public texts' digest (digest(json.dumps(public_texts(ctx, ch))), hd.py:1942, :3368) and have texts cover everything public_texts posts. Evidence: evidence/monitor/sweep-74.md

Also (filed): The server test row runs a module's integration tests
Sweep 78 P2-a: server tools tools/gate/gate.sh:50 gradle_check runs only <module>:test and :spotlessCheck, while upstream CI runs ./gradlew assemble test integration (.github/workflows/ci.yml:72). server-levelup-guide-messages-3 handed over 5212212 (state/events.jsonl:11044); its local test row passed (state/server-levelup-guide-messages/test.json: :api:stats-plugin:test ran BoostDecayTest and LevelUpJingleTest only) while its own LevelUpGuideTest in api/stats-plugin/src/integration/ failed 2/8 only in gate CI run 41512542876 (:api:stats-plugin:integration FAILED, 19:55:57Z): a 13-minute CI round trip, then 'gate failed: dev' (11082). Run <module>:integration for modules with the integration-test-suite plugin or src/integration, and say so in the server tools track.md. Evidence: evidence/monitor/sweep-78.md

Also (filed): The client build cache hits: the modulus check survives grep's early exit
Sweep 79 P1-a: client tools tools/build/build.sh:13 sets set -euo pipefail and carries() (:26) runs unzip -p <apk> lib/.../liblibs.hal.system.osclient.so | grep -aqF "$m"; grep -q exits at its first match, unzip dies of SIGPIPE, the pipeline returns 141 (5/5 on evidence/live/fef4307c9fc524a82e775ca1c0bd760f222836c4.apk though the plain grep matches). So the cache test (:39) fails and every server/central/desktop up (server tools/track.sh:179 flock state/client-live.lock ... build live) rebuilds the live APK one at a time (another build live a32dd70 started 20:09:57Z right after state/live/build.json ok; harness-desktop-relogin-js5 and server-clan-guest ups waited from 20:06-20:07Z). tools/release-dev.sh:52 (pipefail :15) would refuse every release with 'does not carry the live pair's modulus'. Introduced by 53b837c. Avoid the SIGPIPE (grep -aF >/dev/null, or extract then grep). Evidence: evidence/monitor/sweep-79.md

Also (filed): Only the rows that read the texts re-run when the texts change
Sweep 80 P4-a: 7f1aaa9's tx (hd.py:1253) hashes texts_key into every check row on a public track, but docs/PRD.md:304 says only the text rows re-run; goblin-367's row-check-spotless re-ran 20:12:37-20:15:27Z (~3 min gradle) on an unchanged tree at the re-key (events.jsonl:11132-11147). Key only rows whose command reads $EVIDENCE (texts, evidence, subject). Also P5-a: server tools track.sh:61 (ready) and :249 (down's offline guard) run docker logs | grep -q under pipefail (:31): once a container's logs pass 64 KB after 'Server ready in' it returns 141 and down skips offline(), not saving characters; gate.sh:150 avoids the pattern with <<<. Evidence: evidence/monitor/sweep-80.md
