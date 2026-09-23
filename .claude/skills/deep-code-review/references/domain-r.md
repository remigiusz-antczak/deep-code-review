# Domain R checklist

Read this when domain R (Internationalization, encoding & localization) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### R. Internationalization, encoding & localization → depth: `references/i18n-l10n.md`
- No hardcoded user-facing strings; locale-aware formatting, sort/collation, and
  pluralization; **Unicode normalization (NFC)** at boundaries — a NFC/NFD or
  casing difference silently splits or merges dedup/join keys (cross-ref D);
  encoding declared and consistent (UTF-8); timezone display vs. UTC storage
  (cross-ref A).
- 🚩 concatenated translated fragments, `.sort()` on localized text without a
  collator, unnormalized text as a key, `latin-1`/mojibake at an I/O boundary.
