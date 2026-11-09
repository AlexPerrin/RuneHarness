# osrs-harness

The harness that moves changes to their live targets for two products: RuneLite plugins in the official OSRS
Android app (AlexPerrin/osrs-plugins-reverse) and the OpenRune test server with its contributions upstream
(AlexPerrin/OpenRune-Server, -Central-Server, -FileStore, -Developer-Tools). It is neither product's code.

Agents build a change against criteria agreed before the code; scripts check it; an evaluator judges it; a public act
is one card the user approves; the harness publishes exactly that. Everything decided is a row in one SQLite ledger.

```
python3 harness/hd.py                 # a pass, then the view
python3 harness/hd.py tick --dry-run  # the view, changing nothing
python3 -m unittest discover -s tests
```

Read `docs/PROBLEM.md`, `docs/PRD.md` and `docs/ARCHITECTURE.md`; `CLAUDE.md` holds the rules every session runs under.
