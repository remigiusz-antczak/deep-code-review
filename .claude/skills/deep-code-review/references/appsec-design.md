# Application security depth — threat-model method, boundary crossings, trust-signal spoofing

Read this when the review asks for or relies on a threat model, the diff adds a trust boundary, principal, or state transition, a change wires a producer across a publish or trust boundary, or the UI renders user-controlled text as a trust cue (a domain, sender, package, or username). Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A06:2025 — Insecure Design (depth)

**Which threat-model method — name the one that fits, don't hand-wave "a threat model."** **STRIDE** (per element:
Spoofing / Tampering / Repudiation / Info-disclosure / DoS / Elevation) for a component or data flow; **PASTA** when
the model must tie threats to business impact; **attack trees** to decompose one attacker goal; **LINDDUN** for
*privacy* threats (STRIDE's privacy counterpart — its **Linking** / **Identifying** threats have a concrete
lens in `privacy-compliance.md` § Linkability & re-identification, its **Detecting** threat in A07
account-enumeration in `security-appsec.md`); **MAESTRO** for an *agentic-AI* system — the agentic threat-modeling method, complementary
to the OWASP ASI / MITRE ATLAS catalogs in `security-ai-agents.md`. The review lens is **coverage, not ceremony**: a
change that introduces a new trust boundary, principal, or state transition the existing model never considered is a
finding — the model went **stale relative to the diff** — and an agentic surface with no agent-specific
(MAESTRO-shaped) model is the common miss. (Maturity frames — NIST SSDF, OWASP SAMM, BSIMM — measure the org's
*program*, not this diff; name, don't score.) To run a diff-sized model (data-flow table, per-boundary STRIDE or
LINDDUN, mapping to existing checks, residual risk and owner decision), follow `threat-modeling.md`.

- **A producer crossing a publish / trust boundary invalidates guards scoped to the old side — re-audit them.** A
  guard's *sufficiency* is often conditioned on a precondition — "internal only," "never published," "not
  user-facing," "dry-run," "behind auth." When a change wires that producer **across** the boundary (to a published /
  trusted / user-facing / external consumer), every guard justified by the old precondition must be
  **re-audited under the new one** — a weaker guard that was fine "because it never publishes" now ships its excused
  defect to the public surface (a false attribution, say). Two things hide it: the comment defending the weaker guard
  is now **out of date** (its precondition changed) yet reads authoritative, and the guard and the boundary-crossing
  edit usually live in **different files**, so a diff-scoped review sees one but not the other (the DIFF blast-radius
  rule, `SKILL.md`).
- **🚩 at the crossing:** a guard whose rationale cites "internal only / never published / dry-run / no rows" on a
  producer the same change wires to a published or external surface.
- **A rendered *trust signal* must resist *visual* spoofing, not only injection — STRIDE Spoofing at the display layer.**
  When user-controlled text is shown as an identity a human or system trusts and acts on, HTML-escaping and
  input-sanitizing do **not** stop **Unicode confusables / mixed-script homographs** — visual identity ≠ string
  identity, so the trust decision is made on a lie. The spoofable surfaces, a worked example, and the detection
  mechanism (Unicode skeleton / mixed-script restriction, UTS #39) live in `i18n-l10n.md` — threat-model such a signal
  for spoofing and check it there. Distinct from dependency typosquatting (`dependency-currency-and-upgrades.md`) and
  the bidi / Trojan-Source class (`i18n-l10n.md`).
- **🚩** a domain / sender-name / package-name / username rendered from user-controlled text as a trust cue with only
  HTML-escaping — no confusable or mixed-script check.

### Config hygiene and kill switches

Env and config reads should go through one accessor that trims whitespace (a trailing newline pasted into a secret
or flag silently breaks comparisons) and validates presence at startup. Grep for raw `process.env.` / `os.environ`
reads outside it. A kill switch, feature gate, or allow-list must fail closed: a missing, empty, or unparsable value
disables the risky path rather than enabling it, and an unset "disable" flag must not mean "enabled for everyone".

## Authorization: a client-side gate is not a server-side check — verify the trace, then verify the scope

- **A client-side permission/state gate (a hidden button, a disabled control, a client-side
  redirect on unauthorized state) is a UX nicety, not a security boundary, until traced to its
  server handler.** Reviewing only the UI where the rule was introduced and assuming "the server
  must check this too" is not a check — it's a guess. For any new or changed client-side gate:
  identify the server endpoint(s) the gated action calls, and confirm each independently
  re-derives the same condition from **server-trusted data** (the authenticated principal, a
  stored record field) — never a client-supplied flag/field the request happens to carry.
  **Verify:** call the endpoint directly (curl/API client) with the exact request the UI would
  never construct — the state the client-side rule was meant to block — and confirm the server
  rejects it on its own, independent of the UI. Flag any endpoint that doesn't check the
  condition, or checks a client-supplied field instead of deriving it server-side, regardless of
  how correct the UI looks. Companion to `frontend-security.md`'s client-vs-server-truth check and
  `security-appsec.md` A01's "Authorization decided only in the client = no authorization" — this
  is the tracing **procedure**, not a new rule.
- **Moving a client-only check onto a *shared* server endpoint can break every other legitimate
  caller of that endpoint — scope it, don't just relocate it.** "Move the client check to the
  server" is correct in isolation but treats the endpoint as owned by the one flow that motivated
  the fix. A shared endpoint often serves several call sites with different legitimate
  authorization shapes (an admin tool, an import job, another surface acting on someone else's
  behalf) — applying the strictest caller's rule to all of them is a regression, not a fix, for the
  callers that legitimately needed the looser behavior. Before hardening a shared endpoint:
  enumerate every caller/flow that hits it (grep call sites; check other UI surfaces, background
  jobs, admin paths — the DIFF blast-radius rule above applies to the endpoint's callers, not only
  its own diff). Scope the new rule by something the server can independently establish about the
  request's origin or flow (a distinct route, a server-known actor role, a stored record
  attribute) — never by a client-supplied field, and never applied blindly to every caller just
  because one caller needed it. **Verify:** after the fix, exercise every previously-working
  caller (not only the one that motivated the fix) and confirm each still succeeds for its
  legitimate case while the originally-vulnerable case is now blocked.
