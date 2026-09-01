# Parallel / fan-out review — protocol & anti-fabrication contract

Read this when the target is large enough to review across **parallel
subagents** (a `FULL` run of a large repo, or several focused domain passes at
once). A fan-out is very effective — but without a strict contract it manufactures
plausible-but-fake findings and re-derives project context N times. Expands the
"Review mechanics" note in `SKILL.md`; it operationalizes the "a second opinion
should be decorrelated" principle at scale.

The governing fact: **subagents share the orchestrator's blind spots and carry
their own authority into the report.** Both have to be engineered against.

---

## 0. Same pinned surface for every unit

Hand every audit the Phase-0 `START_SHA` (or the dedicated worktree path at that
SHA). Resolve the **full object ID before fan-out**. A missing or mistyped requested
SHA is a hard scope failure: do not silently substitute the checked-out commit or
a unique-looking prefix and call the result exact. Correct the packet and rerun
the exact-scope unit; use abbreviated SHAs only for display after pinning the full
ID. Units read via `git show $START_SHA:path` / files in that worktree — never
"whatever is checked out now." A live tree another agent is editing will otherwise
produce disagreeing `file:line` citations and findings about code that does not
exist on the reviewed ref. If the harness cannot isolate a worktree, the lead
records that limitation and still requires every citation to resolve at
`START_SHA` on re-verify.

A shared pinned worktree is sufficient only for genuinely read-only units. Give
every unit that runs tests or builds its **own worktree/clone and per-run temp,
port, and process namespace**. Aggregate suites can write ignored fixtures, bind
fixed ports, or kill a sibling server even when tracked files stay clean. If the
harness cannot isolate executable units, run them serially and record the limit;
never interpret a concurrently contaminated failure as a candidate defect.

**Mega-files / huge blobs:** when a single file is too large to hold in one
context (tens of KB of dense logic, generated bundles, vendored trees), split by
**named concern** (auth surface, write path, egress, parser) with overlapping
seams of ~50–100 lines so call edges are not orphaned — still one invariant per
unit. Prefer symbol/grep entry points over linear whole-file reads. Do not invent
line numbers for unread regions; unread → `unverified` or out of scope.

---

## 1. Assemble the shared context packet once, hand it to every subagent

A subagent that re-discovers the project from scratch spends most of its budget
re-reading what the lead already knows, and judges against a slightly different
bar. Assemble **one** packet (frozen schema below) and give the identical copy
to each unit.

### Packet schema (copy-paste; fill every field)

```
START_SHA: <sha>
WORKTREE: <path | none — citations still at START_SHA>
HARD_RULES: no fabrication; mask identifiers; read-only tools only
GATE_SCOPE: <what root gate excludes; subtree gates>
TRIAGE_HITS: <already found — deepen, do not re-report as new>
CLEARED: <paths/areas not to re-review>
ARCHETYPE: <web|api|data|agent|iac|lib|other>
AUTHZ_LEDGER: <entry points N · anon planned Y/N · two-principal Y/N>
BANNED_REMEDIES: <from Phase 0 SCOPE | NONE — do not re-propose>
REVERT_INVARIANTS: <one-line mechanism facts the reverts established — design constraints, not history | NONE>
BYTE_FIDELITY: check invisible chars before claiming string equality
LIVE_VS_PAST: git log -S before reporting "live" bugs narrated in comments
NONE_OK: empty finding list is valued
```

**Label every fact-carrying field `verified` or `to-be-verified`** (ids, targets,
counts, names, "X already does Y"): a fact is `verified` only once the lead re-read
it at `START_SHA`; unlabelled ⇒ `to-be-verified`. **Verify each lane's premise at
the pinned ref *before* dispatch** — if the entity a lane names doesn't exist
there, or a value differs from the canonical source, fix the packet before
spawning. A fan-out amplifies one wrong premise into N confident, well-cited, wrong
findings — the most expensive kind, because every anti-fabrication check passes.

**Diagnostics are per-run.** Copy any diagnostic a gate writes to a run-scoped
path the moment it is produced; a tool that writes diagnostics to a fixed global
path (`/tmp/ux-audit.json`) races other units, and on a parallel-gate project that
fixed path is itself a finding.

### Unit manifest (lead-owned; fill before spawn, update on done)

| Unit id | Invariant | Owned paths | Unit/tier actually used | Lead-read | Status |
|---|---|---|---|---|---|
| <catalog id> | <one sentence> | <paths or glob> | <requested → actual if substituted> | Y/N | planned / running / done / skipped |

Record unavailable or refused units in the **fan-out preamble** with the
**named substitute actually used** (never a silent swap). Same-tier units from
the same model family are not decorrelated second opinions.

**A stalled or missing unit is `unverified`, never silently absorbed.** A unit that
never reaches `done` (slow, capped-out, crashed, timed out, refused) does not
vanish into an implied "all clear": its owned invariant is reported `unverified`
in the Phase 5 reconciliation, named with the unit id. Fill the **Lead-read**
column as the lead's own independent read (section 4) covers each owned path, so
Phase 5 can state, per unit, **who actually covered it — finder id *and* lead-read**
— the "no silent caps" principle applied to the fan-out's own completeness, not
only to sampling inside a unit.

### Invariant catalog (pick one per unit — do not invent overlapping "find issues")

| Unit id | Invariant (one sentence) |
|---|---|
| anon-GET | Every documented GET refuses sensitive bodies without auth |
| IDOR | Two-principal object-swap: other→403/404, none→401 |
| dual-surface | Every caller of a sensitive loader enforces the same authz/redaction |
| cache-authz | Identity-derived responses not publicly cached at CDN/origin |
| injection | No string-built SQL/command/HTML sinks on untrusted input |
| spend-cap | Every paid call is behind a pre-call cap (default 0 = no cap = finding) |
| monotonic | No write path lowers a populated/higher-confidence field |
| gate-exclude | Gate-excluded subtrees are named and audited or flagged |
| fail-closed | Security/config absent or empty → refuse, never pass |

Then give each subagent only its **unique scope + one catalog id**. This pays the
domain-context duplication once instead of once per unit.

### Tier the sweep — cheap enumerate, then expensive confirm

One monolithic high-effort finder per domain makes total agent-minutes scale with
**domain size**, not defect count: two large surfaces then hold the whole pipeline
under a small concurrency cap while clean domains sit queued behind them. Split the
fan-out into two tiers so cost tracks **candidate count** instead:

- **Tier 1 — candidate sweep (fast, low-effort).** One cheap pass per unit that
  only *enumerates* candidate invariant violations (`file:line` + a one-line
  claim), no deep proof. A clean domain then costs one cheap sweep, not fifteen
  minutes of deep reading.
- **Tier 2 — confirm (high-effort).** Runs **only on the candidates that survive
  Tier 1**, plus the adversarial re-verify of section 4. High-effort minutes are
  now proportional to surviving candidates, so the fan-out degrades gracefully
  under a small cap.

**Size units small — one invariant, a few hundred lines of owned surface.** A unit
that owns a 500-line file plus its tests is the one that stalls; keep the
one-invariant-per-unit split the catalog already prefers, sized so no single finder
holds more than a few hundred lines of owned surface (mega-files still split by
named concern per section 0). Record the tier each unit actually ran in the
manifest's *Unit/tier actually used* column.

---

## 2. Read-only by toolset, not only by instruction

Review is read-only (principle 7). Fan-out units must not be able to mutate the
reviewed project just because the prompt said "don't edit."

- **Prefer a harness-enforced read-only tool allowlist:** Read / Grep / Glob /
  `git show` / `git log` / `git grep` (and similarly non-mutating inspect). No
  Edit, Write, apply-patch, or mutating shell (`git commit`, `git push`,
  `git checkout`, `git reset`, `rm`, redirects that overwrite project files).
- **If the harness cannot restrict tools,** the prompt must **forbid all mutating
  commands explicitly**, and the lead **snapshots the tree before fan-out**
  (`git status --porcelain` + `git rev-parse HEAD`) and **diffs after**. Any
  unexpected change → hard-fail the fan-out, restore from `START_SHA` /
  worktree, and discard that unit's unverified output until re-run read-only.
- Context-inheriting forks are especially dangerous: strip unrelated parent
  instructions ("open a PR", "commit this") from the unit prompt; give only the
  packet + one invariant.

### Harness notes (map the allowlist; do not pretend every host enforces it)

State in the fan-out preamble which case you are in. Prompt-only "don't edit"
is never enough by itself. **Contract is host-neutral** — only the spawn
mechanism changes.

| Host / pattern | How to get read-only audits | Fallback when you cannot |
|---|---|---|
| **Generic / any agent** | Spawn or hand off with an explicit tool allowlist: Read / Grep / Glob / non-mutating git only. Pass identical packet + `START_SHA` + one invariant. | Mutate-ban in prompt + lead before/after `git status` / `HEAD` diff; hard-fail on drift. Prefer a dedicated worktree the unit cannot push from. |
| **Cursor** (Task / subagents / skills) | Skills under `.cursor/skills/` or `.agents/skills/` (also loads `.claude/skills/` / `.codex/skills/`). Restrict tools when the Task UI offers it; otherwise treat as unrestricted. | Same tree-diff hard-fail. |
| **Claude Code** (subagents / Task) | Prefer a subagent/tool allowlist with no Edit/Write. Slash-invoke `/deep-code-review` when installed under `.claude/skills/`. | Mutate-ban + tree-diff. |
| **Codex** | May load `.codex/skills/` or follow `AGENTS.md`. Assume full Edit/Write/shell unless sandboxed. | Mutate-ban + tree-diff; worktree. |
| **Copilot / Gemini / Aider / Windsurf** | Usually instruction-file driven (`AGENTS.md`, copilot-instructions, `GEMINI.md`, `.windsurf/rules`). No reliable tool lockdown — sequential in-process invariants under principle 7, or external read-only checkout. | Same. |
| **One-shot paste** (no subagents) | No fan-out — run invariants sequentially in-process under principle 7. | N/A |

If the host documents a "read-only" / "ask" / "plan" mode, use it for audit
units and still re-verify at `START_SHA` — mode labels are not evidence.

### Specialized-subagent quirks → never stall security

Some hosts ship **rigid specialized reviewers** (fixed-prompt units that accept
only a repo path + diff selector and refuse a free-form A01 / domain audit).
**Harness ceremony must not delay the security pass.**

| Situation | Action |
|---|---|
| Specialized reviewer rejects / ignores a domain-invariant prompt | Retry **immediately** with a **general-purpose** (or equivalent unconstrained) unit under the **same** read-only contract + shared packet + one named invariant. |
| Specialized reviewer only accepts "branch changes" / "uncommitted changes" | Use it for that shape; run domain A01/authz as a separate generalPurpose unit — do not skip A01 waiting for the specialty harness. |
| Specialty unit unavailable / times out | Same fallback: generalPurpose, read-only, re-verify at `START_SHA`. |

Record the fallback in the fan-out preamble ("specialty rejected → generalPurpose"
or "requested unit unavailable → <named substitute>") so the lead knows the unit
was not the decorrelated specialty reviewer — still re-verify; never drop A01
because the host's named security agent was picky. Never silently swap models.

---

## 3. The fabrication-resistant subagent contract

Put every clause in each subagent's prompt. A clean large tree will otherwise
hand back a hundred confident inventions.

- **One named invariant per unit**, not "find problems in domain X." ("No
  update path can lower a populated field." "Every paid call is behind a
  pre-call cap.") A unit hunting a specific invariant reports real breaks; a unit
  told to "look for issues" fabricates to look thorough.
- **A finding requires `file:line` + the concrete failing input/state**, and that
  `file:line` must resolve at `START_SHA`. No failing case → not a finding. Ban
  severity words without a reproduction.
- **`NONE` is a correct, expected, valued answer.** Say so explicitly, or the
  unit invents an issue rather than return empty.
- **A packet fact is a hypothesis until you read it at `START_SHA`; contradicting
  it is first-class output.** If the entity the packet names does not exist, or a
  value differs from the canonical source, report `BRIEF_CONTRADICTION: <asserted>
  | <found at file:line@START_SHA> | <what I'd have written if I'd trusted it>`
  **first, and stop** — do not substitute a nearby entity or soften it to a caveat.
  A unit that returns only a contradiction has done its job.
- **Cap findings (~5)** and **prefer running a probe over speculating** — a
  five-line script that proves the break is worth more than a paragraph of
  "this could…". Probes that need a planted defect run only in the lead's
  dedicated worktree (Phase 1), never in a shared live tree.
- **Mask real identifiers in the unit's own output** before returning to the
  lead: emails, people/company names, internal IDs, hostnames, secret-shaped
  strings → role placeholders or redacted forms (`j***e@e***.com`). Fan-out is
  how PII otherwise reaches the lead's context and the report. Do not echo
  secret values even redacted if a fingerprint/`file:line` suffices.
- **Return an affirmative `checked_sound` list, not only findings.** For each
  invariant the unit opened the code and confirmed *holds*, record it with the
  same `file:line`-or-drop rigor a defect gets — `invariant | file:line@START_SHA
  | what proves it`. Say this list is a valued, expected product: on a hardened
  target the finding list is empty and `checked_sound` is the unit's **entire**
  output, so the unit affirms specific soundness ("tenant selection is
  JWT-`sub`-only; body/query/header cannot select a tenant") instead of inventing
  a defect to look thorough. An affirmative claim must be as falsifiable as a
  defect claim — the lead re-verifies it (section 4), and it is the primary
  deliverable on a hardened target (SKILL Phase 5, "Invariants verified to hold").

---

## 4. The orchestrator re-verifies every survivor — in both directions

No subagent finding enters the report on the subagent's authority. For each
survivor the lead **re-opens `file:line` at `START_SHA` and confirms against
source, adversarially** — and verification runs **two ways**:

- **Refute false positives.** Try to break the claim; a finding that can't be
  reproduced at source is dropped, not softened. A citation that only exists on
  another branch / dirty tree is contamination — exclude it.
- **Test whether a `NONE`/caveat understated a gap.** A unit that returned
  "NONE, minor caveat" may have missed that the caveat *is* the finding.
  Verification catches **under**-reports, not only over-reports.

**Check the finding against the tests before `CONFIRMED` — re-reading the source
the finder read cannot catch an intended-behavior false positive.** The source
looks exactly as the finder (and a source-only verifier) described it; only the
**tests and the suite encode intent**, so a verify stage that just re-reads source
inherits the finder's blind spot. Before any `CONFIRMED` verdict, do at least one
of:
- **Test-awareness (minimum).** Locate and read the tests that exercise the
  finding's file/function. A finding whose proposed fix would **contradict an
  existing passing assertion** is `REFUTED` — the behavior is intended by design,
  not a defect — unless you can show the test itself is wrong (say why, in
  writing). `REFUTED` drops the finding; it never enters the report.
- **Fix-against-suite (gold standard; required when the finding proposes a code
  change to security / cost / concurrency logic).** Apply the proposed fix in a
  **throwaway worktree** (never the shared tree — principle 7) and run the repo's
  own gates. A fix that turns the suite **red** refutes the finding, or proves it
  needs a different fix; a fix that keeps the suite green and reproduces the
  original break red-first is the strongest `CONFIRMED` a fan-out can produce.

**Confidence marker on every finding** (surface it in the report):
- `CONFIRMED` — the lead independently re-verified it at `file:line` on
  `START_SHA`.
- `CORROBORATED` — two or more independent audit units (different invariants /
  angles) hit the same sink or defect class; still lead-re-verify before it
  blocks a gate, but treat convergence as a stronger signal than either alone.
- `PLAUSIBLE` — subagent-reported, not yet lead-verified. A sibling of the
  `unverified` convention; **never silently promoted** to a bare finding.

**Preserve material dissent.** When unit A reports `NONE` and unit B confirms a
finding on the same sink (or they disagree on severity/reachability), keep both
claims in the lead notes until source re-verify decides. Do **not** majority-
collapse; record which unit the lead favored and why.

**Re-verification is symmetric, and a brief contradiction never majority-
collapses.** When a unit's *measurement* contradicts the lead's *diagnosis*, the
lead verifies the measurement — a hypothesis carries no evidentiary weight against
an instrument reading, and a review that never corrects its own lead is not being
verified. One unit contradicting the packet outweighs nine succeeding on it (the
nine answered a question the tenth just showed was wrong): re-verify at source,
correct the packet, and re-run any unit whose invariant depended on the bad fact.

**Affirmative `checked_sound` claims are re-verified too.** A unit's "this
invariant holds" entries carry the unit's authority exactly as findings do; the
lead re-opens the load-bearing ones at `file:line`@`START_SHA` and drops any that
don't hold. An unverified "invariant holds" is as misleading as an unverified
defect — and on a hardened target it *is* the deliverable (SKILL Phase 5,
"Invariants verified to hold"), so it earns the same file:line-or-drop rigor.

**The lead reads the top-N blast-radius files independently — concurrently with
the fan-out, not post-hoc.** When there are **zero survivors** (the common outcome
on a hardened target, where finders return `[]` and re-verify has nothing to chew
on), the review's credibility rests entirely on the lead's own reading — so make
it explicit and non-empty. While units run, the lead reads the top-N
highest-blast-radius files (N sized to the target; Phase 0's triage already ranks
blast radius) adversarially and independently. This (a) gives a **non-empty
confidence basis on a clean target**, (b) cross-checks the finders' `[]` returns
against a second independent read, and (c) means a slow or stalled fan-out never
leaves the highest-stakes surfaces unread. Record it in the manifest's **Lead-read**
column; Phase 5 reports lead-read coverage alongside finder coverage.

**Stop rule.** Stop expanding fan-out when high-blast sinks already have two
independent passes plus lead re-verify at `START_SHA` — more units on a settled
sink is theater, not coverage.

---

## 5. Subagents inherit the reviewer's blind spots — inject the discriminators

A tool that renders bytes, and a repo that documents its own past, fool every
unit the same way. Put both discriminators in **every** subagent prompt, and have
the orchestrator apply them to security-critical claims itself:

- **Byte-fidelity** (cross-ref principle 2, domains C & R): the viewer may
  collapse NUL / zero-width / bidi / BOM to whitespace or drop them. Any finding
  that hinges on an invisible or easily-confused character — "this delimiter is
  absent," "this comment is stale," "these two strings differ" — is checked at
  the byte level (`xxd` / `od` / a code-point dump) before it is asserted, and
  treated as `unverified` until then. This kills false "stale comment" findings
  **and** catches real invisible-character injection the render hides.
- **Live defect vs documented past one** (cross-ref Phase 4): comments often
  narrate fixed incidents in present tense (`Audit 2026-…`, `Bug B`, `live
  incident …`). Before reporting, apply the discriminator: (a) is there a test
  pinning the corrected behavior? (b) does `git log -S'<symbol>' --oneline` (or
  `git log -L`) show the fix already landed? If either is yes, it is a historical
  note, not a finding. A fan-out will otherwise re-report the repo's own
  changelog as new bugs, once per unit. Pair with Phase 0's **measured** history
  depth — do not argue from a README claim that history is absent.

---

**Delivery:** when a fan-out yields both routine fixes and a change to a
security/permission/authz boundary, split the remediation by risk surface (see
`SKILL.md` Phase 5) — the security-critical diff rides its own small PR for a
decorrelated reviewer, never buried under nits. Report files follow Phase 5's
shared-tree escape hatch.
