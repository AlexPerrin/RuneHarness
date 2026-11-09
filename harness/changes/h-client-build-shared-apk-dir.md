---
slug: h-client-build-shared-apk-dir
track: harness
priority: P1
---
# client build: every build copy links re/apk to the main checkout's, so concurrent repacks race on one decoded tree

Run 301: tracks/client/build/build.sh links each re/* but host|build|out|devtools|devtools-build from ~/osrs-plugins-reverse into the build copy, re/apk among them. tools/repack.sh does rm -rf $RE/apk/base, apktool d into it, patches it in place (patch_local_auth, patch_telemetry, smali edits) and builds from it, then base-single the same way. Two builds at once share that tree: run 301's build of h-mobile-loading-stall (T b7614854) failed 'rm: cannot remove .../re/apk/base/smali/com/google/android/gms/internal: Directory not empty' (evidence/h-mobile-loading-stall/repack-b76148548dff7cc00e9c50c868545341ff08719a.log), and a build that does not fail can package another build's half-patched tree. Fix: re/apk is the copy's own (excluded from the links like host and build). Done when two builds started together both pass check-log and their APKs differ only by what their trees differ by.
