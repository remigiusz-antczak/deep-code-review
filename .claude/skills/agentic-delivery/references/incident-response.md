# Incident response & continuity — the "on fire OR gone" binder

**Read this when** drafting an incident runbook, defining severity levels or
status/comms templates, setting up a break-glass access path, building a
credential/renewal inventory with reminders, or writing a solo-operator
succession note. This is the operational-readiness lens over the delivery OS:
the binder that has to exist *before* either failure mode arrives.

Two failure modes, one root cause — **bus factor = 1**:

- **The system is on fire.** An outage, a breach, data loss, a runaway agent.
- **The operator is gone.** Illness, a two-week absence, or worse — with
  nothing written down, the lights go out.

Neither can be authored during the event. Draft them cold.

## Boundary (what this lens does and does not do)

- **In scope:** *draft* the runbooks, templates, inventory, and the succession
  note. Structure the response.
- **Out of scope — route, never assert:**
  - **Who and when to notify on a breach** (customers, regulators, authorities)
    is a regulated-domain question. It routes to **G2 regulated-domain triage +
    legal counsel**. Notification clocks vary by jurisdiction and data type;
    this lens never states a specific deadline as fact — it points to counsel.
  - **Executing** any breach notification, or any succession/estate action, is
    the **owner's** call, taken with the relevant professional.
- **No fabrication.** Do not invent an SLA number, a legal deadline, a breach
  count, or a renewal date. Unknown timing is `UNVERIFIED` and routed; a date
  you cannot confirm is left blank for the owner to fill.

## Incident runbook

Six phases. Record timestamps and decisions as you go — that log *is* the
postmortem input.

1. **Detect.** How the incident is noticed (alert, report, anomaly). If it was
   noticed by a customer before any monitor, that gap is itself a finding for
   the review phase. Point detection design at the observability lens in
   `deep-code-review` — do not restate it here.
2. **Triage.** Assign a severity (below). Name a single incident lead (even a
   solo operator states "I am lead" to separate the role from the panic).
   Start the incident log.
3. **Contain.** Stop the bleeding before understanding it fully — take the
   feature offline, revoke a key, rate-limit, roll back. Containment beats a
   perfect diagnosis while harm accrues. Prefer a reversible containment.
4. **Eradicate.** Find and remove the root cause, not just the symptom. If the
   cause is a code defect, it goes through the normal review gate before the fix
   ships — an emergency does not suspend `deep-code-review`; it may narrow its
   scope to the diff.
5. **Recover.** Restore normal service. Verify the restore actually worked
   (see restore drills) rather than assuming. Watch for recurrence before
   declaring the incident closed.
6. **Review.** A **blameless** postmortem. Do not re-author the format — reuse
   `template-postmortem.md` and the mandatory-trigger / action-item-closure gate
   in `retrospective.md`. An escaped gap becomes a regression test; a reusable,
   identifier-stripped lesson can go upstream via the `contribution` overlay.

## Severity levels (template — owner sets the thresholds)

Fill these in for the specific product; the tiers below are a starting frame,
not asserted standards. Each tier defines: impact, who is paged, and how often
status is updated.

| Sev | Impact (example — set your own) | Response |
|---|---|---|
| SEV1 | Full outage, data loss, active breach | Drop everything; continuous updates |
| SEV2 | Major feature down, degraded for many | Same-day; regular updates |
| SEV3 | Minor or single-user, workaround exists | Normal queue; note and schedule |

## Comms templates

Honesty over polish. Never publish a fabricated ETA or a cause you have not
confirmed — "we are investigating" is truthful; a made-up root cause is not.

- **Internal update:** what is affected · severity · current action · next
  update time.
- **External / status page:** plain-language impact · that you are on it ·
  when the next update lands — no invented ETA, no blame, no minimization.
  A public status page (even a single static page you can flip) beats silence.
- **Breach comms are different:** their *content and timing* are gated by
  counsel + G2. Draft the mechanism now; do not pre-write a legal notice.

## Break-glass access

Emergency elevated access for when the normal path is down or the normal
approver is unreachable:

- **Pre-authorized and documented** before the emergency — not improvised.
- **Least privilege, time-boxed** — the narrowest access that resolves the
  incident, expiring automatically.
- **Logged and reviewed after.** Every break-glass use is a postmortem item:
  why the normal path failed, and whether the access should have been that
  broad.
- For a solo operator, "break-glass" also means: can a *trusted second person*
  get in at all if you cannot? If the answer is no, that is a bus-factor
  finding (see succession).

## Credential & renewal inventory (with dead-man reminders)

An expired domain, TLS cert, or card silently takes the product down with no
outage to detect. Maintain an inventory the owner keeps current:

| Item | Where it lives | Renews / expires | Reminder lead | Rotation / renewal steps |
|---|---|---|---|---|
| Domain registration | | | | |
| TLS / SSL certificate(s) | | | | |
| Payment card on file (for infra/domains) | | | | |
| DNS provider account | | | | |
| API keys / secrets (rotation cadence) | | | | |
| Cloud / hosting account | | | | |

- **Dead-man, not single-calendar.** A reminder on one person's calendar dies
  with bus-factor 1. Prefer a reminder that fires on a schedule *and* is visible
  to a second party, or that requires an explicit "still handled" acknowledgment
  and escalates if none comes.
- **Automate expiry checks where possible** (cert/domain expiry monitors) so a
  lapse is caught before it bites.
- Leave real dates blank for the owner to enter. Never populate this table with
  invented dates.

## Restore drills

A backup that has never been restored is not a backup. Point the depth at the
reliability / disaster-recovery lens in `deep-code-review` — do not restate it.
What belongs here is the **schedule**:

- A recurring restore drill (restore from backup into a scratch environment and
  verify integrity), on a cadence the owner sets and records.
- The drill result is logged; a failed drill is an incident.

## Solo-operator succession note

The "if the operator is gone" half of the binder. Drafting it is in scope;
the legal/estate dimension is the owner's, with a professional.

- **A trusted second person** and how they are reached.
- **Where everything is:** accounts, the credential inventory above, the
  repos, the infra, the domain — and how that person gains access (ties to
  break-glass).
- **Keep-the-lights-on vs graceful-wind-down:** the minimum to keep the
  product alive for a defined window, and how to shut it down cleanly and
  honestly notify users if that is the call.
- **Boundary:** this note is operational continuity, not a will or a legal
  instrument. Anything with legal force → owner + counsel.

## Verification

- A planted expired or about-to-expire credential/renewal in the inventory is
  surfaced (flagged for action), not passed over.
- A restore-drill schedule is present (a cadence, not just "we have backups").
- Breach notification timing is **routed** to G2 + counsel — never asserted as
  a specific deadline here.
- The review phase reuses `template-postmortem.md` rather than a second format.
