# Gate epistemology — full statements of the principles `SKILL.md` indexes in one line

Read this when: a gate flips, a count jumps, or a check could not run and you must call it defect, flake, or `UNVERIFIED` (3); before closing, deduplicating, or deleting shared state (9); before reporting a change as visible or done (11); before shaping a choice as an owner gate when a ratified invariant may already decide it (12). `SKILL.md` **Gate epistemology** keeps the numbered one-line index and the short principles in full; the numbering is shared, so "principle N" resolves in either file.

---

## Principle 3 — a gate can be wrong about why

3. **A gate can be wrong about why.** Real defect → fail closed. Check could
   not run → `UNVERIFIED` — neither a defect nor a pass; a *required* missing
   check still blocks its gated action even when authorization exists (evidence
   and permission are separate decisions). Applied to a red pipeline: identify
   the failing job **and step** before blaming the newest merge, and if the
   shape matches a known-flaky browser/probe/hydration check, rerun and recheck
   **before** reverting — a revert is warranted only once the failure
   reproduces and is causally tied to the change, not merely adjacent in time. And **a
   conclusion that surprises you** — a gate that flips, a count that jumps — **is the signal
   to re-fetch the specific state at decision time**, not to act on a snapshot remembered from
   earlier in the run (principles 9 and 11 apply the same discipline to a close and to the
   owner's rendered surface).

## Principle 9 — closing or deleting shared state

9. **Closing or deleting shared state needs evidence, not presumption** — the
   "skip rather than guess" bar (principle 5) applied to removal. A ticket
   closed as duplicate/invalid needs a reproducible reason (not "looks like the
   others"), and any unique context it carried migrates to the canonical item
   **before** it closes. A batch of presumed-junk items is a batch of
   `UNVERIFIED` closures until each is checked — a plausible pattern across many
   is not evidence for any one.

## Principle 11 — visible/done is measured on the owner's surface

11. **"Visible/done" is measured on the owner's own surface, never a proxy.**
    Integrated to the mainline (G7), a green branch build, a passing test, an
    insert/row count, a grep count are engineering states — real, but none is
    "the owner can see it." Before reporting a change as *visible*, fetch the
    specific rendered thing from the surface the owner actually uses (a running
    app, the deployed page — which may lag a pinned or cached serve *behind*
    the integrated code), confirm it, and report only what you observed. Keep
    the states distinct in words: **wired / defined / rendered ≠ has a real
    value**; "queryable" ≠ "query written"; "the code path exists" ≠ "it was
    proven to run" (principle 3's `UNVERIFIED`, stated for the liveness case;
    it is what G9 verifies against a deployed SHA).

## Principle 12 — a fork a ratified invariant already decides

12. **A fork a ratified invariant already decides is not an owner gate.** Before shaping a
    choice as a human gate, check whether a ratified invariant — no-data-loss, a security or
    accessibility floor, a monotonic-quality rule — already mandates the answer; if it does,
    applying it is a lane's **mechanical** job, and escalating spends an owner decision on a
    settled question while the lane stalls. Gate only the genuine forks the invariants leave open.
    Conversely, a change that would **reverse** a ratified invariant or decision is not a lane's
    mechanical call either — stop and queue it to the owner rather than silently applying it (the
    code-level instance — never loosening a ratified assert-absent test to ship a conflicting
    feature — is `deep-code-review`'s `testing-and-evals.md`).
