# ADR template

Routed from G3 (`SKILL.md`: "ADRs / contracts... data/security decisions
explicit"). G3 has always required an ADR as *output*; this is the shape,
so a Design gate has something concrete to produce rather than a prose
promise. Nygard's original five-part shape (Title, Context, Decision,
Status, Consequences), with MADR's optional sections folded in — the first
three sections are the core; the rest are removable.

```markdown
# ADR-<NNN>: <short noun phrase — e.g. "Use Postgres row-level security for tenant isolation">

Status: `proposed` | `accepted` | `deprecated` | `superseded by ADR-<NNN>`
Date: <YYYY-MM-DD>

## Context and problem statement

<The forces at play — technological, business, team — stated neutrally, as
if narrating them to someone with no stake in the outcome. This is not the
place to argue for the decision; that's the next section.>

## Decision drivers *(optional — delete if not useful)*

- <driver 1, e.g. "must not require a schema migration during business hours">
- <driver 2>

## Considered options

- <option A>
- <option B>
- <option C — "do nothing" is a real option, include it>

## Decision outcome

We will <full sentence, active voice, "We will…">, because <the deciding
driver(s) from above>.

### Consequences *(all of them — not just the good ones)*

- Good: <…>
- Bad / accepted cost: <…>
- Neutral / just different: <…>

### Confirmation *(optional)* — how we'll know this decision actually held

<the check, test, or metric that would catch drift from this decision>

## Pros and cons of the options *(optional — expand only if the outcome needs defending later)*

### <Option A>

- Good, because <…>
- Bad, because <…>

---
ADRs are numbered sequentially, never reused, never edited after acceptance —
a changed decision gets a new ADR that marks this one `superseded by`.
One or two pages. Lives in version control next to the code it governs.
```

## Gate, trigger, planted-defect test

- **Gate:** a change the Architect hat already flags as needing a decision
  record (`roles.md`: "new surface, data model, or cross-cutting change") has
  an ADR whose Decision Outcome is a real "We will…" sentence, not a
  placeholder. **Trigger:** G3, only for the blast radius `roles.md` already
  uses to decide the Architect hat fires — never a routine change. **Owning
  hat:** Architect.
- **Planted-defect test:** an ADR whose Decision Outcome reads "TBD" → the
  gate flags it.
