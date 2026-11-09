---
slug: harness-stage-deploy-tracks-only
track: harness
priority: P1
---
# staging merges only for tracks that deploy a test server

stage_due (harness/decide.py) merges a head into staging for every track with an upstream, but staging exists to deploy the test server (ARCHITECTURE: 'Stage --> TestServer : server tracks'; the deploy guard at decide.py:416 already requires 'deploy' in T.recipes). The lab track has no deploy recipe, so lab-hello (9d8eaaf) and lab-ci-red (ab2897e), two independent PRs that each append a line to README.md, conflict on a staging tree nothing uses: event merge-conflict '9d8eaaf README.md' and dev_due re-runs lab-hello's dev, which cannot resolve it without putting lab-ci-red's commit in its PR. Fix: stage_due returns None unless 'deploy' in T.recipes (same predicate as line 416), and dev_due's merge-conflict reason applies only to such tracks, so the recorded event stops re-running lab-hello; a decide test for a lab-like track (upstream, no deploy) going past stage to texts/card. Docs: ARCHITECTURE's stage_due line says 'tracks with a deploy recipe'.
