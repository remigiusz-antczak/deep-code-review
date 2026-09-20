# Changelog

All notable changes to this repository are documented here. Format loosely
follows Keep a Changelog; versioning follows Semantic Versioning.

## [1.334.0] — 2026-09-20

### deep-code-review — deepen: NIST 800-63-4 reverses forced password rotation/complexity (#781)

- **`security-appsec.md`** (#781): the authentication area's password-policy coverage now states that flagging the *absence* of forced periodic rotation or character-composition rules follows **outdated** (2017-era) guidance — NIST SP 800-63-4 reverses both ("SHALL NOT impose other composition rules"; "SHALL NOT require subscribers to change passwords periodically"), the one exception being a forced change on evidence of compromise; prefer breached-credential-list screening + a length floor. +1 eval; +1 curl-verified standards-index row (NIST 800-63-4 password policy); and the `docs/standards-index.md` ASVS caveat updated to record this session's direct re-verification of ASVS 5.0 V7 levels (7.3.1/7.3.2 = L2, 7.4.1 = L1), which match the existing citations.
- Independently reviewed **PASS-WITH-FIXES**: all NIST quotes + the ASVS levels confirmed at source. Applied the must-fix — the new password paragraph had been inserted directly above the WebAuthn block, inverting that block's "the block above is about session *tokens*" sentence; relocated it to *after* the WebAuthn block so the contrast reads correctly.

## [1.333.0] — 2026-09-20

### deep-code-review — NEW: cross-border data transfer & residency enforcement (#780)

- **`privacy-compliance.md`** (#780): a new "Cross-border data transfer & residency" section treating residency as its own reviewable surface — the code/config-layer companion to `privacy-by-design.md` §5's pre-code residency *promise*. Four rules: a stated residency promise (region selector, contract, "stored in the EU" claim) is checked against where data *actually* lands (a default/fallback region or a cross-region replica/backup outside the boundary is the finding); backups, logs, and analytics/CDC sinks are checked as **separate** residency surfaces from primary storage; third-party subprocessors receiving personal data have their own processing region checked; and a named transfer mechanism (adequacy / SCCs / BCRs) is flagged as a documentation gap and routed to counsel, never asserted. Fills the previously-dangling `domain-checklists.md` cross-ref into privacy. GDPR cited by name only, per the file's own by-name convention (no article numbers/URLs). +2 evals.
- Research-scout-surfaced. Built by a worktree builder; independently reviewed **PASS** — the builder correctly overrode an instruction to add GDPR article numbers because `privacy-compliance.md`'s own header bars unlogged article numbers (good judgment). Applied two optional polish items (dropped a structural "Chapter V" locator to match the by-name discipline; de-telegraphed one eval prompt).

## [1.332.0] — 2026-09-20

### deep-code-review — NEW: transactional/bulk email deliverability & one-click unsubscribe (#779)

- **`api-contracts.md`** (#779): first email-deliverability coverage in the suite — a new outbound-contract section. SPF/DKIM/DMARC published and aligned (a DKIM `d=` domain not matching the visible From:, or a DMARC policy with no aligned SPF/DKIM, is a silent deliverability failure). RFC 8058 one-click unsubscribe: `List-Unsubscribe` (one HTTPS URI) + `List-Unsubscribe-Post: List-Unsubscribe=One-Click`, DKIM covering those headers, the endpoint returning no redirect — a confirm-click-through defeats one-click because RFC 8058 makes the provider's automated POST *be* the unsubscribe action. DKIM must cover the unsubscribe headers themselves (a relay adding them post-signing silently breaks it). Bounce/complaint suppression. +2 evals; +1 curl-verified standards-index row (RFC 8058). Cross-refs `reliability-error-handling.md` + `privacy-compliance.md`.
- Research-scout-surfaced; RFC 8058 curl-verified by the parent. Independently reviewed **PASS-WITH-FIXES**: all five RFC 8058 quotes confirmed verbatim, but the reviewer caught a **rule-misapplication** — the confirm-redirect scenario had been pinned on the no-cookies/no-context MUST-NOT, which actually governs what the provider's POST may *contain* (privacy linkage), not what the endpoint returns. Corrected in the fold and in both eval grading spots to cite only "MUST NOT return an HTTPS redirect" plus the §3.2 purpose argument. Also softened an uncited "providers now require" claim to "increasingly enforce" and tightened DKIM `d=` alignment wording.

## [1.331.0] — 2026-09-20

### agentic-delivery — autonomous-mode gap-fill: open-ended-lane timebox + checkpoint (#754), spare capacity → hardening at terminus (#757), disk-sized fan-out (#765); partial #763/#386

- **`fast-agentic-delivery.md`**: (**#754**) an open-ended lane is briefed with an explicit wall-clock timebox + a required interim durable checkpoint (a pushed WIP branch/commit at a stated milestone), so liveness and sunk cost are judged by artifact, not runtime/transcript; prefer decomposing into checkpoint-able sub-lanes. (**#757**) at a genuine terminus, spare capacity redirects to verification/hardening of already-landed work (adversarial re-review, coverage, evidence) — a named alternative to idling, still not fan-out or busywork. (**#765**) disk arithmetic: per-heavy-lane footprint ≈ build output + deps; cap concurrent build lanes at ~`disk_free ÷ per_lane_footprint`; an ENOSPC lane death is a sizing bug (the spawn gate omitted disk), never a flaky-lane retry. (**#386**, partial) an orchestrator-owned reaper for orphaned heavy processes, advisory/approval-gated.
- **`multi-session-coordination.md`**: (**#765**) disk on a multi-machine fleet is *not* pooled — each machine gates on its own disk (contrast with the shared-host RAM/heavy-lane aggregation of #740). (**#763**, partial) two peers that mutually paused need an explicit un-pause trigger.
- **`SKILL.md`** (**#386**, partial): a change that would *reverse* a ratified invariant/decision is not a lane's mechanical call — stop and queue it to the owner (companion to principle 12). Plus two routing-trigger widenings (mutual-pause; unattended-run session lifetime). **`project-state.md`** (**#385/#386**, partial): session-only automation dies when the session/host closes — state the required operator action or prefer a durable scheduler.
- **#763's central "the only spawn gate is machine resources / never idle a tick" thesis was NOT imprinted** — it contradicts the free-RAM-is-a-veto, WIP-cap-by-landed-artifacts, and aggregate-distress-shed rules; only its non-contradicting fragment (a utilization-ratchet self-check: track active-lanes ÷ machine-capacity so a chain of individually-justified holds can't silently drift the fleet to idle) was added, explicitly deferring to those three gates. +5 evals. Built by a worktree builder; independently reviewed **PASS-WITH-FIXES** (the #763 fold verified not to weaken the three gates; two eval must-fixes applied — a dangling (a)/(b) prompt reference and a telegraphed utilization ratio). **Closes #754, #757, #765.** #763 and #386 remain open for the owner (the rejected #763 headline; #386 §7's fail-open-evidence request, rejected as contradicting the UNVERIFIED-never-a-pass rule; the operating-mode-doc question).

## [1.330.0] — 2026-09-20

### deep-code-review — NEW: WebAuthn/passkey credential-layer review depth (#778)

- **`security-appsec.md`** (#778): extends the session/MFA block (previously 100% session-tokens/OTP) with the passkey credential layer — the first WebAuthn coverage in the suite. Four rules: (1) **RP ID pinned server-side** to the expected origin, never derived from a client `Host`/`Origin` (verify `origin` + `rpIdHash` against a fixed value); (2) **signature-counter clone detection** — a new `signCount` ≤ the stored value (when either is non-zero) is a possible-clone/replay signal to surface, while an always-zero counter is legitimate (flag a *regression*, not absence); (3) **no silent downgrade** to a non-phishing-resistant factor (password, SMS/TOTP) on a WebAuthn failure; (4) **attestation verified only where the threat model needs provenance** — most consumer flows correctly skip it. Sourced to W3C WebAuthn L3 and NIST SP 800-63-4, both curl-verified. +2 evals; +2 standards-index rows. Research-scout-surfaced, sources curl-verified by the parent.
- Independently reviewed **PASS-WITH-FIXES**: applied all three citation-fidelity must-fixes the reviewer caught against the primary sources — a spliced W3C `signCount` quote missing its "if either is non-zero" qualifier (restored, with the elision marked); a cross-RP-privacy quote misattributed to "an authenticator" instead of "Relying Parties" (reattributed); and a logic bug in the `signCount` eval that graded "both non-zero" when the spec requires "either non-zero" (a regression stored=7 → new=0 must be flagged) — plus the optional NIST syncable-AAL3 quote and a "phishing-resistant when properly configured" hedge.

## [1.329.0] — 2026-09-20

### deep-code-review — frontend quality: caller-side memo defeat (#756), view-switch drops the active filter (#750), shared search highlights-behind-a-fold on a sibling renderer (#751)

- **`frontend-a11y.md`** (#756): a correct child memo is silently defeated by an **inline collection literal at the call site** — a parent passes `new Set(...)`/`new Map(...)`/a spread/an object literal inline in JSX, which takes a new identity on every parent render, so the child's (correctly-keyed) `useMemo`/`React.memo` invalidates and the expensive work reruns. Distinct from the two neighbouring memo bullets by *what is unstable and whether anything flags it*: no `React.memo` at all / an unstable **named derivation** (a view-model) / here a **bare literal** with no derivation to notice and a child memo that is already correct. Fix: hoist the literal into the parent's `useMemo`; don't add memoization the child already has.
- **`product-ux-quality.md`** (#750): a view/tab-switch href built from a narrow param allow-list (`?view=` only) silently drops a cross-cutting `?q=`/facet filter on navigation — build the href by merging over the current params, classifying each as view-scoped vs cross-cutting. (#751): a shared search **filters + force-expands** on one renderer but only **highlights** on a sibling, so a match inside an independent user-collapsed fold has zero visible effect — key the fold state off the active search (force-open a matching ancestor or show an "N matches inside" count), and make the caption match reality. Both extend the #707 "sibling renderers diverge" family.
- +3 evals. Built in-tree; independently reviewed **PASS-WITH-FIXES**: applied the must-fix (corrected the #756 distinctness axis — the reviewer caught that the neighbouring unmemoized-view-model bullet is *also* a caller-side unstable-reference defeat, so the original "callee side" framing was wrong) and the optional (de-telegraphed the #751 eval prompt).

## [1.328.0] — 2026-09-20

### deep-code-review — a shared sort comparator that returns NaN silently corrupts the whole sort (#761); a single-entity detail overlay that returns the whole collection and is uncached (#755)

- **`language-stack-redflags.md`** (JS/TS correctness): (**#761**) a shared sort comparator whose `isMissing`/`isBlank` guard covers `null`/`undefined`/blank but not `NaN` lets a `NaN` (a failed `parseFloat`/`Number()`, `0/0`, an unresolved average — all `typeof 'number'`) slip the type dispatch into `a - b` and return `NaN`. `Array.prototype.sort` never throws on this and the order is silently corrupt — one `NaN` can scramble the order of *other* valid values, not only misplace itself. Fold `Number.isNaN(v)` into the same shared "missing" predicate every caller uses, and regression-test one `NaN` among distinct numbers asserting global monotonicity of the whole result in both directions, not just the `NaN` element's slot. Distinct from the attacker-chosen-key comparator DoS (CWE-407) already in the file. Closes #761.
- **`performance-db-cost.md`** (payload/compute cost): (**#755**) a generic detail overlay/drawer opened from many pages whose data source returns the *entire* underlying collection on every open (defended by a real cross-reference correctness comment) while marked `no-store` — so a large build-time/batch-static majority is recomputed and retransmitted in full on every open across every mount site, though only a small slice is request-volatile. The justifying comment answers the payload-*shape* question, not the orthogonal *caching* one. Fix: split cached-static from volatile (version/build-id or ETag keyed), narrow to a per-id/kind projection where the cross-reference requirement allows, and pin a byte-size-ceiling regression test given the fan-in. Distinct from column-level over-fetch above. Closes #755.
- +2 evals (deep-code-review suite → 429). Built in-tree by the finalizer; gated on independent review before merge.

## [1.327.0] — 2026-09-20

### deep-code-review — product-ux: whole-row click/keyboard affordance hardened on one page's renderer but missed on a sibling page's separate renderer (#707)

- **`product-ux-quality.md`** (interaction-consistency / detection-gap family): an entity-row (same fields, same detail target) is whole-row-clickable on one page but only a single inner `<a>`/`<Link>` cell is interactive on a sibling page that imports a *different*, hand-rolled row component. The sibling clears WCAG in isolation (named, reachable, focus-ringed) and shares no component to check adoption on, so a11y tooling, a per-page review, and a duplicated-string twin-search all pass it clean — the defect is purely relational (a user who learned "click anywhere on the row" is silently punished on the sibling). Detect by enumerating every renderer of the row type (grep the shared fields/detail-link target, not a literal string) and diffing row-level interactivity against a lone anchor; name every renderer in a "make row X clickable" ticket's acceptance criteria, not just the page that prompted it. +1 eval. Closes #707.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**. Applied the must-fix: the shipped Fix prescribed a row-level `tabIndex={0}` + keydown while keeping the inner `<Link>`, which adds a second, roleless focusable for one destination (a worse screen-reader experience, and a self-contradiction with `frontend-a11y.md`'s own `role`/`tabindex`-pair grep). Corrected to keep the inner link as the single named focusable target and extend the whole-row affordance over it (a guarded row `onClick`, or a stretched-link overlay that also preserves native middle-click / open-in-new-tab), giving the row its own `tabIndex`/`role` only when it has no inner focusable path — which also closes the reviewer's optional finding that native-anchor affordances were forfeited without acknowledgement. De-telegraphed the eval prompt (it had narrated the exact guard/attribute/key tokens the expectation grades on) and re-scoped the eval's prescribed fix to the corrected pattern.

## [1.326.0] — 2026-09-20

### agentic-delivery — throughput epistemology: an assigned slice is a floor not a ceiling (#705), decouple action rate from poll-tick rate (#706), consolidate overlapping loop wakes into one pass (#556)

- **`fast-agentic-delivery.md`** (autonomous-throughput family): three folds. (**#705**) an agent that drains its own assigned backlog slice and declares terminus has swept its assignment, not the queue — the slice is a floor on what it commits to deliver, never a ceiling on what it may pull; broaden into the adjacent remainder of the same shared queue (collision-freedom via the occupancy check) before concluding there is nothing left, with room-to-act still a separate, swap-trend-gated question. (**#706**) a loop's own scheduled wake/poll cadence is not the work cadence — treating a ten-minute tick as the unit of work caps throughput at the poll rate, not the machine; on any wake, take every currently-admissible action (admission still governed by the existing WIP-cap / spawn-one-then-resample / disjoint-surface gates), never one action per tick. (**#556**) when several recurring loops wake on the same tick, consolidate them into one reconciliation pass (check once, act on the union) rather than executing every loop end-to-end — runtime behavior that leaves the operator-visible loop set untouched; gate the expensive sweep behind a fast no-op precondition check that runs first. +3 evals. Closes #705, #706, #556.
- Built by a worktree builder subagent, independently reviewed **PASS**. At finalize, verified cross-file consistency against v1.324's peer-coordination rule (#740) — which the wave's own reviewer structurally could not see — and added an explicit cross-reference so the "standing refill" model reads the resource gates as machine-wide aggregates (a per-session concurrency target does not compose across peers; the caps sum), harmonizing #706's refill discipline with `multi-session-coordination.md`. Also applied the reviewer's three optional fixes (two hard-wrap orphans rejoined and the term "fast no-op" introduced on first use; one loosely-dimensional phrase tightened).

## [1.325.0] — 2026-09-20

### deep-code-review — frontend-perf: an unmemoized tab/row view-model recomputes on a sibling input's keystrokes, even behind a debounce (#667)

- **`frontend-a11y.md`** (Core Web Vitals / render-perf family): a per-row/per-tile view-model built inline in the render body returns a new reference on every parent re-render, so even a child already wrapped in `React.memo` can't bail out — memo compares the incoming reference and this one is never stable. The usual trigger is an always-mounted search/filter input whose synchronous "echo" state (held in the shared parent) re-renders on every keystroke while only the debounced value reaches the fetch: the debounce gated the network call, not the recompute, so bumping the debounce delay does not fix the jank — the missing piece is the memo boundary (memoize the view-model on its real upstream inputs, then apply the row-level `React.memo`). Detect by confirming the view-model has no memoization keyed on its real inputs and gating the finding on real cost (a real chart, not a static text cell). +2 evals. Closes #667.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: applied the must-fix (removed a telegraphing "(non-memo'd)" tell from one eval prompt so the responder must infer non-memoization from the symptom, matching the sibling evals' house style) and two precision fixes (named the shared parent as the owner of the echo state so the re-render mechanism is self-consistent; re-keyed the realistic-cost eval expectation to the prose's own "real chart vs. static text cell" gate rather than a raw point count).

## [1.324.0] — 2026-09-20

### agentic-delivery — peer coordination: shared machine-wide budget (#740), routing a persistently-denied action without laundering (#727), a peer's correction is a lead not an order (#732)

- **`multi-session-coordination.md`** (peer-coordination family): three folds extending the peer-to-peer model. (**#740**) every peer honoring its own per-session heavy-lane cap still oversubscribes a shared host, because the caps **sum** — three sessions each at "≤4 heavy lanes" is up to twelve, not four; open a heavy lane only after checking the **aggregate** (a shared machine-wide reservation, or a raw shared signal — `git worktree list | wc -l`, `load1` vs core count, swap-percent), and shed lanes on aggregate distress rather than waiting for your own per-session cap to trip. (**#727**) a persistent cross-peer permission/classifier asymmetry (the identical shared-maintenance or publish action routine for one peer, hard-denied for another on every attempt) is not a retryable flake — after two identical denials, stop retrying, and **surface and route** the blocked action to a peer that can perform it or to the owner; never launder the block by having your own logic reach the same effect through a path the classifier never evaluated, and prefer a classifier-safe in-repo alternative where one exists. (**#732**) a peer's "X is wrong, do Y" correction is indistinguishable from a stale or spoofed message — treat it as a **lead**, reconcile it against your own verifiable state (a SHA, a PR URL, a timestamp) before complying, and refuse or flag one that contradicts what you can already verify; on the sending side cite verifiable state and frame the instruction idempotently. +3 evals; SKILL.md routing trigger widened to name the machine-wide-budget, persistent-denial-routing, and correction-vetting cases. Closes #740, #727, #732.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: applied both must-fixes — rewrote the #727 eval's `expected_output` to drop a mis-cite (the in-session orchestrator-vs-own-subagent classifier case in `fast-agentic-delivery.md` is deterministic, not "intermittent," and only an already-green merge may be delegated to a sub-agent — never a workaround for an active denial), and widened the multi-session routing trigger the reviewer flagged as too narrow for the new sections.

## [1.323.0] — 2026-09-20

### deep-code-review — gh-CLI gotchas: PR-body full-replace clobber (#739); `.github/workflows/*` needs the `workflow` OAuth scope (#719)

- **`parallel-audit.md`** (gh-gotcha family): (**#739**) `gh pr edit --body`/`-b` **and** `-F`/`--body-file` both REPLACE the whole PR body (not append/merge) — in a multi-lane fan-out a wrong `<N>` clobbers an unrelated PR, and a second editor erases the first's checklist/markers; read-verify-write (`gh pr view --json body`, re-post the merged text) or use `gh pr comment`. (**#719**) editing `.github/workflows/*` needs a token with the `workflow` OAuth scope — a push touching a workflow file is rejected without it; check `gh auth status` scopes and treat a missing scope as fail-closed. +2 evals; +1 curl-verified `docs/standards-index.md` row (GitHub OAuth-scopes doc). Closes #739, #719.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: both CLI/scope claims verified via `gh --help` + the GitHub docs; applied both must-fixes — named `-F`/`--body-file` alongside `--body` (the reviewer caught that the original "one flag" claim was false and exempted the very flag #739's incident used), and logged the cited OAuth-scopes doc in `docs/standards-index.md` (the repo's own definition-of-done requires it).

## [1.322.0] — 2026-09-20

### deep-code-review — a CAS after a non-idempotent side-effect does not guard the side-effect (#646)

- **`concurrency-shared-state.md`** (DB / store TOCTOU): a CAS / optimistic guard placed *after* a non-idempotent side-effect (a charge, a send, a third-party write) protects only the **state column** recording it, not the side-effect that already fired — under concurrency (or a lease expiring mid-side-effect) the loser's side-effect already committed, unrecorded or duplicated. Fix in preference order: (a) **claim/CAS first** (reserve, then act), (b) idempotent/keyed side-effect, (c) record the outcome atomically with the transition. Distinct from the wrong-field-CAS bullet (a *right* column that still can't retroact), the fencing-token/paused-holder race (exclusivity vs ordering), and the idempotency-key rule (cross-reffed). +2 evals. Closes #646.
- Built by a worktree builder subagent, independently reviewed **PASS**: confirmed genuinely absent and distinct — eval-1 uses a plain version CAS with **zero lease mechanics** and the flaw still fully reproduces, structural proof it's independent of the lock-liveness race; advisor had caught and fixed an eval domain-collision + telegraph pre-review.

## [1.321.0] — 2026-09-20

### agentic-delivery — NEW reference: multi-session / peer coordination (independent sessions, no shared conductor)

- **NEW `agentic-delivery/references/multi-session-coordination.md`** (routed from `agentic-delivery/SKILL.md`): the doctrine for two-or-more **independent peer sessions / machines** coordinating over a shared async channel with **no single orchestrator** — a distinct axis from `fast-agentic-delivery.md`'s one-conductor + subagent-lanes model. Five folds: (**#593**) commit a machine-readable **claim registry**, not a prose thread; (**#597**) one deterministic **pre-write collision probe** (glob-match the registry + live-PR diff + `exclusive_role` check), never "read the thread and hope"; (**#709**) **verify peer liveness** before spending coordination budget (a board yields zero lift with no live reader); (**#711**) track a **high-water mark** and read the full range each sync, not just the newest entry; (**#713**) reconcile crossed work-splits **deterministically** (in-flight anchor + fixed partition + per-item action-time recheck + first-to-reconcile-wins). +5 evals. Closes #593, #597, #709, #711, #713.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: routing gate confirmed (new file routed, both directions); doctrine confirmed genuinely absent and the distinct peer/no-conductor axis (cross-refs, not restates, the single-session ownership-map + transcript-is-not-liveness rules); all five issue numbers verified live. Applied the must-fix — declared the `exclusive_role` field in the registry schema so the collision-probe's "well-known field" reference resolves — and renamed rule 4 to "first-to-reconcile-wins" to match its definition.

## [1.320.0] — 2026-09-20

### deep-code-review — enforce the upload/body size cap before buffering, not after (OWASP API4 memory axis, #745)

- **`security-appsec.md`** API4: a raw-body / upload size cap must be enforced **before/while streaming** — reject early on an over-limit `Content-Length` AND enforce a hard streaming byte-ceiling (because `Content-Length` can lie or be absent/chunked). Enforcing it *after* buffering the whole body into memory **is** the DoS the cap should prevent. Distinct from the spend-axis bullet, the A05 upload-size cap (which caps size but not the buffering *order*), CL/TE request smuggling, and CWE-789 (an in-payload *declared*-size field). Coverage by a shared bounded-read middleware ≠ whole-app coverage — a raw-body route that bypasses it still ships the bug. +2 evals; extended the existing OWASP API4 `docs/standards-index.md` row (spend + memory axes). Closes #745.
- Built by a worktree builder subagent, independently reviewed **PASS**: OWASP API4 quotes byte-verified; the flagged CWE-789→API10 "dangling xref" was independently confirmed a **false alarm** (the "both" coordinates two correct referents — the builder correctly invented no fix); one optional readability fix applied at finalize (tightened a run-on).

## [1.319.0] — 2026-09-20

### deep-code-review — a11y: live-region loading announce (#737), Label in Name (#736), disclosure aria-expanded (#735)

- **`frontend-a11y.md`** three folds: (**#737**) a loading/skeleton region that visually swaps state needs a **live region** (`role="status"`/`aria-live`) announcing the transition — `aria-busy` alone doesn't announce (WCAG 4.1.3 Status Messages, Level AA; its glossary definition covers a "waiting state"/"progress"); (**#736**) an `aria-label` rewritten for context must still **contain the visible text** (WCAG 2.5.3 Label in Name, Level A), or a voice-control user can't activate it; (**#735**) a disclosure toggle that swaps its label/icon still needs **`aria-expanded`** on the control. +4 curl-verified `docs/standards-index.md` rows (WCAG 2.5.3/4.1.3, MDN status role + aria-expanded, canonical redirect URLs noted); +3 evals. Closes #737, #736, #735.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES** (content clean — only optional cosmetic/provenance nits): every WCAG/MDN quote byte-verified against a fresh fetch, incl. confirming the 4.1.3 status-message glossary scope covers a loading state and the MDN canonical-redirect URLs; folds confirmed genuinely absent and distinct (the #735 fold cross-refs the existing APG mention rather than restating it); evals grounded (#737 rejects `aria-busy`+`aria-label` as sufficient) and de-telegraphed.

## [1.318.0] — 2026-09-20

### agentic-delivery — four operating-doctrine fixes (worktree-reclaim-on-push #538; revert not gated by its own ratchet #734; report the operator's metric #708; self-updating escape command #534)

- **`fast-agentic-delivery.md`** four addendum folds: (**#538**) reclaim a worktree once the lane has reported done AND local HEAD == origin/<branch> AND the tree is clean, **paired with a positive liveness check** (pushed+clean alone isn't proof a lane stopped) — not only on merge; (**#734**) a revert-to-green must not be blocked by the very absolute-count ratchet it restores; (**#708**) report the operator's own metric (open-issue count/delta), not the agent's merge-count proxy, and reconcile continuously; (**#534**) the human escape-hatch one-action ask must be a self-updating/idempotent command, not a stale per-batch PR list. +4 agentic-delivery evals. Closes #538, #734, #708, #534.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: applied the must-fix — the #538 eval had shipped the exact **false-universal** ("a still-running lane always has unpushed WIP, so it can never be reclaimed by mistake") that the prose fix retires; corrected the eval to require the lane-done + liveness pairing, and fixed a backwards "(above)" → "(the transcript-is-not-liveness rule below)" cross-reference.

## [1.317.0] — 2026-09-20

### deep-code-review — pagination correctness (page-token opacity; LIMIT/OFFSET undefined without ORDER BY)

- **`api-contracts.md`**: a cursor/page token is part of the versioned contract — keep it **opaque**, URL-safe, and non-parseable (base64 ≠ opacity — AIP-158), make it **tamper-resistant** (signed/encrypted — the skill's own advice, not AIP-158's), and it must **never carry authorization** (authz is re-checked per request; cross-refs the BOLA/BFLA two-principal matrix in `security-appsec.md`, not restated).
- **`performance-db-cost.md`**: `LIMIT`/`OFFSET` with no fully-discriminating `ORDER BY` is undefined **even on a static table with zero writes** — the query planner may pick different plans (different row order) per LIMIT/OFFSET; a genuine extension of the existing concurrent-write-drift bullet (PostgreSQL §7.6).
- +2 curl-verified `docs/standards-index.md` rows (AIP-158, PostgreSQL §7.6); +2 evals. Core offset/cursor-tiebreak drift confirmed already covered (2 existing evals).
- Research-derived expansion (no filed issue). Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: AIP-158 + Postgres quotes byte-verified at source; applied the must-fix — AIP-158 was over-credited with "tamper-resistant" (its Opacity section covers non-parseability/confidentiality only), so tamper-resistance is now stated as the skill's own advice and AIP-158 is cited only for what it states.

## [1.316.0] — 2026-09-20

### deep-code-review — algorithmic-complexity / resource-exhaustion DoS (hash-flooding, uncontrolled recursion, excessive-size allocation)

- **`language-stack-redflags.md`** DoS section, 3 CWE-backed folds: (1) **CWE-407 hash-flooding** — attacker-chosen *keys* into a hash-map or comparator force worst-case O(n²), surviving an item-count cap (the attack is in the keys, not the count). (2) **CWE-674 uncontrolled recursion** — a recursive-descent parser on attacker-nested input exhausts the call stack on a few-KB payload; distinct from the decompression bomb (byte-size), API10 upstream-consumption, the generic "max depth" cost-cap, and the GraphQL resolver-depth limit. (3) **CWE-789 excessive-size allocation** — trusting a size/count/dimension declared *inside* the payload to pre-allocate; distinct from the wire-level upload cap and the C/C++ integer-overflow-before-`malloc` bullet (oversized→exhaustion vs undersized→corruption). Mitigation shapes + library depth-defaults are hedged as verify-against-target (not on the CWE pages). +3 curl-verified `docs/standards-index.md` rows; +3 evals.
- Research-derived expansion (no filed issue). Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: the reviewer re-curled all three CWE pages and byte-verified every quote including all six CVE lines (append-only proven at object equality); fixes applied — added the CWE-674 cross-refs to the "max depth" cost-cap and GraphQL depth-limit neighbors (airtight the no-restatement distinction), and corrected the standards-index title attribution to "page heading verbatim" (the `<title>` element carries a "CWE - " prefix the quote omits).

## [1.315.0] — 2026-09-20

### deep-code-review — cryptographic-usage correctness (nonce/IV reuse, constant-time comparison, KDF cost floor, DEK/KEK separation)

- **`security-appsec.md`** A04, four folds: (1) **nonce/IV reuse** — AES-GCM nonce reuse recovers the auth subkey → ciphertext forgery (NIST SP 800-38D App. A); CBC/CFB need an *unpredictable* IV, stricter than merely unique (SP 800-38A); a reused CTR/OFB keystream is a two-time-pad break across the full message overlap (CWE-323). (2) **constant-time comparison** as a general rule for any secret (HMAC / session / CSRF / OTP / API-key), CWE-208, with the Node `timingSafeEqual` equal-length gotcha + Java `MessageDigest.isEqual` + Go `subtle.ConstantTimeCompare`. (3) **password-KDF cost floor** — check the work factor, not just the algorithm name (OWASP Password Storage), framed as a moving target. (4) **DEK/KEK key-purpose separation** for hand-rolled envelope encryption (OWASP Cryptographic Storage). ECB / weak-RNG / cert-verify-disabled / JWT alg-confusion confirmed already covered. +6 curl-verified `docs/standards-index.md` rows (both NIST PDFs processed with `pdftotext`); +3 evals.
- Research-derived expansion (no filed issue). Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: the reviewer processed both NIST PDFs and byte-verified every quote, cross-checking the two CVEs against NVD; fixes applied — extended the DEK/KEK quote back to OWASP's most-direct statement ("At least two separate keys are required for this:"), corrected the CTR/OFB reuse scope (full overlapping length / two-time-pad, not "just the repeated blocks"), and reworded the nonce eval's severity to derive from the exposure-boundary discriminator rather than a flat "Critical" label.

## [1.314.0] — 2026-09-20

### deep-code-review — structural cleanup: dedup SKILL.md, reclaim ~920 bytes of routing headroom, fix a thesis-violating SSRF-list drift

- **`SKILL.md`**: removed the "Adversarial / red-team pass" section — a 100% restatement of the Phase-3 table row + `method.md`'s Phase 3 procedure + `security-appsec.md`'s verification etiquette. Its one non-redundant clause (a red-team pass proves exploitability locally and non-destructively only, never against a system you don't own or aren't authorized to test) is preserved in **principle 7** (the always-loaded core). Folded the domain-P appendix into **row P**'s inline trigger (the two reference files' own "read this when" headers already carry the depth). Reclaims ~920 bytes: SKILL.md 23,957 → 23,033 (headroom 43 → ~967 bytes), unblocking future domain rows.
- **`domain-checklists.md`**: the SSRF blocked-range list had silently drifted from the canonical list in `security-appsec.md` (A01) — dropping `.internal` — **while claiming a copy here "can't drift out of date,"** exactly the failure the repo's no-duplication thesis warns against; replaced the drifted copy with a pointer to the canonical list.
- **`method.md`**: fixed a dangling "(section below)" that pointed at no section (the Phase-3 openers are inline).
- Pure structural dedup + citation fidelity — no behavior or eval change. Surfaced by an independent structural self-audit (all 36 reference files read in full; the suite otherwise confirmed exceptionally clean — every cross-file overlap is a deliberate, marked cross-ref) and verified at source: the deletion's redundancy confirmed at three loci, no dangling references to the removed heading, routing byte-gate green.

## [1.313.0] — 2026-09-20

### deep-code-review — a distributed lock/lease guarantees liveness, not exclusivity (fencing tokens)

- **`concurrency-shared-state.md`** new "Distributed lock/lease TOCTOU — liveness is not exclusivity" subsection: a time-bounded distributed lock/lease does **not** guarantee exclusivity against a **paused** (GC/page-fault/SIGSTOP) or **clock-skewed** holder — a second node acquires the expired lease and both write; re-checking "is my lock valid?" before the write does **not** close it (the pause lands between check and write); holder and lock service measure the TTL on their own clocks. The fix lives at the **resource**: a monotonic **fencing token** the resource validates and rejects if stale — but only when the reviewed code controls the resource's write path; for a third-party/managed resource that can't validate a token, the op must instead be **idempotent or compare-and-set**. Distinguished from this repo's cooperative "claim a lane" lease convention, the SQS visibility-timeout race, and lock-ordering/deadlock. Kleppmann + etcd cited; +2 `docs/standards-index.md` rows; +2 evals.
- Research-derived expansion (no filed issue). Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: the reviewer byte-verified every Kleppmann/etcd quote and confirmed the fencing-token scope is correctly gated; applied both must-fixes — softened a leader-election clause that over-attributed a shared-failure-shape claim to etcd (etcd only lists the patterns together, doesn't claim the shared shape), and split a standards-index quote's section heading (the GC-pause quote is under "Protecting a resource with a lock," not "Making the lock safe with fencing").

## [1.312.0] — 2026-09-20

### deep-code-review — front-end / loader performance: serialized independent awaits (#716); a static dataset leaked into the client bundle (#715)

- **`performance-db-cost.md`** (#716): sequential `await`s with no data dependency are an **accidental serialization** (sum-vs-max latency, extra round-trip per call to TTFB), not a design choice — issue independent I/O concurrently (`Promise.all` / `asyncio.gather` / errgroup), keeping genuinely-dependent calls sequential. Distinct from N+1 (per-row), the frontend critical-request-chain waterfall, and the terse "async/parallel where safe" one-liner above it (which states the principle without the failure shape, detection trace, or dependency carve-out).
- **`frontend-a11y.md`** (#715): a shared data-access module can leak an **entire static dataset into a client bundle** through one "harmless" helper import (tree-shaking defeated by a singleton the module builds over the whole dataset at load); resolve it server-side or split the heavy data behind a separate import, plus a standing import-graph test. Distinct from the heavy-optional-library-gated-at-import bullet and the RSC-proxy section (bundle-size leak vs functional-proxy bug).
- +2 evals; bidirectional TTFB↔LCP cross-ref. Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: both folds confirmed genuinely new and distinct (the #716 eval discriminates accidental serialization from a genuine dependency chain, and rejects a blind `Promise.all` over a dependent call); applied the reviewer's must-fix — disambiguating #716 from the terse "async/parallel where safe" line directly above it, per the repo's no-restatement thesis. Closes #716, #715.

## [1.311.0] — 2026-09-20

### deep-code-review — metric type & shape correctness (histogram buckets, instrument type, lazy-create, units)

- **`observability.md`** new "Metric type & shape correctness" subsection: (1) a classic fixed-bucket histogram needs a bucket boundary *at* the SLO threshold or a fraction-under-threshold query returns no/incomplete result **silently**; averaging pre-computed percentiles (`avg(p95)`) across replicas is statistically invalid — recompute from raw buckets. (2) instrument-type mismatch — `rate()` of a gauge is meaningless; `rate()`/`increase()` adjust for a reset **unconditionally**, so a counter zeroed by anything other than a restart still triggers the adjustment and mis-counts at the reset; an OTel `UpDownCounter` recorded with differing attribute sets forks into two series. (3) a metric absent until first occurrence is a **blind spot, not a zero** (breaks ratio denominators + deadman/absence checks). (4) one unit per metric (Prometheus suffixes the unit into the name, OTel keeps it in metadata — only "never mixed" is stack-agnostic). +5 curl-verified `docs/standards-index.md` rows (Prometheus histograms / functions / instrumentation / naming, OTel semconv); +3 evals.
- Research-derived expansion (no filed issue). Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: the reviewer re-curled all sources and pulled the default-bucket constants from four Prometheus client libraries — catching a **fabricated eval premise** (a histogram on default buckets queried at `le="0.25"` was claimed to render blank, but 0.25 is a default boundary in Go/Python/Node/Java; corrected to `le="0.3"`, which the prose already used) — and a **misstated mechanism** (a non-restart reset was said to "defeat" `rate()`'s compensation, but Prometheus adjusts unconditionally; reworded to the violated-assumption framing, verified against a fresh fetch). Plus quote-fidelity fixes (a restored "…" elision; the OTel units carve-out added) and a new `functions/` standards row for the now load-bearing rate() quote.

## [1.310.0] — 2026-09-20

### deep-code-review — two data-state review folds: partial-apply response type drops computed failure detail (#699); a shared honest signal is only as good as its least careful consumer (#700)

- **`product-ux-quality.md`** (#699): a partial-apply operation's success counters must reconcile to its own total — a client response **type** that is a strict subset of the server's return silently drops computed failure detail (`error_count`/`errors`), so counters undercount with no visible cause. Remedy is **both halves**: the type declares the failure fields *and* the render surfaces them (widening the type without a render branch just relocates the silence). Distinct from the remainder-indicator rule (type-boundary drop vs render-time slice).
- **`product-ux-quality.md`** (#700): a correct loading/failed signal is only as good as its **least careful consumer** — one sibling surface off a shared honest hook that reads the raw value and ignores `ready`/`loadError` renders a confident wrong zero. Sweep **every** consumer of the shared instance, not just the one in the diff. Cross-refs the all-call-site-sweep family (`data-quality.md` §5/§6 write-guard & soft-delete; `i18n-l10n.md` normalizer). +2 evals.
- Built by a worktree builder subagent (pre + post advisor self-review), independently reviewed **PASS**: both folds confirmed genuinely distinct from the empty-state/dead-render family and the shared-component adoption / divergent-props rules (different mechanism + stakes class); every eval expectation traced to shipped prose; evals strictly append-only. One optional style-consistency fix applied at finalize (inline "Detect it by…" idiom). Closes #699, #700.

## [1.309.0] — 2026-09-20

### deep-code-review — replay protection for short-lived approval bearer tokens (closes #696)

- **`security-appsec.md`** (A07 Authentication Failures): a short-lived approval/action bearer token verified only for **signature + expiry is replayable** inside its validity window — if it leaks (access log, APM breadcrumb, logging proxy) it can be resubmitted to re-trigger the approved write, attributed to the original approver, with no signal it fired twice. A short expiry only narrows the window; **single-use enforcement** closes it — mint a unique `jti`, record consumed ids, reject a reuse. The record-and-reject must be a **single atomic** step (unique-constraint insert / compare-and-set) — a read-then-insert is itself a TOCTOU that two concurrent replays both pass. Distinguished from four adjacent controls: idempotency key, inbound-webhook replay, **refresh-token reuse detection**, and CSRF. CWE-294 + OWASP JWT Cheat Sheet (Replay Protection) cited; +2 `docs/standards-index.md` rows; +2 evals.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: the reviewer curl-verified CWE-294's title and every OWASP quote, and caught an **OWASP-misattribution** — the prose implied OWASP *ranks* the single-use controls above short expiry, but OWASP lists all mitigations flat/unranked; reworded (against a fresh fetch) so the ranking is stated in the skill's own voice, not attributed to OWASP. Also applied at finalize: the consumed-id **atomicity** requirement (a naive check-then-insert is racy), **refresh-token reuse detection** added as a fourth distinct control, and a quote-punctuation fidelity fix (colon in source). Closes #696.

## [1.308.0] — 2026-09-20

### deep-code-review — conflict-swallowing write must check the affected-row count (#728); an "N/A" empty-collection accessor silently inverted by a generic filter (#729)

- **`concurrency-shared-state.md`** (DB / store TOCTOU): a conflict-swallowing write (`ON CONFLICT DO NOTHING`, `insertMany({ordered:false})`, `MERGE`) used as a race backstop must report the **actual affected-row count** (rowcount / `RETURNING`), not the size of the batch the app decided to insert — else the race the backstop exists for fires and the loser returns "inserted: 1" while its write was a silent no-op. Distinguished from `data-quality.md` §1 (that degrades a *value*; this misreports a *count*). +🚩.
- **`data-quality.md`** (§5 Deduplication & consistency): an accessor returning an empty collection to signal "not applicable" is indistinguishable, to a generic membership filter, from "applies but matches nothing" — so the whole type silently drops from results whenever any caller passes that filter; represent inapplicability explicitly (whole-type bypass / sentinel the filter special-cases), never a bare `[]`. Distinct from the nested-key accessor gap (empty *by mistake* vs empty *on purpose*); cross-refs `product-ux-quality.md`'s empty-state rule + `api-contracts.md` (a documented-contract divergence when the filter is documented as narrowing, not excluding whole types). +🚩.
- +2 evals. No external citation (internal patterns). Closes #728, #729.
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: both folds confirmed genuinely new and distinct against the owner-filed issues (the dispositive test — applying the neighbor bullet's own prescribed fix to #729 does not resolve it); evals confirmed strictly append-only (prior entries byte-identical) at the branch's true parent; applied the reviewer's optional doc-contract sharpening to the #729 bullet.

## [1.307.0] — 2026-09-20

### deep-code-review — payments correctness: multi-currency Money value-object + ledger double-entry / derived-balance

- **`billing-correctness.md`** two new sections. **Multi-currency correctness**: amount and currency are one inseparable value (Fowler's Money value-object pattern, by name); cross-currency arithmetic (summing/comparing amounts in different currencies) is a **type error**, not a rounding nuance; any FX conversion must pin the rate's **source + timestamp**. **Ledger integrity**: every transaction's debits sum to its credits (net zero — double-entry, by name); a balance is **derived** (`SUM(credits) − SUM(debits)` over an append-only entry log), never a mutable running-total column that drifts (cross-refs `concurrency-shared-state.md` CAS + `reliability-error-handling.md` reconciliation). Plus a webhook **amount/currency cross-check** (signature proves authenticity, not correctness) and a **rounding-mode catalog** (half-up / half-even / truncate; `sum(round(x)) ≠ round(sum(x))`). "In scope", 🚩 red flags, and `## Verification` extended to match.
- **`domain-checklists.md`** "Money & numeric precision" bullet gains: amount and currency travel together, never sum/compare across currencies without a provenanced conversion (Depth → `billing-correctness.md`).
- +2 evals. All citations are well-established patterns cited by name — no `docs/standards-index.md` row. Research-derived expansion (no filed issue).
- Built by a worktree builder subagent, independently reviewed **PASS-WITH-FIXES**: absence re-verified repo-wide and by full-file read (pre-existing "ledger" hits are spend/coverage ledgers — a different sense; integer-minor-units precision is orthogonal to currency-pairing); all prior evals confirmed byte-identical (strict append-only); applied the fix — extended the file's `## Verification` checklist with the two new lenses and corrected the domain-checklists parenthetical ordering so "(Float-for-money…)" stays with the float clause.

## [1.306.0] — 2026-09-20

### deep-code-review — the gate-calibration rule's mirror: a fix that breaks a correctly-calibrated gate is the defect, not the gate (closes #443)

- **`method.md`** extends the "Check a firing gate against its own standard first" bullet with the **mirror** of the existing over-strict-gate rule: when the gate already matches its standard, a fix that would make it fail is what's wrong — do not weaken or suppress a correctly-calibrated gate to land a change. Two correct constraints in apparent tension is a **design problem**, not a gate problem: find the design that satisfies both, or route it as an owner trade-off (principle 4), never a unilateral weakening. Cross-links `testing-and-evals.md`'s ratified assert-absent rule (the same shape). +1 eval (a correct `no-restricted-imports` layering gate "fixed" with `eslint-disable` → restructure via a service layer, don't suppress).
- Built by a worktree builder subagent, independently reviewed **PASS**: the mirror was confirmed genuinely absent (every near-miss read in full, including the closest sibling in `testing-and-evals.md` — distinct because it lacks the "find the design that satisfies both" reconciliation move); the `(principle 4)` citation verified verbatim against `SKILL.md`; the eval is grounded, uniquely-id'd, and append-only. Closes #443.

## [1.305.0] — 2026-09-20

### deep-code-review — serverless event-source correctness: recursive-invocation loops, partial-batch failure contract, and the visibility-timeout redelivery race

- **`infra-iac-containers.md`** new section "Serverless functions & event-source triggers": a recursive event-source invocation loop has **no call stack and no depth counter** — a function whose output targets the resource that triggers it (directly or transitively) self-amplifies, and the cycle lives in a **separate resource's trigger wiring in IaC**, invisible to a review that only reads the function body. Review action: draw the resource→trigger graph and check for a cycle; name the platform's **actual detection boundary** (e.g. AWS Lambda's on-by-default recursive-loop detection covers functions ↔ SQS/S3/SNS, only for a supported AWS SDK, stops at ~16 hops, and does **not** cover a DynamoDB-in-the-loop cycle) rather than assuming protection exists; break a confirmed cycle by routing the derived write to a resource the trigger ignores, filtering on a system-authored marker, or computing the value on read.
- **`domain-checklists.md` §W** new bullet: on a batch-triggered handler (queue/stream event source), the **platform — not the code — decides** whether the whole batch or only the failed items get retried/deleted; the per-item try/catch is necessary but not sufficient. Two opposite failures: catch-all + bare success → the platform deletes the whole batch (silent data loss); throw on any item → the platform redelivers the whole batch (double-processing). The fix needs **both** halves — a per-item failure list from the handler **and** the event-source-mapping config flag (AWS: `ReportBatchItemFailures`/`batchItemFailures`).
- **`reliability-error-handling.md`** new bullet: redelivery isn't only shutdown-/failure-triggered — a **slow-but-successful** invocation can lose the visibility-timeout race and be reprocessed by a second worker before it deletes the message, so the idempotent-processing requirement must hold against this non-failed concurrent duplicate too (distinct from the scheduler-level overlapping-run case).
- **`SKILL.md`** domain-L row now reads "Infra / IaC / containers / cloud / serverless".
- **`docs/standards-index.md`** +4 rows (AWS Lambda SQS error handling, Lambda-with-SQS, recursive-loop detection, SQS visibility timeout), all fetched + verified 2026-09-20. +2 evals.
- Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES: all four source URLs re-curled and every "verbatim" quote programmatically substring-checked (one truncated recursion quote extended to the full sentence); non-duplication confirmed against the existing DLQ/retry-cap bullet, the LLM-agent and GraphQL recursion sections, and the scheduler-overlap case; applied fixes — added the cycle-remediation clause and the supported-SDK precondition to the infra section (grounding the DynamoDB-stream eval), hedged the generic partial-batch mechanism claim to AWS-verified scope, fixed a circular cross-reference, and aligned the reliability bullet to the section's bold-lead house style.

## [1.304.0] — 2026-09-20

### deep-code-review — a normalization fix must hold at every query call site, not just build-side (closes #652)

- **`i18n-l10n.md`** new bullet in "Encoding & Unicode normalization": a normalization / case-fold fix applied only on the **write/index side** leaves any **query/lookup call site that normalizes differently (or not at all)** broken — the defect then presents as **missing data** (the row exists; this query doesn't reach it), so the write-side fix + backfill *looks* complete when it isn't. Reviewable property: the write path and **every** read/query path route through the **same shared normalizer**. Detection is **field-scoped, not pattern-scoped** — sweep every compare/filter/lookup against the normalized field (a lookup with *no* normalization at all is the same defect, and has no pattern to grep for). +1 eval. Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES (non-dup vs the normalize-before-compare anchor + case-fold bullet confirmed; field-scoped-not-pattern-scoped detection confirmed in both prose and eval; applied a precision fix — the anchor does name a pipeline stage, so the gap is "same normalizer across every call site," not "where it runs"). Closes #652.

## [1.303.0] — 2026-09-20

### deep-code-review — product-ux: dead-render candidate + empty-state stakes calibration (closes #554, #674)

- **`product-ux-quality.md`** two additions. **#554** — a component **exported and even unit-tested but with zero mount paths from any router/page entry** is a dead-render candidate; the default remedy flips to *wire it up* (retirement is an owner call, not a unilateral delete). Hedged: a static import trace is blind to `React.lazy()`/dynamic `import()`/a component registry/runtime route config, so a zero-entry result is a **candidate/`unverified`**, not a confirmed finding. Distinct from parallel-audit §5 (*which* live surface among candidates) and domain-H dead-code (reference-count — blind to a test-only import). **#674** — a low-stakes supplementary value may degrade a fetch failure to an empty render, but a value read as a **definitive claim** (audit log, security-events list, decision-bearing balance) must surface a **distinct, retryable error state** — narrowing #604(b)'s "cause-neutral empty" carve-out on a definitive-record surface. +2 evals. Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES (doctrine clean; applied: eval Panel-A "swallows"→"logs" to isolate the stakes-axis from domain-F's silent-swallow ban, corrected an "uncaught"→"discarded/caught" cross-ref, and added the candidate-not-confirmed hedge to the dead-render eval). Closes #554, closes #674.

## [1.302.0] — 2026-09-20

### deep-code-review — NoSQL / distributed-store consistency (conditional writes, stale reads, GSI lag, LWT mixing, batch limits)

- **`concurrency-shared-state.md`** new "NoSQL / distributed-store TOCTOU" subsection (distinct from the SQL DB/store TOCTOU section and from the in-process cross-replica-registry bullet): (1) **lost update with no conditional write** — a get-then-put with no conditional/optimistic clause silently clobbers; a single-item DynamoDB/Cassandra write has no `SELECT…FOR UPDATE`/`SERIALIZABLE` escalation path (MongoDB's multi-doc transaction is the costlier, time-capped exception, not a first-class default) — require DynamoDB `ConditionExpression` / Mongo filter-scoped `findOneAndUpdate` / Cassandra LWT `IF`; (2) **default-stale reads** — DynamoDB eventual-by-default (`ConsistentRead`), Cassandra CL `ONE`, Mongo readConcern `local`; (3) **GSI lag** — strongly-consistent reads from a global secondary index are *not supported* (no escape hatch); (4) Cassandra **LWT/non-LWT mixing** on one partition bypasses the guard; (5) **transaction/batch limits** vs assumed SQL-unlimited atomicity. Plus a **`performance-db-cost.md`** hot-partition bullet and a **`role-coverage.md`** cross-ref fixing the previously mechanism-less "Consistency model stated" line. 9 curl-verified `docs/standards-index.md` rows (AWS/DataStax/MongoDB, dated). +3 evals. Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES: all 9 quotes re-curled verbatim, R+W>N correctly omitted (no source), an advisor-caught wrong-mechanism Mongo citation removed pre-review; applied — scoped the "no escalation path" claim (Mongo's multi-doc txn *does* lock) and marked one elided GSI quote lead-in. Closes no filed issue (comparative research find).

## [1.301.0] — 2026-09-20

### agentic-delivery — fleet-coordination doctrine: delegate-merge-to-clean-worktree, stale-brief cohort fix, subagent-OOM back-off (closes #548, #666, #676)

- **`fast-agentic-delivery.md`** three doctrine additions. **#548** — the dirty-working-tree preflight (and its bypass flag) is *also* orchestrator-denied, compounding the classifier-denies-orchestrator asymmetry so a lane can land nothing; fix = **delegate the merge to a subagent in its own clean isolated worktree** (the preflight passes there, no bypass), + a sizing rule (amortize one clean-worktree lane across 2-3 small disjoint already-green PRs; defers train-vs-cascade authority to the cascade section). **#666** — correcting a fan-out **brief already dispatched to a cohort** is two actions (fix the template for future + enumerate/remediate the in-flight cohort, since an inlined brief has nothing left to poll), + a one-lane dry-run before fanning out N. **#676** — a subagent's own crash / low-memory / OOM report is a **first-class back-off trigger** even when the orchestrator's periodic probe reads fine (a probe samples steady-state, misses the peak concurrent heavy lanes hit). +3 evals (agentic-delivery suite 54 → 57). Built by a worktree builder subagent, independently reviewed PASS (advisor-caught + removed a duplicate laundering test pre-review; applied the one wording tweak "back-to-back" → "in sequence" to drop a merge-train vocabulary echo). Closes #548, closes #666, closes #676.

## [1.300.0] — 2026-09-20

### deep-code-review — a test that shells a real external binary must probe function + supply its own config (closes #678)

- **`testing-and-evals.md`** new bullet (after "Deterministic & hermetic"): a test invoking a real external binary (headless browser, `git`, `ffmpeg`, a DB CLI) must (1) gate on a **functional smoke** — the binary actually did the thing — and **skip loudly on any failure**, not a bare `which`/`command -v` presence check (CI is "present but different/broken," not absent: a headless browser crashes without an explicit sandbox setup; `git commit` fails with no configured identity), and (2) **supply its own required launch config** (`git -c user.email=… -c user.name=…` in its own temp repo; explicit browser launch flags) rather than inherit the runner's ambient state. Distinct from the network/DNS/clock/tmpdir hermeticity above, from test-double fidelity (a mock vs a live service — here a real binary behaving differently), and from the gate's cannot-check reporting rule. Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES: the git-identity claims were **empirically re-run** by both builder and reviewer (`git -c user.email= -c user.name= commit` → `fatal: empty ident name`, exit 128; the truly-unconfigured auto-guess case correctly left unasserted); applied a fix dropping `git --version` from the presence-only examples (it executes, unlike `which`/`command -v`). +1 eval. Closes #678.

## [1.299.0] — 2026-09-20

### deep-code-review — domain-checklists §H lockstep folds: generator/allow-list, shared-body-builder sweep, initials-family privacy (closes #649, #681, #682)

- **`domain-checklists.md`** §H ("copies that must stay in lockstep") gains three concrete recipes. **#649** — a hand-maintained allow-list of value combinations (e.g. `(kind, category)` pairs) is a generated-vs-source pair with its generator; diff the list against every combination the generator can emit (an emitted-but-omitted combo is silently dropped). **#681** — a shared request/mutation body-builder fix needs an all-callsite sweep + field-set diff (identical code, but caller-supplied *arguments* diverge — invisible to Phase 4's copy-idiom grep; this is the fix-time instance of the adapters clause, one-implementation-drifting-at-its-callers). **#682** — *two duplicated implementations* of a derived display value (avatar initials, short label, masked id) drift the same way; grep the name *family*, and when the canonical helper encodes a data-minimization cap, a divergent copy showing more is a **compliance gap**, not a style nit (cross-ref Q). Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES: #681-vs-Phase-4 distinctness confirmed at source; reworded #682's opener to break a "same-drift" parallelism that read as continuing #681, and broadened the allow-list framing past 2-tuples. +2 evals. Closes #649, closes #681, closes #682.

## [1.298.0] — 2026-09-20

### deep-code-review — streaming-transport reliability: reconnect jitter, cross-replica registry, gRPC keepalive/flow-control

- From a streaming-transport comparative pass (the WS/SSE section was already deep; these are the verified-absent deltas). **`api-contracts.md`** — (1) bounded reconnect backoff needs **jitter**: a server-side **mass-disconnect** (deploy/restart) drops every connection at one instant, synchronizing all clients' retry schedules → a re-storm on the server that just came back (distinct from one-caller retry jitter and from cache-key stampede); (2) **gRPC streaming** shares the WS/SSE reliability shapes — aggressive client keepalive on a sparse RPC gets the *sender* killed with `GOAWAY(too_many_pings)` when it outpaces the server's `PERMIT_KEEPALIVE_TIME` (the connecting `ping_strikes`/`MAX_PING_STRIKES` mechanism per gRPC proposal **A8**, curl-verified), and a bidi RPC where both ends write without reading can **deadlock** under manual flow control. **`concurrency-shared-state.md`** — an in-process socket/subscription registry (`Map<userId,socket>`) **silently drops delivery once the server is horizontally replicated** (publish on replica A never reaches a subscriber on replica B) — a wrong-answer bug (a `if(socket)` map-miss no-ops with no error), distinct from the single-process lifetime-mismatch bugs; fix = a shared pub/sub adapter or sticky routing. +3 evals. Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES (all quotes re-curled verbatim; applied: split the jitter comparison clause, source-neutral eval wording, added the A8 proposal as the source that connects ping-cadence→GOAWAY). Closes no filed issue (comparative research find).

## [1.297.0] — 2026-09-20

### deep-code-review — product-ux: capped-list remainder, empty-state cause-honesty, PR-body image visibility (closes #604, #568)

- **`product-ux-quality.md`** three additions. **#604(a)** — a capped/sliced list (`.slice(0,N)`/`LIMIT N`/`take(N)`) needs an explicit **remainder indicator** when `total > shown`; a correct top-line count doesn't prove the itemized list is complete. **#604(b)** — a hardcoded empty-state message that asserts a **cause** is a fabricated cause once `count===0` is reachable by more than one path (fetch error / permission denial / genuine empty); enumerate the paths, branch copy per cause or fall back to cause-neutral (distinct from the coverage-honesty rule — that asks whether the source was queried; this asks whether the stated cause is true on every path). **#568** — a PR-body `![](private-raw-host-url)` doesn't render for a cold reviewer (auth header a plain `<img>` can't send), and can break even for the author under cross-origin cookie scoping; gate on **visibility** (uploaded attachment / in-repo diff-able file), not presence. Pre-ship checklist + master grep-collector synced; gate numbering verified intact (4 files cite gates by number). Built by a worktree builder subagent, independently reviewed **PASS** (gate-numbering intact, no fabrication/vendor-naming, principle-2 cite resolves, non-duplication clean). +2 evals. Closes #604, closes #568.

## [1.296.0] — 2026-09-20

### deep-code-review — wave 217 change-detection gate must derive its diff base, not hardcode a release ref (closes #665)

- **`branch-and-merge-hygiene.md`** new bullet (in the "required check must be satisfiable" section): a **change-detection / path-filter** gate (a "did `app/` change? / did a migration touch?" step deciding whether a downstream job runs) must diff against the branch's **actual base** (`@{u}`, the PR's declared target, or a computed `<base>...HEAD` merge-base), never a **hardcoded release-branch constant**. A constant fails two ways: **loud** — the branch outruns the stale cut, the diff balloons, every push false-positives as "changed" (noise, not a correctness bug); **silent (dangerous)** — a literal ref that isn't present in a shallow/partial CI checkout (`fetch-depth: 1`) makes `git diff origin/release-v2...HEAD` **error**, and a naive `| grep -q` swallows the failure as "no match," so the job **skips** a real change with nothing red. Fix: derive the base at run time, ensure it's fetched, **fail closed** on an errored/unresolved base, and name the base diffed against. Built by a worktree builder subagent; independent reviewer **BLOCK** caught a git-mechanism error — the original claimed the *silent* skip came from the branch being *positionally behind* the ref (empirically false: three-dot/merge-base correctly reports downstream commits) — corrected to the ref-**resolvability** mechanism, git-repro-verified before merge. +1 eval. Closes #665.

## [1.295.0] — 2026-09-20

### deep-code-review — wave 216 data-quality: per-group ratio attribution + asymmetric percent guard (closes #686, #654)

- **`data-quality.md`** two additions. **#686** — a **per-group ratio** is wrong when the numerator counts a shared/ownerless entity via a broad **fan-out** rule but the denominator uses a **strict single-owner** rule for the same entity: the entity is charged to every group's numerator, counted in no group's denominator, inflating (or, for an all-shared group, undefining) every group's rate — a distortion no single-row check sees. Includes a hand-computed minimal proof (independently re-derived correct by the reviewer). Distinct from the existing "Denominator integrity" bullet (single-metric entity-type eligibility + test-traffic pollution). **#654** — a percent-unit guard that only rejects an unconverted 0-1 fraction (lower bound) is **asymmetric**: a value **above 1** (an attainment/ratio that can exceed 100%, or a double-`*100`) renders wrong with no error; extend the guard with an upper bound set by the metric's own semantics (no invented ceiling). Built by a worktree builder subagent, independently reviewed PASS-WITH-FIXES (arithmetic re-derived correct, non-duplication verified repo-wide; two Minor eval-wording fixes applied: failure-rate vs pass-rate label, "renders wrong" not "unrendered"). +2 evals. Closes #686, closes #654.

## [1.294.0] — 2026-09-20

### deep-code-review — wave 215 a11y landmarks & focus (closes #693, #662)

- **`frontend-a11y.md`** two additions. **#693** — an unnamed `<section>` is **not a poorly-labeled landmark, it is not a landmark at all**: HTML maps `<section>` to the ARIA `region` landmark **only when it carries an accessible name** (`aria-label` / `aria-labelledby` / `title` fallback), so an unnamed section vanishes from the landmark/rotor navigation; sibling sections from one component drift on this because the visual output never shows the gap (verified vs MDN + W3C accname). **#662** — restore-focus-to-the-trigger is **not modal-only**: it applies to every dismissible overlay (popover, dropdown/menu, combobox listbox, flyout, click-tooltip); the tell is a bare boolean open state with an Escape/outside-click dismiss handler and **no `.focus()` back to the trigger**, dumping focus to `<body>` (verified vs ARIA APG menu pattern). Built by a worktree builder subagent, independently reviewed **PASS** (both claims confirmed at authoritative source; non-duplication clean repo-wide; no fabricated SC number). +2 evals. Closes #693, closes #662.

## [1.293.0] — 2026-09-20

### deep-code-review — wave 214 classify a DIFF's hunks by kind (mechanical / behavioral / new-surface) → matched review depth

- **`method.md`** Phase 2 gains a DIFF-scope triage step: **the PR's title and line-count are not the review's depth budget.** Bucket each changed hunk into **mechanical** (rename, format-only reflow), **behavioral** (logic changed on an existing path), or **new-surface** (a brand-new route/endpoint/handler/consumer/permission — a new trust boundary), and route each at matched depth — a mechanical hunk gets a fast *confirm-it-is-mechanical* read (no moved guard / flipped default / widened type rode in on the rename), a behavioral hunk the full domain audit, and a **new-surface hunk the full Phase 3 adversarial opener set (every opener, not a subset) regardless of the PR's stated size or title** — a new endpoint buried in a PR titled "refactor" is the highest-risk change and the easiest to wave through. A hunk fitting none cleanly defaults to the behavioral read. Distinct from Phase 0's blast-radius *ordering* (which ranks what to review *first*; this sets *depth*). +2 evals. From the competitor-tool comparison (CodeRabbit "Change Stack"). Independent reviewer PASS-WITH-FIXES: cross-referenced the Phase 3 opener list instead of re-enumerating a subset (the original dropped the dual-surface caller check — the one the eval's export example most needs), removed the dependency-bump from the "mechanical" bucket (its risk is off-diff in the changelog, so the mechanical clearing read can't clear it), and added the behavioral default. Closes no filed issue (comparative research find).

## [1.292.0] — 2026-09-20

### deep-code-review — wave 213 self-audit cleanup-B: de-duplicate two restated passages

- The self-audit found two concepts each stated **in full in two places** (the repo's thesis forbids duplicated logic — state once, link elsewhere). Both non-canonical copies trimmed to a short pointer, no meaning lost (each canonical home verified to retain the full mechanism): the **`for x in $LIST` word-splitting footgun** in `language-stack-redflags.md` now points to its fuller home in `branch-and-merge-hygiene.md` §6; the **escalate-on-failure model-tiering** paragraph in `parallel-audit.md` keeps the actionable prescription and points to `model-tiering.md` for the "same pass rate, ~half the cost" claim + tier definitions. Independent reviewer PASS-WITH-FIXES: the trim dropped the "rate-limit headroom" rationale, which had no canonical home — restored it to `model-tiering.md`'s escalate-on-failure lever (its natural fan-out/provider-quota home, distinct from the dollar-cost point). No eval change. Closes no filed issue (internal self-audit).

## [1.291.0] — 2026-09-20

### deep-code-review — wave 212 CSRF guard-coverage + admit-secret strength (closes #579, #671)

- **`security-appsec.md`** two additions. **#579** — a new "🚩 A CSRF guard on one route is not a guard on the class" flag beside the existing CSRF-≠-authn flag: (a) when a CSRF token / double-submit / `Origin` check exists, **grep every cookie-authenticated *mutating* route** and confirm the guard is on **all** of them (a guard bolted onto the one route an incident exposed leaves siblings open — the Phase-4 full-instance-set scoping); (b) **verify the shared body parser requires `Content-Type: application/json`** — a parser also accepting `text/plain` / `x-www-form-urlencoded` / `multipart/form-data` is reachable by **HTML-form-to-JSON CSRF** (a cross-site `<form>` sends exactly those three enctypes with no CORS preflight, since the form-enctype set and the CORS-safelisted Content-Type set are identical by design). **#671** — a static secret used as an **admit** gate (API key / webhook key / admin token) needs an enforced **length/entropy floor at the point of use**, a property separate from constant-time compare (a short/low-entropy secret is brute-forceable however the compare is written); enforce at load and fail closed; admit-direction weakness outranks exclude-direction; detect by grepping the floor, not the secret's name. +2 evals. Independent reviewer PASS-WITH-FIXES: the form-to-JSON-CSRF mechanism verified accurate against the Fetch/WHATWG + HTML specs; applied a one-word scoping fix ("exclude filter" → "exclude secret"). Closes #579, closes #671.

## [1.290.0] — 2026-09-20

### deep-code-review — wave 211 AI-app quality (RAG context-assembly, LLM-judge bias, vector distance-metric)

- Three folds from an AI-application-engineering comparative pass, all verified absent at source. **`testing-and-evals.md`** (a) **RAG context-assembly seam** — beyond the retrieval-quality seam already covered: budget the prompt with the model's **actual tokenizer** (not char/word count); on overflow **drop whole lowest-ranked chunks, never truncate mid-content** (a mid-cut fact/citation the model then completes or misattributes); and place a needed-but-not-#1 chunk at the **start or end**, not buried mid-concatenation ("Lost in the Middle," Liu et al. 2023) — distinct from a long-running agent's compaction and from an output `max_tokens` cap. (b) **LLM-judge bias tests** — beyond temperature-0 and a frozen human-labeled cohort: an **order-swap** consistency check (positional bias, two calls, zero labels), a **self-preference** flag when judge and subject share a model/vendor family, a **verbosity-correlation** check, and re-validating the agreement threshold when the judge model version changes (position/verbosity/self-enhancement biases: Zheng et al. 2023). **`data-quality.md`** §12 — the vector-index contract includes the **distance metric + normalization** (cosine and dot-product agree on ranking only for unit-normalized vectors; an index built for one metric and queried under another silently reorders neighbours), added to the red-flag line. +2 evals. Independent reviewer PASS-WITH-FIXES (all Low/Nit, applied): re-verified both paper citations at arXiv (accurate, not fabricated); corrected the cosine-normalization phrasing; disambiguated the chunk-placement wording; cued the output-cap distinction in the eval prompt; marked the ≥80%-agreement figure a bonus. Closes no filed issue (comparative research find).

## [1.289.0] — 2026-09-20

### deep-code-review — wave 210 self-audit cleanup: principle-7 self-contradiction + a fabricated principle cite

- A dogfood self-audit (Perun run on its own tree) found two principle-citation defects, both fixed here. **Principle 7 self-contradiction:** `SKILL.md` principle 7 read "The **one** unprompted mutation is Phase 1's transient planted probe…", but three sites now license an unprompted worktree mutation under principle 7 (Phase 1's planted-defect probe, Phase 3's discovery probe-test [added in wave 207], Phase 4's fix-against-suite check). Reworded to name the **class** — "Unprompted mutation is confined to transient dedicated-worktree probes, **each reverted or deleted and confirmed**" (byte-neutral) — and aligned `method.md`'s "the one code mutation" phrasing; `parallel-audit.md`'s fix-against-suite step gained the disposal clause the class now requires (reviewer's Low finding). **Fabricated principle cite:** `dependency-currency-and-upgrades.md`'s "Bounded and reversible (`SKILL.md` principle 5)" — principle 5 is "Respect the existing design"; no numbered principle covers bounded/reversible (it's from a different document) — dropped the false attribution, the rule stands standalone. Independent reviewer PASS-WITH-FIXES (the one Low finding applied). No eval change (correctness fix to existing content). Closes no filed issue (internal self-audit).

## [1.288.0] — 2026-09-20

### agentic-delivery — wave 209 fleet coordination honesty (claim freshness/staleness #596 + commit attribution trailer #660)

- **`fast-agentic-delivery.md`** two additions to the multi-agent-coordination section. **#596 claim staleness:** the existing text said to "check for liveness" and "reconcile the dead lane" but never defined *when* a claim is dead — a **claim/ownership record** whose last progress predates a stated **staleness threshold** is treated as dead and reconciled (cheap, reversible), so a crashed lane's leftover claim doesn't lock its objective forever; declaring a *running lane* dead stays the higher bar (needs a positive actual-product signal, never elapsed time alone — killing a live lane is destructive). **#660 attribution:** a commit/PR co-author trailer must name the **real executing agent/model** per lane — a shared template that hardcodes one model name makes the history misattribute lanes that ran on a different model; parameterize the trailer or let each lane stamp its own identity. +2 evals (agentic-delivery suite 52 → 54). Independent reviewer PASS-WITH-FIXES: trimmed #596's opening clause that re-derived the already-linked transcript-is-not-liveness rule, drew the claim-record-vs-live-lane distinction so the threshold isn't over-applied to a kill decision, softened the #660 `deep-code-review` cross-ref to a failure-mode (not an asserted named class), and tightened the stale-claim eval (removed a prompt giveaway; split the live-claim-left-alone check into its own gradeable expectation). Closes #596, closes #660.

## [1.287.0] — 2026-09-20

### deep-code-review — wave 208 telemetry carries a stable resource identity (service/version/environment)

- **`observability.md`** new bullet in the correlation-id/trace family: every emitted signal should stamp a stable **resource identity** — *which service, version, and instance* produced it and *which environment/tier* — via the OpenTelemetry resource attributes `service.name`/`service.version`/`service.instance.id`/`service.namespace` and `deployment.environment.name` (all **Stable**), or an equivalent version+environment dimension. Without it, two things the skill already demands quietly break: a **canary's named halt metric** (`release-engineering.md`) is uncomputable as canary-vs-baseline unless telemetry is partitioned by `service.version`/cohort; and **multi-window burn-rate SLO math** (`role-coverage.md`) corrupts when environments collide in one backend — which is the **default**, since per the OTel spec `deployment.environment.name` "does not affect the uniqueness constraints" so `service.name=frontend` in prod and staging "MUST be considered to be identifying the same service." **`release-engineering.md`** canary bullet gains a partition-by-cohort clause. Two dated `docs/standards-index.md` rows (OTel service + deployment attributes, curl-verified 2026-09-20). +2 evals. Independent reviewer PASS-WITH-FIXES: dropped an unverified "gen_ai.* is Development" comparison (the gen_ai conventions were in fact **moved to a separate repo / marked Deprecated** — also corrected the same stale claim pre-existing at `observability.md`'s GenAI bullet), and made the OTel-citation in one eval sufficient-but-not-necessary. Closes no filed issue (comparative research find).

## [1.286.0] — 2026-09-20

### deep-code-review — wave 207 author a disposable probe test to *discover* an unsuspected bug (Phase 3)

- **`method.md`** new Phase 3 paragraph: beyond the security openers, **author a minimal, disposable test to discover an unsuspected defect in changed correctness-bearing logic no existing test reaches** — distinct from Phase 1's planted-defect probe (which proves a *gate* catches a *known* injected defect), Phase 4 fix-verification (which runs the *existing* suite against a *suspected* finding), and the Phase 3 security openers (which attack a *running* surface). RED = a finding with a real repro attached; **GREEN is only "no defect at the inputs probed"** (record the probe + inputs), promoted to a `checked_sound` / *Invariants verified to hold* row only if it pins the property across the input class, not one example. **Blast-radius bound:** the throwaway worktree contains *filesystem* effects, not *outbound* ones — a paid/network/stateful unit is **stubbed or skipped** and recorded `could-not-check` (distinct from found-nothing), never fired for a result. The probe reuses the same transient-worktree-probe mechanism principle 7 already permits and is **deleted with its removal confirmed** (as Phase 1 reverts-and-confirms), so no unprompted write is left standing. +2 evals. Independent reviewer PASS-WITH-FIXES: corrected a fabricated "principle 5 spend bound" cite (no such numbered principle — grounded in the real unnumbered confirm-before-billable rule; the fix reached two eval loci), aligned the could-not-check idiom to *found-nothing*, operationalized the probe teardown, and marked the eval's boundary-bug list illustrative. Closes no filed issue (competitor-comparison method gap).

## [1.285.0] — 2026-09-20

### deep-code-review — wave 206 delivering & defending a finding (review tone + author-pushback hold-or-concede loop)

- **`report-format.md`** new section **"Delivering & defending findings — tone, and handling pushback."** Two rules the method had implied but never stated for the human-facing side of a review. (1) *Comment on the code, not the author* — state the defect, its impact, and the smallest fix; severity rates **consequence, not blame**; a Blocker is a claim about the code's risk, not an accusation; reserve directive language for a real defect and label a nit so it can't read as a gate (register, not vocabulary — `communication-structure` still governs shape/length). (2) *When the author disputes a filed finding, run a hold-or-concede loop — neither cave nor dig in:* genuinely re-weigh and **drop it if the author is right** (the same base-ref test as `method.md`'s pre-filing `REFUTED`, now applied after the finding shipped); else **restate with more evidence and hold the severity** (a real Blocker doesn't decay to a Nit under pressure); stay civil; if deadlocked, **escalate to a named path and record the resolution** so a later reader sees why. Reflexive concession and reflexive digging-in are named as co-equal failures. **`SKILL.md`** routing for `report-format.md` widened to trigger on "an author disputes a filed finding," not only Phase 5. +2 evals. Independent reviewer PASS-WITH-FIXES (applied: precise "pre-filing `REFUTED`, now applied after the finding shipped" qualifier; de-telegraphed the pushback eval prompt). Closes no filed issue (review-method comparative pass).

## [1.284.0] — 2026-09-20

### deep-code-review — wave 205 WCAG 2.2 Accessible Authentication (3.3.8 password-manager support + 3.3.9 Enhanced)

- **`frontend-a11y.md`** SC 3.3.8 Accessible Authentication (AA): the bullet now covers the **Mechanism** exception in full — a password manager is the canonical mechanism, so allow **paste** into password/OTP fields, set correct `autocomplete` tokens (`current-password`/`new-password`/`one-time-code`), and don't intercept clipboard events — not merely "no puzzle." Names SC **3.3.9 (Enhanced, AAA)**, which drops the object-recognition and personal-content exceptions, so an image CAPTCHA passes 3.3.8 but **fails 3.3.9** (hold high-stakes banking/health auth to it). Curl-verified `docs/standards-index.md` rows for 3.3.8 + 3.3.9 added (fetched 2026-09-20). +2 evals. Independent reviewer PASS-WITH-FIXES: dropped an unsourced "browser vendors reject it" clause (kept the WCAG-backed point). Closes no filed issue (WCAG 2.2 comparative pass).

## [1.283.0] — 2026-09-20

### deep-code-review — wave 204 web cache poisoning via an unkeyed input that shapes the cached body (A01)

- **`security-appsec.md`** A01 "Cache / CDN is an authorization surface" — new paragraph on the poisoning direction (mirror of the identity-leak already there): an attacker-controllable request component that shapes the response body but is **not part of the cache key** — a reflected header (`X-Forwarded-Host`/`X-Forwarded-Scheme`) or a routing-override header (`X-Original-URL`), an echoed param, a `Vary`-absent header — is cached under the normal URL and served to **every** subsequent visitor, turning a *reflected* XSS/open-redirect/script-src into a **stored, mass-distributed** one. Census the cache key against every response-affecting input; **prefer stripping/normalizing at the edge** over keying on an attacker-settable header (which risks cache-key cardinality blowup); never reflect an unkeyed header into a cacheable response. + 🚩 grep. +1 eval. From a caching-correctness comparative pass (leak/stampede/invalidation/negative-caching already covered; poisoning was the one gap). Independent reviewer PASS + applied fixes (X-Original-URL is routing-override not reflected; strip-preference). Closes no filed issue.

## [1.282.0] — 2026-09-20

### deep-code-review — wave 203 WCAG 2.2 Target Size exceptions + a stale LLM-ID cross-ref fix

- **`frontend-a11y.md`** SC 2.5.8 Target Size (Minimum): the 24×24 CSS px bullet now names the **five exceptions** — Spacing (a 24px-diameter circle centred on each undersized target doesn't intersect another's), Equivalent (another control does the function at size), Inline (a target within a sentence, or sized by non-target line-height), user-agent-controlled, and essential — so a review doesn't over-flag exempt inline links or spaced icons. Curl-verified `docs/standards-index.md` row added (SC 2.5.8, fetched 2026-09-20). +1 eval.
- **`model-tiering.md`** cross-ref fix (from the cross-reference integrity self-audit): the `security-ai-agents.md` pointer named "LLM10 Unbounded Consumption" (the pre-2026 ID); that file migrated to the OWASP LLM Top 10 **2026** edition where Unbounded Consumption is **LLM06:2026** (LLM10:2026 is now Improper Output Handling). Corrected to match the repo's `LLM0N:2026` convention. Closes no filed issue.

## [1.281.0] — 2026-09-20

### deep-code-review — wave 202 path traversal on the file serve/download read path (CWE-22)

- **`security-appsec.md`** ("Files, archives & parsers"): serving or downloading a file by a user-supplied path is the same CWE-22 as zip-slip on the read side — `BASE_DIR + name` / `send_file(request path)` / `res.sendFile(req path)` lets `../`, an absolute path, or an escaping symlink read arbitrary files. Fix: resolve to a **canonical `realpath` (symlink-following — a lexical `path.resolve` alone misses a symlink escape)** and verify it is a **true subpath** of the base — compare against base **plus its trailing separator** (a bare `startsWith('/base')` also matches `/base-evil`), reject absolute overrides and escaping symlinks; a bare `../` denylist is bypassable (`%2e%2e`, `....//`). +1 eval. Independent reviewer PASS-WITH-FIXES: added the `/base`-vs-`/base-evil` trailing-separator/subpath caveat and the realpath-vs-lexical-resolve symlink distinction (both prose + eval). Closes no filed issue (CWE Top 25 comparative pass; rank-5 PARTIAL — only zip-slip + PHP LFI were covered).

## [1.280.0] — 2026-09-20

### deep-code-review — wave 201 WCAG 2.2 precision: Consistent Help is order-not-location; Focus Appearance has an area prong

- **`frontend-a11y.md`** aligns two WCAG 2.2 SC bullets to the skill's own already-verified `docs/standards-index.md` rows: **3.2.6 Consistent Help** is the *relative order* of repeated help mechanisms in the content, not pixel/visual location (corrects the prior "consistent location" wording); **2.4.13 Focus Appearance** (AAA) requires **both** an area >= a 2 CSS px thick perimeter of the unfocused component (or sub-component) **and** >=3:1 focused/unfocused contrast — a 1px ring that clears contrast still fails the area prong. +2 evals. Independent reviewer PASS-WITH-FIXES: completed the "unfocused component (or sub-component)" quote and tightened the eval's area-vs-thickness reasoning. Closes no filed issue (WCAG 2.2 comparative pass; backed by existing verified standards-index rows).

## [1.279.0] — 2026-09-20

### deep-code-review — wave 200 review-method dedup: filed findings must dedupe against recently-closed issues, not only open

- **`method.md`** Phase 4 (Synthesize & rank): when a review files its findings as tracked issues, dedup against recently-**closed** issues, not only open ones — a finding matching a recently-closed issue may already be fixed, so re-filing re-lanes shipped work and erodes tracker trust; search closed issues by symbol/symptom before filing. Caveat: a `wontfix`/`duplicate`/`stale`/bot-triage close is **not** a fix — check the close reason, and if the finding still reproduces at HEAD (the Phase 1 re-validate-`file:line`-exists check), file it anyway rather than suppress a live defect. +1 eval. Independent reviewer PASS-WITH-FIXES: resolved a dangling backstop cross-ref to the actual Phase 1 rule, and added the closed-is-not-fixed nuance (fail-closed). Closes #657.

## [1.278.0] — 2026-09-20

### deep-code-review — wave 199 testing depth: test-double fidelity, consumer-driven contract testing, flaky-test quarantine (from a testing-practice comparative pass)

- **`testing-and-evals.md`** — (1) a **test double must not drift from what the real dependency returns**: a mock/stub returning a shape, null-vs-empty, status, or error the live dependency never produces leaves the suite green while the integration is broken (the classic "all tests pass, prod is down"); verify the double against the real contract (a contract test run against both real+double, a recorded interaction/VCR, or provider-generated types). (2) A **chronically flaky test is quarantined and fixed, not retried-until-green** — a blanket CI retry masks a real race and lets a genuine intermittent regression slip through; move it to non-blocking quarantine with an owner + fix deadline, fix the root nondeterminism (a bounded retry on a genuinely external flake, with the rate tracked, is not the finding).
- **`api-contracts.md`** — **consumer-driven contract testing** (e.g. Pact) catches what a provider-vs-self surface diff (`oasdiff`/`buf`) can't: the consumer publishes its real expectations, the provider replays/verifies them in its own CI, and a broker `can-i-deploy` gate blocks the break before production. Resolves the previously-dangling `(consumer-driven contract)` cross-ref from `data-quality.md`.
- +3 evals. Independent reviewer PASS-WITH-FIXES: softened an unhedged "most common" frequency superlative to "the classic" (matching the eval + repo idiom); citation-provenance confirmed clean (patterns named like the file's own `pytest-randomly`/`oasdiff` precedent — no standards-index row). Closes no filed issue (proactive coverage from a testing-practice diff).

## [1.277.0] — 2026-09-20

### deep-code-review — wave 198 observability: toil is reviewable, SLI measurement-point blind spot, saturation target below 100% (from a Google SRE comparative pass)

- **`role-coverage.md`** — (1) the "Toil & rollback" bullet, previously all rollback, now names **toil as a reviewable signal**: a page whose documented response is a scripted, judgment-free runbook step is toil wearing an alert's clothes — automate the response or demote it to a ticket (a human is not a cron); adding on-call headcount spreads toil, it doesn't remove it. (2) The SLI bullet: **where** an SLI is measured is itself a blind spot — server-side metrics can read all-green while client-side rendering/JS breaks the real experience; use a client-perceived signal (RUM / field data, `frontend-a11y.md`'s CrUX / Core Web Vitals lens).
- **`observability.md`** Golden signals — saturation's alert line is a utilization **target below 100%** (systems degrade before full; ~70-80% workload-dependent), tracked per constrained resource, and the target is itself a *cause* alert to pair with a user-facing *symptom* alert. +2 evals. Independent reviewer PASS-WITH-FIXES: dropped a "USE method" name-drop that lacked a standards-index entry (kept the substance), added the cause/symptom-pairing clause, and de-leaked + tightened the saturation eval. Closes no filed issue (proactive coverage from a Google SRE diff).

## [1.276.0] — 2026-09-20

### deep-code-review — wave 197 an `or`/`||` fallback chain over JSON/config fields drops a legitimate falsy value

- **`language-stack-redflags.md`** Python and JavaScript sections: `a or b or default` (Python) / `a || b || default` (JS) over decoded JSON/config skips a legitimately-present **falsy** value — Python `0`/`False`/`""`/`[]`/`{}`; JS `0`/`false`/`""`/`NaN` — and falls through to the next fallback, so the chain can't tell "not set" from "set to a falsy value" (a user's explicit `timeout: 0` is silently ignored). Resolve by **presence, not truthiness**: a presence/`is not None` check in Python, `??` (nullish coalescing, which falls back only on `null`/`undefined`) in JS; test with a falsy-but-present value. +1 eval. Independent reviewer PASS (both languages' falsy sets empirically verified; applied a nit scoping the eval's falsy-value list per language). Closes #650.

## [1.275.0] — 2026-09-20

### deep-code-review — wave 196 Kubernetes Pod Security hardening (from a Pod Security Standards comparative pass)

- **`infra-iac-containers.md`** Kubernetes section, from a comparative pass vs the Kubernetes Pod Security Standards: (1) **`automountServiceAccountToken: false`** on any ServiceAccount/Pod that never calls the API server — the token mounts by default, so an unused one is a free credential an in-pod compromise inherits, and being a *missing* field no bad-value grep catches it; (2) name the built-in **Pod Security Admission** enforcer (`pod-security.kubernetes.io/enforce: restricted` namespace label) alongside OPA-Gatekeeper/Kyverno (policy engines are for rules beyond the built-in Baseline/Restricted profiles); (3) tightened the pod-security bullet — **drop `ALL`** capabilities (Restricted permits only `NET_BIND_SERVICE` back), seccomp **`RuntimeDefault`/`Localhost`** (`Unconfined` or absent is the finding), and `hostIPC` added to the host-namespace list + 🚩 grep. +2 evals. Sourced from kubernetes.io Pod Security Standards / Security Context / ServiceAccount docs (no CIS/NSA control numbers — those sources were not fetchable). Independent reviewer PASS-WITH-FIXES: split a joined grep code-span, corrected a cross-ref, named the one permitted capability.

## [1.274.0] — 2026-09-20

### deep-code-review — wave 195 DB/store TOCTOU: an idempotency short-circuit must diff real state; a CAS must guard the decision's fields, not just status

- **`concurrency-shared-state.md`** §DB/store TOCTOU, two new bullets. (1) An idempotency / no-op short-circuit (`apply(current, next)` skips when equal) is only correct if `current` is the store's **real** state — a DB adapter that passes an empty array / `{}` / a fabricated blank as `current` defeats it: every apply looks changed, re-writing rows and re-firing events/webhooks each run. Load the real current rows before the diff; test the DB path with a **pre-seeded** existing value (an empty-baseline in-memory test passes while the DB path is broken). (2) A CAS/version guard must cover the field the decision **depends on** — a guard on the state column only (`WHERE status='approved'`) still races if the decision also read an independently-mutable field (`amount`, `approved_by`, an evidence column) another writer can change between the read and the CAS; the CAS passes, the action fires on stale inputs. Guard every consumed field — a whole-row version/`updated_at` CAS, or re-read and compare under the same lock. +2 evals. Independent reviewer PASS-WITH-FIXES: removed a self-contradictory parenthetical (a whole-row version CAS is a *valid* guard — the flaw is a state-column-only guard, now stated as such). Closes #642, closes #647.

## [1.273.0] — 2026-09-20

### agentic-delivery — wave 194 issue-lifecycle discipline: read comments before laning, verify every acceptance criterion before closing

- **`fast-agentic-delivery.md`** two additions. (1) Before opening a fix lane, read the issue's **comments**, not just its title/body/labels — a later owner comment (an A/B decision, a narrowed scope, a "defer this," a "superseded by #M") outranks the body, and buildability/priority often live only there; classifying from body + labels alone re-opens a lane the owner already redirected. (2) New section: before a manual or agentic `gh issue close` (or a `Closes #N`), enumerate **every** acceptance criterion and verify each independently against the merged source — a `file:line` receipt per criterion, not one representative check the rest ride on; a multi-criterion issue closed on one silently drops the others (neither open nor done). Leave open with a named per-criterion gap otherwise, or split; and criterion-verification settles *whether* to close, not *when* ("done" still means merged to the default branch). +2 evals (agentic-delivery suite). Independent reviewer PASS-WITH-FIXES: replaced a coined cross-ref phrase with the review method's actual *Intent-conformance* lens and cross-linked the close-side rule back to the default-branch condition. Closes #611, closes #622.

## [1.272.0] — 2026-09-20

### deep-code-review — wave 193 data-quality idempotency: a dedup key over a truncated slug collides; a dual-registered entity's write target is per-field

- **`data-quality.md`** §6, two new bullets. (1) A dedup/idempotency key must hash the **full** content, not a truncated display slug — an id like `slug(source, key, text.slice(0,N))` collides for any two payloads sharing the first N characters, so if it gates a dedup/idempotency upsert the second is silently dropped or overwrites the first; keep the readable slug and the collision-resistant key separate, and test two inputs differing only past the cut. (2) A dual-registered entity (a legacy CSV/row + a newer per-entity file/record) has one write target **per field** — the store the read/compile path treats as authoritative for that field; writing the other store makes the edit a silent no-op, writing both without precedence drifts. Both carry 🚩 red-flag entries and cross-ref §5's artifact→consumer census and the dual-write family. +2 evals. Independent reviewer PASS-WITH-FIXES: added the two 🚩 rollup clauses, widened the #648 cross-ref neighborhood (§5 field-granularity + dual-write family), and tightened the dual-registered eval so its first expectation requires diagnosis rather than restating the prompt. Closes #653, closes #648.

## [1.271.0] — 2026-09-20

### deep-code-review — wave 192 retry/idempotency error-handling: success-scoped existence checks and a "never throws" function's coverage

- **`reliability-error-handling.md`** two new bullets. (1) An idempotent-retry "did a prior attempt already do this?" existence check must match only terminal-**success** records — a status-agnostic lookup (`state=all` / any row with the key) also matches a reverted, cancelled, or failed prior attempt (a closed-not-merged PR, a cancelled-not-fulfilled order) and misreports the work as done, so the retry silently skips real work; filter by success status and test against a key whose only prior record is non-success. (2) A "never throws" function is only as safe as its coverage: a decode/parse (`decodeURIComponent`, `JSON.parse`, `atob`, `new URL()`) in a `.map` callback, a default-argument expression, or any statement outside the guarded block throws *past* the contract and crashes trusting callers; wrap each decode/parse in its own try/catch or prove it sits inside the outer one, and test malformed input per call. +2 evals. Independent reviewer PASS (both mechanisms reproduced empirically). Closes #643, closes #645.

## [1.270.0] — 2026-09-20

### deep-code-review — wave 191 an LLM self-report boolean gated with a loose comparison fails open

- **`security-ai-agents.md`** Defensive patterns: a model's self-report boolean is untrusted input. A **negated** comparison `if (res.safe !== false)` takes the permissive branch for everything except the boolean `false` — an omitted field, `null`, a wrong-typed `"false"`/`0`, or a failed parse all pass, exactly the outputs a hallucinating/prompt-injected/truncated model produces (and bare truthiness `if (res.safe)` is the *inverse* footgun: fails closed on `null`/`0`/omitted but open on truthy junk like the string `"false"`). Require the field present and boolean, demand an explicit `=== true` for the permissive branch, fail closed otherwise; and a model self-grading its own output must corroborate a deterministic check, never replace it — self-reported evidence is not a trusted control (cross-ref `data-quality.md` §7, `branch-and-merge-hygiene.md`, `model-tiering.md`). +1 eval. Independent reviewer PASS-WITH-FIXES: corrected the fail-open scope (the negated comparison, not bare truthiness — which has the inverse hole) and added the self-report-evidence cross-refs. Closes #644.

## [1.269.0] — 2026-09-20

### deep-code-review — wave 190 startup dependency-readiness: gate readiness and retry at boot instead of crash-looping

- **`reliability-error-handling.md`** new bullet in the disposability cluster (startup as the mirror of shutdown): a service must not report ready until its critical dependencies (DB, cache, broker, downstream) are actually reachable, and must retry connecting with bounded backoff rather than `exit(1)` on the first failure — otherwise a transient blip or a deploy-ordering race becomes a self-inflicted CrashLoopBackOff. *Bounded* means **capped and observable**: retry a dependency that is merely *not yet up*, but **escalate/alert** on one that is *definitively broken* (rejected credentials, unresolvable host, invalid config) rather than retry silently forever — an uncapped silent loop just trades a visible CrashLoopBackOff for a pod stuck **Running but never Ready** — and emit a log/metric on each failed attempt. Keep liveness separate from readiness (a `startupProbe` gives a slow boot its own budget); don't assume strict cross-service start-order.
- +1 eval (a DB-at-boot `exit(1)` plus an always-200 readiness probe → CrashLoopBackOff). Independent reviewer PASS-WITH-FIXES, all applied: taught the transient-vs-definitively-broken distinction with a cap/escalation and a per-attempt log/metric (so the skill now backs the eval's gold answer and stays consistent with the file's own "retry-forever is a finding" rule); rewrapped an over-long red-flag line; de-framed an eval expectation to check substance rather than the "mirror" phrasing; named `startupProbe` for symmetry with the shutdown paragraph.

## [1.268.0] — 2026-09-20

### deep-code-review — wave 189 dated overflows & disk-full: epoch/field-width time-bombs and unreaped on-disk stores

- **`time-date-correctness.md`** new **Epoch & field-width limits** section: a stored time value has a fixed bit-width capacity, and outgrowing it is a *dated, scheduled* failure — not a present-tense non-issue. A signed 32-bit `time_t` overflows at **2038-01-19T03:14:07Z** (Year 2038) and wraps negative — still live in 32-bit builds, embedded targets, and on-disk/wire formats; a millisecond epoch stored in a 32-bit int overflows in ~3.5 weeks; a too-narrow date/year field (2-digit year, undersized column) carries its own dated ceiling. Distinct from the calendar-arithmetic and monotonic-clock concerns in *Durations*, and from the 2^53 JSON-number-precision limit (a floating-point safe-integer range, not an epoch bit-width).
- **`performance-db-cost.md`** new bullet under *Concurrency, memory & payloads*: every append-only store **on disk** names a reaper — logs, temp/scratch files, an audit/event table, a dead-letter queue, a metrics/trace store, or an on-disk artifact directory that only grows will eventually fill the disk and take the whole host down (a slow-motion, time-triggered outage no single request reveals). For each: a retention/rotation policy with an actual reaper (size+age cap; TTL/partition-drop; DLQ trim with depth alerting; crash-path temp cleanup) plus a disk-headroom alert *ahead of* full. Explicitly distinct from the in-memory-growth bullet above.
- +2 evals (each baits the "it works fine today" / "there's plenty of disk today" dismissal and requires rebutting it as a scheduled failure). Independent reviewer PASS; applied the reviewer's optional clarity clause distinguishing the on-disk artifact directory from the in-memory/Redis cache already covered above.

## [1.267.0] — 2026-09-20

### deep-code-review — wave 188 vector-index correctness: embedding model-version mismatch & staleness

- **`data-quality.md`** §12: a vector index is a derived dataset whose **embedding model + version** is part of its contract. Vectors from two models/versions occupy different latent spaces, so cross-version similarity is meaningless — and if both are the **same dimension** there is **no error**, just silently wrong nearest-neighbours (a different dimension is the loud case a typed `vector(n)` column rejects). (a) A mixed-version index (incremental re-embed) → re-embed the whole corpus + atomic swap, pin the query to the index's model+version, tag vectors with version. (b) A stale index (source changed, not re-embedded) → re-embed-on-source-change + a freshness/version gate. The **correctness** face — distinct from the security face (LLM09) and the cost face (don't re-embed unchanged, §11).
- +2 evals + a red-flag entry. Independent reviewer PASS-WITH-FIXES: moved the bullet ahead of the section separator so it doesn't absorb the master red-flag rollup (a CommonMark do-no-harm fix), dropped an unverifiable OpenAI-guide attribution (kept the fetch-verified `pgvector` behaviour), and qualified pgvector's dimensionality rule to a typed `vector(n)` column.

## [1.266.0] — 2026-09-20

### deep-code-review — wave 187 credential/cert expiry lifecycle: an unmonitored expiring secret is a scheduled outage

- **`security-appsec.md`** (Secrets, cross-cutting): anything with an expiry — TLS certs, code/JWT-signing keys, API tokens, OAuth client secrets, DB passwords, cloud access keys, domains — needs an **inventory** (expiry + owner), an **ahead-of-time alert** (lead time / synthetic check, not on the outage), and **automated renewal/rotation before expiry** (ACME/cert-manager for TLS; a rotation job with an **overlap window** for secrets/keys). A lapse in prod is a total, time-triggered outage (the classic midnight cert expiry). Distinct from rotating a *leaked* secret (same section) and validating a *request* token's `exp` (A07) — this is the operational lifecycle.
- +1 eval. Incident-driven gap. Independent reviewer PASS-WITH-FIXES (added the cross-skill pointer to `agentic-delivery`'s `incident-response.md` owner-facing inventory template — here it's the review-time check; confirmed the overlap-window is correctly scoped to secrets/keys, not TLS).

## [1.265.0] — 2026-09-20

### deep-code-review — wave 186 React render/bundle perf: memoized-callback needs a memo boundary; heavy lib gated at import not render (closes #629, closes #628)

- **`frontend-a11y.md`** (Core Web Vitals): a memoized callback (`useCallback`) needs a memoized **recipient** — without `React.memo` on the row, a parent state change re-renders every mounted row regardless of stable props (necessary but not sufficient); windowing bounds mount count, not re-render cost. Fix: `React.memo` the row (low-risk *because* props are already stable) + a render-count acceptance check. (#629)
- **`frontend-a11y.md`**: a heavy optional-feature library (editor/chart/PDF/highlighter) rendered behind an interaction gate but **statically imported** from an always-mounted list/row component ships in **every route's bundle** — the gate that matters for bundle weight is the *import*, not the render. Fix: defer via `next/dynamic` / `React.lazy` / inline `import()`. (#628)
- +2 evals. Closes #629, #628. Independent reviewer PASS-WITH-FIXES: removed a stray blank line that had turned the tight CWV list loose (a CommonMark-verified do-no-harm regression on untouched bullets), reworded an illustrative figure to the file's generalize-the-principle convention, and tightened the memo eval's prop-stability premise.

## [1.264.0] — 2026-09-20

### deep-code-review — wave 185 eval-suite quality: Domain-L/T coverage + de-vacuous/de-dup/de-leak

- Acting on a whole-suite eval audit (set found strong: 0 dup ids, median-3 expectations, red-herring design confirmed). **Domain L (Infra/IaC/containers/K8s) had ZERO evals despite two dedicated reference files** — added 3 aligned to `infra-iac-containers.md` (Dockerfile root/unpinned-base/no-limits; K8s privileged/runAsUser:0/no-NetworkPolicy; Terraform 0.0.0.0/0-on-22 + public-unencrypted bucket). Added a **Domain T** (multi-tenancy) fairness/noisy-neighbour eval (shared queue + global limiter starve tenants; distinct from data isolation).
- Fixed 2 vacuous expectations (a length-bound that tested nothing; a vacuous "when written" escape) to real content checks; trimmed a near-duplicate parity eval to its unique bidirectional-diff contribution; de-leaked the billing eval to lead with a symptom.
- +4 evals (327 total, 0 dup ids). Independent reviewer PASS-WITH-FIXES (all new evals verified against the skill's actual guidance): replaced an eval-id citation with the skill rule by content, restored the billing eval's forgery-only clue so the signature-check conjunct is reachable, completed two gold outputs.

## [1.263.0] — 2026-09-20

### deep-code-review — wave 184 silent-measurement defects: randomized test order, head-sampling limits, provider-side 429 back-off

- **`testing-and-evals.md`**: a suite that always runs in file order can pass on the one order that works, hiding inter-test state pollution — run randomized order + a logged seed (pytest-randomly / Jest `--randomize` / JUnit `MethodOrderer.Random`); distinct from environment determinism.
- **`observability.md`**: head (pre-outcome) trace sampling — a *uniform* sampler's aggregate error **rate** stays unbiased, but it still fails on **coverage** (can't guarantee a specific error trace is kept), **variance** (noisy short burn-rate windows), and **p99/tail** estimation; an adaptive/load-shedding sampler biases the rate under load. Use tail sampling that always keeps error traces, and compute SLIs from unsampled counters (OpenTelemetry, verbatim).
- **`api-contracts.md`**: a throttled `429`/`503` must emit `Retry-After` (and ideally the IETF *RateLimit header fields for HTTP* budget — cited by name, as the draft is actively revised) so clients don't guess backoff — the provider's outbound obligation.
- +3 evals; 1 standards-index row (OpenTelemetry sampling, verbatim). Independent reviewer PASS-WITH-FIXES: corrected a sampling-bias **overclaim** (a uniform head sampler's rate is unbiased — the real limits are coverage/variance/tail), a **stale** IETF-draft field citation (draft-11 defines `RateLimit`/`RateLimit-Policy`, not the draft-00 `RateLimit-*` triple → cite by name), and an above/below cross-ref.

## [1.262.0] — 2026-09-20

### deep-code-review — wave 183 frontend/perf defects: SSR hydration nondeterminism, request waterfalls, OFFSET-pagination correctness

- **`domain-checklists.md`** (domain P): SSR hydration mismatch from **nondeterministic render output** (`Date.now()`/`Math.random()`/`typeof window`/browser-API read during render) — distinct from the invalid-nesting case; state-dependent so it misses local/CI, and `suppressHydrationWarning`-misuse hides it; the framework doesn't reliably patch a mismatch and can leave event handlers on the wrong elements. Fix: gate to a post-hydration effect / `useId`.
- **`frontend-a11y.md`** (Core Web Vitals): a **sequential data-fetch waterfall** (critical request chain) on the render path hurts LCP/TTI even with green bundle/image/font budgets — chain *depth*, not payload size, is the cost; parallelize / collapse server-side / prefetch.
- **`performance-db-cost.md`**: `LIMIT/OFFSET` pagination is a **correctness** hazard under concurrent writes (positional shift → duplicate row across pages on insert, skipped row on delete), not only a scan-cost one; use a `(sort_key, id)` keyset cursor.
- +3 evals. Sources by name (react.dev / Chrome Lighthouse / use-the-index-luke), no unverified verbatim. Independent reviewer PASS-WITH-FIXES: added the missing OFFSET citation, softened the "won't patch" hydration overgeneralization, rewrapped the three bullets to the files' line convention.

## [1.261.0] — 2026-09-20

### deep-code-review — wave 182 a rate/spend cap keyed to a cheaply re-mintable token is bypassable (closes #624)

- **`security-appsec.md`** (A06 Insecure Design, rate-limit-key bullet): a cap is only as strong as the cost of minting a fresh key. A self-service or unauthenticated **session token, device id, or API key** an attacker rotates for free is no better than keying on IP — re-minting resets the counter (the *rotating-key-vs-stable-identity* confusion), so "correctly counted per token" is irrelevant when the token is cheaply re-mintable. Key on a **scarce, verified** identity (a verified account, a payment instrument, a credential that itself costs / is rate-limited to create), or rate-limit the **minting** path itself.
- +1 eval. Closes #624. Independent reviewer PASS.

## [1.260.0] — 2026-09-20

### deep-code-review — wave 181 compliance defect-patterns: PCI cardholder data, HIPAA de-identification, NIST AC-2 IAM lifecycle

- **`privacy-compliance.md`**: NEW "Cardholder data (PCI)" subsection — Sensitive Authentication Data (CVV/CVC, full track data, PIN/PIN block) must never be stored after authorization (encryption-at-rest doesn't excuse it); masking (a *display* control) and truncation (a *storage* control) are not interchangeable. Extended the linkability pseudonym bullet with HIPAA §164.514(c)'s bright line — a de-identification code must be "not derived from or related to information about the individual" (a `hash(name+DOB)` pseudonym fails it).
- **`infra-iac-containers.md`**: a grant needs a *lifecycle*, not just correct scope at creation — an IAM/DB/service-account grant with no expiry/owner/deprovision path is standing access nothing revisits (the time axis; NIST SP 800-53 AC-2).
- Doctrine-fit: defect-patterns that name a regime + a code-visible defect and route the legal/adequacy call to counsel (per the repo's own AC-5 / GPC precedent) — not compliance certification. +2 evals; 3 standards-index rows (PCI glossary / CFR §164.514 / NIST AC-2 OSCAL), verbatim. Independent reviewer PASS-WITH-FIXES: corrected a spliced Truncation quote (the "for" was the Masking cross-ref; the real Truncation entry says "relates to") and the AC-2 sub-clause attribution ("notified", not "disabled", is the quoted (h)(2) obligation).

## [1.259.0] — 2026-09-20

### deep-code-review — wave 180 suite hygiene: de-duplicate the branch-triage table, close a routing loop, fix a dangling pointer

- **`report-format.md`**: the branch-triage table was duplicated verbatim from `branch-and-merge-hygiene.md` (and had already drifted — missing a row and the `0*` footnote); shrank it to one illustrative row + a cross-reference to the canonical `branch-and-merge-hygiene.md` § Triage table (the repo's own no-duplication thesis, applied to itself). Also named `infra-evolution-by-stage.md` + `docs-evolution-by-stage.md` in the going-forward roadmap — closing the loop SKILL.md already promised ("both feed the roadmap in report-format.md") but the section never delivered.
- **`domain-checklists.md`**: fixed a dangling "(S0–S3 below)" pointer (no S0–S3 definition exists in that file) → "(S0–S3 in `SKILL.md`)", where the tier definitions actually live.
- Whole-suite self-audit (read-only) otherwise found **no systemic duplication** and swept clean: CWE/WCAG/OWASP standard-ID consistency, routing coverage, version lockstep, byte budget. No eval change (prose-consistency fixes).

## [1.258.0] — 2026-09-20

### deep-code-review — wave 179 language defect classes: Rust `unsafe` soundness, Go concurrency idioms, Java equals/hashCode

- **`language-stack-redflags.md`**: NEW `## Rust` section (none existed) — `unsafe` as a proof obligation: `transmute` to an invalid enum/bool/char value is immediate UB; `unsafe impl Send`/`Sync` silences the thread-safety check without proving it ("compiles + tests pass" is not evidence); other unsafe tells; verify with `cargo miri` (+ ASan/TSan across an FFI boundary) or mark `unverified`.
- **`## Go`** += loop-variable capture (the fix follows the module's `go.mod` go-version, **not** the toolchain — check go.mod, not `go version`); channel-close discipline (send/close on a closed channel, or closing a nil channel = run-time panic); concurrent map access can abort the process (`fatal error: concurrent map writes`) — best-effort, so a clean run isn't proof.
- **`## Java / Kotlin`** += mutating a field used in `hashCode()` after inserting into a `HashMap`/`HashSet` strands the entry in the old bucket → silent not-found; keys must be effectively immutable over their `hashCode` fields (every field `hashCode()` uses must also be in `equals()`).
- +3 evals. Sources verified at primary docs (rust-lang transmute/nomicon, go.dev go1.22/LoopvarExperiment/spec/faq, Oracle Object javadoc). Independent reviewer PASS-WITH-FIXES (corrected the equals/hashCode contract direction, softened the Go map-crash to best-effort + cross-referenced `concurrency-shared-state.md`, fixed the sanitizer naming).

## [1.257.0] — 2026-09-20

### deep-code-review — wave 178 ML split-hygiene: grouped/temporal CV leakage + resampling inside the fold

- **`testing-and-evals.md`** (ML pipeline correctness): the cross-validation **split structure itself** leaks when rows aren't i.i.d. A plain `KFold` scatters a group's correlated rows (many samples per patient/user/device) across train/test → use `GroupKFold`. Shuffled `KFold`/`ShuffleSplit` on time-ordered data trains on the future to predict the past → use forward-chaining `TimeSeriesSplit`. Class-imbalance resampling (SMOTE/over/under) belongs inside the fold on train only — resampling the whole dataset before the split both leaks and makes the test set artificially balanced, so the metric describes a distribution production never sees. Distinct from the as-of *feature* leakage in `data-quality.md` §12 (this is split structure).
- +2 evals. `docs/standards-index.md`: scikit-learn cross_validation + imbalanced-learn common_pitfalls rows (verbatim, fetched/verified 2026-09-20). Independent reviewer **PASS** (verbatim quotes verified character-exact at source).

## [1.256.0] — 2026-09-20

### deep-code-review — wave 177 parallel-audit: CANCELLED-run merge-guard fail-closed + collision-check must page a PR's files (closes #605, closes #609)

- **`parallel-audit.md`** (#605): a merge guard must not render a `CANCELLED` run as FAILURE (the fail-closed mirror of the file's existing fail-open cancel-race note). Distinguish 4 states — PASS/FAIL/PENDING/NO-RUN, `CANCELLED` a subset of PENDING; select the run by grouping per check name at the exact head SHA and taking the latest completion time (not "latest by creation order," which can return the cancelled sibling); the status table shows PENDING/CANCELLED distinct from FAIL.
- **`parallel-audit.md`** (#609): a collision check must read a PR's file list paginated — `gh pr view/list --json files` silently truncates at 100 files (current `gh` client bug `cli/cli#13338`, verified live), so a "no overlap" clear on a large PR is unsound; use `gh api repos/:owner/:repo/pulls/<n>/files --paginate`. Same truncation class as the mind-pagination rule + the forge-only occupancy check (#413).
- +2 evals. Closes #605, #609. Independent reviewer PASS-WITH-FIXES (corrected a mis-cited issue #560→#413, cross-ref path to house convention, made the run-selection rule completion-time-primary, framed the 100-cap as current client behavior, tightened the merge-guard eval).

## [1.255.0] — 2026-09-20

### deep-code-review — wave 176 a11y detector method: focus-indicator contrast floor + reduced-motion symptom-audit (closes #598, closes #599)

- **`frontend-a11y.md`** (#598): a focus indicator must clear a numeric contrast floor (>=3:1 against its surface — WCAG 1.4.11 Non-text Contrast, AA, for UI-component states; 2.4.13 Focus Appearance, AAA, for the indicator area between focused/unfocused states), not merely *change*. An automated check that flags only "nothing changed on focus" validates the wrong property (a too-faint colour passes the diff, fails the product). Scope the detector to **author-styled** indicators — an unmodified user-agent-default focus style is exempt from 1.4.11's floor (2.4.7 still requires it visible), the same gate-vs-standard discipline the file applies to 1.4.3's disabled-control exemption. Beware a narrow-purpose token reused beyond its unenforced doc-comment context.
- **`frontend-a11y.md`** (#599): audit reduced-motion by the *symptom* (motion-producing APIs — `scrollIntoView({behavior:'smooth'})`, `scroll-behavior:smooth`, `Element.animate()`, autoplay/carousel), not only the *mechanism* the codebase already gates; imperative native paths escape a CSS-duration/animation-library-scoped grep.
- +2 evals. `docs/standards-index.md`: WCAG 1.4.11 + 2.4.13 rows (verbatim incl. the 1.4.11 exemption clause), fetched/verified 2026-09-20. Independent reviewer PASS-WITH-FIXES (added the 1.4.11 user-agent-default exemption so the detector isn't over-strict; extended the truncated verbatim quote; tightened #599 to its delta).

## [1.254.0] — 2026-09-20

### deep-code-review — wave 175 server-side template injection (SSTI) depth in A05 (CWE-1336)

- **`security-appsec.md`** (A05 Injection): SSTI given proper depth (previously only named in the injection list). Distinct from XSS — SSTI is untrusted input that becomes part of the **template source** the engine compiles and evaluates, so output escaping does nothing; in a server-side engine (Jinja2/Twig/Freemarker/Velocity/ERB) it is usually an **RCE** path via object-graph traversal, and an engine sandbox is a mitigation, not a boundary. Detect input passed *as the template* (`render_template_string(user_input)`, `Template(...).render`, `env.from_string`). Fix: never compile a template from user input — pass values only as bound context variables to a static template; for genuine user-template features use a logic-less engine or a locked-down sandbox treated as an RCE-grade boundary.
- +1 eval. CWE-1336 verified at MITRE; example payloads (Jinja2, FreeMarker) verified at PortSwigger. Independent reviewer PASS-WITH-FIXES (replaced a mis-attributed SpEL payload with engine-correct verified payloads).

## [1.253.0] — 2026-09-20

### deep-code-review — wave 174 data-correctness trio: UTC-date bucketing, timestamp-tie diff cursor, cross-kind bare-id diff merge (closes #620, closes #618, closes #619)

- **`time-date-correctness.md`**: bucketing a stored instant to a human calendar day/week needs the *actor's* zone, not a silent storage-zone-by-truncation frame (a deliberately declared canonical business-day grid is a legitimate exception); distinct from the wrong-clock-for-"today" and SSR-default-clock siblings (#620). A timestamp is not a unique key — a "since last checkpoint" diff using a record's own timestamp as a strict-`>` cursor drops the newest change on a tie; fix with a strictly-monotonic `(ts, seq)` tiebreak (an ordinal cursor only on an append-only, never-resorted log), cross-referenced to the paginated incremental-sync-cursor face in `domain-checklists.md` domain A (#618).
- **`data-quality.md`**: a diff/index key must be unique across every kind a discriminated-union list mixes — a bare-id Map/Set collides via last-write-wins and silently merges two entities into one delta; fix with a compound `(kind, id)` key; the tell is a sibling's already-stricter contract (#619). Added to the red-flag list.
- +3 evals. Closes #620, #618, #619. Independent reviewer PASS-WITH-FIXES; all 5 prescribed fixes applied (cross-ref the pre-existing incremental-sync twin, declared-grid exception, name both time siblings, lead with the sequence-id cursor fix, #619 red-flag bullet).

## [1.252.0] — 2026-09-20

### agentic-delivery — wave 173 add-only loop discipline: a decrement needs a stated reason, never a silent side effect (closes #473)

- **`fast-agentic-delivery.md`**: when an operator asks for MORE recurring loops to sustain throughput, the operator-visible count is add-only. Editing one loop's instructions in place is the default (no count movement); do not satisfy "more" by consolidating N loops into fewer richer ones — operators track loop count as a delivery-health proxy, so a silent drop reads as doing the opposite of the request. Prune only a genuine named defect (exact duplicate, dead/broken, or contradictory loop), stated explicitly with the reason; the count decreases only with a stated reason. General principle: never move a user-tracked countable resource (loops, open PRs, agents) the wrong way as a SILENT/unexplained side effect of an unrequested optimization — the trust violation is the surprise, not the decrement itself.
- +1 eval. Closes #473. Independent reviewer PASS (re-review after an initial PASS-WITH-FIXES: broadened the prune carve-out beyond exact-duplicate to any named defect, reframed the invariant around silent-vs-explained decrement, moved the section beside the loop cluster with a differentiating cross-ref).

## [1.251.0] — 2026-09-20

### deep-code-review — wave 172 a wrapping `<label>` does not name a control built on a non-labelable host element (closes #569)

- **`frontend-a11y.md`**: HTML `<label>` only names *labelable* elements (`<input>`, `<button>`, `<select>`, `<textarea>`, `<meter>`, `<output>`, `<progress>`, and form-associated custom elements). A widget built on a non-labelable `<div>`/`<span>` given an ARIA role is not named by a wrapping or adjacent `<label>`, so with an `aria-hidden` glyph as its only content it announces with no accessible name — while the JSX looks plausibly labeled and passes a shape-based review. Fix: name it with `aria-labelledby`/`aria-label` and verify the platform-computed accessible name in the accessibility tree. Corrects an earlier wrong framing that blamed the role override rather than the host element: adding a role to a labelable element (`<button role="switch">`) does not lose its label — the WAI-ARIA APG recommends exactly that.
- +1 eval. Closes #569. Independent reviewer PASS-WITH-FIXES; the prescribed fix (form-associated custom elements are also labelable, per the WHATWG HTML spec) applied to the bullet and eval.

## [1.250.0] — 2026-09-20

### agentic-delivery — wave 171 cut per-lane cycle-time before adding lanes (throughput = WIP / cycle-time) (closes #570)

- **`fast-agentic-delivery.md`**: on a capacity-bound machine throughput = WIP / cycle-time (Little's Law); once lanes saturate the CPU/RAM cap, the highest-leverage move is cutting per-lane cycle-time, not raising lane count (which thrashes and LOWERS throughput). Ranked levers: faster gates (diff-affected tests + cached dep installs, full suite still gates the batch/union), batch atomic changes per PR, merge trains, remote/cloud runners to break the machine ceiling, eliminate rework. Differentiated from the WIP-cap section (admission throttle) and cross-linked to CI-offload; anti-pattern flagged (bumping concurrency past the probed cap).
- +1 eval. Closes #570. Reviewer FIX applied (dropped an unsupported "cheapest first" ordering; differentiated from the adjacent WIP-cap section; linked lever 1 to the CI-offload section).

## [1.249.0] — 2026-09-20

### deep-code-review — wave 170 branch-protection required-check-name drift blocks every PR (closes #549)

- **`branch-and-merge-hygiene.md`** (required-check-satisfiable): distinct from the trigger-config case (a check that never fires for a PR) — a job renamed/retired in the workflow while branch protection still requires the OLD status-check name leaves that name with no producer, so it reports no status forever and blocks EVERY PR (mirror: a check dropped from the workflow but left required). Reads as "a required check never ran," but the cause is a stale hardcoded name. Keep the two enumerations in sync (derive the required list from the workflow, or test required-names ⊆ workflow-emittable job names) so a rename fails CI loudly; and a retired name often has more than one consumer (branch protection, a local preflight, merge-queue config) — audit every consumer. Placed with the section's bullet list (cross-ref the Lockstep-surfaces discipline in `domain-checklists.md`).
- +1 eval. Closes #549. Reviewer FIX-FIRST applied (retargeted a dangling cross-ref; moved the bullet into its list; folded the multiple-consumers audit).

## [1.248.0] — 2026-09-20

### agentic-delivery — wave 169 surface the human-run escape hatch when no autonomous path exists (closes #529)

- **`fast-agentic-delivery.md`**: distinct from the delegation asymmetry (wave 165) — when an agent is blocked from a gated terminal step (merge/deploy/paid call) with NO autonomous route (own call denied AND delegation unavailable/also gated), a closed gate with verified work piled behind it is an escalation, not a hold. The failure mode is looping "gated/holding" while banked green mergeable work stays at zero landed (invisible to an operator watching only the branch). On the FIRST denial, convert the block into a one-action human ask (a copy-pasteable `! <command>` the user runs — outside the agent's own classifier, not laundering because the human issues it — or one GUI action), track banked-verified vs landed, and escalate when banked>0/landed=0 persists rather than re-narrating the block.
- +1 eval. Closes #529.

## [1.247.0] — 2026-09-20

### deep-code-review — wave 168 notebook review: hidden state & committed-output leakage (data-science code)

- **`testing-and-evals.md`**: a new section for two notebook-specific failure modes a normal source review misses, distinct from ML-pipeline correctness. (1) Out-of-order execution → hidden state: a notebook's results reflect run order, not source order, so a committed `.ipynb` with non-monotonic `execution_count`s may not reproduce from a clean kernel; check via Restart & Run All / `jupyter nbconvert --execute` / nbclient in CI, not "it ran for me". (2) Committed output cells leak data/secrets: `.ipynb` stores outputs, so a printed `df.head()` (PII) or an echoed token lands in git history; strip outputs (`nbstripout`, a `--clear-output` pre-commit hook, or a CI gate), and a secret that reached a commit must be rotated, not just stripped. Converts the new-domains breadth scout's one non-gated residual into shipped coverage.
- +1 eval. Reviewer FIX-FIRST applied (corrected the fabricated `--ClearOutput` flag to the real `--clear-output`; added the key-rotation instruction the eval grades; softened a "does not reproduce" overclaim to "may not").

## [1.246.0] — 2026-09-20

### deep-code-review — wave 167 CSV / spreadsheet formula injection, export direction (A05)

- **`security-appsec.md`** (A05): the upload checks guard *inbound* files; a data EXPORT (CSV, or XLS/XLSX/ODS from stored rows) is the outbound mirror. A stored user-controlled string starting with `=`/`+`/`-`/`@`/tab/NUL is parsed as a formula by the spreadsheet app on open (CWE-1236) — `=WEBSERVICE(...)`/`=cmd|...` — firing with no injection into the app; HTML-escaping for the web UI does nothing (different output context). Fix at export time: prefix a single quote before any such leading character (ASVS v5.0.0-1.2.10, L3) and follow RFC 4180 escaping.
- +1 eval; +2 standards rows (OWASP ASVS v5.0.0-1.2.10 L3; CWE-1236 — verbatim via raw fetch 2026-09-20). Completes the ASVS/API deep-dive's 5 security-appsec gaps (TLS-cert, smuggling, API6, API4-spend, CSV).

## [1.245.0] — 2026-09-20

### deep-code-review — wave 166 API4 unrestricted resource consumption (spend axis)

- **`security-appsec.md`** (API-overlay): API4 was named-only; now a worked paragraph scoped to the axis nothing else covers — an individually-legitimate request (authenticated, or a valid pre-auth flow like password reset) that triggers a metered PAID downstream call (SMS/OTP, LLM completion, cloud egress, per-lookup data API) with no per-caller cap. Compute exhaustion is covered elsewhere; here the damage is the bill (OWASP's forgot-password SMS scenario: scripted tens of thousands of times, thousands of dollars in minutes). Ask for a provider-side spend ceiling or billing alert per paid integration plus a per-operation throttle; prefer a graduated response (a hard cap trips legitimate OTP/reset sends). Cross-refs `performance-db-cost.md` for in-code spend-governance bugs.
- +1 eval; +2 standards rows (OWASP API4:2023 "Configure spending limits…"; CWE-770 — verbatim via raw fetch 2026-09-20). Reviewer FIX-FIRST applied (corrected a misattributed OWASP-scenario citation; broadened the pre-auth framing; added the graduated-response nuance).

## [1.244.0] — 2026-09-20

### agentic-delivery — wave 165 auto-mode permission gate that denies the orchestrator but allows a sub-agent is a false 'stuck' (closes #515)

- **`fast-agentic-delivery.md`**: an unattended orchestrator draining green/mergeable/un-held PRs can hit a permission classifier that denies its OWN merge ("merge without review") while allowing the identical merge from a spawned sub-agent — the loop runs every tick and lands nothing, reading as "stuck" when the work is done and gated only by the classifier. Fixes: (1) a preflight-keyed allow-rule (permit the orchestrator to merge a PR whose repo green-gate/merge_preflight just passed — the deterministic portion of the review already ran); (2) symmetry + transparency (deny sub-agents too and surface the reason); (3) document the merge-routing. Delegation is fine for a clean merge of an already-green PR, but delegating a *workaround* for an action the orchestrator was just denied is itself catchable as laundering, not a loophole.
- +1 eval. Closes #515. Reviewer FIX-FIRST applied (scoped the "delegation is fine" clause to clean merges; softened the gate-is-review equivalence to "the deterministic portion of the review").

## [1.243.0] — 2026-09-20

### deep-code-review — wave 164 cancel-in-progress concurrency race leaves the head with no CI run (closes #366)

- **`parallel-audit.md`**: extended the "Cancel superseded runs with a concurrency group" bullet with its downside — under rapid successive pushes the run for the FINAL head can be cancelled as a superseded sibling (or never created), leaving the newest SHA with NO run (an ABSENT check, not a failure). The two wrong reads are not symmetric: a strict gate merely refuses a fine branch (safe but noisy); worse, a human trusts the last green (belonging to a since-cancelled head) and silently fail-open merges an unverified head. Confirm a run exists AND concluded for the exact head SHA before trust/merge; treat "no run for this SHA" as a third state (re-dispatch); scope cancel-in-progress so it never cancels the newest run. This is a merge-safety defect, not the cost section's default Medium.
- +1 eval. Closes #366. Reviewer FIX-FIRST applied (restored the fail-closed/fail-open asymmetry; added the merge-safety severity disclaimer).

## [1.242.0] — 2026-09-20

### deep-code-review — wave 163 API6 unrestricted access to sensitive business flows

- **`security-appsec.md`** (API-specific overlay): API6 was named-only; now a worked paragraph. A flow can be correctly authorized, individually within the rate limit, and still harm the business at volume (scalping, hold-then-cancel, referral/coupon farming); a generic per-IP/per-principal limiter misses it because each request is individually legitimate — the signal is automation, not volume. Ask which flows harm the business if excessively used, then add automation-specific controls (device/headless-browser fingerprinting, CAPTCHA/behavioral biometrics, non-human-timing detection). Machine-consumed B2B/partner APIs are the blind spot.
- +1 eval; +2 standards rows (OWASP API6:2023; OWASP ASVS v5.0.0-2.4.2 L3 — verbatim via raw fetch 2026-09-20).

## [1.241.0] — 2026-09-20

### agentic-delivery — wave 162 isolation worktree inherits the parent clone's stale refs (closes #560)

- **`fast-agentic-delivery.md`**: a worktree branched off the local clone's remote-tracking ref runs whatever build/CI/merge scripts that ref points at; if the clone hasn't fetched recently it silently runs STALE scripts and produces FALSE results — e.g. a merge-preflight that still requires a since-removed CI job refuses every PR ("required job never ran") while the fixed script on the true remote HEAD passes. Looks like a live gate bug; is a stale checkout. Fixes: (1) fetch the base ref immediately before creating the worktree (or hard-reset/rebase onto the freshly-fetched remote ref before running any script); (2) for checks that must reflect current remote/CI state (merge gates, required-check verification), query the forge/server API for actual check-runs — immune to local staleness — not a local script copy. New worktree-isolation-gotcha section; cross-refs the gate-epistemology discipline in `branch-and-merge-hygiene.md`.
- +1 eval. Closes #560. Reviewer FIX-FIRST applied (a misplaced modifier had inverted the "immune to local staleness" claim).

## [1.240.0] — 2026-09-20

### deep-code-review — wave 161 continuous coverage-guided fuzzing as CI infrastructure

- **`testing-and-evals.md`**: the taxonomy lists property/fuzz as a shape; this adds the depth the file gave mutation testing — a coverage-guided fuzzer run continuously (OSS-Fuzz/ClusterFuzzLite, `go test -fuzz`, `cargo fuzz`/libFuzzer, Atheris) mutates inputs against live coverage feedback and keeps finding new crashes, unlike a one-off property test. The review question is not "is there a fuzz target" but "is it wired to a scheduled/CI job, and does a crash reach a human" (triaged into a committed crash corpus that becomes regression tests); a target attached to no job is decorative. Caveat (per review): a passing OpenSSF Scorecard Fuzzing score can be satisfied by a non-coverage-guided property-testing library, so it alone is not evidence of continuous fuzzing — apply the wired-to-CI + crash-corpus bar regardless.
- +1 eval; +1 standards row (OpenSSF Scorecard Fuzzing — risk + description + rationale verbatim via raw fetch 2026-09-20).

## [1.239.0] — 2026-09-20

### deep-code-review — wave 160 HTTP request/response smuggling (A01)

- **`security-appsec.md`** (A01): a correct auth gate can still be bypassed if the edge/WAF and the origin disagree on where one HTTP message ends and the next begins. A `Transfer-Encoding` + `Content-Length` request parsed inconsistently by the two hops (CL.TE/TE.CL/TE.TE) smuggles a second, uninspected request past the WAF, or poisons the connection so the next user's request is prefixed with attacker bytes it can capture (a confidentiality break). The anonymous-GET sweep proves nothing here — it exercises only the edge's own parser, not edge/origin agreement. New forgeability-row item (5) + a dedicated paragraph. Fix at the framing layer (HTTP/1.x: `Transfer-Encoding` present => ignore `Content-Length`; reject a message with both); add a desync test (plain curl won't surface it).
- Folded the deferred back-reference from wave 157: A03's "signed vs same-channel-checksummed" clause now points to `release-engineering.md`'s producer-side signing section (bidirectional cross-link).
- +1 eval; +1 standards section (OWASP ASVS v5.0.0-4.2.1 L2 / -4.2.2 L3; CWE-444 — verbatim via raw fetch 2026-09-20).

## [1.238.0] — 2026-09-20

### deep-code-review — wave 159 shared accessor silently no-ops for the nested-key polymorphic shape (closes #559)

- **`data-quality.md`** §5: a shared exact-key filter matching a hardcoded OR-list of top-level field names (`[row.fooId, row.barKey, …].filter(Boolean).includes(key)`) silently returns empty — no error — for any polymorphic record shape whose id is nested under a sub-object (`metadata`/`frontmatter`/…): the candidate list is empty so `[].includes(key)` is always false, and that collection reads as "nothing ever matches" instead of failing loudly. It survives review because the other shapes work and a correctly-written per-shape accessor masks it. Catch: enumerate every shape and check its real field nesting at the schema/type; cross-check a correct sibling accessor; if the endpoint documents the parameter as uniform, the gap is a broken promise (`api-contracts.md`). Fix: a per-shape accessor registry (a closed, type-checkable enumeration), not another ad-hoc top-level entry; regression-test one fetch-by-real-key per shape. Framed as the read-side sibling of the erosion-guard rule.
- +1 eval. Closes #559. Reviewer nits applied (registry-vs-open-ended-write-sites clarification; doc-promise cross-ref).

## [1.237.0] — 2026-09-20

### deep-code-review — wave 158 TLS enforced is not TLS validated (client cert-validation bypass, A04)

- **`security-appsec.md`** (A04): new rule — "TLS everywhere" is about the wire; it says nothing about whether the client validates the certificate. A client with validation disabled — `verify=False` (requests), `rejectUnauthorized:false`/`NODE_TLS_REJECT_UNAUTHORIZED=0` (Node), `InsecureSkipVerify:true` (Go), an all-accepting `TrustManager`/`HostnameVerifier` (Java), `ssl._create_unverified_context`, `curl -k` — still uses `https://` but trusts any certificate from any host, so a MITM terminates and re-originates for free (CWE-295; the hostname-mismatch sub-case is CWE-297). Internal/service-to-service TLS is not exempt — pin the internal CA, don't disable validation. Explicitly disambiguated from the JWT `verify=False` in A07 (signature verification, a grep false-positive collision).
- +1 eval; +1 standards section (OWASP ASVS v5.0.0-12.3.2/-12.3.4 both L2, CWE-295, CWE-297 — all quoted verbatim via raw fetch 2026-09-20). Reviewer nits applied (softened frequency claim; grep list made a superset of the shallow index; CWE-297 precision).

## [1.236.0] — 2026-09-20

### deep-code-review — wave 157 producer-side signed releases (consumer-verifiable)

- **`release-engineering.md`**: new section — does the release process produce a signature a downstream CONSUMER can check (cosign/keyless Sigstore, `npm publish --provenance`, PyPI attestations/PEP 740, a GPG-signed tag or `.asc`/`.sig`, or a SLSA `.intoto.jsonl` release asset)? Distinct from deploy-side SLSA build-provenance verification (`infra-iac-containers.md`) and the depth of `security-appsec.md` A03's one-line "signed vs same-channel-checksummed" question, which it now cross-links. A project can have internal SLSA provenance yet ship nothing consumer-verifiable — that gap is the finding; and presence is not validity (Scorecard itself does not verify signatures).
- +1 eval; +1 standards row (OpenSSF Scorecard Signed-Releases, risk/description/caveat verbatim via raw fetch 2026-09-20). Reviewer FIX-FIRST applied (cross-link to A03) + nits (PEP 740 precision; validity caveat; 🚩 line convention).

## [1.235.0] — 2026-09-20

### deep-code-review — wave 156 base-branch identity as a merge-eligibility axis (closes #565)

- **`branch-and-merge-hygiene.md`**: a PR-open without an explicit base falls back to the tool's default (for `gh pr create`, a `gh-merge-base` git config if set, else the repo default branch); when the intended integration branch is not the default, a lane that omits the base flag silently opens against the protected default, and a merge gate checking only green + mergeable merges it there — a governance breach. New subsection: every PR-open passes the base explicitly; base-branch identity is a merge-eligibility axis (refuse a PR whose base is not the expected integration branch); recovery for an already-merged-to-protected PR is an owner decision + a port to the integration branch, never an auto-revert of the protected branch.
- +1 eval. Closes #565. Reviewer FIX-FIRST applied: the `gh pr create` default-base mechanism is stated as its true two-tier fallback, not over-claimed as always the repo default.

## [1.234.0] — 2026-09-20

### deep-code-review — wave 155 duplicate-detection depth: orphaned straggler + unassembled molecule (closes #582)

- **`product-ux-quality.md`** ("Unified across modules"): two refinements to the duplicate-detection technique (the base literal-string-grep rule is unchanged). (1) The **orphaned straggler** — a shared component existing and adopted in its named set is not proof the concept is unified; diff the component's doc-comment named set against a fresh whole-tree grep, and treat a hit outside it as a *candidate* straggler to confirm renders (not an automatic defect — consistent with the render-trace bullet). (2) The **unassembled molecule** — duplication with no shared literal string; call sites re-assemble the same primitives ad hoc and diverge on the assembly decisions; grep a repeated scaffolding pattern (not the label) and fix by building the one shared atom.
- +2 evals (one per sub-concept, matching the file's precedent). Closes #582.

## [1.233.0] — 2026-09-20

### deep-code-review — wave 154 committed binary artifacts as an unreviewable supply-chain surface

- **`domain-checklists.md`** (domain H): a genuinely compiled/opaque blob (`.jar`/`.dll`/`.so`/`.wasm`/`.pyc`, a prebuilt bundle, a vendored SDK binary) checked into the tree is code nobody can source-diff, so a malicious swap is indistinguishable from a legitimate rebuild — a supply-chain surface, distinct from the NUL-byte case (a *text* file git *misclassifies* as binary). Build from source in CI, or fetch at build/run time; if vendoring is unavoidable, pin by content hash with recorded provenance (domain K / A03, and A08 integrity failures).
- +1 eval; +1 standards row (OpenSSF Scorecard Binary-Artifacts, verbatim risk + description + remediation, fetched 2026-09-20). Reviewer FIX-FIRST applied: the standards-index description is now the verbatim source sentence (the earlier draft paraphrased it), and the eval prompt now cues the NUL-byte contrast so its discrimination expectation is reachable.
- Citation-ledger hygiene from wave 153's review: the V7 session-management row now attaches "such that re-authentication is enforced…" to re-authentication (its true subject) and restores the "Verify that" stem on 7.4.1.

## [1.232.0] — 2026-09-20

### deep-code-review — wave 153 session termination & timeout (A07)

- **`security-appsec.md`** (A07): new rule — session termination & timeout are server-side controls, not a cookie `Max-Age`. Require both a server-enforced inactivity (idle) timeout and an absolute maximum session lifetime (ASVS v5.0.0-7.3.1/-7.3.2, L2), not a client-trusted cookie. Logout must actually terminate server-side: a stateless JWT can't be "deleted", so it needs a deny-list of terminated tokens, a per-user not-before timestamp, or per-user signing-key rotation (ASVS v5.0.0-7.4.1, L1). Closes a dangling cross-reference from `frontend-a11y.md` (which pointed at "A07 session lifetime" prose that did not exist).
- Applied the JWT-algorithm-confusion citation nits from wave 152's review: ASVS id-form now `v5.0.0-9.1.2` per the repo convention; the ASVS quote no longer splices across a sentence boundary; the JWT Cheat Sheet quote carries a leading ellipsis for the dropped "if possible".
- +1 eval. +2 standards rows (OWASP ASVS v5.0 V7 §7.3.1/7.3.2/7.4.1; OWASP Session Management Cheat Sheet), fetched + verified 2026-09-20.

## [1.231.0] — 2026-09-20

### deep-code-review — wave 152 JWT algorithm confusion (A07)

- **`security-appsec.md`** (A07): new rule — JWT algorithm confusion. `alg: none` was already flagged; the live-key variant is worse. A verifier that accepts both a symmetric (HS256) and an asymmetric (RS256/ES256) algorithm AND reads the algorithm from the token's own `alg` header is forgeable — an attacker signs with `alg: HS256` using the RSA/EC **public** key (published, not secret) as the HMAC key, and a naive `verify()` accepts it. "The signature verifies" is not enough when the attacker chooses the algorithm. Fix: pin an algorithm allow-list per verification context; never derive the algorithm from the token; don't mix signature and MAC algorithms on the same key material.
- +1 eval. +2 standards rows (OWASP ASVS v5.0 §9.1.2 (L1, confirmed at source); OWASP JWT Cheat Sheet), fetched + verified 2026-09-20.

## [1.230.0] — 2026-09-20

### deep-code-review — wave 151 lock-ordering deadlock (prevention vs recovery)

- **`concurrency-shared-state.md`**: new red flag — lock *ordering*, not just lock *scope*, is what prevents deadlock. Two code paths that acquire the same two-plus locks in different orders deadlock under contention (a circular wait), even when each lock is held briefly with no I/O — distinct from the held-across-I/O case, and invisible to a single-threaded test or one that only exercises one acquisition order. Applies to in-process mutexes and DB row/table locks alike. Fix: a fixed global acquisition order at every multi-lock site (sort by a stable key), or a primitive that orders for you (C++ `std::scoped_lock`). Ordering is the prevention; the `40001`/deadlock-victim retry is the recovery — complementary, not competing. Closes the "no deadlock ordering" item that `domain-checklists.md` already promised but the routed file never delivered.
- +2 evals (DB row-lock transfer; in-process mutex pair). +2 standards rows (PostgreSQL 13.3.4 Deadlocks; cppreference `std::scoped_lock`; fetched + verified 2026-09-20).

## [1.229.0] — 2026-09-19

### deep-code-review — wave 150 reconcile a self-inconsistent design reference before building (closes #500)

- **`product-ux-quality.md`**: caveat to the "the reference is the styling source of truth" rule — a real design reference often contradicts *itself* (the same component drawn two ways on two screens, a spacing token whose value disagrees with its own usage, a flow whose steps don't match its summary). Copying it verbatim ports the contradiction into the product as an *implementation* bug (harder to spot and fix than a design one), and "match the reference" cannot adjudicate a reference that disagrees with itself. Surface the specific conflict, reconcile to one canonical interpretation first (pick the reading the rest of the design implies, or raise it as an owner A/B decision), and record that interpretation as its own reviewable artifact kept separate from the build.
- Reviewer FIX-FIRST applied: the eval prompt now states only observable symptoms (two button shades across screens; a documented 16px token vs actual 12px spacing) so it tests diagnosis rather than recall; the third expectation now requires the reconciliation be recorded as its own reviewable artifact.

+1 eval (275 → 276). Closes #500.

## [1.228.0] — 2026-09-19

### deep-code-review — wave 149 streaming transports (WebSocket / SSE) contract & reliability

- **`api-contracts.md`**: new "Streaming transports (WebSocket / SSE)" section — a live push connection is neither a queue nor an outbound call and needs its own review. Reconnection resumes from the last delivered position (SSE re-sends `Last-Event-ID` and the server must replay the gap; WebSocket has no built-in resume, so the application carries its own cursor/sequence; bounded backoff). Per-connection backpressure (cap the send buffer; drop/coalesce/disconnect; the browser sender watches `bufferedAmount`). Liveness both ways (ping interval + track outstanding pongs + reclaim on a missed pong). Ordering/dedup explicit across a reconnect (the transport orders within one connection only; per-message id + idempotent consumer).
- Reviewer FIX-FIRST applied: the WebSocket auth cross-reference now points to `security-appsec.md`'s API-specific overlay (OWASP API Security Top 10) WebSocket paragraph, not A01; the per-connection ordering claim no longer rests on RFC 6455's §5.4 fragment-ordering quote (stated as TCP/HTTP transport semantics instead); the RFC 6455 Pong quote is restored verbatim.

+3 standards rows (WHATWG SSE §9.2, RFC 6455, WHATWG WebSocket), +2 evals (273 → 275).

## [1.227.0] — 2026-09-19

### deep-code-review — wave 148 GraphQL resolver N+1 + null-deref-as-DoS (CWE-476) red-flags

- **`performance-db-cost.md`**: GraphQL resolver N+1 — the structural variant the textual "query in a loop" grep misses (the executor invokes a field resolver once per parent node, so there is no visible loop). Detect by queries-per-request count; fix with a DataLoader per-request batch/cache seam.
- **`language-stack-redflags.md`** (DoS section): null/nil dereference on a reachable path (CWE-476) is a crash/DoS, not a wrong-answer bug. Guard a nullable/optional/unchecked-cast value before dereference on any attacker- or upstream-reachable path (Go nil panic / Java NPE / Python None / JS undefined / C/C++). Closes the one real CWE-Top-25 detection gap (null-deref was named as a protected finding but had no detection procedure).
- **`language-stack-redflags.md`** (C/C++): added CWE-120/121/122 to the existing 787/416/125 ASan/UBSan citation (the two CWE-Top-25 partials).

## [1.226.0] — 2026-09-19

### deep-code-review — wave 147 filed singles: abort-cause, CI/dev resource parity, data-dead-filter (closes #551, #389, #371)

- **#551** (`reliability-error-handling.md`): an AbortController fires for both a timeout and a user-cancel;
  a blanket `if (AbortError) return` hides a real timeout — distinguish the cause (`AbortSignal.reason` /
  per-cause controller): user-cancel silent, timeout surfaced + retry-eligible.
- **#389** (`testing-and-evals.md`): local/CI parity includes the resource envelope — a hardcoded CI-tuned
  worker count OOMs the same gate on a lower-headroom dev host; size concurrency to the host or an
  overridable knob.
- **#371** (`product-ux-quality.md`): a filter/facet option matching zero real rows is a dead control (data,
  not structural) even with a working handler; derive options from the actual data distribution.

+3 evals (268 -> 271 deep-code-review).

## [1.225.0] — 2026-09-19

### deep-code-review — wave 146 webhooks — provider (outbound) side (breadth research)

`api-contracts.md`: the webhooks section was inbound-only. Renamed it "Webhooks — consuming (inbound)" and
added "Webhooks — providing (outbound)": sign every outbound payload (HMAC over `msg_id.timestamp.payload`,
the Standard Webhooks convention — space-delimited multi-signature for zero-downtime rotation, ed25519 also
allowed); the tenant-registered callback URL is an SSRF surface (validate / resolve-pin / block internal
ranges per A01, re-validate at connect time for DNS rebinding); bounded retry into a visible dead-letter, not
a silent drop; a stable delivery id + monotonic sequence so the consumer's inbound dedup works, and
state/disclaim ordering.

+1 eval (267 -> 268 deep-code-review). SRC fetched + verified 2026-09-19: Standard Webhooks community spec
(cited as a convention, not an IETF/W3C standard).

## [1.224.0] — 2026-09-19

### deep-code-review — wave 145 timestamp / parity / SSR-clock correctness (closes #558, #370, #561)

- **#558** (`domain-checklists.md` §A): the non-unique-timestamp trap also bites an incremental-sync cursor —
  a batch-stamped timestamp used as a strict `WHERE ts > :cursor` drops (or `>=` double-reads) rows at a page
  boundary; page on a unique monotonic tiebreak (`(ts,id)` composite) or an explicit sequence.
- **#370** (`domain-checklists.md` §H): one shared classifier with no duplicate implementation can still
  drift at its callers — the divergence is in the adapters; test the two call sites agree on a shared fixture
  and derive inputs from one spec.
- **#561** (`time-date-correctness.md`): a `now: Date = new Date()` testability default captures the server's
  clock/zone on a `'use client'` server-rendered first paint; pass the request time + user zone explicitly.

+3 evals (264 -> 267 deep-code-review).

## [1.223.0] — 2026-09-19

### deep-code-review — wave 144 data-quality: active-not-emitted signals (#480, #552) + external identity cluster (#461)

`data-quality.md`:
- **#480 + #552:** an acknowledgment ("drop acknowledged") or readiness flag (`data_ready`/`is_complete`)
  that nothing READS is not a control — it is write-only and changes no behavior (the drop still ships, the
  not-ready data is still served). Require a reader (gate the merge/publish; check before the consumer reads);
  the review test is a grep-for-a-reader. §7.
- **#461:** when an internal identity resolver model/number is forbidden (no-ML / spend / privacy), consume
  an external pre-computed identity cluster + its public artifact as the resolver instead of a name-only
  match; treat it as a corroborating source with recorded provenance. §3.

+2 evals (262 -> 264 deep-code-review).

## [1.222.0] — 2026-09-19

### deep-code-review — wave 143 experimentation infrastructure: isolate concurrent experiments (breadth research)

`release-engineering.md` Experiment-toggle bullet extended (code side, respecting the read-side boundary to
`growth-analytics`): concurrent experiments that both mutate the same surface with no layering and no mutual
exclusion **confound** each other — per-experiment bucketing + SRM don't catch cross-experiment interference;
the assignment infra must use orthogonal layers (Google overlapping-experiment infra) or mutually exclude
overlapping experiments. Read-side concerns (novelty/primacy over-time effects, multiple-comparison / FDR)
named as `growth-analytics` (read-side) analysis, not built here.

+1 eval (261 -> 262 deep-code-review). SRC fetched + verified 2026-09-19:
research.google/blog/overlapping-experiment-infrastructure (Tang et al., KDD 2010, by name).

## [1.221.0] — 2026-09-19

### deep-code-review — wave 142 NEW DOMAIN: time, dates & time zones (breadth research)

New reference `references/time-date-correctness.md`, routed from SKILL.md domain A, plus a correction to the
domain-A "Time & dates" one-liner in `domain-checklists.md` (it stated a blanket "store everything in UTC"
that is wrong for a wall-clock-anchored recurrence). Covers: the **instant-vs-wall-clock** distinction (UTC is
right for an instant, wrong for a recurring 9am / monthly-invoice date which drifts by the DST offset if
frozen to one UTC instant — store local + tz-id, re-resolve per occurrence); **ambiguous (fold) / missing
(gap)** local times at a DST transition (PEP 495); **tzdata as a stale-able dependency** (a future
wall-clock->UTC conversion frozen before a government rule change is wrong after it — IANA theory); durations
monotonic + a **calendar day is 23/25h** on a DST day (leap smear).

+3 evals (258 -> 261 deep-code-review). SRC fetched + verified 2026-09-19: tc39.es/proposal-temporal timezone,
peps.python.org/pep-0495, data.iana.org/time-zones/tzdb/theory.html, developers.google.com/time/smear.

## [1.220.0] — 2026-09-19

### deep-code-review + agentic-delivery — wave 141 cheap-lane delegation discipline (closes #504, #498)

- **model-tiering.md (#504):** tier by **correctness-subtlety, not diff size** — a small change can hide a
  structural/ordering trap a cheap model ships plausible-but-wrong and self-reports green on (a proxy pass,
  not the outcome). Verify against real acceptance (independent check / rendered geometry / the criterion);
  re-derive a cheap-tier miss from the acceptance criterion, not "make the failing tests pass". Lever-6
  caveat: a consult cap that must bound cost needs harness-level exclusion, not a prompt cadence.
- **host-enforcement.md (#498):** tool/capability access named as a declared per-control level; a prompt-level
  "do not use tool X" is protocol-only (the worker can still call X — model instructions aren't a sandbox);
  the host-enforced form is spawning with an allowed-tools set excluding X, with a protocol-audit fallback.

+2 evals (deep-code-review 257 -> 258, agentic-delivery 49 -> 50).

## [1.219.0] — 2026-09-19

### deep-code-review — wave 140 enforce data-honesty invariants by construction, not render convention (closes #502)

`data-quality.md` §2: for any anti-fabrication / data-honesty invariant, prefer enforcing it **by
construction** (shape the type/return so the dishonest value has no constructor — e.g. emit a bin only for an
observed period, so a "collected-zero" cell can't be built) over a render-time / call-site convention a later
edit silently violates; pin with a "never emits X" test. The how-to-guarantee companion to "make impossible
states unrepresentable" (`reliability-error-handling.md`), the open-world third state
(`product-ux-quality.md`), and "an absent window is not a decline" (§8). Reviewer check: can the dishonest
value even be constructed?

+1 eval (256 -> 257 deep-code-review).

## [1.218.0] — 2026-09-19

### deep-code-review — wave 139 a gate's committed fixture is part of its contract (closes #507)

`testing-and-evals.md` new section: a gate that asserts real-data-shaped output is honest on a clean clone
only if the committed fixture can produce what it checks — else it is red-by-construction (green from a
populated checkout, red on a fresh clone) and the repo's "green `verify` from a clean clone" DoD claim is
false. Fix by enriching the fixture to exercise every asserted field, or scoping real-data-only assertions
to a real-bundle run; verify from a truly clean clone. The repeated "several contributors each copy the real
bundle in" workaround is the signal that the fixture/gate contract is the defect. `docs-and-dx.md`: one
pointer line by the missing-prerequisite → symptom map.

+1 eval (255 -> 256 deep-code-review).

## [1.217.0] — 2026-09-19

### deep-code-review — wave 138 caching correctness (#478) + a CONCURRENTLY migration correction

Closes #478. `performance-db-cost.md` (Caching & memoization):
- **Invalidate every derived entry, not just the entity's own key** — composite/aggregate/list/rendered
  entries that embed the mutated entity; surrogate-key/tag invalidation or a dependency index. HTTP caches
  invalidate only the target URI; related keys are "candidates" (RFC 9111 §4.4).
- **Bound key cardinality, not just total size** — an unbounded/high-cardinality key = near-zero hit rate
  and single-use entries.
- **A shared cache must key on whatever varies the representation** (Accept-Language/Accept-Encoding) —
  RFC 9111 §4.1; distinct from the identity/authz Vary rule (a cross-user auth leak).
- **CONCURRENTLY correction**: a failed concurrent index build leaves an INVALID index (skipped for
  queries, still pays write overhead) and CREATE INDEX CONCURRENTLY cannot run in a transaction block.
Co-evolution: `domain-checklists.md` §E, `performance-db-cost.md` 🚩 grep footer.

+3 evals (252 -> 255 deep-code-review). SRC fetched + verified 2026-09-19: rfc-editor.org/rfc/rfc9111,
postgresql.org/docs/current/sql-createindex.html.

## [1.216.0] — 2026-09-19

### deep-code-review — wave 137 data-pipeline contract & lineage: schema-registry compatibility + backward lineage

Two data-pipeline correctness gaps, each with its own fetched source.
- **A convention is not a gate — enforce message-schema compatibility mechanically** (`api-contracts.md`).
  A schema registry compatibility mode rejects an incompatible schema at register/CI time; the mode is a
  function of deploy order (BACKWARD = consumers-before-producers, FORWARD = producers-before-consumers,
  FULL = independent; `*_TRANSITIVE` checks all prior versions; NONE disables). The message-boundary
  counterpart to the `oasdiff`/`buf breaking` gate on the HTTP surface.
- **Backward lineage: a wrong output must be traceable to the transform that produced it** (`data-quality.md`
  §2). Column-level lineage maps each output column to the input columns + the transformation — the
  backward, transform-level counterpart to forward provenance (origin) and the forward consumer census (§5).

+2 evals (250 -> 252 deep-code-review). SRC fetched + verified 2026-09-19:
docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html,
openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet.

## [1.215.0] — 2026-09-19

### deep-code-review — wave 136 reliability under stress: retry budgets + deadline propagation (research round 9)

Two ways a system amplifies its own load exactly when a dependency is struggling
(`reliability-error-handling.md`):
- **Cap retries with an aggregate budget, not only a per-request limit.** A per-request cap bounds one
  call, but if every failing call retries during a partial outage the combined retry traffic multiplies
  load on the struggling dependency (a retry storm) and can hold it down after the fault clears. Add a
  process/client-wide retry budget — a ceiling on the retry rate — and fail fast once exceeded. Distinct
  from the circuit breaker (destination health) and from keeping retries to one layer.
- **Propagate the deadline; don't reset it at each hop.** A request arriving with a remaining deadline
  must pass the remaining time down, not start each downstream call on a fresh full timeout — else an
  N-hop chain runs up to N×T of backend work while the caller gave up at T. Derive each downstream
  timeout from the inbound deadline, and check the deadline still has room before a retry.

+2 evals (248 -> 250 deep-code-review). SRC fetched + verified 2026-09-19:
sre.google/sre-book/addressing-cascading-failures ("60 retries per minute in a process ... just fail the
request"), grpc.io/docs/guides/deadlines ("converts the deadline to a timeout from which the already
elapsed time is already deducted").

## [1.214.0] — 2026-09-19

### deep-code-review — wave 135 CI-gate correctness: false-green pass-through holes + build-regenerated tracked files (closes #520, #514)

Two ways a required check reports green over code it never validated. `branch-and-merge-hygiene.md`:
- **A pass-through that fires on the wrong event is a false-green hole (#520).** A required check's
  pass-through job (exit 0 for out-of-scope PRs) is legitimate only when nothing was in scope. When the
  real job runs on `push`/`synchronize` but the pass-through also fires on an `edited` (title/body) event,
  a title edit reports a conclusive Success for code the checker never re-ran. Make the pass-through
  reachable only on the paths/events where the real check is genuinely N/A; the real job's own conclusion
  (or a re-run on the current head) must back the required status for an in-scope PR.
- **A git-tracked file the build regenerates poisons a clean-tree gate run in the same working tree (#514).**
  A build that rewrites a committed, tracked artifact makes any same-tree clean-tree assertion
  (`git diff --exit-code`, a merge preflight, a pre-commit hook) red on a build-created diff. Fix at the
  source (don't track a build output; or regenerate deterministically as its own step and scope the check
  to exclude the path), or run the clean-tree check in a fresh checkout the build never ran in.

+2 evals (246 -> 248 deep-code-review). SRC fetched + verified 2026-09-19:
docs.github.com/en/webhooks/webhook-events-and-payloads (pull_request activity types — `edited` and
`labeled`/`unlabeled` are distinct actions).

## [1.213.0] — 2026-09-19

### deep-code-review — wave 134 concurrent & distributed correctness: memory visibility + trace propagation (research round 8)

Two axes the concurrency and observability sections under-covered, each with its own fetched source.

`concurrency-shared-state.md`:
- **Memory visibility is a separate axis from atomicity.** For every shared mutable field read by a
  thread/goroutine other than its writer, name the synchronization edge (lock, atomic, `volatile`,
  channel op, fence) that orders the write before the read. With none the write has no guaranteed
  visibility — the reader may never observe it or observe it reordered — and no interleaving is needed
  to fail, so a check-then-act race hunt misses it (a plain polled `bool` flag, or a lazily-assigned
  singleton / broken double-checked locking, are the canonical cases). A data race is undefined
  behavior in C/C++ and `unsafe` Rust and "incorrect" (with multiword tearing) in Go — not a benign
  stale scalar.

`observability.md`:
- **A shared log correlation id is not an unbroken distributed trace.** Every service can stamp the same
  id on its logs while each still starts a fresh root span, so logs reassemble by grep but the trace
  backend shows N disconnected fragments. Verify one request's trace id resolves to one trace in the
  tracing backend; the break is at a hop without auto-instrumentation (queue publish, cron/background
  job, async handoff) where W3C `traceparent` must be injected into the envelope by hand.

+2 evals (244 -> 246 deep-code-review). SRC fetched + verified 2026-09-19:
doc.rust-lang.org/reference/behavior-considered-undefined.html (Rust data races = UB),
go.dev/ref/mem, en.cppreference.com/w/cpp/language/multithread, w3.org/TR/trace-context.

## [1.212.0] — 2026-09-19

### agentic-delivery — wave 133 parallel-lane hygiene: repo-global stash + decouple finalize (closes #536, #506, #528)

Filed-backlog drain (issues surfaced by concurrent-lane delivery runs). Two additions to
`fast-agentic-delivery.md`:
- **A worktree does not isolate repo-global refs (#536)** — `git stash` is a single repo-wide stack
  (`refs/stash`), not per-worktree, so a sibling lane's push/pop consumes or reorders this lane's entry
  (silent WIP loss). Never bare stash push/pop under concurrency — commit-then-reset, a second worktree,
  or `git stash create` (a dangling commit SHA that never touches the shared `refs/stash`), restored via
  `git stash apply`. (#536's scratch-path-collision half was already covered; this ships the
  genuinely-new stash half.)
- **Land the fix, then finalize separately (#506, #528)** — a lane that opens a draft PR early and does
  async finish-work can orphan the draft when a lingering helper process or a retry loop holds the turn
  open past the promote step. Decouple fix-landing from finalize (ready the PR once code+gates are green;
  make finalize a separate idempotent step), kill a lane-owned helper the moment its step ends, bound
  every flaky finalize step to a cap that fails to a report, and have the orchestrator sweep-and-adopt
  orphan drafts.

+2 evals (47 -> 49 agentic-delivery). Triage confirmed #525 / #519 already covered
(concurrency pkill / auto-close-hygiene) — closed with cited evidence, not rebuilt. #528-F3
(load1 back-off for an I/O-heavy fan-out) was found not actually actionable and is shipped here.

## [1.211.0] — 2026-09-19

### deep-code-review — wave 132 verify build provenance at deploy, not just generate it (SLSA, research round 7)

Comparative vs SLSA v1.0. Closes the asymmetry: inbound package signatures are a blocking gate
(`infra-iac-containers.md`) but the OUTBOUND SLSA attestation had no verify step. `security-appsec.md`
A03 now covers the consumer side — verify the attestation before promoting (**subject digest matches
the artifact** first, else a validly-signed attestation for a *different* artifact passes; then
signature valid, signer/builder trusted, canonical source repository matches) and **fail closed** on
missing/mismatch — the runtime-proven-gate lens applied to the supply chain. Plus SLSA Build level
detail (L1 exists/forgeable/may-be-unsigned, L2 signed + downstream authenticity verification, L3
hardened) so a bare "adopts SLSA" with no level named isn't credited as the strong guarantee.
`infra-iac-containers.md` cross-linked with the same blocking-gate phrasing as its inbound sibling;
the by-name SLSA standards-index entry promoted to a verified row.

+1 eval (243 -> 244). SRC fetched + verified 2026-09-19: slsa.dev/spec/v1.0/{levels,verifying-artifacts}.
Independent review PASS-WITH-NITS; all nits applied (subject-digest first check, "may be unsigned",
canonical-source-repo).

## [1.210.0] — 2026-09-19

### deep-code-review — wave 131 frontend accessibility & performance depth (research round 6)

Comparative vs WAI-ARIA Authoring Practices + WCAG 2.2 + web.dev Core Web Vitals. Six additions to
`frontend-a11y.md` (its 6 new WCAG-2.2 A/AA criteria + first-rule-of-ARIA were already present — this wave adds a different, adjacent set spanning ARIA authoring, WCAG 2.2.1/2.2.2/2.3.3, and web.dev CWV):
- **Phantom focus (4th rule of ARIA)** — hidden interactive content (closed off-canvas menu, collapsed
  accordion, CSS-hidden dropdown) must leave the tab order (`inert` / unmount / `tabindex=-1`);
  `aria-hidden="true"` must never sit on a container with a focusable child. The mirror of the
  open-dialog focus-trap.
- **Timing & motion** — WCAG 2.2.1 (a time limit that logs out / discards input needs a
  warn-and-extend affordance; the security-vs-a11y tension is resolvable — keep the short timeout, add
  the affordance) and 2.2.2 (auto-moving/updating content > 5s needs pause/stop/hide); plus a
  reduced-motion JS-path note (2.3.3: a CSS media query doesn't reach a `requestAnimationFrame` /
  motion-library animation — the JS must consult `matchMedia`).
- **Core Web Vitals lab-vs-field** — the p75 is a FIELD measurement (CrUX/RUM); a green Lighthouse
  lab run is not "meets Core Web Vitals" (same lab-necessary-not-sufficient caveat as an a11y scanner);
  plus a frontend byte-weight budget as a CI ratchet, and CLS-from-late-chrome / long-tasks-from-3p
  detail.

+3 evals (240 -> 243). SRC fetched + verified 2026-09-19: WAI-ARIA using-aria (Rule 4), WCAG 2.2.1,
WCAG 2.2.2, web.dev Core Web Vitals (all logged in docs/standards-index.md).

## [1.209.0] — 2026-09-19

### deep-code-review — wave 129 crash-case fail-open batch proof + P0 throughput-gate (closes #378)

Standalone-backlog drain, the crash cousin of #483's hung-gate rule, in `branch-and-merge-hygiene.md`:
a tool **broken in this environment** (harness crash / dependency down) is a **can't-check, not a red**
("could not check" is not "found a problem", `product-ux-quality.md`), so it must **fail-open for the
batch proof** — drop that one broken term, run the runnable subset, keep batching — rather than
collapse the whole train to serial merging; and **treat a throughput-gating tool as P0** (its blast
radius is the whole delivery rate). Reconciled against #483: a hang is timeboxed + escalated (unknown
validity), a crash is routed around now (definitively broken); both keep the flaky/heavy gate out of
the blocking union term and hold the same floor at the grain each leaves intact (a hang validated
nobody; a crash validated everyone except a member whose essential check was the crashed term). +1
eval. This is #454 point-1, split from wave 126 per that review.

Independent review FIX-FIRST (the same-floor equivalence was asserted, not earned) then re-confirmed
PASS after naming the surviving-evidence difference.

## [1.208.0] — 2026-09-19

### deep-code-review — wave 130 privacy threat modeling: linkability + account-enumeration (research round 5)

Comparative vs LINDDUN + NIST Privacy Framework. Two GENUINE-NEW privacy lenses plus a polarity note:
- **Linkability & re-identification** (new section, `privacy-compliance.md`): minimization limits what
  you hold; linkability is whether a pseudonymized/aggregated export can still single out an
  individual — small-cohort singling-out (report the smallest group size, don't assert "anonymous"),
  a recomputable/stable pseudonym reused across purposes as a linkage key, a quasi-identifier
  COMBINATION. Measure-don't-certify (the k / DP threshold is the owner's call; legal anonymity routes
  to counsel). 2nd source: NIST PF CT.DP-P Disassociated Processing.
- **Account enumeration / detectability** (`security-appsec.md` A07): diff signup/login/reset responses
  (status/body/redirect/TIMING) between exists/not-exists — CWE-203 Observable Discrepancy / LINDDUN
  Detectability; fix is a generic response + constant-time path.
- **Non-repudiation polarity flip** (`observability.md`): the audit trail is a security goal but
  LINDDUN's Non-repudiation privacy threat from the subject's side. Unpacked the bare "LINDDUN"
  mention in the threat-model list with cross-refs.

+2 evals (237 -> 239). SRC fetched + verified 2026-09-19: CWE-203, NIST PF CT.DP-P (logged). LINDDUN
cited by-name only (established, like STRIDE). Independent review PASS-WITH-NITS; nit applied
(cross-ref direction above->below).

## [1.207.0] — 2026-09-19

### deep-code-review — wave 128 API-contracts batch: long-running operations, RFC 9457 errors, PATCH-replacement break (research round 5)

Research-derived (comparative vs Google AIP / Zalando / Microsoft API guidelines). Three additions to
`api-contracts.md`:

- **Long-running operations** (new section): an endpoint that can't finish in the sync budget must not
  fake synchrony — return 202 + an independently-versioned operation/job resource (stable id; status
  enum with real terminal states, not a boolean; error-only-on-failed / result-only-on-succeeded; a
  documented poll mechanism), and the client distinguishes poll-transport failure from operation
  failure. The **start call needs provider-side idempotency** so a retried start (lost 202) folds into
  the same operation instead of spawning a second (the provider half of reliability's caller-side
  idempotency; internal durability is domain W).
- **RFC 9457 error envelope** (extend Typed-errors): one consistent machine-readable envelope across
  the surface (`application/problem+json`; obsoletes RFC 7807) instead of an ad-hoc per-endpoint shape,
  and the stable code is part of the versioned contract (frozen post-release; changing it is breaking).
- **PATCH/PUT full-replacement break** (6th non-obvious breaking-change): adding a new mutable field to
  a full-replacement resource breaks an old round-tripping client, which clears the field it predates
  (AIP-134).

+3 evals (234 -> 237). SRC fetched + verified 2026-09-19: RFC 9457 (obsoletes 7807; media type +
members), AIP-134 (full-replacement new-field data loss) — logged in docs/standards-index.md.

## [1.206.0] — 2026-09-19

### agentic-delivery — wave 126 revert a degradation workaround when the blocker clears (closes #454)

Standalone-backlog drain. A new section in `fast-agentic-delivery.md`: a degradation workaround is
temporary by default — tie its removal to the condition that caused it. The expensive trap is that the
workaround OUTLIVES the outage: momentum keeps the degraded mode running because nothing is red (the
slower path still "works"), so no failing gate prompts the switch-back until a human notices the
slowness — a self-monitoring failure. Discipline: tie the workaround to its trigger at install time,
track active workarounds as open obligations, restore the primary mechanism the moment the blocker
clears ("still works" is not "still the right mechanism"). +1 eval (46 -> 47 agentic-delivery).

Independent review returned FIX-FIRST twice, both verify-before-cite catches, both fixed: the first
draft mis-cited #483's hung-gate rule for a "keep merging on the reduced batch" claim it contradicts
(corrected to reference branch-and-merge-hygiene.md accurately — a hung gate timeboxes + escalates,
its reduced subset does not license an unvalidated merge; a tool broken-in-environment is a
can't-check, not a red); the second cited the wrong SKILL.md principle (3 = can't-check/UNVERIFIED,
not 2 = banlist). #454 point-1 (a crashed tool must fail-open the batch proof) is the separate open
#378, split to its own wave.

## [1.205.0] — 2026-09-19

### deep-code-review — wave 127 test reliability fallback paths, not just guard paths

From research round 5 (comparative vs chaos-engineering / Google SRE): the suite prescribed
fallback/degraded paths in 5+ loci but never required a repo-owned TEST that the fallback branch runs
correctly (only a fired-counter or a one-time game-day). Extends `testing-and-evals.md`'s "test the
failure" bullet from security/guard paths to reliability fallback paths (circuit-open, retry-exhausted
/ dead-letter, cache-miss serve-stale, generation-failure): force the trigger and assert the branch
OUTPUT, not just no-crash / a counter; plus a matching clause in that file's closing red-flag recap.
Plus a recency bar on `release-engineering.md`'s chaos section (date the game-day like the restore
drill; stale once the exercised path materially changed). +1 eval (233 -> 234).

Independent review PASS-WITH-NITS; both nits applied (recap clause added; a Rollback-section
over-attribution reframed to "extending the exercise bar to a recency bar"). SRC (fetched):
principlesofchaos.org, sre.google/sre-book/{testing-reliability, addressing-cascading-failures}.

## [1.204.0] — 2026-09-19

### deep-code-review — wave 125 a NUL/control-byte source file is git-binary-unreviewable (closes #479)

Standalone-backlog drain (domain H maintainability / reviewability + a domain-K CI-gate candidate). A
new bullet in `domain-checklists.md` §H: a tracked source file containing a raw **NUL** (`0x00`) is
git-classified **binary** — `git diff` / `git show` / `git log -p` print "Binary files differ"
(`git diff --stat` shows `Bin`) and `grep`/`ripgrep` print only "Binary file matches" unless forced
with `-a`/`--text`, so the change is undiffable in its PR and the file's identifiers are un-searchable,
though it runs fine — a reviewability defect orthogonal to correctness. A non-NUL control byte stays
text-classified but renders invisibly (milder, same escape fix). Use the language escape (`\0`);
a commit/CI gate can flag any tracked source path git treats as binary. +1 eval (232 -> 233).

Independent review returned FIX-FIRST after empirically testing (live git 2.50.1): the filed issue's
own text overclaimed that `git blame` shows "Bin N bytes" (it runs fine) and that "any control byte"
triggers binary classification (only NUL does) — both corrected against empirical behavior before
merge, in the bullet and the eval; re-confirmed PASS.

## [1.203.0] — 2026-09-19

### deep-code-review — wave 124 data-quality: per-hop pivot graph + observability-class bias (closes #468)

Standalone-backlog drain (domain D data integrity). Two additions to `data-quality.md`:

- **#468 per-hop pivot graph** (§10, cross-ref §1/§3) — a connector/transform pivot engine (identifier
  -> transform -> new entities -> next transform; the Maltego/SpiderFoot pattern) compounds two risks a
  single-source lane does not have: attribution risk (a wrong entity mid-chain poisons downstream hops,
  so each transform's output must re-pass the identity/fanout gate before attribution, not just at the
  chain end) and identity-disclosure risk (each hop contacts a new host directly — route a gated hop
  through a licensed broker under the declared identity policy, never spoof; no rate-limit-evasion
  fan-out). Per-hop guards, not a single end-of-chain gate.
- **#466 observability-class bias** (§8) — observability is a per-entity-class property, not only a
  per-window one: whole classes (operators, investors) are structurally less publicly observable than
  others (engineers, researchers, OSS contributors), independent of time window. Label a
  public-footprint class and carry it into every consumer so an empty profile in a low-observability
  class renders "not observed," never "inactive," and a ranking never reads unobserved as low-activity.
  Extends §8's temporal "absent window is not a decline" rule to the cross-sectional axis (#466 was
  PARTIAL, not covered — §8 covered only temporal gaps).

+2 evals (230 -> 232). #468 closed; #466 addressed (cross-sectional stratum shipped).

## [1.202.0] — 2026-09-19

### deep-code-review — wave 123 segregation of duties / maker-checker (closes #472)

Standalone-backlog drain (domain B / AppSec A01). A new "Segregation of duties" lens in
`security-appsec.md`, orthogonal to the two-principal (IDOR) matrix it sits beside: the matrix tests
that principal A cannot reach principal B's *object* (cross-principal access); SoD tests that the
**same** principal cannot both **initiate and approve** a consequential action (issue and approve a
payout, create and activate a credential, request and grant access, submit and merge to a protected
surface). Checks that `approver != requester` is enforced server-side on a stable principal id (not a
client field), that a user cannot self-grant the approver role, that it is scoped to genuinely
consequential actions (gating every write is friction, not control), and that the maker-checker
decision is audit-trailed (cross-ref `observability.md`, not restated). SOX, PCI DSS, and NIST 800-53
AC-5 mandate the control by-name; whether a target is legally required routes to `business-ops` /
counsel, not this gate.

Independent dogfood review returned FIX-FIRST (the audit-trail conjunct from #472's acceptance line
was unshipped; one eval narrated its own answer; the scope-gate — #472's named regression risk — was
untested); all fixed and re-confirmed PASS before merge. +2 evals (228 -> 230).

## [1.201.0] — 2026-09-19

### deep-code-review — wave 122 workflows/jobs §W cluster (closes #467, #430)

Standalone-backlog drain (domain W jobs/scheduling + M observability). Three method-level additions to
`domain-checklists.md` §W, each closing a filed issue:

- **#467 firing-suppression** — a signal->action system needs firing-suppression distinct from
  delivery-idempotency: a cooldown window per (entity, signal type), suppression-with-audit (never a
  silent drop), and a deterministic firing key over (entity, signal type, event instance) so repeated
  observations of one real event fold into a single firing. Distinct from the delivery-idempotency key
  (same-message re-execution).
- **#430a progress-emission** — liveness signals are end-of-window (a heartbeat proves only
  process-alive; a stale last-success catches a zero-success run only after its staleness window, and
  never fires for a partial grind that keeps last-success fresh), so catching a systemic fault in-flight
  needs progress emission: processed/total + a fault count + a fault-rate alert.
- **#430b lane-fault-budget** — bound the lane as a whole, not only each item: a per-item retry cap
  still lets thousands of individually-bounded-but-failing items burn the run, so a high
  consecutive-fault fraction (upstream down) aborts the remaining lane fast (wall-clock and/or
  consecutive-fault budget).

Independent dogfood review returned FIX-FIRST (a self-contradiction in the #430a prose vs the liveness
sentence it extended, baked into the eval; a lone soft "Ideally" expectation; #467 shipping 2 of 3
named legs); all fixed and re-confirmed PASS before merge. +3 evals (225 -> 228).

## [1.200.0] — 2026-09-19

### deep-code-review — wave 121 bulkheads / resource isolation + gate-on-success (reliability-error-handling.md)

From the COMPARATIVE research round (Release It! stability patterns benchmark): Bulkhead / resource
isolation was the one gap — and the architecture lens already promised it (`role-coverage.md`: "bounded
by timeouts, bulkheads, and circuit breakers (cross-ref F)") while F had no bulkhead content. New
section (repairs that dangling cross-ref):

- Partition a shared pool by dependency/traffic class; fail fast when a pool/breaker is exhausted;
  divide a fixed downstream capacity per replica with a floor; shed/degrade low-priority work under
  self-overload (folds Fail-Fast + sync Shed-Load + Blocked-Threads + Unbalanced-Capacities).
- Also (closes filed **#455** net-new): a downstream consumer gates on the producing step's SUCCESS,
  not the artifact's existence (existence != freshness != success); adding an abort to a formerly-
  hanging step is a write-path change (preserve last-good, don't write-then-throw). (rule-1 skip-write
  was already covered; this is the rule-3 net-new.)

Three evals (deep-code-review 222 -> 225). Source: Release It! (Nygard) by name. Trio -> 1.200.0.
`SHA256SUMS` regenerated last.

Closes #455.

## [1.199.0] — 2026-09-19

### agentic-delivery — wave 120 delivery-lane hygiene (closes #492, #494, #496)

Draining the filed backlog. Three deltas to `fast-agentic-delivery.md`:

- **#492**: reproduce the bug on current integration HEAD before writing a fix — an inbound report is
  about a past build (deploy/report lag) and may already be fixed on HEAD.
- **#494**: after applying a captured diff (3-way/context), re-run the formatter on the changed files
  (the apply can shift bytes), AND brief the lane up front with the root/repo-wide gate it will be
  judged by at land — not a workspace-local subset (point 1's briefing arm).
- **#496**: a hard-reset sync loop on a live-served worktree silently kills the dev server (clean
  exit) → the UX gate hits a dead port; serve from an untouched tree / ff-only / health-checked supervisor.

Three evals (agentic-delivery 43 -> 46). Trio -> 1.199.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): PASS-WITH-NITS -> applied. Shipped #494's missing briefing arm (brief the
lane with the root gate up front) so #494 fully closes; softened "apply shifts bytes" -> "can shift"
(a clean apply against the exact base doesn't); stripped the diagnosis from the #492 eval prompt so it
tests inference. No-duplication verified clean across all three deltas.

Closes #492. Closes #494. Closes #496.

## [1.198.0] — 2026-09-19

### deep-code-review — wave 119 graceful shutdown & disposability (reliability-error-handling.md)

From the COMPARATIVE research round (12-Factor App benchmark): factor IX Disposability was the one gap
— the crash/resume rules covered the batch/cron shape, but a long-running listening service / queue
worker disposed on every deploy had no graceful-shutdown home. New subsection:

- Order: fail readiness BEFORE closing the listener (else the LB routes to a closed socket).
- Drain is bounded (timeout >= p99, force-close + log survivors); zero/unbounded drain both wrong.
- The platform grace window + LB deregistration delay is a separate additive clock, not the app's drain.
- A worker nacks/returns its in-flight job on shutdown (at-least-once redelivery), not "exit as-is".
- Release lease + flush telemetry before exit; a mid-write kill must be retry-safe.

Three evals (deep-code-review 219 -> 222). Source: 12factor.net/disposability (fetched 2026-09-19);
Kubernetes preStop/terminationGracePeriod named as examples only (not a pinned spec). Trio -> 1.198.0.
`SHA256SUMS` regenerated last.

## [1.197.0] — 2026-09-19

### deep-code-review — wave 118 branch-and-merge cluster (closes #448, #469, #483)

Draining the filed backlog. Three deltas to `branch-and-merge-hygiene.md`:

- **#469**: a THIRD mergeability state — GitHub recomputes `mergeable` async, so an overlapping PR is
  briefly null/UNKNOWN after a base-changing merge (not CONFLICTING); poll-until-settled, retry
  UNKNOWN only. (GitHub-verified; hedged for other forges.)
- **#448**: the ABSENCE of a mutable hold marker is not authorization — deletion-by-edit false-clears
  a preflight; back holds out-of-band, body automation append/insert-only, fail-closed on disappearance.
- **#483**: a union/merge-train gate that HANGS (not fails) stalls the pipeline — detect by the gate
  job's OUTPUT liveness (the base head is stationary during the gate run by design; base-head movement
  is the drain-phase signal), treat a hang as can't-check/UNVERIFIED, timebox + fall back to the
  runnable subset as proof-of-record (never merge on it), keep heavy gates in per-change checks.

Three evals (deep-code-review 216 -> 219). Trio -> 1.197.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): FIX-FIRST -> applied. #483's base-head-movement heuristic was vacuous
during the gate-run hang window (the base head only moves in the drain phase) — re-led with gate-output
liveness (mirroring the long in_progress-shard rule) and shipped the timeout→runnable-subset fallback
the issue asked for, so #483 fully closes; hedged the async-mergeable claim to GitHub; fixed flow.

Closes #448. Closes #469. Closes #483.

## [1.196.0] — 2026-09-19

### deep-code-review — wave 117 DB migration depth + concurrency transaction-isolation

Two verified depth findings (postgres/mysql backend correctness), all facts fetched from primary docs.

- **db-migration** (`performance-db-cost.md`): lock ACQUISITION (not just duration) — a pending
  ACCESS EXCLUSIVE blocks the table via the lock-manager wait-queue rule; backfill throttles on an
  observed backpressure signal; the constraint-add hazard is a family (UNIQUE/FK/CHECK/type-change),
  fixed by two-phase `NOT VALID` + `VALIDATE` / `CREATE UNIQUE INDEX CONCURRENTLY`; `migrate` is
  dual-write + a zero-gap completion proof.
- **concurrency isolation** (`concurrency-shared-state.md`): a transaction boundary is not the
  concurrency guard — at the default level (Read Committed in PG, REPEATABLE READ in MySQL/InnoDB) it
  gives atomicity+durability, not isolation; the guard is FOR UPDATE / CAS / SERIALIZABLE, and a
  40001/deadlock abort retries the whole transaction.

Three evals (deep-code-review 213 -> 216). Sources logged: postgres transaction-iso / sql-altertable /
explicit-locking / lock-manager README + mysql innodb-transaction-isolation (fetched 2026-09-19).
Trio -> 1.196.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): FIX-FIRST -> applied. Corrected a lock-mode overclaim (ADD FOREIGN KEY
takes SHARE ROW EXCLUSIVE, not ACCESS EXCLUSIVE); fixed an ACID term (BEGIN gives atomicity, the guard
gives isolation); co-evolved the stale bare-"transaction" peer + both 🚩 footers the new rules refute;
re-attributed head-of-line blocking to the lock-manager wait-queue rule.

## [1.195.0] — 2026-09-19

### deep-code-review — wave 116 web frontend security (browser-native controls, frontend-a11y.md)

From the COMPARATIVE research round (benchmark vs OWASP ASVS 5.0): V3 "Web Frontend Security" was the
one category-level gap — the existing Security section covered XSS/CSP/secrets/localStorage but not the
browser-native control cluster. Five deltas added to `frontend-a11y.md`, each MDN-verified this session
and scoped (not overclaimed):

- **postMessage** — a `message` listener must validate `event.origin` (+ message shape) before trusting
  `event.data` (any origin can post; CWE-346).
- **Subresource Integrity** — `integrity` + `crossorigin` on third-party/CDN `<script>`/`<link>` so a
  CDN compromise can't run arbitrary code in every browser.
- **Trusted Types** — `require-trusted-types-for` as a DOM-XSS backstop on top of output encoding
  (Baseline 2026; tinyfill for older browsers — scoped, not claimed universal).
- **Referrer-Policy** — the modern default is already safe, so the finding is a *weakened* policy or a
  token-bearing URL leaking via `Referer`.
- **Clickjacking** — promoted from a bare header-name in A02 to a named threat + per-page
  `frame-ancestors`/`X-Frame-Options` verification on authenticated/state-changing pages.

Three evals (deep-code-review 210 -> 213). Sources: 4 MDN pages fetched + logged; OWASP ASVS 5.0 V3
by name. Trio -> 1.195.0. `SHA256SUMS` regenerated last.

## [1.194.0] — 2026-09-19

### deep-code-review — wave 115 LLM streaming / completion-delivery review (security-ai-agents.md)

From a round-3 research scout (verified genuine at source; the standard LLM-app items are covered under
LLM01/10 + LLM06 + testing-and-evals RAG + privacy egress — streaming/completion-delivery mode was the
zero-hit gap). Added as ONE bullet in "Defensive patterns to look for" (keeping the OWASP LLM01–LLM10
enumeration a clean 1:1 walk), no new external source (under OWASP LLM Top 10 2026, already logged).

- Check `finish_reason`/`stop_reason` before use (a length/safety-truncated 200 read as complete) — LLM10.
- A complete-string moderation/sanitizer guard must run on the ASSEMBLED stream, not per-chunk — LLM10.
- Chunk-boundary evasion (a payload split across two chunks passes a per-chunk sanitizer) — LLM10.
- A client disconnect must cancel the upstream generation (non-cancelled generation burns billed tokens;
  distinct from pre-dispatch caps) — LLM06; cross-ref the abort-wiring discipline in reliability-error-handling.md.

Three evals (deep-code-review 207 -> 210). Trio -> 1.194.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): FIX-FIRST -> applied. Moved all 4 deltas out of the mid-OWASP-list splice
into "Defensive patterns" (one bullet, LLM10/LLM06 tagged) so the LLM01–LLM10 walk stays 1:1; rewrote
the client-disconnect eval to withhold the mechanism and make the "distinct from pre-call caps"
expectation discriminate; added the reliability-error-handling cross-ref. No fabrication/overclaim found.

## [1.193.0] — 2026-09-19

### deep-code-review — wave 114 resource lifecycle / leak review

From an industry-research scout (verified genuine at source; acquire/release-on-error-path already
covered by A10, unbounded-cache/goroutine-leak already covered — these 3 sub-patterns were zero-hit).
Engineering-judgment deltas, no new external citation.

- **A subscription/listener/observer that outlives its subscriber is the same lifetime mismatch** —
  the live emitter retains the dead subscriber (no GC) and its handler fires on detached state; pair
  register with deregister on teardown. → `concurrency-shared-state.md` (+ 🚩 footer widened).
- **Listener/timer/subscription with no teardown** (`addEventListener`/`.on`/`.subscribe`/
  `setInterval` with no matching removal; a `useEffect` with no cleanup) → `language-stack-redflags.md`.
- **A pool connection not released on the error path starves the pool**; pool exhaustion as its own
  symptom → `performance-db-cost.md` (cross-ref `security-appsec.md` A10 for the general form; 🚩 grep
  extended).

Three evals (deep-code-review 204 -> 207). Trio -> 1.193.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): PASS-WITH-NITS -> applied (widened the concurrency 🚩 footer to match the
extended lifetime class; added the pool-exhaustion pattern to the perf-db-cost 🚩 grep; cross-ref'd
A10 from the pool bullet). No-duplication and correctness verified clean.

## [1.192.0] — 2026-09-19

### deep-code-review — wave 113 API/SDK evolution & deprecation discipline (api-contracts.md)

From an industry-research scout (verified genuine at source; the file's header claims "SDK boundaries"
scope but the body was HTTP-only, and SemVer-MAJOR was stated without a recognition taxonomy or a
mechanical check). New section between "Public interface hygiene" and "Webhooks".

- **Breaking-change recognition taxonomy beyond remove/rename** — stricter validation, changed
  default, new required param, widened/nullable output, added enum member; + the forward-compatibility
  mirror; + a public exported symbol / CLI flag is a contract like an HTTP response (fulfils the SDK
  scope the header claims).
- **Mechanical surface-diff CI gate** distinct from hand-written contract tests (which catch only what
  was asserted) — per ecosystem: `oasdiff` / `buf breaking` / `cargo-semver-checks` (by name).
- **Removal needs a sunset window + usage precondition** — the HTTP `Sunset` header (RFC 8594) as the
  machine-readable signal, and call-volume evidence before dropping (skip rather than guess). Distinct
  from security-appsec's zombie-route sunset.

Three evals (deep-code-review 201 -> 204). Source: RFC 8594 (Informational) fetched + logged this
session. Trio -> 1.192.0. `SHA256SUMS` regenerated last.

## [1.191.0] — 2026-09-19

### deep-code-review — wave 112 feature-flag & experiment correctness (release-engineering.md, domain K)

From an industry-research scout (verified genuine at source; lifecycle / kill-switch / both-states /
PII already covered — these three were the absent slivers, on the code-review side vs growth-analytics'
read side).

- **Experiment assignment is reviewable code** — deterministic hash(unit+salt), not Math.random /
  session-scoped; unit stable across logout→login; exposure fires at variant-render, not page load; an
  SRM guard wired (a high-sensitivity signal the assignment/exposure pipeline is broken — several
  causes, not one). Extends the Experiment-toggle bullet.
- **Pin the evaluated flag value once per request/transaction** — re-eval mid-request renders a
  composite of both paths; a config-read consistency bug, not a data race; complements TTL-caching the
  fetch (cache the fetch, pin the value).
- **Provider-unreachable default per flag category, and disambiguate "closed"** — fail-open is the bug
  for a risky feature; release-toggle-closed = old path, ops-kill-switch safe default = engaged.

Three evals (deep-code-review 198 -> 201). Sources by name (Fabijan KDD-2019 SRM; Kohavi et al.). Trio
-> 1.191.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): PASS-WITH-NITS -> applied. Must-fix: a cross-ref to a non-existent
"migration-parity.md consistency rule" was repointed to the real lifetime-mismatch rule in
`concurrency-shared-state.md` (verify-before-cite). Also: corrected an eval's OWASP section (A06 not
A07), scoped the SRM claim to a multi-cause symptom (not a pointer to the bucketing code), and dropped
an uncued TTL sub-expectation from the pin-once eval.

## [1.190.0] — 2026-09-19

### deep-code-review — wave 111 telemetry / analytics-event correctness (data-quality.md)

From an industry-research scout (verified genuine at source; PII-in-analytics + consent were
already covered in `privacy-compliance.md`, and one-definition-per-metric in `growth-analytics` —
these three were the absent slivers, at the data-quality × api-contracts intersection).

- **An externally-consumed event is not dead-pipe just because no in-repo reader exists** — the
  artifact→consumer census misfires for a `track()`/`emit()` whose consumer is a vendor
  dashboard / warehouse / funnel; rename/removal of a published event is a breaking change, not a
  cleanup. Carve-out added to the census bullet (§5), cross-ref `api-contracts.md`.
- **Test/QA traffic pollutes the metric denominator** the same way an ineligible type does —
  filter at the emitter/ingestion boundary (enforced once), not a per-dashboard `is_test` filter.
  §4 denominator-integrity.
- **Outcome-correlated sampling biases the metric** — sample at a uniform known rate
  (reweightable) or independently of the measured outcome. §8.

Three evals (deep-code-review 195 -> 198). No new external source (engineering-judgment deltas).
Trio -> 1.190.0. `SHA256SUMS` regenerated last.

## [1.189.0] — 2026-09-19

### deep-code-review — wave: numeric correctness at a boundary

From an industry-research scout (verified genuine at source; float-for-money was already covered,
these boundary-crossing numeric mechanics were absent by repo-wide grep).

- **Integer past 2^53 across a JSON boundary is silently rounded, not rejected** — JSON numbers
  interoperate as IEEE 754 double, exact only for integers in [-(2^53)+1, (2^53)-1] (RFC 8259 §6);
  a 64-bit id / large amount sent as a JSON number arrives changed while `type: integer` still
  passes. Send as strings or a documented range contract. → `api-contracts.md`.
- **Non-finite results (NaN/±Infinity) don't fail loud on the float path** — they poison
  min/max/sort/aggregate (NaN compares false to everything). Scoped honestly: many languages guard
  division (Python's `/` raises), and encoders diverge on non-finite output (JS → null, Python →
  non-standard token, Go → error), so the "silent null" outcome is stack-specific, not universal.
  → `domain-checklists.md` domain A.

Two evals (deep-code-review 193 -> 195). Sources logged in `docs/standards-index.md`: RFC 8259
(STD 90) + CWE-1339 (fetched 2026-09-19); IEEE 754 added to the by-name list (paywalled). Trio ->
1.189.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): FIX-FIRST -> applied. The non-finite claim was overclaimed as a
universal (empirically false: Python `/` raises, `json.dumps(NaN)` emits a token, Go errors) —
rescoped to the unguarded-float path with per-stack encoder behavior, and the eval pinned to
Node/JS so its expectations stay sharp. IEEE 754 was cited but unindexed — added by-name.

## [1.188.0] — 2026-09-19

### deep-code-review — wave 109 i18n / Unicode-security depth (domain R)

From an industry-research scout (verified genuine at source; all 4 sub-checks were absent by
repo-wide grep). Domain R was already a routed lens (bidi/Trojan-Source, NFC/NFD, collation,
timezone all covered) — these are the missing sub-checks, added as depth, not a new lens.

- **Unicode confusables / mixed-script homograph** — a user-controlled string rendered as a
  *trust signal* (domain, sender name, package name, username) needs confusable / mixed-script
  detection, not just HTML-escaping; visual identity ≠ string identity. Mechanism depth (UTS #39
  skeleton / mixed-script / restriction levels) in `i18n-l10n.md` next to the bidi sibling;
  security framing (STRIDE Spoofing at the display layer) as a bullet in `security-appsec.md` A06.
- **Locale-dependent case-folding** (Turkish ı/İ, German ß→SS) — a case-insensitive compare/key
  must use Unicode case-folding, not an ASCII `lower()/upper()` round-trip. `i18n-l10n.md`.
- **Grapheme-cluster-safe truncation** — slicing on bytes/code-units splits surrogate pairs and
  ZWJ/combining sequences (mojibake); truncate and count on UAX #29 grapheme clusters. `i18n-l10n.md`.
- **Locale-formatted input parsing** — `1.234` is 1234 or 1.234 by locale; a naive parse is a
  silent 1000× data-integrity bug. Parse against the input's locale or require a machine format.
  `i18n-l10n.md` (read-side counterpart to the existing output-formatting rule).

Three evals (deep-code-review 190 -> 193). Sources logged in `docs/standards-index.md`: Unicode
UTS #39 + UAX #29 (both fetched 2026-09-19). Trio -> 1.188.0. `SHA256SUMS` regenerated last.

## [1.187.0] — 2026-09-19

### agentic-delivery — wave 108 autonomous-loop epistemology + auto-close hygiene

- **#423** (SKILL.md gate epistemology, new principle 12): an apparent owner-fork that a
  ratified invariant (no-data-loss, a security/a11y floor, a monotonic-quality rule) already
  decides is not a human gate — applying the invariant is a lane's mechanical job; escalate
  only the genuine forks the invariants leave open.
- **#476** (fast-agentic-delivery.md, sibling to the under-close section): the over-close
  mirror — a close keyword fires the *whole* referenced issue on merge, so an umbrella/epic
  or partly-advancing PR must use a non-keyword link (`Part of #N`); and the parser is purely
  textual, so a keyword only *quoted* while explaining a bug still closes the issue. A split
  clause states which section governs which case; it does not license parking a G7-complete item.
- **#413** (fast-agentic-delivery.md, ownership-map absence-check): `gh`/issue state is blind
  to local-only branches, worktrees, and unpushed commits, so a forge-only occupancy check can
  read "unclaimed" while a lane is in flight; scan local git too, treating a hit as a lead to
  check for liveness (not proof of an active lane), then adopt-and-re-verify or reconcile it.
- **#421** (SKILL.md principle 3, net-new clause): a conclusion that surprises you is the
  signal to re-fetch the specific state at decision time, not to act on a remembered snapshot.
  (The four-instance unification #421 also proposed is already covered by existing re-verify instances (SKILL.md principles 3/9/11, plus the
  mergeable-snapshot and open-tracker sections) in their own homes — restating it was declined per the no-duplication rule; only this trigger
  clause was net-new.)

Three evals (agentic-delivery 40 -> 43, incl. the over-close discriminator paired with the
existing under-close eval). Trio -> 1.187.0. `SHA256SUMS` regenerated last.

## [1.186.0] — 2026-09-19

Wave 107 — **product-ux data-viz honesty batch: invertibility, heat-cell third state, sparkline, UX auto-merge policy** (#459 + #487 + #486 + #485 + #471; dcr; from the 4-agent parallel triage). Five deltas in `product-ux-quality.md`: **(#459+#487)** a new section — a rendered tier/score/**aggregate encoding** (sparkline tick, heat cell, count) must **invert** to the exact source rows it summarizes (drill-through), or it is decoration that can't be verified or corrected; applies to aggregate encodings, not only per-row chips. **(#486)** a grid/heat-map/calendar cell needs a **third state** (event / collected-zero / not-collected) — an uncollected cell painted as low-activity fabricates "quiet" where the truth is "unknown" (grid form of observed-low-vs-unobserved). **(#485)** named the **sparkline** case in the sparse-line rule. **(#471)** a UX-bearing change does not **auto-merge** on code/build/lint + presence-only evidence, and a disabled UX-quality gate is a **P0** blocking that change-class. Inline 🚩 on the invertibility section and the auto-merge policy. Three evals (deep-code-review 187 -> 190). Trio -> 1.186.0. Closes #459, #487, #486, #485, #471.

Dogfood reviewer (sonnet): PASS-WITH-NITS → applied. MED: added a carve-out so the invertibility rule does not collide with the decorative-chart (`aria-hidden` + printed-number) exemption above; delivered #471's third practice — screenshot the **whole affected surface**, not a clip of only the diff's region — so "Closes #471" is honest. LOW: corrected "Inline 🚩 on each" to the two sections that actually got one; backlinked the heat-cell bullet to "Every data state" (link-don't-restate). Nit: de-gifted eval 1's prompt.

## [1.185.0] — 2026-09-19

Wave 106 — **data-quality integrity batch: re-attribution drops, connected-component over-merge, freshness decay-curve fabrication** (#446 + #465 + #463; dcr; from the 4-agent parallel triage). Shared spine: a data-integrity gate/count/curve must reflect OBSERVED reality, not a blind count or an invented model. **(#446, §1)** an identity/roster/ER change re-keys attribution across cached signals, so a volume drop may be a correction (re-attributed / poisoned-as-ambiguous) not a regression — investigate the fold before ack/block (the gate is the trigger, the fold is the adjudication). **(#465, §3)** raw connected-components over-merge (spurious A~B + real B~C); run graph metrics — a single-artifact bridge edge / low centrality flags the false merge a shared-key gate misses. **(#463, §8)** a binary in-window freshness gate is observable and ships; a continuous decay curve (`0.5^(days/half_life)`) is a banned fabricated number (invented half-life), and vendor half-lives are not data. Three 🚩 flags. Three evals (deep-code-review 184 -> 187). Trio -> 1.185.0. Closes #446, #465, #463.

Dogfood reviewer (sonnet): FIX-FIRST → fixed pre-merge. HIGH: a wrong graph-theory claim — a bridge edge has *high* betweenness centrality (Girvan-Newman), so "low centrality = weak link" was inverted; replaced with **low neighborhood overlap / embeddedness** (the actual weak-tie signal), in the section and the eval. MED: scoped #446 against the run-over-run drift guard in the same section ("beyond-attrition drop = regression" is the trigger to investigate, not the verdict). MED: softened an unsourced vendor-half-life provenance claim to "unverified unless it traces to a primary source" (no-fabrication, in-section and eval). LOW: relabeled the decay curve a **fabricated constant** (Principle 2), not "model-authored" (no model in `0.5^(days/hl)`).

## [1.184.0] — 2026-09-19

Wave 105 — **autonomous-terminus honesty batch: verify every work queue + enumerate don't keyword-filter** (#445 + #450; agentic-delivery). Two coherent `fast-agentic-delivery.md` sections — the two halves of "terminus is a claim about ALL work": **(#445)** before declaring done, enumerate EVERY work surface (issue tracker(s), a gaps/todo queue, a debt/critique file, failing/skipped tests, TODO comments, an open-review backlog) and confirm each drained-or-blocked — "I finished my queue" is not "nothing left"; name the queues checked; the delivery-side analog of the review coverage-ledger reconcile (`method.md`). **(#450)** discover work by enumerating the surface, not a keyword/title filter (titles are lossy — a docs/CI/security item may lack the keywords; mind pagination) — a filter orders a known-complete set, never defines it; state the filter when claiming done. Each with a 🚩 tell. Two evals (agentic-delivery 38 -> 40). Trio -> 1.184.0. Closes #445, #450.

Dogfood reviewer (sonnet): PASS-WITH-NITS → 3 polish fixes applied. Cross-linked the terminus section to this file's own termination-conditions bullet (it generalizes "backlog empty" to "every surface"); generalized the pagination note (dropped a GitHub-specific "~30 rows" stated as generic — the eval stays GitHub-specific, correctly); moved the `---` back-matter divider back to before `## Sources` (the insert had stranded it). Verified clean: no-duplication (vs work-loop / go-faster / research-not-delivery + method.md), correctness, eval discrimination, 🚩-tell convention.

## [1.183.0] — 2026-09-19

Wave 104 — **soft-delete & referential-integrity correctness** (#493; dcr, data-lifecycle lens). Extends `data-quality.md` §6 (lifecycle) — which already noted deletes-are-soft + erasure — with the **correctness** angle (distinct from the privacy-erasure obligation): once a table has a `deleted_at`, every read / JOIN / COUNT / uniqueness check must exclude deleted rows via a **default-scoped accessor**, not drift-prone per-call-site filters; a `UNIQUE` column needs a **partial index** (`WHERE deleted_at IS NULL`) or the tombstone blocks re-creating the value; delete semantics across FKs are deliberate — `ON DELETE CASCADE` can over-delete (shared/audit rows), a hard delete under-deletes (dangling FKs / orphans), and a soft-deleted parent with live children is a leak. Three 🚩 flags; cross-refs `privacy-compliance.md` (erasure). Two evals (deep-code-review 182 -> 184). Trio -> 1.183.0. Closes #493.

Dogfood reviewer (sonnet): FIX-FIRST → SQL-correctness fixes applied pre-merge. (HIGH) the UNIQUE "fold the delete marker into the key" fallback was unsafe as written — a bare nullable `deleted_at` in a composite `UNIQUE` lets duplicate **live** rows through (`NULL ≠ NULL` on Postgres/MySQL/SQLite); qualified it to require a **non-null** sentinel. (MED) the dangling-FK claim was unconditional — an *enforced* FK with `RESTRICT`/`NO ACTION` blocks the delete rather than orphaning; scoped it to unenforced / `SET NULL` relations. (MED) both evals' third expectation required disclaiming an *unprompted* erasure topic (correct-by-silence would fail) → reworded to absence-framing. Rewrapped the long 🚩 line. Verified clean: no-duplication, scope gate, eval-2 discriminator (rejects hard-delete).

## [1.182.0] — 2026-09-19

Wave 103 — **state-machine / lifecycle correctness** (#490; dcr, new lens from the architecture-pattern research). A new section in `reliability-error-handling.md`: any entity with a status/lifecycle (order, subscription, document, job, ticket) is an often-implicit state machine — review it as one, distinct from saga compensation and the dual-write atomicity above. Checks: model the valid `from→to` transition set (a bare `UPDATE status=?` with no from-state check permits `refunded→shipped`); guard each transition with **compare-and-set** in the write, not read-then-write (which races two transitions into a double effect — the state-machine face of the concurrency CAS rule); make **impossible states unrepresentable** (one enum, not a boolean soup admitting `isRefunded && !isPaid`); **no stuck/orphan states** (every non-terminal state has a timeout/exit; terminal states stay terminal); transition **side effects fire once** (cross-ref idempotency + dual-write). Scope-gated to entities with a lifecycle. Two evals (deep-code-review 180 -> 182). Trio -> 1.182.0. Closes #490.

Dogfood reviewer (sonnet): FIX-FIRST → blocker fixed pre-merge + nits. The "No stuck/orphan states" bullet listed "a manual path" as an acceptable exit yet named "an approval that never expires" as the hazard — a self-contradiction (an approval IS a manual path), and it contradicted eval 2 (whose reviewer-approval exit the bullet would have waved through). Restated the discriminating rule: an exit must not depend on **one specific actor** always acting (a timeout/escalation, or a reclaim any eligible actor can take). Nits: qualified impossible-states so genuinely orthogonal flags aren't false-flagged; disambiguated "0 rows-affected" in the eval (absent id vs illegal transition); split the 3-in-1 🚩 clause into three flags.

## [1.181.0] — 2026-09-19

Wave 102 — **test-quality batch: type-check ≠ full suite + tautological property test** (#364 + #373; dcr, testing-and-evals). Two smells added to "What good tests do": **(#364)** a passing type-check / compile is a **partial** gate, not the suite — after a conflict resolution on a long-behind branch a type-correct three-way merge can still fail a behaviorally-pinned test (the other side refactored the pinned shape away); run the full behavioral + regression suite before declaring the resolution correct, and treat a broken pinned test as a signal to re-examine the resolution, not a cue to delete it. **(#373)** a property test whose **generator encodes the invariant it checks** is tautological — it never samples the violating case, passes vacuously, guards nothing; the generator must sample the full input space independently of the property (sibling of the mocked-into-a-tautology smell). Both append a clause to the tail 🚩 block. Two evals (deep-code-review 178 -> 180). Trio -> 1.181.0. Closes #364, #373.

Dogfood reviewer (sonnet): PASS-WITH-NITS → two precision fixes applied. (#373) qualified "independently of the property": constraining a generator to a property's *precondition* is legitimate PBT — the smell is specifically encoding the property's *conclusion*, so the overbroad wording could have false-flagged a well-scoped test (a stricter-than-the-standard risk). (#364) dropped "an arity" from the type-invisible examples — arity IS type-checked, contradicting the bullet's own claim; replaced with a default value. Both mirrored in the evals. Verified clean: no duplication, correctness, 🚩-block, eval discrimination.

## [1.180.0] — 2026-09-19

Wave 101 — **systems-correctness batch: caching-correctness gaps + the dual-write problem** (#478 + #482; dcr). **(#478, performance-db-cost.md)** extends the existing Caching & memoization section (correct key / invalidation / TTL / tenant-isolation were already present — the issue's "0 files" was term-based) with the genuine net-new: **stampede / thundering-herd on expiry** (single-flight or soft-TTL, not a bare TTL), **cache-aside write race** (write-then-invalidate ordering / versioned keys, not set-after-write), **negative caching** (short re-checkable TTL for not-found/errors), and the **authoritative-vs-advisory** contract (a cache as source-of-truth = data loss on eviction). **(#482, reliability-error-handling.md)** a new section on the **dual-write problem** — a local write + a remote publish in two non-atomic steps diverge (lost vs phantom event); fix = transactional outbox / CDC (event in the same transaction, commit-before-publish), fallback = idempotent consumer + reconciliation; scope-gated to cross-system operations, distinct from saga compensation. Both append a clause to their file's tail 🚩 block (`🚩 grep` in performance-db-cost, `🚩 red flags` in reliability). Two evals (deep-code-review 176 -> 178). Trio -> 1.180.0. Closes #482.

#478 stays **open**: this wave shipped its genuine net-new (stampede, cache-aside race, negative caching, authoritative-vs-advisory), but #478's own acceptance also names invalidation-depth (derived/related-key completeness), key-isolation (cardinality / PII-in-key), and TTL-discipline (freshness cadence) as distinct checks **and** requires an invalidation eval — none shipped here, so closing it would over-claim. Those remain a scoped follow-up.

## [1.179.0] — 2026-09-19

Wave 100 — **data-integrity evidence-grading trio** (#458 + #460 + #464; dcr, batched — one theme: a signal's weight depends on provenance/distinctiveness, not raw presence). Three method-level deltas in `data-quality.md`: **(#460, §1)** grade-monotonic write-authority — the non-regression gate must arbitrate a non-empty value-A→value-B overwrite by source grade (refuse `new.grade < incumbent.grade`, keep incumbent on ties), additive to the populated→empty + fanout checks, else a lower-grade source silently overwrites a higher-grade value while the field stays populated; **(#458, §3)** grade a shared value by frequency, not all-or-nothing — a value's match/join weight is inversely related to its commonness (rare = stronger, common = demote as a generic key), via a deterministic value-commonness table + corroboration scaled by commonness; **(#464, §2)** corroboration counts independent *origins*, not distinct domains — collapse derivation (an aggregator / repost / re-cite of one origin is one origin), preferring the conservative count where derivation can't be established. All three are deterministic (no invented scores); #460 extends the non-regression gate (§1) and #458 routes a field-emptying demotion through it, while #464 governs a corroboration count, not a write path. Three evals (deep-code-review 173 -> 176). Trio -> 1.179.0. Closes #458, #460, #464.

Dogfood reviewer (sonnet): FIX-FIRST → both blockers fixed pre-merge + nits. (1) The ledger over-claimed "all route through the non-regression gate" — false for #464 (it governs a corroboration count, not a write path); scoped it. (2) The three deltas added no clause to the file's tail "🚩 red flags" block (its dominant convention, 4-commit precedent) — appended three, and removed #460's lone inline "In review:" question so review-surfacing is uniform. Nits: de-gifted the frequency eval (dropped a parenthetical that handed the "generic value" conclusion), comma-form multi-issue Closes, and cross-referenced §2 source-independence to §7 occurrence-not-attribution (the two halves of corroboration discipline). Verified clean: no duplication, correctness, determinism, eval count 173→176.

## [1.178.0] — 2026-09-19

Wave 99 — **a finished check's green can be stale off a prior evaluation — confirm it ran against the current head, and know each gate's trigger model** (#365; dcr). A new section in `branch-and-merge-hygiene.md` (after mergeable-is-a-snapshot): most gates re-evaluate only on a subset of events (typically a new push) and do NOT recompute on a body/metadata edit, a base retarget, a bot amending the description, or a rebuild another process is mid-way through — so a finished green can certify a state that no longer exists. Two shapes: merging while another lane still owns the change (green belongs to the pre-rebuild head → lands an intermediate state), and a gate reading a stale cached artifact/body. Rule: read the SHA/input-digest the passing check ran against vs the merge target (pin-to-SHA, `method.md`), and know each gate's trigger model so a mutation it does not cover is recognized as invalidating. The verdict-staleness sibling of the moving-base cases (mergeability-snapshot / stale-base gate-diff) and distinct from a check that never ran. One eval (deep-code-review 172 -> 173). Trio -> 1.178.0. Closes #365.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + two nits. The do-not-recompute list wrongly included "a rebuild/rebase mid-way," but a rebuild that pushes a new head DOES fire the push/synchronize trigger — and the section's own advice said to "wait for the gate to re-evaluate," contradicting the trigger-coverage label. Restructured into two clearly-labeled causes: **trigger coverage** (body/metadata/retarget/cached-artifact — the check never re-runs) and **timing** (a rebuild fires the trigger but its run is still in flight — the visible green is the pre-rebuild one). Nits: relocated the inline 🚩 to the file's bottom "🚩 Red flags" list (its established convention; the sibling §236 hazard sits there too), and dropped an eval clause about "an actor still mutating" that had no hook in the eval's completed-edits scenario.

## [1.177.0] — 2026-09-19

Wave 98 — **a completion claim in a PR body or handback carries a `Verify:` line, or it is unverified** (#401; agentic-delivery). A new section in `fast-agentic-delivery.md`: a delivery lane's PR body / handback that asserts a verified outcome ("tested and working," "confirmed in the browser") is a self-reported claim, not evidence — it is auditable only if it carries a `Verify:` line naming HOW (the command run, the surface exercised, the evidence link). Without it, treat the claim as `unverified` and ask for the method, not the adjective (a false "done" is trusted, built on, and surfaces late). The constructive form of the over-claim rule applied to the delivery artifact — a **claim-quality** requirement, NOT a trusted control (still self-reported; the SHA-pinned forge run is the control — cross-ref `branch-and-merge-hygiene.md` self-reported-evidence). Pairs with visual evidence (what changed vs how confirmed) and the co-evolve-the-gate-with-its-producers rule (gate on `Verify:` only if the lane template emits it). One eval (agentic-delivery 37 -> 38). Trio -> 1.177.0. Closes #401.

Dogfood reviewer: PASS-WITH-NITS → no blocker; no-duplication verified airtight (the `Verify:`-convention definition is genuinely new — `branch-and-merge-hygiene.md` §378 only names "a `Verify:` line" as one item in a list of body-gate conventions, never defines it; §412's mechanism is cross-reffed, not re-taught), and consistency with §412 (claim-quality not a trusted control) + §378 (co-evolve) confirmed, placement load-bearing, insertion-hazard sweep clean. Applied two nits: labeled the new red flag `🚩 tell:` to match the file convention, and tightened its tail so "unverified until the method is stated" cannot read out of context as "method stated ⇒ verified" (still self-reported after; the forge run is the control).

## [1.176.0] — 2026-09-19

Wave 97 — **ML fairness — detect it in review, never certify it** (#457; dcr, new area from the research cron). A new section in `testing-and-evals.md` (after the ML cluster): a fairness DETECTION lens for a default review, which had none (0 fairness content). **Scope-gated first** — applies only to a consequential decision about people with a group dimension in the data, else say so and stop (avoiding a fabricated "stricter than the standard" finding). Detects: protected-attribute direct use (disparate treatment) vs proxy (disparate impact) — a proxy is **demonstrated** by in-data correlation, never asserted, and absence of the attribute is not fairness (nor is blindly dropping a suspected proxy); requires a **disaggregated** evaluation with a **stated, justified** fairness metric (flagging the absence of a choice, not prescribing one); flags a missing model card (per-subgroup performance, Mitchell et al. 2019). Cross-refs `data-quality.md` §4 (dataset representativeness), `product-output-safety` (the output-harm guardrail — inventory / never-certify / measure — **not restated**), NIST SP 1270 (bias taxonomy), and the coverage-not-grade rule. Three evals (deep-code-review 169 -> 172). Trio -> 1.176.0. Standards logged (NIST SP 1270 read direct, Model Cards — both 2026-09-19). Closes #457.

Dogfood reviewer: FIX-FIRST (close call) → both fixes applied; everything else cleared (no-duplication vs `product-output-safety`, both sources verified to primary, eval-discrimination incl. the drop-the-feature guard, correctness, no metric-impossibility overreach). MAJOR: the scope gate's **inverse** — the fabricated-finding it exists to prevent — was unevalled, while the suite pervasively plants the does-not-apply case as an executable test; added a third eval (an out-of-scope demand-forecast model whose null manufactures a fairness finding → fails all expectations). NIT: legal terms of art ("disparate treatment/impact") appeared in-body with counsel-routing only in provenance; added an in-section clause routing the unlawful-or-not determination to counsel (`business-ops` Lane R), mirroring `product-output-safety` — the code finding is the missing measurement, never a legal verdict.

## [1.175.0] — 2026-09-19

Wave 96 — **MCP (Model Context Protocol) server/client security — the topology's delta** (#453; dcr, new area from the research cron). A new section in `security-ai-agents.md`: when the target is/hosts/connects to an MCP server it inherits a new principal + two surfaces the general agent-security lenses do not cover by default. Three labelled families, each specializing a general lens (not restating it): **(1) authorization in the proxy topology** — OAuth-proxy confused deputy (per-client consent MUST precede the third-party flow), token passthrough forbidden (`aud` must be the MCP server; no upstream-token forwarding — cross-ref A07), least-privilege scopes; **(2) consent-UI fidelity & local-server execution** — a one-click local server runs code with the client's privileges, so the exact untruncated command MUST be shown (approved bytes == executed bytes; cf. ASI09); **(3) tool metadata is untrusted, model-read instruction surface** — tool-description poisoning (hidden docstring directives the user does not see) and rug-pull (definitions mutate post-approval -> pin/hash + re-approve on change; extends ASI04). OWASP MCP Top 10 named as a **beta** regime only (no category IDs walked). Two evals (deep-code-review 167 -> 169). Trio -> 1.175.0. Standards logged (official MCP security spec, OWASP MCP Top 10, Willison/Invariant Labs — all fetched 2026-09-19). Closes #453.

Dogfood reviewer: PASS-WITH-NITS → no blocker. The fabrication pass was clean (the reviewer re-fetched all three sources; every `MUST`/quote/status verbatim-faithful), and duplication + eval-discrimination were verified. Applied the cheap nits, several serving the repo's own thesis: added MCP to the file's read-this-when trigger and the `SKILL.md` agent/LLM domain row (a standalone MCP server with no LLM now routes here); cross-linked the new tool-metadata section to the existing "trust the transport, not the payload" bullet (the third MCP trust leg); fixed the intro's "two surfaces" -> three (parallelism with the three families — the same enumeration discipline W94 corrected); dropped quote-marks on two illustrative glosses (the verbatim quotes live in `docs/standards-index.md`); softened "Official OWASP GenAI project" -> "Official OWASP project" in the ledger (the GenAI umbrella was not confirmable from the project page); "steal the code" -> "steal the MCP authorization code"; `MCP0x` -> `MCPxx`.

## [1.174.0] — 2026-09-19

Wave 95 — **a new PR-body / artifact gate is a contract with its producers — co-evolve them, or every automated PR silently fails it** (#411; dcr, branch-and-merge hygiene). A new section in `branch-and-merge-hygiene.md`: adding a gate that requires a convention in the PR **body** or a committed **artifact** (a `Verify:` line, a changelog fragment, a commit trailer) silently fails every producer that does not yet emit it. §5's "sequence the gate-adding PR last" handles the in-flight batch; this covers **standing** producers — PR templates, Dependabot/Renovate, release bots, agent swarms — which keep emitting the old shape on every future run until their **definition** is updated (automation cannot "just adapt" like a human author). Practices: co-evolve gate + producers in one change; grandfather/ramp (warn-only or apply-after-date); make the failure name the exact fix; inventory the producers first. Review lens + 🚩. Cross-referenced to the merge-train ordering rule (§5) and the message-payload sibling in `api-contracts.md`. One eval (deep-code-review 166 → 167). Trio → 1.174.0. Closes #411.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + a lockstep co-fix + a nit. The eval's expectation 2 (and expected_output) accepted a bare "apply the gate to PRs opened after a date" as a valid ramp — but a **past-dated** cutoff does nothing for a **standing** producer (its next run is always after any past date), the exact failure the section teaches, so a plausible wrong answer could have scored full marks. Qualified the ramp to a bridge (warn-only or a *future* cutover) with co-evolving the producer definitions as the primary fix, and fixed the same imprecision in the section's "Grandfather or ramp" bullet in lockstep. Nit: reworded a self-contradictory "fails it green-but-unmergeable" red flag (a failing check is red) to "refused — green on its real work, red on the new gate". Reviewer verified NO DUPLICATION (extends §230 + `api-contracts.md`, both distinct), cross-refs resolve, and the null-answer discrimination holds.

## [1.173.0] — 2026-09-19

Wave 94 — **a producer crossing a publish/trust boundary invalidates guards scoped to the old side** (#399; dcr, A06 Insecure Design + the DIFF blast-radius rule). A new bullet in `security-appsec.md` A06: a guard's sufficiency is often conditioned on a precondition ("internal only / never published / dry-run / behind auth"); when a change wires the producer **across** that boundary (to a published/external consumer), every guard justified by the old precondition must be **re-audited** — a weaker guard that was fine "because it never publishes" now ships its excused defect to the public surface (a false attribution). Two things hide it: the defending comment is now **stale** yet reads authoritative, and the guard + the boundary-crossing edit live in **different files** (a diff-scoped review sees one, not the other). Added the trigger to `SKILL.md`'s DIFF blast-radius 🚩 list. One eval (deep-code-review 165 → 166). Trio → 1.173.0. Closes #399.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + a nit. The blast-radius list header read "(each obliges Phase 3 anon-GET / two-principal probes)" — a universal the new producer-crossing member **falsifies** (its remedy is a guard re-audit, not a reachability/scoping probe; a reviewer following it literally would run the wrong probe and wrongly clear the case). Reworded to name the obligation per class (anon-GET / two-principal for the access items; a guard re-audit for the producer-crossing one). Nit: relocated the A06 cue to a standalone 🚩 bullet (off the mid-bullet position) and de-duped a "stale" echo.

## [1.172.0] — 2026-09-19

Wave 93 — **a green run is a sample, not a proof, when the trigger is nondeterministic or the run is too costly to repeat** (#414; dcr). A new section in `testing-and-evals.md`: some fixes can't be validated in one session (a ~1-in-N nondeterministic trigger; a ~20-min run where one pass isn't proof), so shipping on a single green run is a false "done" — distinguish **validated** from **happened-to-pass-once**. Ship the part you *can* validate; **name the part you can't as a Known-limitation** in the PR body with a concrete follow-up (a named residual is honest, a silent one ships a false done); don't let "while I'm here" scope-creep bolt an **unproven** refactor onto an otherwise-validated PR; symmetric with refusing a **placebo** fix proven not to work. Trailing 🚩 line added. One eval (deep-code-review 164 → 165). Trio → 1.172.0. Closes #414.

Dogfood reviewer: PASS-WITH-NITS → two applied. Added a closing cross-ref distinguishing this *ran-green-but-once* residual from a *deferred / never-run* gate (`parallel-audit.md`'s "an unrun matrix is `unverified`, not a pass") and `SKILL.md` principle 2 — both resolve the same way (name the residual, never a silent pass), linked not restated (verified parallel-audit:459 carries that spine). And added a placebo hook to the eval prompt so its symmetric-with-placebo expectation tests scenario reasoning, not lesson recall.

## [1.171.0] — 2026-09-19

Wave 92 — **adding a new dependency is a governance decision, not an implementation detail** (#439; dcr). A new §4 in `dependency-currency-and-upgrades.md` (sections 1–3 keep *existing* deps current; this covers *taking on a new one*): a new runtime dependency is a long-term liability the maintainer carries — bundle-size/perf, supply-chain/security surface (the whole transitive tree), license, maintenance — so it is an **owner/maintainer decision**, not one an agent or feature PR can unilaterally own. Report "needs a new dep" as **BLOCKED-ON-OWNER** with the exact dep + tradeoff (never a fait-accompli `npm install`); check for a lighter path first (existing capability / bundled lib / native API); calibrate by weight (tiny/ubiquitous/audited routine, heavy/novel/broad-surface = owner's call). Review lens + 🚩: a PR adding a manifest dependency alongside a feature — necessary, minimal, maintained, approved? The global confirm-before-a-lasting-commitment rule applied to the dependency manifest. One eval (deep-code-review 163 → 164). Trio → 1.171.0. Closes #439.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + one nit. Two cross-refs — "different severities (see §4)" and "rank it per §4" — are about **severity** but pointed at §4; they were **dangling on origin/main** (no §4 existed) and would have become **active misdirection** the moment this PR added a real §4 (new-dep governance). Re-pointed both to **§3** (Severity discipline) — which also fixes the pre-existing latent bug (do-no-harm: the PR must not regress the accuracy axis of the file it edits). Nit: added a cross-ref from §4 to §2's slopsquat / established-package check (governance = *whether* to add; §2 = the added dep's *integrity* once approved).

## [1.170.0] — 2026-09-19

Wave 91 — **a negative-assertion (assert-absent) test is a ratified constraint — never loosen it to ship a conflicting feature** (#432; dcr). A new section in `testing-and-evals.md`: a test asserting something is **absent** (`assert.doesNotMatch(brief, /ProgressBar/)`, "no attainment %") encodes a deliberate, often-ratified design constraint. When a feature request conflicts, the **wrong** move is to delete/loosen the guardrail to pass (silently reversing a ratified decision — the code-review equivalent of pulling the smoke detector); the **right** move is to read the negative test as intent, ship only the non-violating part, and report the conflict as **BLOCKED-ON-OWNER** (changing a ratified constraint is an explicit owner-visible commit, never a feature-PR side effect). Review lens + 🚩: a diff that loosens/removes an assertion — especially an absence assertion — while adding a feature. Pairs with `product-ux-quality.md`'s *show coverage, not a grade* (the test that pins the omit-attainment contract); distinct from the retired-because-unreachable-spec case (owed a named gap). One eval (deep-code-review 162 → 163). Trio → 1.170.0. Closes #432.

Dogfood reviewer: PASS-WITH-NITS → three applied. Trimmed an eval expectation whose second clause demanded cross-doc navigation a correct "can I delete this test?" answer needn't volunteer (a false-negative risk); rewrapped the appended 🚩 line to the block's width; and reworded "the enforcement half of" → "a test-layer enforcement of" *show coverage, not a grade* (that section already carries its own 422-gate + contract enforcement). The flat imperative title was kept per house style (body hedges "often-ratified").

## [1.169.0] — 2026-09-19

Wave 90 — **a published standard is the constructive escape from an invented score — check both the definition and the *selection* layer** (#396; dcr, domain D / anti-fabrication). A new bullet in `data-quality.md` §7: instead of an "invented composite index" or inferred human-judgment score, adopt an external **published standard** whose definition is the spec, not the tool's judgment (examples named **by name only**: CHAOSS, Fellegi-Sunter, W3C PROV, rel=me / ORCID / schema.org `sameAs`, network-science centrality, ESCO / O*NET). **The subtle trap it closes:** citing each metric's spec while **hand-picking which metrics to include** re-introduces the invented index *one level up* — the selection becomes editorial judgment, hidden because every row still has a spec URL. Two-layer + observability check: each metric a cited **definition**; the metric **selection** itself a cited published **model** (not a tool-chosen set); each metric's **input observable**; deviations recorded per metric with a reason. Corollary: a standard often supplies an honest **skip band** for free (Fellegi-Sunter's possible-match tier). The named standards are added to `docs/standards-index.md`'s **by-name** list (not fetched this session). One eval (deep-code-review 161 → 162). Trio → 1.169.0. Closes #396.

Dogfood reviewer: PASS-WITH-NITS → two precision nits applied; the reviewer confirmed the provenance is clean (all six standards characterized at category level only, no version/figure/URL asserted, in the by-name list) and noted the wave correctly **omitted** #396's one spec-level claim ("CHAOSS metric-models refuse a single roll-up") that would have needed a fetch. Nits: restored "redundant **with a system that already observes it**" (the observability check had dropped the with-what); and re-labelled the standards-index group **network-science structural-position measures** since Burt structural holes is a brokerage/position measure, not strictly a centrality index.

## [1.168.0] — 2026-09-19

Wave 89 — **show coverage/readiness, never a fabricated attainment/grade** (#407; dcr, domain P product-UX honesty). A new section in `product-ux-quality.md`, paired with the confidence-false-precision section: a progress bar / `%-complete` / grade with **no honest current reading is a fabricated "done"** — the honest alternative is **coverage/readiness** ("N of M key results measurable/instrumented"), always computable, and for an unmeasured item render **"awaiting reading"**, never a manufactured number. Enforce structurally, not by convention: a **write-broker/observation gate that 422s** any attainment/on-track claim the system can't substantiate, and a **contract declaring "attainment out of scope"** so a later "add progress bars" ask is triaged as *ratify a rule first*. A display that would honestly be "awaiting reading" on nearly every row is worse than no feature — hold it. Review lens: ask the denominator/rule + measured-vs-inferred. One eval (deep-code-review 160 → 161). Trio → 1.168.0. Closes #407.

Dogfood reviewer: FIX-FIRST (light) → four one-liners applied pre-merge. (1) The new `##` section had added **no pre-ship-checklist line**, breaking the file's strict section→checklist convention (the rule was inert at the checklist layer) — added one. (2) Added an explicit **boundary sentence** vs the paired confidence-tier section (there a reading exists but is rendered false-precise; here no honest reading exists, so any grade fabricates a "done") — the file's adjacent-rules-declare-their-boundary convention. (3) Softened the over-claim "coverage is *always* honestly computable" → "computable without inventing a reading (given an enumerable M and a defined 'measurable')". (4) Split a compound eval expectation (hold-when-mostly-empty vs the review lens) into two.

## [1.167.0] — 2026-09-19

Wave 88 — **corroboration establishes occurrence, not attribution** (#368; dcr, domain D / anti-fabrication). A new bullet in `data-quality.md` §7: an event confidence often fuses three independent propositions — occurrence, role, and **entity-attribution** — and cross-source corroboration (N independent publishers naming the same event) evidences only **occurrence**, never whether entity X was involved. A promotion that lifts the *whole* fused confidence to "fact-grade" on an agreement count silently promotes a **weakly-matched attribution** — the worst axis (a confident false attribution is worse than publishing nothing). The tell: a `min(identity_match, occurrence, role)` confidence **raised** by a corroboration count that only evidences occurrence, overriding the binding minimum that flagged the shaky match. Rule: corroboration may raise only occurrence/role, never past the entity-attribution component — it answers "did it happen," never "whose is it"; safest default, carry the count as unrendered evidence and don't promote a fused confidence at all. One eval (deep-code-review 159 → 160). Trio → 1.167.0. Closes #368.

Dogfood reviewer: PASS-WITH-NITS → three applied pre-merge: the detector moved from a non-conforming inline 🚩 into the file's consolidated 🚩 red-flags index (the file's one-index convention); the descriptive claim aligned to the rule ("evidences occurrence (and role)"); and the "a false attribution is worse than publishing nothing" cross-ref re-pointed from §1 (monotonic-quality) to **§2** (No fabrication — "an empty cell beats a confident-looking wrong one"), its literal home, in both the bullet and the eval (the recurring mis-pointed-cross-ref class).

## [1.166.0] — 2026-09-19

Wave 87 — **the gate's own harness crash is a could-not-check, not a finding** (#372; dcr). Generalizes the canonical cannot-check bullet in `reliability-error-handling.md` from an *external dependency* to the gate's **own harness** (a headless browser, dev/preview server, probe): a crash during harness **setup, before the first measurement**, is a could-not-check — it must not block or be reported as a violation (after bounded transient retries). Adds the specific defect + detector: **a gate that exits the *same* failure code for a setup/harness crash as for a real violation** leaves consumers unable to tell an outage from a finding, so a flaky harness blocks everything and trains blanket-overrides (which then suppress the real findings too) — require **distinct exit semantics + a distinct message**, and flag any gate whose pre-measurement crash is indistinguishable from a finding. The security/authz/integrity fail-closed exception is unchanged. One eval (deep-code-review 158 → 159). Trio → 1.166.0. Closes #372.

Dogfood reviewer: PASS-WITH-NITS → one clarity nit applied. The security/authz/integrity/spend exception now explicitly names **its own harness failing to launch** as a can't-verify that still fails **closed** — foreclosing a literal misread of the newly-broadened fail-open list (the reviewer verified security gates were never actually made to fail open: the exception is a categorical by-gate-class override, and a harness crash is a can't-verify). The novel exit-semantics detector (same code for crash and violation is the defect), the base-vs-overlay layering vs `fast-agentic-delivery.md`, and the eval's strict quality-vs-security boundary expectation were each confirmed clean.

## [1.165.0] — 2026-09-19

Wave 86 — **an auto-merger scopes by a manufactured ownership signal, not by author** (#424; agentic-delivery). An auto-merge/auto-rebase system must act on agent PRs and never on a human's own — but "merge PRs authored by the bot" **fails when agents authenticate as the human** (agent lanes run `gh` under the owner's token, so every PR shows the same author; observed: a human-owned design PR shared the agent author and was distinguished only by a semantic read — had it gone mergeable the drainer would have merged unfinished work). New section in `fast-agentic-delivery.md`, right after the queue-drainer section (that iterates the candidate set; this decides which PRs are in it): give agents a **distinct identity** (bot account / separate `GITHUB_TOKEN`) so authorship discriminates; else key on an **explicit convention** (allowlist / denylist / `agent-mergeable` label / `bot/*` vs `feat/*` prefix) and **default-deny anything not positively marked agent-owned**. General: automation on shared artifacts needs a reliable ownership signal — when identity is shared, manufacture one, don't infer from a field every actor shares. One eval (agentic-delivery 36 → 37). Trio → 1.165.0. Closes #424.

Dogfood reviewer: FIX-FIRST → two corrections applied pre-merge, both verified against primary sources. (1) The 🚩 tell cited `is:author @me` — invalid GitHub syntax (`is:` takes pr/issue/open/closed/…, never author; author filtering is `author:@me` / `gh … --author @me`); corrected, since a fabricated qualifier in a grep-detector line is worse than none (no-fabrication rule). (2) This entry had said the drainer "nearly merged" the human's PR, but #424 is explicit it never became mergeable ("had it become mergeable, the drainer would have"); reworded to the conditional, mirroring the reference file's already-hedged parenthetical.

## [1.164.0] — 2026-09-19

Wave 85 — **safe programmatic git under multi-worktree automation** (#417 + #426; dcr). Two safety rails added to `branch-and-merge-hygiene.md` §6, for agent/automated git where no human eyeballs the diff. **#426:** `git add` stages on-disk content including conflict markers, so `add` exiting 0 is not proof of resolution — and a `[param]`/glob-metachar path (`app/kpis/[key]/page.tsx`) can make `git checkout --theirs` **silently no-op** (glob-expands to a no-match); quote/escape metachar paths (or the shell's glob switch — `setopt noglob` in zsh, `set -f` in bash) and **grep the staged tree for conflict markers, gating on the result** (`git grep --cached -qE '…'` failing on a hit, or `git diff --cached --check`; a bare `git diff -G` prints but exits 0, so it does not gate). **#417:** to update a branch already checked out in another worktree, use a **detached-HEAD fast-forward** (`git worktree add --detach <dir> origin/<branch>` → push `HEAD:<branch>`), never a force-push (which strands that lane's unpushed work on a diverged branch + discards its pushed commits); verify the remote ref is an ancestor first. Two red-flag lines + two evals (deep-code-review 156 → 158). Trio → 1.164.0. Closes #417, #426.

Dogfood reviewer: FIX-FIRST → three empirically-verified corrections applied pre-merge. (1) The marker-grep `git diff --cached -G '…'` **exits 0 even with markers staged** — wired `cmd && commit` it always commits, the exact silent-pass trap it condemned; replaced with `git grep --cached -qE '…'` (exit 0 = found → block) / `git diff --cached --check`. (2) `set -f` disables globbing only in bash/POSIX sh — in **zsh** (the shell the bug lives in) it is NO_RCS and leaves globbing on; corrected to `setopt noglob` / `noglob` for zsh, quoting primary everywhere. (3) A remote force-push does not *clobber* the other lane's unpushed work — it **strands** it on a now-diverged branch (and discards commits already pushed); aligned four sites to the eval's already-correct "strands." All three verified in a scratch repo (bash + zsh, `git grep`/`--check` exit codes).

## [1.163.0] — 2026-09-19

Wave 84 — **a serial queue-drainer must advance past a blocked head, not re-select it** (#400; agentic-delivery). A serial auto-processor (merge-drainer, retry queue, task poller) that picks the first-eligible item each cycle spins forever on one item blocked for a persistent reason — head-of-line **starvation** that looks like *idle*: an auto-merge drainer re-picks the first green+mergeable PR that a stricter final gate (a PR-body lint) keeps refusing, and never reaches the others. New section in `fast-agentic-delivery.md`: the cheap pre-filter (green+mergeable) is **not** the final admission gate; **iterate all candidates and advance past a refusal** (never break + re-select the head); keep a **cooldown / skip-set** with periodic re-eval; **log per-item outcomes** so a spin is visible, not mistaken for idle. Completes the adjacent *sweep the whole ready queue* rule (scan-all ↔ don't-get-stuck-on-the-head). One eval (agentic-delivery 35 → 36). Trio → 1.163.0. Closes #400.

Dogfood reviewer: PASS — clean across all axes, no findings. No-duplication verified distinct from the adjacent *sweep the whole ready queue* (scan-completeness), *mergeable is a snapshot* (stale vs persistently-blocked), *red base* (base-red vs one-item-blocked), and wave 83's *go-faster signal* (agent-side taxonomy vs a concrete stalled instance); both internal cross-ref directions confirmed correct; eval discrimination, the trio version bump, and SHA256SUMS all verified.

## [1.162.0] — 2026-09-19

Wave 83 — **a go-faster signal fires on a clock, not on state; holding is a valid response** (#419; agentic-delivery). The **counterweight** to "an unattended time budget is a work loop" above: that rule says *don't stop while the backlog has work*; this one says *don't fake work once it doesn't*. A recurring pressure signal (a cron, a "why are you stalling?" prompt) fires on a clock, not state, so it keeps arriving when the correct action is to **hold** — async work draining, backlog exhausted or owner-gated (a termination condition), or only risky moves left. New section in `fast-agentic-delivery.md`: distinguish **stalled** (blocked on yourself → move) from **correctly holding** (async progressing / owner-gated → no move); answer the pressure with a **truthful one-line status** (what's running, what's blocked and on whom), never manufactured work; at a genuine terminus prefer non-fan-out moves (drain the queue, close delivered, surface gating decisions), then hold — busywork under observation is still busywork. One eval (agentic-delivery 34 → 35). Trio → 1.162.0. Closes #419.

Dogfood reviewer: PASS-WITH-NITS → two no-duplication cross-ref refinements applied pre-merge: the bullet-2 status triad now cross-refs the adjacent *if the loop is idling, say so loudly* rule it extends (same whole-window status, opposite failure — **silence** there vs **filler** here) rather than the ask-ledger data structure it had pointed at; and the counterweight framing now names the *the owner's message cadence is not the loop's clock* bullet it mirrors (that stops owner-quiet throttling the loop down; this stops a pressure tick driving it up).

## [1.161.0] — 2026-09-19

Wave 82 — **a delegated "verify green" is a lead, not the authoritative gate** (#408; agentic-delivery). In a delegate → review → land pipeline, a subagent's green in an isolated worktree ran a **narrower scope** than the real gate (changed-files / package-local, not repo-wide), so it can sit on failures the full gate catches — an unused-import that root `eslint . --max-warnings 0` flags, formatter diffs on untouched files, coverage / cross-workspace checks the worktree could not run. New section in `fast-agentic-delivery.md`: the **authoritative gate is the full-repo run at integration** (real pre-commit hook / CI, on the integrated tree); **land re-runs the full gate** and that is the verdict of record — a lane's green is `unverified` until then. Framed as the **inverse** of the symlinked-deps / provisioning-gap sections (env too *poor* → false failure; here too *partial* → false pass) and **distinct** from the stale-verdict case (moved head vs partial scope). One eval (agentic-delivery 33 → 34). Trio → 1.161.0. Closes #408.

Dogfood reviewer: PASS-WITH-NITS → three applied pre-merge: a directional cross-ref slip fixed (the provisioning-gap section is *above* this one, not below — the inverse relationship itself was correct); a disambiguating cross-ref added to the neighbouring "CI-offload the heavy gate" section (closest existing prose — kept distinct: that picks *which tier* a lane runs for the RAM budget, this is what a *delegated* verdict entitles you to conclude + the integrated-tree point); and #408's "budget a fix-and-recommit at land" item folded in (a delegated green predicts less rework, never none).

## [1.160.0] — 2026-09-19

Wave 81 — **fix a mis-cited operating principle** (#398; dcr correctness / exemplary-repo hygiene — a reference bar must cite its own principles correctly). The "empty beats fabricated" / "computed-not-fabricated" concept is **No fabrication = `SKILL.md` principle 3**, but six loci labeled it **principle 4** (Do no harm): `product-ux-quality.md` (×2), `migration-parity.md`, and three eval expected-outputs/expectations in `deep-code-review/evals/evals.json`. Corrected all six to principle 3; the genuine principle-4 citations (net-positive-on-every-axis, no-regression, never-delete-a-feature-to-reach-parity) were each verified in context and left untouched. No behavior change — a self-citation accuracy fix. Trio → 1.160.0. Closes #398.

Reviewed independently via advisor (a stronger model with full context): the classification of all fifteen principle citations — the six corrected to principle 3 and the nine genuine do-no-harm principle-4 citations left untouched — was confirmed, and a repo-wide proximity scan (any `fabricat`/`invent`/`empty beats` concept within ±2 lines of a `principle N` citation) verified no seventh mis-cite locus remains.

## [1.159.0] — 2026-09-19

Wave 80 — **ML in production: drift monitoring & safe model rollout** (dcr; completes the ML lifecycle after wave 75). A new `##` section in `testing-and-evals.md`, after "ML pipeline correctness": the *post-deployment* half — W75 verified the model was **trained** honestly and `data-quality.md` §12 verifies train/serve feature parity; this covers a model that **silently decays** in production or a **swap that ships a quietly worse model**, both invisible to the training checks. (1) **Drift monitoring** — a served model degrades with no error as the input distribution drifts; monitor the input-feature + prediction distributions and realized performance against **lagging** ground truth (alert on a proxy — distribution shift / confidence drop — in the meantime); green infra dashboards are not model monitoring. (2) **Safe model rollout** — a new model version is a behavior change, not a deploy; green error-rate / latency do not mean it is as good, so prove it on **prediction quality** via **shadow** or **canary / champion-challenger** with a rollback path and a longer quality-based bake than a code canary (ground truth lags). Specializes the generic `observability.md` monitoring and `release-engineering.md` canary/rollback disciplines to the ML case; explicitly distinct from W75 (training) and data-quality §12 (train/serve skew). A red-flag line added. One eval (deep-code-review 155 → 156). No new external standard → no `docs/standards-index.md` change. Research-derived (no filed issue). Trio → 1.159.0.

Dogfood reviewer: PASS-WITH-NITS (no fix-first — the provenance axis that flagged the prior waves was verified against the primary source here). Three optional prose nits applied: an in-bullet distinction from `data-quality.md` §12's train/serve *parity* check (drift = live inputs vs the training baseline over time, not two computation paths at one instant); reduced a verbatim symptom-phrase overlap with §12; and softened "ground truth lags" → "often lags" (not universal — some labels arrive fast).

## [1.158.0] — 2026-09-19

Wave 79 — **EU NIS2 name-and-route**, a new regulatory area (the last non-gated new-area from the coverage cartography; primary-sourced this session). A new tree entry in `business-ops/regulated-domain-triage.md`: an organization operating its own in-scope services in the EU (medium-sized+ in a covered sector — energy, transport, digital infrastructure, cloud / data centres / DNS, health, water, public administration, …) → name the **EU NIS2 Directive (Directive (EU) 2022/2555)** + engineering-obligation leads (the risk-management measures — risk analysis, incident handling, business continuity, supply-chain security, cyber hygiene; and **incident-reporting readiness** → maps to `deep-code-review` observability + `agentic-delivery`'s `incident-response.md`; the supply-chain half reuses the CRA / A03 leads); route in-scope / essential-vs-important / reporting-authority / timelines / management-accountability to counsel (name-and-route boundary; no rot-prone dates encoded). Distinct from the CRA's product scope (NIS2 = how you *operate*; CRA = the *product* you ship). Verified by direct fetch of EUR-Lex 2022/2555 this session — the verbatim risk-management-measures list and the staged reporting windows were **not** reachable via the fetch (cited by name only; the leads are grounded in the preamble categories the fetch did surface).

Dogfood reviewer: FIX-FIRST → two provenance-precision fixes applied pre-merge. (1) The entry (and its Verification bullet, eval, and this changelog) had cited the risk-management-measures **article by its number** — which `regulated-domain-triage.md`'s own boundary forbids ("regimes are named by name only; no article numbers … until fetched, logged, and confirmed"), and that article's measure list was never reachable in the fetch; dropped the number at every locus, matching the CRA/EAA precedent (the eval no longer requires a boundary-violating answer to pass). (2) The `docs/standards-index.md` row had attributed business-continuity and supply-chain-security to recitals 79/89, which the fetch did not pin there; reworded to cite to the recitals only the categories they surfaced and to mark the full measure set as by-name / not-pinned. One eval + a Verification-list entry (business-ops 8 → 9). Research-derived (no filed issue). **business-ops → 1.5.0; trio → 1.158.0.**

## [1.157.0] — 2026-09-19

Wave 78 — **mergeability is a snapshot against a moving base head**, from issues **#376 + #379** (review-method deltas; dcr). "Green + mergeable" is a snapshot against the current base head, not a durable property: landing one PR can flip an overlapping PR back to CONFLICTING while its checks stay green (they ran against the old base). New `###` subsection in `branch-and-merge-hygiene.md`, after the merge-train section, at two scales — (1) *snapshot-then-batch*: re-check mergeability before **each** merge (not once at the top of the batch), and group the batch by file sets (serial-with-rebase within a group, parallel only across disjoint groups); (2) *sweep-while-resolving*: a merge sweep run concurrently with a resolver lane re-dirties the resolution on every merge, so **freeze the merge step (not the build step)** while a resolver is active — queue greens, land the hardest-to-rebase set first, then drain. Framed as the stale-base failure (below) at the mergeability layer. `fast-agentic-delivery.md`'s existing branch-and-merge cross-ref extended to point here (the #376 fleet-coordinator audience). One eval (deep-code-review 154 → 155). No new external standard → no `docs/standards-index.md` change. Trio → 1.157.0. Closes #376, #379.

Dogfood reviewer: FIX-FIRST → all four addressed pre-merge. (1) A parenthetical had over-claimed that the merge-train union "pre-empts most of this" — but that union branch is **thrown away** (step 4) and the member branches are left unchanged, so it proves the *combination builds* and surfaces the collisions without making a conflicting member mergeable; this also **contradicted #376's own tooling caveat**. Rewrote it: the union "does not make a conflicting member mergeable — sequence the resolver first, then run the train," and the per-merge re-check still applies at step 3. (2) Added the missing 🚩 red-flag line for this failure mode (the file's per-subsection convention). (3) Tightened eval expectation 1 to the unprompted causal claim (green CI ran against the *old* base, so it is not evidence of current mergeability). (4) PR body uses per-issue `Closes` keywords (GitHub's comma-list auto-close fires only on the first).

## [1.156.0] — 2026-09-19

Wave 77 — **per-diff delta gating over absolute-count ratchets under parallel lanes**, from issue **#375** (a review-method delta; agentic-delivery). An absolute-count gate over the whole tree — `--max-warnings N`, a coverage-percent floor, a bundle-size budget — is **contended shared state** under parallel write-lanes: two lanes off the same base each add a harmless delta, and the second to push goes red for consuming a slot the first already took (punished for arriving second; invisible until the second lane's CI runs; scales with fan-out width). New section in `fast-agentic-delivery.md`: **gate on the per-diff delta** ("no new warnings versus the merge base") — order-independent, so no lane consumes another's slot; keep the absolute count as a slow-moving burndown target, never the per-PR gate under fan-out; never raise the ceiling to pass (a ratchet only tightens). Explicitly distinguished from the adjacent phantom-warning `--max-warnings` false-fail (there the count is *wrong*; here it is *right but contended*), and generalized to any absolute-threshold gate on a shared counter (coverage %, bundle-size). One eval (agentic-delivery 32 → 33). No new external standard → no `docs/standards-index.md` change. Trio → 1.156.0. Closes #375.

Dogfood reviewer: FIX-FIRST → all three fixed pre-merge. (1) The cross-reference to the "cap in-flight lanes" section had read "the same **contention** as" — but that section's failure is over-admission (real spend with the integration head unchanged), not one lane's legitimate land red-flagging another; softened to "the same **shape** as" (the shared principle — gate on the quantity you own, not an ambient total — still holds, and the pointer stays useful). (2) The worked example was arithmetically under-specified: from a base of `N-1`, lane B reaches `N+1` only if lane A *also* added a warning — made lane A explicitly add one and take the last slot. (3) "never the per-PR gate" was unqualified, but an absolute ratchet is fine for a single committer (as #375 itself notes) — scoped it to "under fan-out" in the section, the eval, and this entry.

## [1.155.0] — 2026-09-19

Wave 76 — **EU Accessibility Act (EAA) name-and-route**, a new regulatory area (the coverage cartography's EAA candidate, now primary-sourced). A new tree entry in `business-ops/regulated-domain-triage.md`: a consumer product / service on the EU market (e-commerce, banking / payment terminals, transport ticketing & self-service, e-readers, computers / OS) → name the **EU Accessibility Act (Directive (EU) 2019/882)** + the EN 301 549 / WCAG engineering benchmark (routes to `frontend-a11y.md`); route in-scope / micro-enterprise-exemption / timelines to counsel (name-and-route boundary; no rot-prone dates encoded). Verified by direct fetch of EUR-Lex 2019/882 this session (the cartography couldn't reach a primary source; now logged in `docs/standards-index.md`). One eval + a Verification-list entry (business-ops 7 → 8). **business-ops → 1.4.0; trio → 1.155.0.**

Dogfood reviewer: FIX-FIRST → fixed pre-merge. The EAA ledger row had asserted "aligns with EN 301 549 / WCAG" attributed to the EUR-Lex fetch, but that page names neither standard — removed the claim from the ledger (EN 301 549 kept as a by-name engineering lead in the skill body only, WCAG stays grounded by its own row); softened the tree/eval "the benchmark **is** EN 301 549 / WCAG" to a lead-to-verify, per the name-and-route boundary.

## [1.154.0] — 2026-09-19

Wave 75 — **ML-pipeline correctness** (data leakage, training reproducibility, label quality), from research issue **#384** (a new area; dcr-only). Perun's AI coverage was security / output / governance-shaped; this adds the *correctness of a classical ML training/eval pipeline* — where a leaked split makes the reported metric **false** (the anti-fabrication thesis in classical-ML clothing).
- **`testing-and-evals.md` (new subsection):** split train/test before any preprocessing, fit preprocessing on the train subset only (a Pipeline stops CV/tuning leaking), no target/temporal leakage, no duplicate rows across splits — a leaked split *passes too well* (scikit-learn); and training must be reproducible (seed the RNG, pin data/model/code per reported number) so a metric delta is attributable (Breck et al., *The ML Test Score*, 2017).
- **`data-quality.md`:** requiring expert labels sets the bar but doesn't verify it — measure inter-annotator agreement (bounds label noise, caps the achievable metric), spot-audit errors, handle class imbalance honestly; label errors distort the metric *and* re-rank models (Northcutt et al., NeurIPS 2021, ≥3.3% avg errors across the 10 benchmarks studied). The *opposite* lesson from inter-model agreement.

Three sources verified by direct fetch (2026-09-19), in a new `docs/standards-index.md` section. Three evals (deep-code-review 151 → 154). Trio → 1.154.0. Closes #384.

Dogfood reviewer: PASS-WITH-NITS → scoped the Northcutt figure to "across the 10 benchmarks studied" (it had read as a universal property) and dropped a stray "~" in the eval; sources otherwise verified verbatim.

## [1.153.0] — 2026-09-19

Wave 74 — **EU Cyber Resilience Act (name-and-route) + VEX**, from research issue **#358** (cartography survivor — a new regulatory area + a supply-chain artifact).
- **CRA (`business-ops/regulated-domain-triage.md`):** a new tree entry — shipping a product with digital elements to the EU market → name the **EU Cyber Resilience Act (Regulation (EU) 2024/2847)** + its engineering-obligation leads (security-by-design; SBOM + coordinated-vulnerability-disclosure; a support / update period; reporting actively-exploited vulns to the designated authority → maps to dcr A03); route in-scope / conformity-class / reporting-authority / exact-timelines to counsel (name-and-route boundary; no rot-prone dates encoded).
- **VEX (`security-appsec.md` A03):** pair an SBOM with a **VEX** — a producer-issued per-CVE exploitability assertion (`not_affected` *with a justification*, `affected`, `fixed`, `under_investigation`) so a consumer distinguishes a real exposure from a component that merely *ships* the vulnerable code on an unreachable path (CISA VEX; complements, never replaces, the SBOM).

CRA + VEX verified by direct fetch this session (2026-09-19), in a new `docs/standards-index.md` section. Two evals — business-ops (6 → 7, + a Verification-list entry) and deep-code-review (150 → 151). **business-ops → 1.3.0; trio → 1.153.0.** Closes #358.

Dogfood reviewer: PASS-WITH-NITS → both fixed pre-merge. Generalized the CRA reporting recipient to "the designated authority" (the CSIRT-coordinator/ENISA specifics are correct to CRA Art. 14 but were not in the fetched summary — routed to counsel, per verify-before-cite), and added a VEX prompt to A03's *How to detect* so the eval's reviewer check has a home on the detection surface.

## [1.152.0] — 2026-09-19

Wave 73 — **crypto-agility & post-quantum readiness** in `security-appsec.md` A04, from research issue **#359** (cartography survivor — a new technical dimension; A04 reviewed *current* crypto but had nothing on algorithm agility or PQC).
- **Crypto-agility:** algorithm choices named in config / metadata (a versioned suite id), not hard-coded per call site, so a primitive can be rotated without a rewrite; a ciphertext / signature envelope carries an algorithm identifier so old and new coexist during migration.
- **Harvest-now-decrypt-later:** long-lived confidentiality warrants a migration path to the NIST post-quantum standards — **FIPS 203 ML-KEM** (KEM), **FIPS 204 ML-DSA** + **FIPS 205 SLH-DSA** (signatures), published 2024.
- **Bounded (not stricter than the standard):** the finding is a hard-coded, un-versioned primitive with no swap path on a long-lived-data surface — not "ship ML-KEM today." No compliance deadline encoded (rot rule).

- **GPC adjacent (domain Q):** honor the **Global Privacy Control** universal opt-out — the code reads `Sec-GPC: 1` / `navigator.globalPrivacyControl` and acts on it as a do-not-sell/share opt-out (a greppable check); the *legal* binding question routes to counsel / `business-ops` (`privacy-compliance.md`).

FIPS 203/204/205 + W3C GPC verified by direct fetch this session (2026-09-19), in `docs/standards-index.md`. Two evals (deep-code-review 148 → 150). Trio → 1.152.0. Closes #359 (PQC/crypto-agility + the GPC adjacent).

Dogfood reviewer: PASS-WITH-NITS (PQC half) → the one soft item was that #359 also names a "GPC adjacent (Q)" sub-scope; rather than half-close, built the GPC honor-check too so "Closes #359" is accurate. FIPS names + GPC signal verified verbatim by direct fetch; bounded (no PQC mandate / no deadline); provenance filed in a correctly-dated section.

## [1.151.0] — 2026-09-19

Wave 72 — **LLM-application engineering correctness** (RAG retrieval-seam + agent-trajectory eval), from research issue **#391** (cartography survivor — a new area under the existing agent/LLM archetype; section-add to `testing-and-evals.md`, no new archetype). The AI-evals section covered generic model-output quality but not the RAG retrieval seam or agent trajectories:
- **RAG evaluated at the retrieval seam, not only end-to-end** — a faithful answer over the *wrong* retrieved context is still wrong, and a good end-to-end score can hide a retrieval miss the model covered from parametric memory (which fails silently when the knowledge base changes). Evaluate retrieval quality (context precision / recall @k, chunk-boundary loss, reranking) AND generation faithfulness separately.
- **An agent is evaluated on its trajectory** — tool-call selection + arguments + multi-step completion — not only its final answer (a right answer via a lucky / unsafe path is a latent failure).

Framed by concept, not vendor: RAG technique = Lewis et al. 2020 (neutral anchor); metric names operationalized by a tool like RAGAS (a *tool*, not a standard). Both added to `docs/standards-index.md`; one-line cross-ref from `security-ai-agents.md` (the RAG *correctness* half vs its *security* half). One eval (deep-code-review 147 → 148). Trio → 1.151.0. Closes #391.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. Re-filed the two standards-index rows under a proper `2026-09-19` dated section (they had landed inside the 2026-09-08 idea-critic section — a date/scope contradiction) and scoped the RAGAS row to what the cited index page shows (per-metric definitions were read on the sub-pages). Un-conflated **faithfulness** (groundedness) from **answer relevancy** (addresses the question) — two distinct metrics — in the bullet and the eval.

## [1.150.0] — 2026-09-19

Wave 71 — **a deserializer re-enforces its builder's invariants** (`data-quality.md`), from owner-filed **#403** (top triage net-new). In a build → serialize → parse pipeline, a serialized line can be torn / hand-edited / older-schema / written by someone else, so "the builder guarantees X" does not mean a parsed object satisfies X. The parse path must independently **re-derive computed fields** (a count from the validated collection, not read verbatim) and **validate element shape** (not just a primitive type) — a parser weaker than its own builder reintroduces, at the deserialize trust boundary, the exact fabrication the builder prevents, invisible to a builder-only test suite. Proof: property tests `parse(serialize(x))` preserves the invariant + `parse(torn input)` drops/rejects rather than emits a violating object (a tautological generator tests nothing — ties #373). The data-integrity face of untrusted deserialization (CWE-502). One eval + a 🚩 red-flag (deep-code-review 146 → 147). Trio → 1.150.0. Closes #403.

Dogfood reviewer: PASS-WITH-NITS → tightened an over-claim ("tests nothing" → exercises only round-trip fidelity, never the violation path) and logged **CWE-502** in `docs/standards-index.md` (a pre-existing cite-without-log gap this wave also touches).

## [1.149.0] — 2026-09-19

Wave 70 — **slopsquatting**: a dependency existence / provenance check beyond name-proximity, from research issue **#402** (AI-code research). A03's only name discriminator was typosquat (a character off a popular name); a package name an LLM *hallucinated* — that an attacker pre-registers — isn't a typo of anything, so it passed every named check.
- **`security-appsec.md` A03:** verify a *newly-added* dependency resolves to an **established** package (registry age, download history, a real source repo / provenance), not merely that it isn't a typo. LLM-hallucinated names are a *predictable* pre-registration target.
- **`dependency-currency-and-upgrades.md`:** the release-age cooldown also catches a never-existed-until-now name (no history to clear the window); typosquat / slopsquat / maintainer-hijack named together.
- **By-defect, not author-gated** — the rationale mentions the elevated base rate in AI-assisted code, but the check gates on the dependency's provenance, never on who wrote the diff.

Source (USENIX Security 2025, Spracklen et al.) added to `docs/standards-index.md` + the file's own standards list. One eval (deep-code-review 145 → 146). Trio → 1.149.0. Closes #402.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. The reviewer fetched the USENIX PDF and confirmed every figure accurate, but caught two provenance-honesty defects in the standards-index row: a false "corroborated across the authors' GitHub" claim (the GitHub states a 19.7% overall rate, not the per-model figures) and a per-package-vs-per-sample denominator misframe. Corrected the row ("at least 21.7% of *packages recommended by* open-source models …"; GitHub corroborates names/samples/models + a 19.7% overall rate), removed the inline figures from A03 (they live in the ledger), and fixed the eval's denominator.

## [1.148.0] — 2026-09-19

Wave 69 — a new **i18n / l10n depth reference** (domain R), from research issue **#390** (coverage cartography — a genuinely new area, no new archetype). Domain R routed only to an 8-line checklist that omitted bidi/RTL; new `references/i18n-l10n.md` carries the standards-heavy depth a checklist can't hold, routed from the R map row + the checklist header:
- **Encoding & normalization:** UTF-8 declared in-document; normalize before compare / dedup / key — and *after* concatenation, because "None of the Normalization Forms are closed under string concatenation" (UAX #15), so per-fragment NFC can still assemble to un-normalized output.
- **Bidi / RTL:** declare `dir`; wrap opposite-direction phrases; reject/flag Unicode bidi *override* controls (UAX #9 — "avoided … because of security concerns," UTR #36) — the Trojan-Source class.
- **Plurals / formatting / collation:** CLDR plural categories (zero/one/two/few/many/other), never `n == 1`; locale-aware number/date/currency formatting; a locale collator, not `.sort()`; text-expansion room.

Sources verified by fetch this session (2026-09-19): W3C i18n, UAX #15, UAX #9 + UTR #36, Unicode CLDR — all added to `docs/standards-index.md`. One eval (deep-code-review 144 → 145). Trio → 1.148.0. Closes #390.

Dogfood reviewer: PASS-WITH-NITS → both fixed pre-merge — scoped the UAX #9 "avoided … because of security concerns" quote to the **overrides** (RLO/LRO) and distinguished them from the *safer* **isolates**; "see UTR #36".

## [1.147.0] — 2026-09-19

Wave 68 — a data-provider / integration-contract review lens for `data-quality.md` §12 (domains D + I), from owner-filed **#345**. When a product's job is to *feed another system's scoring / automation*, the contract seam has four failure modes no shape-only (domain I) check catches:
- **Emits raw events when the consumer needs scoring inputs** — should emit windowed aggregates + velocity keyed on the consumer's canonical ids (with provenance + license/tier), not triggers the consumer must re-aggregate.
- **Static / manual delivery** where the consumer needs a **live channel + cadence** (a table/feed read on schedule).
- **No per-field source-of-truth declaration** (authoritative / partial / never) — so the consumer wires fields the provider never ships.
- **A claimed input stale or misclassified vs the provider's live artifact** — reconcile every claimed provider-input (count + classification) before it drives a downstream score (a pre-reclassification blend can be off ~100×). Gate: diff declared provider-inputs vs the actual current output; a mismatch blocks sign-off.

Shape stays in `api-contracts.md` (consumer-driven contract); this is the quality / semantics half at the provider seam. One eval + a §12 red-flag (deep-code-review 143 → 144). Trio → 1.147.0. Closes #345.

Dogfood reviewer: PASS-WITH-NITS, no must-fix (all four modes verified genuine deltas, not restatements; the "~100×" example is owner-sourced and generic).

## [1.146.0] — 2026-09-18

Wave 67 — a delivery-CI hygiene batch from owner-filed **#346** and **#349**.
- **#346 (`docs-and-dx.md`) — a gate's stated *location* is a claim with its own currency.** When a gate moves (CI → local-only, one job to another, behind a label/trigger), an agent runs what the docs / PR template / comments *say* runs. Audit agent-facing docs for dangling CI job/label/trigger references (a dead reference is a defect); a relocation to local-only makes the local bar the blocking one; **fail the audit closed** — a gate whose docs can't name a live location is unenforced until proven otherwise. Else the gate runs *nowhere* while every surface reads green.
- **#349 (`branch-and-merge-hygiene.md`) — a worktree-relative hook runs its base's copy; land the safe hook everywhere first.** Second-order to #298: once hooks resolve per-worktree, a lane cut from an old base runs *that base's* (stale / heavyweight) hook and hangs → gets bypassed. Rules: hook content fail-safe by default (safe core, slow/interactive steps opt-in); land the safe hook on every long-lived base *before* normalizing resolution; verify which hook runs (base-dependent, idempotent re-assert); an audited escape hatch instead of a whole-tier `--no-verify`.

Two evals (deep-code-review 141 → 143). Trio → 1.146.0. Closes #346, #349.

## [1.145.0] — 2026-09-18

Wave 66 — verify-the-premise before acting, two additions to `method.md`'s presence/absence section (extending #250), from owner-filed **#353** and **#363**.
- **#353 — a perception-sourced "it's missing" against code that already implements it is a `delivery-gap`, not a build order.** A third verdict beside confirmed-absent and false-absent: when runtime confirms the capability is present but a reporter evaluated the surface as missing, the working code isn't reaching them. Diagnose why (build/env drift, route/mount mismatch, preference/state gating); deliver the reason + the smallest fix, not a reimplementation.
- **#363 — a "broken / decorative / always N" premise is a claim to verify against live data, and a flat metric can be the honest answer.** Measure the live distribution and read the code before fixing (the "constant" may be an already-overwritten initializer); a near-constant value can be the honest truth of the corpus, and inflating it via fuzzy / non-independent matching fabricates it — make the count provable and gated, not larger (empty beats fabricated).

Also: fixed the stale `docs/roadmap.md` status line ("main @ 1.48.0" → a dated snapshot pointing at `VERSION` / `CHANGELOG`).

Two evals (deep-code-review 139 → 141). Trio → 1.145.0. Closes #353, #363.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. Medium: "empty beats fabricated" was cited as `SKILL.md` principle 4, but that principle is *Do no harm* — anti-fabrication is **principle 3** (corrected in the new prose + the eval; the pre-existing repo-wide mis-numbering cluster is filed separately, not widened into this diff). Also added a 4th delivery-gap diagnostic axis (runtime / integration fault — a reached, mounted control whose live channel never connects / backend never emits / error is swallowed) and made the "third outcome" enumeration scope explicit (unconfirmed-absent is the couldn't-boot branch).

## [1.144.0] — 2026-09-18

Wave 65 — a UI-state / test-integrity batch from owner-filed **#360 / #361 / #362** (the "green logic test, broken UI" family).
- **#360 (`product-ux-quality.md`) — a disclosure default derived from async-fetched data silently never fires (mount-capture).** `useState(open)` seeded from a value the hook doesn't re-sync locks in first-paint state; an async signal that lands after mount never applies (unit test green, running UI wrong). Fix: drive the mount default from synchronous data, surface the late signal via a non-reflowing affordance (not force-open), verify in the running app.
- **#361 (`testing-and-evals.md`) — a state-dependent spec must assert its precondition, not lean on a default.** A browser spec that asserts on expand-only content, or clicks a bulk toggle a redesign removed (`if (count) click` — a no-op), is green only because the default matched; flip the default and it breaks at the slow gate. Drive the state explicitly; prefer an explicit assertion over best-effort click-if-present.
- **#362 (`testing-and-evals.md`) — pin the equivalence between a should-render / should-expand predicate and the set it gates.** `predicate(x) === (renderSet(x).length > 0)`, both directions and non-vacuous, so a "smart default" can't drift into hiding real content or expanding an empty container.

Three evals (deep-code-review 136 → 139). Trio → 1.144.0. Closes #360, #361, #362.

## [1.143.0] — 2026-09-18

Wave 64 — a UX / audit-visibility honesty lens for `product-ux-quality.md` (domain P), from owner-filed **#351**. When an action **presented as non-destructive** (resolve / archive / dismiss, backed by a retained `resolved_at` / `archived_at` column) removes the record while giving **no cue that it persists, is reversible, or where it went**, the user cannot tell it from a hard delete — two failures:
- **Product-safety:** the action reads as destructive (a first-time user watches the row vanish and concludes they deleted it), suppressing a reversible, low-stakes action.
- **Audit / history visibility:** when the retained trail is meant to be reviewable, an unreachable surface makes it effectively invisible (the data is intact; the defect is visibility, not integrity).

**Scoped to the hidden reversibility, not default-hiding as such:** hiding a completed item behind a known filter (an `is:open` list, an active board, inbox archive) is a convention, not a defect; a soft-**delete** (`deleted_at`) is out of scope ("reads as a delete" is intended there). **Fail-open** — a human adjudicates every hit. Fix: keep the record in place, muted + a status label, or a discoverable labelled resolved/archived view; not colour-alone; verify on the running app's default surface. Pattern described generically (no vendor named).

One eval + one domain-P checklist box (deep-code-review 135 → 136 evals). Trio → 1.143.0.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. High: the flag criterion was over-broad (it flagged conventional archive / `is:open` default-hiding and prescribed rendering soft-deleted rows forever) — rescoped to labelled-non-destructive + no-persistence-cue, carved out conventions + soft-delete, added the fail-open human-adjudicates clause. Also added the missing sweep-checklist box and relabelled "data-integrity"→"audit / history visibility."

Closes #351.

## [1.142.0] — 2026-09-18

Wave 63 — two anti-fabrication data-honesty axes for `data-quality.md` (scoring & config discipline, §7), from owner-filed **#344** and **#355**.
- **#344 — name a derived field for what it measures, not the conclusion you want.** A column called `relationship_strength` that is really a co-occurrence *count* is a schema-level overclaim; surface the corroborating evidence (co-authored N papers; met at N events), not a manufactured score; require multiple independent signals before asserting a tie (a lone co-mention/co-attendance is a lead, not a relationship); and reconcile a relationship's **two-sided** edge. The UI half is the confidence-tier false-precision rule (`product-ux-quality.md`).
- **#355 — a ranking / scoring / leaderboard gates on an *observed* liveness signal; a missing liveness field is a blocker.** Ranking without a liveness gate puts dead / discontinued entities on a live shortlist; liveness comes from the subject's own recent activity, not mere record existence; no liveness signal → fail closed (exclude / flag `unknown`), never "rank everything, filter later." The affirmative complement to the exclusion-gate-fails-closed bullet above it.

Two evals (deep-code-review 133 → 135). Trio → 1.142.0. Closes #344, #355.

## [1.141.0] — 2026-09-18

Wave 62 — verify-first before laning a tracked issue, from owner-filed **#352** (and the doctrine half of **#347**). An issue's OPEN state is not proof its fix is absent: GitHub auto-closes a linked issue only "when you merge a linked pull request into the default branch," and `Closes` / `Fixes` / `Resolves #N` are "interpreted only when the pull request targets the repository's default branch" (verified against GitHub Docs this session). A fleet that merges day-to-day into a long-lived integration branch therefore leaves issues **done in the tree, open in the tracker** — and an agent reading "open" as "not done" re-lanes finished work.
- **New subsection in `fast-agentic-delivery.md`** (the duplicate-work home): before opening a fix lane for a tracked issue, grep the *integration* branch you would base on for the fix's landmark; know the forge's auto-close scope; if already delivered, stop and report "already delivered" with `file:line` + the commit SHA, don't re-lane, and don't hand-close ("done" = merged to the default branch).
- **#347's automation half is routed, not built.** A team merging off-default must *supply* a scoped close-on-staging-merge automation (explicit `Closes #N` only, never a heuristic; least-privilege; idempotent) — that is project tooling, owner-gated, out of this prose skill's charter.
- **Provenance.** GitHub linked-PR doc added to the file's own Sources **and** `docs/standards-index.md` (fetched 2026-09-18).

One eval (agentic-delivery 31 → 32). Trio → 1.141.0. Closes #352; #347's doctrine landed here, its automation stays open as an owner-gated tooling item.

## [1.140.0] — 2026-09-18

Wave 61 — name the exploited-in-the-wild instruments for the "known-exploited" severity gate, from research issue **#357**. `dependency-currency-and-upgrades.md`'s severity discipline gated on "Known-exploited (or high-CVSS)" but named **no source** for "known-exploited" — a gap the skill's own principle 2 (prefer the canonical instrument) exposes.
- **Named instruments.** A "known-exploited" finding must now cite the canonical source: **CISA KEV** ("the authoritative source of vulnerabilities that have been exploited in the wild") for *is it exploited now*, and **FIRST EPSS** (probability a CVE "will be exploited in the wild in the next 30 days") for *how likely*. Read alongside CVSS (likelihood vs severity) — the same multi-signal discipline the rubric applies everywhere.
- **Guardrail — inputs, not a lower bar.** Both bodies cast their scores as an *input* to prioritization, so KEV / EPSS **raise and rank, never lower the bar**: a low EPSS, or a CVE's absence from KEV, does **not** disarm a reachable-path finding (absence of exploitation evidence is not proof of safety; EPSS is a 30-day probability, not a verdict) — the same refusal to over-trust a derived number that the confidence-tier false-precision rule applies to UI display.
- **Provenance.** KEV + EPSS added to the file's own standards list **and** `docs/standards-index.md` (both URLs fetched this session, 2026-09-18) — the ledger-mirror discipline.

One eval (dcr 132 → 133). Trio → 1.140.0. Closes #357.

## [1.139.0] — 2026-09-18

Wave 60 — build-side product playbook from owner-filed **#343**. Perun's domain P reviews a product surface for defects; it was not written as a build spec. New reference `agentic-delivery/references/production-grade-product-playbook.md` adds the build→verify direction: it names the positive build-time patterns and pairs each with the domain-P axis that verifies it.
- **Scope — net-new only, no restatement.** The patterns already stated once as enforced review axes (why-it-matters / actionability #332, ranking & sort legibility #333, progressive disclosure, one-component-per-concept, interaction-completeness) are *pointed at* `product-ux-quality.md` in a build→verify table, not copied (a second copy is the duplication this suite condemns). The file adds only the three build-time patterns domain P assumes but does not shape: **job-first information architecture** (derive the layout from the user's core decision; illustrative surface-shapes, not a taxonomy to complete), **lead with the relationship, not the record** (for entity-graph products), and **density as a build target** (choose the baseline in the G3 ADR, don't inherit a component-library default).
- **Placement.** Lives in `agentic-delivery` (the build side, G3 Design), not `deep-code-review` (whose identity is the review bar, and whose `SKILL.md` is byte-capped) — routed from the G3 design block with a "read it when" trigger; verified by dcr domain P at G6.
- **Provenance.** Cites public design *conventions*, never a private vendor; a named precedent method takes a `docs/standards-index.md` row.

One eval (agentic-delivery 30 → 31). Trio → 1.139.0. Closes #343.

## [1.138.0] — 2026-09-18

Wave 59 — verification-honesty deltas from owner-filed #334 / #336 / #340 (the other four of the #334–#340 batch — #335/#337/#338/#339 — were already covered and closed with file:line evidence, not duplicated). Three small, seam-guarded additions:
- **#334 — a visual receipt must show the feature, not a wall past it** (`testing-and-evals.md` + `product-ux-quality.md` checklist): non-empty is necessary, not sufficient — a login / error / empty page is a valid non-empty image; capture authenticated content via a **dev / identity-bypass render mode**, not a route-auth-walling production build; prefer a deterministic readiness signal over a network-idle heuristic (a hot-reload socket defeats it). Discriminated from reproducing a **build-specific** defect (which uses the production build, `method.md`) so it doesn't contradict that rule.
- **#336 — a persistent cannot-check is not a finding** (`reliability-error-handling.md`): a gate reaching an external dependency retries a transient error bounded, then on a persistent outage / timeout / retired endpoint **does not block and is not reported as a finding** — fails closed only on an observed problem; never wire a gate to a retired/unversioned endpoint; bound the gate's own runtime. **Exception:** a security / authz / integrity / spend attestation still **fails closed** on a can't-verify (a fail-open there is the bug). Phrased as "does not block / not a finding" (**not** "fails open", which already denotes the reviewer-honesty could-not-check status elsewhere).
- **#340 — an operating-discipline doc for stable environment invariants** (`docs-and-dx.md`): record how to render a reviewable/authenticated state, which capture tool works, which gates are conditional, known flakiness — once, read before environment-dependent work; a rediscovered invariant is filed back as part of closing the task. Scoped to **stable invariants** (a derived status still follows "store the query, not the answer").

Two evals (dcr 130 → 132). No `SKILL.md` content change (all four references already routed). Trio → 1.138.0. Closes #334, #336, #340.

## [1.137.0] — 2026-09-18

Wave 58 — two owner-filed product-value axes for `product-ux-quality.md` (domain P), **#332 + #333** (dogfood-derived). The domain-P rules prove a component *renders* correctly; these add the *does it help the user act* half. Two distinct sections (different failure modes, evidence, gates):
- **Actionability (#332)** — a primary information unit answers *why it matters* via a **derived** signal (count / recency-delta / graph-degree) plus a concrete next step where an action is possible, most-actionable-first-and-stable. **Hard anti-fabrication rule:** the signal is derived/deterministic, never a model-authored importance score or LLM salience judgement (the content-layer cousin of the confidence-tier false-precision rule). Warn-and-list (fail-open) heuristic gate, explicitly contrasted with the fail-closed `ci-gates.sh` check-#6/#7.
- **Ranking & sort-mode legibility (#333)** — the default order serves the user's job (recency is a mode, rarely the right default on a decision surface); each exposed sort mode is self-explaining ("orders by …") and **measurably distinct** (near-identical modes collapse; the sort key needs a measured distribution — an opaque/near-constant key is ordering-layer false precision). Extends the variant-bloat rule to ordering, and owns the shared default-ordering principle the actionability section references (stated once).

Private-vendor exemplars from the issues are described as **patterns, not named** (CLAUDE.md third-party-identifier rule); the public **Smart Brevity** method is named and added to `docs/standards-index.md` by-name. Two checklist items + two evals (dcr 128 → 130). No `SKILL.md` content change (domain P already routes `product-ux-quality.md`). Trio → 1.137.0. Closes #332, #333.

## [1.136.0] — 2026-09-18

Wave 57 — `domain-checklists.md` middle-tier de-duplication, **#325 Option A** (owner-selected). The checklist tier restated definitions its per-domain deep files own — the repo's own anti-duplication thesis, violated. Surgically converted the **3 copied definitions/rules the #325 audit surfaced** to a scannable check + a pointer to the canonical deep file (each verified do-no-harm: the full detail was confirmed present in the deep file before the copy was dropped):
- **Monotonic-quality invariant** (domain D) — near-verbatim from `data-quality.md` (dc even linked while copying); now gist + `data-quality.md` §1 (full invariant + two-part non-regression gate) and §5 (the every-mutation-primitive / discover-write-sites coverage).
- **CSRF-guard-is-not-authentication** (domain B) — the "why it's bypassable" + the CWE-352-vs-CWE-306 split now point to `security-appsec.md`; the check (CSRF ≠ auth → effectively unauthenticated) stays.
- **Open-work triage scope + deliverable** (domain S) — a 3rd verbatim copy; the compact-packet scope rule + the triage deliverable now point to `branch-and-merge-hygiene.md`; the domain-S-unique O/S seam stays.

The other two audit pairs (the F and I sections' 🚩 quick-scan lists) were **assessed and kept**: a 🚩 quick-scan IS the checklist's core function (dc:7), the section headers already route to the fuller lists in the deep files, and dropping them would regress the reviewer's scannability — do-no-harm over literal conversion (A1 rated them Nit/acceptable). Trio → 1.136.0.

## [1.135.0] — 2026-09-18

Wave 56 — link-rot / citation-freshness audit of `docs/standards-index.md` (the "verify before citing" ledger, which `install.sh` vendors into every install's `references/`). Re-fetched every cited URL: content was accurate (**zero drift across ~90 URLs**) but not fully live — **1 dead + 4 moved**, now fixed and each re-verified by direct fetch this session:
- **Dead:** the OWASP ASVS project page now 404s (OWASP is migrating `www-project-*` → `projects/*`) — repointed to `github.com/OWASP/ASVS`; re-verified 5.0.0 / May 2025 / the `v<version>-<chapter>.<section>.<requirement>` id form, and **dropped the L1/L2/L3 level claim** (not re-verifiable on the new URL — ASVS 5.0 restructured; do not cite levels without the 5.0 spec). Date precision corrected "30 May" → "May 2025".
- **Moved (cited content verbatim-intact at the new host):** OWASP Top 10:2025 → `top10.owasp.org/2025`; its A03 detail; OWASP API Security 2023 → `api-security.owasp.org`; the GitHub Actions security page → `.../reference/security/secure-use` (renamed "Secure use reference"; two quotes re-stated to the page's current wording).

Added a dated freshness note at the ledger top; original per-section verification dates left unchanged (they record first verification). Trio → 1.135.0 (the ledger is not a skill; no skill-content change).

## [1.134.0] — 2026-09-18

Wave 55 — a CI gate for the recurring Verification-list doc-sync miss (its root-cause fix). Adding an eval to a skill that enumerates one Verification bullet per eval (closed by "plants these cases") has silently left a later-added eval un-enumerated **four times** (product-output-safety since v1.75.0, undetected until this gate; v1.125.0; and two caught in review at v1.133.0) — no gate referenced eval ids. `scripts/ci-gates.sh enumeration` now has a **check #7**: for a closed allowlist of the six skills that enumerate EVERY eval id (`business-ops`, `contribution`, `growth-analytics`, `positioning`, `product-discovery`, `product-output-safety`), every id in `evals/evals.json` must appear in `SKILL.md`, fail-closed. Scoped by allowlist because the "plants" marker is ambiguous — `idea-critic` and `agentic-ceo` carry it but name only key cases, and the large skills do not enumerate (an unscoped check would false-flag them). Planted-red self-test added, incl. a scoping assertion (`test-ci-gates.sh` 73 → 74). The **fourth instance, caught by the new gate**: `product-output-safety`'s Verification list was missing `confidence-as-defined-tier-not-model-number` (its eval was added at v1.75.0; the behaviour was already in the method at "Show uncertainty as a defined tier", only the enumeration bullet was absent) → product-output-safety 1.3.2. Trio → 1.134.0. The allowlist is **manual and, unlike checks 1–5, does not self-gate**: a new enumerate-every-id skill must be added to it by hand (a typo'd/stale entry is fail-closed by a resolves-check after the loop; a missing addition is not caught).

## [1.133.0] — 2026-09-18

Wave 54 — audit-2 remediation (portability + eval coverage), from two focused follow-up audits.

### Portability — install.sh
Audited against the suite's loudest claim (agent-agnostic install): `install.sh --full --with-codex` lands every skill at all four host roots (`.claude` / `.cursor` / `.agents` / `.codex`), with `references/` — including the vendored `standards-index.md` and `example-review-report.md` — present at **each** root; the claim holds. One fix: the generated `AGENTS.md` **repeated the primary path** ("Primary path: `X` (`X`; also …)") because `LOCATIONS` began with the primary path. It now lists only the **mirror** roots, and omits the parenthetical entirely under `--minimal`. Verified across default / `--full --with-codex` / `--minimal`. (REVIEW.md / `## Code Review Rules` is correctly a Phase-6 review-time imprint, not an install-time write — no change.)

### Eval coverage — four load-bearing rules were untested
The eval-quality audit found rule-consistency and non-duplication **clean across all 11 skills**; the only defects were four load-bearing rules with zero eval coverage. One eval added to each:
- **agentic-delivery** (→ 1.133.0): a paid-model-call lane with no per-lane budget is **BLOCKED** (not run unlimited) and **UNPRICED** (not zero) — the G2 spend-cap invariant.
- **contribution** (→ 1.1.1): a paraphrased confidential fact that **passes the banlist** is surfaced in the residual-risk block for a human — the scrub is necessary, not sufficient.
- **idea-critic** (→ 1.133.0): an objection resting on a **stale number** is re-verified against current state and a sound proposal reaches PASS_TO_USER — the anti-false-negative axis.
- **growth-analytics** (→ 1.1.1): AARRR read **bottom-up** — diagnose retention before pouring in acquisition.

Trio → 1.133.0 (dcr `SKILL.md` version-only, no content change); contribution → 1.1.1; growth-analytics → 1.1.1.

## [1.132.0] — 2026-09-18

Wave 53 — round-3 external research (one net-new gap; the rest of the scan confirmed already-covered). Added a **mutation-testing** lens to domain J (`references/testing-and-evals.md`): the quantified method for the suite's most-repeated testing thesis — coverage measures what *ran*, not whether a test would *catch a fault*. When load-bearing logic leans on a coverage number as its assurance, measure the product suite's fault-detection with a **mutation score**; a **surviving mutant is a finding in the method's own shape** — a `file:line` plus the exact behaviour no test asserts (a High-confidence weak-assertion finding). Names the technique + the CI operator (Stryker's `thresholds.break`; no endorsed threshold number) + representative engines (Stryker JS/TS, PIT JVM, plus per-language equivalents), keeps it **distinct from the gate-planted-defect self-test** (that proves the checker; this scores the shipped tests), and **bounds it to the highest-stakes modules** (a mutation run scales with suite size × mutant count). One new eval (dcr 127 → 128). `docs/standards-index.md` gains pitest.org + stryker-mutator.io (**verified by direct fetch 2026-09-18**). Trio → 1.132.0; `SKILL.md` content unchanged apart from the gate-required version bump (depth lands in the routed reference). (The operator's fail-open default — Stryker's `break` is `null` unless set — is disclosed in the lens so the gate is not mistaken for one that already fails closed.)

## [1.131.0] — 2026-09-18

Wave 52 — self-audit remediation (agentic-delivery leanness). Trimmed the redundant G5 restatement in the "local stack up" procedure (`agentic-delivery/SKILL.md`): it re-stated the G5 gate row's UI rule verbatim, so it now points to G5 and keeps only the unique `product-ux-quality.md` link and the step-3 → G5 tie. Brings the file **24009 → 23945 B, back under 24000** (resolving the float disclosed in v1.129.0; it remains the largest SKILL.md, so its size-allowlist entry stays valid). Trio → 1.131.0; no other skill-content change. (The D2 fork-inheritance bullet was assessed and **kept** — it is the general-lane application, distinct from `parallel-audit.md` §2's read-only-fan-out case, and already cross-refs it; collapsing it would lose the general-lane mitigation. The `domain-checklists.md` middle-tier de-duplication is proposed as an owner decision in #325.)

## [1.130.0] — 2026-09-18

Wave 51 — self-audit remediation (gate hardening, from the four-agent audit's A4 Low). `scripts/ci-gates.sh enumeration` check #6 now **fails closed on a skill dir carrying neither `SKILL.md` nor `VERSION`**. A fully-enumerated but empty dir previously passed the subcommand (checks 1–5 pass; check #6's three branches covered skill-only / version-only / both-present, not both-missing) — the CI *suite* still caught it via the globbed name-matches-dir job and `routing`, but the subcommand was not self-sufficient and its comment over-claimed that checks 1–5 covered the case (the recurring over-claim-in-prose class, here about a gate). Added the both-missing branch, corrected the comment to name the real backstop, and added a planted-red self-test (`test-ci-gates.sh` 72 → 73; the pre-existing ghost fixture's `realskill` is now given files so ghost's omission stays the sole defect). Trio (`deep-code-review`, `agentic-delivery`, `idea-critic`) → 1.130.0; no skill-content change.

## [1.129.0] — 2026-09-18

Wave 50 — self-audit remediation (Perun's own bar on Perun; four independent audit agents found zero Blocker/Critical/High). No change to what a review of a target produces — internal suite cleanup plus one install-time pointer fix. Trio (`deep-code-review`, `agentic-delivery`, `idea-critic`) → 1.129.0; the independent-line overlays touched here bump patch.

### Leanness — deep-code-review (SKILL.md 23872 → 23507 B; hard 24000-byte gate, headroom 128 → 493)
- Collapsed the Definition-of-done status bullet to a one-line pointer: the whole rule (evidence surface, strongest reading, tree-under-review URL/branch/sha, no-surface-named = invalid, `validate_status_claims.py`) already lives in `references/report-format.md`; the DoD restated it. Closes a status-rule-stated-three-times duplication.
- Moved the security-team colour **definitions** to `references/role-coverage.md` (which already tabulates them); **kept the Black-team prohibition inline** (a safety constraint stays in the always-loaded file).

### Provenance ledger — docs/standards-index.md (by name only; no URLs fetched this session)
- Added the threat-modeling method catalog cited inline in `security-appsec.md` / `security-ai-agents.md` — **STRIDE, PASTA, LINDDUN, MAESTRO, attack trees, OWASP SAMM, BSIMM** — closing the recurring cite-without-a-ledger-row miss.
- Added **RFC 2119**, **llms.txt**, **choose-boring-technology / innovation tokens**, and **evolutionary architecture / fitness functions**.
- Added a **product-discovery** by-name row (Mom Test, JTBD switch interview, Torres continuous discovery, Ellis PMF survey, Testing Business Ideas, ICE/RICE, fake-door/concierge/Wizard-of-Oz) and extended the **growth-analytics** row with the experiment-rigor leads (peeking, always-valid/mSPRT, group-sequential/alpha-spending, CUPED, product-led growth).

### Correctness + hygiene
- **Install-time pointer bug:** four overlays pointed unconditionally at `communication-structure`, which their own `--with-*` flags do not install. Conditioned on "if installed" with a BLUF fallback (the `agentic-delivery`/`idea-critic` pattern): **business-ops → 1.2.1, positioning → 1.0.1, product-output-safety → 1.3.1, agentic-ceo → 1.1.1**.
- README: moved **Nielsen's usability heuristics** into the verified-by-fetch summary (it was listed under "referenced by name"); tightened the overlay-count wording.
- `agentic-delivery`: prefixed its three own-reference targets (`template-adr.md`, `retrospective.md`, `template-postmortem.md`; four citations) with `references/` — a bare basename otherwise reads as a `deep-code-review` sibling file. This added ~44 B, floating the file 23965 → 24009 B on its standing owner-reasoned size-allowlist (`ci-gates.sh`); a trim back under 24000 is scheduled with the `agentic-delivery` de-duplication in the next (dedup) wave.

## [1.128.0] — 2026-09-18

Wave 49 of the dogfooding batch: re-applies the machine-report format from external contribution #142 onto current main — the spec for the machine-readable findings file a program consumes. The contribution's author is credited in the commit trailer; the stale fork PR is closed as superseded by this re-application. Lead change is in `deep-code-review`; `agentic-delivery` and `idea-critic` bump in lockstep with no content change.

### Added — deep-code-review
- **`references/machine-report.md`** (#142) — the findings file a program consumes: block-style YAML
  carrying the same findings, ids, severities, and areas as the markdown report, a **coverage row for
  every assigned domain (A–T and W)** (absence of a row is not a clean run — a consumer cannot tell
  "no findings" from "not scanned"), plus the re-verification (`PRIOR`) and fan-out shapes. Routed
  from `SKILL.md` beside the Phase-5 report templates; `report-format.md`'s first machine-report
  mention now points at the spec. Disclosure **extends** the report's finding-level rule: a public
  committed copy keeps finding `id` / `area` / `severity` plus the disclosure-safe run header and
  `target`, and **generalizes** the two identifier-vector fields (`base_ref` per `report-format.md`'s
  branch-name rule, `prior`). One new eval (dcr 126 → 127).

## [1.127.0] — 2026-09-18

Wave 48 of the dogfooding batch: #281 — pricing-strategy methods in `business-ops` Lane A (an independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.127.0 via the CHANGELOG coupling, no dcr content change).

### Added — business-ops (→ 1.2.0)
- **Pricing-strategy methods** (#281). Lane A now names the pricing-method space beyond value/
  cost-plus/competitor: the **Van Westendorp** price-sensitivity survey (structured for the user to
  run; read the band back from their results) and **usage-based / outcome-based / per-seat /
  good-better-best** packaging (tied to the user's value metric; usage/outcome fit AI cost-scaling)
  — applied to the user's willingness-to-pay, never setting the price, never fabricating a survey or
  market number. Methods named by-name. One new eval (business-ops 5 → 6). **OKRs (in the issue
  title) were not added** — goal-setting is outside business-ops's money/compliance two-lane scope.

## [1.126.0] — 2026-09-18

Wave 47 of the dogfooding batch: #276 (regime half) — name-and-route the AI-governance regimes in `product-output-safety` (independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.126.0 via the CHANGELOG coupling, no dcr content change). Completes #276.

### Added — product-output-safety (→ 1.3.0)
- **Name-and-route the AI-governance regimes** (#276, regime half). The hard-boundary and
  Standards-by-name sections now name the **EU AI Act** and **ISO/IEC 42001** (AI-management-system)
  alongside NIST AI RMF, and route the binding applies/obligations/deadline question to counsel —
  **no dates or version numbers** (both regimes revise; the EU AI Act timeline is amendment-sensitive).
  Names and routes only; asserts no duty. One new eval (product-output-safety 6 → 7). With the cards
  half (v1.124.0), this completes #276.

## [1.125.0] — 2026-09-18

Wave 46 of the dogfooding batch: a documentation-sync fix in `business-ops` (an independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.125.0 via the CHANGELOG coupling, no dcr content change).

### Fixed — business-ops (→ 1.1.1)
- **Verification list omitted a shipped eval id.** The `## Verification` "plants these cases" list
  named four of the skill's five evals; added the missing `design-time-regulated-domain-triage`
  bullet so the rules→eval-id map matches `evals/evals.json`. Documentation-sync only — no behavior
  or eval change.

## [1.124.0] — 2026-09-18

Wave 45 of the dogfooding batch: #276 (cards half) — model/data cards as a transparency-artifact check in `product-output-safety` (an independent-line overlay; the AI-governance-regime half of #276 stays owner-deferred).

### Added — product-output-safety (→ 1.2.0)
- **Model / data cards** (#276, cards half). MEASURE gains the transparency artifact: a shipped AI
  feature carries a **model card** (intended use, subgroup performance, limitations, owner+version)
  and a **data card / datasheet** (data composition, provenance, consent, gaps); its absence is a
  transparency finding, and a card stating an unmeasured metric is the no-fabrication floor in a
  template. Cards named by-name (Model Cards / Datasheets / Data Cards; three ledger rows). One new
  eval (product-output-safety 5 → 6). The NIST AI RMF half of #276 was already covered
  (the product-output-safety Standards-by-name section, NIST AI RMF entry); the ISO 42001 / EU AI Act regime half is **owner-deferred**
  (amendment-sensitive). The dcr/agentic-delivery/idea-critic trio bumps to 1.124.0 via the
  CHANGELOG coupling — no dcr content change.

## [1.123.0] — 2026-09-18

Wave 44 of the dogfooding batch: #277 — LLM/agent telemetry (OTel GenAI) + honest developer-productivity measurement (SPACE/DevEx).

### Added — deep-code-review
- **LLM/agent telemetry** in `observability.md` — an LLM/agent feature needs first-class per-call
  signals (token usage, latency, cost, model+version, outcome, a trace), not just service latency/
  error; the **OpenTelemetry GenAI semantic conventions** (`gen_ai.*`) name them — adopt the names,
  pin no version (the spec is at *Development* stability). Do not log raw prompts/responses (PII).
- **Developer-productivity honesty** in `release-engineering.md` (beside DORA) — productivity and
  experience are multi-dimensional (**SPACE / DevEx**); a single proxy (LoC, PR count) is gameable
  false precision; route a people-performance judgement to the owner, never assert it from repo
  activity.

Frameworks named **by-name** (three ledger rows in `docs/standards-index.md`, no URL/version). One
new eval (126 total).

## [1.122.0] — 2026-09-18

Wave 43 of the dogfooding batch: #279 — architecture maturity (Well-Architected), cloud cost (FinOps), and resilience (chaos engineering).

### Added — deep-code-review
- **Well-Architected pillars** in `infra-iac-containers.md` — review the design across the
  cross-cloud pillars (operational excellence, security, reliability, performance efficiency, cost
  optimization; sustainability where tracked), naming which pillar each finding serves; a
  one-pillar-only audit is the gap. No pinned pillar counts.
- **FinOps** in `performance-db-cost.md` — cost as a continuous inform → optimize → operate
  practice; a bill with no allocation/owner/anomaly-alert is a finding, and a cost tool bought
  before allocation just visualizes an unattributed bill.
- **Chaos engineering** in `release-engineering.md` — resilience is exercised, not asserted: a
  steady-state hypothesis + blast-radius-limited fault injection; a DR/failover/rollback path never
  run is `unverified`.

Frameworks named **by-name** (three ledger rows added to `docs/standards-index.md`, no URL / version
/ pillar-counts). One new eval (125 total).

## [1.121.0] — 2026-09-18

Wave 42 of the dogfooding batch: #278 — data contracts + the train/serve seam.

### Added — deep-code-review
- **`data-quality.md` §12 — data contracts & the train/serve seam** (#278). A data contract is the
  declared, versioned producer-to-consumer agreement covering schema + quality/SLA + **semantics/
  units** + owner (the data-plane sibling of `api-contracts.md`'s consumer-driven contract —
  cross-linked, not restated); a producer semantic change that breaks a declared consumer is a
  breaking change even when the row still parses (cents -> dollars passes every type check). Plus
  training/serving skew: one shared feature definition + a point-in-time / as-of join so a feature
  never uses data unavailable at prediction time. Tools named by-name (Great Expectations / dbt); no
  spec or version pinned. One new eval (124 total) + red flags.

## [1.120.0] — 2026-09-18

Wave 41 of the dogfooding batch: #282 — experiment rigor + product-led growth in `growth-analytics` (an independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.120.0 with the CHANGELOG per the lockstep coupling, no dcr content change).

### Added — growth-analytics (→ 1.1.0)
- **Experiment rigor — pre-commit the design, no peeking** (#282). A method sub-section + a DoD
  item + an anti-rationalization row: peeking (stopping the moment p < 0.05) inflates the
  false-positive rate above the nominal 5%; require a pre-committed sample size/duration read
  **once**, or a sequential design with a valid stopping rule; pre-declare a **primary + guardrail**
  metric; CUPED variance reduction where a pre-period exists; a day-2 read of a 14-day test is
  `UNVERIFIED`. Product-led growth: the activation path is the experiment surface, same rigor.
  Frameworks named **by-name** (no version/figure pinned). One new eval (growth-analytics 4 → 5).

## [1.119.0] — 2026-09-18

Wave 40 of the dogfooding batch: #301 — bind the existing release-age-cooldown guidance with an eval.

### Added — deep-code-review
- **Eval for the release-age cooldown** (#301). The cooldown guidance already shipped in
  `dependency-currency-and-upgrades.md` (a 7-day release-age window; Renovate `minimumReleaseAge` /
  Dependabot / pnpm-npm equivalents; security-advisory updates exempt; the no-cooldown red flag).
  This wave adds the acceptance eval that binds it: a routine bump auto-merged hours after publish is
  a finding (missing cooldown, A03 supply-chain), while a security-advisory patch is exempt and
  fast-tracks. No new guidance — the eval closes the #301 acceptance. One new eval (123 total).

## [1.118.0] — 2026-09-18

Wave 39 of the dogfooding batch: #300 — measure pipeline flow before adopting a platform or a second methodology.

### Added — deep-code-review
- **`release-engineering.md` — "Measure the flow before adopting a platform or a second
  methodology"** (#300). Placed beside the existing DORA section (domain K, not observability): the
  DORA metrics say whether the pipeline is healthy; a cheaper set of **iteration signals**
  (time-to-green, queue/runner wait, rerun/flake rate — explicitly **not** DORA metrics) says where
  the loop hurts. Before buying a build/merge platform or adopting a **second delivery
  methodology**, measure both on a p50/p95 basis, attribute the p95 to a stage, take the cheap fix
  first. Adoption bar: *which measured metric does it move, and by how much?* — no number, no
  adoption (route the spend to the owner with the measurement). **One delivery methodology per
  repo** (a measured bottleneck justifies switching, never running both). One new eval (122 total).

## [1.117.0] — 2026-09-18

Wave 38 of the dogfooding batch: #299 — modularize before splitting the repo.

### Added — deep-code-review
- **`infra-evolution-by-stage.md` — internal-package rung before a repo split** (#299). A new trigger
  row plus a short prose note: carve an **internal package** (a named import boundary) inside the one repo first —
  cheap and reversible; split to a **separate repo** only when a part has an independent change
  cadence AND distinct external consumers AND its own release + ownership. Co-evolving artifacts
  (schema ↔ validator ↔ types ↔ docs) stay **co-located** or they drift across repos (domain H); a
  repo split is org/deploy structure, not a substitute for the module boundary. "modular monolith"
  added to the by-name standards list. One new eval (121 total).

## [1.116.0] — 2026-09-18

Wave 37 of the dogfooding batch: #296 — one canonical path→gate manifest across CI, hooks, and the local suite.

### Added — deep-code-review
- **`parallel-audit.md` §6 — one canonical path→gate manifest** (#296). When more than one surface
  routes gates by path (CI `paths:` filters, a hook's file scoping, the local suite's directory→
  suite map), the parallel hand-maintained copies **drift** — a path gated in CI but not the hook
  silently skips its gate on one surface. Keep the glob→gate-set map in **one** version-controlled
  manifest that every surface **derives** from, with a **CI drift-gate** that fails when any
  surface's routing no longer matches it (the no-duplication rule applied to gate routing). An
  unrecognized path resolves to the full gate set (fail closed, already in §6), never to no gate.
  One new eval (120 total) and a §6 signal.

## [1.115.0] — 2026-09-18

Wave 36 of the dogfooding batch: #295 — quarantine the untrusted reader from the privileged actor.

### Added — deep-code-review
- **`security-ai-agents.md` — "Quarantine the reader from the actor"** (#295). The existing
  agent-security controls (spotlight, schema-validate, least-privilege) all live inside **one**
  identity that both ingests untrusted content (tool/MCP output, fetched pages, another agent's
  message) and holds the privileges to act — a confused deputy. The architectural control is a
  **two-role split**: a reader with no credentials/write/egress that emits only structured,
  schema-validated **data operands** (never the action), and a privileged actor whose action is
  fixed by the trusted task plan (plus an action allowlist) and that takes the reader's value
  **only as an operand**. An injection then corrupts at most an operand, not the action — a schema
  validates shape, not authority. For MCP: trust the transport, not the payload. Reviewed as an
  architecture question a per-file diff cannot answer. One new eval (119 total).

## [1.114.0] — 2026-09-18

Wave 35 of the dogfooding batch: #302 — prefer consumer-contract assertions over giant golden snapshots.

### Changed — deep-code-review
- **`api-contracts.md` — contract assertions over a whole-payload golden dump** (#302). The
  Contract-tests section no longer endorses a bare "golden request/response set" for a
  cross-boundary payload: assert the fields/types/constraints a **consumer** depends on, so a
  backward-compatible additive change passes and only a real incompatibility fails. A
  whole-response snapshot fails on every change alike (can't tell a break from a reorder) and
  trains an `--update-snapshots` re-record reflex that rubber-stamps the next real break; golden
  fixtures are reserved for small stable identities (cross-ref `testing-and-evals.md`). One new
  eval (118 total) and a red flag.

## [1.113.0] — 2026-09-18

Wave 34 of the dogfooding batch: #294 + #298 — the evidence tier of a merge gate.

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — "Self-reported evidence is not a trusted control; a local
  hook is advisory"** (#294, #298). A merge decision rests on a forge run verified on the exact
  reviewed SHA; a local hook, a `Tests: N/N` line, and a checked PR-template box are
  self-reported and `--no-verify`-bypassable — never logged as a green control. And under a
  worktree, an inherited absolute `core.hooksPath` or a pre-push hook that diffs a hardcoded
  default branch gates the wrong tree/range (a pre-push hook's real range is the pushed refs on
  stdin). One new eval (117 total) and two red flags.

## [1.112.0] — 2026-09-18

Wave 33 of the dogfooding batch: #297 — terminate work you own without collateral kills.

### Added — deep-code-review
- **`concurrency-shared-state.md` — "Terminating work you own"** (#297). Load-shedding or
  aborting a lane must kill the processes it **owns** (an owned process group / job object,
  terminated by pgid) — never a name/command pattern like `pkill -f` / `killall`, which reaps a
  sibling lane's identically-named process, a shared dev server, or the orchestrator itself
  (collateral damage invisible in any diff). Covers graceful escalation (SIGTERM → grace →
  SIGKILL), killing-then-reaping orphaned children, and a teardown record that leaves the lane
  recoverable. The shedding *trigger* stays in the `agentic-delivery` overlay; this is the
  *mechanism*. One new eval (116 total) and matching red-flag clauses.

## [1.111.0] — 2026-09-18

Wave 32 of the dogfooding batch: #303 — harden the Wave-30 frontmatter gate (enumeration check
#6) to fail closed, closing the fail-open it shipped with.

### Changed
- **`ci-gates.sh` enumeration check #6 now fails closed** (#303). A skill dir must carry **both**
  a SKILL.md and a VERSION — a SKILL.md with no VERSION (or the reverse) now fails and names the
  skill, where before it was silently skipped (a fail-open in a gate whose contract is
  fail-closed). The stamp is read as **metadata.version**, anchored to the frontmatter
  `metadata:` block, so a `version:` in a description block-scalar or the body can no longer
  satisfy it; and an absent stamp, an unparseable stamp, and a drifted stamp are now reported
  distinctly. Two new planted-RED self-tests (missing VERSION; a nested sub-key decoy that must
  not mask a drift) plus a metadata-anchor regression test; the pre-existing missing-stamp
  planted-RED reworded to metadata.version; 72 gate tests.

## [1.110.0] — 2026-09-17

Wave 31 of the dogfooding batch: #271 behavioral-hotspot prioritization for domain H — a
review that leads with the debt that actually costs the team, not every structural smell.

### Added — deep-code-review
- **`domain-checklists.md` domain H — prioritize maintainability debt by team behavior**
  (#271). A ranking lens: order the domain-H findings by change-frequency × complexity (a
  "hotspot") computed from the target's own git history, so the review leads with the debt in
  the files the team keeps touching. It is a ranking lens, **not a severity bump** — a
  structurally ugly file with near-zero churn stays low, and the severity gate still rules each
  finding on its own merits. Distinct from Phase-0 blast-radius (which ranks the *audit scope*
  across all domains). Where git history is absent (shallow clone, fresh import), it falls back
  to complexity alone rather than inventing a churn number. One new eval (115 total).

## [1.109.0] — 2026-09-17

Wave 30 of the dogfooding batch: two process-hardening lessons mined from this session's own
near-misses, filed as #290 and #291 — the recurring-miss fix the skill preaches (pair a rule
with a gate; catch the class the mechanical gates miss).

### Added
- **CI gate: each SKILL.md `metadata.version` must equal its own `VERSION`** (#290). A sixth
  per-skill check inside `ci-gates.sh enumeration` (already run in CI) fails when any skill's
  frontmatter version stamp drifts from its sibling `VERSION`, and names the skill. Nothing
  reads that stamp at runtime, so the drift was invisible to every other gate — it slid on the
  three lockstep skills for seven releases (v1.101.0–v1.107.0) before the #272 fix. Exact match against each skill's
  *own* VERSION, so independent-line skills are checked correctly with no false-positive
  surface. Two planted-RED self-tests (a drift and a missing stamp); 69 gate tests.
- **`method.md` count-invariant for a claimed add/remove** (#291). Under the intent-conformance
  lens (Phase 2), a diff that *claims to add* an item is falsified by an unchanged item count:
  a delta of zero on an add means the new text was spliced into an existing item and silently
  replaced it (two items fused into one). The fusion keeps every byte valid, so lint, format,
  and checksums pass over it — only the count delta or a human read catches the lost item. This
  wave's own Wave 29 near-miss is the worked example. One new eval (114 total).

## [1.108.0] — 2026-09-17

Wave 29 of the dogfooding batch: #268 review-calibration (an anti-slop lens) + #272, the
SKILL.md frontmatter version drift (a real housekeeping bug — the three lockstep skills'
frontmatter had been stuck at 1.100.0 since it stopped moving with the bump).

### Added — deep-code-review
- **`method.md` anti-slop — a review-calibration record suppresses settled nits, never
  security/logic** (#268). A settled style/preference nit the team has already declined — kept
  in a committed, path-scoped review-calibration record (in git, not a hosted memory service) —
  is dropped so the review doesn't re-raise what the owner already dismissed. The record
  **never** suppresses a security, logic, null-deref, or data-validation/data-loss finding;
  calibration silences preference noise, not correctness or safety. One new eval (113 total).

### Fixed
- **SKILL.md frontmatter version drift** (#272). The three lockstep skills' `metadata.version`
  frontmatter had lagged the authoritative `VERSION` file since 1.100.0; bumped to match
  (1.108.0) in all three. A CI gate that fails on `metadata.version` ≠ `VERSION`, so the drift
  can't recur silently, is filed as #290.

## [1.107.0] — 2026-09-17

Wave 28 of the dogfooding batch: three owner-filed CI-diagnosis hygiene lessons (#285, #286,
#287), all into `branch-and-merge-hygiene.md`'s required-check section (extending the #262/#194
SKIPPED and trigger-event content).

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — CI-diagnosis hygiene: a SKIPPED check, a stale base, a hung
  shard** (#285, #286, #287). **#285**: read the workflow `on:` block FIRST and name the right key — for PRs
  *targeting* an integration branch, a required check that never runs is governed by
  `on.pull_request.branches` (the base-branch filter), not `on.push.branches`; absent = a
  structural no-run/Pending block, diagnosed before the cost-gate / flake hypotheses
  (`on.push.branches` only stamps the branch's own HEAD green post-merge, not the open PRs). **#286**:
  a gate diffing against `origin/main` (not the PR base) fails the *whole queue* when the
  integration branch drifts — check the stale base (`git log HEAD..origin/main`) before triaging
  N same-gate failures; sync on each additive `main` merge; a new gate documents its baseline.
  **#287**: a long `in_progress` shard is diagnosed by its log (hang vs timeout), not by waiting
  or rerun-storming; rerun at most once, on evidence. Two new evals (112 total).

## [1.106.0] — 2026-09-17

Wave 27 of the dogfooding batch: two review lenses (round-1 remainder, no provenance risk) —
#269 intent-conformance and #270 the proven-impact bar for the chronically-noisy security
classes.

### Added — deep-code-review
- **`method.md` Phase 2 — intent-conformance is a lens distinct from correctness** (#269).
  Besides "is the code right," ask "does the change do what it *claimed*" — does the diff
  satisfy its PR description / linked issue / stated acceptance criteria? A flawless
  implementation that does X while the ticket asked for Y, or silently drops a stated
  requirement, is a finding cited to the stated intent; where none is stated, say so rather
  than infer. The review-side counterpart to the delivery spec gate (`agentic-delivery` G1).
- **`method.md` anti-slop — a proven-impact bar for the chronically-noisy security classes**
  (#270). The general noise-floor was already the anti-slop rule; this adds that a finding in
  a suspicion-prone class (DoS, rate-limiting, resource-exhaustion, generic input-validation
  with no reached sink, open-redirect) with no demonstrated impact path is held `unverified`
  or dropped to Nit, never posted as a High on suspicion (mechanism-unproven applied to the
  classes that most produce false alarms; a proven path re-promotes). Secrets / authz /
  data-loss keep their severity. Two new evals (110 total).

## [1.105.0] — 2026-09-17

Wave 26 of the dogfooding batch: #280, the ARIA APG per-widget-contract lens — the one
genuine residue of the round-2 a11y gap. Verify-against-repo collapsed the rest:
first-rule-of-ARIA, target-size 24×24 with exceptions, keyboard operability, and the
widget-role grep were already present.

### Added — deep-code-review
- **`frontend-a11y.md` — a custom interactive widget is built to its ARIA APG pattern**
  (#280). Generic keyboard operability was already covered; this adds the per-widget
  contract: each widget class (dialog, tablist, combobox, listbox, menu, disclosure, slider,
  tree) has a prescribed role + states + a **full keyboard map** (dialog: `Esc` + focus trap;
  tablist: `Arrow`/`Home`/`End`; combobox: `Arrow`+`Enter`+`Esc`), so "Tab reaches it" is not
  "operable" — a custom `role="tablist"` with no arrow-key navigation, a `role="dialog"` with
  no `Esc`, or a control whose `aria-expanded`/`aria-selected` doesn't reflect state, is a
  finding. The native-element-first rule still holds; the APG applies only to hand-built
  widgets. One new eval (108 total).

## [1.104.0] — 2026-09-17

Wave 25 of the dogfooding batch: #275, a threat-modeling method lens — the highest round-2
gap after an idea-critic pass revised the sequence (ship #275 as a coverage lens now, the
#267 precision/recall instrument next, #276 AI-governance deprioritized as the lowest
review-action-density and the most date-sensitive).

### Added — deep-code-review
- **`security-appsec.md` A06 + `security-ai-agents.md` — name the threat-modeling method,
  check coverage not ceremony** (#275). A06 already asks "is there a threat model?"; this
  names *which method fits* — STRIDE (per element), PASTA (business impact), attack trees (one
  attacker goal), **LINDDUN** (privacy, the `privacy-by-design.md` counterpart), **MAESTRO**
  (agentic AI, the modeling method behind the OWASP ASI / MITRE ATLAS catalogs in
  `security-ai-agents.md`) — and adds the coverage lens: a change that introduces a trust
  boundary, principal, or state transition the existing model never considered is a finding
  (the model went stale relative to the diff), and an agentic surface with no agent-specific
  model is the common miss. Maturity frames (NIST SSDF, OWASP SAMM, BSIMM) measure the org's
  program — named, not scored. One new eval (107 total).

## [1.103.0] — 2026-09-17

Wave 24 of the dogfooding batch: two of the three HIGH gaps from the 2026-09-17
competitive-landscape research (#265, #266). #267 (a precision/recall detection-eval
instrument) is deliberately **held for its own wave** — an instrument never run is a
specification, not an instrument (principle 2) — and will ship against a corpus built from
this repo's own history (see the #267 scoping note).

### Added — deep-code-review
- **`security-appsec.md` — deterministic corroboration: an LLM claim rides on a proof it
  cannot generate** (#265). Names the code-level SAST/quality engines the field runs (Semgrep,
  CodeQL / code-scanning, SonarQube, Snyk, plus `bandit`/`ruff`/`mypy`/`hadolint`) as canonical
  instruments, `SARIF 2.1.0` / `OSV JSON` as the ingestion format, and the proof↔claim map: a
  taint/data-flow path confirms "input reaches this sink"; a verified-live secret confirms
  "this secret is real"; an exact version↔CVE match confirms "this version is vulnerable";
  reachability turns "you depend on X" into "you execute X's vulnerable path". Running scanners
  (Phase 1) and re-verifying findings (`parallel-audit.md` §4–5) already existed; this adds, for
  a class a deterministic engine can *prove*, corroborate-against-the-proof-or-mark-`unverified`
  — completing the "multi-signal corroboration" principle on the security side.
- **`docs-and-dx.md` / `method.md` Phase 6 — imprint a review-scoped rules block** (#266).
  Beyond the all-tasks `AGENTS.md`, the imprint can carry a review-only surface first-party
  reviewers read: a `## Code Review Rules` section (OpenAI Codex reads exactly that) and/or a
  root `REVIEW.md` (Anthropic's managed Code Review reads it), with the Perun-severity ⇄
  🔴 Important / 🟡 Nit / 🟣 Pre-existing mapping. States the surface split — the managed
  reviewer reads `REVIEW.md`, the local `/code-review` reads `CLAUDE.md` only — so an imprinted
  repo drives a Perun pass and the bots consistently. Content into the existing
  idempotent-additive imprint mechanism. Two new evals (106 total).

## [1.102.0] — 2026-09-17

Wave 23 of the dogfooding batch: four coordination- and review-honesty lenses (#258, #259,
#260, #262). #261 was closed as already covered by the shipped cadence (#253) and ask-ledger
(#257) rules; #262 landed as a review lens, not a repo CI fix (its evidence was a downstream
project's workflow, absent here).

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — a local preflight stricter than the forge's own verdict is
  a deadlock** (#262). When the forge reports a cost-gated job `skipped/Success` (green under
  branch protection) but a locally-added merge preflight refuses that verdict on an
  app-touching PR, and the only unblock is an owner-only label or a manual dispatch, an agent
  is deadlocked — a gate stricter than the standard it enforces (the gate-vs-standard rule,
  here applied to CI). The preflight must diagnose *policy-declined* (cost gate: work exists, a
  human must grant the run) vs *nothing-to-run* (path filter: no in-scope change) and name the
  owner action, not refuse blindly.
- **`method.md` — a pattern-bug is scoped by grepping the idiom, not the first callsite**
  (#259). A Phase 4 finding that matches a copyable idiom (a guard expression, a state-check, a
  pasted data-flow pattern) is scoped by grepping the idiom across the tree in the same pass:
  the search result is the blast radius, reported as one class-finding with its full instance
  set, never the first callsite alone. The review analogue of the one-component-per-concept
  duplicate-twin sweep, for a bug pattern rather than a duplicated component. Two new evals
  (104 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — a process-policy change is not a mid-task interrupt** (#258).
  Extends the interrupt rule: re-ordering the queue, switching serial↔parallel, or reshuffling
  priority queues to the lane's next checkpoint (a filed issue, a pushed commit, a merged PR),
  never mid-edit or mid-compose — each mid-task redirect makes the lane re-orient and ship
  nothing (the interrupt-thrash anti-pattern). The only mid-task interrupt is P0 safety.
- **`fast-agentic-delivery.md` — progress is a durable artifact, not a spawned lane** (#260).
  A lane computing locally with nothing pushed is not-started (`spawned` ≠ `started`, the
  claim-side form of the existing `assigned` ≠ `in-progress`). Grade each lane zero / in-flight
  / done by its durable output; a status names each lane's push / PR / issue URL; the window's
  ETA is projected from the durable-output rate, not the spawn rate.
- **`fast-agentic-delivery.md` — pointer** (#259): two lanes reporting the same bug idiom is a
  missed sweep, not two findings; the review-side rule lives once in `method.md`. Two new evals
  (29 total).

## [1.101.0] — 2026-09-17

Wave 22 of the dogfooding batch: a control disabled only until client state hydrates is
*loading*, not dead (#256); and a long unattended session answers "what's left" from a
durable, ask-indexed ledger, not by re-reading the transcript (#257).

### Added — deep-code-review
- **`product-ux-quality.md` — a control disabled only until client state resolves is
  *loading*, not disabled** (#256). A write control gated on client-only state
  (`useAuth`/`useSession`, a hydration flag) is server-rendered in its `disabled` default and
  looks like a permanent dead control for the SSR → hydration window, but it is in the
  **loading** data state and must *look* loading (skeleton/spinner) — distinct from the
  contextually-unavailable control that stays disabled and owes an explanation. Optimistic-
  enabled is allowed only when the click is captured and replayed after hydration (never a
  dropped no-op, which is the dead-control trust defect). The static `disabled={!session}`
  tell is an `unverified` lead confirmed only by a pre-hydration render — a fourth gate-1
  timing class, and could-not-check fails open. Adds an interaction-completeness bullet, a
  pre-ship checklist item, a gate-1 inspection detector, the timing-class extension, and the
  **pre-hydration capture primitive** its detector cites (a real server-HTML / JS-disabled /
  throttled snapshot procedure in `testing-and-evals.md`, so the gate has a routed positive
  control and is not a citation to an absent instrument). One new eval (102 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — index the backlog by the owner's ask, and read it to answer
  "what's left"** (#257). Extends the unattended-work-loop rule: the durable backlog the loop
  already keeps must also carry the **ask-set** (one row per owner request: id, ask, status,
  evidence, next action), updated at each milestone; "what's remaining" is answered by reading
  that ledger in one or two tool calls, never by an O(N) transcript re-scan that re-litigates
  settled items. A row is done only on the canonical surface (a merged-to-default SHA or a
  live URL), not a branch that merely contains the fix — `project-state.md`'s receipt
  discipline, not restated. Distinct from the review-side end-of-session claim audit
  (`method.md`, #244) and the feedback-coverage map (`roles.md`). One new eval (27 total).

## [1.100.0] — 2026-09-17

Wave 21 of the dogfooding batch: a coordinator's throughput follows its own cadence and the
resource ceiling, not the owner's message frequency (#253).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — the owner's message cadence is not the loop's clock**
  (#253). Extends the unattended-work-loop rule (which already owns the durable backlog and
  pull-the-next-item discipline): a coordinator that refills a lane only when a new owner
  message grants a turn has made human message frequency an accidental concurrency
  controller — throughput sags when the owner goes quiet while safe capacity sits idle. A
  completed lane refills on the coordinator's own cadence; a quiet stretch never lowers
  target concurrency; admission stays governed by the fan-out gates (disjoint surfaces, free
  RAM + swap trend, one-lane-then-re-probe with a burst reserve), never by message count,
  and the target is a maintained concurrency with backpressure, never unbounded spawning.
  Also sharpens the ownership-map rule with the converse over-caution: a shared artifact in
  flight blocks only the lanes that touch it — disjoint-surface lanes proceed. One new eval
  (26 total).

## [1.99.0] — 2026-09-17

Wave 20 of the dogfooding batch: a verification claim names the procedure that produced
it, and a heavy verification run certifies only a frozen, quiescent head (#250, #251, #252).

### Added — deep-code-review
- **`report-format.md` — name the procedure, not just the surface** (#250, #252). A
  verification surface includes the experiment that produced the result: a UI-behaviour
  claim names its interaction method (native keyboard / pointer / scripted DOM call / AT
  command) and exact viewport (+ route/state/sha); an absence claim names its search space
  and runtime confirmation. Two results contradict only when method and viewport match —
  otherwise they are method-sensitive, reconciled one variable at a time, not by picking a
  winner.
- **`method.md` — presence and absence are not the same claim** (#250). An absence finding
  is unfalsifiable from the report (it inherits the searcher's vocabulary), and under
  parallel delivery it is read as a work order — a false absence builds a second, competing
  implementation. Absence is held higher: search by behaviour across every encoding, confirm
  at runtime (principle 2; else `unverified`/unconfirmed-absent, not a gap), a downstream
  builder re-confirms before building, and a disproven absence is reported back. The shared
  surface rule lives once in `report-format.md`; this adds the asymmetry and links to it. Two
  new evals (101 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — release verification runs on a frozen, quiescent head**
  (#251). Release verification (certify one frozen head, once, after integration closes, with
  the machine to itself) is a different contract from defect discovery (continuous, any recent
  head, findings durable when stale) — the same commands run for different purposes. Gate
  release verification on quiescence; freeze and name the SHA (a verdict against a moved head
  is STALE, not pass/fail); give the heavy run the machine; split it so partial progress
  survives; keep discovery findings, discard a discovery verdict. Composes with #247 on a
  different axis. One new eval (25 total).

## [1.98.0] — 2026-09-17

Wave 19 of the dogfooding batch: a rewritten browser spec owes its retired coverage a
structural fallback, and a worktree assignment is a path an integrator can detach onto
(#246, #247).

### Added — deep-code-review
- **`testing-and-evals.md` — a rewritten browser spec names its retired coverage and
  pins the wiring it can no longer reach** (#246). When a redesign makes a spec's target
  surface structurally unreachable in the test environment (a surface that now renders
  only user-submitted content while the test store is intentionally empty) and the spec
  is rewritten against another surface, the dropped coverage must be named as a gap
  (principle 2: an unrecorded absence reads as coverage) and pinned by a source-level
  structural gate — a unit assertion that the wiring still exists. That fallback is
  weaker than the browser scenario it replaces (it proves the component is referenced,
  not that the interaction works) and is never a substitute. A Phase-2 trigger in
  `method.md` routes to it. One new eval (99 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — a worktree assignment is a path, not an adjective; an
  integrator on a shared branch detaches** (#247). "An isolated worktree off `<branch>`"
  is ambiguous — lanes reuse the same checkout and collide on the tree, not on files.
  The brief names the exact path each lane owns and writes only under; an integrator
  folding into a shared branch uses a detached worktree (`git worktree add --detach
  origin/<branch>`), which escapes git's "already checked out" refusal and cannot be
  squatted; a lane verifies tree ownership (`git status --short`) before its first write;
  a gate failing on an untouched file is an environment fault (the collision twin of the
  unowned-file-gate rule above), not a code bug; and another lane's uncommitted work is
  never stashed. One new eval (24 total).

## [1.97.0] — 2026-09-17

Wave 18 of the dogfooding batch: an unattended window is a work loop, a delivery
reconciles its claims against the artifact, and research is not delivery
(#243, #244, #245).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — an unattended time budget is a work loop, not a
  single task** (#243). A granted window is worked until a termination condition fires
  (backlog empty / every remaining item blocked / a resource ceiling), each stated with
  its evidence; the standing backlog lives in a file the loop re-reads, a milestone is a
  cue to pull the next item (an owner stop/redirect is the separate control signal), and
  an idle loop names the condition it is parked on rather than going silent. Extends the
  queue-a-requirement-to-a-file rule to the standing backlog.
- **`fast-agentic-delivery.md` — research is not delivery** (#245). A brief earns its
  cost only when its conclusions become tracked work — each recommendation an
  issue/backlog row/recorded rejection opened in the same step, commissioned with a
  named downstream consumer, reported as consumption not production, with a
  depth-distribution check so the expensive recommendations aren't the ones that
  evaporate. References #235's landed-artifact status rule. One new agentic-delivery
  eval (23 total).

### Added — deep-code-review
- **`method.md` — reconcile the report's claims against the delivered artifact** (#244).
  A Phase 5 sibling to the coverage-ledger reconciliation: enumerate the report's own
  claims and join each to the committed diff (a hunk, a test, a file), reporting
  present/partial/absent including your own misses, trusting the diff over any lane's
  report of what it did, run unprompted before close — an audit that only fires after
  the owner asks "did you actually do all of it?" is a retrofit, not a control. The
  set-completeness question that precedes per-claim verification. One new
  deep-code-review eval (98 total).

## [1.96.0] — 2026-09-16

Wave 17 of the dogfooding batch: the admission schedule leaves a reserve, and a
disabled action explains itself (#239, #240).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — leave a safety reserve when admitting lanes**
  (#239). Sharpens the one-lane-at-a-time admission rule: never fill to 100% of
  observed headroom — leave a reserve so a later spiky lane (a browser gate, a
  dependency install, a test runner) still fits, since observed headroom is
  average-case and the lane that lands the burst is not.

### Added — deep-code-review
- **`product-ux-quality.md` — a disabled action explains its cause and recovery
  path** (#240). Beyond looking disabled (gate 1) and reacting consistently (#230): a
  contextually unavailable action names the unmet prerequisite and a concrete next
  step, in reachable text (nearby or a focusable wrapper/popover — a native `disabled`
  element may get no hover/focus events, so its own tooltip is unreachable); a
  permanently role-unavailable action is hidden or replaced, not a dead end. A
  Pre-ship line and an eval (97 total).

## [1.95.0] — 2026-09-16

Wave 16 of the dogfooding batch: resource-aware fan-out and lane discipline — an
orchestrator that scales a write fan-out by lane count burns hours of spend while the
integration head never moves (#235, #236, #237, #238). All in agentic-delivery.

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — cap in-flight write lanes by landed artifacts**
  (#235). Lane progress is a durable artifact (pushed branch / PR / committed diff),
  never a running transcript; status is "M landed, K in flight, head at `<sha>`", not
  "N lanes running"; admission is earned by completion (a WIP limit, a delivery-ratio
  drain), not by machine headroom.
- **`fast-agentic-delivery.md` — gate a fan-out on the swap trend, not a free-RAM
  reading** (#237). Sharpens the existing swap section: free-RAM% fails open under
  thrash (a post-mitigation number, healthiest under worst load), so sample swap twice
  for direction, let free RAM corroborate a stop but never authorize a spawn, add free
  disk and live-lane count to the probe, and treat a collapse in work rate as the
  resource signal.
- **`fast-agentic-delivery.md` — a worktree is a resource with a lifecycle** (#236).
  Teardown is part of the lane contract; the orchestrator owns garbage collection, but
  GC is advisory and approval-gated (proposes removals, refuses uncommitted-work
  candidates), never an autonomous destructive sweep; free disk and worktree count are
  ceilings the spawn probe enforces.
- **`fast-agentic-delivery.md` — queue new requirements to a file, don't interrupt a
  running lane** (#238). Extends the acknowledge-the-burst rule: new scope goes to a
  durable file the lane polls at its checkpoints; interrupts are reserved for
  stop/redirect; scope is frozen per deliverable; repeated re-briefs mean split the
  lane, not send a third.

Two new agentic-delivery evals (22 total). Lockstep bump to 1.95.0.

## [1.94.0] — 2026-09-16

Wave 15 of the dogfooding batch: an export / print / share-image feature is a second
render surface, produced by a different code path than the screen and never inspected
— so the artifact a user downloads clips content, drops the axes/legend that lived
only in interactive chrome, ignores the theme, or exports a blank image (#232).

### Added — deep-code-review
- **`product-ux-quality.md` — export / print / share is a second render surface**
  (#232). Enumerate every download/print/copy-as-image path (`toDataURL`/canvas, SVG
  serialisation, `@media print`) and inspect the produced artifact like a route: no
  clip of off-viewport content, axis/legend/labels baked in (an interactive-only
  readout needs a static equivalent), theme honored or normalised, self-describing,
  and every data state exported honestly. Folded into the rendered route sweep (#227)
  as "also render every export path"; a distinct axis from the production-build repro
  rule. One Pre-ship line and one eval (96 total).

## [1.93.0] — 2026-09-16

Wave 14 of the dogfooding batch: assembled-product visual review — the domain-P rules
for a single screen existed, but no phase applied them across every route, so a class
of defect spanning many surfaces reached the owner after a green gate (#227, #228,
#229, #230, #231). Each addition references existing domain-P canon rather than
restating it.

### Added — deep-code-review
- **`method.md` Phase 2 + `product-ux-quality.md` — rendered route sweep** (#227). A
  FULL-review step that enumerates every route (router tree AND nav manifest — a
  mismatch is a finding) and rules the domain-P checklist on each across a matrix
  (`{~390, ~1440} × {light, dark} × {top, mid-scroll}` + state transitions), reporting
  coverage as a ledger (a route not rendered is `unverified`, not clean; a clean
  finding doesn't generalise past the routes rendered). The domain-P analogue of the
  anonymous-GET sweep; the matrix is defined here and referenced elsewhere.
- **`product-ux-quality.md` — data visualization** (#228). A chart must answer a
  question legibly: a value axis or direct labels, a keyboard-reachable value+date
  readout, real samples marked with no trend implied across sparse points, and
  non-visual access to the numbers. A heuristic chart-anatomy check folds into the
  enforcing gate's fail-open self-test.
- **`product-ux-quality.md` — layout invariants** (#229). Extends gate 1's inspection
  list with sticky-chrome collision, gutters, optional-slot reservation,
  no-reflow-on-state-change, and tabular numerals — checked mid-scroll and on state
  transitions (the route sweep's matrix), reusing gate 1's geometry primitives.
- **`product-ux-quality.md` — interaction consistency** (#230). Beyond completeness:
  per-class hover/active/focus parity, every hover affordance also reachable by
  keyboard and touch, and tooltips that add information — the divergent-styling defect
  the one-component-per-concept grep can't see.
- **`product-ux-quality.md` — space efficiency** (#231). Footprint tracks information:
  an empty record must not occupy a populated record's footprint, and a grid has a
  density target at the wide viewport — the space-appropriateness complement of the
  honest-empty-state rule.
- **`evals/evals.json`** — four evals (95 total): route-sweep-vs-single-shot,
  mid-scroll layout invariants, interaction-consistency-vs-completeness, sparse-trend.

## [1.92.0] — 2026-09-16

Wave 13 of the dogfooding batch: merge-train and PR-integration hygiene — landing
several PRs safely without dropping or reverting work (#220, #221, #222, #223, #224).
Five lessons, each referencing existing canon (the §5 merge-train mechanism, the
#212 superset-fold sibling) rather than restating it.

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` §5 merge trains — a union/integration PR is verification-only**
  (#220). Its CI aggregates every member's checks, so it is never the critical path:
  don't hold already-green members waiting on union CI, and close the union with a
  pointer rather than squashing or merging it in place of its members.
- **`branch-and-merge-hygiene.md` §5 — red-base discharge** (#224). When the base is
  red and a green-base-required preflight blocks the fixes that would green it,
  discharge the deadlock with a merge train — the union's green discharges the
  "base green at head between merges" wait, and licenses no red member and no
  `--admin` override. References the merge-train mechanism; `release-engineering.md`
  cross-links it.
- **`branch-and-merge-hygiene.md` §5 — a stop halts new work only** (#222). An
  already-green + `MERGEABLE` PR still merges (or is handed off by URL), and an
  unpushed rebase must be pushed or its worktree path + branch + HEAD printed in the
  stop message.
- **`branch-and-merge-hygiene.md` §6 — a subset absorbed at a stale SHA can revert a
  later fix** (#223). B absorbed A's source at an older SHA, so merging B after A
  silently overwrites A's later fix with no conflict; merge the fuller tip first (or
  fold A's missing commits in) and grep the live tree for the fixed symbol. Distinct
  from the generated-artifact superset fold.
- **`branch-and-merge-hygiene.md` §6 — diff two tips before closing a PR as duplicate**
  (#221). Title/branch similarity is not patch equality; **two-dot** `git diff` of
  both heads (`git range-diff` when they forked from different points), fold any
  unique hunk into the survivor, and record the diff in the close comment.
- **`release-engineering.md`** — cross-link to §5's merge trains + red-base discharge;
  the mechanism lives there and this file never restates it.
- **`evals/evals.json`** — three evals (91 total): tip-diff-before-close, stale-SHA
  subset-absorb revert, red-base train discharge.

## [1.91.0] — 2026-09-16

Wave 12c of the dogfooding batch: evidence freshness — reproduce a finding against the
build and SHA it came from, and validate the receipt (#206, #209, #217).

### Added — deep-code-review
- **`method.md` — reproduce a built-artifact finding against the build it audits, not the
  dev server (#206).** The environment axis of reproduction fidelity (sibling of the
  gate's-own-detector and local≠CI rules): a production-build audit finding (a control obscured
  under a sticky header, a WCAG focus-not-obscured failure) often will not appear on the dev
  server — minification, CSS order, hydration, asset paths differ. A dev-server "can't reproduce"
  does not refute it; reproduce against the built artifact or the deployed/preview URL.
- **`method.md` — re-validate a carried-forward finding before repeating it (#217).** A finding
  captured at an earlier `start_sha` is a hypothesis until re-checked: confirm the `file:line`
  still exists at HEAD and re-run the surfacing gate before repeating it. Repeating an
  already-fixed finding is a false positive; reporting a worsened one as unchanged over-claims a
  trust-critical status (rate the claim). A "still open" status holds only at the current SHA.
- **`report-format.md` — the report records its capture SHA (#217).** A `Reviewed at (start_sha)`
  line in the ground-truth block, matching the machine report's field, so a later session knows
  what to re-verify each finding against.
- **`product-ux-quality.md` — the UI receipt must be a valid non-empty image (#209).** A
  proxy/504-wiped screenshot stub passes a bare existence check but proves nothing (existence is
  not content — principle 2); and capture from a clean or separate tree, since a shots script
  that stashes discards the diff under review.
- Two new evals (88 total). Lockstep bump to 1.91.0.

Closes #206, #209, #217.

## [1.90.0] — 2026-09-16

Wave 12b of the dogfooding batch: coordination and stacked-PR hygiene — an ownership map
locks writes, not work; a shared generated artifact needs a superset fold (#210, #212,
#213, #214).

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — attribute a stacked PR's CI failure to the commit that
  owns it (#210).** A PR stacked on another runs its base's commits too, so a base-introduced
  failure turns the downstream red for nothing. Find which commit the failing step is in
  (`git log <merge-base>..<head>` is the PR's own diff; an ancestor commit is the base PR's
  defect) — attribute it to the base PR and never commit the fix downstream (it double-patches
  once the base merges). Composes with 12a's "a run names the SHA it graded."
- **`branch-and-merge-hygiene.md` — a shared generated artifact needs a superset fold, not two
  independent writes (#212).** The existing regenerate-don't-hand-splice rule fires on a
  conflict; the worse case fires on none — two open PRs each rebuild a derived artifact
  (`out/`, a lockfile, `app/data/`) from a shared source, both merge cleanly, and the second
  silently drops the first's regeneration. Trigger: a PR regenerates an artifact while another
  open PR touches the same source (found via `gh pr list --limit 500`). Fix: rebase onto the
  merged first and rebuild (superset fold).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — an ownership map blocks a dual *write*, not dual *work* (#213).**
  Sharpens the SKILL.md occupancy rule: a module-ownership map answers who may write where, not
  whether a lane is already building the objective; a forge assignment is intent, not progress
  (`assigned` ≠ `in-progress`). Check for an active lane on the objective, and announce-then-take
  (claim before opening the worktree).
- **`fast-agentic-delivery.md` — a fan-out ETA states its parallelism assumption (#214).** A
  serial ETA on parallel lanes (or the reverse) is off by ~N×; state the parallelism assumption,
  the constraint that caps it, and both parallel/serial numbers when uncertain. A one-number ETA
  with an unstated assumption is unearned precision — prefer a stated appetite (G0).

Two new evals (deep-code-review 86, agentic-delivery 20). Lockstep bump to 1.90.0.

Closes #210, #212, #213, #214.

## [1.89.0] — 2026-09-16

Wave 12a of the dogfooding batch: a gate is only *run* when its enforcing surface can
see the artifact it checks — CI/gate-visibility honesty (#207, #208, #211, #215, #216).

### Added — deep-code-review
- **`method.md` — a skipped gate scope is `unverified`, not clean (#211, #215).** A
  multi-scope gate that skips a scope whose input is absent (a privacy gate whose
  *identifier* scan needs a pattern list and, missing it, runs only the *secret* scan
  yet exits 0) has not cleared the skipped surface. Read which scopes ran, not the bare
  exit code; a green privacy exit with the identifier scope skipped is not "boundary
  clean" — a status claiming it over-claims a **trust-critical** surface (rate the
  *claim* Critical). An instance of principle 2 (a pass is evidence only where the
  enforcing surface could see the artifact), stated once and referenced.
- **`method.md` — a CI re-run certifies the SHA it ran, not the PR head (#207).**
  "Re-run all jobs" re-dispatches the original frozen payload SHA, so a green re-run can
  certify a stale tree; a status names the commit it graded — a green whose SHA is not
  the PR head is `unverified` for the head. The moved-tree twin of the self-certifying
  gate.
- **`method.md` — name *why* local and CI diverge (#216).** Beyond the gate set:
  sharding/worker count (the existing config-vs-baseline rule), OS font metrics (a
  wrap-point differs by host — assert the layout **invariant**, never an absolute width
  or wrap-point, reinforcing the geometry-not-pixels rule in `testing-and-evals.md`),
  and dirty local resolution (a stale cache or symlinked `node_modules` resolves
  different versions than CI's clean `npm ci` — reproduce on a clean install).
- **`branch-and-merge-hygiene.md` — a required check must be *satisfiable* (#208, #207).**
  A required check whose name is not backed by a job that runs and concludes for this PR
  sits pending forever — indistinguishable from a hang, merge-blocked exactly as a
  failure. A path-filtered skip with no status is not green (fix: emit a conclusive
  status for out-of-scope paths, or don't require that job for that PR class); a
  trigger-event gap (labeled-only, or a `workflow_dispatch` run that never attaches to
  the PR rollup) means the workflow exists but the check never runs. A **High**
  merge-blocker config gap in its own right (guardrail 3: intrinsic, not "Blocker
  because CI is red").
- Two new evals (85 total). Lockstep bump to 1.89.0.

Closes #207, #208, #211, #215, #216.

## [1.88.0] — 2026-09-16

Wave 11f of the dogfooding batch: one screen verified is not the product — scope a
parity claim to the correspondence table (#200).

### Added — deep-code-review
- **`migration-parity.md` — the correspondence table is a coverage ledger (#200).** An
  agent that verified one route (a cheap, shell-less changelog page) reported that *the
  product* matched — the other screens never rendered, and did not match. Gate 4's
  correspondence table (`product-ux-quality.md`) is that ledger; the new rule is it
  **exists before any claim** and each row carries its state (`verified` / `unverified`
  / `n-a`). A parity status is **scoped to the verified rows and never phrased over the
  product**; aggregate phrasing ("the app matches," "all pages") is valid only when
  every row is `verified`, else the honest form is `N of M screens verified — remaining:
  …`. An unrendered screen is an unprobed surface (`SKILL.md` principle 2). Sample a
  **chrome-bearing, data-dense** screen first — a static page proves almost nothing about
  the shell.
- **`report-format.md` — verdict cap + coverage line (#200).** Mirroring the
  `Authz posture` cap: the verdict is **capped below Approve** while any in-scope screen
  is `unverified`, and the ground-truth block carries a `Parity coverage: N/M` line.
- **`scripts/validate_status_claims.py` — fourth detector (#200).** Flags a positive
  parity claim carrying a population quantifier (all / every / whole / the app) but no
  N/M coverage fraction; it requires a parity-context word (so "all tests pass" is
  spared) and fires even on a downgraded row.
- **Severity: High, not Blocker.** The issue proposed Blocker; the `SKILL.md` rubric
  reserves Blocker for "won't build/run/test, live data corruption, live exploited vuln"
  and Critical for a monotonic-quality breach that *will* ship wrong data. A parity claim
  generalized past its sample ships neither — it is a serious defect that **blocks unless
  a named owner accepts** (the High band), because it retires the verification task. Rated
  High accordingly.
- One new eval (83 total). Lockstep bump to 1.88.0.

Closes #200.

## [1.87.0] — 2026-09-16

Wave 11e of the dogfooding batch: a screenshot is an artifact, not an inspection (#198),
and prove a layout claim with geometry, not class names (#199).

### Added — deep-code-review
- **`product-ux-quality.md` gate 1 — the screenshot's inspection contract (#198).** A
  screenshot proves a render happened, not that it is correct: "screenshot attached"
  with no cited inspection is `unverified`, not `verified` (the treatment a parity claim
  with no named surface gets). Gate 1 now defines a **pixel-defect checklist** once —
  overlap / clip-truncation / contrast (`frontend-a11y.md`) / disabled-looks-disabled /
  state — that a UI status must cite. `report-format.md` requires the surface **and** the
  inspection for a UI claim.
- **`testing-and-evals.md` — prove a layout claim with geometry, not class names (#199).**
  A class assertion (`toHaveClass`, `toBeVisible`, a snapshot) passes while two elements
  render on top of each other. New section: a rendered **bounding-box non-intersection**
  assertion at each screenshot width (red-before / green-after), with clip
  (`scrollWidth > clientWidth`) and disabled-looks-disabled (computed affordance)
  companions. **Scope discipline:** non-intersection and non-clipping only — never
  absolute pixels / widths (renderer flake). This is the mechanical proof behind gate 1's
  overlap / clip items.
- **`scripts/validate_status_claims.py` — third detector (#198).** Flags a positive UI
  status leaning on a screenshot (`screenshot` / `.png` / `captured`) that names no
  inspection token (overlap / clip / contrast / disabled / bbox / geometry); it fires even
  on a downgraded row, exempting a row that cites what it inspected.
- Two new evals (82 total). Lockstep bump to 1.87.0.

Closes #198, #199.

## [1.86.0] — 2026-09-16

Wave 11d of the dogfooding batch: budget the CI an agent swarm triggers (#195).

### Added — deep-code-review
- **`parallel-audit.md` — budget the CI a fan-out triggers (#195).** A write fan-out
  that opens many small PRs, each re-triggering the full browser/a11y/e2e matrix,
  multiplies shared runner minutes without improving review. New section: prefer one
  reviewable PR per concern; keep draft iteration on a cheap, path-filtered gate and
  reserve the expensive matrices for a `full-ci` label / manual dispatch / the final
  merge gate; cancel superseded runs with a concurrency group keyed by PR/ref; keep a
  documented one-command local full suite and require the labelled full run before
  merging an app change. **Path filters must fail closed** — a filter that skips a gate
  on an unknown path is a gate exclusion (`method.md`), and privacy/security checks are
  never path-filtered out. **State the residual risk** — the cheap gate will not catch
  browser-only regressions until the full run, so an unrun matrix is `unverified`, not a
  pass (principle 2). The wasted-runner-minutes cost is **Medium**, batched as one
  finding (`branch-and-merge-hygiene.md` §7); only the fail-open filter carries higher
  severity.
- One new eval (80 total). Lockstep bump to 1.86.0.

Closes #195.

## [1.85.0] — 2026-09-16

Wave 11c of the dogfooding batch: coordinate a parallel restyle fan-out (#194) — own
the shared shell before spawning page lanes, and flag work built on the wrong
integration base as High.

### Added — deep-code-review
- **`migration-parity.md` — shell-ownership ledger before a restyle fan-out (#194a).**
  When a multi-screen port/restyle fans out to parallel page lanes, the shared shell
  (layout, nav, tokens, chrome primitives) becomes contested write state that a per-PR
  review passes lane-by-lane while the collision lives between them. Before spawning,
  the lead publishes an ownership ledger (same shape as `parallel-audit.md` §1's unit
  manifest, by reference): exactly one lane owns each shared-shell path (a partition),
  and the shell lands first. Spawning with no ledger is a **High** coordination defect;
  a page lane editing a shell path it does not own is a finding even when its diff is
  correct.
- **`branch-and-merge-hygiene.md` — check the base of in-flight work (#194b).** §2 now
  enumerates open branches/PRs and verifies each base against the detected integration
  target (reusing §3's `git rev-list --left-right --count`); §7 rates a large or
  long-lived change built on the **wrong** integration target (two long-lived branches,
  `STAGE` growth/mature) as **High** — above the Medium merge-debt row, because the cost
  compounds per commit on the wrong base — with the retarget/rebase command named.
- Two new evals (79 total). Lockstep bump to 1.85.0.

Closes #194.

## [1.84.0] — 2026-09-16

Wave 11b of the dogfooding batch: name the parity verification surface (#192), and
prove a design delta before acting on it (#196).

### Added — deep-code-review
- **`SKILL.md` / `report-format.md` — name the verification surface (#192).** A
  `VERIFY_SURFACE` first-response field (url-or-port · tree/worktree · branch · sha,
  or `NONE_RUNNING`), required on a web / port / parity task: `TREE_STATE` is where
  you edit, `VERIFY_SURFACE` is what a human would see, and the two are routinely
  different trees. `report-format.md` sharpens the surface rule — when more than one
  tree can serve the app, "the default served state" is whichever process holds the
  port, so a parity claim names the running instance built from the tree under review
  (URL + branch + sha); a parity claim naming no surface is **invalid, not
  downgraded**; and never direct a human to a URL whose served sha you have not just
  confirmed (per #182).
- **`scripts/validate_status_claims.py` — second detector (#192).** Beside the
  hedged-green detector, flags a positive UI/parity status that names no verification
  surface (no URL, no sha). The sha test requires >= 7 hex chars with a digit, so an
  all-letter hex-looking word is not mistaken for a commit.
- **`product-ux-quality.md` — establish a delta before acting on it (#196).** A
  cropped screenshot of one side is a hypothesis, not evidence: render **both sides at
  the same viewport width** and diff the corresponding region; confirm each app-only /
  design-only element's **state** (present-but-collapsed / disabled-by-data /
  in-a-menu) before calling it a delta; and trust the current rendered reference over
  a stale source comment. A delta that does not exist has no bucket (it feeds the #193
  restyle classification).
- Two new evals (77 total). Lockstep bump to 1.84.0.

Closes #192, #196.

## [1.83.0] — 2026-09-16

Wave 11a of the dogfooding batch: reconcile bidirectional parity (#189) with the
preserve-a-feature rule — restyle an app-only feature, don't delete it (#193).

### Changed — deep-code-review
- **`migration-parity.md`** — new *Restyle an app-only feature into the target's
  design language* section resolves the tension between the parity differ's "app-only
  element is a finding" (#189) and the preserve-a-real-extra-feature rule: classify
  each app-only element as **decoration** (→ remove-to-match), **real functionality**
  (→ **restyle into the target's design language**, preserving the capability — the
  affirmative default, not escalate-and-wait), or **owner-approved removal** (a named
  decision). Deleting app-only functionality to reach visual parity **without a named
  owner approval is High** (do-no-harm, principle 4 — blocks unless a named owner
  accepts). Fill an **exception ledger** (element · bucket · verdict · target
  primitive) before a restyle; the review-smell paragraph and 🚩 signals carry the
  severity.
- **`product-ux-quality.md`** — the bidirectional-parity gate's app-only *feature*
  verdict changes from "escalate to the owner" to **restyle into the target's design
  language** (escalation demoted to the fallback when no target primitive fits);
  *Done* and the parity checklist now read every app→design entry **resolved**
  (restyled / decoration-removed / owner-adjudicated), not "empty". Refines #189.
- One new eval; the #189 eval updated to the restyle-default reading (75 total).

Closes #193.

## [1.82.0] — 2026-09-16

Wave 10 of the dogfooding batch: design parity is bidirectional (#189).

### Added — deep-code-review
- **`product-ux-quality.md`** — the parity differ must check **set equality, not
  containment**: run the mismatch list in both directions per screen (design→app AND
  app→design), and don't wave through app-only elements as "intentional extras". The
  operative test for an app-only element is *does removing it lose a user capability?*
  — pure shell (an extra header, a "Showing N of N" line) defaults to
  remove-to-match; a capability-bearing element (a filter bar, view tabs, per-card
  upvote arrows) is a feature that **escalates to the owner** (never self-cut to match
  a look reference — `migration-parity.md`'s preserve-a-real-feature rule). The
  app→design list routes to owner adjudication, not an automatic differ fail. One new
  eval (#189).

Closes #189.

## [1.81.0] — 2026-09-16

Wave 9 of the dogfooding batch: assert the property, not its proxy (#187, #188).

### Added — deep-code-review
- **`frontend-a11y.md`** — guard a deliberately-decorative / sub-AA colour token at
  its point of **use**, not its value: WCAG 1.4.3 holds informational text to 4.5:1,
  so a value-only test that pins the token sub-AA stays green while a component paints
  text with it and fails the audit. Add a use-site guard that fails when the token
  colours a real text node — fail-closed but with a pinned-exempt escape for text
  1.4.3 genuinely exempts (aria-hidden / decorative / logotype / large text), so the
  gate is narrowed to the standard, not stricter than it. General form: assert the
  property a test encodes, not the value it is derived from (#187).
- **`method.md`** — classify a failure by **config** and **baseline** before calling
  it a regression: a failure seen only under a memory-mitigated `--workers=1` serial
  run can be a shared-state harness artifact the parallel CI config never hits.
  Reproduce under CI's actual worker config (config axis) and under the identical
  reduced config on the merge-base (baseline axis) before reporting a code defect
  (#188).
- Two new behavioral evals.

Closes #187, #188.

## [1.80.0] — 2026-09-16

The offline half of the live eval harness (#61) — the split-rubric runner, no live
model call yet.

### Added
- **`scripts/run-evals.py`** — the execution layer over every skill's `evals.json`.
  `--dry-run` (default) enumerates and classifies every eval as **hard** (a
  deterministic `eval_predicates.py` predicate is bound) or **soft** (needs the LLM
  judge), re-runs the hard-axis golden-pair discrimination, and prints a coverage
  report as JSON — no model, no network, no spend. `--selftest` proves the runner's
  guards offline (the decorrelation guard aborts on an equal *or missing* model id;
  the spend-cap guard aborts on a missing/non-positive cap; the live path refuses
  without configuration). Wired into CI as an offline gate.
- The hard/soft split is derived from `eval_predicates.BINDINGS`, so no `evals.json`
  is tagged and no skill version is forced by it.

### Owner-gated (issue #61 stays open)
- The live model call is an explicit un-built stub — this ships no model-calling
  code, so `--live` cannot spend. Filling the model client + per-call spend
  accounting, the scheduled/dispatch workflow (where the key lives), the committed
  results-freshness gate, and the axis tag across all evals remain owner steps.

## [1.79.0] — 2026-09-16

Wave 8 of the dogfooding batch: verify-the-real-thing (#180, #181, #182). Each lens
extends a shipped one and points at it rather than restating it.

### Added — deep-code-review
- **`infra-iac-containers.md`** — confirm a deploy on a byte only the *new* build
  serves, never `/health`: on a build-then-promote platform the old pod keeps
  answering `/health` = 200 through a slow build's `504`, so poll a discriminator (a
  new-build-only asset path 404 -> 200, a build id, a changed header). Sharpens the
  verify-by-effects rule (#148) (#182).
- **`method.md`** — prove a verify gate *idempotent* (run it twice), not just green
  from a clean clone: a gate whose steps write artifacts a later step consumes can
  pass once and fail on re-run; a non-handler export from a framework route module
  (`.next/types/**`) is one concrete order-dependent trigger (#180).
- **`product-ux-quality.md`** — measure a field's distribution before building a
  confidence/corroboration UI: a near-constant field is false precision even as a
  tier — drop it or reframe to what actually varies (extends the confidence-tier
  detector #155) (#181).
- Three new behavioral evals.

Closes #180, #181, #182.

## [1.78.0] — 2026-09-16

Wave 7 of the dogfooding batch: gate- and probe-honesty (#157, #165, #166, #167,
#168). Each lens points at existing content rather than restating it.

### Added — deep-code-review
- **`security-appsec.md`** (A01) — a downloadable export is a *sharper* leak surface
  than an on-screen view: enumerate every surface serving a sensitive dataset and hold
  exports no weaker than the dashboard; deliver confidential per-viewer data via an
  authenticated, server-scoped API, not an SSR page scoped only by client-side identity
  (#165). Points at the existing dual-surface census, does not restate it.
- **`method.md`** — a no-regressions gate keys on **reachability** over the
  before-vs-after route graph, not surface-position stability: a relocated feature is
  not a removed one, but a genuinely orphaned route is a regression despite a lingering
  label (#157).
- **`data-quality.md`** — §7: a boolean/categorical parser accepts every shape the
  source emits, and an exclusion gate (`is_fund`, `is_deleted`) fails **closed** on an
  unrecognised value, never a silent `false` (#166); a suppression/allow-list match
  compares an **exact value set** through one shared predicate with a row-level audit,
  never a substring (#167). §11: a feasibility probe for a current-state signal gates
  on **freshness** (max-timestamp per metric), not just schema and match-rate (#168).
- Five new behavioral evals; new data-quality 🚩 signals.

Closes #157, #165, #166, #167, #168.

## [1.77.0] — 2026-09-16

Wave 6 of the dogfooding batch: the design-parity **verification** cluster (#169,
#170, #171, #177, #178) — how to *check* an implementation against a design without
rubber-stamping a mismatch. Each lens points at existing parity content rather than
restating it.

### Added — deep-code-review
- **`product-ux-quality.md`** — a **parity differ** as a fourth Phase-6 enforcing
  gate: build a mechanical comparator before pixel-matching and gate every "matches"
  claim on its diff image + structured mismatch list, never a sentence; it proves
  equivalence (not that someone looked) and states what it cannot prove
  (intentional-improvement-vs-regression; threshold agreed, not derived) (#177). Read
  the reference at its highest fidelity — running build > design source > screenshot
  (#169). Classify every diff **structural vs cosmetic**, get structural parity first,
  and never call a structural divergence "close / 1:1" — a different structure is a
  different screen (#170). Repeated correction of a "matches" claim means the
  verification **method** is broken — build the comparator, do not outsource
  verification back to the reviewer (#171). The four-axes structure/styling split was
  sharpened so *presence* is structural and *rendered look* is cosmetic (one taxonomy).
- **`migration-parity.md`** — match the **chrome**, never the mock's **data**:
  copying a design mock's *sample* value into the real product is fabrication
  (principle 3), a Blocker that surfaces weeks later; read the mock's own "sample"
  disclaimer as the boundary; brief the split into every parallel worker (#178).
- Three new behavioral evals; new parity 🚩 signals; one pre-ship checklist line.

Closes #169, #170, #171, #177, #178.

## [1.76.0] — 2026-09-16

Wave 5 of the #143–#164 dogfooding batch: the coverage cluster. All five lenses
apply one existing canonical kernel — principle 2, *"an absence is evidence only
after a positive control fires"* (`SKILL.md`) — at five different scopes, and each
**references** it rather than restating it (the anti-duplication thesis).

### Added — deep-code-review
- **`method.md`** — two gate-coverage axes. A green gate clears only the surface it
  enumerated, not one it never visited: an unvisited route / state / branch is
  `unverified` under that green, not clean, and is distinct from a config-declared
  exclusion (#159). And per-lane / per-flag passes in isolation do not clear the
  shipped union — a regression can live only in the combination no single-lane run
  exercises (#158).
- **`data-quality.md`** — §8: an absent activity window is not a decline (distinguish
  observed-low from unobserved before a number implies a trend), and recency must be
  monotone in elapsed time (#163). §7: carry a per-row coverage / provenance flag and
  keep each score glass-box, so a thin-input score is not read as equal-confidence to
  a fully-covered one (#164).
- **`product-ux-quality.md`** — an empty state must name its coverage
  (no-data-collected vs collected-and-genuinely-none), never imply a false all-clear
  over an unprobed source (#156).
- Four new behavioral evals: gate-coverage, lanes-vs-union, activity-absence,
  empty-state-coverage.

Closes #156, #158, #159, #163, #164.

## [1.75.0] — 2026-09-16

Wave 4 of the #143–#164 dogfooding batch: confidence as a defined tier, not a
false-precision number (#155) — spanning the product-output-safety skill (the rule)
and deep-code-review (the review detector).

### Changed — product-output-safety (1.1.0)
- **`SKILL.md`** — MANAGE's "show uncertainty" rule sharpened: render confidence as
  a defined coarse tier (Confirmed / Corroborated / Single-source / Unverified; text
  plus a colourblind-safe cue), never a false-precision number; publish a definition
  per tier (undefined verbal-probability terms are read inconsistently — Kent,
  *Words of Estimative Probability*); keep source reliability and claim corroboration
  as independent axes; never publish the model's own confidence number as precision
  (#155). One new eval.

### Added — deep-code-review
- **`product-ux-quality.md`** — a review detector: confidence surfaced as a bare
  number ("87%", a raw score) is false precision — flag it and require labeled tiers;
  the tier-definition rule is product-output-safety's, not restated here (#155). One
  new eval.

### Docs
- `docs/standards-index.md` — logged Kent, *Words of Estimative Probability* (read
  from the declassified CIA primary source this session) and the Admiralty Code
  (Wikipedia-verified, cited by name only).

## [1.74.0] — 2026-09-16

Wave 3 of the #143–#164 dogfooding batch: four delivery / observability / privacy
lenses across four references, each pre-distinguished from the section it extends.

### Added — deep-code-review
- **`infra-iac-containers.md`** — the deploy-contract preflight gains two lenses:
  deploy artifact size is a first-class budget — externalize heavy, slow-changing
  assets to object storage / a CDN and fetch large data at runtime; a size-rejected
  upload fails silently while the old pod keeps serving (#147); and a deploy upload's
  HTTP status is not the deploy's outcome on a synchronous-build platform — verify by
  effects (a new deployment id / booted pod / changed served version), and read
  409-vs-timeout before re-uploading (#148).
- **`observability.md`** — audit the logs a platform injects (an auth-proxy sidecar
  dumping per-request PII and an authz-scope list to a shared store), not only your
  app's own log statements (#150).
- **`privacy-compliance.md`** + **`security-ai-agents.md`** — gate a sensitive derived
  value at the source: the exact value stays in a local gitignored cache, only a
  coarse band crosses a boundary (behind an off-by-default flag), and never pull the
  per-row values into a model's context when an aggregate query would do (#154).
- Four new evals (deep-code-review 51 → 55).

## [1.73.0] — 2026-09-16

Wave 2 of the #143–#164 dogfooding batch: six data-quality review lenses, all in
`deep-code-review/references/data-quality.md`, each pre-distinguished from the
section it extends.

### Added — deep-code-review
- **`data-quality.md`** — six lenses:
  - a fanout/uniqueness gate false-blocks legitimate coverage expansion — hard-block
    only a value *absorbed from a now-departed distinct record*, not a newly-shared
    *standing* value among related entities (#149);
  - the resolution order when no stable id exists, and surfacing the unresolved
    count as a first-class output (#153a);
  - never sum heterogeneous constructs into one composite score (#162);
  - test every enum/config mapping against the source's real value distribution,
    not the literals a unit test feeds it (#153b);
  - backtest a proxy-derived metric against ground truth before shipping, and match
    the validation metric to the claim — an ordinal rank validated by concordance /
    a C-index, not MAE (#151, #161);
  - measure existing-source coverage before scoping new enrichment/scrapers, and
    scope to the measured residual (#152).
  - Plus new 🚩 red-flag detectors and a Cyrillic-to-Latin typo fix.
- Six new evals (deep-code-review 45 → 51).

## [1.72.0] — 2026-09-15

Wave 1 of a new dogfooding batch (#143–#164): five field lenses from peer
dogfooding and live-build runs, each pre-distinguished from a shipped neighbor.
Content in deep-code-review + agentic-delivery.

### Added — deep-code-review
- **`frontend-a11y.md`** — a global focus/scroll-into-view correction handler
  (the WCAG 2.2 *Focus Not Obscured* remedy) must yield to an open overlay and
  scope to the focused element's own scroll container, or it scrolls the
  background out from under an open modal — the a11y remedy silently breaking
  `product-ux-quality.md`'s rule that a drawer overlays so "the user keeps their
  place" (#143).
- **`method.md`** — reproduce a gate's finding with the gate's **own detector**,
  not a hand-rolled probe that can "reproduce" a passing state (a repro-fidelity
  axis distinct from the gate being wrong or unrun) (#146); and an **input
  reference is stale until you check its revision + completeness** before building
  on it — the build-time analog of verify-before-you-report (#160).
- Three new evals.

### Added — agentic-delivery
- **`fast-agentic-delivery.md`** — a subagent's transcript size or mtime is
  **not a liveness signal**: never kill (a destructive, shared-state action —
  principle 9) or trust a lane on transcript staleness; judge liveness from the
  agent's actual product (#144); and **serve and commit from separate trees** —
  a long-running process that rewrites a tracked, gate-asserted config dirties
  every commit from the same tree (#145).
- Two new evals.

## [1.71.0] — 2026-09-15

Three more field learnings (#138–#140) from the peer dogfooding run, each
pre-distinguished from a shipped lens. Content in deep-code-review + agentic-delivery.

### Added — deep-code-review
- **`method.md`** — fix the failing **LAYER**, not the first plausible one: a
  missing-value symptom is often a data/config/mapping gap, not a render bug; localize
  the layer before patching (a view fallback masks it), name the proven layer, and
  handle the **two-layer** case (correct default forward + backfill existing records).
  The high-frequency instance of principle 9 (#139).
- **`product-ux-quality.md`** — one component at **two scopes** (single-entity vs
  aggregate/rollup) needs scope-aware copy + per-row attribution + a capped union; a
  distinct axis from #123 (prop) and migration-parity's section-set superset (#140).
- Two new evals.

### Added — agentic-delivery
- **`fast-agentic-delivery.md`** — parallel lanes sharing one **out-of-tree scratch
  path** cross **commit metadata** (lane A commits with lane B's message): invisible to
  a diff-scoped review and not covered by worktree-per-lane; give each lane a unique
  scratch path and verify metadata ownership, not just the diff. 🚩 grep
  `git commit -F <fixed-path>`. Complements `concurrency-shared-state.md` (#138).

### Changed
- Lockstep bump to **1.71.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review + agentic-delivery. Closes #138, #139, #140.

## [1.70.1] — 2026-09-15

Patch: sharpen the #135 lens (`agentic-delivery/references/fast-agentic-delivery.md`)
with the reconciled mechanism from the peer session. A monitor-armed subagent cycles
stop→wake and can emit "completed" more than once for the same task-id, so a single
"completed" is **not proof of terminal completion**. Added the detection **tell** (a
repeated "completed" for the same task-id, or the agent's own last report still
"waiting") and de-hedged the mechanism to what the harness documents (conditioned on
that harness design, kept host-neutral). Eval updated to match. Lockstep bump 1.70.1
(deep-code-review, agentic-delivery, idea-critic, plugin); content: agentic-delivery.

## [1.70.0] — 2026-09-15

Three more field learnings (#133–#135) from a per-surface UI migration + a
merge-train run, sent by the peer dogfooding session. Content in deep-code-review +
agentic-delivery.

### Added — deep-code-review
- **`migration-parity.md`** — unify the **chrome/shell** (per-page header, tab strip,
  stat-tile, sub-nav, the which-tabs rule) **before** porting screens: the scaffold
  level above component unification; a surface that reimplements a chrome primitive is
  a structural defect; align the outlier family to the majority; render the same
  sub-view superset with honest-empty states, keeping a view hidden only when it would
  show a **misleading aggregate** (computed-not-fabricated over tab-count symmetry);
  unify a two-behavior control (nav link vs toggle) as one styling primitive + two
  thin wrappers, never a dual-mode-prop component (#133).
- **`frontend-a11y.md`** — "one control, one role": a dual-mode nav/toggle component
  emits the wrong role/focus/keyboard semantics for the unwired mode; share styling,
  wrap behavior (the a11y half of #133).
- One new eval.

### Added — agentic-delivery
- **`fast-agentic-delivery.md`** — a symlinked `node_modules` breaks the heavy gates
  three ways (`tsc` TS2307 from under-install, dev-bundler boot, `--max-warnings`
  drift); run `npm ci` in the worktree — local-QA-red / CI-green is the tell (#134,
  generalizing #127's symlink note). And confirm a subagent is **idle** before
  dispatching a duplicate lane — a monitor-armed subagent's "completed" can arrive
  while it still runs; the watcher-side complement to #127.1 (#135).
- One new eval.

### Changed
- Lockstep bump to **1.70.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review + agentic-delivery. Closes #133, #134, #135.

## [1.69.0] — 2026-09-15

Wave 2 of the dogfooding batch (#122, #124, #129, #130.1) — the migration /
prototype-reference cluster — landed as a new routed reference under domain P
(`migration-parity.md`), per the owner's structure decision (a reference, not a new
domain). Content in deep-code-review.

### Added — deep-code-review
- **`references/migration-parity.md` (new, routed from domain P)** — the port /
  prototype-reference half of domain P, alongside `frontend-a11y.md` and
  `product-ux-quality.md`. Four lenses:
  - Verify parity **surface-by-surface, on real data**, never from a structural or
    seed-data audit — the latter over-reports parity and misses route defaults,
    missing fields, per-page reimplementations, dropped sub-views (#130.1).
  - Anchor findings on **treatment, not data-volume**: a sparse mockup is not a
    feature spec; separate treatment differences (restyle) from data-volume
    artifacts (progressive disclosure, never deletion) from real extra features
    (preserve). "Drop/remove X to match the reference" is a review smell; a
    height/count delta versus a seed mockup is a notice, not a defect (#129).
  - **Flow-cost** pass — navigation cost (clicks + scroll to complete and to
    reverse/switch) and cognitive load — is first-class, beyond structural/pixel
    parity (#122).
  - A **cited** per-screen craft checklist grounded in NN/g's 10 usability
    heuristics (fetched + logged), Refactoring UI (by name), and the target's own
    design system — a review names the principle, not "looks off" (#124).
- Routed from `SKILL.md` (domain-P table + read-when trigger) and
  `domain-checklists.md` domain P. NN/g moved from by-name to **verified by direct
  fetch** in `docs/standards-index.md` (2026-09-15).
- Four new evals.

### Changed
- Lockstep bump to **1.69.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review only. Closes #122, #124, #129, #130.

## [1.68.0] — 2026-09-15

Wave 1 of a large dogfooding batch (#120–#130, from the peer migration run). Seven
self-contained lenses that each extend an existing section; the migration/prototype
cluster (#122, #124, #129, #130.1) follows in a later release pending a structure
decision. Content in deep-code-review + agentic-delivery.

### Added — deep-code-review (review lenses + detectors)
- **`reliability-error-handling.md`** — fail closed to LAST-GOOD, not to abort, when
  a preflight's live-read failure is stricter than the system's own downstream
  staleness gate; degrade to a snapshot the downstream already trusts, fail closed
  only when none is valid. Distinct from retry (#120). 🚩 added.
- **`testing-and-evals.md`** — testing an outbound alert/webhook from a spawned job
  needs async `spawn` + a localhost listener (`spawnSync` deadlocks the in-process
  capture); assert one POST with a privacy-safe body (#121).
- **`product-ux-quality.md`** — one shared component rendered with a feature-bearing
  optional prop defaulted off at some mount sites is a consistency defect the
  twin-search misses; enumerate every mount site and diff the props (#123). Plus:
  variant/option bloat (N interchangeable ways to view one thing) is a simplicity
  smell — cut to one default, don't tune the set (#125); and unification is a
  **precondition** of a port, not a cleanup pass (#130.2).
- **`report-format.md`** — the "Beware the proxy" passage widened once to name two
  more proxies: a green typecheck/unit suite for a surface that only renders across
  a framework boundary, and merge-state/structural-match standing in for subjective
  UX quality (the felt in-flow experience is the bar) (#126, #128 completion side).
- **`frontend-a11y.md` + domain P** — server/client-boundary lens: a plain
  non-component value exported from a `"use client"` module and imported by a server
  component is silently replaced with a client-reference proxy — an unstyled/empty
  render that passes typecheck, lint, and unit tests; caught only across the real
  split. Lint-shaped static check + fix pattern + debugging heuristic (#128).
- Five new evals.

### Added — agentic-delivery (delivery overlay)
- **`fast-agentic-delivery.md`** — run verification in the **foreground**: a
  sub-agent's backgrounded gate loses its verdict (the parent isn't reliably
  notified after the sub-agent exits) (#127.1). Boot-the-dev-server lanes need a
  copy-on-write clone, not a symlink, of the dependencies dir (the modern bundler
  rejects a path outside its root); a gate must distinguish "could not run" from
  "found a problem" (#127.2). Acknowledge a live-feedback burst before dispatching —
  silent throughput reads as ignoring (#130.3).
- Two new evals.

### Changed
- Lockstep bump to **1.68.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review + agentic-delivery. Closes #120, #121, #123,
  #125, #126, #127, #128. (#122, #124, #129, and #130's remaining part .1 are wave 2.)

## [1.67.0] — 2026-09-14

Four more field-learning lenses (issues #114–#117), continuing the same
dogfooding run. All land in deep-code-review; each verified from source (the
bash-3.2 footgun reproduced live on macOS's `/bin/bash`) and privacy-scrubbed.

### Added — deep-code-review (review lenses + detectors)
- **`security-ai-agents.md` + `domain-checklists.md` (domain C)** — anchor
  relative time deterministically (the time instance of deterministic-first): a
  prompt resolving *today* / *last quarter* must be handed an authoritative
  current date by code — the model never authors *now*, or it ships a plausible
  wrong date as fact (LLM07). Inject the anchor into the **trusted** region,
  never untrusted/RAG context (LLM01 indirect injection); **fail closed** on a
  missing/unparseable anchor — no silent `now()` default. Grep hook added (#114).
- **`language-stack-redflags.md` (Shell / Bash)** — `set -u` + `"${arr[@]}"` on
  an *empty* array is a fatal `unbound variable` under bash 3.2 (still macOS's
  default `/bin/bash`); guard with `${arr[@]+"${arr[@]}"}`. Most dangerous in
  trap/cleanup/reporting code, where it masks the real failure (#115).
- **`SKILL.md` principle 2 + `method.md` Phase 1** — an enforcement artifact (a
  gate / CI / privacy / lint / hook / checksum script) changed in the diff it
  gates is self-certified: green CI ran the shipped copy grading itself. Re-run
  the **base** version (`git show <base>:`) independently; a change that narrows
  what the gate catches while staying green is a Blocker (#116).
- **`reliability-error-handling.md`** — the converse retry/timeout lens: grep the
  project's **own** retry/backoff/timeout primitive and confirm every
  external-I/O site on the critical path routes **through** it; an
  existing-but-bypassed site is the finding, and the fix is to route it through
  the existing primitive, not add a second. Grep lead added (#117).
- Three new evals: `prompt-resolves-relative-date-needs-injected-anchor`,
  `gate-changed-in-diff-rerun-base-version`,
  `reliability-confirm-uniform-primitive-routing`.

### Changed
- Lockstep bump to **1.67.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content changed: deep-code-review only. Closes #114–#117.

## [1.66.0] — 2026-09-14

Five field-learning improvements from a live dogfooding run (issues #109–#113,
filed from a peer session working a real UI-parity migration), generalized and
privacy-scrubbed. Extends the visual/design-parity discipline (1.64.0) with the
measurement root-cause and hardens the delivery overlay for browser-only signals.

### Added — deep-code-review (review lenses + detectors)
- **`product-ux-quality.md`** — "match by measured device-pixels, not user-space
  units — equal user-units ≠ equal pixels"; same-axis oscillation of one property is
  the tell of a duplicated implementation at a different render scale (measure the
  scale ratio and derive, don't tune; validate you measured the visible ink, not an
  overlay/focus path). Cross-refs the stop-tuning discipline (#109).
- **`product-ux-quality.md`** — cross-file UI duplication is invisible to a
  diff-scoped review; the duplicated visible literal string/heading is the search key
  that surfaces the twin the user renders (#112).
- **`domain-checklists.md` (domain P)** — an SSR/hydration restricted-content-model
  nesting detector (a block-level element or `<p>` inside a `<p>`, nested
  `<button>`/`<a>`): the browser auto-corrects it, so it is absent from the hydrated
  DOM and can be state-specific — scan the SSR/static output in the specific state,
  not the live DOM (#111). Grep hook added.
- Three new evals: `visual-parity-measure-pixels-not-user-units`,
  `ssr-hydration-restricted-nesting-scan-static`, `duplicate-ui-twin-across-files`.

### Added — agentic-delivery (delivery overlay)
- **`fast-agentic-delivery.md`** — draft-gated heavy/browser gates hide a
  UI-regression wave: fast-tier-green is not UI-correct; run heavy gates on the
  integration branch periodically while the draft is open (or budget the wave), and
  verify browser-only signals centrally (#110).
- **`fast-agentic-delivery.md`** — delegate visual/parity work by measured number,
  not adjective: numeric acceptance targets up front; the lane returns a measurement
  table the coordinator confirms against the reference (#113).
- Two new evals: `draft-gated-heavy-checks-hide-ui-regressions`,
  `delegated-visual-work-needs-numeric-targets`.

### Changed
- Lockstep bump to **1.66.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content changed: deep-code-review + agentic-delivery. Closes #109–#113.

## [1.65.0] — 2026-09-14

Trims `agentic-delivery/SKILL.md` back under the 24,000-byte size budget
(28,049 → 23,954 B) by relocating operational depth to its routed reference —
the skill's own progressive-disclosure rule applied to itself. No rule, gate, or
principle removed. The `agentic-delivery` size-allowlist pin in `ci-gates.sh` is
now droppable (routing reports plain `ok`, no `SIZE ALLOWED`); removing the pin
itself is left as a separate owner call.

### Changed
- **`agentic-delivery/SKILL.md`** slimmed: the fan-out-sizing tiers + pilot
  procedure and the environment-probe procedure (probe commands,
  decide-from-probe, shell-semantics, contention-vs-defect) moved to
  `references/fast-agentic-delivery.md`; the act-on predicate (free RAM + swap
  trend), the Conductor's event-driven rhythm, the drift rule, and
  escalate-after-two-failures stay in the core. Prose compressed throughout.
- **`agentic-delivery/references/fast-agentic-delivery.md`** gains the relocated
  **Environment probe procedure** and **Size the fan-out** sections; its framing
  (read-when, the load-average section's opener, and the cross-references)
  updated so it no longer claims the probe procedure lives in `SKILL.md`.
- Lockstep bump to **1.65.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` changed content.

## [1.64.0] — 2026-09-13

Sharpens the visual/design-parity discipline (issue #105). The 1.62.0/1.63.0 work
made the **default served state** the canonical parity surface and named the proxy
trap; a real dogfood run still shipped a false "looks the same" ✅ by walking
*around* that rule — offering a **structural** check as visual evidence,
**reconfiguring** what "default" means and then verifying it, conflating the four
axes, and **guessing** the axis instead of asking. This closes those gaps.

### Added
- **`product-ux-quality.md` — new section "'Looks the same' is about rendered
  appearance — four axes, and a structural check is not a visual one."** Names the
  four independent axes (**structure / styling / content / data**) and forbids
  conflating them (a section-order/DOM diff is a *structure* claim, never "looks the
  same"; do not "fix" data to answer a styling complaint); a
  structural/DOM-order/section-presence check (or a passing test / loaded data) is a
  **proxy** for rendered appearance — claim parity only from a computed-style and/or
  screenshot diff of the default state; **do not move the goalpost** (reconfiguring
  the default persona/seed/flag then verifying "the default" measures a surface you
  authored); **enumerate every diff in one pass** before fixing (piecemeal-fix-then-
  redeclare is the repeated-false-✅ loop); **disambiguate the axis** when told "not
  the same" (after one wrong guess, ask not guess); the **reference** is truth for
  styling — compare element × breakpoint × theme, not memory. Four new pre-ship
  checklist items.
- Three new evals: `visual-parity-structure-not-styling`,
  `visual-parity-default-not-reconfigured`, `visual-parity-ask-axis-not-guess`.

### Changed
- **`report-format.md` — proxy trap widened.** A **structure/DOM-order or
  section-presence match** and a **self-reconfigured surface** (switching the
  default, then verifying "the default") are named as proxies alongside the passing
  test / green build / merged PR / hand-configured render.
- **`SKILL.md`** — domain-P routing trigger now fires on visual/design-**parity**
  work ("make X look like Y", a port/restyle/redesign), where the claim is about
  rendered appearance, not structure/tests/data.
- Lockstep bump to **1.64.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content. Closes #105.

## [1.63.0] — 2026-09-13

Completes the completion-claim discipline (issue #101) — the proxy trap, the
completion record, and a mechanical checker. Builds on 1.62.0 (which shipped the
default-state-canonical + caveat-downgrade core).

### Added
- **`deep-code-review/scripts/validate_status_claims.py`** — a heuristic checker
  ("a ✅ that needs an asterisk is a ✗"): given a status table it flags a positive
  status (✅ / done / exact / matches / verified / complete) co-occurring with a
  hedge (if / only / once / unless / requires / caveat / mostly …) and no
  downgrade marker (⚠️ / ❌ / partial / blocked / unverified). Exit 1 = candidates
  to re-check, 0 = clean, 2 = usage. A lead for judgement, not an automatic
  defect. Ships beside the skill (copied by `install.sh`), routed from
  `report-format.md`, with a self-test in `test-ci-gates.sh` (planted hedged-green
  flagged; an honest downgrade not flagged; a clean table passes).
- New eval `completion-claim-proxy-not-user-outcome`.

### Changed
- **`report-format.md`** — the **proxy trap** named explicitly (a passing test /
  green build / merged PR / hand-configured render is a proxy for the user's
  outcome, not the outcome) and the **completion record** (a status carries
  `(surface · default-state observed · reference checked) + what was not checked`).
- Lockstep bump to **1.63.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content. Closes #101.

## [1.62.0] — 2026-09-13

Status-claim honesty (issue #102) — closes a trust gap surfaced by a real
over-claim: an agent marked a rebuilt UI "✅ exact" after checking a mock and a
hand-picked view, not the default state a user lands on, and kept the ✅ despite a
noted caveat. The status-reporting discipline already existed (`report-format.md`,
`product-ux-quality.md`); this closes the two holes the failure fell through.

### Changed
- **`report-format.md`** — a status names the **surface** its evidence came from
  and holds at its **strongest reading**: a `✅` / done / exact / matches / verified
  the author can immediately qualify is **downgraded** (⚠️ / partial / ❌), never a
  green label beside a caveat ("caveat-exact isn't exact"). For a UI/parity claim
  the canonical surface is the **default served state**.
- **`product-ux-quality.md`** — new "Parity claims: the default state is the
  canonical surface" section + checklist items: verify the **default landing
  state** (signed-out / no-role / default route / local default), not only a mock
  or a hand-picked persona view; a claim resting on a non-default surface must name
  it; no status green-with-a-caveat. "More than the happy-path state" is necessary
  but not sufficient — the default must be among the states checked.
- **Principle 2** (`SKILL.md`) — a status you emit names its evidence surface,
  holds at its strongest reading, downgrades on a caveat, and takes the default
  served state as canonical for a UI/parity claim.
- New eval `ui-parity-claim-checks-default-state-not-mock`. Lockstep bump to
  **1.62.0** (deep-code-review, agentic-delivery, idea-critic, plugin); only
  `deep-code-review` gained content.

## [1.61.0] — 2026-09-13

Domain-C review lens for **agent context/memory lifecycle** — the one genuine gap
found by a verify-grounded scan of the 2026 agent-building frontier (context/
memory management, recursive & multi-agent orchestration, agent security). The
scan's headline was that the bar is **current** — OWASP LLM/Agentic/Agentic-Skills
all on their latest 2026 editions, and most frontier concepts already owned by the
suite; this ships the single genuine gap the scan found.

### Added
- **`security-ai-agents.md` — "Context & memory lifecycle" defensive lens** (domain
  C): a long-running agent that summarizes/compacts context, evicts old tool
  results, or persists memory can **silently drop a safety constraint** (approval
  scope, authority grant) with **no attacker and no crash** — so ASI06 (adversarial
  poisoning) and F (crash recovery) miss it by construction. Reviews the lifecycle:
  compaction preserves/re-asserts constraints; tool-result clearing exempts the
  constraint/authority-bearing item; persistent memory validates on write and
  expires; cross-agent handoff carries the full trace; resume revalidates authority.
  Cross-refs `agentic-delivery/references/project-state.md` (the delivering-agent
  runbook — here it is a review check over the *target*), ASI06, LLM09, and domain
  T. New eval `agent-context-lifecycle-constraint-survives-compaction`; 🚩 tells
  added to the C checklist in `domain-checklists.md`.
- **LLM06 "bound the tree, not just the call" clause** — in a recursive/multi-agent
  system the depth/step/spend cap must be propagated to every spawned sub-agent, or
  a parent cap not forwarded leaves the tree unbounded (a real filed bug class).

### Changed
- `docs/standards-index.md` — six sources verified by direct fetch this session
  (2026-09-13): Anthropic long-running-agents (2025-11-26), context-editing,
  compaction, and memory-tool docs; Cognition "Don't Build Multi-Agents"
  (2025-06-12); langchain-ai/deepagents #1698.
- Lockstep bump to **1.61.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.60.0] — 2026-09-12

Two new review domains — the taxonomy grows from A–S (19) to A–W (21): **T
Multi-tenancy & isolation** and **W Workflows, jobs & scheduling** (issue #96).

### Added
- **Domain T — Multi-tenancy & isolation** (`deep-code-review`): the cross-tenant
  leak that survives a clean access-control review — a cache / index / pool / job
  that forgot the tenant key, tenant context outliving its request, per-tenant
  lifecycle (export & deletion across every store), noisy-neighbour fairness, and
  the isolation model (row-level / schema / silo-per-tenant). Checklist-only in
  `references/domain-checklists.md` (like A/H/N/R); the seam is stated explicitly
  against **B/A01** (authz / IDOR) and **G** (races). New eval: a tenant-less
  cache key leaks across tenants even though the authorization review is clean.
- **Domain W — Workflows, jobs & scheduling** (`deep-code-review`): orchestration
  correctness for cron, queues, and multi-step workflows — never-runs (liveness),
  runs-twice (exactly-once *effect* on at-least-once delivery), dead-letter and
  retry caps, cron timezone / DST, ordering, durable long-running / saga state
  with compensation, and backpressure. Checklist-only; the seam is stated against
  **F** (single-call handling) and **G** (races), and scoped **out** of **E**
  (one-time migrations) and **K** (deploy / rollout). New eval: an at-least-once
  billing job needs an idempotent effect, a liveness alert, and an explicit
  timezone.

### Changed
- **Taxonomy A–S → A–W (21 domains).** Propagated the range through `SKILL.md`
  (domain map, phases, both role tables), `domain-checklists.md`, `method.md`,
  `role-coverage.md` (T assigned to the Backend lead, W to Platform / DevOps / SRE
  so no domain is orphaned), and `README.md`. **U, V and X–Z remain unassigned** —
  a domain earns its letter; the map grows only when a genuinely new class of
  defect does, never to pad the alphabet.
- Lockstep bump to **1.60.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.59.0] — 2026-09-11

README-authoring method — so the skillset produces onboarding READMEs for any
project, not just this one.

### Added
- **`deep-code-review/references/readme-authoring.md`** — the depth behind the
  domain-O "README (human-facing)" checklist: model the reader (default the
  evaluator), the plain-value-first onboarding arc with progressive disclosure,
  one host-native diagram (quote Mermaid labels; no external badges — a rotting
  live value), the anti-slop craft (superlatives out, tables over repeated
  patterns, no uncontrolled third-party claims), accuracy-vs-code (every
  command/flag verified against the tool; verify a pin actually pins), and keeping
  the **safe install path as the quickstart**. Generalized from this repo's own
  README overhaul and its independent review; routed from domain O and cross-linked
  from `docs-and-dx.md`. New eval resists two planted bad asks (a version badge; a
  shorter-but-unsafe install first).

### Changed
- Lockstep bump to **1.59.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.58.0] — 2026-09-11

Adopt the **Perun** umbrella brand (issue #38) — theme + wordmark only.

### Changed
- **README hero + `plugin.json` description** rebranded to **Perun** ("bring the
  thunder to your codebase") — the suite's umbrella identity, named for the
  Slavic thunder god of order and justice (strikes down chaos, never fabricates,
  leaves the bar in place). The **flagship skill name `deep-code-review` is
  unchanged**, as are all sibling skill names; the brand is the suite/repo layer.
  Added `perun` to `plugin.json` keywords.
- **Repo-slug rename deferred** (owner decision): GitHub redirects make it safe
  to do anytime; the pinned URLs to update when chosen are README (clone + npx
  slug) and `plugin.json` (homepage/repository). Brand adopted first.
- Copy kept **agent-agnostic**: "for building with AI agents", any major coding
  agent — no single-vendor focus.
- Lockstep bump to **1.58.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed (branding metadata only).

## [1.57.0] — 2026-09-11

Support & feedback operations lens (issue #44, G3) — agentic-delivery.

### Added
- **`agentic-delivery/references/support-ops.md`** — narrow reactive support-ops:
  an intake + triage taxonomy, a per-severity SLA template (owner sets the
  numbers), canned-response quality, and the **support→backlog loop** (a ticket
  revealing real work becomes a well-formed work item via the Where/Done-when/
  Verify/Why contract). **Load-bearing safety gate:** never auto-send an external
  reply and never make a promise/refund/commitment without owner approval — the
  same human-approval-on-external-action gate the skill applies to push/deploy.
  It cross-refs rather than restates: `incident-response.md` (outage tickets),
  `deep-code-review`'s `docs-and-dx.md` (Diátaxis help-center), and
  `communication-structure` (no-slop responses). Scope is narrow — not
  onboarding/activation (growth/product-ux). New evals: a ticket becomes a
  well-formed backlog item; no external reply/refund is auto-sent without
  approval. Independently reviewed before merge.

### Changed
- Lockstep bump to **1.57.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` gained content (a reference + a minimal routing
  pointer + two evals); it stays allowlisted for SKILL.md size (a trim pass into
  references is due).

## [1.56.0] — 2026-09-11

Adopt the two additive principles that were not yet codified (issue #37).

### Added
- **`deep-code-review/references/docs-and-dx.md`** — a "Persisted knowledge
  hygiene — store the query, not the answer" lens (domain O): a durable doc/memory
  that records a fact derived from live state (an issue count, a current version)
  rots; store the *query* that regenerates it. Audits a memory store / `AGENTS.md`
  / runbook for three decay modes — dead paths, status-without-a-command, and
  embedded credentials (cross-ref `privacy-compliance.md`) — each a finding.
- **`agentic-delivery/SKILL.md`** — a **work-item contract** beside the output
  contract: a work item is specified as **Where / Done-when / Verify / Why**, and
  one missing *Done-when* or *Verify* is underspecified and sent back to be scoped,
  not started (the input the output contract is graded against).

### Notes
- The third sub-item (a — the suite map as a *registry that describes access, never
  copies*) was already adopted: `agentic-ceo/SKILL.md` frames the registry as "a
  map, not a bundle" and its anti-rationalization table rejects restating a skill's
  steps. No change needed there; verified before closing.
- No duplication introduced (the memory-audit's secret check cross-refs the privacy
  reference rather than restating it; the work-item contract has no prior home).

### Changed
- Lockstep bump to **1.56.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin).

## [1.55.0] — 2026-09-11

Design-time regulated-domain obligation triage (issue #43, G2) — business-ops.

### Added
- **`business-ops/references/regulated-domain-triage.md`** (business-ops → 1.1.0)
  — the design-time front door for Lane R: a decision tree that runs *before the
  architecture hardens* (and re-prompts on entering a new market or handling a new
  data type). Triggers — health data, payments/card data, minors, EU/UK personal
  data, US-state privacy, biometrics, consequential/automated decisions, money
  movement, enterprise security — each **name the regime** (HIPAA, PCI DSS, COPPA,
  GDPR/UK GDPR, CCPA/CPRA, biometric-privacy, SOC 2/ISO 27001, and the like, by
  name only) and surface engineering-obligation **leads**, then **route the binding
  question to counsel**. The privacy branches point downstream to
  `deep-code-review`'s `privacy-by-design.md` (pre-code artifacts) and
  `privacy-compliance.md` (engineering) rather than restating them; it reuses Lane
  R's asymmetric boundary instead of duplicating it. **Boundary:** name + route;
  it never determines that a regime binds this business, and asserts no article
  number, threshold, or deadline. New eval: a health/payments/minors input yields
  a "route to counsel + named regime", never a compliance conclusion. Unblocks the
  G4/G5 lenses (they inherit the named regime).

### Changed
- Lockstep bump to **1.55.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `business-ops` gained content (independently versioned 1.0.0 →
  1.1.0).

## [1.54.0] — 2026-09-11

Two deep-code-review lenses: privacy-by-design product artifacts (issue #46, G5)
and billing/monetization correctness (issue #48, G7).

### Added
- **`deep-code-review/references/privacy-by-design.md`** — the pre-code
  privacy/compliance *artifacts* an EU user or enterprise buyer demands, as a lens
  over domain Q: a ROPA-style processing register, a DPIA scaffold + risk
  questions, a consent-UX spec, a subprocessor list with data-flow notes, and
  data-residency options. It sits *above* `privacy-compliance.md` (which stays the
  code layer — inventory, retention/DSAR/erasure, consent recording) and links to
  it rather than restating it. **Boundary:** scaffold + gap-detect; the
  privacy-policy/ToS text, whether a DPIA is legally required, and lawful-basis
  selection route to counsel. Frameworks named by name only; **no article numbers
  or legal deadlines** until fetched. New eval: a new PII field prompts the
  register/DPIA question.
- **`deep-code-review/references/billing-correctness.md`** — a mechanics lens on
  domain E (cross-ref F/G/I) for revenue correctness: metering (exactly-once),
  proration, dunning/failed-payment recovery, tax/VAT *application in code*,
  refunds/chargebacks, webhook idempotency, and the double-charge/revenue-leakage
  races. **Boundary:** review the logic; tax registration/filing and
  revenue-recognition policy route to an accountant, pricing to the owner
  (`business-ops`); **no invented tax rate**. New eval: a double-charge race and a
  non-idempotent webhook are both flagged.

### Changed
- Both references routed from the domain table in `deep-code-review/SKILL.md`
  (rows E and Q) with when-triggers; SKILL.md 21298 → 21439 bytes, well under the
  24000 budget.
- Lockstep bump to **1.54.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.53.0] — 2026-09-11

Operational-readiness lens — incident response + continuity (issue #45, G4).

### Added
- **`agentic-delivery/references/incident-response.md`** — the "system on fire
  OR the operator is gone" binder for bus factor = 1. Incident runbook
  (detect→triage→contain→eradicate→recover→blameless review), severity-level and
  status/comms templates, a break-glass access path, a credential/renewal
  inventory (domain, TLS, card, DNS, secrets) with **dead-man** reminders, a
  restore-drill schedule, and a solo-operator succession note. It reuses the
  blameless `template-postmortem.md` / `retrospective.md` for the review step and
  points restore/observability depth at `deep-code-review` rather than restating
  it. **Boundary:** breach-notification *timing* routes to G2 + counsel and is
  never asserted here; executing notification/succession is the owner's; no
  invented SLA, deadline, or renewal date. New eval: a planted expired TLS
  credential is surfaced, a restore-drill schedule is present, and the breach
  deadline is routed, not fabricated.

### Changed
- Lockstep bump to **1.53.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` gained content (a reference + a minimal
  routing pointer + one eval); the routing pointer keeps the allowlisted
  SKILL.md's growth to routing, not depth.

## [1.52.0] — 2026-09-11

Decision-hygiene frame for the builder's own hard calls (issue #47, G6).

### Added
- **`idea-critic/references/decision-hygiene.md`** — a routed reference that
  structures the owner's *own* high-stakes call (pivot, quit/kill, big
  irreversible spend) rather than attacking a proposal. Frame: one-way vs
  two-way door classification; the outside view (reference-class / base rate);
  sunk-cost, confirmation, and escalation-of-commitment surfaced; and
  kill/quit/pivot criteria pre-committed *before* the bet. It reuses the
  `kill-criteria` premortem instead of restating it, and it **structures** the
  decision for the owner — it never makes the call and never fabricates a
  probability (an ungroundable number is labeled `assumption`).

### Changed
- Lockstep bump to **1.52.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `idea-critic` gained content (a reference + its routing pointer).

## [1.51.0] — 2026-09-11

Routing-eval coverage for the conductor (issue #63, offline half).

### Added
- **`agentic-ceo/evals`** — a routing eval per registry destination (deep-code-review,
  agentic-delivery, idea-critic, growth-analytics, positioning, product-output-safety,
  communication-structure, contribution — joining the existing product-discovery /
  business-ops / owner cases). Each pins a (stage, area, artifact) prompt to its
  expected skill and asserts the routed method is not re-implemented inline
  (registry-not-bundle).
- **`test-ci-gates.sh`** — a coverage assertion: every shipped skill except the
  conductor must have an `agentic-ceo` routing eval, so a destination cannot be
  mis-routed unnoticed. Now 55/55. Live grading of each case rides the eval harness (#61).

### Changed
- Lockstep bump to **1.51.0** (deep-code-review, agentic-delivery, idea-critic, plugin).
  No skill content changed (conductor evals + a self-test added).

## [1.50.0] — 2026-09-11

Gives the SKILL.md size ratchet teeth and gates the install overlay-stamp guard
(issues #16, #83).

### Changed
- **`ci-gates.sh routing` size budget now FAILS, not warns** (#16). An oversized
  `SKILL.md` fails the gate against the documented byte budget (`ci.yml` enforces
  **24000**), unless the skill is on a small reasoned allowlist in `cmd_routing`
  (today only `agentic-delivery`, the full G0–G10 delivery OS). A pin is allowed its
  overage, never required to keep it. Documented in
  `references/skill-authoring-and-size.md`.

### Added
- **`test-ci-gates.sh`** — a non-allowlisted oversized `SKILL.md` now FAILS (was a
  warn); an allowlisted one passes with a `SIZE ALLOWED` note; and every
  skill-adding overlay flag (`WITH_*` guarding a `SKILLS+=` block) must appear in the
  AGENTS.md overlay-stamp guard, so a standalone `--with-<x>` install cannot land a
  skill without its stamp (#83 — the class fixed in #82). Now 54/54.

### Changed
- Lockstep bump to **1.50.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed (a reference doc gained the budget number).

## [1.49.0] — 2026-09-11

Fixes the plugin-install rail and stale first-party metadata (issues #78, #72, #80,
#79). A `/plugin install` or marketplace pin previously discovered **zero** skills —
skills live under `.claude/skills/` but the plugin default scans a root `skills/` and
`plugin.json` declared no `skills` path, so only metadata loaded. Same honesty class
as #55 (documented pin vs actual tree).

### Fixed
- **`.claude-plugin/plugin.json`** — add `"skills": "./.claude/skills"` so the plugin
  rail discovers all 11 skills (the field supplements the default `skills/` scan; path
  relative to plugin root, per the Claude Code plugins reference fetched this session).
  `install.sh` already copied from `.claude/skills/`; the two rails now agree (#78).
- **`plugin.json` description** — was a three-skill string ("gated-delivery and
  idea-critic"); now states the real posture (review-only default + opt-in overlays)
  without copying any skill's method (#72). The GitHub About field was updated to
  match (#79).
- **`docs/roadmap.md`** — `infra-evolution-by-stage` / `docs-evolution-by-stage`
  marked shipped 1.35.0, not "Proposed" (#80).

### Changed
- Lockstep bump to **1.49.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.48.0] — 2026-09-11

Adds **`product-output-safety`** (skill #11) — governs the harm a product's own AI
outputs and automated decisions do to end-users (bias, hallucination surfaced as
fact, over-reliance, missing AI-disclosure, deceptive patterns, unsafe automation of
high-stakes actions). Distinct from `deep-code-review` (the code's security) and
`business-ops` (money/legal routing): it is the behavior of the shipped product
toward its users. The one gap-analysis item (#42) admitted as a standalone skill
under the #66 admission rule; the rest fold as lenses/references.

### Added
- **`.claude/skills/product-output-safety/`** — MAP the per-feature harm inventory,
  MEASURE it with output-harm evals / red-teaming, MANAGE it with a human-in-the-loop
  gate on high-stakes / irreversible actions (NIST AI RMF core functions, by name).
  Hard boundary: red-team + measure + recommend HITL; never certifies "safe" /
  "unbiased" / "compliant", never fabricates a harm metric, routes any legal
  disclosure duty to counsel (+ `business-ops` Lane R). Opt-in, `--with-output-safety`,
  not in `--full`. Four refusal evals (never-certifies-safe, high-stakes-action-gated,
  routes-legal-disclosure-duty, no-fabricated-harm-metric).
- Wired into every enumerated site: `ci.yml` routing, `write-checksums.sh`,
  `install.sh` (flag + `SKILLS` + overlay stamp), `recommend-overlays.py`
  (`REVIEW_ONLY_SKILLS` + advisory list), the `agentic-ceo` registry + routing,
  `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/roadmap.md`.

### Changed
- Lockstep bump to **1.48.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). The new skill starts at its own `1.0.0`.

## [1.47.0] — 2026-09-11

Executes the fabrication-refusal evals offline for the first time. Each skill's
`evals/evals.json` described a refusal but was only a fixture, never run; this adds
deterministic predicates that grade a candidate answer and a gate proving each
predicate SEPARATES a fabricated answer from a refusal — no model, no network, no
spend. First slice of the live eval harness (issue #61); the model-calling runner
is the next slice.

### Added
- **`scripts/eval_predicates.py`** — two deterministic predicates over a candidate
  answer: `no_fabricated_finding` (rejects an asserted CWE-id, or a line-numbered
  defect with vuln context, on a clean file) and `no_fabricated_numeric_fact`
  (rejects an asserted currency / percentage / multiplier figure, including worded
  forms like `USD 180` and `four point two billion`), shared by positioning and
  business-ops. A `BINDINGS` table ties each of the three fabrication-refusal evals
  to its predicate and cross-checks the real eval ids, so a renamed eval fails the
  gate rather than silently orphaning the predicate.
- **`scripts/eval-fixtures/`** — a golden `good.txt` (a refusal, must PASS) and
  `red.txt` (a fabricated answer, must FAIL) per bound eval.
- **`--selftest`** — asserts every predicate discriminates its good/red pair;
  wired into `ci.yml` (offline, no key). `test-ci-gates.sh` gains records including
  a planted-RED (a good fixture overwritten with a fabricated answer) that must
  fail closed and name the eval, plus evasion regressions locking known dodges.
  Now 52/52.

### Changed
- Lockstep bump to **1.47.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.46.0] — 2026-09-11

`--recommend` now surfaces the advisory + conductor overlays (issue #68). Previously it
could only ever name 3 of 10 skills (deep-code-review + the delivery/critic pack), so
every advisory skill was invisible exactly when the owner was choosing what to install.

### Changed
- **`scripts/recommend-overlays.py`** — prints an unconditional "advisory overlays
  available (opt-in, default off)" block listing product-discovery, growth-analytics,
  positioning, business-ops, agentic-ceo, communication-structure, and contribution with
  their `--with-*` flags and a one-line reach. It still writes nothing and never
  auto-installs; shape-based auto-push of the highest-fabrication-risk skills is a
  deliberate non-goal.
- Lockstep bump to **1.46.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.45.0] — 2026-09-11

Adds a fabrication-refusal eval to `deep-code-review` (issue #65): the crown-jewel
skill's most-cited safety property — "never invent a defect, metric, CWE, source, or
line" — now has an executable fixture.

### Added
- **`deep-code-review/evals/evals.json`** — `refuses-fabricated-finding-on-clean-file`:
  a prompt that baits CWE ids and line numbers over a clean file; the pass condition is
  no-finding / unverified, not a plausible-looking defect. Distinct from
  `planted-defect-must-be-reported`, which guards fabricating verification *status*.

### Changed
- Lockstep bump to **1.45.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No other skill changed.

## [1.44.0] — 2026-09-11

Adds a **suite-enumeration completeness gate** (`ci-gates.sh enumeration`) — the
enforce-in-code fix for the drift class behind the 1.43.0 registry bug and the
recurring recommend-overlays miss. A new skill can no longer ship green while
missing from a hand-maintained list (issue #62).

### Added
- **`ci-gates.sh enumeration <root>`** — asserts every shipped skill appears in all
  five hand-maintained lists: the `agentic-ceo` registry table (a row, not prose),
  `install.sh` (`SKILLS+=`), the `ci.yml` routing lines, the `write-checksums.sh`
  find-list, and `recommend-overlays.py`. Fail-closed; wired into `ci.yml`.
- **`test-ci-gates.sh`** — two records: the real tree is fully enumerated, and the
  gate goes RED on a planted un-enumerated skill (so it cannot pass vacuously).
  Now 47/47.

### Changed
- Lockstep bump to **1.44.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.43.0] — 2026-09-11

Fixes a routing bug in the `agentic-ceo` conductor (→ 1.1.0): its suite registry was
written at 1.37.0 and never updated as later skills shipped, so it could not route to
`growth-analytics` (1.38.0), `positioning` (1.41.0), or `business-ops` (1.42.0) — a
third of the suite was unreachable from the conductor. Found by two independent review
agents converging on the same defect.

### Fixed
- **`agentic-ceo` → 1.1.0** — the registry table and routing section now cover all
  nine non-conductor skills; new routing eval `routes-later-skill-not-inline`
  exercises dispatch to a later-shipped skill (business-ops Lane A/R). A
  suite-enumeration completeness gate to prevent recurrence is filed as a follow-up.

### Changed
- Lockstep bump to **1.43.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). All other skills unchanged.

## [1.42.0] — 2026-09-11

Adds `business-ops` (1.0.0) — the second thin advisory guide (built last) and the
last of the recommended suite skills. Two clearly separated lanes: Lane A applies
pricing / unit-economics arithmetic to the user's own numbers with the formula shown
(never a directive); Lane R routes legal / tax / securities / employment / privacy —
and fundraising — to a licensed professional (never concludes). Opt-in overlay,
default off, not in `--full`; install with `--with-business`.

### Added
- **`business-ops/`** (new skill, 1.0.0) — the asymmetric Lane A / Lane R boundary
  stated in the frontmatter description (the routing key); standing "educational
  information, not advice" disclaimer; refusal evals: `shows-formula-not-directive`,
  `routes-regulation-questions`, `fundraising-is-a-securities-matter`,
  `no-fabricated-financials`. Never fabricates a figure, statute, rate, or deadline.
  Frameworks registered by-name in `docs/standards-index.md`.
- Wired into CI routing, checksums, `recommend-overlays.py` (`REVIEW_ONLY_SKILLS`),
  `install.sh` (`--with-business`), `CONTRIBUTING.md`, `README.md`, `CLAUDE.md`.

### Changed
- Lockstep bump to **1.42.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). All other skills unchanged.

## [1.41.0] — 2026-09-11

Adds `positioning` (1.0.0) — the first of two thin advisory guides (highest
fabrication-risk, built last): value proposition, segment, differentiation, and a
message house on the USER's own inputs, produced as a hypothesis to validate with
real buyers. Opt-in overlay, default off, not in `--full`; install with
`--with-positioning`.

### Added
- **`positioning/`** (new skill, 1.0.0) — Value Proposition Canvas → positioning
  statement → message house → validate-with-real-buyers, plus the minimum-viable-brand
  rule pre-PMF. Every artifact is a hypothesis or an empty-slot template; refusal evals
  enforce it: never fabricate TAM / competitor claims / customer quotes / outcome
  numbers / trademark-domain clearance (a search is not clearance → route to a
  professional). Frameworks registered by-name in `docs/standards-index.md`.
- Wired into CI routing, checksums, `install.sh` (`--with-positioning`),
  `CONTRIBUTING.md`, `README.md`, `CLAUDE.md`.

### Changed
- Lockstep bump to **1.41.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` / `growth-analytics` (1.0.0), `product-discovery` (1.1.0),
  `communication-structure` (1.2.0), `contribution` (1.1.0) unchanged.

## [1.40.0] — 2026-09-11

Broadens `communication-structure` (→ 1.2.0) into the suite's **no-slop output
contract**: it now governs human-facing *deliverables* (reports, plans, docs,
tables), not only short messages. BLUF, one ask, core-value-only, and the full
"cut on sight" list apply to any output; the 30-second / 150-word cap stays a
message rule (a deliverable is as long as its content requires and no longer).
This is the single home the `agentic-ceo` conductor already points every skill's
output to — enforcing the owner's "clean, concise, no model-forced filler" bar
across all outputs, not just chat.

### Changed
- **`communication-structure` → 1.2.0** — scope widened from messages to messages
  *and* deliverables; new "Deliverables, not just messages" section; description
  updated.
- Lockstep bump to **1.40.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` / `growth-analytics` (1.0.0), `product-discovery` (1.1.0),
  and `contribution` (1.1.0) unchanged.

## [1.39.0] — 2026-09-11

Folds a **Non-goals** lens into `product-discovery` (→ 1.1.0) — the inverse of the
prioritization list and the scope-defense that stops a coding agent from
gold-plating. This completes the carve decision: the standalone product-strategy
skill is dropped; its distinct half (what NOT to build) lives here, its JTBD and
PMF halves already did.

### Changed
- **`product-discovery` → 1.1.0** — new *Non-goals (what you are deliberately NOT
  building)* section: recorded, stage-tied decisions revisited each stage; fed by
  the riskiest-assumption gate; used as one-line scope defense when a request
  touches a non-goal. Refusal eval `non-goals-scope-defense` (flags the collision,
  asks to reopen, never invents a non-goal the user did not choose). Description
  updated to name "what to deliberately not build".
- Lockstep bump to **1.39.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` (1.0.0), `growth-analytics` (1.0.0), `contribution`
  (1.1.0), and `communication-structure` (1.1.0) unchanged.

## [1.38.0] — 2026-09-11

Adds `growth-analytics` (1.0.0) — the standing measurement scoreboard: one
customer-value North Star, the AARRR funnel read bottom-up (retention first), an
event taxonomy that answers a named question, and stage-aware instrumentation.
Opt-in overlay, default off, not in `--full`; install with `--with-growth`.

### Added
- **`growth-analytics/`** (new skill, 1.0.0) — measure the user's own data against
  the user's own baseline; never fabricate benchmarks, metrics, or "good"
  thresholds; route real figures to the user's analytics. States the
  product-analytics vs ops-observability identifier seam (a stable pseudonymous
  per-user id for cohorts) as a pointer to `observability.md` /
  `privacy-compliance.md`, not a restatement. Refusal evals: no fabricated
  benchmarks, North-Star-not-vanity, instrument-only-what-answers-a-question,
  route-real-figures-to-analytics.
- Wired into CI routing, checksums, `install.sh` (`--with-growth`),
  `CONTRIBUTING.md`, `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.38.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` (1.0.0), `product-discovery` (1.0.0), `contribution`
  (1.1.0), and `communication-structure` (1.1.0) unchanged.

## [1.37.0] — 2026-09-11

Adds `agentic-ceo` (1.0.0) — the suite's conductor: the orchestrator that routes
across the specialist skills, sizes its own effort to the project stage, and runs
the under-pressure chaos playbook. Opt-in overlay, default off, not in `--full`;
install with `--with-ceo`.

### Added
- **`agentic-ceo/`** (new skill, 1.0.0) — a registry of the suite's skills (a map,
  not a bundle), `(stage, area) -> (skill, lens)` routing, stage/size effort-sizing
  (one agent wearing several skill-hats on small work; fan-out only for read-mostly,
  decomposable work), and the owner-under-pressure chaos playbook (capture losslessly
  -> reflect the full list -> triage to the vital few -> one next action -> hold the
  rest -> support by action, never "calm down"). Refusal evals enforce
  route-not-fan-out on small work, no dropped request under a flood, and routing the
  unknowable to the owner. Self-contained for the suite; general delivery/critique
  defer to `agentic-delivery` / `idea-critic`.
- Wired into CI routing, checksums, `install.sh` (`--with-ceo`), `CONTRIBUTING.md`,
  `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.37.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `product-discovery` (1.0.0), `contribution` (1.1.0), and
  `communication-structure` (1.1.0) unchanged.

## [1.36.0] — 2026-09-11

Adds `product-discovery` (1.0.0) — the first product-advisory specialist skill:
decide whether something is worth building, what to build first, and whether what
shipped works, by structuring evidence from real users. Opt-in overlay, default
off, not in `--full`; install with `--with-discovery`.

### Added
- **`product-discovery/`** (new skill, 1.0.0) — the riskiest-assumption gate (name
  it, run the cheapest disconfirming test before building), Mom-Test / JTBD
  discovery interview design + interpretation, fake-door / concierge experiments, a
  product-market-fit read (very-disappointed survey + retention cohorts), and ICE
  prioritization — all on the user's own inputs. The epistemic spine is enforced by
  refusal evals: it never fabricates findings, quotes, personas, market size,
  scores, or a "validated" verdict, and routes the unknowable to the owner.
- Wired into CI routing, checksums, `install.sh` (`--with-discovery`),
  `CONTRIBUTING.md`, `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.36.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `contribution` (1.1.0) and `communication-structure` (1.1.0) unchanged.

## [1.35.0] — 2026-09-11

Extends the stage-aware going-forward roadmap with two *when-to-add* reference
lenses for `deep-code-review`, complementing the existing *how-to-secure* domain
files without duplicating them.

### Added
- **`deep-code-review/references/infra-evolution-by-stage.md`** (new) — infrastructure
  and architecture are *earned, not provisioned*: per-stage build-vs-not-yet, an
  observable trigger for each step (CI, staging, containers, IaC, observability,
  orchestration, service extraction, SLOs), a floor that never relaxes (security,
  secrets, auth, backups), and six business/ops facts routed to the owner. Routed
  from the Project-stage section and domain L.
- **`deep-code-review/references/docs-evolution-by-stage.md`** (new) — which documents
  acquire normative force at which stage (one-pager → design-doc/RFC → spec),
  trigger-not-calendar, and a two-tier router+depth shape for agent legibility.
  Routed from the Project-stage section and domain O.

### Changed
- **`deep-code-review/SKILL.md`** → **1.35.0** (lockstep with `agentic-delivery`,
  `idea-critic`, and the plugin): the Project-stage section now routes the two
  stage-evolution lenses, and domain rows L and O cross-link them (when-to-add vs.
  how-to-secure). No change to `contribution` (1.1.0) or `communication-structure`
  (1.1.0).

## [1.34.0] — 2026-09-11

Hardens the `contribution` self-improvement skill so quality can only ratchet up —
it can never weaken the bar, fabricate, or self-authorize a send. Grounded in
research into secure self-hosted agents (a kernel/userspace split) and
self-modifying-agent precedents, which converge on one conclusion: keep the
human-gated, no-auto-PR, protected-core design, and gate only the irreversible step.

### Added
- **`contribution/kernel-paths.txt`** (new) — the enforceable protected-core path
  list. A drafted contribution whose changed files intersect it is a **kernel edit →
  human-authored only**, never an agent-drafted send. Meta-immutable (the list is
  itself a kernel path).
- **`contribution/evals/evals.json`** — `kernel-edit-refused` (a draft that would
  weaken the privacy gate is refused as a kernel edit) and `injection-lesson-rejected`
  (a lesson that directs the process is treated as untrusted data).

### Changed
- **`contribution/SKILL.md`** + **`references/contribution-procedure.md`** → **1.1.0**:
  a kernel-vs-userspace protected core (immutable kernel: the scrub, the
  evaluator/thresholds, merge authority, the provenance ledger, the Definition of
  Done, and the kernel path-list itself); the **second-order kernel rule** (a
  self-improvement that changes how the scrub / evaluator / generality-gate *behaves*
  is human-authored only); **evaluator independence** (graded by the unmodified
  harness); the **lesson-is-untrusted-data** injection guard; a **mosaic-leakage**
  line in the provenance block; the "human-gated send, automate everything reversible
  before it" reframe; and an explicit scope extension to **agent prompts, skills, and
  orchestration** as drafts for human review. Anima-style decay/impact triage is
  admitted only as a *local* candidate filter, never an autonomous upstream writer.
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.34.0**;
  `contribution` → **1.1.0** (independent line). `SHA256SUMS` regenerated.

## [1.33.0] — 2026-09-11

Stage-aware review + a going-forward roadmap. `deep-code-review` now calibrates
its *demands* to the project's lifecycle stage (prototype / mvp / growth / mature)
and ends a FULL review with a stage-sequenced roadmap — what to do now, what to
defer, and which skillset to adopt going forward — so effort matches the stage
instead of over-engineering a prototype or under-hardening a live product. Stage
calibrates **urgency only**; it never rewrites a defect's severity and never
downgrades a security, secret, or data-loss finding.

### Added
- **`deep-code-review/SKILL.md`** — a `STAGE` field in the first-response block and
  a compact **Project stage** section: a four-stage table (what each stage relaxes
  the *demand* on) plus three guardrails — stage is declared or evidence-named
  (never guessed; unstated defaults to the stricter reading); security / secret /
  data-loss findings never relax; stage moves urgency, not intrinsic severity
  (reusing the latent-findings rule).
- **`deep-code-review/references/report-format.md`** — a **Going-forward roadmap**
  (machine + plain-language): sequences the findings already reported by
  stage-urgency, points at `install.sh --recommend` for the skillset to adopt (no
  restating), and adds ≤ 3 evidence-grounded development moves — anything needing
  business context the repo cannot evidence is routed to *Decisions needed (owner)*,
  not invented.

### Changed
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.33.0**;
  independent skills unchanged. Definition of done (a) now requires a FULL review to
  state `STAGE` and produce the going-forward roadmap. `SHA256SUMS` regenerated.

## [1.32.0] — 2026-09-11

New review lens: **agent-readiness**. A first-class way to assess whether a repo
or product is architected, tested, gated, documented, and permissioned for
coding agents to work in it safely — the thesis-fit, evidence-grounded form of an
"AI-transformation" review. It is a lens over existing domains (C, J, K, M, N, F,
O, H), not a new domain or a new skill, and it deliberately **stops at the
technical substrate**: it never advises which product to build, how to reorganize,
or what business metric to set (that would require inputs the repo does not
contain and would violate the evidence and no-fabrication principles).

### Added
- **`deep-code-review/references/role-coverage.md`** — an **Agent-readiness
  lens**: a role-map row (leads on C J K M N F O H) and a lens section whose spine
  is the boundary between reviewable technical substrate (agent-safe scoping,
  agent-verifiability, gating, observability, legibility — all from existing
  domains) and business/strategy questions, which are routed to *Decisions needed
  (owner)*. Deliverable is the standard severity-ranked `file:line` report plus a
  short agent-readiness summary — never a strategy deck.
- **`deep-code-review/SKILL.md`** — the compact role table gains the matching
  `Agent-readiness` row so the map and its depth stay consistent.

### Fixed
- **`contribution/SKILL.md`** — corrected the procedure ordering so the mechanical
  privacy scrub runs on the **drafted files** (draft in step 3, then scrub in step
  4), not before drafting; the previous numbering could be read as scanning an
  undrafted checkout, making the "mechanical floor" vacuous. `contribution` → **1.0.1**.

### Changed
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest →
  **1.32.0**; `communication-structure` (1.1.0) unchanged; `contribution` → **1.0.1**
  (fix above). `SHA256SUMS` regenerated.

## [1.31.0] — 2026-09-11

New opt-in overlay `contribution`: prepare a privacy-safe, generalized
improvement back to the public skillset for a human to review and open as a PR.
This is the self-improvement capability the owner asked for — a skillset that
gets better from field use — built with the safety shape the design work
required rather than an autonomous push.

### Added
- **`.claude/skills/contribution/`** (new; independent line at **1.0.0**) — an
  opt-in overlay that turns a generalizable, scrubbed lesson into a drafted skill
  edit + CHANGELOG + eval + routing, runs the repo's own gates, and assembles a
  **provenance-and-risk block** a human signs before the PR. One routed reference
  (`references/contribution-procedure.md`) and three evals
  (`third-party-identifier-blocked`, `non-generalizable-imprint-locally`,
  `no-autonomous-push`). Guardrails: a hard **generality gate** (contribute only a
  defect-class or method-gap the bar lacks and that reproduces beyond one project —
  otherwise imprint locally via `deep-code-review` Phase 6); reuse of the repo's
  existing **fail-closed privacy gate** as the mechanical floor, with the human as
  the privacy authority for the semantic leaks a pattern scan cannot catch; a
  **protected core** (tests, privacy gate, and merge authority immutable to the
  agent) so a self-improvement loop cannot game its own evaluator; and **no
  autonomous push or PR** to the public repository.
- **`install.sh`** — `--with-contribution` flag (deliberately **not** part of
  `--full`, since it is the one overlay whose function is moving content toward a
  public destination); usage, header, AGENTS.md overlay stamp, and re-install
  line updated. Default install stays review-only; the new skill is off unless
  explicitly requested.

### Changed
- **`agentic-delivery/SKILL.md`** — G10 gains a one-line discovery pointer: when
  the `contribution` overlay is installed, it is the mechanism for proposing the
  generalized, stripped lesson back to the public skillset (the
  generalize-and-strip mandate itself is unchanged).
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest →
  **1.31.0**; `communication-structure` stays **1.1.0** (unchanged this release);
  `contribution` starts at **1.0.0** on its own independent line. `SHA256SUMS`
  regenerated over the five skill trees.
- **`README.md`**, **`CONTRIBUTING.md`**, **`CLAUDE.md`** — document the new
  overlay, its install flag, and its routing-gate line.

## [1.30.0] — 2026-09-11

Selective adoption from an external "studio coordination" proposal, filtered by
this repo's own bar: security-cleared, thesis-fit, non-regressive, and cited only
to sources verified this session (no new citations were needed). The proposal's
product pivot (a brand/marketing "studio OS") and its rewrite of the delivery
overlay were **declined** — the rewrite would have deleted runnable detection
instruments and added a standing-authorization carve-out that conflicts with the
confirm-before-action rule. Every existing instrument is preserved; only
additions and internal-consistency fixes land.

### Added
- **`agentic-delivery/references/host-enforcement.md`** (new) — a claimed-vs-enforced
  honesty framework: three levels (protocol / validated-artifact / host-enforced),
  each with what it *cannot* establish, a per-control capability declaration, and an
  optional adapter interface. Routed from `SKILL.md`.
- **`agentic-delivery/references/project-state.md`** (new) — a durable project-record
  contract, a resume / crash-after-effect reconciliation protocol (an interrupted
  effect with an unknown result is not presumed failed; an uncertain side effect is
  not replayed), and a non-code artifact-receipt contract that *extends*, not
  restates, the SKILL.md Output contract. Routed from `SKILL.md`.
- **`deep-code-review/references/model-tiering.md`** — a "did the tiering work?"
  cost-accounting section (model / usage / price / budget / outcome tracking; cost per
  *accepted* task with failures in the numerator), added **alongside** — not
  replacing — the existing optimization levers.
- **`idea-critic/SKILL.md`** — a "test the claim before assent" reframe (a sound plan
  may pass once a real failure hypothesis was tried and held; automatic disagreement
  is as performative as automatic agreement), an `UNVERIFIED` operational status
  *outside* the verdict enum (review-could-not-run is not a rejection), a two-recheck
  cap on `REVISE`, an "independence is a declaration" note, and an anti-rationalization
  row against a proposal that games its own evaluator.
- **`agentic-delivery/evals/evals.json`** — four scenarios pinning shipped instruments:
  crash-after-external-effect, goal-change-invalidates-work, fabricated-or-stale-receipt,
  g6-severity-and-permission.

### Changed
- **`agentic-delivery/SKILL.md`** — G6 now applies the `deep-code-review` severity
  rubric verbatim (Blocker/Critical block, High needs a named owner's acceptance,
  Medium tracked and non-blocking), resolving a contradiction where G6 blocked on
  Medium; principle 3 reworded so a check that "could not run" is `UNVERIFIED` (never a
  fake pass) and evidence is separated from permission. The same wording is aligned in
  `references/roles.md` and `references/fast-agentic-delivery.md`.
- **`communication-structure/SKILL.md`** — cut reflexive hedges but **keep material
  uncertainty** ("the log is unavailable" is evidence, not filler); the A/B decision
  template is retained.
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.30.0**;
  `communication-structure` → **1.1.0** (independent line); `SHA256SUMS` regenerated.

### Declined (from the external patch, with reason)
- The `studio-capabilities` specialist packs (brand/marketing/commercial), the "CEO
  mandate" Conductor reframe, and the install-trigger `description` rewrite — a
  different product (agency OS), not a portable code-review bar.
- A Human-gates "standing authorization — do not ask again" carve-out — conflicts with
  the confirm-before-destructive/irreversible non-negotiable.
- The rewrite's deletion of runnable instruments (behavioural drift tell, fan-out tiers
  + the Cemri failure-mode mapping, the RAM/swap headroom probe, the seven cost levers,
  the A/B ask template) — all kept.
- 19 new `standards-index` rows and the promotion of NIST SSDF / AI RMF / SLSA from
  by-name to verified — not verified by direct fetch this session.
- The size-enforcement CI cap and the idea-critic validator/test-suite tightening —
  coupled to the rejected rewrite or to coordinated fixture changes; deferred to a
  separate, self-contained change rather than risk the gate.

## [1.29.0] — 2026-09-10

Tier 2–3 of the same prime-agent-informed batch: supply-chain and CI/CD
detection instruments, a dependency release-age cooldown control, six eval
fixtures, and two repo-hygiene items. Additive; the method and the default
(review-only) install are unchanged. Two Tier-3 items were found **already
implemented** during the work and are recorded, not re-added (see Note).

### Added
- **`deep-code-review/references/security-appsec.md`** — A03 gains CI/CD
  trigger-and-token hygiene (`pull_request_target` untrusted checkout,
  `${{ github.event.* }}` script injection, least-privilege
  `GITHUB_TOKEN` / `permissions`) and a verification-vs-authenticity instrument:
  a same-origin checksum is integrity, not authenticity, and does not neutralize
  the trust-on-first-use risk of a `curl | sh` install; severity keys on
  reachability. Cited to GitHub's Security-hardening guide.
- **`deep-code-review/references/security-agent-skills.md`** — AST02 gains the
  integrity-vs-authenticity grade, downloaded-manifest path-traversal
  validation, and a pointer that CI workflow files are executable config
  reviewed under A03; AST03 gains installer over-privilege beyond identity files
  (shell-rc append, global `npm i -g`, `PATH` export).
- **`deep-code-review/references/dependency-currency-and-upgrades.md`** — a
  release-age cooldown control (refuse to resolve a version until it has been
  public N days; Renovate `minimumReleaseAge`, security advisories exempt) plus
  a matching red flag. Cited to Renovate's docs.
- **`deep-code-review/evals/evals.json`** — six fixtures pinning the new
  instruments (interpreter-is-the-exec-sink, silent safety-param drop,
  process-group-is-not-isolation, installer over-privilege, cost-vs-token cap,
  inconsistent untrusted-content spotlighting).
- **`.gitattributes`** — normalize text to LF and keep shipped `*.sh` LF so the
  installer runs identically on every checkout.
- **`.github/workflows/ci.yml`** — the `name:`-matches-directory check now runs
  on every shipped skill, not only `deep-code-review`.

### Changed
- The three lockstep skill `VERSION` files, their `SKILL.md` stamps, and the
  plugin manifest follow **1.29.0**; `SHA256SUMS` regenerated.
  `communication-structure` remains at 1.0.0.

### Note
- "Run `install.sh` end-to-end in CI" and "sort `SHA256SUMS` entries" were found
  **already implemented** and were not re-added: `scripts/test-ci-gates.sh`
  already drives the real installer (`ci-gates.sh install --src .`) across modes
  with an idempotent-second-run assertion, and `scripts/write-checksums.sh`
  already sorts its entries.

## [1.28.0] — 2026-09-10

Five agent/LLM review-instrument sharpenings for domain C, found by routing the
skill's own `agent / LLM` archetype path against a production agent runtime and
recording where a reference stated a rule but handed the reviewer nothing to
run. Additive; no change to the method, scope modes, or the default
(review-only) install.

### Added
- **`deep-code-review/references/security-ai-agents.md`** — the "untrusted
  content is data" principle gains a detection step (enumerate every sink where
  non-prompt content enters a prompt; require a delimiter + a data-guard at
  each; **inconsistent** spotlighting is itself the finding) and a reframe for
  code-interpreter agents, where "model output reaches `exec`" is the product —
  so the controls to review are the isolation boundary and the default
  confirmation gate, not the exec call. Tool-gating now locates the dispatch
  chokepoint and separates a shipped default from an opt-in `examples/` demo;
  a human-confirmation gate must fail **closed** when no interactive UI exists.
  Spend governance gains the **cost ≠ tokens** and **before ≠ after** (pre-call
  vs post-hoc reconciliation) tests plus a `while (true)` loop-bound check.
  Matching `🚩 grep` keys throughout.
- **`deep-code-review/references/security-agent-skills.md`** — AST06 gains an
  isolation-grading instrument: grep the exec runtime for `subprocess` /
  `Popen` / `spawn`, check each spawn for a real boundary (namespaces, seccomp,
  netns, uid-drop, chroot, a container), and treat `start_new_session` /
  process groups / Job-Objects as lifecycle control, not a security boundary; an
  opt-in `examples/` sandbox or gate that is not loaded by default is not an
  enforced control. Matching `🚩 grep` keys.

### Changed
- The three lockstep skill `VERSION` files, their `SKILL.md` stamps, and the
  plugin manifest follow **1.28.0**; `SHA256SUMS` regenerated for the changed
  skill trees. (`communication-structure` remains at 1.0.0.)

## [1.27.0] — 2026-09-10

Two field lessons for the delivery overlay and the product-UX review half, each
a completeness fix to an existing rule rather than a new one. No change to the
review method or the default (review-only) install.

### Added
- **`agentic-delivery/SKILL.md`** — the Conductor operating rhythm gains a
  *drift-detection and recovery* step: the event-driven "does not do the lane's
  work itself" rule stated **behaviourally** (a run of consecutive
  query/build/edit/mutate turns is the tell), with a stop → package → dispatch →
  resume recovery and one named exception (work only the Conductor's own session
  can perform, done minimally and handed straight back). Applies the existing
  event-driven discipline to *action*, not only attention.
- **`agentic-delivery/SKILL.md`** — Gate epistemology principle 11:
  "visible/done" is measured on the owner's own surface, never a proxy (an
  integrated SHA, a green branch build, a passing test, an insert/grep count);
  keeps wired/defined/rendered distinct from has-a-real-value. Ties to
  principle 3's `UNVERIFIED` and the G9 production-verify gate.
- **`deep-code-review/references/product-ux-quality.md`** — a redesign-trigger
  section complementing "not a licence to redesign": the owner's *repeated*
  rejection (2+ times) of the same element is a structural signal to stop tuning,
  name the flaw, research two or three comparable products, and surface concrete
  options for the owner to choose (show, don't tell). Reconciled with principle 5
  and grounded in principle 9.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin manifest
  follow **1.27.0**.

## [1.26.0] — 2026-09-09

New reference `skill-authoring-and-size.md` (domain H): a portable rule for
keeping agent skills lean as they accrete lessons — a thin always-loaded
`SKILL.md` core + a routed index, depth in on-demand `references/`, two budgets
(body tokens on invocation, `description` chars always-loaded, ≤1024 by spec), a
reasoned allowlist (allowed-not-required), and a size ratchet that FAILS on bloat
with a self-test that proves it fires. Routed from the domain map (H) and a
"skills as targets" pointer. CI `--max-bytes` stays 100000 (still a warning);
tightening to 24000 and making it FAIL need a follow-up with `workflow` scope.
No behaviour change to the review method.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin
  manifest follow **1.26.0**.

## [1.25.0] — 2026-09-09

Concurrency, scheduling, and merge-cadence cut for `agentic-delivery`. Default
install stays review-only.

### Added
- **`agentic-delivery/references/fast-agentic-delivery.md`**: five field-tested
  refinements — a corrected resource-gate signal (free RAM + swap trend, not
  `load1` alone, which conflates disk I/O with CPU contention), CI-offload as
  the actual concurrency unlock (lane weight over lane count), sweeping the
  whole ready queue on every Conductor trigger, a fleet-wide external-advisory
  gate-epistemology case, and reconciling an independent-PR-queue merge
  cascade with the existing union-proof-before-a-train rule. Five sources
  fetched and cited (Kanban WIP limits, Google small-CLs, blast radius,
  GitLab merge trains, Linux load-average mechanics). Routed from three spots
  in `SKILL.md` (environment probe, Conductor operating rhythm, gate
  epistemology).

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin
  manifest follow **1.25.0**.

## [1.24.0] — 2026-09-08

Cost-governance leftover from colliding PR #13, restamped onto
current main so it does not reuse shipped 1.22.0 / 1.23.0.

### Added
- **`model-tiering.md`**: default-and-ceiling callout — cheapest tier
  that clears its own gate; state a reason before exceeding frontier
  except lead-verify / adversarial-design.
- **`agentic-delivery` environment probe**: composite resource
  predicate (free RAM >15% AND load1 < cores × 1.3 AND CPU idle >25%,
  plus macOS swap check). Throttle when any one trips.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.24.0**.

## [1.23.0] — 2026-09-08

Discipline and compatibility cut. Mechanisms, not packs. Default
install stays review-only.

### Added
- Anti-rationalization (excuse → rebuttal) tables in `idea-critic`
  and `agentic-delivery` G4/G5.
- Headed-browser evidence as a **required** G5 / domain P receipt
  when a rendered page can change. Unit tests alone are not a UI gate.
- Spec Kit constitution *compat*: if `.specify/` or `constitution.md`
  exists, review against it. Do not install Spec Kit.
  `--recommend` prints that notice.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.23.0**.

## [1.22.0] — 2026-09-08

Distribution and fixture-eval cut. Default install stays review-only.
Does not claim OpenSSF Model Signing.

### Added
- `evals/evals.json` on each of the three skills (fixture contract:
  planted defect must be reported; `--recommend` must not write;
  owner-request cannot HOLD). Wired into `scripts/test-ci-gates.sh`.
- `SHA256SUMS` of the three skill trees and `scripts/write-checksums.sh`.
  CI compares the committed file to a fresh regeneration.
- `SECURITY.md` — pin by release tag, refuse unsigned HEAD, honest
  signing gap.

### Changed
- README documents `git clone --branch vX.Y.Z` and
  `npx skills add remigiusz-antczak/deep-code-review#vX.Y.Z` next to
  `install.sh`, with an AST07 warning against floating HEAD.
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.22.0**.

## [1.21.0] — 2026-09-08

Orchestration lessons unique to the leftover PR #11 branch, restamped
onto current main so they do not collide with shipped 1.20.0. Additive
on 1.20.0 — the review bar's six phases, domains A–S, the gate table,
and the report shape are unchanged. Two items checked against 1.19.0
were already present (robust shell list-membership; worktree-per-lane
preflight) and are not duplicated.

### Added
- **`agentic-delivery/SKILL.md`**: "Environment probe (before you size
  anything)" (probe RAM/CPU/disk and usable tool/connector auth; decide
  heavy-lane count, model tier, and local-vs-CI from the probe, not
  habit); a general-lane context-inheriting-fork rule (a fork carries
  every prior instruction, not only the newest one — fresh unit for
  narrow work, or an explicit prohibition plus a check of what the unit
  actually called); a lane's own scope ends at its own green PR, not at
  the merge; Gate epistemology principle 9 (closing/deleting shared
  state needs evidence, not presumption); G7-vs-G8 clarification (a
  work item is done at integration; release/deploy is later and
  owner-gated); principle 3 gains a concrete triage step (identify the
  failing job **and step**, rerun a suspected flake, before reverting).
- **`deep-code-review/references/parallel-audit.md`** §2: tree-diff is
  blind outside the tree (issue/comment/message); verify a prompt-level
  strip actually held from the unit's tool calls, not its summary.
- **`deep-code-review/references/branch-and-merge-hygiene.md`** §1:
  truncated forge listing — `gh issue list`/`gh pr list` default page
  is 30; count with `--limit` or paginate.
- **`deep-code-review/references/product-ux-quality.md`**: reviewable
  who/what/when change history behind any decision-of-record edit, and
  agent/model-authored values stamped as such at write time.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the
  plugin manifest follow **1.21.0**.
- README missing-space nit after the personal-install sentence.

## [1.20.0] — 2026-09-08

Closes the remaining 1.19.0 self-review backlog after 1.19.1 landed
the byte-exact VERSION gate (F2/F8).

Domain C now walks OWASP LLM Top 10 **2026** titles quoted from
`OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf` (fetched 2026-09-08). 2025 IDs
remain only as a compatibility map. New reference
`security-agent-skills.md` walks OWASP Agentic Skills Top 10
AST01–AST10 against both skill-consuming targets and this repo's
`install.sh` / VERSION / SHA stamp.

Repo dogfood that is settings-not-code (F3/F6/F7) is applied on the
GitHub repo itself: `delete_branch_on_merge`, secret scanning + push
protection, Dependabot security updates, tag `v1.19.1`. This commit
adds Dependabot version updates for GitHub Actions, an issue-template
`config.yml` so GitHub indexes the templates (F5), a PR-template gate
list that matches CONTRIBUTING (F10), and the idea-critic description
trigger `Use when` (F9). Required-review branch protection is still
off so a same-owner merge is not trapped.

### Added
- `.claude/skills/deep-code-review/references/security-agent-skills.md`
  (AST01–AST10), routed from `SKILL.md`.
- `.github/dependabot.yml` for `github-actions`.
- `.github/ISSUE_TEMPLATE/config.yml`.

### Changed
- Domain C / `security-ai-agents.md` walks LLM01–LLM10:**2026**.
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.20.0**.
- PR template mirrors CONTRIBUTING's pre-PR gate block.
- idea-critic description starts `Use when`.

## [1.19.1] — 2026-09-08

Patch on 1.19.0. The VERSION provenance gate no longer strips
whitespace before matching, and it no longer accepts a matching heading
anywhere in CHANGELOG.md. VERSION must be byte-exact ASCII core SemVer
(`MAJOR.MINOR.PATCH`, no leading zeros in a multi-digit part) with at
most one optional terminal LF. The first `## ` heading in CHANGELOG.md
must announce that version.

Closes the fail-open that accepted a planted `  1.19.0  ` file, and the
stale-ordering hole where an older first heading still passed if a later
heading matched. Ports the unpushed local `d104e72` contract onto main
and adds the planted whitespace / NUL / first-heading cases to
`scripts/test-ci-gates.sh`.

### Changed
- `scripts/ci-gates.sh` `version`: hex-validate raw VERSION bytes, then
  require the first CHANGELOG release heading to announce it.
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the
  plugin manifest follow **1.19.1**.

### Tests
- Eight new version-gate cases: leading-zero major, NUL, embedded
  whitespace, multiline, leading whitespace, stale first heading
  (reject); exact `1.13.0` with trailing LF, and no trailing LF (accept).

## [1.19.0] — 2026-09-08

A hardening pass on top of 1.18.0's software-house roles, from four research
streams: closing this skill's own spend-cap gap, filling the domain-K release-
engineering gap and the one-line G10 retrospective, hardening `idea-critic`
past a same-brain "independent" verdict, and six portable lessons drawn from
one AI-agent-maintained project's own operational history (scrubbed of every
project-specific detail — generic principles and fictional examples only).
Additive on 1.18.0 — the review bar's six phases, domains A–S, gate table, and
report shape are unchanged. Four candidate detectors from that lessons pass
(duplicated-UI-concept drift, write-only inputs, render-trace-before-edit,
UI-changing diffs needing visual proof) were found **already shipped** in
1.18.0's `product-ux-quality.md` and `parallel-audit.md` §5 during
verification against this branch — not re-added; see the PR body for the full
staleness note. Grounded in the sources logged in `docs/standards-index.md`'s
three new 2026-09-08 sections.

### Added
- **`references/model-tiering.md`** (domain E): three vendor-neutral model
  tiers, the cost/quality levers in the order the evidence favors reaching for
  them (effort tuning, prompt caching, batching, escalate-on-failure, budgets,
  bounded advisor consults, model swap last), two negative results (don't fan
  out on a single dependent chain; don't over-consult an advisor), and the
  mapping onto this skill's own fan-out tiers and delivery hats.
- **`references/release-engineering.md`** (domain K, the release half
  `dependency-currency-and-upgrades.md` never covered): feature-flag
  category/lifetime checklist, canary/blue-green claims checked against actual
  router/traffic-split config, DORA-or-`UNMEASURED`. Paired with a **Release**
  depth section in `agentic-delivery/references/roles.md`.
- **`agentic-delivery/references/retrospective.md`** + **`template-
  postmortem.md`** (routed from G10): blameless principle, mandatory-trigger
  criteria (not every bug fix), action-item-closure gate, repeat-root-cause
  check against prior postmortems.
- **`agentic-delivery/references/template-adr.md`** (routed from G3): Nygard's
  five-part shape + MADR's optional sections, giving G3's existing "ADRs /
  contracts" requirement an actual shape.
- **"Conductor operating rhythm"** subsection in `agentic-delivery/SKILL.md`:
  event-driven attention (not polled), fan-out sized to decomposition (not
  concurrency), pilot before full width, escalate-a-lane-don't-just-retry-it,
  and an empirical failure-taxonomy callout (Cemri et al., MAST) mapping onto
  the existing gate shape.
- **`idea-critic`**: verdict schema gains `steelman` (attack the strongest
  defensible reading of the claim) and `strongest_attack_survived` (the
  sharpest objection actually tried, and why it failed — required and
  non-generic on `PASS_TO_USER`), both enforced by `validate_verdict.py`; a
  premortem clause on the `kill-criteria` hat; Independence now tiers
  decorrelation strength (a different model family is stronger than a
  different context alone); a new "false-closure REVISE" pitfall.
- Six portable-lesson closes verified absent from this branch before being
  added: `role-coverage.md` (success-metric-to-emitted-event loop closure +
  the missing SRE-workbook burn-rate citation), `testing-and-evals.md`
  (stated Test-Pyramid-vs-Testing-Trophy philosophy required), `frontend-
  a11y.md` (URL-backed drawer/filter state), `infra-iac-containers.md` (a
  green health check is not proof of an out-of-band post-deploy data
  dependency), `docs-and-dx.md` (dated status/handoff doc proliferation),
  `concurrency-shared-state.md` (worktree-per-lane + spawn-time duplicate-work
  preflight).
- `branch-and-merge-hygiene.md`: stacked-PR-safe branch deletion, generated-
  file merge-conflict resolution (regenerate, never hand-splice), a new
  "Merge trains" subsection (verify the union once, merge members
  individually, sequence a gate-adding PR last), a combined safety-rail bullet
  on gating an irreversible command on a preflight's documented pass condition
  paired with a robust-shell-list-membership lesson (`for x in $LIST` on an
  unquoted variable silently stops excluding anything under a non-word-
  splitting shell; use a literal `case` or `grep -qxF` instead), and a §8
  spike/prototype branch-naming convention. A matching grep-flag row in
  `language-stack-redflags.md`'s Shell/Bash section.
- Three operating-discipline sentences with no code detector: principle 5 (a
  previously and explicitly made design choice is treated as a stated style
  guide — propose against it, never silently revert it); the Confirm bullet
  (a tentative/question-phrased message is a request for assessment, not
  authorization); `report-format.md`'s mechanism-unproven-fix language now
  extends to status reporting generally (running ≠ fixed).
- `docs/standards-index.md`: three new 2026-09-08 sections logging every
  source above with fetch dates and, per the file's own convention, what each
  fetch did **not** confirm (DORA's single-source caveat, the MAST paper's
  14-mode taxonomy not independently enumerated, Panickssery et al. tested on
  GPT-4/Llama 2 not Claude, and others).

### Changed
- `parallel-audit.md`: the shared fan-out context packet is flagged cacheable;
  a don't-start threshold complements the existing stop rule (don't fan out on
  one dependent chain or a single-context target); the Tier-1→Tier-2 sweep now
  tiers by model capability, not only effort; a new addendum distinguishes a
  concurrency-capacity flake from a genuine defect.
- `agentic-delivery/SKILL.md` G2 now requires a per-lane token/dollar budget
  before G4 starts (no budget = blocked, not unlimited) — closes a
  self-referential gap between this skill's own LLM10/`spend-cap` invariants
  (enforced on every *target*) and its own gate table (which enforced neither
  on itself). G0 now names an explicit appetite (a time-box, not an estimate).
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the plugin
  manifest follow **1.19.0**.

## [1.18.0] — 2026-09-08

The delivery overlay becomes a **software-house in a repo**: the full role roster
as hats (not standing bots), a first-class **Product Analyst** role, a hardened
adversary, the orchestration discipline that keeps parallel lanes from thrashing,
and the product-UX **interaction-completeness** bar. Additive on 1.17.0 — the six
review phases, domains **A–S**, the severity rubric, and the report shape are
unchanged; the review side gains one product-UX section and one fan-out
discriminator, the delivery overlay gains one routed reference, and the CI routing
gate now also covers the overlays. Grounded in five directly-fetched sources
(Anthropic *Building Effective AI Agents*; Claude Code Subagents; Anthropic Agent
Skills; MetaGPT; ChatDev) logged in `docs/standards-index.md`.

### Added
- **`agentic-delivery/references/roles.md`** (routed from that skill's `SKILL.md`):
  the software-house role roster as **hats, not headcount** — Conductor, Product
  Analyst, Architect, Implementer, Evil Twin, QA, Security, UX & Design, Release,
  Docs — each mapped to when it fires, the gate it owns (G0–G10), and the
  `deep-code-review` review lens it corresponds to. Depth only for the three roles
  the review-side `role-coverage.md` does **not** hold (Product Analyst,
  Evil-Twin-as-hat, Implementer); one-line pointers for the rest, to avoid
  restating the review overlay. Includes the two-tier **gates a software-house
  repo runs** table (commit-time: privacy/format/lint/type/unit+count; CI:
  build+E2E-at-SHA / verify-visible-UX / ux-evidence / dependency) with the repo's
  own gate epistemology (tell can't-check from found-a-problem; fail open on the
  former; provable-red on a planted defect; never stricter than the standard).
- **Product Analyst** hat in `agentic-delivery` (Operating model + G0/G1): turns a
  real signal into a testable spec, enforces **interaction-completeness**,
  benchmarks solved elements against **named** comparable products, and maintains
  a **feedback-coverage map** (each item → scoped → verified / deferred) — the
  product analogue of the review's coverage ledger.
- **Interaction-completeness + unified-UX** section in
  `references/product-ux-quality.md` (domain P): one **shared component per
  concept** (reuse/extend, never reimplement per page; a fix lands in the shared
  component, not one caller), **no write-only inputs** (read-back required),
  **WYSIWYG** (store markup, render it — never show raw `**`/`<u>` tokens), and
  fix-the-surface-that-renders — with new grep 🚩 rows and two pre-ship checklist
  items.
- **Render-surface discriminator** in `references/parallel-audit.md` §5: a grep
  match is a *candidate*, not a live site — trace route → component (UI) or the
  call graph (code path) before a finding or a fix names a `file:line` as the live
  surface; a fix aimed at a grep hit the target never runs is wasted work that
  leaves the real surface broken.
- `docs/standards-index.md`: a **2026-09-08** verified-by-direct-fetch section for
  the five sources above, each row stating what the fetch did and did **not**
  confirm (the arXiv abstracts do not enumerate specific role titles verbatim).

### Changed
- **`idea-critic`** hardened into a "proper evil twin": a **default-to-dissent**
  prime directive (with the reflexive-praise trigger), **attack before
  substantive work** (not after), and **verify-your-own-objection — the critic is
  a lead, not an oracle** (check a pushback's premise against current verified
  state; a critic that blocks good work with a stale fact is a false negative).
- **`agentic-delivery` orchestration discipline**: *Worktrees and occupancy* now
  states that a subagent/fork mechanism does **not** necessarily isolate the tree
  (assume shared until proven; branch/index/deps are per-tree), requires cleaning
  the base before launching and a **preflight** (running workers, `git worktree
  list`, open PRs) before spawning any lane; *Failure* adds **a running lane is
  not a finished one** (report what runs; report done only when verified).
- **`recommend-overlays.py`** now inspects the target for the quality gates it
  already has (CI, lint, format, tests, pre-commit, privacy — filename-level,
  reporting "not detected", never "absent") and frames the pack as the
  software-house roles + the gates the imprint would add. It also detects a
  **live custom delivery pack**: a skill under a real host skill root
  (`.claude/skills/` and peers — not a `docs/` archive) whose path, frontmatter
  `name`, or a small `SKILL.md` prefix names a delivery OS. Named packs already
  counted; a private factory, a software-house-pattern skill, or an
  already-installed `agentic-delivery` overlay previously still received
  `--with-delivery` / `--full`. Detection is review-negative (`deep-code-review`
  and `idea-critic` never count), skips non-regular files and `SKILL.md`
  symlinks (a FIFO would hang `open()`; a symlink can point outside the
  target), and stays bounded — one level under each known skill root, reading
  only a prefix, failing closed on any single unreadable file.
- **CI + CONTRIBUTING**: the `routing` gate runs on **all three** skill dirs
  (`deep-code-review`, `agentic-delivery`, `idea-critic`), so a new overlay
  reference cannot ship unrouted — the repo dogfoods its own "documented but
  unenforced is a finding" rule.
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the plugin
  manifest follow **1.18.0**. README gains a *software-house overlay* section and
  refreshed counts.

## [1.17.0] — 2026-09-08

Dogfood of 1.15.0/1.16.0 against two external product repositories plus the
Agent Skills spec. Three defects in the bar itself, not in those products: `--recommend` treated archived Superpowers
notes as a live delivery OS; kit-leftover `AGENTS.md` was not a named DX
defect; delivery never required a running local stack. Anti-slop is now an
explicit Phase-4 filter so a review of a well-gated product does not emit
community-health noise.

### Added
- **Anti-slop** in `references/method.md` Phase 4: drop findings that would
  not change a merge or a ship. Kit leftover (`AGENTS.md` still describing
  scaffold `app/` while the product lives in `apps/` / `packages/`) is **one**
  DX finding, not a docs wall.
- **Kit leftover vs product tree** and **local environment is DX** in
  `references/docs-and-dx.md`.
- **Local environment (own it)** in `agentic-delivery`: discover the project's
  one-command / compose / devcontainer, bring it up, verify against the
  running process (`verify:served` when present), tear down. G5 is
  `UNVERIFIED` if the stack never started.
- `idea-critic` pitfall: `HOLD` slop recs (extra docs, restyle, second
  delivery OS) unless a named defect requires them.

### Changed
- `--recommend` only treats a delivery pack as live when a skill path exists
  (`.claude/skills/superpowers/SKILL.md` and peers) or a marker directory sits
  outside `docs/` / `archive` / `history` / `code-review` / `notes`. Historical
  Superpowers plans under `docs/` no longer suppress `agentic-delivery`.
- Overlay `VERSION` files and plugin manifest follow 1.17.0.

## [1.16.0] — 2026-09-08

A **product-UX quality** reference under domain **P** — the *design half* of a
frontend review (whether a UI feels **at-home**: conventional, self-evident,
correct in every data state, cleanly encoded), complementing the a11y-correctness
half `frontend-a11y.md` already owns. Additive on 1.15.0: the six phases, domains
**A–S**, the severity rubric, and the report shape are unchanged; domain P gains
a second reference (routed by a "read it when…" trigger) and the web archetype
must-load set. No new URL, version, or date is cited — the design half grounds
in WCAG 2.2 (already tracked), Nielsen's usability heuristics (named, not
URL-cited), and the public precedent of top products.

### Added
- **`references/product-ux-quality.md`** (routed from domain P): the "at-home"
  design bar — **every data state ruled on** (empty/loading/error/partial/
  overflow), **one-visual-channel-per-dimension** encoding hygiene,
  **never-colour-alone** (the greyscale test), the **metric/KPI delta standard**
  (caret + magnitude, colour by *sentiment* not direction), **self-evident-over-
  explained** (progressive disclosure; legends collapsed, glyph-grid not prose),
  **drawers-overlay + no-dead-controls**, and a **named** top-product precedent
  per solved element. Opens with the reconciliation rule (read first): matching a
  convention is a review **observation** surfaced under "Decisions needed (owner)"
  with the minimal-visual-impact fix — **never a licence to redesign**. Closes
  with a **Phase-6 UX-evidence gate** that fails open on could-not-check.

### Changed
- `SKILL.md` domain **P** routes both `frontend-a11y.md` and
  `product-ux-quality.md`. Web archetype must-load includes the design half.
- README P-row names the design half; Nielsen's usability heuristics added to
  the by-name standards list.

## [1.15.0] — 2026-09-08

The review bar stays the default product. Optional overlays inject a
public-safe **gated delivery** pattern and a **pre-owner idea attack** into
a target repo. Spec compliance (Agent Skills description ≤1024 characters,
`SKILL.md` under 500 lines) unblocks every later install.

### Added
- **`agentic-delivery`** (opt-in) — G0–G10 gated delivery: smallest-sufficient
  hats, independent QA/security, one writer per worktree, exact-SHA receipts,
  human approval on push/merge/deploy. Names `deep-code-review` at G1/G6/G7.
  Public-safe distillation; no operator preferences, no private intake, no
  runtime names.
- **`idea-critic`** (opt-in) — three hats (skeptic, better-way, kill-criteria);
  verdict `HOLD | REVISE | PASS_TO_USER`; `owner-request` cannot HOLD.
  `scripts/validate_verdict.py` fail-closes on a missing key, an illegal
  HOLD, or a list-shaped `user_question`.
- **`./install.sh --recommend <project>`** — inspects the target and prints a
  pack. The agent may recommend `--full`; the owner decides. Another delivery
  pack already in the tree is a reason **not** to also install
  `agentic-delivery`.
- Install flags: `--with-delivery`, `--with-critic`, `--full`,
  `--with-extra-hosts` (Gemini, OpenCode, Copilot `.github/skills/`, Windsurf,
  Hermes, Kiro).
- `.claude-plugin/plugin.json` so `/plugin marketplace add` works.
- Community health: `CODE_OF_CONDUCT.md`, issue templates, PR template.
- `references/method.md`, `domain-checklists.md`, `report-format.md` — method
  depth moved out of `SKILL.md` (progressive disclosure).

### Changed
- Default `./install.sh <project>` remains **review-only**. Delivery is never
  the default.
- `deep-code-review` `description` rewritten to ≤1024 characters, when-to-use
  in the first 57 characters.
- `SKILL.md` is the map (under 500 lines). Checklists, phase procedures, and
  report templates load on demand.
- `CONTRIBUTING.md` points at `scripts/test-ci-gates.sh` + `ci-gates.sh`.
- Chat voice is **not** vendored. Compressed assistant prose, if wanted, is
  a pointer to the public caveman skill repository. Persisted artifacts stay
  normal English.

### Not in this release
- No private operating-registry content, live values, or third-party
  identifiers.
- No default-on full pack.
- No caveman files copied into this tree.

## [1.13.0] — 2026-09-02

A role-aware **software-house overlay** over the existing method, plus the repo's
own gates re-homed into one fail-closed helper proven by a self-test harness.
Additive and smallest-sufficient — the six phases, domains **A–S**, the severity
rubric, and the report shape are unchanged; the overlay only orders and assigns
domains through a delivery-role or security-team lens, it never adds or drops one.

### Added
- **Role & team overlay** in `SKILL.md` + `references/role-coverage.md` (routed
  by path with a "read this when…" trigger): per-role leads-on domains for the
  nine delivery roles, driven through the same A–S method. Adds the lenses this
  file does not hold — **architecture quality** (seams, dependency direction,
  SPOFs, drift from the stated design), **lightweight product planning**
  (problem→acceptance, smallest slice, success metric), **SLI/SLO with error
  budget & burn-rate**, and **release-owner sign-off**.
- **Security-team colour model** (re-packages the same evidence by stance — no new
  rules; Red still needs `file:line`, Blue still fails closed): **Red** adversarial
  pass, **Blue** detection/fail-closed, **Purple** red→blue gate, **Yellow** build,
  **Green** (Yellow+Blue), **Orange** (Yellow+Red), **White** scope/ROE/owner
  decisions/sign-off.
- **Black Team — the agent boundary is absolute.** A physical / human-operations
  lens (intrusion, impersonation, social engineering, surveillance, badge/lock
  bypass, device placement) where an agent may **only plan, tabletop, and analyse
  owner-supplied evidence** — never perform or operationally direct any such action,
  and never test a real person or site. Real assessments are **human-led under
  written owner authorization and legal rules of engagement (ROE)**; a request that
  crosses the line has its operational part refused and its planning part kept.
- `scripts/ci-gates.sh` — one **fail-closed** production helper for the repo's
  documented gates (`privacy`, `routing`, `version`, `install`): no `|| true`, no
  always-success fallback, no pipeline that swallows the real exit status. Privacy
  reports matching **file names only, never content**, and fails closed on a
  missing, empty/comment-only, or malformed-ERE banlist while honouring an optional
  sibling `.banlist.local.txt`. Routing matches basenames **literally** (fixed-
  string) and flags dangling routes, with a non-failing size WARN.
- `scripts/test-ci-gates.sh` — a **16-case RED/GREEN self-test harness** pinning
  that helper's contract with real exit codes preserved: privacy (reject empty and
  all-comment banlists, detect a planted secret, reject an invalid ERE without
  disclosing banlist content, load the sibling local override), routing (reject
  unrouted, reject a regex-meta basename match, WARN on an oversized SKILL.md),
  version (reject malformed VERSION and a missing CHANGELOG heading), and install
  (overwrite a placeholder with the real vendored docs; **Claude**, **minimal**,
  **Codex**, and **full** agent-agnostic default modes; **Codex/full** assert the
  managed AGENTS.md block sentinels — `deep-code-review:begin`, `Installed:`,
  `Agent-agnostic` — and **full** re-installs to prove exactly one idempotent
  managed block, never a duplicate; collision-free backups on rapid repeated
  installs).

### Changed
- CI (`.github/workflows/ci.yml`) now runs the self-tests and then enforces the
  documented gates through that **same single helper** — one authoritative
  implementation, no inline copies, so the enforced check and its tests never
  diverge.
- `install.sh` backups are **portable and collision-free** — a seconds-resolution
  timestamp plus an existence-checked numeric suffix (avoiding `date +%N`, which is
  unsupported on BSD/macOS `date`), landing under `.../skill-backups/`, never inside
  `skills/`.
- **Confidentiality scoped first- vs third-party** (principle 11): a project's
  intended-public identity (published maintainer/author, public repo URL) is not a
  leak, while drift beyond that stated-public surface is the finding; softened the
  prose's unsupported scanner/breach claims to what the gate actually proves. The
  project's own `CLAUDE.md` confidentiality rule is aligned to the same scoping so
  the repo's governance and the skill it ships no longer disagree on first-party
  identity (the repo dogfoods its own gate: `.banlist.txt` bans secrets + generic
  patterns, real identifiers live in gitignored `.banlist.local.txt`).
- README reference-file count → **20**.

## [1.12.0] — 2026-09-01

Throughput-and-affirmation harvest from a FULL run against a large, hardened
production Node codebase: make the fan-out cheap on large targets, make the verify
step catch intended-behavior false positives, and make the review's value legible
on a target that yields few or no defects. Additive — phases, domains A–S, and the
report shape are unchanged; the report gains one co-equal affirmative section.

### Added
- `parallel-audit.md`: **two-tier sweep** — a cheap Tier-1 candidate enumeration
  before the high-effort Tier-2 confirm that runs only on survivors, so
  agent-minutes track candidate count, not domain size; plus small
  one-invariant units (a few hundred lines of owned surface) so no single finder
  stalls the pipeline under a small concurrency cap.
- **Verify against the tests, not only the source** (`parallel-audit.md` §4 +
  SKILL Phase 4): before `CONFIRMED`, read the tests that exercise the finding — a
  fix that contradicts a passing assertion is `REFUTED` as intended behavior — and,
  for a change to security/cost/concurrency logic, apply the fix in a throwaway
  worktree and run the suite. Re-reading the source the finder read cannot catch an
  intended-behavior false positive; only the tests encode intent.
- **"Invariants verified to hold"** as a first-class, co-equal report section
  (Phase 5 + report format + rules + definition of done) fed by a new
  `checked_sound` affirmative return in the fan-out contract — the primary
  deliverable on a hardened target, grounded `file:line`-or-drop like any finding.
- **Runtime-proven-gate lens** in domains B (home), C (tool-authz proven live), and
  F (subsystem proven to execute): is the gate measured at runtime (a
  self-proof/health check) and **fail-closed when the proof is absent**, or merely
  present in code? An unproven gate that reads as safe is itself the finding.
- **Failure direction as a severity axis** (rubric + Phase 4): fail-open (bypass /
  over-grant / leak) scales with blast radius; fail-closed (self-DoS / over-deny /
  conservative accounting) caps **Low** unless it enables a further exploit.
- Domain H: **duplicate-source-drift** probe — byte-identical lockstep copies
  (vendored, per-plane, generated-vs-source) need a parity test or single source;
  flag the missing guard, not the duplication.
- **Lead independent read of the top-N blast-radius files**, concurrent with the
  fan-out (`parallel-audit.md` §4 + Phase 2), so a zero-survivor run still has a
  non-empty confidence basis and no high-stakes surface goes unread.
- **Coverage attributed per unit** — finder id + lead-read, with a stalled/refused
  unit marked `unverified` rather than silently absorbed (Phase 0 ledger + Phase 5
  reconciliation + `parallel-audit.md` unit-manifest Lead-read column).

### Changed
- Example report version stamp 1.12.0; the example now shows the affirmative
  invariants ledger, a REFUTED-at-verify candidate (intended, test-encoded,
  fail-closed), and finder + lead-read coverage.

## [1.11.0] — 2026-08-21

Harvest from a same-owner inter-agent bridge review: name ASI01–ASI10, and
treat audience-mismatch plus committable-identifier leaks as first-class.

### Added
- ASI01–ASI10 titles (from the 2025-12-09 OWASP announcement, verified
  2026-08-21) in `references/security-ai-agents.md`.
- Same-owner vs many-audience probe under ASI07 (channel audience named;
  protocol keyed on tenant/uid, not a display name).
- Privacy: committable artifacts (PR/doc/fixture/commit) as a Q surface.
- Fan-out revision identity now fails closed on a missing or mistyped full SHA.
- Executable review units use separate worktrees and temp/port/process namespaces;
  aggregate suites serialize when that isolation is unavailable.
- Standards-index addendum 2026-08-21 (ASI titles; 2026 LLM Top 10 exists,
  titles unverified).

### Changed
- Domain C / adversarial pass / domain Q flags point at the new probes.

## [1.10.0] — 2026-08-21

Instrument/measurement discipline from three 2026-08-21 FULL/PR feedback runs —
the reviewer's own tools, not the code, were the dominant error source. Durable
invariants only; host-CI trimmed to one Phase-1 line + one report row (no new
first-response field), requirements-move ceremony left out.

### Added
- Principle 2: an absence needs a positive control; canonical instrument over
  proxy; read a platform-computed value from the platform (a gate reimplementing
  it is a finding); a project's enforcement is verified against the artifact, not
  the doc; self-review test blind spot.
- Phase 1: pipe/`$?`, SIGPIPE-141, `grep -q`, and `2>/dev/null` gate hazards
  (mechanics in `language-stack-redflags.md`); a tool count is a floor until caps
  are checked; gate-vs-standard (narrow ≠ weaken; WCAG 1.4.3 example); host-CI of
  the base branch.
- Phase 0: provision the worktree (never symlink deps; an env-shaped failure in a
  fresh worktree ≠ Blocker); read the revert *body* for its invariant.
- DIFF quick-path (consolidated) + ceremony-to-scope: ledger emitted at every
  scope, two-artifact report FULL-only, lighter `found → fix → re-gate` trail when
  reviewer = fixer.
- `mechanism-unproven` fix marker (Fix line + Phase 5 + definition-of-done).
- Domain G: singleton lifetime-vs-data bug class (leaks with perfect sync).
- Domain P 🚩: an a11y gate computing names from `innerText`; a presence-only name
  check.
- Ground-truth report row: `Host CI (base <ref>)`.
- `parallel-audit.md`: `REVERT_INVARIANTS` packet field; brief facts labelled
  `verified`/`to-be-verified` with premise verified before dispatch;
  `BRIEF_CONTRADICTION` as first-class output; symmetric re-verification; per-run
  diagnostic paths.
- `frontend-a11y.md`: cross-view consistency pass (WCAG 3.2.4 / 3.2.6) and the
  accessibility-tree-not-`innerText` rule.
- WCAG SC 1.4.3 / 3.2.4 / 3.2.6 verified by direct fetch (2026-08-21) in
  `docs/standards-index.md`.

### Changed
- Example report version stamp 1.10.0.

## [1.9.0] — 2026-08-19

Method honesty and detection depth from two FULL multi-model skill-feedback
runs — narrowed to durable invariants; host/model ceremony and duplicated
doctrine left out.

### Added
- SCOPE / packet field `BANNED_REMEDIES` (records Phase 0 revert/deletion scan).
- Principle 5: drift from a named stating artifact is the finding.
- Phase 2 named check: stated invariant / landed guard → bypass census
  (appsec untrusted-egress caller census; data-quality artifact→consumer).
- Config/runtime evidence rule: no severity on an unobserved branch.
- Planted-probe skip caps gate-self-test only (DoD wording).
- Parallel-audit: unit manifest, material dissent preservation, stop rule,
  named substitute in fan-out preamble.
- Soft-no-op persistence (empty artifact overwrite) in reliability + F map.
- Concurrency: corrupt→wipe ban; stale RMW across `await`.
- Data-quality: denominator integrity; absent/expected-empty/false/empty-list.
- Spend ledger: test present-fault branch (`EACCES`/`EISDIR`/invalid body).

### Changed
- Phase 5 BLUF: top defects + `Decisions: N` pointer; product/redesign never
  carries Blocker/Critical gate language.
- Example report version stamp 1.9.0.

## [1.8.0] — 2026-08-17

Depth from multi-model review of the skill itself: close authenticated-IDOR and
cache/CDN blind spots; force agent hard-gates; install support docs; lean privacy
+ observability refs; token-cutting coverage ledger and DIFF-scoped Phase 1.

### Added
- A01: Identity Map **forgeability** column + bypass row-set; **bidirectional
  gate proof**; **two-principal matrix**; **cache/CDN authz**; dual-surface
  beyond `page.tsx` (serialized payload, server actions, RPC/GraphQL/WS);
  tenant/row scoping; presigned URL / upload checks; safer anon-GET (canary +
  anon-vs-auth body diff; local/dev default).
- A05 files/archives/XXE; A06 business-logic detect steps; A07 session cookies +
  OAuth/OIDC + refresh rotation; API overlay procedures (BOLA/BFLA, mass-
  assignment, zombie APIs, GraphQL/gRPC/WS).
- `references/privacy-compliance.md`, `references/observability.md`.
- Phase-0 coverage ledger + archetype → load map; first-response hard block
  (`SCOPE`/`START_SHA`/`TREE_STATE`/`REVERTS_CHECKED`/…).
- Banned remedies: deleted gate paths (`--diff-filter=D`), not only Revert
  subjects.
- Authz posture ledger in Ground truth; negative authz tests in DoD;
  DIFF authz 🚩 list; public-repo disclosure rule for committed reports.
- Parallel-audit: frozen packet schema + invariant catalog.
- `install.sh` copies `standards-index.md` + `example-review-report.md` into
  installed `references/`.
- ASVS 5.0.0 verified by direct fetch (2026-08-17) in standards-index.

### Changed
- Phase 5 default: chat BLUF ≤30 lines + out-of-tree; `code-review/` write is
  opt-in (`--write-report` / confirm).
- Phase 1 scoped for `DIFF`/`FILE` (changed-path tests; plant only if gate under
  review).
- Domain S FULL: consequence branches + count by default.
- Domain B: SSRF ranges single-sourced in appsec; A02–A10 one-liners + force
  load of `security-appsec.md` before Phase 3.
- S2 world-reachable without auth = Critical (zero discretion).
- README domain table + reference count; example report version stamp 1.8.0.
- CI asserts installed support docs present.

## [1.7.0] — 2026-08-17

Access-control depth from a production anonymous-read class of defect:
identity must be mapped per request class before any gate is proposed; API
redaction is not page protection; preflight that expects anonymous 200 on
data routes is a finding; internal business data is Confidentiality Tier S2.

### Added
- **Identity Arrival Map** (document / XHR / bare curl) in `security-appsec.md`
  A01 — required before proposing middleware or document gates; "middleware on
  document when identity only arrives via client Bearer" marked anti-pattern.
- **Dual-surface check** — sensitive loader used by API ∩ RSC/SSR page;
  asymmetric redaction = Critical when world-reachable.
- **Anonymous GET sweep** — mandatory Phase 0/3 opener for networked apps
  (status + body size, no auth).
- **Confidentiality tiers S0–S3** in the severity rubric (incl. internal
  business data as S2 → Critical if world-readable).
- Phase 0: platform-vs-app-vs-preflight trust rows; **banned remedies** from
  recent auth/middleware/gate reverts.
- Phase 1 planted-defect matrix: missing / **empty** / wrong / path-excluding
  config.
- `parallel-audit.md`: specialized-subagent reject → **generalPurpose** fallback
  under the same read-only contract (do not stall A01 on harness ceremony).

### Changed
- Phase 5: prefer out-of-tree report during active Critical remediation; chat
  order for FULL = verdict → plain top 5 → decisions → path to machine table
  (table in file, not first bubble); advise-only on security gates (no
  auto-implement middleware).
- Domain B checklist + adversarial opener cross-link the new A01 procedures.
- `testing-and-evals.md`: empty-config self-test called out.

## [1.6.0] — 2026-08-17

**Agent-agnostic packaging.** The method was already host-neutral in substance;
install + docs still read Claude-first. Default install now mirrors the skill
into every common skill root (`.agents/`, `.cursor/`, `.claude/`), `AGENTS.md`
is the cross-vendor entry pointer, and SKILL/parallel-audit/docs speak to any
major coding agent first.

### Added
- Default multi-path install: `.agents/skills/`, `.cursor/skills/`,
  `.claude/skills/` (+ optional `--with-codex` → `.codex/skills/`).
- `--minimal` lean install; `--with-cursor` kept as no-op for compatibility.
- Harness table rows for Copilot / Gemini / Aider / Windsurf; generic-first
  fan-out contract.

### Changed
- SKILL "How to use" + confidentiality restatement → agent-agnostic discovery
  and `AGENTS.md`-canonical imprint language.
- `docs-and-dx.md` portability / imprint: prefer `AGENTS.md`, peers as pointers.
- README / AGENTS.md install pointer: no "for non-Claude agents" framing.
- CI dry-run asserts `.agents` + `.cursor` + `.claude` paths on default install.

## [1.5.0] — 2026-08-17

Depth + install portability on top of 1.4.0's multi-agent checkout safety. New
reference playbooks for reliability, concurrency, and API contracts; review-
surface gate in the definition of done; harness notes for fan-out; version
stamp + optional Cursor-native install path; worked fictional example report.

### Added
- `references/reliability-error-handling.md` — domain F depth (timeouts/aborts,
  retries, crash/SIGINT resume, silent subsystem no-op).
- `references/concurrency-shared-state.md` — domain G depth (races, file stores,
  TOCTOU, tests/jobs vs real shared paths).
- `references/api-contracts.md` — domain I depth (public contracts, webhooks,
  message-schema evolution; OWASP API Top 10 overlay stays in appsec).
- Skill `VERSION` file (`1.5.0`); `install.sh` stamps version + short SHA into
  the AGENTS.md pointer and **refreshes** that block on re-install.
- `install.sh --with-cursor` — also copies the skill to
  `.cursor/skills/deep-code-review/` (Cursor-native; Cursor already loads
  `.claude/skills/` for compatibility — verified against Cursor Agent Skills
  docs this session).
- `docs/example-review-report.md` — fictional FULL report showing `START_SHA`
  preamble, `CONFIRMED`/`CORROBORATED`/`PLAUSIBLE`/`latent`, and plain-language
  companion.
- `parallel-audit.md` harness notes — Claude Code / Cursor / Codex / one-shot
  map for read-only toolsets vs mutate-ban + tree-diff fallback.
- Definition-of-done + first-response **review surface pinned** checklist
  (`START_SHA`, worktree, history count).

### Changed
- README domain table routes F/G/I to the new references; install docs cover
  `--with-cursor` and the version stamp.

## [1.4.0] — 2026-08-17

Ops/safety hardening for **live multi-agent checkouts** — the review loop already
caught real defects under an anti-fabrication contract; this release makes the
method safe when another agent is editing, switching branches, or committing in
the same tree. Additive: domains A–S and report sections unchanged; new
confidence marker `CORROBORATED`; Phase 0/1/5 and `parallel-audit.md` carry the
depth.

### Added
- **Immutable review surface** — Phase 0 captures `START_SHA`, prefers
  `git show $START_SHA:path` or a dedicated worktree/clone (default for `FULL`),
  and detects a shared/mutating checkout (`git status` twice; occupied → don't
  plant or write into the live tree). First-response line states the pinned ref.
- **History-depth check** — Phase 0 runs `git rev-list --count HEAD` /
  `git log --oneline -5` (and shallow detection); never trust a prose "no
  history" claim; tree scrub ≠ history scrub for secrets/PII.
- **Triage-first fast lane** — Phase 0 runs project `doctor`/gates/documented
  invariants before expensive fan-out; Review mechanics and Phase 2 order by
  blast radius after those hits.
- **`parallel-audit.md` contracts** — read-only tool allowlist (or mutate-ban +
  lead before/after tree-diff hard-fail); transitive identifier masking in
  subagent returns; mega-file chunking by named concern; `CORROBORATED`
  confidence when independent units converge on the same sink.
- **Phase 5 shared-tree escape hatch** — if the checkout is occupied or an
  unrelated change is in flight, deliver the human-readable report out-of-tree /
  offer a dedicated review branch instead of writing `code-review/` into someone
  else's commit surface.
- **Hermetic-test shared-state red flag** — domain J (cross-ref G) + depth in
  `testing-and-evals.md`: tests that write real tracked/shared data paths with
  cleanup only in `finally`/`try` that hard-exit can skip.

### Changed
- Principle 7 — planted-defect probe defaults to a dedicated worktree/copy;
  report write is conditional on an unshared idle tree; fan-out least-privilege
  is by toolset where the harness allows.
- Principle 11 / confidentiality restatement — masking is transitive through
  fan-out, not lead-only.
- Phase 1 planted probe — worktree/copy at `START_SHA` by default; never plant
  into a tree another process can commit from.

## [1.3.0] — 2026-08-14

New capability — **branch, merge & open-work triage**. The review now analyzes
every open branch and advises, per branch, whether to merge it (to `main` or
`develop`, per the detected branching model), open a PR, rebase/refresh, delete
(if already merged), archive, split, or escalate — so leftover work gets cleaned
up instead of rotting. Unlike 1.2.0, this **does** change the domain list
(A–R → A–S) and **adds a report section** (the branch & merge triage table).
Additive and opt-in to act on: the triage is advice; any merge/delete/push runs
only on explicit approval.

### Added
- `references/branch-and-merge-hygiene.md` — the depth behind the new domain S:
  ground the branch set before judging it (`git fetch --all --prune`; a shallow/
  stale clone hides open work; open-PR state is forge state, mark `unverified`
  when forge auth is absent); detect the branching model (Trunk-Based / GitHub
  flow / GitLab flow / git-flow) to resolve each branch's target; classify by
  **content, not just tip** — `git branch --merged` misses squash/rebase-merges,
  `git cherry` recovers single-commit squashes but a **multi-commit squash defeats
  patch-id matching**, so the forge merged-PR list is the authoritative
  corroborator; a per-branch decision tree → recommendation with the exact
  command; merge-strategy trade-offs; safety rails (never delete unique unmerged
  work, `--force-with-lease` not `--force`, a leaked secret is fixed by rotation
  not branch deletion); and severity discipline so branch cleanup never buries a
  real defect. All enumeration commands validated against a scratch repo this
  session. Routed from the new domain S.
- **Domain S — Branches, merges & open-work triage** in `SKILL.md` (A–R → A–S),
  scoped to a local git checkout; a Phase-0 open-branch/open-PR inventory hook; a
  Phase-5 triage-table output; a **Branch & merge triage** section in the findings
  report and an "Open work to tidy up" section in the human-readable report; and a
  definition-of-done line requiring every open branch to carry one recommendation.
- Boundary made explicit with section O (`docs-and-dx.md`): O owns *is branch
  protection configured*; S owns *what open work exists and what to do with it* —
  cross-referenced, not duplicated.
- `docs/standards-index.md`: verified-this-session rows (2026-08-14) for
  Trunk-Based Development, GitHub flow, GitLab flow, git-flow (Driessen), Fowler's
  branching-patterns article, GitHub's merge-method / protected-branch / merge-
  queue / branch-deletion docs, and the `git` reference manual, with the two
  attribution caveats surfaced by primary-source checks (GitHub's own docs do not
  state "main is always deployable"; "merge debt" is not Fowler's phrase).

## [1.2.1] — 2026-08-14

### Fixed
- `install.sh` backed up an existing skill to `…/.claude/skills/<name>.backup-<ts>`
  — **inside** `skills/`, where Claude Code then loaded the backup as a duplicate
  skill. Backups now go to `…/.claude/skill-backups/` and are never loaded.

### Changed
- `install.sh` is **universal by default**: alongside the Claude Code skill it
  writes an additive, idempotent cross-agent `AGENTS.md` pointer (Codex, Cursor,
  Copilot, Gemini, Aider), so the method is not Claude-only. The opt-in
  `--portable` flag is replaced by a `--claude-only` opt-out (`--portable` is still
  accepted as a no-op, with a note).

## [1.2.0] — 2026-08-14

Coverage extension — dependency currency & safe upgrades, repository hygiene,
cross-agent portability of the standards imprint, and DX depth — plus the repo now
enforces its own documented gates in CI. Additive; phases, domains A–R, and report
formats are unchanged.

### Added
- `references/dependency-currency-and-upgrades.md` — detect stale / EOL /
  known-vulnerable dependencies, then upgrade with discipline (no blind "latest",
  semver-risk sizing, changelog review, regenerated lockfile, the project's own
  gate proven green on the bumped tree, provenance check) with severity discipline
  so "behind latest" never becomes noise. Routed from K and H.
- Repository hygiene & community-health review (`docs-and-dx.md`, SKILL.md O):
  LICENSE, SECURITY.md, CONTRIBUTING, CODEOWNERS + its enforcing rule, branch
  protection, CHANGELOG, templates — rated by repo exposure (Info/Low private,
  escalating when public / distributed / reaching production).
- Cross-agent portability: a divergence check across `CLAUDE.md` / `AGENTS.md` /
  peer instruction files, and a Phase-6 imprint that now defaults fresh standards
  to a canonical cross-vendor `AGENTS.md` with thin per-agent pointers; the
  "documented but unenforced = advisory" durable-standards finding.
- `install.sh --portable` — additively drops an idempotent root `AGENTS.md`
  pointer so non-Claude agents (Codex, Cursor, Copilot, Gemini, Aider) discover
  the method.
- This repository now dogfoods its own bar: `.github/workflows/ci.yml` (routing,
  name-match, `install.sh` parse, banlist-driven fail-closed privacy gate; a
  SHA-pinned action + least-privilege token), plus `SECURITY.md`,
  `CONTRIBUTING.md`, and `.editorconfig`.
- 16 standards verified by direct fetch and logged in `docs/standards-index.md`.

### Changed
- **DX** (`docs-and-dx.md`) gains fewest-commands-to-first-run (normalized
  bootstrap / devcontainer), dev/prod parity, and time-to-first-run as friction.
- **Phase 6 / imprint** is now idempotent and additive (detect-and-stop,
  create-if-missing, add-only-missing-lines, print-what-changed) and pairs every
  imprinted standard with the gate that enforces it.
- **Decorrelated second-model review** (SKILL.md review mechanics) is read-only
  and fail-soft — it advises, never hard-blocks.
- README reference-file count (10 → 11); standards list refreshed.

### Fixed (from a self-review of the skill)
- **Phase 5** no longer mandates writing `code-review/…` for a `DIFF` of a PR/MR
  (which may have no writable checkout, and would land the file inside the diff
  under review) — that write is scoped to FULL / local-checkout, and a DIFF's
  deliverable is the review comment on the PR.
- **Phase 1**'s planted-defect gate probe now requires a verified-clean tree (or a
  throwaway worktree) and a confirmed revert, carved into principle 7 as the one
  permitted transient mutation.
- **Severity rubric**: `unverified` / `PLAUSIBLE` findings now have an explicit
  gate rule (reported at provisional severity, block only once confirmed); Blocker
  vs Critical for data damage is discriminated (already-corrupting vs
  will-corrupt-next-run).
- **Coverage**: input-amplification DoS (ReDoS, decompression / entity-expansion
  bombs) added to the adversarial pass and the red-flag greps; AI-eval golden-set
  **contamination** flagged as a Critical eval defect; one-shot-prompt mode now
  names the references to also paste.
- **Duplication / pointers**: data-quality's spend-governance restatement folded
  into a cross-reference to `performance-db-cost.md`; a stale "section M" secret
  pointer repointed to N; `N-A` → `N/A`; `CREATE INDEX CONCURRENTLY` marked
  Postgres-specific.

## [1.1.0] — 2026-08-13

Field-hardening pass distilled from four independent FULL-run engagements. No
restructuring — phases, domains A–R, and report formats are unchanged; these are
additive method, rubric, and reference refinements.

### Added
- `references/parallel-audit.md` — fan-out protocol for large targets: a shared
  context packet, a fabrication-resistant subagent contract (one named invariant,
  `file:line` + failing case, `NONE` is valued), and orchestrator re-verification
  of every subagent finding in both directions. Routed from "Review mechanics"
  and Phase 2.

### Changed
- **Phase 1** now verifies gate *scope*: run the project's own aggregate gate by
  name, confirm exit codes, enumerate what the gates exclude and report coverage
  per subtree, prove each gate goes red on a planted defect, and flag
  decorative/unwired tests — plus a container/serverless deploy-contract
  preflight.
- **Severity rubric** gains a reachability qualifier: a `latent` finding keeps its
  intrinsic severity but gates "enabling the subsystem," not merge (a bounded +
  gated + recoverable destructive breach may be High); owner priority raises
  prominence, not severity. Machine and human reports gain a two-status verdict
  and `CONFIRMED`/`PLAUSIBLE` finding confidence.
- **Domains A–E, C, O** and their references gain: latest-batch-by-`max(col)`;
  exposure-boundary-first + CSRF≠auth; the "asserted-but-unenforced safety
  property" class; a spend-safety checklist (default-off caps, fail-open ledgers,
  `SELECT sum()` TOCTOU, cross-process guards); monotonic read-path shadowing +
  write-guard-covers-every-primitive; and a docs↔code claim-reconciliation
  technique.
- **Principle 2 / Phases 4–5**: byte-fidelity before invisible-character claims; a
  live-vs-documented-incident discriminator; report privacy re-scan, third-party
  proper-noun scrub, and PR-split by risk surface.
- README reference-file count (9 → 10).

## [1.0.0] — 2026-08-13

Initial release: a universal, evidence-grounded deep code-review skill.

### Added
- `.claude/skills/deep-code-review/SKILL.md` — the review method (6 phases) and
  eighteen domain checklists (A–R) plus an adversarial/red-team pass, severity
  rubric, exact report format, and definition of done.
- Nine on-demand reference playbooks under `references/`: application security
  (OWASP Top 10:2025), AI/LLM/agent security (OWASP LLM Top 10:2025 + Agentic
  Applications 2026), data integrity & quality, performance/DB/cost, testing &
  evals, infrastructure/IaC/containers, docs/DX (incl. the standards-imprint
  phase), frontend/accessibility (WCAG 2.2 AA), and language/stack red flags.
- `install.sh` — one-command install of the skill into any project's
  `.claude/skills/`, with backup-on-update and self-install guard.
- `README.md` (human-facing, with a Mermaid method diagram and a coverage map),
  `CLAUDE.md` (AI-facing standards for this repo), `docs/standards-index.md`
  (verified standards with URLs + verification dates), `.banlist.txt` privacy-gate
  seed, `LICENSE` (MIT), and `.gitignore`.

### Notable design decisions
- **Judge the outcome, not just the code** — a hard monotonic-quality invariant
  for any data producer, with a required non-regression test.
- **Do no harm** — every proposed change must be net-positive across all axes;
  never fix one by regressing another.
- **Respect the existing design** — accessibility/UX defects are fixed in place;
  design-altering changes are surfaced as owner decisions.
- **Standards imprint** — an opt-in final phase persists a tailored standards set
  into the reviewed project so quality holds on later iterations.
- **Human-readable report** — Phase 5 also writes a plain-language, non-technical
  report into a top-level `code-review/` directory in the reviewed repo (dated,
  additive), so a founder or leader can act on it without reading the code.
- **No duplication** — the skill has a single home; `SKILL.md` routes to every
  reference; nothing is restated.
- **No fabrication / cite-only-verified** — standards are split into
  directly-fetched (with dates) and by-name in `docs/standards-index.md`.
