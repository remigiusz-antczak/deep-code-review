# Application security depth — consequential and high-value actions

Read this when the target or diff performs a consequential or high-value action: a payout, wire transfer, payout-destination change, credential issue, privilege grant, or merge to a protected surface. Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A01:2025 — Broken Access Control (depth: segregation of duties, transaction authorization)

**Segregation of duties — a consequential action needs a distinct *second* principal, and this is not the two-principal matrix in `security-appsec.md`.**
The matrix tests that principal A cannot reach principal B's *object* (cross-principal access, IDOR). Segregation of
duties is the orthogonal axis: the **same** principal must not be able to both **initiate and approve** a
high-consequence action — issue and approve a payout, create and activate a credential, request and grant elevated
access, submit and merge to a protected surface. Check that
**`approver != requester` is enforced server-side on a stable principal id** (not a client field, not a display name),
that a user cannot **self-grant** the approver role to satisfy it, that it's scoped to genuinely consequential actions
(gating every write is friction, not control), and that the maker-checker decision is **audit-trailed** — who
requested, who approved, when (cross-ref `observability.md` § Audit trail & repudiation; don't restate). Absent, one
compromised or malicious account completes the whole chain alone. (SOX, PCI DSS, and NIST 800-53 AC-5 mandate this
control; whether a given target is legally required to enforce it routes to `business-ops` / counsel, not this gate.)
- **🚩** a consequential action (payout, credential issue, privilege grant, protected-surface merge) whose initiate and
  approve steps accept the **same** principal id; an `approver` / `approved_by` read from a client field or equal to
  the requester; an approver role a user can grant themselves.

**Transaction authorization (WYSIWYS) — an orthogonal, *same*-principal control, not a restatement of segregation of duties above.**
Segregation of duties is about *who* approves — a distinct second principal. Transaction authorization is about *what*
that principal is shown and confirms, even when it's the same person who initiated the action. For a high-value
transaction (wire transfer, payout-destination change), the OWASP Transaction Authorization Cheat Sheet's
**What You See Is What You Sign** principle requires the confirmation step show and let the user acknowledge the
transaction's own significant data — the actual target account and amount — not a generic "confirm?": "An
authorization method must permit a user to identify and acknowledge the data that is significant to a given
transaction." The same cheat sheet also requires each transaction be authorized with credentials **unique to it**, not
a reusable session factor: "If applications only ask for transaction authorization credentials once … the user could
authorize any transaction during the entire session or reuse the same credentials," which lets a compromised session
or sniffed credential authorize an attacker-substituted transaction the user never saw. A confirmation reusing the
login-session MFA code and showing only a generic prompt fails both halves at once — it isn't transaction content, and
it isn't unique/bound to this transaction. Cross-ref `billing-correctness.md` for the amount/ledger-correctness side
of a money-movement change; this control is the authorization-credential side, not the arithmetic.
- **🚩** a high-value transaction confirmation showing a generic prompt instead of the actual amount/recipient, or
  accepting the same MFA/session credential already used to authenticate the session.
