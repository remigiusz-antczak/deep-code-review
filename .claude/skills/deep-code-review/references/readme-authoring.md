# Authoring a README that onboards — the human front door

**Read this when** writing or reviewing a project's README so a newcomer — a
non-technical evaluator *and* a skeptical engineer — can understand it, trust it,
and adopt it. This is the depth behind the "README (human-facing)" checklist in
`docs-and-dx.md`: that section holds the non-negotiables (BLUF, a diagram,
one-command setup, explicit status, never bake live metrics); this holds the
method for turning them into a page people actually onboard from.

## Model the reader first (default: the evaluator)

A public README's primary reader is usually deciding *whether to adopt*, not
already installing. Build for evaluation, with install as the clear next step.
Name the personas the project **actually** has — never invent segments to pad —
and give each a "start here" pointer. Two archetypes almost always coexist and
pull opposite ways; serve both:

- **the non-technical evaluator** (founder / lead): wants the outcome, the
  plain-language value, and which decisions land on them — not the internals;
- **the skeptical engineer**: wants evidence it is real — accuracy, depth, and
  proof it is not marketing.

The arc below serves both by ordering plain value first and **demoting** depth,
never deleting it.

## The onboarding arc (progressive disclosure)

Order the page as a decision funnel; each section answers the next question the
reader has:

1. **Hero** — the name, one line of what it is, and the value. No preamble.
2. **Who it's for** — a short persona table with a "start here" column.
3. **The problem** — concrete failures stated as plain consequences, not only
   jargon: an engineer sees the real terms, a founder sees the cost.
4. **What you get** — outcomes, not a feature list; what is different after
   adopting, and briefly what it does **not** do (scope / non-goals — the first
   thing a skeptic checks, and the cheapest way to prevent mis-adoption).
5. **What's in the box** — one diagram + one table. The map, not the manual.
6. **Quickstart** — the one correct path (see *Keep the safe path the default*).
7. **How it works** — the mechanism, briefly.
8. **Depth & where next** — everything a skeptic needs, in `<details>` or lower
   sections, and the front-door links surfaced (contribute, get help, report a
   vulnerability, license) so the reader knows where to go. Never blocks the funnel.

## Visuals (host-native, and verified per host)

- **One diagram that earns its place**, not three competing for the same
  attention. An overview or a lifecycle journey onboards better than an internals
  diagram.
- **Render with what the target host supports — and verify per host.** Mermaid,
  tables, `<details>`, and alert callouts (`> [!NOTE]`) are host-specific: alert
  callouts are GitHub's, and Mermaid and raw HTML are stripped or left unrendered
  on package-registry pages (npm, PyPI, crates.io), where the same README is
  republished to a host the author didn't choose. Check each feature on **every**
  host the README ships to, not just the repo host. Where Mermaid does render,
  **quote every node label** and avoid `<b>` tags (raw HTML in labels is not
  guaranteed); `<br/>` is safe.
- **Give every diagram a text alternative.** A fenced Mermaid block has no `alt`
  attribute, so an adjacent prose or table restatement is the only accessible
  path — make the arc's "one table" that fallback, and say so. Also: meaningful
  link text (never "click here") and correct heading order. The skill owns
  accessibility (domain P); the README is not exempt.
- **Show it working.** For a CLI or UI, an output sample onboards faster than
  prose — but a pasted transcript embeds a version, a path, and a count and rots
  exactly as prose does; prefer a regenerable or clearly-captioned capture, under
  the accuracy rule below.
- **No external badges.** A badge is a third-party fetch on every page view: it
  leaks the reader's IP and referrer to the badge host (a privacy surface, domain
  Q) and the README degrades when that host is down or moves. Link the releases /
  changelog instead.

## Say it without slop

"Professional and exciting" comes from clarity and real outcomes, never from
adjectives. Apply the no-slop output rule — the `communication-structure` overlay
— to the README too; the craft specific to a README:

- Cut every empty superlative (*revolutionary, seamless, best-in-class,
  cutting-edge*) — show the outcome instead.
- One idea per line; kill a repeated structural pattern — the same sentence shape
  eight times is slop; use a table.
- Do not characterize products you do not control; attribute (link) or drop.

## Accuracy is the trust (an inaccurate README is worse than a plain one)

- **Every command, flag, and claim matches the code.** Diff the README's flags
  against the installer / CLI; a flag the tool does not have — or an install
  command that silently does something else — destroys an engineer's trust on the
  spot.
- **Verify the command does what you say.** Confirm, for example, that a
  package-manager shorthand actually supports the version pin you tell the reader
  to use; if it cannot, do not ship it as the safe path.

(Keeping live values out of prose is a parent non-negotiable — see the README
checklist and the persisted-knowledge-hygiene section in `docs-and-dx.md`: store
the query, not the answer.)

## Keep the safe path the default

If the install carries a security discipline — pin a release tag, verify
checksums, do not pipe an unsigned `HEAD` to a shell — then the **secure path is
the quickstart**, never a friendlier-but-unsafe shortcut placed first. A
quickstart that trades the project's own supply-chain rule for a shorter command
is a finding. Offer the portable form of a command (e.g. `shasum -a 256 -c`
alongside `sha256sum -c`) so a less-technical reader on any OS is not stranded on
the one security step. And surface a genuine trust guarantee the tool provides —
local-only, reversible, backs up before overwriting — where the reader asks for
it, in the quickstart.

## Review checklist

- [ ] Reader modelled; personas real (not invented), each with a "start here".
- [ ] Arc runs plain-value-first (incl. scope / non-goals); depth demoted to
      `<details>` / lower sections; front-door links surfaced (contribute, help,
      security, license).
- [ ] One diagram that earns its place, every label quoted, with a text/table
      alternative beside it; no external badges.
- [ ] No empty superlatives; no repeated pattern a table would replace; no
      uncontrolled third-party claims.
- [ ] Every command / flag / claim verified against the code; the safe install
      path is the quickstart.
- [ ] Host-specific features verified on every host the README ships to; in-page
      anchors resolve; each diagram renders or has a fallback on each host.
