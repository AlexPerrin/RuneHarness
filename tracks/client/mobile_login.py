#!/usr/bin/env python3
"""mobile_login.py <slug>: launches the app on $ANDROID_SERIAL and signs in at Central's form as the slug's own account; prints LOGGED_IN or FAILED: <why>.
Each step acts once on the screen it reads (the host's GameStateChanged and LoginIndex lines, the focused window, the view
labels), then waits for the next screen; a screen it does not know, a refused login or the app's death is FAILED.
"""
import datetime, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

ADB = os.environ.get("ADB", "/mnt/c/Users/Alex/AppData/Local/Android/Sdk/platform-tools/adb.exe")
PKG = "com.jagex.oldscape.android"
CANVAS = {0: ("Existing User", 1370, 625), 12: ("Accept", 1027, 668), 10: ("Play Now", 1197, 540)}   # LoginIndex: the button that leaves it, on the AVD's 2400x1080 landscape canvas
LAUNCHER = "com.google.android.apps.nexuslauncher"
WAIT = {-1, 30, 37}   # no screen yet, the browser's sign-in, the connection to the world: the next screen comes from the app, the browser or the server
REFUSED = 9           # "Unexpected server response", Try again: a login response without a page of its own, or a failed reconnect after a lost connection
START_ERROR = 1000   # the app's start page "Error connecting to server": the host logs it as UNKNOWN (raw 1000), and nothing after it
LABELS = ("Use without an account", "Stay signed out", "No thanks", "Close", "Accept")   # Chrome's first run and prompts before the issuer's /oauth2/auth
FORM = ("Username", "Password", "Sign in")   # Central's sign-in form (no dev account): each mobile its slug's own account, never one shared (a second login of one account is refused Duplicate)


def account(slug):
    """The slug's mobile account, name and password: the fork track's account() names with 'm' for the desktops' N (a run's mobile and live desktop differ)."""
    return "h" + hashlib.sha1(slug.encode()).hexdigest()[:9] + "m"


def adb(*a, retries=5):
    for _ in range(retries):
        r = subprocess.run([ADB, "-s", os.environ["ANDROID_SERIAL"], *a], capture_output=True, text=True)
        if "accept4 failed" not in r.stderr:
            return r.stdout.replace("\r", "")
        time.sleep(1)
    return ""


def labels():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    xml = adb("exec-out", "cat", "/sdcard/ui.xml")
    return {m[0].strip(): ((int(m[1]) + int(m[3])) // 2, (int(m[2]) + int(m[4])) // 2)
            for m in re.findall(r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml)}


def screen():
    """(game state, LoginIndex, focused package, the labels of a window not the app's, the game's raw state)."""
    log = adb("logcat", "-d", "-s", "osrsrl-host:I")
    st = re.findall(r"GameStateChanged (\w+)(?: \(raw (-?\d+))?", log); ix = re.findall(r"LoginIndex (\d+)", log)
    focus = re.search(r"mCurrentFocus=Window\{\S+ \S+ ([^/}\s]+)", adb("shell", "dumpsys", "window"))
    pkg = focus.group(1) if focus else ""
    return (st[-1][0] if st else "", int(ix[-1]) if ix else -1, pkg, ({} if pkg in (PKG, "") else labels()),
            int(st[-1][1]) if st and st[-1][1] else None)


def step(st, ix, pkg, lab, raw=None, name=""):
    """The action on one screen: ('done',), ('wait',), ('tap', name, x, y), ('sign_in',) or ('fail', why)."""
    if st == "LOGGED_IN":
        return ("done",)
    if raw == START_ERROR:
        return ("fail", "the app's start error page 'Error connecting to server' (gameState 1000)")
    if pkg == "com.android.chrome":
        err = next((t for t in lab if re.search(r"ERR_[A-Z_]+", t)), None)
        if err:
            return ("fail", f"the browser's sign-in: {err}")
        if all(l in lab for l in FORM):
            return ("wait",) if name in lab else ("sign_in",)   # the name typed: the form posts, its answer comes next
        hit = next((l for l in LABELS if l in lab), None)
        return ("tap", hit, *lab[hit]) if hit else ("wait",)   # the issuer's page redirects back to the app by itself
    if pkg == LAUNCHER and st in ("", "UNKNOWN"):
        return ("wait",)   # the process runs before its window takes focus from the launcher; main() fails a death
    if "Wait" in lab and any(t.endswith("isn't responding") for t in lab):
        return ("tap", "Wait", *lab["Wait"])   # the system's ANR dialog (the emulator's launcher while the app starts): the app goes on behind it
    if pkg not in (PKG, ""):
        return ("fail", f"an unknown window {pkg}: {', '.join(lab) or 'no labels'}")
    if st != "LOGIN_SCREEN":
        return ("wait",)   # starting, LOGGING_IN, LOADING: the next state comes from the app or the server
    if ix == REFUSED:
        return ("fail", "the server answered the login or its reconnect unexpectedly (LoginIndex 9)")
    if ix in CANVAS:
        return ("tap", *CANVAS[ix])
    return ("wait",) if ix in WAIT else ("fail", f"an unknown login screen (LoginIndex {ix})")


def sign_in(lab, name):
    """Types the account into Central's form (a label's tap focuses its field) and posts it."""
    for f in FORM[:2]:
        adb("shell", "input", "tap", *map(str, lab[f])); adb("shell", "input", "text", name)
    adb("shell", "input", "tap", *map(str, lab[FORM[2]]))


def main(slug):
    name, signed = account(slug), False
    adb("logcat", "-c")
    adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    started, acted = False, None
    while True:
        st, ix, pkg, lab, raw = screen()
        alive = bool(adb("shell", "pidof", PKG).strip())
        if started and not alive:
            return "FAILED: the app died"
        started |= alive   # monkey returns before the process exists
        act = step(st, ix, pkg, lab, raw, name)
        if act[0] == "done":
            return "LOGGED_IN"
        if act[0] == "fail":
            return "FAILED: " + act[1]
        if act[0] == "sign_in":   # an empty form after the post is Central's refusal (401 answers the form again)
            if signed:
                return f"FAILED: Central refused the sign-in of {name}"
            print(f"Central's sign-in: {name}", file=sys.stderr, flush=True); sign_in(lab, name); signed = True
            continue
        here = (st, ix, pkg, act[1:2])
        if act[0] == "tap" and here != acted:   # one tap per screen, then the next screen is read: a second tap on one screen toggles panels
            print(f"{st} LoginIndex {ix} {pkg}: {act[1]}", file=sys.stderr, flush=True)
            adb("shell", "input", "tap", str(act[2]), str(act[3])); acted = here
        time.sleep(1)


def recreated(since):
    """The live stack's containers (state/live/tree.json) started after `since` (UTC ISO): a deploy replaced the server under the start."""
    try:
        names = json.loads((ROOT / "state/live/tree.json").read_text()).get("containers", [])
        out = subprocess.run(["docker", "inspect", "-f", "{{.Name}} {{.State.StartedAt}}", *names], capture_output=True, text=True).stdout
    except (OSError, ValueError):
        return []
    return [l.split()[0].lstrip("/") for l in out.splitlines() if l.split()[-1] > since]


ROOT = Path(os.environ.get("HD_ROOT") or Path(__file__).resolve().parents[2])

if __name__ == "__main__":
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    r = main(sys.argv[1])
    if r != "LOGGED_IN" and (gone := recreated(since)):
        r += f" while a deploy recreated the live stack ({', '.join(gone)})"
    if r != "LOGGED_IN":   # up's failure path kills the emulator: the start's logcat is kept before it
        d = ROOT / "state" / sys.argv[1]
        d.mkdir(parents=True, exist_ok=True); (d / "login-failed.logcat.txt").write_text(adb("logcat", "-d", "-v", "threadtime"))
        # the game server's side of the same start (its login refusals and their reason, the sessions it holds): a later deploy loses it
        srv = subprocess.run(["docker", "logs", "-t", "--since", (datetime.datetime.fromisoformat(since) - datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "osrs-openrune"],
                             capture_output=True, text=True)
        (d / "login-failed.server.txt").write_text(srv.stdout + srv.stderr)
    print(r)
    sys.exit(0 if r == "LOGGED_IN" else 1)
