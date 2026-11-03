---
slug: h-test-warnings
track: harness
priority: P2
---
# tests: no ResourceWarning in the gate log

The gate log of a passing suite is full of ResourceWarning lines: tests/test_observe.py opens files with open(...).write(...) and never closes them. Write the fixtures with pathlib.Path(...).write_text(...) so a passing run of python3 -m unittest discover -s tests prints no ResourceWarning. Touch nothing else.
