"""javcheck.py <jav_config url> [world host]: fails (exit 1) when the served jav_config names any host but this machine's.
Privacy rule: no client ever contacts Jagex, RuneScape or Google. Run by track.sh up and by the client's network QA."""
import re, sys, urllib.request

LOCAL = {"127.0.0.1", "localhost", "10.0.2.2"}
URL_HOST = re.compile(r"[a-z][a-z0-9+.-]*://([^/:\"\s\]]+)", re.I)
NAMED = re.compile(r"[a-z0-9.-]*(?:jagex|runescape|google[a-z]*)\.[a-z]{2,}", re.I)  # a bare host such as param 19's client id


def foreign(body, local=LOCAL):
    return sorted({h for h in URL_HOST.findall(body) if h.lower() not in local} | set(NAMED.findall(body)))


if __name__ == "__main__":
    body = urllib.request.urlopen(sys.argv[1], timeout=10).read().decode("utf-8", "replace")
    bad = foreign(body, LOCAL | set(sys.argv[2:]))
    print("non-local hosts: " + " ".join(bad) if bad else "jav_config local only")
    sys.exit(1 if bad else 0)
