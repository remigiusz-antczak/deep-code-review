# How Perun improves itself

**BLUF.** Perun is improved by running Perun on Perun: its own review skill
(`deep-code-review`), idea attack (`idea-critic`), eval net, and mechanical gates
are the quality bar for every change to the skillset. This is **Loop 2 of the
["growing together" model](roadmap.md)** made operational — the runbook, and where
each piece already lives. This page is a *map*: it links the pieces, it does not
restate them (the [registry-not-bundle](../CLAUDE.md) thesis, applied to the loop
itself).

## The loop (each step names the tool that owns it)

| # | Step | What happens | Defined in |
|---|------|--------------|-----------|
| 1 | **Signal** | A real-run failure becomes an issue with a *Where / Done-when / Verify / Why* contract — "Verify" is load-bearing, or "done" is an opinion | [roadmap.md](roadmap.md) "Additive principles" |
| 2 | **Triage + place** | Decide it is worth implementing and general (not slop); assign one home; pre-distinguish it from every existing lens so no second copy is created | [CLAUDE.md](../CLAUDE.md) "No duplication" |
| 3 | **Draft** | Write the depth as prose in a routed `references/*.md`, with a "Read this when…" trigger; route it from the owning `SKILL.md` | [CLAUDE.md](../CLAUDE.md) "Adding or updating a reference file" |
| 4 | **Attack** | Run `idea-critic` (skeptic / better-way / kill-criteria) and the advisor *before* substantive work; adopt or rebut each finding against the bytes | [`idea-critic`](../.claude/skills/idea-critic/SKILL.md) |
| 5 | **Eval** | Add one *behavioral* eval per lens (a prompt and the behavior a correct answer must show) | `.claude/skills/<skill>/evals/evals.json` |
| 6 | **Review** | An independent dogfood reviewer, held to Perun's own bar, reads the diff for anti-duplication, placement, correctness, privacy, and fabrication — before merge | [roadmap.md](roadmap.md) ("independent reviewer pass before merge"); named as procedure here |
| 7 | **Gate** | The mechanical gate suite (routing / version / privacy / enumeration / size / checksums) plus the offline eval-predicate net must all pass | [`ci.yml`](../.github/workflows/ci.yml), [`scripts/ci-gates.sh`](../scripts/ci-gates.sh), [`scripts/eval_predicates.py`](../scripts/eval_predicates.py) |
| 8 | **Ship** | Lockstep version bump, CHANGELOG, regenerate `SHA256SUMS` last, tag; a human authorizes the landing. The release squash commit carries `Model: <model>` and `Reviewed-By: <reviewer id> receipt:<sha, path, or PR review URL>` trailers, which CI's advisory review-tiers step (`tier_gate.py`) checks | the [version gate](../.github/workflows/ci.yml) checks the CHANGELOG announces the version, and [`scripts/write-checksums.sh`](../scripts/write-checksums.sh) regenerates the pin; the full lockstep sequence is maintainer practice, not yet an in-repo doc |

Steps 4–7 are `deep-code-review` and `idea-critic` pointed at Perun's own tree.
Dogfooding is not a metaphor here — it is the release process.

## The eval rubric is split on purpose — what is built, what is planned

Loop 2 grades improvements on a **split rubric** (see [roadmap.md](roadmap.md)),
because the two kinds of axis fail differently:

- **Hard axes — deterministic, no model.** Boundary-compliance and non-fabrication
  are graded by code, *because a fluent wrong answer fools an LLM judge*. **Built:**
  `scripts/eval_predicates.py` binds the fabrication-refusal evals to deterministic
  predicates and proves each one discriminates a golden refusal from a golden
  fabrication (`--selftest`, in CI, no API key, no network, no spend). Because the bindings are curated in the
  script rather than in `evals.json`, the layer can change or be removed without
  touching skill content or bumping a version.
- **Soft axes — LLM-judge, decorrelated.** Whether a *behavioral* lens actually
  changes model behavior needs a model to judge it — the other ~60 evals' behavioral
  expectations are specification today, not executed. **Planned:** issue #61, the
  live eval runner (the "next slice of the eval-harness work" named in
  `scripts/eval_predicates.py`). When it is built it must use a cheap, decorrelated
  judge; enforce a per-run spend cap *before* each call; fail closed on a missing
  key or input; and stay **owner-invoked, never a required CI gate**, because it
  costs money per run.

## Invariants the loop must never break

- **Registry, not a bundle** — link, never duplicate; this page is itself the example.
- **Quality only ratchets up** — a regression gate stops backsliding, generalized eval
  cases raise the floor, and a human authorizes every landing.
- **The fuel is verified eval cases and cited standards** — never hoarded user data,
  never a fabricated finding, source, metric, or citation.
- **Deny by default; unreadable must never look like empty** — a check whose input is
  missing fails closed, and an unverified claim is marked `UNVERIFIED`, not omitted.
