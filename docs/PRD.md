# Requirements

The constraints every solution to docs/PROBLEM.md must satisfy, each derived from its principles.
Code and tests cite the ids. docs/ARCHITECTURE.md is the mechanism that meets each;
docs/ACCEPTANCE.json is the checklist below as data, where only `passes` may change.

The workflow they constrain: agents build a complete PR → the user reviews it as text in the console and says yes → it is carried upstream → maintainer feedback becomes changes on that PR.

### R1 Goals (from P1 P10)
Each goal is measured by its command whenever its target moves, shown with the tree it was measured on, and work is chosen to close the gap to its target.
A server change unblocks the client once live on the test server.

### R2 Flow (from P3 P10)
A defined change reaches its live target with no person involved once the changes it depends on are live (in the fork's integration tree: gated, merged and tested there;
of the same PR: gated);
a dependency upstream in another repo holds only its dependent's card until merged there, never its dev work;
upstream contributions that belong together are bundled into one card by the user's word, and dev work goes on past the contribution queue;
a change the user closes takes no further step and leaves the integration tree;
a done or closed change leaves no worktree or local branch.
A shipped mcp/ change is live in each running session's MCP servers from its next request, with no session restarted.
The orchestrator, a top-level session visible in the user's console, spawns and stops every run and is the user's chat: it shows each card in full and shows questions and alerts and acts on the user's other words, never waiting on the user (a question is text in its reply and the loop goes on);
the user's yes (`hd approve`) and close are the user's own;
with no orchestrator session the user is told to start one;
a session acting on another orchestrator definition than the live one is given the live one to read and acts on it from then on, with no user step, no session ended, no spawn held and no run stopped;
its watch wakes it only when a line it acts on appears (spawn, card, question, alert);
planning across tracks belongs to a planner run listed by facts, and the orchestrator keeps one read-only monitor sweep running that validates shipped harness changes landed and finds harness bugs, each session restarting it from the last sweep's report;
nothing depends on any session staying alive.

### R3 Contract (from P1 P2 P7 P11)
What ships is exactly what was checked and approved, against a contract written before the code: the track's seed rows (one added later joins it at its next head not carried upstream, one about the upstream PR only a change that opens one), the accuracy spec, the live upstream rules with their blob shas, the user's answers (one recorded after the brief of the run that handed over and the head's last verdict is the dev's before the head moves on, a done change reopened by it;
a filing joined to the change is its scope, not the user's word: a head handed over before it is still gated and shipped, and the change reopens on top of it once done;
a closed change takes none) and prior findings;
a row is proved through the change's own tree, never through a change that depends on it.
The hand-over passes every script row and the carried tools heads' tests;
the gate runs the local script rows first and fork CI only once they pass;
a step failing outside the head (a source down, a quota refusal) records no result and is re-run once its source answers, never the head's failure;
the reviewer judges every row once, pass or fail, a row it did not check is not judged and never passes, and verdicts append;
a text-only failure is fixed in place.
A gate is bound to the tree it ran on, a verdict and an approval to the head and contract they cover, each void when its input moves.
A verdict covers the judged rows: a script row added or changed leaves it standing.
A claim with no record counts for nothing;
an unknown fact stops a step.
A limit in the mechanism a change touches is fixed in that change: a hand-over states its limits, each a filed change, and one naming an in-scope limit, or stating one otherwise, is refused;
every open harness change names its mechanism, and the planner merges the open changes sharing one that no dependency orders;
changes on one mechanism a dependency orders stay apart, so a fix the user wants first is never held behind its follow-up;
a limit in another mechanism, and any filing on a mechanism with an open change it neither waits on nor blocks, joins that change (one per mechanism), and a change cannot file a limit on a mechanism of the changes it was filed from, so filing converges.

### R4 Authority (from P4 P5)
Only a write to OpenRune and a client release need the user.
Each is shown, once complete, as one card in the orchestrator's console: every act the carry will do, in order (the upstream PR, new or the open one found by its head branch, the head and its base), each exact text it posts (title, body, the one comment with each finding it answers, the reviewers it asks), the verdict and the evidence path.
The user's yes is their own `hd approve <slug> <head>`, recorded locally, bound to the head and the digest of the card's texts and withdrawn when either moves;
their no or their word to wait is `hd hold` (recorded by the orchestrator): the card is hidden at that head, or at every head with `--all`, until a new head or the lift, and their close is `hd close`;
a card wakes the orchestrator once per head and texts.
The carry does the act exactly as shown, rerunnable, and records its result.
The comment is the dev's push summary (pr-comment.md): a new PR's names its head, an update's every commit since the PR's live head (fetched from the PR when the clone lacks it);
until it does the change goes back to its dev with the commits it misses, and no card shows.
A PR already at the head, ready, with nothing left to post gets no card;
only a commit waits on CI.
A maintainer's finding answered with no code is one run: its contract, reply and verdict, with no gate.

### R5 Recovery (from P3 P5)
Any failure is repaired in one pass with no user action;
a repair is recorded only when its effect is observed, and one that recurs is raised once.
Only what the user alone can decide or fix is raised, once per change.
Nothing is decided from elapsed time.

### R6 Economy (from P5 P8 P9)
A script runs before an agent, an agent before the user;
nothing is checked twice for the same input;
agents but the planner are bounded by one count;
harness changes are dispatched first, then a change on a PR before new content, each change at the best priority of the changes it blocks;
priorities are the user's five tiers (P0 a harness fix: it blocks work;
P1 a harness improvement: work goes ahead without it, but it significantly cuts the time to reach P2 work, such as the login flow;
P2 our upstream changes;
P3 features;
P4 new quests), a harness change never below P1;
no run is listed for a change below the best tier of a change with a run due and not yet listed, a change whose run is listed or alive or only waiting (on a dependency, a gate, the user) holding nothing, nor one whose due run the pass cannot list (an alert names why), nor below the band the user holds until the user lifts it, that band alone dropping a listed run not yet started;
a change's runs are one dev and one qa run per head move and one qa run per finding answered with no code, a listed run not yet started taking its step's moved input under its name, and any other run names its cause in its step;
the pass acts and logs only when a change's state changes;
a run hands off to a fresh run at the context limit, listed at once whatever the tier or the count;
a run keeps a desktop up only while it plays in it;
bring-up, scenarios and lookups are scripts.

### R7 Visibility (from P10)
`hd` prints what to spawn, the cards and questions waiting, what runs, each goal's number with its tree, and the facts of every open change, derived;
nothing else.
Every run is an agent of a visible session.

### R8 Trees (from P6 P9)
A change's tree T is its base, its dependencies and its head merged;
an upstream PR is self-contained: its head holds no unmerged commit of another PR's change, so its T is its head on upstream main (with its same-PR dependencies), and its card and carry follow its own gate there (a head the upstream PR is already at is never rebuilt or re-gated because main moved), the test server deploy running beside them and holding neither;
a carried tools head rebased onto its moved branch by the pass, a dev step only where the rebase stops;
a conflict is the dev's step, and a resolution against a permanent pin is a merge ref of both heads, used by the integration tree only and kept while the base moves past it or the head moves on from it and it still merges.
Two changes conflict only where they change the same fact: the source docs (PROBLEM.md, PRD.md, ARCHITECTURE.md) hold one fact per line, each requirement and paragraph a block of its own, and the gate's docs row fails a doc out of that format.
Two changes to different fact lines of a source doc merge, neighbouring lines included, with no dev run.
The harness changes, and the client code changes, ready to ship merge onto their live branch as one batch per track, gated and shipped once, one ship or definition commit at a time on the live checkout;
a failure drops only the change that causes it, and one the live branch fails alone blames none.
The integration tree merges the pins, then the gated heads by priority and creation;
a head's conflict is its own dev step and leaves it out while the rest deploy;
a pin's conflict, with the base or another head, holds the deploy and is the dev step of the oldest gated change at it;
one pass names every conflict.
A server change's T includes the Central tree of its central dependencies, a central change being live once gated.
T is built at most once, in a copy no agent commits from;
a build or gate is keyed only by what it runs, a gate's code never rekeying a build, and one whose key is no longer current is stopped;
its artefact serves the dev's check, the gate, the review and the deployment.
The game cache is rebuilt only when its inputs change.
Every artefact and process is named after its change or run;
a game client is a mobile (the official Android app on an emulator) or a desktop (RuneLite on Windows), by that word alone.

Nothing contacts Jagex: every mobile the client track boots resolves no hostname, checked by its `up`.
Constraints that need no mechanism: the user's own RuneLite and the tester account are never touched (A10).
Each track's seed rows and the dev's and reviewer's rules live in each repo's `tools/track.md` and `.claude/skills/`.

## Acceptance

Each check is a command.
`python3 -m unittest tests.test_hd.<R>` runs the requirement's class against fakes of git, gh, docker and the process table;
a live check reads the real state.

1. **R1** `tests.test_hd.R1`: a target move lists the measure step once;
   the measurement is bound to the target's tree;
   a goal dependency neither live nor closed holds its measure;
   a server head live on the test server unblocks the client changes depending on it;
   a passing verdict on a live change marks the units it names, and only then;
   below target with nothing open a planner run is listed.
   Live: `hd` shows each goal's number with a tree equal to its target's current tree.

2. **R2** `tests.test_hd.R2`: a hook during a pass completes in under 1 s, runs its deny rules and its fact is folded in (a bound run is never dropped as no longer due) and deleted once folded;
   a pass reads the world outside the state lock, takes the result of a fetch another pass has in flight instead of fetching again, and streams the events file;
   a change with a live dependency goes from defined to live with no `approve`, `answer` or console call;
   a closed change lists no run and leaves T_int;
   a dependency in another repo's upstream PR holds its dependent until live, its card until merged upstream, and one of the same PR until gated;
   a done or closed change ends its runs, a started one with its record and an ended event, and a closed dependency holds nothing;
   a dependency a late answer or joined filing reopens holds its dependents until its dev acts on it, on every track and in the same upstream PR alike;
   a fresh dev ref the base contains is neither live nor done until handed over;
   a head whose last verdict fails is the dev's step before it is built, gated or judged again;
   an MCP server whose mcp/ files change restarts at the session's next request once its requests in flight are answered, the session's initialize given to the new server and its tools list told changed;
   a done change's worktrees and local branches go in each repo, the dev ref last and still done, a branch no live branch holds stays unless the change is closed, remote refs are never touched, a failed removal is raised once;
   `hd` lists a spawn exactly while an agent step is unmet and no run is alive for its input, a step's input being what its run is given (a dev run due: the handed-over head, the contract, the hand-off), never a ref its own agent writes, so a change has at most one live run;
   a run being alive through its idle stops until the stop after its hand-back, an idle stop refused while a background command or monitor it started has not reported its end, and its record newer than its change's last answer;
   a trigger is the subject it names (the process log an alert names, a gate failure's change and T): one an open change's body names, or a planner handed back on since its process's count last started over, lists no planner however reworded or recounted, and a gate failure lists none while it is its dev's (no dev run handed back on that T, or a run of the change alive);
   `hd` lists no relayed message and `hd tell` is no command, the orchestrator's brief carries the card, question and alert steps, its frontmatter only its name and description, and the hook denies its session the AskUserQuestion tool;
   with no `claude --agent orchestrator` process the user is told to start it with `tools/orchestrator.sh`, and no planner is listed for it;
   an orchestrator process whose held orchestrator.md blob (the one its `hd` last printed it, else its start-time one: the live checkout's HEAD then, by its reflog) differs from HEAD's is alerted, its own `hd` prints the live file in full and records it held, and every other section (its spawns) prints as before;
   after a compaction the hook gives a session the live file again when it differs from its start-time one;
   a pass rewrites `state/wake.orchestrator` only when a spawn, card, question or alert line appears, a repeated line not waking it.

3. **R3** `tests.test_hd.R3`: a change without a contract lists the contract step and no dev;
   a hand-over with a failing script row, or whose pushed ref is not the head it names, is refused;
   a gate whose only failing rows are held (exit 75) exits 75, recording no result;
   a harness hand-over reads its local dev ref, never a pushed one;
   a script row the user's answer waives is not run;
   an answer recorded after a hand-over and the head's last verdict, on any track and on a done change, makes the next step a dev run whose brief carries it, the head not built, gated or shipped until a new hand-over, and one a verdict on the head already judged does not;
   an answer row written before a SendMessage to the running dev's agent is that run's, not late for its hand-over;
   an answer on a closed change is refused;
   a verdict missing a row, or with a row not judged and none failing, is refused, and the next brief lists the open rows;
   a contract row needs no change depending on its own;
   verdicts append;
   a text-only fix leaves the verdict at the same head valid;
   a gate at T does not hold at T';
   a verdict at H does not hold at H';
   a harness change's tools commits are handed over, gated and landed with it;
   a moved upstream rule file voids only the rule rows;
   a rule file absent upstream at the last verdict and still absent moves nothing;
   a seed check row added to a contract keeps its verdict;
   a hand-over without a `Limits:` section, or with an entry in it not `limit:<slug>` or naming a limit in its own scope, is refused, a mechanism with two open harness changes no dependency orders or a harness change naming none is an alert that lists the planner, an out-of-scope limit or a filing on a mechanism with an open change joins that change unless it waits on or blocks it, a limit back on a finder's mechanism is refused, and `--supersedes` holds the merged changes for the user's close;
   a seed row added later joins a contract at a head not carried upstream;
   a seed row tagged `upstream` joins no local change's contract;
   a contract's check rows run before its gate rows, which run only when every check passed;
   a failed fetch leaves every change where it was.
   Live: every `evidence/<slug>/contract.md` row has an id and a result.

4. **R4** `tests.test_hd.R4`: a gated, judged, complete PR (every open change of it in its tip's head) is one card in the view, at that head: its acts in order (push, open the draft or update the open PR found by its head branch without the owner prefix, replacing its title and body where they differ from the live ones, CI, the one comment, ready, the review request), each exact text, each finding the comment answers, the verdict and evidence, and the yes, no and close commands;
   `hd hold` hides the card at its head (held by the user, a wait), a new head shows it again, `--all` holds every head until `--lift`;
   a lift with the user's words keeps them in its event, writes no answer row and lists no dev run;
   a card waiting on a dependency's upstream merge whose card the user holds is one alert naming that hold, and the dependent's dependents go on;
   the same-head tips of one PR show one card;
   `hd approve` records the yes locally only at the user step, bound to the head and the texts' digest, and new texts or a new head withdraw it;
   the carry runs only while the yes holds;
   a release card is published after the yes;
   the carry pushes (no force), opens the draft or edits the open PR's differing title and body, waits for green CI only when it pushes, posts one PR comment per head and text: the push summary naming every pushed commit, then each finding's reply, quoting it and @ each asker once (a review-thread finding too: no thread reply);
   it readies the PR, asks review of the maintainers who reviewed it (none: GitHub asks CODEOWNERS on ready) and records its result, spending the yes (a record GitHub contradicts, the PR moved or back to draft, is not trusted: a new card);
   a CI check failed in a step the head does not read (the gate's own classifier) is re-run once its source answers, never the head's;
   every other stop records its result, the PR as it is: a failure the head causes (a CI step it reads) is the change's FAIL and its dev step, any other fault spends the yes and shows the card again with it;
   only a read GitHub does not answer leaves no result: the pass reruns it;
   a PR the carry opened keeps the yes on a rerun;
   a PR already at the head, ready, with every reply posted, gets no card;
   a finding with no dev ref has its PR tip's head and no gate;
   a central change is carried to Central's upstream;
   the dry-run check fails a candidate only on a public act main plans neither before nor after it.
   Live: `hd approve` or `hd close` from a subagent or the orchestrator session is denied, while the user's own `!` command fires no hook.

5. **R5** `tests.test_hd.R5`: a state record read while hd or a track script writes it is whole;
   two passes and a gate over the same state read each GitHub resource once, then only revalidate (304s), a dry-run (the gate's included) from the cache and the local refs alone, never the network, the carry's CI wait through the same cache (no GitHub read bypasses it), and an exhausted quota is an alert that holds every GitHub read;
   a pass on the live state peaks under 200 MB;
   console gone → its runs end and their artefacts are removed in one pass;
   a tools ship never changes the tools a running track script reads (each runs from its copy, removed once nothing uses it);
   a run the orchestrator stops (TaskStop of its agent, one resumed after its hand-back too, or `hd stop`) ends and frees its slot, and a process the run started, reparented or not, is gone;
   a run's Bash command, and one of an agent it spawned, runs in its slice, and the pass stops an ended run's slice and the Windows processes a track script recorded under it;
   a failing test, a test suite and a gate, stopped or not, leave no temp dir behind;
   an agent a run spawns (its `reader`) is not bound, held, refused or ended as a run, and stops at its next tool call once that run has ended;
   a `reader`'s Bash command that writes is denied;
   a dead ship process → rerun;
   a deploy alive runs to its end, whatever tree or tools ship arrives;
   a script ended 3 times on the same args without a result → raised once, a new args or a landed result restarts the count;
   a build or container check failing for the host's cause (memory, disk, docker, a killed run's container) exits 75, records no result and is run again, never the head's FAIL;
   the builds and container steps alive at once hold at most the host's MemTotal and nproc, a dev's own build counted: a tools ship moving 12 build keys starts 3 builds of 5g/4 CPUs on 19.5 GB/16 CPUs, the next on one's end;
   a build or gate alive under a key no longer current is stopped and the current one started, the proc record naming the key of the process holding it, a carry never stopped, and a batch gate on a prefix still current holds while members arrive;
   a gate row whose files did not change keeps its result, and a gate running such a row finishes;
   a yes recorded then the orchestrator gone → the ship completes;
   a repair whose effect is not observed is not logged;
   the same repair twice raises once;
   a second `hd ask` on a change with an open question is refused, and an open question holds the change (no run, gate, ship or upstream step) until its answer;
   a fix a dev files with `hd new --blocks` holds the change with no question raised;
   a change waiting on a fix waits on the change that carries it: a dependency on a superseded change, or a `--blocks` filing joined into an open change, names that change;
   a dependency cycle among open changes is one alert naming it, each change in it shows as in that cycle (never plain 'waiting on'), and `hd new` and a git commit naming harness/ refuse it;
   a repo without the noreply git identity gets it in one pass, so its clones commit with no per-run env;
   docker not answering → one alert, no script starts and no run that builds or tests (a code or judge run off the harness track) is listed, an unspawned one ends, and it is listed again once docker answers.

6. **R6** `tests.test_hd.R6`: the same T never builds or gates twice;
   the same head and contract never judge twice;
   no more than the configured agents are listed, the planner outside that count;
   with a band held, no run is listed for a change below it and a listed one is dropped;
   while a change of a higher tier has a run due and none listed or alive, no run is listed for a lower one, a dependency of the higher change still runs, and the lower is listed while every higher change only waits, has a run listed or alive, or has a due run the pass cannot list, which shows as an alert;
   `hd new` makes a harness change P1 at least;
   two passes over unchanged facts append no event;
   a run over the context limit is told to start no new work and hand off cleanly (commit and push its work in progress, record what it judged, collect its subagents and stop its processes, write the hand-off file: what is proven, what is left, the exact next step, whether a server or desktop is up), and its successor, the same role on the same change, is listed in the same pass with the hand-off file and that commit, past the tier hold and the agent count;
   three runs of a change past it since its last handover or the last planner run that handed back on that alert are raised;
   a session of no run past it is told nothing;
   a run whose desktops are up through a stretch of tool calls with no devtools call is told once to bring them down, the count starting again at its next devtools call or up;
   every run record carries its usage and transcript.
   Live: `tools/track.sh up <slug> 2` prints two logged-in desktops' ports and returns.

7. **R7** `tests.test_hd.R7`: `hd` output contains only spawns, cards, questions, runs, goals and change facts, and prints no step name as a state;
   a command missing an argument it reads prints its usage, never a traceback.
   Live: `python3 hd.py` on the real state.

8. **R8** `tests.test_hd.R8`: T is `git merge-tree` of base, deps and head;
   a head holding another PR's unmerged commits is a dev step before its build (stacked);
   a change whose same-track upstream dependency has a PR (open or not yet opened) joins it, its head on top of the dependency's, and waits on no upstream merge, while one in another repo holds its card until merged there;
   a PR has its card only when every open change of that PR is in its tip's head (one card, one carry);
   a head the upstream PR is at is not re-gated when main moves, and its pending reply's card shows at once;
   three handed-over harness changes merge into one batch tree, gated once and shipped once (a shorter prefix that passed ships only once the one longer fails), no second ship starting while one runs, and a failing batch is bisected to the change that fails alone, which leaves it once the live branch passes its rows alone (failing them, an alert and no member blamed), while one conflicting only with an earlier member waits, and the planner reads a batched member's failure from its batch's gate;
   `hd commit` waits for a ship's lock, commits its paths alone and pushes the live branch;
   a client code change ships in the client batch;
   a gated change has its card, and its carry planned, while T_int conflicts, the conflict's dev listed beside it;
   a server change's key and `CENTRAL` carry the merge of its central dependencies, and T_int the one of its heads';
   a conflict lists the dev;
   two changes adding facts to every other requirement and paragraph of PRD.md and ARCHITECTURE.md merge onto the live branch in either order, the same fact changed two ways conflicts, and a source doc out of the one-fact-per-line format fails the docs row;
   one change editing a fact line and another inserting a fact on the line before it merge in either order, while a code conflict beside them stays the dev's;
   a carried tools head its branch moved past is rebased by the pass and re-gated with no dev run, a rebase that stops listing the dev with its files;
   a harness hand-over whose carried tools heads' tests fail is refused;
   a build is keyed by T and tools/build/ alone, a gate by the build key, tools/gate/ and the rows' files: a gate-only tools edit rebuilds nothing;
   a row's key holds only the part of tools/gate/ it runs: an edit of one gate.sh verb re-runs that verb's rows alone, the fork CI row keeping its result;
   the live branch's own gate keeps a member's row results, and a ship keeps the gate of the tree it shipped;
   a batch merges its members' heads on one tools branch, a tools conflict with an earlier member waiting;
   a merge ref `local/merge/<a>-<b>` stands in for heads a and b (the base one of them) in T_int while a is an ancestor of (or is) the head, b of the current partner, and it merges, a later head merged on top of it;
   a pin's conflict lists the dev of the oldest gated change at its deploy step;
   T_int merges heads by priority, then creation, and a lower-priority head's conflict lists its dev while the higher-priority heads deploy;
   one T_int pass names every conflicting head (each left out, the rest merged on) in one dev run, with hd's merge order;
   build(T) runs once per T and in the change's build copy;
   the dev's clone is clean after a build;
   the cache step runs only when its input hash changes;
   every container, volume, clone, mobile and desktop is named by its change or run.
   Live: `tools/track.sh build <slug>` twice prints `cached` the second time.
