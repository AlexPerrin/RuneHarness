---
slug: h-fork-build-stale-pack-state
track: harness
priority: P1
---
# fork build: every tree's server cache packed as CI packs it, no incremental state carried from another tree

tracks/fork/build/build.sh reuses the build copy (git clean -fd keeps the ignored .data/cache/incremental_live and incremental_server) and the store's copied .data/cache, so or-cache's incremental packing skips a pack type whose TOML files are unchanged. Its unit fingerprint (or-cache PackServerConfigOSRS.kt init: PackUnit sources = the type's toml files) omits the gameval ids the TOML resolves through, and FileStore's reseedServerCache restores the previous server outputs, so a renumbered id in a gamevals.toml leaves the server cache holding the old id. Seen: hunter-feat-pr 637cedb renumbers projanim.telegrab 65534->65523; or:0abbfc5be22c (log state/hunter-feat-pr/build-0abbfc5be22ca6f36993c25bc5755fcc04e1849d_c022e2f6d72a5-1.log: 'Packing Server Configs 1/1 varp' only) has no projectile 65523, and Telekinetic Grab on a goat throws 'Projectile not found: projanim.telegrab' (evidence/hunter-feat-pr/in-game-283.md). Upstream CI packs from a fresh checkout and is unaffected. Fix in the build: no incremental state from another tree reaches a build (OPENRUNE_FULL_REBUILD=1 in the container, or the state removed with the copy's clean), and an or:<T> already built from carried state (or:0abbfc5be22c) is built again. Proof: hunter-feat-pr's candidate rebuilt holds getProjectile(65523); a test of the build recipe.
