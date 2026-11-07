---
slug: h-filestore-build
track: harness
priority: P1
---
# filestore track: a FileStore head builds, tests and reaches a server build

Two defects stop every FileStore change (found by run 104 at 45516d0): (1) tracks/filestore/track.sh gradle() runs ./gradlew, but upstream OpenRune-FileStore commits gradlew as mode 100644, so build and test fail with 'gradlew: Permission denied' (run it as 'bash ./gradlew'). (2) tracks/fork/build/filestore.init.gradle: the fork's composite build with FILESTORE fails at configuration with 'RootProjectAccessor.java: method getFilestore() is already defined' (the fork enables TYPESAFE_PROJECT_ACCESSORS; FileStore's root project is named 'filestore' and includes a subproject ':filestore'), so 'track.sh up' never builds a server with the head. Proof: tracks/filestore/track.sh build, test and up filestore-cs2-group-name-hash at 45516d0 all succeed; a test per fix.
