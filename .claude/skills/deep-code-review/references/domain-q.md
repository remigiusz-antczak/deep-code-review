# Domain Q checklist

Read this when domain Q (Privacy, compliance & licensing) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### Q. Privacy, compliance & licensing → `references/privacy-compliance.md`
Load the reference when the target stores, exports, or logs personal data, or when
a licence/regulatory obligation is in scope — retention/erasure procedures,
export-boundary suppression, and licence-compatibility detail live there.
- Only necessary personal data collected; retention/deletion honored; PII
  minimized in logs/analytics/traces; **suppression/erasure enforced once at the
  export/publish boundary** so all downstream inherits it. Dependency licenses
  compatible; attributions where required. Regulatory obligations (consent,
  data-subject rights) met where in scope.
- 🚩 PII in analytics events, GPL code in a permissive project, no retention
  story, tracking without consent, erasure reimplemented per-consumer, a
  committable artifact (PR body, doc, fixture, commit) carrying a real name,
  agent-instance name, or personal workflow when the repo's privacy gate
  forbids it.
