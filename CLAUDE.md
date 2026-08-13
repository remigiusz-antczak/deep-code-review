# CLAUDE.md — working in this repository (AI-facing)

## What this is
This repo is a **single deliverable**: a universal, deep code-review skill.
The crown jewel is `.claude/skills/deep-code-review/SKILL.md`; its depth lives in
`.claude/skills/deep-code-review/references/*.md`. Everything else (`README.md`,
`install.sh`, `docs/standards-index.md`) supports distributing and trusting that
skill. There is no application to build and no runtime — the "product" is prose
that a human or an agent executes.

## How to work here
- **Edit the skill, not a copy of it.** The skill has exactly one home
  (`.claude/skills/deep-code-review/`). `install.sh` copies *from* there; never
  create a second copy anywhere in this repo.
- **No duplication — this is the repo's thesis.** The skill condemns duplicated
  logic; the repo must not contain a second copy of any checklist, principle, or
  definition. `SKILL.md` holds the map + concise checklists; each `references/`
  file holds depth `SKILL.md` doesn't. If you're tempted to restate a section,
  link to it instead.
- **Every reference file must be routed.** `SKILL.md` must name each
  `references/*.md` by path with an explicit "read this when…" trigger.
  Progressive disclosure only works if the parent routes to it; an unrouted
  reference is dead weight and fails review.
- **Verify before you cite.** Any standard, version, date, or list added to the
  skill or to `docs/standards-index.md` must come from a source you actually
  fetched this session. Record the URL + verification date in
  `docs/standards-index.md`. Anything you couldn't fetch goes in the by-name list
  **without** a URL. Never paste a remembered link.

## Definition of done (for a change here)
- The skill still reads as one coherent method; scope modes, report template, and
  the definition-of-done checklist stay internally consistent.
- Every `references/*.md` is routed from `SKILL.md`; every routed path exists.
- `bash -n install.sh` passes and `install.sh` still lands the skill with a
  `name:` matching the directory.
- `docs/standards-index.md` contains only URLs verified this session, each dated.
- The privacy/no-fabrication grep (below) is clean.

## Hard rules (never violate)
- **No fabrication.** No invented findings, data, sources, metrics, CWEs, dates,
  version numbers, or line numbers. If a source won't confirm it, omit it or mark
  it `unverified`. When two sources conflict, trust the authoritative one and
  make no claim you can't back.
- **Confidentiality / privacy.** No real names, company/team names, emails,
  internal IDs, hostnames, or identifying URLs anywhere — code, comments, docs,
  fixtures, commits, PR bodies, or git history. Fictional placeholders only
  (`Acme Capital`, `jane@example.com`, "the operator"). This repository is built
  partly from lessons mined out of private projects; those lessons are
  **generalized to their underlying principle** and stripped of every identifier.
- **Do no harm.** Any edit is net-positive across every axis (clarity, accuracy,
  coverage, consistency) and never regresses another. Respect the existing
  structure; propose a restructure as a decision, don't impose it.
- **Confirm before destructive/irreversible/shared-state actions** (force-push,
  history rewrite, deletes, external sends). Local reversible edits proceed.

## Pre-commit check (run before every commit)
```bash
# no accidental identifiers/secrets (tune the pattern to real risks; a hit is a
# lead to triage, not necessarily a secret — but never commit an uncleared hit)
grep -rInE 'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' . \
  --exclude-dir=.git && echo "BLOCK: potential secret" || echo "clean"
# every reference file is routed from SKILL.md
for f in .claude/skills/deep-code-review/references/*.md; do
  grep -q "$(basename "$f")" .claude/skills/deep-code-review/SKILL.md \
    || echo "UNROUTED: $f"
done
```

## Adding or updating a reference file
1. Write depth that `SKILL.md` genuinely can't hold (procedures, payloads, greps,
   worked patterns) — not a restatement of the checklist.
2. Add a "Read this when…" line at the top.
3. Route it from the matching domain section in `SKILL.md`.
4. If it cites a standard, verify the source and log it in
   `docs/standards-index.md`.
