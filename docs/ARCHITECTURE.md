# Architecture of the harness (hd)

The solution to docs/PROBLEM.md that meets docs/PRD.md (R1–R8).
One loop over five nouns: a **change** (definition and contract), its **tree** T, the **judgments** bound to T or to the head, its **targets**, and the **runs** that worked it.
`next(change)` is the first unmet of a fixed list;
everything shown or acted on is read off it.

```
hd.py             the loop: next(change), facts, records, the pass, the public act (console card and carry); commands below
hd.yaml           repos (each fork with its upstream), paths, `mechanisms` (the harness components a harness change names), the agent count, the context limit, the fork's permanent pins, `hold` (the user's held band, e.g. P1;
                  the orchestrator sets and removes it on the user's word)
hook.py           SubagentStart/Stop: run start (the run named by the brief path in the agent's own transcript, <session>/subagents/agent-<id>.jsonl;
                  else its first tool call binds it;
                  an agent whose brief names a run already ended is stopped at once, `continue: false` naming the run and why it ended, the run left ended) and end, each a fact file in state/facts/ (a hook never takes the state lock), then the pass started without waiting;
                  a stop fires at each idle turn and leaves the run live (usage, last line), refused (decision block) while a background command or monitor the agent started has no task notification yet;
                  the stop after its SubagentHandback ends it;
                  its record is newer than its start and the change's last answer, a filing its own only when filed from its slice (the `new`, `joined` or `limit` event's `slice`);
                  PreToolUse: a subagent or the orchestrator may not `hd approve` or `hd close` (the user's `!` command fires no hook);
                  the orchestrator's session may not AskUserQuestion (its definition's frontmatter holds only name and description, so a reread carries all of it);
                  a git commit naming harness/ is denied while the definitions hold a dependency cycle;
                  a run's Bash command, or one of an agent it spawned (its meta file's parentAgentId, at any depth), denied by none of these starts with a line `hd scope <run>`;
                  a run's SubagentHandback is denied while a background command, monitor or subagent it started has no task notification, TaskStop result or 'No task found' yet (a run cannot TaskStop its subagent: it asks it with SendMessage to return), and each subagent's hand-back is kept as evidence/<slug>/subagent-<id>.md;
                  SessionStart (compact): an orchestrator session whose start-time definition is not the live one is given the live one (hd.reread);
                  PostToolUse: the orchestrator's TaskStop of a run's agent (one a SendMessage resumed after its hand-back too) ends the run as `hd stop` does, a fact the pass folds;
                  a run hands off at the context limit;
                  else a run whose change's up.json lists desktops, after IDLE_CALLS tool calls with no desktop devtools call since that up or its last devtools call, is told once to `down` until it next plays.
                  An agent whose <session>/subagents/agent-<id>.meta.json names a parentAgentId (a `reader` a run spawned) is part of its parent's run, not a run: none of the above binds, holds, refuses or ends it (the deny rules still apply);
                  once that run has ended it stops (`continue: false`) at its next tool call, since neither the run nor the orchestrator's TaskStop of the run stops it;
                  a `reader`'s Bash command that writes (a redirection to a file, rm/mv/cp, git that moves a ref (a `git branch` that creates, deletes, moves or retracks one;
                  its listing forms read), track.sh up/build/gate/down, docker run, a gh or hd write (a `gh api` with a non-GET method, or with fields and no method named)) is denied
tools/track.sh    the harness track's script;
                  tools/track.md its rules and seed rows;
                  tools/docfmt.py writes the source docs one fact per line (a break after each semicolon and sentence end, a table a block per row), and its --check fails the docs row on a doc it would change.
                  Each product repo holds its own track the same way (the fork's on branch local/harness): build | up | down | gate | ship | measure | log <slug> [T], blocking on facts, the build in its tools/build/build.sh, the gate and the contract rows' verbs in its tools/gate/gate.sh (which sources build.sh);
                  its judgment skills under its .claude/skills/
.claude/agents/   orchestrator.md (the driver session), dev.md, qa.md, planner.md (cross-track planning and monitoring), reader.md (a run's read-only lookup, returning its conclusion);
                  each run's role file (dev, qa, planner, reader) names the roots a file search starts from (this repo, ~/src, ~/osrs-plugins-reverse, ~/.gradle) and forbids one from `/`;
                  dev.md and qa.md have a wait block on an observable fact, never a `pgrep -f` on text the waiting command itself carries, a background task's output file or a bound of time or tries;
                  a step runs in the foreground and a game event is waited on with a devtools wait_for
mcp/              serve.py runs each server of .mcp.json (`serve.py <name>`, its command line in servers.json): once a file in mcp/ changes it holds the next request, lets the requests in flight answer, stops the server and runs itself again, replaying the session's initialize (its answer dropped) and the held request, and sends tools/list_changed;
                  osrs-mcp (cache, wiki, gamevals);
                  the devtools front (desktop: POST to a desktop's devtools port, each call in its own thread so the runs sharing it never queue behind one another, a tool's `port` names it and a call naming none is refused, and walk_to walks any distance in minimap clicks of 12 tiles until the player stands on the tile or a click moves it no closer, every answer names a session that dropped to the login screen, and every request is answered: the netstat probe for a listening port waits NETSTAT_WAIT at most, its start included, a desktop call waits ANSWER_WAIT past its own timeoutMs at most, the whole call with its token read, and an exception is an error answer;
                  mobile: the client repo's bridge), answering with none running from a cache or the snapshot
harness/          goals/, changes/ (definitions, committed); state/, evidence/ at the root, git-ignored
tests/test_hd.py  one class per requirement, over fakes of git, gh, docker and the process table
```

- `hd`, by the orchestrator: prints spawns (`Agent(<role>, "Read and follow state/briefs/<run>.md")`), cards (each act the carry does and each exact text, the yes and no commands), questions, runs, goals, change facts (R7)

- `hd approve <slug> <head>`, by the user, as a `!` command in the orchestrator's window: at the user step only: `state/<slug>/approval.json` {head, texts: the digest of the card's texts}

- `hd ship <slug> <head>`, by the pass (the public step's script): carries the approved head upstream or publishes the release, re-checking the yes;
  records `ship.json` (R4)

- `hd answer <slug> [--waive <row>] <text>`, by the orchestrator, with the user's words: an answer appends a contract row (refused on a closed change: file a change);
  `--waive` names a script row the hand-over and gate then skip

- `hd hold <slug> [--all|--lift] [<why>]`, by the orchestrator, on the user's no or word (a word only on when it ships is a hold or its lift with the why, never an answer row: an answer row lists a dev run): `state/<slug>/hold.json` at the head: no card at that head, the pass removes it once the head moves;
  --all: `held: all[: <why>]` in the definition (the orchestrator commits it), no card at any head;
  --lift removes both

- `hd close <slug> <text>`, by the user, as a `!` command in the orchestrator's window: the answer row, and `closed: answer-<n>: <text>` in the definition (the orchestrator commits it): the change is done, its runs end, it leaves T_int and holds no dependent

- `hd stop <run>` (the orchestrator's TaskStop of the run's agent ends it the same way, by the hook's stopped fact): ends the run's record, so it frees its agent slot (and its own agents stop at their next tool call, which the slice's stop returns at once when they wait on a command) and stops the run's processes: its slice, then each Windows process a track script recorded under it in `state/winpids/<slice>/<pid>` (its image, a record the script's `down` drops once it ended that process), by `taskkill /F /PID <pid> /FI "IMAGENAME eq <image>"`, then removes the slice's temp root `state/tmp/<slice>/`

- `hd scope <run>`, by the hook, as the first line of each Bash command of a run: moves the command's shell (its parent) into a scope of the run's systemd user slice `hd-<run>.slice` (each `-` of the name a `_`) and returns once the shell is in it: every process the command starts, reparented or not, is the run's;
  the scope is `hd-<run>-<task>.scope`, the task the basename of the shell's output file `<task>.output`, so the hook's PostToolUse on the run's TaskStop of that task stops the scope (Claude Code ends only the shell);
  the hook's next line exports TMPDIR as the slice's temp root `state/tmp/<slice>/` (hd scope makes it), so every temp file of the run goes with its slice;
  a failure is one stderr line, the command runs on

- `hd ps`, by a run: lists the processes of its shell's run slice, pid and command line, the asking command's own excepted, so a run finds its own hung step and kills it

- `hd new <slug> ... [--blocks <change>] [--mechanism <m>] [--limit-of <change>] [--supersedes <a,b>]`, by a planner, the orchestrator, a dev, the user: writes a definition;
  each change it makes wait has its listed, unspawned runs ended by a `waits` fact at once, so their spawn is refused;
  `--blocks` adds it to that change's deps (a dev's fix outside its track);
  refused when its deps close a dependency cycle.
  A change's mechanism is its `mechanism`, required on the harness track and one of hd.yaml's `mechanisms` (a product change's is its slug);
  a filing on a mechanism with an open change it neither waits on nor blocks (transitively, through its `--deps` and `--blocks`) and no open `hd ask` holds joins that change instead (a held one joins nothing and counts in no merge alert until answered): its text appended to the body and as an answer row `filed by <filer>` (no `answer` record: it outdates no run's record), scope the next hand-over takes, or a dev run on top of a head that is done without it;
  `--limit-of` records the finder in `limit-of` and is refused on a mechanism in the finder's scope (its own and, transitively, its `limit-of` changes');
  the finder waits on the fix as with `--blocks`, whether the filing is new or joined;
  `--supersedes` marks those open harness changes `superseded: <slug>`: each holds with no runs until the user's `hd close`;
  each pass raises one user's alert per superseded change naming its pasteable `! python3 <root>/hd.py close` command, as a card names its own;
  every dependency on a superseded change or on the filing (`--blocks`, `--limit-of`) is rewritten to the change that carries the fix, the new one or the one it joined, cycle-checked

- `hd show <slug>`, by the orchestrator: the definition, contract, every verdict, the build and gate lines, the hand-off file (a run reads its brief instead)

- `hd handover <slug> [summary] Limits: none|limit:<slug>...`, by dev: reads the dev ref (pushed;
  a harness one local, never pushed;
  no sha typed), runs every `check:` row of the contract (a `tools/` script, a unittest run or `true`;
  anything else runs as `false`), refuses on any failure, a conflict, an empty evidence dir, a missing `Limits:` section, an entry in it that is not `limit:<slug>` (a limit in prose is in scope: fixed, never stated) or a `limit:<slug>` that is no change or is in the change's scope, records {head, T, given} (given: the count of answer rows the handing dev run's brief held when written, or its last SendMessage told it (the hook's `told` fact), the hand-over's own count when no run;
  answer-n is the nth row, so a row above that count, and above every answer row the head's last verdict judged, is late for that hand-over: never ordered by time)

- `hd verdict <slug> <head> <rows.json>`, by qa: every row pass, fail or not-judged, appended;
  keyed to the head and `judged`, the hash of the rows without a script (a check or gate row is gated, never judged);
  `run` names the change's started, unended qa run, and with none (the pass ended it, or no qa runs) it refuses;
  refused if a row is missing, or not judged with none failing

- `hd tree <slug> <commit>`, by a track script: the T commit and tree of a working-copy snapshot, so a dev builds T

- `hd rows <slug> <T commit> <build copy>`, by a track script's gate: every `check:` row, then every `gate:` row (fork CI among them) only when every check passed, whatever the file's order, at the track root with `BUILD` set;
  exit 1 names the failures;
  a row exiting 75 is held (the step that failed reads nothing of the head: its source is down), and only held rows exit 75: the gate records no result and the pass starts it again;
  a row ended by a signal is held the same way only when the harness sent it while the row ran: every stop of the pass (a script's, a slice's) first writes its time to state/stopped, which the row reads at its end;
  any other end (the head's own crash) is its result;
  a build or a container check that fails for the host's cause, not the tree's (`hosted` in each server and Central tools/build/build.sh: 'cannot allocate memory', 'no space left' (a full disk), docker not answering, a container name a killed run left, exit 137 while the host's OOM killer logged a kill), exits 75 the same way, so it is never 'build failed: dev';
  a tree's own failure (a compile error, a failing test, its container's own --memory limit) records ok:false

- `hd room <docker run ...>`, by a track script, for each build and check container: under `state/room.lock`, runs it (exec, the same pid) once its --memory and --cpus fit beside every held entry of `state/room/` within the host's MemTotal and nproc (read from /proc/meminfo and the CPU affinity), else records itself waiting and blocks on the pidfds of the held ones until one ends, never a timer;
  a dev's own `tools/track.sh build` goes through it as the pass's builds do

- `hd ask <slug> <text>`, by agents: refused while a question is open on the change

- `hd commit <path>... -m <msg>`, by the orchestrator: commits those paths of the live checkout alone, authored as Alex Perrin with the co-author line, then pushes the live branch to origin, under `state/ship.lock`: never at once with a ship's merge

- `hd tick`, by the timer, the hook: one pass: a dry pass reads the world (git, GitHub, docker, each read once, memoised;
  a fetch another pass has in flight is waited on and its result taken;
  every GitHub read goes through state/gh, each page conditional on its ETag) outside the state lock;
  under it the pass folds the hooks' facts into the run records, re-reads the state, decides and writes;
  a pass whose hd.py a ship moved since its process loaded it acts nothing there and re-execs the live hd.py;
  builds, gates and ships start in their own systemd scopes;
  under HD_SUITE they stay in the suite's cgroup, each in its own session, so a suite's processes end with it and no loop scope is its

## Data

```
harness/goals/<slug>.md        slug, track, target (a number: a goal without one is skipped as a bad definition), deps;
                               measured by the track's `tools/track.sh measure`;
                               server-content.json, regenerated by server-content.py, is its inventory
harness/changes/<slug>.md      slug, track, kind (change|release|local), priority (P0 a blocking harness fix, P1 a non-blocking harness improvement that cuts the time to P2 work, P2 our upstream changes, P3 features, P4 new quests;
                               a harness change P1 at least), deps, goal, units, pr, finding (comment ids carried), network, version, closed;
                               body
evidence/<slug>/contract.md    rules: {AGENTS.md: <blob>, CONTRIBUTING.md: <blob>};
                               rows `- id | text | check: <cmd> | judge`;
                               a track seed row the file lacks (by id) is written into it by the pass at a head not carried upstream (`hd.unseeded`);
                               a row tagged `| upstream` (it judges or checks the upstream PR's texts or commits) seeds only a change that opens one (`hd.upstream`)
evidence/<slug>/               accuracy.md, pr-title.txt, pr-body.md, pr-comment.md (the push summary;
                               a reply-only change's: its reply), pr-reply-<finding>.md, release-notes.md, in-game evidence, handoff.md
state/<slug>/handover.json     {head, T, tools, given}         state/<slug>/gate.json      {T, ok, detail}
state/<slug>/verdicts.jsonl    {head, contract, judged, rows{id: pass | fail: note | not-judged}, rules{file: blob}, run}   appended
state/<slug>/ask.json          {text}   hold.json {head, held}: the user's no at a head
state/<slug>/approval.json     {head, texts}: the user's yes   ship.json {head, ok, fault: head | carry, detail}: the carry's result   opened.json {pr, head}: the PR the carry opened
state/<goal>/measure.json      {tree, value, report}           state/live/tree.json        {tree, commit, heads, names}
state/runs/<name>.json         {role, change, step, input, brief, given, console_pid, console_start, agent_id, transcript, started, ended, record, last, usage, handoff_told};
                               runs/by-agent/<id> → name (<id>.idle: the hook's desktop idle count)
state/facts/<ns>-<pid>.json    the hooks' facts not yet folded {fact: bind|resumed|end|stopped|told|context-limit, run, ...}, one file each;
                               the fold deletes each it applied, a run record keeps the last applied id (`fact`) so a reader applies the rest once
state/fetch/<hash>             the last result of one clone's remote fetch, flocked while it runs: a pass that finds it held waits and takes that result
state/gh/<hash>.json          {url, code, etag, body, next}: the one cache of GitHub REST reads, keyed by URL, shared by passes, gates, dry-runs and the carry (its PR, CI and comment reads, the CI wait polling them afresh);
                              each read sends If-None-Match (a 304 costs no quota);
                              HD_OFFLINE (every `hd tick --dry-run`, check-dry-run's included) reads it alone and fetches no git remote: never the network;
                              gh/quota.json {reset, at, url}: GitHub refused on its quota, every GitHub read is unknown (its steps hold, an alert) until GitHub's reset
state/briefs/<run>.md          the prompt;
                               state/events.jsonl  one line per state change (rotated at 20 MB;
                               read streamed, each byte once per process);
                               state/wake.orchestrator  the lines new to its sections, state/seen.orchestrator.json  the lines it has seen and the last head shown of each change's card;
                               state/orchestrator-read/<pid>-<start>  the orchestrator.md blob `hd` last printed that session in full
state/<slug>/proc-<script>.json {pid, start, args, key, rows, attempts, room} (key: the key its result is recorded under, none for a carry; rows: a gate's row keys; attempts count on the same args and key since the last result or the script's last change, raised once at 3;
                               room: a build's [memory, CPUs], the largest container its tools/build/ names);
state/room/<pid>.json          {pid, start, mem, cpus, owner, held}: one container `hd room` admitted (held) or holds waiting;
                               owner: HD_PROC, `<slug>/<script>` of the pass's process it runs under, '' for a dev's
state/<slug>/tools-conflict-<repo>.json {head, onto, detail}: the pass's rebase of a carried tools head stopped, its files named; repair-<name>.json {attempts}: a script or repair in flight
fork local/merge/<a>-<b>       a recorded resolution of heads a and b (b may be the base), used by T_int while a is an ancestor of the head, b of the current partner, and it merges (a later head on top)
```
Every `state/` JSON record is written to a temp file beside it and renamed over it (`hd.write`, each track script's writers), so a reader sees the old record or the new one, never a partial one.
T = `git merge-tree --write-tree` of the base, the dependencies' heads and the head, made a commit with `commit-tree`, dated the newest of its parents' committer dates (the same inputs give the same commit), so a copy can check it out;
a merge-tree conflict only in content of the source docs is merged line by line (`hd.merge_lines`: each side's changed lines kept, a conflict only where both change overlapping lines differently), so neighbouring facts never conflict;
the integration tree T_int is the same over every gated open server head plus the permanent pins.
A head stays in T_int (a Central head live) while its gate passed at the same tree under an earlier tools key, until its re-gate's result replaces that record (`gated(kept=True)`), so a tools ship takes no content off the live server.
A head whose last verdict fails is not gated (`hd.passed`), so it leaves T_int and unblocks no dependent;
a change whose target is live (not upstream main or a tag) is done only once its last verdict passes, since another change's deploy carries a gated head before it is judged.
Build and gate have their own keys when the track has a tools branch, hashed at its tip by `hd.tools_run` (tools/track.sh only dispatches the verbs).
The build key is T's tree joined with `-<hash12>` of every file under `tools/build/` (the code a build runs: build.sh, the Dockerfile, central.init.gradle);
the gate key is the build key joined with `-<hash12>` of every file under `tools/gate/` (the gate and every verb a contract row runs) and each other tools file a row's command names, with the contract's script rows;
a row's key is the same hash over that row alone, given to the gate as `ROWKEYS`, and a gate keeps the result of a row recorded at its key (`state/<slug>/row-<kind>-<id>.json`, the results of its last four keys, so the live branch's own gate never drops a member's;
none for a held row) unrun, so a tools change to one row's file re-runs that row alone;
in a row's key each tools/gate/*.sh is only the part the row runs (`hd.gate_part`): the functions its `tools/track.sh <verb>` reaches (the verb's own, its dispatch arm's, every function they call) and the file's code outside every function, comments dropped;
a row running no verb of the file hashes none of it, a file without functions is whole;
so an edit of one verb moves that verb's rows alone and the fork CI row keeps its result, while the shared code (the dispatch, the sourced build.sh in the build key) moves every row;
a script gets the build key as `T` (the artefact it builds or uses) and the gate key as `G` (the gate's record);
a build fix re-builds and re-gates, a gate fix re-gates alone, a tools commit outside both (docs, tests, up's code) neither;
`hd tree` prints the build key, so a dev's build is the pass's;
T_int admits a change whose gate passed at its current key, the test `nxt` applies).
A server change with central dependencies carries `-c<central12>` in its T: the Central tree, Central's base and those changes' heads merged, which its build includes (`CENTRAL=<Central clone>:<commit>`;
`hd tree` prints it third);
T_int carries the one of its heads' central dependencies.
Builds are artefacts named by that key: a server image `or:<T>` (jar and game cache), a client APK `evidence/<slug>/<T>.apk` with its repack log, a harness test run (keyed by its batch tree without `harness/`, so a definition commit on the live branch re-builds, re-gates and blocks the ship of nothing;
ship fast-forwards to the current batch tree).
A server build holds its slug's `state/<slug>/build.lock` while it builds alone, never through the gate's rows (gate-ci's CI wait), so a rekeyed build or a dev's build waits on no gate;
under it the build removes a container of its name a killed build left running, and its own as it ends;
every build and check container runs with `--init`, so a stop's SIGTERM, which docker run proxies, ends it with its script.
The host bounds the builds and container steps alive at once, across every slug and track: the pass starts a build that takes room (`Ctx.room_of`) only while it fits beside its alive builds and every `state/room/` entry not of one of them (`Ctx.builds_fit`), so a tools ship moving every build key starts as many as the host holds and each further one on the observed end of one;
each container then waits in `hd room`, a gate's checks and a dev's build included;
build.lock stays one build per slug, never the bound.
The game cache is keyed by the hash of its inputs (OpenRS2 cache id, pack configs, gamevals) in a named docker volume, which the build makes its own uid's before it runs (docker creates a volume root-owned).
The game data of a revision (the download, keyed by game.example.yml's blob12, the gate's release asset key) is stored once in that volume: a build missing the cache restores it and repacks, never downloading openrs2 again for that revision;
a revision missing from the volume is restored from the gate's release asset when it is listed, so openrs2 serves only a revision no image holds yet.
Every build renders the copy's game.yml from T's game.example.yml (game.yml is ignored, so clean keeps an older tree's).
A hand-over's check rows get the build key as `T`, as the pass's build, so a dev's build is the pass's.
The build copy is `<repo>/.worktrees/<slug>-build`, the dev's clone `<repo>/.worktrees/<slug>`, worktrees of the product repo;
a track's `tools/` sit on its repo's `tools` branch (hd.yaml) in `<repo>/.worktrees/<the branch's last segment>`, made by the pass when missing.
A product track script run from that checkout (or any other) first copies its `tools/` to `state/tools/<content hash>/tools` and execs itself there, exporting `TOOLS_ROOT` (the copy's parent, where `hd rows` runs a gate's rows) and `TOOLS_SRC` (the checkout): a ship fast-forwards the checkout, never a running build, gate, deploy or up;
the pass removes a copy no process names in its command line or cwd and no container mounts from.
The harness gate runs its rows from the build copy at T (`TOOLS_ROOT`), so a change to a check is judged by that check;
check-dry-run compares against the live checkout's plan (`LIVE`), and fails when the candidate's pass exits non-zero or prints a traceback: a crash plans nothing, which is no pass.
A harness change carries a fix to a tools branch on branch `harness/<slug>` of that repo: the hand-over records each such head (refused unless it descends from the tools branch or its tests fail, as check-tools runs them;
once handed over, a head the branch moved past is rebased onto it by the pass in `<repo>/.worktrees/<slug>`, recorded in the hand-over and re-gated, a conflict being the dev's step), the head joins T's key (`<tree>+<head12>`), the gate runs the repo's `tools/**/test_*.py` at it in `<repo>/.worktrees/<slug>-build` with HOME and PATH alone (the gate's env is not theirs), ship fast-forwards the tools branch to it, and the change is live once the live branch and every such branch hold their heads.
A done or closed change leaves nothing behind: the pass ends its runs (a started one with its record and an `ended` event, freeing its slot), then removes, in each repo, its clone, its build copy and any worktree on its local branches (`harness/<slug>`, `client/<slug>`, `dev/<slug>`;
one whose status shows only untracked symlinks holds no edits and goes forced, one with edits stays), then those branches, the dev ref last;
a branch goes once the base, the repo's tools branch or the change's head holds its tip, or the change is closed;
`swept.json` keeps the head the dev ref held;
a superseded change's runs end the same way, its clone and branches kept until the user's `hd close`;
remote branches are public and stay;
a script that cannot start is an alert;
containers, volumes, mobiles and desktops carry the slug or the run name.

## The loop

```
next(change):
  closed by the user?
    yes → done
  deps live or closed?
    no → wait on them (a same-track upstream dependency: gated;
    the dependent with no pr or branch of its own joins its PR, a chain one PR)
    a dependency a late answer or joined filing reopened (its own step not done) → wait on it until its dev hands over
  question open (hd ask)?
    yes → wait for the answer: no run, gate, ship or upstream step
  contract.md?
    no → qa run (server, central) | derived from the definition and seed rows (client, harness, a PR round filed from a finding)
  handover at the dev ref's tip, no answer since (newer than it and the head's last verdict;
  a joined filing or finding counts at once on an upstream change, else once its head is done or no head of its own is in flight)?
    no → dev run, even on a done change (it reopens) (a hand-off file lists its successor;
    FAIL findings and gate details in the brief)
  carried tools head behind branch?
    rebase it in the pass (its tools worktree), record it in the hand-over;
    a rebase that stops → recorded, dev, its files named
  head's last verdict (its contract) FAIL?
    yes → dev, before the head is built, gated or judged again;
    the step counts and lists its fail rows, and names its not-judged rows apart
  T
    conflict → dev;
    an upstream head holding unmerged commits of another PR's change (stacked), or not holding the head of a same-PR dependency it joins → dev
  build(T)
    not built → tools/track.sh build;
    failed → dev
  gate(T)
    not run → tools/track.sh gate (script rows, fork CI on gate/<slug> at T, probe, tests);
    failed → dev
  verdict(head, contract)
    none → qa run;
    FAIL with a code row → dev;
    text-only rows: qa fixes the text, re-marks
  test server? (server, beside) live.json ⊇ head?
    no → deploy T_int (built once) in the same pass, holding neither card nor ship (a local change: its target, then done);
    a conflict → the later-merged change's dev (a pin's: the oldest one at this step): against a change, resolve in its own branch;
    against a permanent pin, the base or a union, push local/merge/<a>-<b>;
    every conflicting head is left out and the rest merged on (pins first, then heads by priority, then creation), so one dev step lists them all with the merge order;
    only a pin's conflict holds the deploy, the tree without a conflicting head deploys
  shipped (upstream)?
    the open upstream PR (found by its head branch, no owner prefix) is at head, or the change is a round with no commit of its own (reply-only): no build, no gate (only a commit is gated;
    a PR's live head is never re-gated because main moved);
    a same-PR dependent counts it gated
  public (upstream, release)
    one fact read per pass: the open PRs of the upstream (`gh pr list`), the review and conversation comments of a PR (REST, which marks bots)
    carried (its own ship.json, the PR open at it and ready, or a same-PR change's built on it; or the PR at head, ready, ours answering every finding)?
      yes → wait on the maintainers (a release: until its tag exists)
    a dependency upstream in another repo, not merged there?
      yes → wait on its upstream merge (it is in no PR of this repo);
      its card held by the user: one user's alert naming that hold (lift it, or hold this card too), gone once this card is held too, the test server deploy going on
    an open change of the PR it waits for (head not in this head, or built on it)?
      yes → wait: a card is a complete PR, shown once, at its tip (one card for same-head tips), its texts covering every change of it;
      a round with no dev ref has its tip's head
    pr-comment.md names the head (a new PR) or every commit since the live head (git rev-list live-head..head, the head fetched by pull/N/head when the clone lacks it)?
      no → dev (input comment, head, the commits it misses): no card, no generic text
    the one comment quotes every finding of the round no comment of ours answers?
      no → dev (input findings, head, the ones it misses): no card
    the draft PR at head has a failed CI check (read afresh; unread → unknown)?
      yes → dev (input ci, head): no card, and `hd handover` refuses that head: CI never runs again at a head, so a fix or a rebase onto main starts it
    approval.json at head, texts?
      no → card in the console: the acts in order (push when the PR is not at head, open the draft when no PR is open, else update PR N (the one the carry opened too, on a rerun) replacing a differing title or body, CI when it pushes or the PR is draft, the one comment (pr-comment.md when it pushes, then each reply, pr-reply-<finding>.md), ready), each exact text with the finding it quotes, the verdict, the evidence path, the yes (`hd approve`), no (`hd hold`) and close (`hd close`) commands;
      hold.json at its head or `held: all` in the definition hides it (held by the user, a wait) until a new head or the lift;
      it wakes the orchestrator once per head and texts
  carry (`hd ship`, approved)
    release: gh release with the APK, notices and log.
    Upstream: push head to the PR's branch (no force), open the draft when none (opened.json at once, so a rerun updates it), else edit the title and body that differ from the live ones (REST PATCH: `gh pr edit` reads the retired Projects (classic)), CI green at head when it pushed or the PR is draft, one PR comment naming the head (once per head and text: its marker), the push summary then each finding's reply (no review-thread reply);
    it quotes each finding and @ only their askers, each once (a later mention keeps the bare name), else the change's FAIL;
    an @ on a '>' quote line or in code is no mention;
    ready, and no review request: the account cannot ask reviewers upstream, so maintainers pick a ready PR up;
    each step a ship.log line as it starts and ends, the CI wait naming the checks it waits on and ending on their result or a failed read, a step observed done skipped.
    Success: ship.json, approval.json removed (the yes is spent).
    A failed check stops the carry as the change's FAIL: nothing re-runs CI at a head.
    Failure: ship.json ok false, the PR as it is;
    fault head (a failed CI check, a reply naming others): the change's `FAIL upstream` dev step, the yes kept for the same head;
    the dev handing the same head over after it (a text fixed, no commit) answers it, decided on the two records' heads and order alone; a failed CI check stays the dev's while GitHub lists it at the head, whatever the records say.
    fault carry (any other: a GitHub write refused): the yes spent, the card again naming what stopped it.
    A GitHub read that fails: no result (carry held), the pass reruns it, a second death on the same args an alert
  batch (`hd.batch`: harness, and client code; a release is gated alone)
    every change of the track at this step, in hand-over order, merged onto the live branch (no per-change build or gate):
    a conflict with the branch → dev;
    with an earlier member → wait for the next batch.
    Members' heads on one tools branch merge in the same order (the merged commit is the batch's head there, which ship fast-forwards the branch to);
    a member whose tools conflict with an earlier member's → wait for the next batch.
    Each prefix is a tree, its gate `state/ship-<track>/gate-<key>.json` (NAMES: its changes, each change's rows with its own env;
    a harness check of the tree alone runs once per gate);
    the longest passing prefix ships (one ship moves every member of it), unless a failed prefix lies beyond the one longer (a member joining after its gate started waits for the next batch);
    a gate running on a prefix still current with no result holds, the state naming its key;
    with no passing prefix gate the whole batch, after a failure the prefix halfway between the longest passing and the shortest failing one, down to the first member alone, then the live branch with that member's rows:
    passing, the member's failure is its dev's and it leaves the batch;
    failing, an alert and the batch waits, no member blamed.
    A ship runs under `state/ship.lock`, a T already on the live branch moves only the carried tools branches not yet holding (and pushed at) their heads;
    it clears the kept gates but the one of the tree it shipped (`gate-<G>`)
  wait
    upstream merged;
    each maintainer word on the pr (an inline comment, a review's body, a conversation comment;
    no bot: GitHub's user.type Bot or performed_via_github_app, or hd.yaml's `bots`) that no definition's `finding` carries and no reply or comment of ours answers (a reply after it in its thread, or any comment of ours quoting it;
    no date counts) joins the pr's one open round: its open change not yet carried (the tip, least slug), the id added to its `finding` and a judged answer row `finding <id> by <author>` to its contract, before the pass decides the changes' steps (a listed run takes it in a rewritten brief);
    with none open, a P1 change <track>-<pr>-c<id> on the pr with deps [the pr's tip changes] and the track's seed rows, derived.
    `hd new --pr <n>` on an upstream track joins that round the same way (an answer row `filed by`, its deps the round's)
  done
```
A head counts as live or done only as the change's own work: handed over, or off its base's first-parent line (merged in);
a fresh dev ref cut at a base commit is neither.
A fresh dev ref is no head in the dev step's reason: it names the answer or filing that reopened the change, never the base tip.
A contract's rule rows carry the upstream rule files' blob shas;
a verdict records each file's blob on upstream main ('' for a file absent there), and when one moves from the last verdict's, only those rows are re-judged.
A reviewer is listed only where the contract has `judge:` rows (client changes have none;
releases do).
A hand-over at the same head after a verdict re-marks only the failed rows.
A goal's `measure` is a step of the goal, held by its deps as a change is: unmet when its target's tree (client: master and the live T_int;
plus the digest of the passing units) is not the tree of `measure.json`.
A passing unit is one a change of the goal names in `units` while it is live at a head whose last verdict passes every row;
the script gets them as PASSES.
Below target, the planner files changes.

**The pass** (`hd tick`, a systemd user timer and after every run end): fetch each remote once;
for every change, in order (harness changes;
then changes on a PR, off the upstream tracks or blocking another;
then new content: an upstream change without a PR;
each at the best priority of the open changes it blocks, by a dep or by the conflict a change's last state names as holding its test server deploy), compute `next`;
list no run for a change whose priority is below `hold` or below the best priority of a change whose `next` is a dev or qa run it would list and none is listed or alive for it, dropping a listed, unspawned run only below `hold`;
start the script step of each change whose process is not alive (pid with start time), one ship at a time;
a process alive under a key no longer its step's is stopped with its systemd scope (`Facts.stop`) and the current one started;
a build or gate alive on a head its verdict failed is stopped (`Ctx.halt`), its record dropped, since that head is its dev's;
a gate alive under another key that runs a row whose key still holds is not stopped: it finishes and the next gate runs only the rows it left;
starting a keyed process also stops the slug's other process alive under a key of another tree (a gate on the old build key when the new build starts);
a deploy's key is its tree and the hash of the tools it runs (tools/track.sh, tools/build/, tools/server/), so a fix of them restarts its count;
a deploy alive is never stopped, a newer tree or tools ship included: the pass deploys the newest tree after its end (openrs2 serves no ranges, so a stopped download restarts from 0);
write an event only when `next` differs from the last event;
end the runs whose console is gone and remove what they own;
stop the processes of every ended run (its hand-back, `hd stop`, the pass's end) whose slice is still active or whose Windows processes or temp root are still recorded, and every `hd-*.slice` no live run holds once its owner is gone: a test's `hd-t<pid>.slice` once `<pid>` is dead, any other once empty;
remove every temp root a suite or test runner made outside a run (`hd-<kind>-<pid>-*` in the temp dir, named by its process) once `<pid>` is dead, whatever ended it;
a temp root is removed whole, each dir in it made writable first, so a read-only dir a test left in it never keeps it;
drop a listed, unspawned run once its change's `next` is no longer that run's step;
end a started run once its change's `next` is the other role's run (dev or qa) or a wait, but for a wait only on deps created before it started (met at its start, a re-gate) or limits it filed (`hd new --limit-of`): its agent's next calls are denied but reads, writes to evidence/<slug>/ and its hand-back;
a run the pass ended neither settles its step nor counts toward the one retry (`unlistable`): only its own hand-back, the head's stop or its console's death does;
a listed, unspawned run whose change's `next` is a step of its role on a moved input (a joined row, a definition commit) takes that input, step and a rewritten brief under its name, so its spawn binds and no run is listed again;
repair what is observed broken, once (a missing tools worktree, a repo without the noreply git identity);
remove a tools copy nothing uses.

**The orchestrator** (`.claude/agents/orchestrator.md`) is a top-level session the user starts once with `~/osrs-harness/tools/orchestrator.sh` (it runs `claude --agent orchestrator "drive"` in the user's terminal), so it and every agent it spawns show in the user's console with their transcripts (an agent a run spawns, its `reader`, shows under it;
a headless session's agents are not shown).
A watch on `state/wake.orchestrator` wakes it, rewritten by the pass only when a spawn, question or alert line appears or a card (a change at a head and texts) not shown before;
it runs `hd`, spawns each listed run by path, TaskStops each at its hand-back, files a harness change for a fault a hand-back reports, commits definitions, keeps one read-only monitor sweep running (a general-purpose agent that edits nothing and validates that the harness changes shipped since the last sweep landed and finds harness bugs;
started on session start;
its report kept as `evidence/monitor/sweep-<n>.md` with the v8 head it swept, its findings filed by root cause, the next sweep's brief naming that report, the changes shipped since and its open findings), re-arms the watch (an expiry is a wake too).
Its runs bind to its process as their console.
It loads its definition only at start, so a shipped one reaches it by being read: `swap` compares the orchestrator.md blob each `claude --agent orchestrator` process holds (the one in its `state/orchestrator-read/<pid>-<start>`, else the one it started on: the live checkout's HEAD at its start time, by the HEAD reflog) with HEAD's, and alerts a session on another blob;
its own `hd` (`reread`) prints it the live file in full after its sections and records that blob held, so it acts on it from then on while its runs and spawns go on: no session ends for a definition;
a compaction keeps only the start-time definition, so the SessionStart hook (compact) gives the session the live file again when the two differ;
MCP servers load only at a session's start (.claude/settings.json hooks reload live), so `swap` also compares each session's start-time `LOADED` blob (.mcp.json) with HEAD's and raises one `user:` alert per session naming it and `tools/orchestrator.sh` for its restart;
an mcp/ file needs none, serve.py carries it;
a gone session's read record is dropped by the pass.
`hd` alerts `user: no orchestrator session` while no `claude --agent orchestrator` process exists, naming `tools/orchestrator.sh`.
It is also the user's chat: it shows each card in full and shows questions and alerts as text in its reply (it has no AskUserQuestion tool: a wait would stop every spawn), records answers (`hd answer`) when the user's words come, and acts on the user's other words at once;
the user's yes is their own `! python3 ~/osrs-harness/hd.py approve <slug> <head>` and their close is their own `! ... close <slug> <text>`, neither firing a hook.

**The planner** is a run listed on significant facts only (an alert, among them a mechanism with two open harness changes no dependency orders (one waits on the other, transitively) or a harness change naming none, which it merges with `--supersedes`;
a gate failure, a goal below target with nothing open;
never time or an event count;
a trigger is its subject (the `state/<slug>/<name>.log` an alert names, else a gate failure's change and T, else the run `<change>-<n>` it names, else its text), left out while an open change's body names it or once a planner run handed back on it after its process's `since` (when start() last started its count over, named in the alert);
a gate failure is its dev's until a dev run handed back on that T with no run of the change alive;
an alert for the user lists none), outside the agent count (one at most);
a planning request from the user with a measurable target reaches it as a goal, any other as a change.
It files the changes that close a goal's gap with dependencies across tracks, and turns an issue it observes in operation (a run ended without its record twice, a harness-made gate failure, a needless question) into a harness change on that issue's mechanism that a harness dev run remediates, and on every run merges the open and today's merged harness changes that patch one mechanism into one root-cause change (`--supersedes`).
Its hand-back is its record, filed or not.
It writes no product code.

**Runs**: the brief is a run's one read of its change: the definition, the contract with the user's answers, the last verdict, the build and gate lines (each its verdict and key, the log in the `state/<slug>/<name>.log` it names) and the hand-off, each once;
`hd show` is not read again.
The role file holds the nevers;
the track file holds the rules.
A dev run commits in its clone, builds with `tools/track.sh build <slug>` (the working copy snapshotted to an anonymous commit, T computed, the build copy checked out at T, built incrementally), brings the result up with `up <slug> [N]` (server from `or:<T>` on the change's ports, accounts seeded, N desktops started, each given `OPENRUNE_ENDPOINT=http://127.0.0.1:<port>` (the launcher takes jav_config from it alone, and jav_config names every other endpoint), loading the devtools jar of the client track's build of slug `live` (the client's main), and logged in by widget actions, blocks until every devtools endpoint answers, a key or typing call the starting client never received resent once a state read answers again;
a desktop whose launch fails fails up naming its error, never waits: the launcher exits (its exception), or its devtools plugin logs that it could not bind its port;
any up that fails or is stopped names the step it ended at before it takes down what it started;
a launch the WSL interop ended before Windows ran it (its log holds that error alone) is launched again once the interop answers, any JVM it left stopped first;
a server change's quest requirements in the mode its front matter `quest-mode` names, `respect-progress` unless `assume-completed`;
`restart <slug>` keeps that mode and the database;
a server up's game.yml has idle logout off (live keeps the image's), so a run's desktops stay logged in while its agent reads;
each desktop of an up is kept logged in until `down`: a logout observed is logged in again, a failed login retried once the server is ready after it, never while the same server refuses it;
a failed login that left the desktop logged in (no inventory) is logged out and tried again at once, a second such failure waiting like any other;
a desktop's endpoint runs its up's tool calls one at a time in arrival order (the plugin interrupts the active call on each new one, and a run and its keeper both call), a cancel notification passing at once;
the endpoint answers every tool call within 20 s past its own timeoutMs, its wait for the call ahead included, an error (code -32002, which a keeper takes as a cancel and logs in again) when the plugin has not answered (a hung plugin, a stream that never ends), so a call is bounded whatever bridge sent it;
a cancelled keeper call starts its login again, never read as the endpoint gone;
a keeper call once sent waits for its answer however long it queues (only its connect is bounded), so no step it gave up on runs later;
`restart` logs the desktops out before the server restarts, and a failed step of `up` takes down what it started;
a desktop login ends on a page Enter does not submit: Escape, Enter again, else the refusal named;
a server up's database is fresh, or with `RESUME=1` the accounts as the change's last `down` saved them, down waiting until the server has saved every character;
its realm live's, `dev_mode` off and xp at 1x, each account a member at rank 0, or with `STAFF=<N>` the Nth desktop's an administrator, the rights read back after the logins;
a login that made an account but its own, a lost key, logged out and in again;
a login whose inventory widget does not show container 93 fails up, as does one whose widget has no slots 10 game ticks after the first event after LOGGED_IN), runs a server change's tests with `test <slug> [module...]` (each touched module's tests and spotlessCheck on the build copy, the log in its evidence dir), and hands over.
A harness dev runs the unit tests in its worktree;
the harness track's `build` refuses without the loop's T and TCOMMIT.
The hook tells a run past the context limit (set below the bound with room for a clean hand-off, measured under 11000 tokens) to start no new work, then in order: commit its work in progress on the dev ref (pushed off the harness track), record what it judged (a judge: `hd verdict` when a row failed, else the judged rows in `handoff.md`), collect its subagents and stop its processes, write `handoff.md` (what is proven, what is left, the exact next step, whether a server or desktop is up) and hand back;
the successor, the same role on the same change, is listed in the same pass past the tier hold and the agent count, its brief naming that commit and the file to resume from.
Three runs of a change past the limit since its last handover are an alert (the change too large for one run, or its brief spending context on reading).

**Authority**: everything runs with the one shared GitHub token.
The public act is the carry, `hd ship <slug> <head>`, started by the pass only while approval.json holds that head and the digest of the card's current texts, and re-checking both before it acts.
The one hook rule: `hd approve` and `hd close` (the user's word, typed by the user as a `!` command, which fires no hook) are denied inside a subagent or the orchestrator session (a hook input with an agent id or type) when a command runs them (at a command's start);
a command that only quotes them (grep, echo, a heredoc body) runs.
A bare `hd` or `hd tick` without `--dry-run` (the acting pass) is denied in a subagent: a run views with `hd show` or `hd tick --dry-run`.
A bare `hd` is one with no argument at all, as main() runs the pass (`hd --help` prints usage).
A run's `kill` is denied unless every target is a pid in its own slice or the shell's job (%n), and its pkill and killall are denied.
A `while`/`until` loop's `pgrep -f <pattern>` (in its condition or body, outside a heredoc body or a quoted argument) is denied when the pattern matches the command's own text, since it then matches its own `bash -c` shell and the wait never ends;
a one-shot `pgrep` listing ends, so it runs;
the denial names `hd ps`, which lists the run's own processes for its `kill`.
A subagent's `timeout` command (outside a heredoc body or a quoted argument) is denied: a step ends on its observed outcome, the Bash call's own limit re-issued when it ends first.
A subagent's sleeping loop that counts (a `for` loop, or a `while`/`until` loop with a counter) is denied as the same bound by another name;
a loop that sleeps until its condition, the fact, holds is the wait.
A sleep counts against the innermost loop that holds it, so a `for` loop wrapping an `until <fact>` wait is that wait.
A run's desktop devtools call names a port of its change's up.json desktops: one naming none is given the run's one desktop, any other is denied, its reason naming the run's ports.
A desktop's devtools endpoint answers only a request carrying the token in its instance's guard file, read on each request (its up's up.json `token`, sent as `Authorization: Bearer`), any other 401: every JVM of the instance loads the server tools' DevtoolsOwner, the JDK's HttpServer provider filtering the devtools port, and the bridge and desktop_login.py send the token of the up whose instance owns the port.
The guard file is empty, any caller answered, while a session's desktop bridge runs without mcp/serve.py (it predates serve.py, never reloads and sends no token, read from the processes): desktop_login.py writes it at the desktop's start and its keeper again on each change of that fact, so the guard turns on once none lives.
A run's own agent stops (`continue: false`) at its next tool call, its hand-back let through, once the pass, the head or `hd stop` ended its run.

**Base, head**
- Client: `origin/main`, `origin/client/<slug>`
- Server: upstream `main`, fork `dev/<slug>`
- Central: upstream `main` of OpenRune-Central-Server, its fork's `dev/<slug>`
- Harness: the live checkout's branch (`HEAD`), `harness/<slug>` (and `harness/<slug>` of each product repo whose tools it changes)

**build(T)**
- Client: host build, ninja, repack with `OPENRUNE=1 LOCAL_AUTH=1`, the jav_config and world-list URLs patched to `OPENRUNE_ENDPOINT` (default `http://10.0.2.2:8080`, a Jagex, RuneScape or Google host refused);
  APK and log
- Server: Gradle in container `build-<slug>`, cache by inputs;
  image `or:<T>`;
  a tree whose settings name `.m2-rsprot` (the pin local/android's locally published rsprot) gets the fork clone's `.m2-rsprot`, and without it the build fails saying so;
  with a Central dependency `CENTRAL` names the Central tree, built in by the init script `central.init.gradle`, which substitutes every Central module (`openrune-central` by `:central-app`)
- Central: Gradle `assemble` in container `build-<slug>`
- Harness: the test suite at T

**gate(T)**
- Client: repack log lines (checked again at install), probe report at T, network QA when `network`;
  `log` reads logcat by pattern since a marker
- Server: script rows (gameval ids unique across T_int, a dupe test (src/test or src/integration) per item-moving module, evidence files, commit subjects and trailers after an existing PR's live head), fork CI on `gate/<slug>` at a child of T whose workflows first move the runner's ephemeral ports above the game port 43594 (with `CENTRAL`, also holding the Central tree and a workflow step that builds it in by `central.init.gradle`;
  the change's head unchanged), its status one read of the sha's runs, conditional on the last ETag (a 304 costs no GitHub quota), a quota refusal holding the row until GitHub's reset;
  its CI restores the game data from the fork release asset `game-data-<game.example.yml blob12>` (seeded by the gate from `or:<T>` when absent, the first upload standing) on an actions/cache miss, never downloading openrs2's cache (no asset fails that step, the runner's, re-run once the asset is listed);
  a head that changes the revision (game.example.yml) restores neither, so its CI runs `:or-cache:freshCache`, the step the classifier calls the head's;
  a head that changes another cache input (or-cache/, /pack/, gamevals, raw-cache) packs on the restored revision, that step the head's, so openrs2 is never its step;
  each step carries the job's timeout-minutes, so a timeout names the step that ran out;
  a run failed, cancelled or timed out at a step the head does not touch (the runner's setup, openrs2's download unless the head changes the revision, the packing when the head changes no cache input) is re-run once its source answers (openrs2: its newest cache of the revision yields bytes), held after its third attempt
- Central: `gradle test`, evidence files, commit subjects
- Harness: tests;
  `hd tick --dry-run` plans no upstream action the live checkout's pass does not;
  each carried tools head's tests

**judge**
- Client: release only
- Server: every contract row
- Central: every contract row, from `up`: the server's base built with this Central (the server track's build and up), `down` stops it
- Harness: none

**ship**
- Client: push the batch tree to `main`;
  release after the yes
- Server: test server: deploy `or:<T_int>` with the issuer's secret in its game.yml, its sidecars serving `tools/server/jav_config.ws.template` (the APK's with params 11, 20, 22 and 28 naming `issuer.py`, its sign-in and tokens;
  `javcheck.py` after `up` and `ship`: local hosts only);
  upstream after the yes
- Central: live at its gate (dependent server builds include it);
  upstream to Central after the yes
- Harness: under `state/ship.lock` (a T already on the live branch: only the carried tools branches not yet at their heads), fast-forward each carried tools branch and push it to the remote of its repo's `name` (never upstream), then the live branch to the batch tree under the state lock (never under an acting pass), push;
  any of them moved past its gated base: nothing moves, the next pass merges the batch again

```mermaid
sequenceDiagram
  participant O as Orchestrator
  participant D as dev
  participant S as tools/track.sh
  participant P as Pass
  participant Q as qa
  participant U as User
  P->>P: contract exists, no hand-over: brief written, event
  O->>D: Agent(dev, "Read and follow state/briefs/<run>.md")
  D->>S: build <slug>: T, image or:<T>
  D->>S: up <slug> 2: server, two logged-in desktops
  D->>P: hd handover <slug> (script rows pass, {head, T})
  P->>S: gate <slug> <T>: rows, fork CI
  P->>S: ship test server: or:<T_int>
  O->>Q: Agent(qa, brief)
  Q->>P: hd verdict: every row
  P->>U: card in the console (acts, exact texts, verdict, evidence)
  U->>P: ! hd approve <slug> <head>
  P->>P: hd ship carries: push, draft, CI, comment, replies, ready; ship.json
```

## Run and test

```
~/.config/systemd/user/hd-tick.service   [Service] Type=oneshot  ExecStart=/usr/bin/python3 %h/osrs-harness/hd.py tick
~/.config/systemd/user/hd-tick.timer     [Timer] OnBootSec=1min  OnUnitActiveSec=1min   [Install] WantedBy=timers.target
loginctl enable-linger alex && systemctl --user enable --now hd-tick.timer
python3 hd.py                            # a pass, then the view
python3 hd.py tick --dry-run             # the view, nothing started or recorded
python3 -m unittest discover -s tests    # one class per requirement over fakes; Tools runs the harness track script for real
the suite sets HD_SUITE=1 for every process it starts and refuses to load under it: a test's gate never runs the suite (a test's deliberate inner suite runs under HD_SUITE=nested, where EndToEnd skips)
a gate's test row records unittest's runner alone (its own fd), never what the tests print: its detail names the failed tests, each with its traceback's last lines (the assertion)
every run of the harness suite through the track script (the gate's test row, a dev's `tools/track.sh test <slug>`) keeps the runner's whole report in state/<slug>/tests.txt, which its record names last beside every failed test
a gate's test row keeps it under the gate's own slug (state/ship-harness/tests.txt for the harness batch), never a member's, whose dev's test overwrites it
a gate's test runner (the harness suite's and each carried tools head's) puts every temp dir of its tests under one root it removes at its end and at its stop (SIGTERM)
fork .worktrees/harness: python3 -m unittest tools/server/test_tools.py   client .worktrees/harness-v8: python3 -m unittest tools/test_track.py
each tools branch ignores __pycache__/; no compiled cache is committed
```

- R1 Goals: the goal's `measure` step keyed by the target's tree;
  the live tree unblocks client deps;
  the planner plans

- R2 Flow: `nxt`, the pass, the briefs, the hook's bind and end, `wake` and the wake file, the orchestrator session

- R3 Contract: contract.md, `hd handover` and `hd verdict` refusals, `hd new`'s one change per mechanism (a dependency orders the rest), records bound to T or head and contract, rule-row shas

- R4 Authority: the console card (acts, exact texts), approval.json bound to head and texts as the yes, `hd ship`'s carry re-checking both, the one hook rule

- R5 Recovery: the timer, rerunnable steps, pids with start times, repairs on observed effect, one ask per change

- R6 Economy: artefacts keyed by T, verdicts keyed by head and contract, the agent count, events on edges, the hook's context limit, the track scripts

- R7 Visibility: `hd` prints facts;
  `hd show`

- R8 Trees: merge-tree, the docs' one fact per line, `local/merge/*` refs, the build copy, cache by input hash, names by slug or run
