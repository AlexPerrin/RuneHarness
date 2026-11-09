---
slug: h-fork-build-v-clobber
track: harness
priority: P2
---
# fork build.sh tree(): the composite read loop clobbers the build version v



## alert 74 fault 347 (×1, first 2026-11-09T07:51:26+00:00)
tracks/fork/build/build.sh tree(): the dev path's 'while IFS== read -r k v' over hd candidate --composite clobbers the global v (build version, line 20); at EOF v is empty, so build_locked's label check compares '' to a missing image's '' and prints 'cached or:<T>' without building. Every dev build without TCOMMIT is skipped. Fix: read into other names (e.g. read -r ck cv).
