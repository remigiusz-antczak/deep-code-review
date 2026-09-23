# Domain N checklist

Read this when domain N (Configuration, secrets & environments) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### N. Configuration, secrets & environments
- All config via env/secret-manager with a committed, secret-free `.env.example`;
  missing config fails **loudly** at startup. Sensible safe defaults; dev/staging/
  prod separation. Files that *functionally* need real values (allowlists, seeds)
  are gitignored and loaded at runtime; a missing file degrades to a clean no-op,
  never a crash or a fabricated result.
- 🚩 committed secrets, hard-coded config paths, prod behavior depending on an
  undocumented value, a silent default that masks misconfiguration.
