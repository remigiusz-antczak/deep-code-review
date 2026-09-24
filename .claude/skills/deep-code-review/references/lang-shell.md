# Shell / Bash red flags

Read this when the target runs any shell — CI `run:` steps, hooks, Dockerfile `RUN` lines, Makefile recipes, or shell scripts (reviewed code — the reviewer's own verification-shell hazards stay in the parent). Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.


- Unquoted expansions (`rm -rf $DIR`), `eval`, `curl … | bash`, parsing `ls`,
  missing `set -euo pipefail`, secrets in `set -x` traces, world-writable temp.
- `for x in $LIST` as a membership/exclusion check on an **unquoted** variable —
  bash word-splits it, zsh (default) does not, so a safety-critical skip/exclusion
  list silently stops excluding under the wrong shell. Use `case` or a line-based
  `grep -qxF`; full mechanism + the merge-guard instance:
  `merge-operations.md`.
- **`set -u` + `"${arr[@]}"` on an *empty* array is a fatal `unbound variable`
  under bash 3.2 — still macOS's default `/bin/bash` (verified `3.2.57`).** A
  script that conditionally builds an array (flags, a discovered file list,
  cleanup targets) and expands it under `set -u` aborts the instant the array is
  empty; this most often sits in **trap / cleanup / reporting** code on the error
  path, where it **masks the real failure** it was meant to report. Guard the
  expansion (`${arr[@]+"${arr[@]}"}`) or seed the array — and run the script
  against the **actual `/bin/bash` on the target**, since a dev box's
  newer/homebrew bash can behave differently and hide it.
- **A bracket *range* used to VALIDATE a character class — `case $x in *[!0-9a-f]*)`,
  `[[ $x =~ ^[0-9a-f]+$ ]]`, `grep '[0-9a-f]'` — is resolved against the locale's
  collating sequence, not codepoint order, so the *same* script returns a *different*
  verdict under a different `LC_COLLATE`.** POSIX defines a range expression as "the set
  of collating elements that fall between two elements in the collation sequence,
  inclusive" and warns that "in other locales" (than POSIX/C) "a range expression has
  unspecified behavior" (The Open Group Base Specifications, RE Bracket Expression). On
  an implementation that collates in dictionary order under a UTF-8 locale (GNU/glibc:
  `a A b B … z Z`), the uppercase letters sort *inside* `[a-f]`/`[a-z]`, so a guard meant
  to *reject* anything that is not lowercase hex (`*[!0-9a-f]*`) silently *accepts* an
  uppercase digest; under `LC_ALL=C` (byte order) the same guard is strict and rejects
  it. The leniency is a property of the **locale + collation data, not the OS** — a
  C/POSIX locale, or any libc that collates these ASCII ranges by codepoint, is strict,
  so do not key the risk to a platform ("macOS is lenient"); verify the target's
  `LC_ALL`/`LANG`. Consequence: a pre-commit hook that blocks every local commit on one
  developer's box while CI stays green, or the reverse — a lenient local pass a strict CI
  rejects — from a **byte-identical** script run in two locales. **Fix:** pin `LC_ALL=C`
  for the comparison, or drop the range for an explicit enumerated set
  (`*[!0123456789abcdef]*`); a POSIX named class (`[[:xdigit:]]`, `[[:lower:]]`) reads the
  intent but is itself locale-scoped, so a security/gate comparison should still pin
  `LC_ALL=C`. **Grep lead:** a bracket *range* (`[a-f]`, `[0-9a-f]`, `[A-Z]`, `[a-z]`)
  inside a `case` / `[[ =~ ]]` / `grep` used as a validity check with no `LC_ALL=C` in
  scope — read whether the compared value can carry the boundary case (uppercase where
  lowercase is meant). **Discriminator vs the gate-divergence family:** the *drifted local
  gate copy* false-green (`merge-operations.md` § "Self-reported evidence is not a
  trusted control") is two scripts that **differ** — a stale vendored paste behind the CI
  definition — fixed by *single-sourcing* the logic; here the script is single-sourced and
  **byte-identical**, and single-sourcing does **not** fix it: only pinning `LC_ALL=C` (or
  an explicit set) stops one file being read two ways. Distinct too from the
  changed-files / fetch-by-ref detective control and the extension-allow-list
  under-coverage gate in `reliability-error-handling.md` (which turn on *which* input the
  gate sees, not on how one input is interpreted), and from the application-text collation
  rules in `i18n-l10n.md` (sorting / case-folding *user data* for display — this is
  collation inside a *gate's control flow*).
- **A script that gates on another tool's log, not its exit status.** Gate on
  the tool's exit status, captured to a file — never a pipe (pipe-hides-exit-code
  hazard: `language-stack-redflags.md`'s verification-shell section); the
  mechanized form is `templates/pre-push-verify.sh`, which decides only on the
  captured command's exit code and never greps a log. If a log must still be
  parsed, anchor on the runner's own summary line, copied from a **real passing
  run** — never written from memory: a bare `PASSED`/`FAILED` word also matches
  test *names*, so a failing run can quote a green test's name as its evidence.
  Dry-run the check against one known-green and one known-red log before it
  runs unattended. The last line is an explicit positive result; its absence is
  failure.
