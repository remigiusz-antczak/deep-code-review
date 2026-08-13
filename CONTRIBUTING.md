# Contributing

Thanks for improving the deep code-review skill. The engineering standards, the
definition of done, and the hard rules for this repository live in
**[`CLAUDE.md`](CLAUDE.md)** — it is the single source of truth and governs every
change. Read it first; the essentials are only summarized here.

## The essentials

- **One deliverable, one home.** The skill lives only in
  `.claude/skills/deep-code-review/`. Never create a second copy — `install.sh`
  copies *from* there.
- **No duplication.** `SKILL.md` holds the map and the concise checklists; each
  `references/*.md` holds the depth `SKILL.md` doesn't. Link, don't restate — and
  every reference must be routed from `SKILL.md`.
- **Verify before you cite.** Any standard, version, or date added to the skill or
  to `docs/standards-index.md` must come from a source you fetched, recorded with
  its URL and verification date. Never paste a remembered link.
- **No fabrication, no private data.** See `CLAUDE.md` for the hard confidentiality
  and no-fabrication rules; they apply to code, comments, docs, commits, and git
  history.

## Before you open a PR

Run the same gates CI runs ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)):

```bash
# every reference is routed from SKILL.md
for f in .claude/skills/deep-code-review/references/*.md; do
  grep -q "$(basename "$f")" .claude/skills/deep-code-review/SKILL.md \
    || echo "UNROUTED: $f"
done
bash -n install.sh   # the install script parses
```

Green gates, the definition of done in `CLAUDE.md` satisfied, and a one-line note
of what you verified in the PR body.
