# Frontend client-side security depth (domain P / A05, A02)

Read this when the diff sanitizes or renders user-controlled HTML, sets or edits a
Content-Security-Policy, adds a `postMessage`/`message` listener, loads a third-party or CDN
`<script>`/`<link>`, stores a token or writes to `localStorage`/`sessionStorage`, sets
`Referrer-Policy`, a link/redirect/request carries a token or id in its URL, or the target
can be framed by another origin. Expands `frontend-a11y.md`'s "Security & compatibility" section
with the CWE/OWASP-cited depth a typical review doesn't need. Overlaps `security-appsec.md`'s A05
(XSS)/A02 (misconfig) at the browser-specific mechanics named below.

---

- **A `message` listener validates `event.origin` (and the message shape) before trusting `event.data`.** Any
  origin can `postMessage` to a window, so a handler reading `event.data` with no allow-list check on
  `event.origin` is an origin-validation flaw (CWE-346); a trusted sender can still relay a malformed payload,
  so validate the message syntax too (MDN *Window.postMessage*: "always verify the sender's identity using the
  `origin` and possibly `source` properties").
- **Third-party / CDN `<script>` and `<link>` carry Subresource Integrity.** An `integrity="sha384-…"` hash
  plus `crossorigin` lets the browser refuse a resource a compromised CDN has altered — without it, one CDN
  compromise rewrites what every user's browser executes (MDN *Subresource Integrity*).
- **A "strict" CSP is a specific, enforceable `script-src` — not just a header being present.** OWASP's Strict
  CSP form: `script-src 'nonce-{RANDOM}' 'strict-dynamic'` (or `'sha256-{HASHED_INLINE_SCRIPT}'
  'strict-dynamic'` when nonces aren't feasible), plus `object-src 'none'` and `base-uri 'none'` — never a
  bare `'unsafe-inline'`, which lets any inline script run (including an attacker's), defeating the point: a
  strict policy exists to "protect against classical stored, reflected, and some of the DOM XSS attacks"
  (OWASP *Content Security Policy Cheat Sheet*). The nonce must be fresh and unguessable **per HTTP
  response**, wired through an actual templating layer — a hardcoded or reused nonce is equivalent to
  publishing it, and a middleware that mechanically stamps `nonce="…"` onto every `<script>` tag in
  already-assembled HTML hands the same nonce to an attacker-injected `<script>` too (the cheat sheet's own
  warning: "attacker-injected scripts will then get the nonces as well"). Backstops CWE-79 — Cross-site
  Scripting, rank #1 in the CWE Top 25 (`security-appsec.md` already cites it).
- **Trusted Types as a DOM-XSS backstop on top of output encoding, not instead of it.** The
  `require-trusted-types-for 'script'` CSP directive forces DOM injection sinks (`innerHTML`, `eval`,
  `script.src`) to take policy-created typed values, turning a raw-string sink into a `TypeError` — a
  browser-enforced backstop (MDN *Trusted Types API*: Baseline 2026; a tinyfill keeps older browsers from
  throwing but enforces nothing there), layered on `frontend-a11y.md`'s output-encoding rule.
- **DOM Clobbering: HTML-injection-only, no script execution needed — the neighbor to Trusted Types above.**
  Named `id`/`name` attributes on ordinary elements (`<form id="config">`, `<a name="url">`) auto-expose as
  properties on `window`/`document`; a sanitizer stripping only script-based XSS lets that markup through, so
  an attacker's element can shadow whatever global the app relies on (OWASP *DOM Clobbering Prevention Cheat
  Sheet*, worked example: injecting `<a id=config><a id=config name=url href='malicious.js'>` against code
  reading `window.config.url`, "to load additional JavaScript code, and obtain arbitrary client-side code
  execution"). DOMPurify's default config only guards built-ins — app-defined names need
  `SANITIZE_NAMED_PROPS: true` (namespaces `id`/`name` with a `user-content-` prefix); on the Sanitizer API,
  set `blockAttributes` on `id`/`name` (its default doesn't stop this). CSP doesn't close the gap either — it
  can stop a clobbered *script source* from loading new attacker JS, but not clobbering used inside code
  already present (e.g., an `eval()` argument). Fix both ends: sanitize named props, and type-check
  (`instanceof`) any bare `window.*`/`document.getElementById(...)` read before trusting it as configuration
  or a callback — a clobbered global is a real `Element`, not the object the code expects. Distinct from this
  skill's other "clobber" hits (concurrent writers racing on shared state, e.g. `concurrency-shared-state.md`)
  — this is a same-origin HTML-injection attack, no race involved. Applies wherever user HTML is sanitized and
  rendered: CMS body text, markdown renderers, comment systems.
- **`Referrer-Policy` does not leak a token-bearing URL cross-origin.** The `Referer` header sends the full
  URL (path + query) to other origins; the modern default is already `strict-origin-when-cross-origin` (MDN
  *Referrer-Policy*), so the finding is a **weakened** policy (`unsafe-url`, `no-referrer-when-downgrade`) —
  or secrets/ids placed in a URL at all, which then ride the `Referer` to a third party (prefer keeping them
  out of the URL).
- **Clickjacking is a named threat, not just a header in a list.** Every page rendering an authenticated or
  state-changing action confirms `frame-ancestors` (CSP) — or legacy `X-Frame-Options` — restricts who may
  frame it; an unset framing policy lets an attacker overlay it in a transparent iframe (`security-appsec.md`
  A02 lists the header among misconfig; this is the threat and the per-page verification).
