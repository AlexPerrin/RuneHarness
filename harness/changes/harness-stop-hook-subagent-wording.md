---
slug: harness-stop-hook-subagent-wording
track: harness
title: The stop hook calls a live subagent a background command; empty slices and
  temp dirs linger
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T06:46:44Z'
---
Monitor sweep 48 P2-a: keeper-after-failed-1's stop was refused at 06:27:42Z with 'background command(s) a191368c66e8eb3bb ... block on it in the foreground with one until-loop' though it was a reader subagent (hook.py:308-315); the run's TaskStop then failed ('owned by a191368c66e8eb3bb'). hold_handback (hook.py:205-213) already tells the two apart. P2-c: empty slices hd-t2553453, t2571495, t2575550 (0 tasks since 06:11-06:14Z) and stale /tmp/hd-suite-*, /tmp/hd-run-3aea6div are never removed. Acceptance: the refusal names a subagent as a subagent to wait for; empty slices and a run's temp dirs are removed when their run ends.

Also (filed): A run cannot find its own hung process: the hook denies its pgrep and nothing else names it
Monitor sweep 49 P2-a: server-clan-guest-3's `track.sh down server-clan-guest` (pid 2850649) hung; at 06:48:02Z the hook denied the run's pgrep for it ('self-matching pgrep'), and nothing else lists a run's processes, so the run cannot stop a process it started. Acceptance: a run can list the processes of its own slice (e.g. hd names them, or the denial suggests a non-self-matching form) and stop its own.

Also (filed): A failing tools test leaks its systemd slice; stale suite temp dirs remain
Monitor sweep 50 P2-b: empty slices hd-t2553453, hd-t2571495, hd-t2575550 (06:11-06:14Z) are still active: test_tools.py:415-424 test_each_desktop_jvm_is_recorded_under_the_runs_slice_until_down stops its slice only after its asserts pass, with no addCleanup; hd's slices() (hd.py:297) lists them. Stale /tmp/hd-suite-zk2pf16n (57M), /tmp/hd-suite-jsm6083l, /tmp/hd-run-3aea6div. Acceptance: a test's slice and temp dirs go whatever its outcome; existing leftovers are removed.

Also (filed): The pass can stop a running test's slice, and pre-existing /tmp/hd-* dirs are never removed
Monitor sweep 51 P2-a: b875d38's pass (hd.py, live[sl] == 0 branch) stops every 0-task hd-* slice no live run holds, from one systemctl show read before a loop of systemctl stop calls (120 s timeout each); a test (hd-t<pid>.slice) or run can start a scope in that gap and be killed. P3-a: hook.py:241 puts new runs' TMPDIR under state/tmp/<slice>, but /tmp/hd-suite-zk2pf16n (57M), hd-suite-jsm6083l, hd-suite-7bcgmzgh and hd-run-3aea6div stay forever. Acceptance: the pass never stops a slice whose creator is alive (e.g. hd-t<pid> only once <pid> is dead, TasksCurrent re-read before each stop); /tmp/hd-* dirs no live process holds are removed.
