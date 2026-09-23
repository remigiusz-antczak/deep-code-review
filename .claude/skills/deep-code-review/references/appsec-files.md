# Application security depth — files, archives, parsers, and exports

Read this when the target or diff accepts uploads, issues presigned or signed URLs, extracts archives, serves or downloads a file by a user-supplied path, parses XML or another format with an include mechanism, or exports CSV or spreadsheet files. Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A01:2025 — Broken Access Control (depth: signed URLs and upload authorization)

**Presigned / signed URLs & uploads.** Presigned URLs: one object, short TTL, re-issued per request; must die on
permission revocation. User uploads: authorize per object; never rely on unguessable paths; size/type/magic-bytes
checks; no executables in public dirs; SVG/HTML as stored XSS; archive extract = zip-slip risk (see A05 files block).

## A05:2025 — Injection (depth: files, archives, parsers, exports)

**Files, archives & parsers.** Uploads: enforce a size cap **and** an allow-list of types validated by
**magic bytes**, not the client-supplied `Content-Type` or extension. Store outside any directory the server will
execute or serve as code; no executables in public dirs. Treat SVG and HTML as **stored XSS** — serve from a separate
origin, or `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`, never inline on the app origin.
Archive extraction: reject entries whose resolved path escapes the target dir (**zip-slip**, CWE-22), plus symlinks,
absolute paths, and decompression bombs (cap entry count and uncompressed size).
**Serving or downloading a file by a user-supplied path is the same CWE-22 on the read side:** a handler that opens
`BASE_DIR + name`, `send_file(request.args['path'])`, or `res.sendFile(req.query.path)` lets `../` — or an absolute
path or an escaping symlink — walk out of the base and read arbitrary files (`/etc/passwd`, secrets, another tenant's
data).
**Resolve to a real, canonical path (`realpath`, which follows symlinks — a lexical `path.resolve` alone does not) and verify it's a true subpath of the base**
— compare against the base **plus its trailing separator**, or use a real is-subpath check, since a bare string-prefix
on `/base` also matches `/base-evil`; canonicalize *before* the check, reject absolute overrides, and reject an
escaping symlink; a bare `../` denylist is bypassable (`%2e%2e`, `....//`). Grep
`sendFile`/`send_file`/`send_from_directory`/`open(<dir> + <input>)` with no post-resolve base-prefix check. XML
parsers: **disable external entities and DTDs** (XXE, CWE-611) — `defusedxml` in Python,
`setFeature(FEATURE_SECURE_PROCESSING, true)` / disallow-doctype-decl in Java, `noent: False` for lxml. Same posture
for any format with an include/reference mechanism (XSLT, SVG `<use>`, YAML anchors, spreadsheet formulas).

**CSV / spreadsheet formula injection (export direction, CWE-1236).** The upload checks above guard *inbound* files
(the include/reference line even names inbound spreadsheet formulas, for XXE); a data **export** — CSV, or an
XLS/XLSX/ODS generated from stored rows — is the *outbound* mirror and needs its own check. Any stored,
user-controlled string (a display name, a coupon code, a free-text note) whose value **starts with** `=`, `+`, `-`,
`@`, a tab, or a NUL is parsed as a **formula** by the spreadsheet app that opens the export, not as text — an
exfiltration / RCE-adjacent chain (`=WEBSERVICE(...)`, `=cmd|...`) that runs when a human opens the file — a plain
formula evaluates on open; `=WEBSERVICE`/DDE `=cmd|` payloads typically prompt a security warning first — with
**no injection into your app** required. HTML-escaping the same field for the web UI does **nothing** here — a
different output context. Fix at **export** time: prefix a single quote before any such leading character. ASVS
v5.0.0-1.2.10 (L3) names them (a non-exhaustive list — the standard says "including") — "special characters (including
'=', '+', '-', '@', '\t' (tab), and '\0' (null character)) must be escaped with a single quote if they appear as the
first character in a field value" — and also requires RFC 4180 escaping for the CSV itself. 🚩 a CSV / XLSX export path
(`csv.writer`, `fast-csv`, SheetJS / `xlsx` write, a manual comma-join) writing a stored field with no
leading-character check.
