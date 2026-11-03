---
slug: h-criterion-cmd-dest
track: harness
priority: P2
---
# hd criterion add: --cmd option shares dest 'cmd' with the subcommand (use dest cmd_text)



## alert 1 fault 7 (×1, first 2026-11-03T03:47:23+00:00)
hd criterion add is unusable: the subparser's --cmd shares dest 'cmd' with the subcommand, so main() dispatches to cmd_<--cmd value> (KeyError cmd_accuracy) or, without --cmd, to the view and adds nothing. Fix: dest='cmd_text' on the option. Worked around by calling cmd_criterion with a Namespace.
