# Next.js App Router footguns

Read this when `next` is a dependency (probe: `grep '"next"' package.json`) and the code uses the App Router (`app/`).

- **Every `"use server"` export is a public POST endpoint**, callable with arbitrary arguments regardless of where it
  is imported. The auth and authorization guard must be the first statement in the action, and inputs must be
  validated inside it. A guard only in the calling component or layout is not a guard.
- **`cookies().set` during render throws.** Cookies can be written only in server actions and route handlers
  (and middleware/proxy). A set in a Server Component or layout is a runtime error on that path.
- **React `cache()` is per request**, not a cross-request cache; do not rely on it for rate limiting, memoizing
  secrets, or sharing data between users. Cross-request caching is `unstable_cache` / `use cache` with explicit keys
  and tags, and must never cache per-user data under a shared key.
- **`redirect()` and `notFound()` work by throwing.** Inside `try/catch` the catch swallows them; rethrow, or call
  them outside the `try`.
- **A page that suspends (Suspense) on slow data is cut by the proxy or platform timeout** and can render blank or partial with a
  200; bound each fetch with a timeout and give the boundary a fallback error state. See the latency-budget probe in
  `reliability-error-handling.md`.
