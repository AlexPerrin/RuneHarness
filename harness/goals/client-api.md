---
slug: client-api
track: client
target: 100
deps: [harness-device-network-block]
---
## Goal
100% of the RuneLite API interface methods working in the official OSRS Android app. The metric is the share of the
methods of `net.runelite.api.Client` and the other `net.runelite.api` interfaces that the probe calls in the running app
(against the test server) and confirms: a value of the declared type, no exception, and for the methods the host maps to
native hooks the expected effect in the client. The probe prints the percentage and writes its per-method report
(method, result, evidence) to the evidence dir; the orchestrator reads the report to pick the gaps.
