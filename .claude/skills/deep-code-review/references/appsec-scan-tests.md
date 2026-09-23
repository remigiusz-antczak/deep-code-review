# Application security depth — completeness of security inventory tests

Read this when the target ships a regression or inventory test that scans every route, handler, or migration and asserts a security property (auth is checked, input is validated, a credential is refused). Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A01:2025 — Broken Access Control (depth: inventory-test completeness)

- **An automated "scan every X, assert property P" inventory/regression test is only as complete as how it *recognizes* X — a source-text pattern match silently under-covers a file written in an equivalent, unrecognized syntax.**
  Enumerating every route/handler/migration by hand (`security-appsec.md` A01) is the reviewer's own sweep. When the
  **codebase itself** ships an automated version of that sweep — a regression test scanning every route file,
  migration, or handler registration and asserting a security property (auth is checked, input is validated, a
  credential is refused) — the test's completeness depends entirely on how its scan recognizes the construct. A scan
  built as a **string / regex / brace-paren-balancing match for one specific literal spelling** of the construct,
  rather than a parse against the language's real AST / compiler API / exported-symbol table, finds **zero** matches
  in any file expressing the identical, runtime-equivalent construct in a *different* syntactically valid form — the
  assertion loop has nothing to iterate over for that file and reports **nothing, not a failure**: the suite stays
  green while the property goes completely unchecked there. Concretely (generalizes past this one framework): a
  Next.js inventory test finding "every mutating route handler" by grepping the literal substring
  `export async function POST(` silently skips every handler written as `export const POST = async (request) => {...}`
  — equally valid, identical at runtime, invisible to the scan; a brand-new such handler with zero auth checks ships
  under a fully green suite. The test's own docstring typically overclaims a guarantee the mechanism cannot deliver
  ("every route is covered by construction"), because the author reasoned about the one convention true across the
  codebase the day it was written, not every syntactically valid way the language/framework can express the same
  behavior — the completeness claim is itself untested. **Detect:** is the scan pattern-based rather than an
  AST/compiler-API symbol lookup; does the language/framework offer more than one valid spelling of the construct; and
  — the decisive check — does the test's own fixture set include a
  **negative case written in an alternate-but-valid syntax**, property deliberately absent, asserted to be caught?
  Absent that fixture, the completeness is asserted in a comment, not proven. **Fix:** parse with the language's real
  compiler/AST API and check exported names / bound values regardless of declaration form (frequently already a
  project dependency); where a full parse is impractical, broaden the pattern to cover every currently-known
  equivalent spelling **and** add one regression fixture per alternate form, so the completeness claim is itself under
  test. **Distinct from** `reliability-error-handling.md`'s extension-allow-list gate gap (that under-covers by
  **which files** enter the scan at all — a file-selection axis, fixed by `git ls-files`): this under-covers
  **inside** an already-scanned file, by which **syntactic spelling** of the target construct the pattern recognizes —
  the file has the right extension and is read, the construct inside it just doesn't match. Also distinct from the
  href-transform test-symmetry heuristic in `appsec-links.md` (A05): that finds a **sibling function** an audit never reached; here
  there is exactly **one** scanner, defeated by **one file** written in a different dialect of the same construct it
  already knows how to check. **🚩** an inventory/regression test whose comment or docstring claims "every X is
  covered" while its own scan is a literal string/regex/brace match for a single syntax form, with no fixture proving
  an alternate-syntax negative case is caught.
