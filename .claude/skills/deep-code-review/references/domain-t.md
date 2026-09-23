# Domain T checklist

Read this when domain T (Multi-tenancy & isolation) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### T. Multi-tenancy & isolation
Apply when one deployment serves multiple tenants (customers, orgs, workspaces)
from shared infrastructure. **N/A by scope** on a single-tenant app or a personal
CLI. Distinct from **B/A01**, which owns whether *this request* is authorized for
*this object* (IDOR, missing authz), and from **G**, which owns races on shared
mutable state — **T owns whether the tenant boundary holds across shared
infrastructure**. Its distinctive leaks occur *even when the request-level authz
gate passes and no race exists* — a cache or index keyed without the tenant,
context bleeding between requests — because a shared component, not the request
handler, forgot the tenant. A missing tenant *predicate* on a query shares the
defect class with **B/A01** (data-level access control); what T owns there is the
**systemic** fix — scoping enforced in one place, not re-typed per caller.
- **Every tenant-scoped query carries the tenant predicate — enforced in one
  place, not remembered per caller.** A `WHERE tenant_id = ?` re-typed at each call
  site is one forgotten clause away from a full-table cross-tenant read; push it
  into row-level security, a session variable the DB enforces, or a scoped
  repository/query builder that **fails closed when the scope is absent**. The
  classic breach is a missing tenant filter on a **background job, admin, export,
  or report path** — the routes nobody views by hand (cross-ref B/A01, W jobs).
- **Cache, index and derived-store keys include the tenant.** A cache key, memo,
  search index, vector namespace, materialized view, or rate-limit bucket keyed
  *without* the tenant id serves one tenant's data to another **on a hit** — and
  the authz layer never runs, so B's checks never see the request. This is the
  leak that survives a perfect access-control review.
- **Per-request tenant context does not outlive its request** (cross-ref G,
  lifetime): a tenant id cached on a singleton, thread-local, module global, or a
  connection handed back to a cross-tenant pool bleeds into the next tenant's
  request **even with perfect locking**. Reset or thread the tenant per unit of
  work; never derive it from anything but the authenticated principal.
- **The isolation model is explicit and matches the data's sensitivity**:
  shared-row (RLS), shared-schema, or database/silo-per-tenant — each trades blast
  radius against cost; name which one is in use and why. Where a tenant is promised
  its own encryption key or data residency, a shared-pool default silently
  violates it (cross-ref Q privacy, L infra).
- **Noisy-neighbour fairness**: one tenant's request rate, query cost, or job
  volume must not starve the rest — per-tenant quotas/limits and bounded work per
  tenant (cross-ref E cost, W jobs).
- **Cross-tenant lifecycle is complete**: tenant export and deletion cover *every*
  store — primary, cache, search index, blobs, logs, backups; a half-deleted
  tenant is both a privacy breach (Q) and a future cross-tenant leak.
- 🚩 a tenant-scoped table queried with no tenant predicate on any path (job,
  admin, export, report); a cache/index/rate-limit key missing the tenant id;
  tenant context on a singleton/thread-local/pooled connection; an admin "see
  everything" query reachable by a tenant principal; per-tenant deletion that
  skips the cache/index/backups.
