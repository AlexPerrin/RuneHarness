# Requirements

What any solution to docs/PROBLEM.md must do, grouped by the harness's four jobs and the user's authority. Each
requirement is testable; docs/ARCHITECTURE.md names the mechanism that meets it.

The workflow they constrain: a change is defined → its criteria are agreed → a dev submits a head → scripts check
the candidate → qa judges the head → it reaches staging and, for a public act, a card → the user's approval →
publish → maintainers' findings become criteria.

## M. Memory

- **M1** Every decision is recorded once, by the actor that made it, bound to what it covers: a submission to its
  head and candidate; a check result to the candidate tree; a verdict to the head and the criteria it judged; a
  decision of the user to its question; an approval to the card's exact acts and texts; a published step to its
  card. A record is void when what it covers moves, and is never recomputed from the live world.
- **M2** The ledger is one typed store: every kind of record has a schema, kinds are columns never text prefixes,
  a record cannot exist without what it refers to, a run ends once, migrations are code with a test.
- **M3** Observations of the world (a ref's sha, a GitHub resource and its ETag, a landed head, a running
  container) are stored when observed, with what they observed, so a pass reads the world only where it moved.
- **M4** Definitions (changes, goals) and evidence (accuracy specs, PR texts, in-game proof) are files in this repo,
  committed, so the user can read and edit them as text and git holds their history.
- **M5** A run's brief is its one read of its change: the definition, the criteria with their results, the decisions
  and findings since its last submission, the check details, the hand-off of a predecessor; nothing is re-read.

## H. Hands

- **H1** Build, bring-up, check, deploy, publish and measure are scripts per track, in this repo, blocking on facts
  and returning results; an agent runs them by one command and never reproduces their steps by hand.
- **H2** A candidate tree is built at most once, in a copy no agent commits from; its build serves the dev's
  check, the gate, the evaluator and the deployment. A build, gate or deployment is keyed by the tree it runs on and
  an explicit recipe version, never by the checker's code; a fixed checker is re-run on request.
- **H3** A script logs each step it completes, so an interrupted one resumes and a hung one names its step; a step
  that fails for a cause outside the tree (host, quota, a source down) records no result and runs again.
- **H4** The test server runs staging: one branch holding the base, the permanent local branches and every checked
  server head, merged once each; a conflict is the dev's step; a closed change is reverted out, and so is a local
  branch the merging change supersedes. A server change is built and judged on staging (its candidate is staging plus
  its head), so it is proved on what the test server runs; its PR is packaged from the head alone (G4).
- **H5** Every process a run starts is the run's: stopped with it, bounded by one count of builds and one of agents,
  named after its change or run. No mobile or desktop contacts Jagex, checked by its bring-up.
- **H6** Harness and client changes ship one at a time by fast-forward of the live branch to a checked candidate.
- **H7** A build artifact (image, volume, container, clone, build copy, context) exists only while a fact names it:
  each is recorded with its owners (a change, a tree a change still names, a job, a run), and the pass releases it
  once none holds (a new head, close, merge, withdrawal, a job's or run's end, a kill included), ending on its observed
  absence. Content-addressed caches are shared (one Gradle home per build slot; one cache store per game revision); the build cache
  goes when the last build ends. The free space of the build disks is a fact: below a set level no build starts and
  the user is told compaction is due, with its commands.
- **H8** The local stack is a reference OpenRune deployment: the server built and run as upstream's release is (the
  release workflow's Gradle steps and bundle, `java -jar server.jar` beside `game.yml` and `.data/`), Central embedded
  (`central.same-instance`) on upstream's ports serving the clients' config and sign-in, the cache from OpenRune-FileStore,
  and desktops connecting through RSProx as upstream's README sets out. A harness stand-in for what these tools do
  goes. Login works for any client: every desktop and the APK sign in by that one path, each proved on the live stack. Each
  remaining deviation is named with its reason in docs/ARCHITECTURE.md; Privacy outranks the reference.

## G. Gate

- **G1** Criteria are written before the code: the track's seed criteria, the accuracy specification from the
  recordings and the wiki, the live upstream rules with their blob shas, the user's decisions, maintainers'
  findings. Each is scripted (a command the gate runs) or judged (the evaluator checks it), and checkable from the
  change's own build before its verdict: a claim seen only once deployed (on the live test server, on a mobile) is a
  client change depending on it, never its criterion. A criterion added later joins the change at its next head.
- **G2** Cheapest first, each once: the gate runs every scripted criterion on the candidate before any evaluator
  run; the evaluator runs only where judged criteria exist and judges every one, pass or fail, never passing one it
  did not check; nothing is checked twice for the same tree, head and criteria.
- **G3** A failing verdict lists the dev before anything is built, gated or judged again; a text-only failure is
  fixed in place and re-marked without a new dev run.
- **G4** An upstream PR is self-contained: its head holds no unmerged commit of another PR nor any staged commit, and
  its CI runs it on upstream main; a dependency in another PR holds only the card until merged there, never the dev work.
- **G5** A harness change is checked against reality before it ships: its tests, and its pass replayed over a
  snapshot of the live ledger, differing from the live pass only where a criterion says so.

## A. Authority

- **A1** Only a write to an OpenRune repo and a client release need the user. Each is one card in the driver's
  chat: every act in order, each exact text, the verdict, the evidence, and the three commands.
- **A2** `hd approve <slug> <head>` is the user's alone: their own `!` command, or, in a remote session where `!` cannot be
  sent, their word "approve" in the driver's chat, which the driver runs for that card; it copies the card into the approval. The publish
  executes the approval's steps with its texts, logging each, resuming from the first not done, and nothing else. A
  new head or text makes a new card. `hd hold` hides a card; `hd close` ends a change. Agents cannot run approve or
  close.
- **A3** A maintainer's word is triaged by the driver as a finding, an ask of the user, or an acknowledgement;
  a finding is a criterion on the PR's one open change; one comment per published head answers every finding; CI is
  never re-run at a head but by the user's word.
- **A4** A question to the user carries typed options, each with its effect (a dependency, a waived criterion, an
  accepted difference, a close, a repo move); the decision applies the effect. Only the user's decision accepts a
  difference from the official game.
- **A5** The user's standing holds (a track held from upstream, a priority band held) are records the loop obeys
  until the user lifts them.

## T. Tempo

- **T1** The loop is a pass: observe what moved, decide every change's next step from the ledger, act. It runs on a
  timer, after every run end and after every command; it costs under a second when nothing moved; it logs only when
  a change's state changes.
- **T2** A step is "done when this record exists" and any process may die anywhere; the next pass continues from
  the ledger. Nothing is decided from elapsed time.
- **T3** A run ends only by its own hand-back (one line, checked against its record), the orchestrator's stop, its
  change's close or its console's death; the pass never ends a live run. At the context limit a run hands off to a
  successor listed at once.
- **T4** Runs are bounded by one count; priority is the user's tiers P0–P4 with a held band (their order: the client
  and the server work it needs, then overlapping upstream work, then content for its own sake); harness changes first,
  then PR rounds, then new content; a change takes the best tier of the changes it blocks; one dev and one qa run
  per head move.
- **T5** The orchestrator is a visible session with the lifecycle of a run: bound when it starts, shown only what is
  new since its last view, drained when its context nears the limit or its definition moved, ended by its own exit,
  replaced by a supervisor; it holds no state, spawns what `hd` lists, inspects every run's transcript, processes and
  stack, corrects or stops an agent not moving its change toward its brief, and never chats or waits on the user. The
  driver is the console the user chats with: it shows cards, questions and alerts and does what the user says, nothing
  on its own.
- **T6** Harness defects are facts the pass computes into alerts with a dedup key, not findings an agent searches
  for; the user disposes of each once through the driver: a one-off fix, a harness change a dev fixes at the root, or
  a dismissal; an alert recurring after its fix landed reprints as a regression. No agent runs to look for problems.
- **T7** `hd` prints spawns, cards, questions, triage lines, alerts, runs and goals, derived; `hd kpi` prints the
  harness goal's numbers; every run is an agent of the visible orchestrator.
- **T8** A goal is measured whenever its target's tree moves; a goal below target with nothing open lists one dev
  run in plan mode, which files changes and no code.

## Acceptance

`python3 -m unittest discover -s tests`: one class per letter group over recorded ledger snapshots (decide), a
throwaway git repo and a recorded HTTP transcript (observe), a fake GitHub transport (publish), the hook's JSON
(hook). docs/ACCEPTANCE.json lists each requirement with `passes`. Live checks: a harness change ships through its
own loop (H6, G5); an upstream change reaches a ready PR after one approval and a publish killed after its push
resumes (A2); a maintainer finding reaches a new PR comment through the loop (A3).
