#!/usr/bin/env bash
# tracks/server.sh <verb> <slug> [args]: the server track's scripts. Each verb blocks on facts and prints its result;
# the pass and the agents call the same verbs (docs/ARCHITECTURE.md). Env from hd: SLUG HEAD T TCOMMIT BASE CLONE
# EVIDENCE WORK. Artefacts are named by the change: ~/src/work/<slug>-build, container build-<slug>, volume
# gradle-<slug>, image or:<T>, containers server-<slug> and http-<slug>, client windows titled <slug>.
set -euo pipefail
verb=$1; slug=$2; shift 2

build()      { :; }   # R8: the build copy checked out at TCOMMIT (dev: the working copy snapshotted to an anonymous commit first);
                      #     cached when image or:<T> exists → prints `cached`; else Gradle in build-<slug> with volume gradle-<slug>
                      #     and the remote build cache; the game cache from ~/src/work/cache keyed by its input hash; image or:<T>;
                      #     the dev's clone untouched; writes state/<slug>/build.json {T, ok, detail}; log kept per T.
up()         { :; }   # server-<slug> from or:<T> on the change's ports, http-<slug> sidecar with jav_config rewritten to
                      #     localhost; waits for "Server ready in"; seeds the accounts (members); starts N desktop clients titled
                      #     <slug>, logs each in by widget actions (no coordinates); blocks until every devtools endpoint answers;
                      #     prints `LOGGED_IN <client> <devtools port>` per client. Fact-based waits only.
down()       { :; }   # stops the clients titled <slug>, removes server-<slug> and http-<slug>.
gate()       { :; }   # R3: every `check:` and `gate:` row of the contract with the env; writes state/<slug>/gate.json {T, ok, detail}.
gate_ci()    { :; }   # pushes TCOMMIT to fork gate/<slug>, dispatches CI and Formatting if absent, blocks until both conclude.
ship()       { :; }   # the integration tree: build (cached by T), image, deploy with rollback tag, "Server ready in" or roll
                      #     back; writes state/live/tree.json {tree, commit, heads, names}. One at a time by construction.
measure()    { :; }   # R1: the server goal: harness/goals/<goal>.json rows {unit, source, passes} → the share passing;
                      #     writes state/<goal>/measure.json {tree, value, report}.
log()        { :; }   # the server-<slug> log since the run's marker, filtered by pattern.
recordings() { :; }   # the RSProx index: which recordings hold a packet type or text (every filter on).

case $verb in build|up|down|gate|gate-ci|ship|measure|log|recordings) ${verb//-/_} "$@" ;; *) echo "verbs: build up down gate gate-ci ship measure log recordings" >&2; exit 2 ;; esac
