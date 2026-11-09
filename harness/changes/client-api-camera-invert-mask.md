---
slug: client-api-camera-invert-mask
track: client
priority: P2
goal: client-api
---
# Client setInvertPitch/setInvertYaw/setCameraMouseButtonMask still ClientStub throws on Android

Split from client-api-client-stubs (it carries the camera rows with a game field: pitch relaxer, orb/free speed, camera speed). evidence/client-api/api-probe.tsv reads inert (ClientStub throw) for setInvertPitch, setInvertYaw, setCameraMouseButtonMask. The Android game has no invert flag or mouse-button camera mask (static RE, docs/offsets.md 'camera speeds'): the touch drag (touch state 8 in 0x41d0a4, decomp 0051d0a4.c:2624-2658) writes the yaw delta Client +0x894b0 and pitch delta +0x894ac from the pixel deltas times the settings sensitivity, with no sign flag; key rotation uses fixed +-0xc0/+-0x60 targets; a mouse drag is the same touch state. The setters drive that form: invert negates the delta the drag produced (an inline hook after the two stores, or on the targets they feed) per axis; the mouse-button mask selects which pointer buttons start state 8 when a mouse is attached (or the row is excluded with the reason if Android routes no button to it). The probe reads each effect where it lands (the delta / target after a synthetic drag). Done when the three rows pass on the mobile measure with no pass lost.
