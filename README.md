# osrs-harness

The harness that moves changes to their live targets for two products: a RuneLite-plugin client for the official OSRS
Android app (AlexPerrin/osrs-plugins-reverse, APK releases) and an OpenRune test server (the fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code.

One loop over five nouns: a change (its definition and its contract), its tree T (base + dependencies + head), the
judgments bound to T or to the head, its targets, and the runs that worked it. One pass reads the facts (git, GitHub,
docker, processes) and does the first unmet step of every change: a script, an agent to spawn, or a card for the user.

```
python3 harness/hd.py                 # a pass, then the view: spawns, cards, questions, runs, goals, changes, alerts
python3 harness/hd.py tick --dry-run  # the view, changing nothing
python3 -m unittest discover -s tests
```

Read `docs/PROBLEM.md` (first principles), `docs/PRD.md` (the constraints), `docs/ARCHITECTURE.md` (how it is built),
`docs/HANDOFF.md` (the current state) and `docs/ISSUES.md` (the open ledger). `CLAUDE.md` holds the rules every
session and agent runs under.
