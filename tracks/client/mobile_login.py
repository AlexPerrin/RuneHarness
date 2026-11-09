#!/usr/bin/env python3
"""mobile_login.py <slug>: launches the app on $ANDROID_SERIAL and signs in at Central's form as the slug's own account; prints LOGGED_IN or FAILED: <why>.
Each step acts once on the screen it reads (the host's GameStateChanged and LoginIndex lines, the focused window, the view
labels), then waits for the next screen; a screen it does not know, a refused login, the game server losing the session before LOGGED_IN or the app's death is FAILED.
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


def views(xml):
    """The window's labels {text: centre} and its text fields {hint: (text, focused, x, y)}."""
    nodes = [dict(re.findall(r'([\w-]+)="([^"]*)"', n)) for n in re.findall(r"<node ([^>]*)>", xml)]
    centre = lambda n: tuple((a + b) // 2 for a, b in zip(*[map(int, p) for p in re.findall(r"(\d+),(\d+)", n["bounds"])]))
    return ({n["text"].strip(): centre(n) for n in nodes if n.get("text", "").strip() and "bounds" in n},
            {n["hint"]: (n.get("text", ""), n.get("focused") == "true", *centre(n)) for n in nodes if n.get("class") == "android.widget.EditText" and n.get("hint")})


def labels():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    return views(adb("exec-out", "cat", "/sdcard/ui.xml"))


def screen():
    """(game state, LoginIndex, focused package, the labels of a window not the app's, the game's raw state, that window's text fields, the focused window's id)."""
    log = adb("logcat", "-d", "-s", "osrsrl-host:I")
    st = re.findall(r"GameStateChanged (\w+)(?: \(raw (-?\d+))?", log); ix = re.findall(r"LoginIndex (\d+)", log)
    focus = re.search(r"mCurrentFocus=Window\{(\S+) \S+ ([^/}\s]+)", adb("shell", "dumpsys", "window"))
    win, pkg = focus.groups() if focus else ("", "")
    lab, fields = ({}, {}) if pkg in (PKG, "") else labels()
    return st[-1][0] if st else "", int(ix[-1]) if ix else -1, pkg, lab, int(st[-1][1]) if st and st[-1][1] else None, fields, win


def form(lab, fields, name, posted):
    """Central's form: each field tapped until focused, the name typed into it, both read back holding the name, then Sign in;
    after the post the form leaves; a validation tooltip, or the form again with both fields empty (Central's 401), is FAILED naming it."""
    tip = next((t for t in lab if t.startswith("Please ")), None)   # Chrome's validation tooltip: the form did not post
    if tip:
        return ("fail", f"Central's form did not post: {tip}")
    if posted:   # the posted page stays drawn (its fields part cleared) until the redirect hands the app the code; Central's 401 is the same form, both fields empty
        empty = not any(fields.get(f, ("",))[0] for f in FORM[:2])
        return ("fail", f"Central answered its sign-in of {name} with its form again (401)") if empty else ("wait",)
    for f in FORM[:2]:
        if f not in fields:
            return ("fail", f"Central's form has no {f} field: {', '.join(lab)}")
        text, focused, x, y = fields[f]
        if text == name:
            continue
        if not focused:
            return ("tap", f"{f} field", x, y)
        if text and not name.startswith(text):
            return ("fail", f"Central's {f} field holds {text!r}, not {name}")
        return ("type", f)   # empty, or the typed name still landing
    return ("tap", FORM[2], *lab[FORM[2]])


def step(st, ix, pkg, lab, raw=None, name="", fields=None, posted=False, lost=False, win="", anr=None):
    """The action on one screen: ('done',), ('wait',), ('tap', name, x, y), ('type', field) or ('fail', why).
    lost: the game server logged this start's session lost (the app may sit in LOADING after it with no end);
    anr: {the system's "<app> isn't responding": the dialog window Wait was tapped on}, kept across screens by main."""
    if st == "LOGGED_IN":
        return ("done",)
    if lost:
        return ("fail", f"the game server lost {name}'s session while the app was {st}")
    if raw == START_ERROR:
        return ("fail", "the app's start error page 'Error connecting to server' (gameState 1000)")
    if pkg == "com.android.chrome":
        err = next((t for t in lab if re.search(r"ERR_[A-Z_]+", t)), None)
        if err:
            return ("fail", f"the browser's sign-in: {err}")
        if all(l in lab for l in FORM):
            return form(lab, fields or {}, name, posted)
        hit = next((l for l in LABELS if l in lab), None)
        return ("tap", hit, *lab[hit]) if hit else ("wait",)   # the issuer's page redirects back to the app by itself
    if pkg == LAUNCHER and st in ("", "UNKNOWN"):
        return ("wait",)   # the process runs before its window takes focus from the launcher; main() fails a death
    who = next((t for t in lab if t.endswith("isn't responding")), None) if "Wait" in lab else None
    if who:   # Wait again on the same dialog (a tap dropped while it draws); a new dialog of the same app after Wait: it hangs (run 301: Chrome's first run, 30 min)
        if (anr := {} if anr is None else anr).setdefault(who, win) != win:
            return ("fail", f"{who} again after Wait")
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


def lost(name, since):
    """The game server logged the account's session lost since `since` (UTC ISO): 'Game session lost: user='<name>''."""
    r = subprocess.run(["docker", "logs", "--since", since + "Z", "osrs-openrune"], capture_output=True, text=True)
    return f"Game session lost: user='{name}'" in r.stdout + r.stderr


def main(slug):
    name, posted, since = account(slug), False, None
    adb("logcat", "-c")
    r = adb("shell", "am", "start", "-W", "-n", PKG + "/com.jagex.android.MainActivity")   # am, not monkey: monkey aborts on another app's ANR before it launches; by component: the launcher filter has no DEFAULT category
    if "Status: ok" not in r and "Status: timeout" not in r:   # timeout: started, its first frame slower than -W waits
        return "FAILED: the app did not start: " + r.strip()
    acted, anr = None, {}   # -W returns once the activity is up: the process exists from here
    while True:
        st, ix, pkg, lab, raw, fields, win = screen()
        if not adb("shell", "pidof", PKG).strip():
            return "FAILED: the app died"
        since = since or (st == "LOGGING_IN" and datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))   # this start's login: an earlier session's loss is before it
        act = step(st, ix, pkg, lab, raw, name, fields, posted, bool(since) and st in ("LOGGING_IN", "LOADING") and lost(name, since), win, anr)
        if act[0] == "done":
            return "LOGGED_IN"
        if act[0] == "fail":
            return "FAILED: " + act[1]
        here = (st, ix, pkg, act[:2])
        # one act per screen, then the next screen is read: a second tap on one screen toggles panels, a second typing doubles the name;
        # a field's tap alone again while it is not focused (it only focuses it; Chrome drops a tap while its custom tab settles)
        if act[0] in ("tap", "type") and (here != acted or act[1].endswith(" field") or act[1] == "Wait"):
            print(f"Central's sign-in: {name}" if act == ("type", FORM[0]) else f"{st} LoginIndex {ix} {pkg}: {act[1]}", file=sys.stderr, flush=True)
            adb("shell", "input", *(("text", name) if act[0] == "type" else ("tap", str(act[2]), str(act[3])))); acted = here
            posted |= act[1:2] == (FORM[2],)
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
        (d / "login-failed.sockets.txt").write_text(adb("shell", "cat", "/proc/net/tcp", "/proc/net/tcp6"))   # where the app's connections stand (a stall's js5 on 10.0.2.2:443 = :01BB)
        # the game server's side of the same start (its login refusals and their reason, the sessions it holds): a later deploy loses it
        srv = subprocess.run(["docker", "logs", "-t", "--since", (datetime.datetime.fromisoformat(since) - datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "osrs-openrune"],
                             capture_output=True, text=True)
        (d / "login-failed.server.txt").write_text(srv.stdout + srv.stderr)
    print(r)
    sys.exit(0 if r == "LOGGED_IN" else 1)
