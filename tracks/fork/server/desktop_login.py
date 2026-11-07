#!/usr/bin/env python3
"""desktop_login.py <devtools port> [keep <server container>] <user> <password> | <devtools port> [keep <server container>] token | <devtools port> logout | <devtools port> guard <token>: logs a desktop
client in, by its login form or (token) by the token login its Jagex session variables start (prints LOGGED_IN or
FAILED: <reason>; LOGGED_IN only once the inventory widget shows container 93, FAILED when TICKS game ticks pass with no slot in it), or out through the logout tab's button (prints LOGIN_SCREEN) through its devtools endpoint; keep: logs it in again after each logout, until the desktop is gone. Keys, but
for the refused login's dialog that takes none: its Try again is clicked where the canvas width puts it. It acts only on the instance
that owns the port when it starts (DESKTOP_DIR/run/<port - 7779>/owner, its up's slug and claim): no call is sent once that
instance changes hands, and keep ends then. Each call carries that up's devtools token (its up.json), which the endpoint requires.
guard: writes the instance's guard file (DevtoolsOwner reads it on each request): the token, or empty (any caller) while a
session's desktop bridge predates mcp/serve.py; keep writes it again whenever that fact changes, so the guard turns on once none lives.
"""
import contextlib, fcntl, http.client, json, os, re, subprocess, sys, tempfile, threading, time, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))   # this checkout: its state/ is the one its hd writes

LOGOUT_BUTTON = 11927560  # component.logout:logout
INVENTORY_ITEMS = 9764864  # component.inventory:items, one dynamic child per slot of container 93
FRAMES = 10  # state reads after Enter: the client takes a key on its next frame, the rest a margin on a loaded host
CONNECT = 30  # seconds a connect may take: a starting client may not accept yet, and an unsent call is sent again
TRY_AGAIN_Y = 277  # canvas y of the refused login dialog's Try again button (read on a desktop in that state)
TICKS = 10  # game ticks a logged-in client waits for the inventory widget's slots: the server sends the interface and container 93 on the login tick


class Refused(Exception):
    """The endpoint answered with an error (an unknown key; get_client_state 'Cancelled' while the client starts)."""


class Cancelled(Refused):
    """The endpoint interrupted the call ('Cancelled': a caller's notifications/cancelled interrupts whichever call is active), or
    answered it unanswered past its bound (code -32002): it is there."""


def whole(f):  # f() again from its start while one of its calls is cancelled: a cancelled step may have half run (a type_chat half typed)
    while True:
        try:
            return f()
        except Cancelled:
            pass


class Gone(Exception):
    """The instance this process started on no longer owns the port (its down removed it; another up may claim it)."""


claim = None  # the owner file's text when the process started (main sets it): every call first checks it is unchanged


def owner(port):  # the text of the owner file of the instance on that devtools port, None when no up owns one
    try:
        with open(f"{os.environ.get('DESKTOP_DIR', '/mnt/c/osrs-test')}/run/{int(port) - 7779}/owner") as f:
            return f.read()
    except OSError:
        return None


def legacy():  # pids of the desktop bridges no mcp/serve.py runs: a session started before serve.py, whose bridge never reloads and sends no token
    ps = {f[0]: f for f in (l.split(None, 2) for l in subprocess.run(["ps", "-eo", "pid=,ppid=,args="], capture_output=True, text=True).stdout.splitlines()) if len(f) == 3}
    return [p for p, (_, pp, a) in ps.items() if re.search(r"devtools_bridge\.py \S+ http", a) and "mcp/serve.py" not in ps.get(pp, ("", "", ""))[2]]


def guard(port, tok):  # the instance's guard file: the up's token, or empty while a legacy bridge lives (its runs send no token); the legacy pids
    old = legacy(); want = "" if old else tok
    f = f"{os.environ.get('DESKTOP_DIR', '/mnt/c/osrs-test')}/run/{int(port) - 7779}/guard"
    try:
        with open(f) as g:
            have = g.read()
    except OSError:
        have = None
    if have != want and (claim is None or owner(port) == claim):
        with open(f + ".new", "w") as g:
            g.write(want)
        os.replace(f + ".new", f)
    return old


def guarding(port):  # keep's guard: written again on each change of the legacy bridges, until the instance changes hands
    while owner(port) == claim:
        t = devtoken(port)
        if t:  # an unread up.json never opens the guard
            guard(port, t)
        time.sleep(2)


def devtoken(port):  # the devtools token of the up owning the instance on that port (its state/<slug>/up.json): the endpoint answers no other caller
    try:
        with open(f"{os.environ.get('HD_ROOT', ROOT)}/state/{(owner(port) or '').split(' ')[0]}/up.json") as f:
            return json.load(f).get("token", "")
    except (OSError, ValueError):
        return ""


class Answered(http.client.HTTPConnection):
    """Only the connect is bounded: once sent, a call waits for its answer. The endpoint runs its up's calls one at a time
    (DevtoolsOwner), so a call may queue behind a run's walk_to; a call given up on would still run later (a replayed ENTER)."""
    def connect(s):
        super().connect(); s.sock.settimeout(None)


class AnsweredHandler(urllib.request.HTTPHandler):
    def http_open(s, req):
        return s.do_open(Answered, req)


urllib.request.install_opener(urllib.request.build_opener(AnsweredHandler))


def call(port, name, **args):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                 "params": {"name": name, "arguments": args}}).encode(), {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                                 "Authorization": f"Bearer {devtoken(port)}"})
    while True:
        if claim is not None and owner(port) != claim:
            raise Gone(f"the instance on {port} changed hands")
        try:
            with urllib.request.urlopen(req, timeout=CONNECT) as r:
                body = r.read().decode()
            break
        except urllib.error.URLError as e:  # urlopen wraps a failure to connect or send: the request never reached the client
            if name == "get_client_state" or not isinstance(e.reason, TimeoutError):
                raise
            wait(port, (), leave=True)  # the client is busy starting: resend once it answers a state read again
    line = next((l[5:] for l in body.splitlines() if l.startswith("data:")), body)
    msg = json.loads(line); out = msg.get("result", {})
    text = "".join(c.get("text", "") for c in out.get("content", []) if c.get("type") == "text") or json.dumps(out)
    if "error" in msg or out.get("isError"):  # a refused call (an unknown key) must not pass as done
        unanswered = (msg.get("error") or {}).get("code") == -32002   # the endpoint's bound passed (a call ahead held the desktop, or the plugin hung): it is there
        raise (Cancelled if text == "Cancelled" or unanswered else Refused)(f"{name}: {msg.get('error') or text}")
    return text


def state(port):
    try:
        s = call(port, "get_client_state")
    except Refused:
        return {}  # no state yet (the client is starting, its thread busy): the next read has one
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            return {}
        raise
    try:
        s = json.loads(s)
    except ValueError:
        return {"gameState": s}
    return s


def wait(port, states, poll=2, leave=False):
    """Blocks until the game state is one of states (leave: is none of them); the client reports a state on every read,
    so nothing is timed."""
    while (g := (s := state(port)).get("gameState")) is None or (g in states) == leave:
        time.sleep(poll)
    return s


def clear(port):  # press_key takes one key per call
    for _ in range(24):
        call(port, "press_key", key="BACKSPACE")


def try_again(port):  # the refused login's dialog ('Incorrect username or password': Try again / Forgotten password?) takes no key, only a click
    # on Try again, the login box's top button; the login screen is drawn 765 wide, centred on the canvas, from its top
    call(port, "click", x=state(port)["canvasWidth"] // 2, y=TRY_AGAIN_Y)


def attempt(port, leave=(lambda port: call(port, "press_key", key="ESCAPE"), try_again)):
    """Presses Enter and returns the attempt's end state: LOGGED_IN or LOGIN_SCREEN, or None when the key started no attempt.
    The client takes a key on its next frame and a submit leaves LOGIN_SCREEN on that frame, and each state read runs on a
    frame, so FRAMES reads still on LOGIN_SCREEN are a page Enter does not submit (a refusal's response page): each of leave
    in turn (Escape, then Try again) is tried on it, and Enter is pressed on the page under it."""
    call(port, "press_key", key="ENTER")
    for _ in range(FRAMES):
        if state(port).get("gameState") != "LOGIN_SCREEN":
            return wait(port, ("LOGGED_IN", "LOGIN_SCREEN"))["gameState"]
    if not leave:
        return None
    leave[0](port)
    state(port), state(port)  # each read runs on a client frame: the page has changed before Enter
    return attempt(port, leave[1:])


def login(port, user, password):
    s = wait(port, ("LOGIN_SCREEN", "LOGGED_IN"))
    if s["gameState"] == "LOGGED_IN":
        return inventory(port)
    call(port, "press_key", key="ESCAPE")  # any login screen page back to the welcome page
    state(port), state(port)  # each read runs on a client frame: the page has changed before the next key (one frame took both)
    call(port, "press_key", key="ENTER")   # Existing User: the form, its login field focused
    clear(port)
    call(port, "type_chat", text=user, send=False)
    call(port, "press_key", key="TAB")
    clear(port)
    call(port, "type_chat", text=password, send=False)
    return result(port, attempt(port, leave=()), "the server refused the login")


def token(port):
    s = wait(port, ("LOGIN_SCREEN", "LOGGED_IN"))
    if s["gameState"] == "LOGGED_IN":
        return inventory(port)
    return result(port, attempt(port), "the server refused the token")   # the session's login page: Enter plays; the client fetches its token from param 11


def result(port, g, refused):
    if g is None:
        return "FAILED: Enter started no login: the login screen is on a page Enter does not submit and neither Escape nor Try again leaves (the disconnected dialog)"
    return inventory(port) if g == "LOGGED_IN" else f"FAILED: back at the login screen: {refused}"


def inventory(port):
    """LOGGED_IN when the inventory widget's slots show container 93's items, else FAILED naming both (an empty widget over
    a full container leaves every item_action unfound); waits until the logged-in client has built the widget's slots, and
    FAILED once TICKS game ticks pass without them (the server sent no inventory)."""
    base = first = None
    while True:
        try:
            slots = json.loads(call(port, "get_widget", componentId=INVENTORY_ITEMS)).get("dynamicChildren") or []
        except Refused:  # not built yet: the interface opens after LOGGED_IN
            slots = []
        if slots:
            break
        if (t := tick(port)) is not None:
            base = t if base is None else base   # the newest event may be from an earlier login (the tick goes on across logins): count from the first one after it
            first = t if first is None and t != base else first
            if first is not None and t - first >= TICKS:
                return f"FAILED: {TICKS} game ticks after LOGGED_IN the inventory widget has no slots: the server sent no inventory (container 93)"
        time.sleep(1)
    shown = {c["childIndex"]: (c["itemId"], c["itemQuantity"]) for c in slots if not c.get("selfHidden") and c.get("itemId", -1) > 0}
    try:
        held = {i["slot"]: (i["itemId"], i["quantity"]) for i in json.loads(call(port, "get_inventory", inventoryId=93))["items"]}
    except Refused:  # no container 93: the server sent no inventory, an empty one
        held = {}
    return "LOGGED_IN" if shown == held else f"FAILED: the inventory widget shows {shown} but container 93 holds {held}"


def state_line(port):
    """(0, the client's state) or (1, FAILED: why) when the endpoint or its client thread is gone (a crash, a probe
    that stopped the client); a busy client (Cancelled) is there."""
    try:
        return 0, call(port, "get_client_state")
    except Cancelled as e:
        return 0, str(e)
    except (OSError, Refused, Gone) as e:
        return 1, f"FAILED: devtools endpoint on {port}: {e}"


def tick(port):  # the game tick of the newest recorded event (a logged-in client's interfaces fire scripts every frame), None before any
    events = json.loads(call(port, "get_timeline", channels=["script", "var", "chat", "container"], limit=1)).get("events") or []
    return events[-1]["tick"] if events else None


def logout(port):
    call(port, "invoke_menu_action", param0=-1, param1=LOGOUT_BUTTON, type="CC_OP", identifier=1, option="Logout")
    return wait(port, ("LOGIN_SCREEN",))["gameState"]


def keep(port, act, ready):
    """A run's desktop that is logged out (a disconnect, a server restart, any logout) is logged in again by act: it waits
    for LOGGED_IN, then for LOGIN_SCREEN, then logs in. A failed login is tried again once the server is ready after it
    (ready(since): a server that was down or restarting), and never while the same server refuses it; a login made by
    another waits for the next logout. A failed login that left the client logged in (no inventory) is logged out first:
    it is tried again at once, the second time like any failure. A cancelled call starts the login again (whole): the endpoint
    answered. Ends when the endpoint is gone (the desktop stopped)."""
    while True:
        wait(port, ("LOGGED_IN",)); wait(port, ("LOGIN_SCREEN",))
        again = True
        while True:
            since = time.time()
            with locked(port):
                r = whole(act)
                out = r != "LOGGED_IN" and state(port).get("gameState") == "LOGGED_IN" and whole(lambda: logout(port))
            print(r, flush=True)
            if out:
                print(f"keep: logged in without the inventory, logged out ({out}): {'logs in again' if again else 'waits for the server to be ready again'}", flush=True)
                if again:
                    again = False
                    continue
            while r != "LOGGED_IN" and not ready(since) and state(port).get("gameState") != "LOGGED_IN":
                time.sleep(2)
            if r == "LOGGED_IN" or not ready(since):
                break


def server_ready(container):  # ready(since): the container logged "Server ready in" at or after since
    def ready(since):
        t = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(since))
        out = subprocess.run(["docker", "logs", "--since", t, container], capture_output=True, text=True)
        return "Server ready in" in out.stdout + out.stderr
    return ready


@contextlib.contextmanager
def locked(port):  # one action at a time on a desktop: up, restart and keep each log it in
    with open(f"{tempfile.gettempdir()}/desktop-login-{port}.lock", "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX); yield


if __name__ == "__main__":
    port, a = sys.argv[1], sys.argv[2:]
    claim = owner(port)
    if claim is None:
        print(f"FAILED: no desktop instance owns port {port}"); sys.exit(1)
    if a[0] == "guard":
        old = guard(port, a[1])
        if old:
            print(f"desktop on {port} answers any caller while the desktop bridges {' '.join(old)} predate mcp/serve.py and send no token")
        sys.exit(0)
    if a[0] == "state":
        rc, text = state_line(port); print(text); sys.exit(rc)
    k = a[0] == "keep"; c, a = (a[1], a[2:]) if k else (None, a)
    act = (lambda: logout(port)) if a[0] == "logout" else (lambda: token(port)) if a[0] == "token" else (lambda: login(port, a[0], a[1]))
    if k:
        threading.Thread(target=guarding, args=(port,), daemon=True).start()
        try:
            keep(port, act, server_ready(c))
        except (OSError, Refused, Gone) as e:
            print(f"keep: devtools endpoint on {port} gone: {e}")
        sys.exit(0)
    try:
        with locked(port):
            r = whole(act)
    except (OSError, Refused, Gone) as e:
        r = f"FAILED: devtools endpoint on {port}: {e}"
    print(r)
    sys.exit(0 if r in ("LOGGED_IN", "LOGIN_SCREEN") else 1)
