# Project state, recovery & artifact receipts

**Read this when** beginning multi-step delivery, changing objectives,
transferring ownership, checkpointing, or recovering context after a reset or
crash. This is a compact record *contract*; it ships **no** storage engine or
recovery service. Keep **one** canonical project record with a single named
writer (the Conductor or a designated state writer), referencing existing
specs/issues/artifacts rather than copying them. Workers submit receipts for that
writer to reconcile. Keep credentials and private source content out of the
record.

## Record contract

| Entry | Required content |
|---|---|
| Identity | `schema_version`, project id, record revision, updated-at, writer, previous revision |
| Objective | Objective revision, owner goal, acceptance, constraints/non-goals, priorities, stop conditions |
| Knowledge | Facts with source + observation date; assumptions labelled separately with a validation/expiry condition; open uncertainty |
| Work | Task id, objective revision, one accountable owner, dependencies, the direct/delegate/parallel/investigate decision + reason, status, next action/trigger |
| Decisions | Decision id, alternatives weighed to consequence, rationale/evidence, owner, superseded decision |
| Acceptance | Criterion, required check, artifact revision, `PASS`/`FAIL`/`UNVERIFIED`, evidence source + observer |
| Artifacts | Real immutable identities + locations, producing task, integration/publication/visibility receipts; never invent an id for uncreated work |
| Resources | Aggregate + per-lane budgets, spent/reserved/unknown, remaining bound, requested vs actual model config (see `model-tiering.md` in the `deep-code-review` skill) |
| Authority | Grant source, authorized actor/action/resource/scope, conditions/expiry, current applicability; pending actions + denial reasons; **no credentials** |
| Recovery | Active owners, unfinished effects + action ids, last observed result, safe next action, reconciliation needed |

Checkpoint at objective/decision changes, dispatch or ownership handoff, receipt
acceptance, gate/budget transitions, before **and** after a consequential
effect, and before suspension/compaction. Keep entries compact; link to long
logs. **A checkpoint is a recorded claim, not evidence an action completed.** A
schema change needs an explicit migration; an unknown schema is not silently
interpreted. If the host cannot give atomic, durable writes, say so and verify
read-back — do not claim crash-safe persistence from a text instruction.

## Receipt contract (extends the SKILL.md Output contract)

The worker Output contract in `SKILL.md` (role, exact revision, artifacts,
acceptance covered, commands run + exit status, findings, remaining risk, cost)
holds for every lane. This adds **non-code identity + provenance** so the same
receipt discipline survives designs, data, and published resources:

| Artifact | Identity + appropriate evidence |
|---|---|
| Code | Immutable base + final Git SHA, review scope, exact-revision test/CI evidence; G5 served-app / UI checks where applicable |
| Document / design | Native immutable version if available, else an exported-content digest + snapshot date; render/read-back + the acceptance actually reviewed |
| Dataset / model | Version or snapshot, content/manifest digest, source lineage + observation date; the data-quality / model-eval scope actually run |
| Published / deployed | Provider operation or resource id **plus** the deployed version/content digest + observation date, and a read-back from the intended user surface |

A mutable URL or filename alone is insufficient; capture a dated snapshot/digest
before acceptance. **A digest proves content identity, not correctness,
accessibility, authorization, or delivery.** Evidence for an older
artifact/objective cannot silently accept the current one — justify each
unaffected criterion or rerun the check. Whether a control is *claimed* or
*enforced* is graded in `host-enforcement.md`.

## Resume protocol

1. Load and validate the latest record + objective revision; inspect live owner
   changes and authority sources. Mark saved facts stale where freshness matters.
2. Reconcile owners, live workers, artifacts, and external-action receipts.
   **Decide whether an interrupted effect completed before retrying: an unknown
   result is not failure** — query the authoritative service, or hold that action
   for resolution. Without observable status or safe (idempotent) retry
   semantics, do **not** replay an uncertain side effect.
3. Revalidate current permissions, required evidence, and the aggregate budget. A
   saved grant never revives expired or revoked authority; applicable explicit
   standing authorization remains usable (confirm-before-action still governs
   anything it does not cover — see `SKILL.md` Human gates).
4. Cancel or reassign obsolete work with acknowledged ownership transfer,
   preserving its artifacts, failures, and cost; choose the next action against
   the *current* objective; checkpoint the reconciled record, then proceed.
