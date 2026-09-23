# Application security depth — threat-model method, boundary crossings, trust-signal spoofing

Read this when the review asks for or relies on a threat model, the diff adds a trust boundary, principal, or state transition, a change wires a producer across a publish or trust boundary, or the UI renders user-controlled text as a trust cue (a domain, sender, package, or username). Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A06:2025 — Insecure Design (depth)

**Which threat-model method — name the one that fits, don't hand-wave "a threat model."** **STRIDE** (per element:
Spoofing / Tampering / Repudiation / Info-disclosure / DoS / Elevation) for a component or data flow; **PASTA** when
the model must tie threats to business impact; **attack trees** to decompose one attacker goal; **LINDDUN** for
*privacy* threats (STRIDE's privacy counterpart — its **Linkability** / **Identifiability** threats have a concrete
lens in `privacy-compliance.md` § Linkability & re-identification, its **Detectability** threat in A07
account-enumeration in `security-appsec.md`); **MAESTRO** for an *agentic-AI* system — the agentic threat-modeling method, complementary
to the OWASP ASI / MITRE ATLAS catalogs in `security-ai-agents.md`. The review lens is **coverage, not ceremony**: a
change that introduces a new trust boundary, principal, or state transition the existing model never considered is a
finding — the model went **stale relative to the diff** — and an agentic surface with no agent-specific
(MAESTRO-shaped) model is the common miss. (Maturity frames — NIST SSDF, OWASP SAMM, BSIMM — measure the org's
*program*, not this diff; name, don't score.)

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
