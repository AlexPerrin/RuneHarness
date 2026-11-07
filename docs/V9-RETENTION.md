# V9 retention

The hand-off for the harness developer: v8 creates build artifacts for every change and removes none of them. On
2026-11-06 the host's C: drive was 94% full (868 of 931 GB used) with the harness idle; one session removed the
artifacts by hand. This document states what accumulated, the root cause, and the requirement v9 meets. Read it with
docs/V9-BRIEF.md §2.2 (tracks) and §3b (harness health).

## 1. What accumulated (measured 2026-11-06, no run live)
| Artifact | Created by | Measured | Removed by |
|---|---|---|---|
| Server image `or:<T>` / `osrs-openrune:<T>` (one per tree T built) | `tracks/fork/build/build.sh` (`docker build -t or:$T`) | 830 images, 242 GB; 10 in use, 213.7 GB pruned | nothing |
| Gradle volume `gradle-<slug>` (one per change) | `tracks/fork/gate/gate.sh` (`-v gradle-$slug:/gradle`), `openrune-gradle`, `upstream-pr-gradle-*` | 58 unattached volumes, about 65 GB, each 1.0-2.0 GB of the same dependency cache | nothing |
| Cache store volume `or-cache-store` | the build's `$GK` asset cache | 32 GB | nothing |
| Build cache | `docker build` | 54 GB, 21 GB reclaimable | nothing |
| QA clone per built tree `openrune-work/qa/integration-<T>`, `<slug>-run` | the v8 gate and integration runs | 157 dirs, 110 GB, 2.3 GB each, the oldest 19 days; every one dirty only in regenerated `.data/gamevals/*.rscm` | nothing |
| Image build context `openrune-work/image-<T>` | the v8 image build (v9: `$copy/.image`, `rm -rf`'d only before the next build of the same copy) | 29 dirs, 16 GB | nothing |
| Build worktrees `OpenRune-Server/.worktrees/<slug>` and `<slug>-build` | `build.sh` (`git worktree add`) | 35 GB | nothing |
| Stopped containers `http-<slug>`, `server-<slug>`, `boot-<T>` | `track.sh up` | 13 containers | `down` removes a stack's containers; a killed run leaves them |

`grep` of `tracks/fork/{track.sh,build/build.sh,gate/gate.sh}` for `rmi`, `image prune`, `volume rm`, `builder prune`,
`worktree remove` finds none. The only removals are `docker rm -f` of a slug's own containers and `rm -rf` of a
directory about to be rebuilt in place.

## 2. Why disk cannot be reclaimed after the fact
Docker Desktop and WSL keep their data in two `.vhdx` files that grow and never shrink: deleting files or pruning
inside them leaves C: unchanged until the file is compacted from Windows (`wsl --shutdown`, then `Optimize-VHD -Mode
Full` in an admin shell; sparse VHD is disabled by WSL as unsafe). On 2026-11-06 they held 374 GB (`docker_data.vhdx`)
and 257 GB (`ext4.vhdx`) of which 23 GB and 100 GB were live after cleanup. Compaction needs every WSL process and
Docker Desktop stopped, so the harness can never do it; it can only keep the files from growing.

## 3. Root cause
An artifact is created keyed by a tree T, a slug or a commit, and nothing records that its key stopped being needed.
No step of a change's life (merge, close, supersede, new head, withdraw) names the artifacts it orphans, so the only
owner of the disk is the user. The two per-slug stores multiply the cost: a Gradle cache is content-addressed and
identical across slugs, yet each slug gets its own 1-2 GB volume, and every new head of a change adds an image and a
clone that the old head's no longer need.

## 4. Requirement
An artifact exists only while an observable fact names it; the step that makes the fact false removes it.
1. **The store records the owner.** Every image, volume, clone, worktree and context is a row `(kind, key, owner)`
   where the owner is a change head T, a run, or an open card. This is the store of V9-BRIEF §2.7; no scan of the
   host decides what to delete.
2. **Release is a step of the event, not a sweep.** A new head of a change releases the artifacts of its previous T
   unless a card or a run still names them. Close, merge and withdraw release the change's. A run's end releases its
   containers and clones. The release verb (`docker rmi`, `docker volume rm`, `git worktree remove`, `rm -rf`) is
   idempotent and ends on the observed absence of the artifact (CLAUDE.md: atomic, not timed).
3. **One Gradle cache volume**, shared by every slug (a content-addressed cache needs no per-slug copy), replacing the
   58 per-slug ones. `or-cache-store` is likewise one volume keyed by its input hash, kept while any open change
   builds from that input.
4. **The build cache is bounded by its owner too**: `docker builder prune` runs when the last build of a T ends
   (observed: no build container live), never on a clock.
5. **A disk fact is a harness fact.** `hd` reads free space on the volume that holds `$HOME/src` and on the Windows
   host drive (`df /mnt/c`) in the pass and raises an alert at a set free-space level: the user is told that
   compaction is due, with the exact commands of §2. Below the level, no new build starts (a build that the host
   refuses already exits 75: V9-BRIEF §2.3), so the pass never fills the drive.
6. **A kill leaves nothing.** A run killed mid-build leaves `build-<slug>`, `boot-<T>` and partial `.tmp` directories;
   `hd`'s repair removes every container, `.tmp` and clone whose owner row is gone, found by the store, not by name.

## 5. KPIs (add to V9-BRIEF §3b)
- Retained bytes per closed change: 0 images, 0 volumes, 0 clones, 0 worktrees after its release step.
- Images on the host: at most the images named by open changes' heads and live stacks (10 after the cleanup, which is
  the right order of magnitude).
- Free space on the host drive at the end of a 47 h window equals its start, within the open changes' artifacts.

## 6. Out of scope
Compacting the `.vhdx` files (needs the user: §2). The server clone `OpenRune-Server`, `osrs-plugins-reverse` (18 GB)
and `~/.claude` (17 GB: transcripts, agent dashboard) hold history and are not build artifacts.
