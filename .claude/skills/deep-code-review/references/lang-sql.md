# SQL / migrations red flags

Read this when the target contains SQL or schema/data migrations. Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.

## SQL / migrations

- String interpolation into SQL (see the per-language `lang-*.md` files).
- `SELECT *` in app code; missing `LIMIT`/pagination; query inside a loop (N+1).
- Migrations: `ALTER`/`CREATE INDEX` without `CONCURRENTLY` on a large table
  (locks writes; Postgres syntax — use the engine's online-DDL equivalent
  elsewhere); adding a `NOT NULL` column with no default; backfill in the same
  transaction as DDL; no rollback path. See `performance-db-cost.md`.
