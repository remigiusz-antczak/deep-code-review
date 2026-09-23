# Application security depth — credentials: passkeys, MFA, OTP, password policy

Read this when the target or diff implements passkeys / WebAuthn, push MFA, OTP delivery or verification, or a password policy. Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A07:2025 — Authentication Failures (depth: credentials)

**Passkey / WebAuthn credential-layer checks — `security-appsec.md` A07 is about session *tokens*; this is the *credential*.**
WebAuthn/passkeys are the platform-default sign-in and the credential NIST treats as phishing-resistant when properly
configured (its verifier-name binding is exactly rules 1–2 below), so a project shipping "passkey login" earns a
credential-layer pass, not just a session-token one:
- **RP ID pinned server-side** to the expected origin, never derived from a client-supplied `Host`/`Origin` header. A
  credential is *scoped to* its Relying Party ID — "a valid domain string identifying the WebAuthn Relying Party" (W3C
  WebAuthn L3) — so an attacker-influenced RP ID lets a credential validate for the wrong origin; verify `origin` and
  `rpIdHash` against a fixed expected value on every assertion.
- **Signature counter checked for clone detection.** Its "purpose is to aid Relying Parties in detecting cloned
  authenticators" (W3C WebAuthn L3): a new `signCount` **≤** the stored value is a possible-clone/replay signal to
  surface, never silently ignore. (A counter that's always `0`/absent is legitimate on some authenticators — flag a
  *regression*, not its absence.)
- **No silent downgrade to a weaker factor.** A WebAuthn failure that quietly falls back to a password or SMS/TOTP
  defeats the phishing resistance the flow advertises — NIST SP 800-63-4 requires AAL2 to
  **offer at least one phishing-resistant option** and AAL3 a phishing-resistant authenticator with a
  **non-exportable** key. The silent fallback path is the finding.
- **Attestation verified only where the threat model needs authenticator provenance** (regulated/high-assurance
  tiers); most consumer flows correctly skip it — don't over-flag its absence. Syncable ("multi-device") passkeys have
  exportable keys, so NIST bars them at AAL3 — check the assurance tier before requiring *or* forbidding sync.

**Push-based MFA needs challenge-response, not blind-approve — and OTP is a secret with its own lifecycle discipline.**
A bare accept/deny push, sent repeatedly and often paired with social engineering, is push-bombing (MFA fatigue): the
attacker relies on the victim eventually tapping approve out of habit or annoyance. The OWASP Multifactor
Authentication Cheat Sheet's mitigations: require challenge-response push authentication (for example, number
matching) so approval can't be blind, rate-limit or cap push notifications so repeated prompting isn't possible in the
first place, and monitor for multiple pushes in a short window as an anomaly signal. Where the factor is an OTP (SMS,
email, or a TOTP-adjacent one-time code), the same sheet sets a lifecycle floor the implementation SHOULD meet:
enforce a short TTL, ensure single use, apply strict attempt limits, invalidate on successful verification — and
SHOULD NOT log the OTP value. This is distinct from the constant-time compare OTP verification already needs (A04,
`appsec-crypto.md`) and from the per-operation send-cost throttle on OTP dispatch (`security-api.md` § API4): those
guard the compare operation and the send volume; this bounds the code's own lifecycle and exposure. Cross-ref the
one-shot approval-token `jti`/single-use primitive in `appsec-tokens.md` — same record-and-reject discipline, applied to a
human-facing OTP instead of a machine-bearer token.

**🚩** a push-MFA flow with a plain accept/deny and no rate cap; an OTP written to an access/debug log, accepted more
than once, or carrying no expiry.

**Password policy follows current NIST, not 2017-era habits.** Flagging the *absence* of forced periodic rotation or
character-composition rules is following **outdated** guidance — NIST SP 800-63-4 reverses both: "Verifiers and CSPs
SHALL NOT impose other composition rules (e.g., requiring mixtures of different character types)" and "SHALL NOT
require subscribers to change passwords periodically" (but "SHALL force a change if there is evidence that the
authenticator has been compromised"). Screen new passwords against a known-breached-credential list and set a length
floor instead; a mandated 90-day rotation or a complexity regex is itself the finding, not its absence.
