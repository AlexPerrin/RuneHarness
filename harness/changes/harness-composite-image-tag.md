---
slug: harness-composite-image-tag
track: harness
priority: P1
---
# fork build: a composite build's image tag is not a valid docker tag

tracks/fork/build/build.sh names a build with CENTRAL or FILESTORE or:<T>+c<central tree12> (composite_suffix). Docker refuses '+' in a tag (invalid reference format), so gradle succeeds and docker build fails: every server change built with a Central or FileStore head cannot build, up, test or gate. Seen in run 41: state/server-android-token-login/build-e5399e3be249b7709d38c1e8b4811b3a2c15b0ab+cc6e461efc74e-1.log. The tag must keep the composite key distinct (e.g. '-c<tree12>' or '_c'), and every reader of or:$T (track.sh up/token, gate.sh seed, deploy) must agree with it; decide.py's build key may keep '+'.
