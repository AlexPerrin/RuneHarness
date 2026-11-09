#!/usr/bin/env python3
"""The server track's scripted criteria that read text. Exit 1 names every miss.
  text.py evidence   pr-comment.md and, for a new PR (no $PR), pr-title.txt and pr-body.md present and non-empty in $EVIDENCE
  text.py commits    every commit $BASE..$HEAD not on an existing PR's head fork/$PUBLIC_BRANCH nor on staging (unless staging holds $HEAD): subject feat:/fix:, no Claude-Session trailer, only a Co-Authored-By trailer
  text.py texts      a new PR's pr-body.md has upstream's template sections (read live from origin/main), no fork PR link in any text the carry posts (each pr-reply-*.md too),
                     pr-comment.md names $HEAD unless it is a reply in a review thread (it quotes the finding: '> ')
  text.py dupes      a module whose main sources gain an item-moving call has a test source added or changed ($BASE...$HEAD,
                     on an existing PR fork/$PUBLIC_BRANCH...$HEAD; for a head merging staging, only what staging...$HEAD adds too)
Env: EVIDENCE, CLONE, BASE, HEAD, PR, PUBLIC_BRANCH.
"""
import os, re, subprocess, sys

E, CLONE, BASE, HEAD = (os.environ.get(k, "") for k in ("EVIDENCE", "CLONE", "BASE", "HEAD"))
MOVES = re.compile(r"\b(inv(Add|Del|Transfer|Move|Replace|Swap|TakeFee|Transaction|Drop|Equip|Sell)[A-Za-z]*|wornUnequip|shopBuy|invSell|objRepo\.(add|del))\b")
FORK_LINK = re.compile(r"AlexPerrin/OpenRune-Server(#\d+|/pull/\d+)|\bfork PR #\d+", re.I)


def git(*a):
    return subprocess.run(["git", "-C", CLONE, *a], capture_output=True, text=True).stdout


def text(name):
    p = os.path.join(E, name)
    return open(p).read() if os.path.exists(p) else ""


def evidence():
    need = ("pr-comment.md",) + (() if os.environ.get("PR") else ("pr-title.txt", "pr-body.md"))  # an open PR keeps its title and body
    return [f"{n} missing or empty in {E}" for n in need if not text(n).strip()]


def live():
    # an existing PR's public head (fork/$PUBLIC_BRANCH) cannot change without a force-push: check only what follows it
    return f"fork/{os.environ['PUBLIC_BRANCH']}" if os.environ.get("PR") and os.environ.get("PUBLIC_BRANCH") else ""


def staging():
    # a head that merges staging (a staging repair) carries staging's own content over upstream main: none of it is the change's.
    # Unless staging already holds HEAD (then staging...HEAD is empty and would hide the change).
    s = "refs/heads/staging"
    held = subprocess.run(["git", "-C", CLONE, "merge-base", "--is-ancestor", HEAD, s], capture_output=True).returncode == 0
    return s if git("rev-parse", "--verify", "-q", s).strip() and not held else ""


def commits():
    bad = []
    for c in git("log", "--no-merges", "--format=%H%x01%s%x01%b%x02", HEAD, f"^{BASE}", *(f"^{r}" for r in (live(), staging()) if r)).split("\x02"):
        if not c.strip():
            continue
        sha, subject, body = (c.strip("\n") + "\x01\x01").split("\x01")[:3]
        if not re.match(r"(feat|fix)(\(.+\))?: ", subject):
            bad.append(f"{sha[:9]}: subject is not feat: or fix:: {subject[:60]}")
        trailers = [l for l in body.splitlines() if re.match(r"[A-Za-z-]+: ", l) and l.split(":")[0] in ("Claude-Session", "Co-Authored-By", "Signed-off-by")]
        if any(l.startswith("Claude-Session:") for l in trailers):
            bad.append(f"{sha[:9]}: carries a Claude-Session trailer")
        if any(not l.startswith("Co-Authored-By:") for l in trailers):
            bad.append(f"{sha[:9]}: a trailer other than Co-Authored-By")
    return bad


def texts():
    bad = []
    template = git("show", "origin/main:.github/pull_request_template.md")
    body = text("pr-body.md")
    for h in re.findall(r"^##+ *(.+?)\s*$", template, re.M) if not os.environ.get("PR") else []:
        if h.lower() not in body.lower():
            bad.append(f"pr-body.md lacks the template section '{h}'")
    for n in ["pr-title.txt", "pr-body.md", "pr-comment.md"] + sorted(f for f in (os.listdir(E) if os.path.isdir(E) else []) if re.fullmatch(r"pr-reply-.+\.md", f)):  # every text the carry posts
        if FORK_LINK.search(text(n)):
            bad.append(f"{n} links a fork PR (it renders as a red Closed on upstream)")
    if HEAD[:9] not in text("pr-comment.md") and not text("pr-comment.md").startswith("> "):
        bad.append(f"pr-comment.md does not name the head {HEAD[:9]}")
    return bad


def added(base):
    """The files and the added (path, line)s of base...HEAD."""
    files, lines, path = set(), set(), None
    for line in git("diff", "--unified=0", f"{base}...{HEAD}").splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            files.add(path)
        elif line.startswith("+") and path:
            lines.add((path, line[1:]))
    return files, lines


def dupes():
    files, lines = added(live() or BASE)
    if staging():   # the change's own: in neither upstream main (or the PR's live head) nor staging
        f2, l2 = added(staging())
        files, lines = files & f2, lines & l2
    flows = {}
    tested = {p[:m.start()] for p in files if p and (m := re.search("/src/(test|integration)/", p))}
    for path, line in lines:
        if "/src/main/" in path and path.endswith(".kt"):
            for m in MOVES.finditer(line):
                flows.setdefault(path, set()).add(m.group(1))
    bad = []
    for p, calls in sorted(flows.items()):
        mod = p.split("/src/main/")[0]
        print(f"item flow in {p}: {', '.join(sorted(calls))}")
        if mod not in tested:
            bad.append(f"{mod} moves items with no test source added or changed (upstream AGENTS.md: a dupe test per flow)")
    return bad


if __name__ == "__main__":
    bad = {"evidence": evidence, "commits": commits, "texts": texts, "dupes": dupes}[sys.argv[1]]()
    print("\n".join(bad) or f"{sys.argv[1]}: ok")
    sys.exit(1 if bad else 0)
