#!/usr/bin/env python3
"""Verify a "done / fixed / deployed" claim on the AUTHORITATIVE surface.

A merged PR, a green CI run, or a local tree is a PROXY for delivery; the
surface a reviewer actually opens can be silently stale (a broken auto-sync
leaves a preview hours behind HEAD), and a local `main` can be thousands of
commits behind the real base. This script checks the claim where it counts.

WHAT IT PROVES — AND WHAT IT DOES NOT. A PASS proves that the surface serves
(or the remote branch contains) the claimed build. It does NOT prove the
feature works, renders, or is correct: pair it with the functional check.

Modes (stdlib only, no third-party dependency):

  served --url U --expect-sha S --probe SPEC [--probe SPEC ...]
      Fetch the running app and extract the build/commit id the SERVING
      PROCESS reports. SPEC is one of:
        header:NAME              a response header of U (case-insensitive)
        meta:NAME                <meta name|property="NAME" content="..."> in U
        path:/version.json:key   JSON at that same-origin path; key is dotted
                                 (e.g. build.sha)
      PASS only when at least one probe yields an id and every yielded id
      matches S (the shorter of the two, at least 7 hex chars, is a prefix of
      the longer). A value that is not a commit sha — a data timestamp, a
      semver, a JSON number — is NOT a build id: a payload's "data as of"
      stamp dates the artifact, not the running code. Redirects are NOT
      followed (a redirect means U is not the surface that serves the build;
      re-run with the Location URL if that is the real surface). --timeout
      bounds each socket read and, as a wall-clock cap, the body read.

  ref --repo DIR --branch B --expect-sha S [--remote origin] [--timeout 120]
      Fetch B from the remote the reviewer uses, then PASS only when S is an
      ancestor of (reachable from) that fetched remote head. A local branch or
      a stale local tree is never consulted. Fetch writes the remote-tracking
      ref refs/remotes/<remote>/<B>, exactly as a plain `git fetch` would.
      Git runs with GIT_TERMINAL_PROMPT=0 and no terminal; a call past
      --timeout seconds is killed and reported as COULD_NOT_CHECK.

  --json  print one JSON object (verdict, observed id, surface, reason, UTC
          observation time) for a board post or a handback `Verify:` line.

Leakage: a rejected build-id value is reported by type and length only, and
every printed URL (the surface, a redirect Location, a URL remote) drops its
userinfo, query, and fragment. A --url carrying userinfo is refused.

Exit codes: 0 PASS; 1 FAIL (the surface serves / the branch holds something
else); 2 COULD_NOT_CHECK (no build id, non-200, redirect, network or git
error, a timeout, a shallow clone, an ambiguous or too-short sha, or bad
usage). Exit 2 is never a pass: an unverifiable claim stays unverified.

Side effects: `served` performs HTTP GETs (proxy env vars are honoured);
`ref` runs `git fetch` against the named remote. Nothing else is written.
"""
import argparse
import contextlib
import datetime
import io
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

PASS, FAIL, COULD_NOT_CHECK = 0, 1, 2
VERDICT = {PASS: "PASS", FAIL: "FAIL", COULD_NOT_CHECK: "COULD_NOT_CHECK"}
MIN_SHA = 7
MAX_BODY = 2 * 1024 * 1024
DEFAULT_GIT_TIMEOUT = 120.0  # seconds per git call in `ref` mode
HEX_RE = re.compile(r"^[0-9a-f]+$")
PROVES = "the surface serves this build; not that the feature works"
PROVES_REF = "the remote branch contains this commit; not that it is deployed or works"
# Tests swap this for {} so a local fixture never routes through a proxy.
_PROXIES = None


class CheckError(Exception):
    """A condition that makes the claim uncheckable (always exit 2)."""


def _sha(value, what):
    """Normalise a claimed sha: hex only, at least MIN_SHA chars, else refuse."""
    s = (value or "").strip().lower()
    if not HEX_RE.match(s):
        raise CheckError(f"{what} {value!r} is not a hex commit sha")
    if len(s) < MIN_SHA:
        raise CheckError(f"{what} {value!r} is shorter than {MIN_SHA} chars; too ambiguous to compare")
    return s


def _matches(expected, observed):
    """True iff the shorter sha (both already >= MIN_SHA) prefixes the longer."""
    n = min(len(expected), len(observed))
    return expected[:n] == observed[:n]


# --------------------------------------------------------------------------
# served
# --------------------------------------------------------------------------
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # urllib then raises HTTPError with the 3xx code


class _MetaParser(HTMLParser):
    def __init__(self, name):
        super().__init__()
        self.name = name.lower()
        self.found = None

    def handle_starttag(self, tag, attrs):
        if tag != "meta" or self.found is not None:
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        if (a.get("name") or a.get("property") or "").lower() == self.name:
            self.found = a.get("content", "")


def redact_url(url):
    """Return `url` safe to print: userinfo, query, and fragment dropped, control chars removed.

    A surface URL or a peer's redirect target can carry a password or a token
    (`https://user:pw@host/p?token=...`); only scheme, host, port, and path are
    kept. Non-URL text is returned with control characters stripped. Pure.
    """
    text = "".join(ch for ch in str(url) if ch.isprintable())[:300]
    try:
        parts = urllib.parse.urlsplit(text)
        host = parts.hostname or ""
        port = f":{parts.port}" if parts.port else ""
    except ValueError:
        return "<unparseable URL>"
    if not parts.scheme or not parts.netloc:
        return text.split("?", 1)[0].split("#", 1)[0]
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    return urllib.parse.urlunsplit((parts.scheme, host + port, parts.path, "", ""))


def _describe(raw):
    """Type and length of a value that is not a build id — never the value (it may be a secret). Pure."""
    return f"{type(raw).__name__} of length {len(str(raw))}"


def _fetch(url, timeout):
    """GET url without following redirects; return (headers, body text).

    `timeout` bounds each socket operation AND the whole body read (wall-clock),
    so a server that trickles bytes cannot hold the check open.
    """
    handlers = [_NoRedirect()]
    if _PROXIES is not None:
        handlers.append(urllib.request.ProxyHandler(_PROXIES))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": "surface_check/1"})
    shown = redact_url(url)
    try:
        with opener.open(req, timeout=timeout) as resp:
            status = resp.status
            headers = resp.headers
            deadline = time.monotonic() + timeout
            chunks, size = [], 0
            while size < MAX_BODY:
                if time.monotonic() > deadline:
                    raise CheckError(f"{shown} body not read within the {timeout:g}s wall-clock cap")
                chunk = resp.read1(min(65536, MAX_BODY - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            body = b"".join(chunks).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            loc = redact_url(exc.headers.get("Location", "?"))
            raise CheckError(f"{shown} redirected ({exc.code}) to {loc}; not followed — "
                             "re-run with that URL if it is the surface the reviewer opens")
        raise CheckError(f"{shown} returned HTTP {exc.code}, not 200")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        detail = exc.reason if isinstance(exc, urllib.error.URLError) else exc
        raise CheckError(f"{shown} could not be fetched: {str(detail).replace(url, shown)[:200]}")
    if status != 200:
        raise CheckError(f"{shown} returned HTTP {status}, not 200")
    return headers, body


def _parse_probe(spec):
    kind, sep, rest = spec.partition(":")
    if not sep or not rest or kind not in ("header", "meta", "path"):
        raise CheckError(f"bad --probe {spec!r} (want header:NAME, meta:NAME, or path:/p.json:key)")
    if kind == "path":
        path, sep, key = rest.rpartition(":")
        if not sep or not path.startswith("/") or path.startswith("//") or not key:
            raise CheckError(f"bad --probe {spec!r} (path form is path:/same-origin/path:dotted.key)")
        return kind, (path, key)
    return kind, rest


def _json_key(doc, key):
    cur = doc
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _as_build_id(raw):
    """Return (sha, None) for a usable build id, else (None, why-not).

    A rejected value is described by type and length only, never echoed: a
    header or JSON key named like a build id can hold a token or a secret.
    """
    if raw is None or raw == "":
        return None, "absent"
    if not isinstance(raw, str):
        return None, f"{_describe(raw)} is not a commit sha (a timestamp/number is not a build id)"
    v = raw.strip().lower()
    if not HEX_RE.match(v):
        return None, f"{_describe(raw)} is not a commit sha (a data timestamp or version is not a build id)"
    if len(v) < MIN_SHA:
        return None, f"{_describe(raw)} is shorter than {MIN_SHA} hex chars; too ambiguous"
    return v, None


def check_served(url, expect, probes, timeout):
    """Return (code, observed, reason) for the served-build check."""
    expected = _sha(expect, "--expect-sha")
    try:
        parts = urllib.parse.urlsplit(url)
        userinfo = parts.username is not None or parts.password is not None
    except ValueError:
        raise CheckError("--url is not a parseable URL")
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise CheckError(f"--url scheme {scheme or '(none)'!r} unsupported; want http or https")
    if userinfo:
        # urllib would resolve "user:pw@host" as a hostname, leaking it to DNS.
        raise CheckError("--url carries userinfo credentials, which are not sent and would leak "
                         "(argv is visible to local users); give the bare URL")
    if not probes:
        raise CheckError("at least one --probe is required; the build id must come from a named signal")
    parsed = [(spec, *_parse_probe(spec)) for spec in probes]
    page = None
    if any(kind in ("header", "meta") for _, kind, _ in parsed):
        page = _fetch(url, timeout)
    found, missing = [], []
    for spec, kind, arg in parsed:
        if kind == "header":
            raw = page[0].get(arg)
        elif kind == "meta":
            mp = _MetaParser(arg)
            mp.feed(page[1])
            raw = mp.found
        else:
            path, key = arg
            _, body = _fetch(urllib.parse.urljoin(url, path), timeout)
            try:
                raw = _json_key(json.loads(body), key)
            except ValueError:
                raise CheckError(f"{path} is not JSON")
        sha, why = _as_build_id(raw)
        if sha is None:
            missing.append(f"{spec}: {why}")
        else:
            found.append((spec, sha))
    if not found:
        return COULD_NOT_CHECK, None, "no build id reported (" + "; ".join(missing) + ")"
    bad = [(s, v) for s, v in found if not _matches(expected, v)]
    observed = found[0][1]
    if bad:
        detail = ", ".join(f"{s}={v}" for s, v in bad)
        return FAIL, bad[0][1], f"surface serves {detail}, not {expected} (stale or wrong build)"
    via = ", ".join(s for s, _ in found)
    note = f"; unreported: {'; '.join(missing)}" if missing else ""
    return PASS, observed, f"served build {observed} matches {expected} via {via}{note}"


# --------------------------------------------------------------------------
# ref
# --------------------------------------------------------------------------
def _git(repo, *args, timeout=DEFAULT_GIT_TIMEOUT):
    """Run one git command non-interactively; a hang past `timeout` s raises CheckError.

    GIT_TERMINAL_PROMPT=0, a closed stdin, and a new session (no controlling
    terminal) stop git and its ssh child from waiting on a credential prompt;
    on timeout the whole process group is killed so a grandchild holding the
    pipes cannot keep the check open.
    """
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = subprocess.Popen(["git", "-C", repo, *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
    except OSError as exc:
        raise CheckError(f"git could not be started: {exc}")
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            if hasattr(os, "killpg"):
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        proc.communicate()
        raise CheckError(f"git {args[0]} timed out after {timeout:g}s (a hung remote or credential prompt)")
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def check_ref(repo, remote, branch, expect, timeout=DEFAULT_GIT_TIMEOUT):
    """Return (code, observed-remote-head, reason) for the reachability check.

    Every git call is bounded by `timeout` seconds; a timeout raises CheckError (exit 2).
    """
    git = lambda *a: _git(repo, *a, timeout=timeout)  # noqa: E731  (one bound runner for this check)
    expected = _sha(expect, "--expect-sha")
    shown = redact_url(remote)  # a URL remote can carry credentials
    if remote.startswith("-") or not remote:
        raise CheckError(f"bad --remote {shown!r}")
    if branch.startswith("-") or git("check-ref-format", "--branch", branch).returncode != 0:
        raise CheckError(f"bad --branch {branch!r}")
    if git("rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise CheckError("shallow clone: ancestry is incomplete, reachability cannot be decided")
    tracking = f"refs/remotes/{remote}/{branch}"
    fetch = git("fetch", "--quiet", "--no-tags", remote, f"+refs/heads/{branch}:{tracking}")
    if fetch.returncode != 0:
        raise CheckError(f"git fetch {shown} {branch} failed: {fetch.stderr.replace(remote, shown).strip()[:300]}")
    head = git("rev-parse", "--verify", "--quiet", tracking + "^{commit}").stdout.strip()
    if not head:
        raise CheckError(f"{tracking} did not resolve after fetch")
    res = git("rev-parse", "--verify", "--quiet", expected + "^{commit}")
    if res.returncode != 0:
        # After a full fetch every ancestor of the remote head is local, so an
        # unknown object is not on the branch; an ambiguous prefix is refused.
        amb = git("rev-parse", "--disambiguate=" + expected).stdout.split()
        if len(amb) > 1:
            raise CheckError(f"--expect-sha {expected} is ambiguous in {repo}; give more chars")
        return FAIL, head, f"{expected} is not in {repo} after fetching {shown}/{branch} (head {head[:12]})"
    full = res.stdout.strip()
    anc = git("merge-base", "--is-ancestor", full, head)
    if anc.returncode == 0:
        return PASS, head, f"{full[:12]} is reachable from {shown}/{branch} (head {head[:12]})"
    if anc.returncode == 1:
        return FAIL, head, f"{full[:12]} is NOT reachable from {shown}/{branch} (head {head[:12]})"
    raise CheckError(f"git merge-base failed: {anc.stderr.strip()[:300]}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="print one JSON object instead of text")
    p = argparse.ArgumentParser(prog="surface_check.py", parents=[common],
                                description="Verify a done/deployed claim on the authoritative surface.")
    p.add_argument("--selftest", action="store_true", help="run offline self-tests")
    sub = p.add_subparsers(dest="mode")
    s = sub.add_parser("served", parents=[common], help="check the build id a running app serves")
    s.add_argument("--url", required=True)
    s.add_argument("--expect-sha", required=True)
    s.add_argument("--probe", action="append", default=[],
                   help="header:NAME | meta:NAME | path:/version.json:key (repeatable)")
    s.add_argument("--timeout", type=float, default=10.0)
    r = sub.add_parser("ref", parents=[common], help="check a sha is reachable from a remote branch")
    r.add_argument("--repo", default=".")
    r.add_argument("--remote", default="origin")
    r.add_argument("--branch", required=True)
    r.add_argument("--expect-sha", required=True)
    r.add_argument("--timeout", type=float, default=DEFAULT_GIT_TIMEOUT, help="seconds per git call")
    return p


def main(argv=None):
    """CLI entry point; returns the exit code (0 PASS, 1 FAIL, 2 COULD_NOT_CHECK)."""
    args = _parser().parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.mode:
        _parser().print_usage(sys.stderr)
        return COULD_NOT_CHECK
    # Printed and JSON surfaces never carry userinfo, a query, or a fragment (tokens live there).
    surface = (redact_url(args.url) if args.mode == "served"
               else f"{redact_url(args.remote)}/{args.branch} in {args.repo}")
    proves = PROVES if args.mode == "served" else PROVES_REF
    try:
        if args.mode == "served":
            code, observed, reason = check_served(args.url, args.expect_sha, args.probe, args.timeout)
        else:
            code, observed, reason = check_ref(args.repo, args.remote, args.branch, args.expect_sha, args.timeout)
    except CheckError as exc:
        code, observed, reason = COULD_NOT_CHECK, None, str(exc)
    if getattr(args, "json", False):
        print(json.dumps({
            "mode": args.mode, "verdict": VERDICT[code], "exit": code, "surface": surface,
            "expect_sha": args.expect_sha, "observed": observed, "reason": reason,
            "checked_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "proves": proves,
        }, sort_keys=True))
    else:
        print(f"surface_check {args.mode}: {VERDICT[code]} — {reason}")
        print(f"  surface: {surface}; proves: {proves}")
    return code


# --------------------------------------------------------------------------
# --selftest — offline: a local http.server fixture on 127.0.0.1 and throwaway
# git repos (a bare "remote" plus a clone) in a temp dir. Every negative case
# proves the check FIRES (never a silent pass).
# --------------------------------------------------------------------------
def _selftest():
    import http.server
    import shutil
    import tempfile
    import threading

    global _PROXIES
    _PROXIES = {}
    good = "0123456789abcdef0123456789abcdef01234567"
    stale = "fedcba9876543210fedcba9876543210fedcba98"
    routes = {
        "/hdr": (200, {"X-Build-Sha": good}, ""),
        "/hdr-stale": (200, {"X-Build-Sha": stale}, ""),
        "/hdr-short": (200, {"X-Build-Sha": "0123"}, ""),
        "/hdr-ts": (200, {"X-Build-Sha": "2026-09-23T10:00:00Z"}, ""),
        "/none": (200, {}, '<html><script>{"data_as_of":"2026-09-23T10:00:00Z"}</script></html>'),
        "/meta": (200, {}, f'<html><head><meta name="build-sha" content="{good}"></head></html>'),
        "/mixed": (200, {"X-Build-Sha": good}, f'<meta name="build-sha" content="{stale}">'),
        "/version.json": (200, {}, json.dumps({"build": {"sha": good[:12]},
                                               "data_as_of": "2026-09-23T10:00:00Z", "ts": 1790000000})),
        "/notjson.json": (200, {}, "<html>nope</html>"),
        "/redir": (302, {"Location": "/hdr"}, ""),
        "/boom": (500, {"X-Build-Sha": good}, ""),
        "/proxied": (203, {"X-Build-Sha": good}, ""),
        "/hdr-secret": (200, {"X-Build-Sha": "Bearer s3cr3t-t0ken-value"}, ""),
        "/redir-cred": (302, {"Location": "https://jane:hunter2@evil.example/next?token=abc#frag"}, ""),
    }

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/drip":  # a body that trickles in under the per-read timeout forever
                self.send_response(200)
                self.send_header("Content-Length", "100000")
                self.end_headers()
                with contextlib.suppress(OSError):
                    for _ in range(200):
                        self.wfile.write(b"<")
                        self.wfile.flush()
                        time.sleep(0.1)
                return
            code, hdrs, body = routes.get(path, (404, {}, "missing"))
            data = body.encode()
            self.send_response(code)
            for k, v in hdrs.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    passed = failed = 0

    def run(argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(argv)
        return rc, buf.getvalue()

    def case(name, argv, want, must=None):
        nonlocal passed, failed
        rc, out = run(argv)
        ok = rc == want and (must is None or must in out)
        passed += ok
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} (rc={rc}, want {want})" + ("" if ok else f"\n      {out.strip()}"))

    def served(path, sha, *probes):
        argv = ["served", "--url", base + path, "--expect-sha", sha, "--timeout", "5"]
        for pr in probes:
            argv += ["--probe", pr]
        return argv

    H_ = "header:x-build-sha"
    case("served: header full sha matches", served("/hdr", good, H_), PASS)
    case("served: 7-char expected prefix matches", served("/hdr", good[:7], H_), PASS)
    case("served: stale build id FIRES", served("/hdr-stale", good, H_), FAIL, "stale or wrong build")
    case("served: missing id -> could not check", served("/none", good, H_), COULD_NOT_CHECK, "no build id")
    case("served: payload timestamp is not a build id", served("/hdr-ts", good, H_), COULD_NOT_CHECK,
         "not a commit sha")
    case("served: served id too short refused", served("/hdr-short", good, H_), COULD_NOT_CHECK)
    case("served: meta tag matches", served("/meta", good, "meta:build-sha"), PASS)
    case("served: meta absent (only a data stamp) refused", served("/none", good, "meta:build-sha"),
         COULD_NOT_CHECK)
    case("served: version.json dotted key (short served id) matches",
         served("/", good, "path:/version.json:build.sha"), PASS)
    case("served: version.json data_as_of stamp refused",
         served("/", good, "path:/version.json:data_as_of"), COULD_NOT_CHECK, "not a build id")
    case("served: version.json numeric ts refused", served("/", good, "path:/version.json:ts"),
         COULD_NOT_CHECK)
    case("served: non-JSON version path refused", served("/", good, "path:/notjson.json:sha"),
         COULD_NOT_CHECK, "not JSON")
    case("served: probes disagree FIRES", served("/mixed", good, H_, "meta:build-sha"), FAIL)
    case("served: redirect not followed", served("/redir", good, H_), COULD_NOT_CHECK, "redirected (302)")
    case("served: HTTP 500 refused even with a matching header", served("/boom", good, H_),
         COULD_NOT_CHECK, "HTTP 500")
    case("served: HTTP 404 refused", served("/gone", good, H_), COULD_NOT_CHECK, "HTTP 404")
    case("served: non-200 2xx (203) refused", served("/proxied", good, H_), COULD_NOT_CHECK, "HTTP 203")
    case("served: expected sha < 7 chars refused", served("/hdr", good[:6], H_), COULD_NOT_CHECK,
         "shorter than 7")
    case("served: non-hex expected sha refused", served("/hdr", "v1.2.3-abc", H_), COULD_NOT_CHECK)
    case("served: no probe refused", served("/hdr", good), COULD_NOT_CHECK, "at least one --probe")
    case("served: bad probe spec refused", served("/hdr", good, "cookie:x"), COULD_NOT_CHECK, "bad --probe")
    case("served: non-http scheme refused",
         ["served", "--url", "file:///etc/hosts", "--expect-sha", good, "--probe", H_], COULD_NOT_CHECK)
    rc, out = run(["served", "--json", "--url", base + "/hdr-stale", "--expect-sha", good, "--probe", H_])
    try:
        doc = json.loads(out)
        ok = (rc == FAIL and doc["verdict"] == "FAIL" and doc["observed"] == stale
              and doc["proves"] == PROVES and doc["checked_at"].endswith("Z"))
    except (ValueError, KeyError):
        ok = False
    passed += ok
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  served --json: machine verdict carries observed id + proves")

    def no_leak(name, argv, want, secrets, must):
        nonlocal passed, failed
        rc, out = run(argv)
        ok = rc == want and must in out and not any(s in out for s in secrets)
        passed += ok
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} (rc={rc}, want {want})" + ("" if ok else f"\n      {out.strip()}"))

    no_leak("served: non-sha value reported as type+length, never echoed", served("/hdr-secret", good, H_),
            COULD_NOT_CHECK, ("s3cr3t", "Bearer"), "str of length 25")
    no_leak("served: redirect Location stripped of userinfo/query/fragment", served("/redir-cred", good, H_),
            COULD_NOT_CHECK, ("hunter2", "jane", "token=abc", "frag"), "https://evil.example/next")
    no_leak("served: surface drops query in text output", served("/hdr?token=abc", good, H_), PASS,
            ("token=abc",), f"surface: {base}/hdr;")
    cred = base.replace("http://", "http://jane:hunter2@") + "/hdr?token=abc"
    no_leak("served --json: userinfo URL refused; surface and reason drop userinfo and query",
            ["served", "--json", "--url", cred, "--expect-sha", good, "--probe", H_, "--timeout", "5"],
            COULD_NOT_CHECK, ("hunter2", "jane", "token=abc"), f'"surface": "{base}/hdr"')
    t0 = time.monotonic()
    rc, out = run(["served", "--url", base + "/drip", "--expect-sha", good, "--probe", "meta:build-sha",
                   "--timeout", "1"])
    ok = rc == COULD_NOT_CHECK and "wall-clock" in out and time.monotonic() - t0 < 10
    passed += ok
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  served: trickling body hits the wall-clock cap (rc={rc})"
          + ("" if ok else f"\n      {out.strip()}"))
    srv.shutdown()

    tmp = tempfile.mkdtemp(prefix="surface-check-selftest-")
    env_keys = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_SSH_COMMAND")
    saved = {k: os.environ.get(k) for k in env_keys}
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                      GIT_AUTHOR_NAME="Jane Smith", GIT_AUTHOR_EMAIL="jane@example.com",
                      GIT_COMMITTER_NAME="Jane Smith", GIT_COMMITTER_EMAIL="jane@example.com")
    try:
        remote = os.path.join(tmp, "remote.git")
        work = os.path.join(tmp, "work")
        g = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
        g("init", "--quiet", "--bare", remote)
        g("init", "--quiet", work)
        g("-C", work, "commit", "--quiet", "--allow-empty", "-m", "a")
        g("-C", work, "remote", "add", "origin", remote)
        g("-C", work, "push", "--quiet", "origin", "HEAD:refs/heads/main")
        pushed = g("-C", work, "rev-parse", "HEAD")
        g("-C", work, "commit", "--quiet", "--allow-empty", "-m", "b")
        local_only = g("-C", work, "rev-parse", "HEAD")

        def ref(sha, branch="main"):
            return ["ref", "--repo", work, f"--branch={branch}", "--expect-sha", sha]

        case("ref: pushed sha reachable", ref(pushed), PASS)
        case("ref: pushed 7-char prefix reachable", ref(pushed[:7]), PASS)
        case("ref: local-only commit FIRES (merged locally, not on remote)", ref(local_only), FAIL,
             "NOT reachable")
        case("ref: unknown sha FIRES", ref(stale), FAIL, "is not in")
        case("ref: sha < 7 chars refused", ref(pushed[:6]), COULD_NOT_CHECK, "shorter than 7")
        case("ref: missing remote branch refused", ref(pushed, "nope"), COULD_NOT_CHECK, "git fetch")
        case("ref: option-like branch refused", ref(pushed, "--upload-pack=x"), COULD_NOT_CHECK, "bad --branch")

        # Two blobs whose ids share a 7-hex prefix (found by a birthday search
        # over this content template): a 7-char --expect-sha naming either is
        # ambiguous and must be refused, never read as "not on the branch".
        blob = lambda i: subprocess.run(["git", "-C", work, "hash-object", "-w", "--stdin"], check=True,
                                        input=f"surface-check ambiguity fixture {i}\n", capture_output=True,
                                        text=True).stdout.strip()
        b1, b2 = blob(1365), blob(3820)
        if b1[:MIN_SHA] == b2[:MIN_SHA]:
            case("ref: ambiguous 7-char sha refused", ref(b1[:MIN_SHA]), COULD_NOT_CHECK, "ambiguous")
        else:
            failed += 1
            print(f"FAIL  ref: ambiguity fixture no longer collides ({b1[:MIN_SHA]} vs {b2[:MIN_SHA]})")

        g("-C", work, "push", "--quiet", "origin", "HEAD:refs/heads/dev")
        shallow = os.path.join(tmp, "shallow")
        g("clone", "--quiet", "--depth", "1", "--branch", "dev", "file://" + remote, shallow)
        case("ref: shallow clone refused", ["ref", "--repo", shallow, "--branch=dev", "--expect-sha", pushed],
             COULD_NOT_CHECK, "shallow clone")

        # A remote whose transport hangs (a stand-in ssh that only sleeps) must
        # hit the timeout and exit 2, not block the caller.
        g("-C", work, "remote", "add", "slow", "ssh://git@hang.example.invalid/x.git")
        os.environ["GIT_SSH_COMMAND"] = "sleep 30 #"
        t0 = time.monotonic()
        case("ref: hung fetch times out -> could not check",
             ["ref", "--repo", work, "--remote", "slow", "--branch=main", "--expect-sha", pushed, "--timeout", "1"],
             COULD_NOT_CHECK, "timed out")
        if time.monotonic() - t0 > 10:
            failed += 1
            print("FAIL  ref: hung fetch was not killed promptly")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nselftest: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
