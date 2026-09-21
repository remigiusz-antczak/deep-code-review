# Infrastructure, IaC, containers & cloud review

Read this when the target ships Dockerfiles, Kubernetes manifests/Helm,
Terraform/Pulumi/CloudFormation, CI/CD workflows, serverless/FaaS functions with
queue/stream/table event-source triggers, or any cloud configuration.
Misconfiguration here is a common real-world breach cause tracked under the
named OWASP category (OWASP Top 10:2025 A02) and a supply-chain surface
(A03). Benchmark against the relevant **CIS Benchmarks**; adopt **SLSA** for
build provenance. Review the design against the cross-cloud **Well-Architected** pillars —
operational excellence, security, reliability, performance efficiency, cost optimization (and
sustainability where the platform tracks it) — and name **which pillar each finding serves**; a
design audited for only one pillar (usually security) with no reliability, cost, or
operational-excellence lens is itself the gap. Pillar sets differ and are revised per cloud — use
the common set, do not pin a count.

---

## Deploy-contract preflight (run first for a containerized/serverless target)

Cheap one-line checks that decide "Blocked" vs merely "changes-requested" — run
them before the domain audits, because they fail late and silently otherwise:

- **Lockfile ↔ install command.** If the build runs `npm ci` /
  `pip install --require-hashes` / `yarn --immutable`, the lockfile must be
  committed or the build hard-fails (`git ls-files | grep -E
  'package-lock|pnpm-lock|yarn.lock|poetry.lock|go.sum|Cargo.lock'`).
- **Entrypoint file mode.** `CMD ["./entrypoint.sh"]` with no exec bit never
  starts — check `git ls-files -s <entrypoint>` shows mode `100755`, or a
  `chmod +x` runs in the Dockerfile.
- **Build-time vs runtime data dependency.** A page/module that opens a DB or
  reads a runtime secret at **module/import scope** breaks a build-time prerender
  — it must defer to runtime (`export const dynamic = "force-dynamic"` or the
  framework's equivalent), or the build fails against a resource that doesn't
  exist yet.
- **Boot the documented-minimal config and hit the health/readiness path.** The
  configuration the README calls "minimal" must actually start and answer
  `/health` — a `set -e` entrypoint that aborts when an "optional" dependency is
  absent violates the deploy contract on the exact path the docs call optional.
- **A green health check is not proof the product works.** A process can boot
  cleanly and answer `/health` while still functionally empty or broken, when a
  feature depends on a step that runs **outside** the deploy pipeline entirely —
  a data backfill, a warehouse pull posted to an ingest endpoint, a webhook
  registration, a cache warm. For every dependency the running system reads at
  request time that the deploy/build step itself does **not** populate,
  confirm: (a) the deploy runbook names the out-of-band step as part of "how to
  deploy," not a separate undocumented ritual, and (b) it is followed by a
  **content-bearing** smoke check (does the expected data actually exist?), not
  only a liveness check (did the process start?). A dashboard that redeploys
  clean and returns 200 immediately, then shows nothing but empty states for
  hours because the data-populating script never ran, is exactly this failure —
  and a liveness-only health check cannot see it, because it was never asked to
  look.
- **Deploy artifact size is a budget — externalize heavy, slow-changing assets.**
  A deploy upload can be **silently rejected** past a size limit: the stream sends
  the full body, then dies at the gateway's timeout with an HTTP/2 framing error or a bare `504`
  (no response body), while the app keeps serving the **old** pod — "the latest
  deploy didn't ship," and a build-logs view that shows only the last *successful*
  build hides the failed one. Treat artifact size as a first-class budget and flag
  growth past the last-known-good by a large factor; serve media from object
  storage / a CDN and fetch large data at runtime rather than baking either into
  the image (baking a large data bundle also couples data-freshness to a full
  redeploy). Bisect a suspected size rejection: a lean artifact lands where the
  heavy one fails.
- **A deploy upload's HTTP status is not the deploy's outcome.** On a platform
  that builds the image **synchronously inside the request**, every upload returns
  a `504` (or an HTTP/2 stream reset) at the gateway's timeout **whether the build
  later succeeds or fails** — so the status code is useless as a success/failure signal, and an agent
  that trusts it either abandons a good deploy or blindly re-uploads (a blind
  re-upload can hit a *"deploy already in progress"* `409` lock). Verify by the
  **effects**: a new build/deployment id, a booted pod/replica, a changed served
  version — that is the source of truth. Read the returned code before re-uploading
  (a `409` means wait; a timeout means it was likely accepted), and prefer a deploy
  API that returns a durable deployment id + async status over one that blocks on
  the build inside the gateway window.
- **Confirm promotion on a byte only the *new* build serves — never on `/health`.**
  A liveness endpoint both the old and new artifact answer cannot confirm a
  promotion: on a build-then-promote platform the **old** pod keeps returning
  `/health` = 200 throughout a slow build's `504`, so polling it "proves" a success
  that never happened (the old artifact answering). Pick a **discriminator** that
  differs between the artifacts and poll that — a static asset path the new build
  ships and the old lacked (`404` → `200` exactly when the new pod takes over), a
  build/commit id, a changed response header. A response byte only the new build can
  serve is the honest promotion signal (sharpens the effect-verification above:
  `/health` is an effect **both** builds produce).

---

## Containers (Docker / OCI)

- **Non-root**: an explicit `USER` (not root); read-only root filesystem where
  possible; drop all Linux capabilities and add back only what's needed;
  `no-new-privileges`.
- **No secrets in the image**: not in `ENV`, not in a `RUN` that bakes a token
  into a layer (layers are extractable even if later deleted), not in the build
  args left in history. Use build secrets / runtime secret mounts.
- **Pinned, minimal base**: pin the base image by **digest** (`@sha256:…`), not
  `:latest`; prefer minimal/distroless; multi-stage build so build tools don't
  ship. Scan the final image (Trivy/Grype) and generate an SBOM.
- **Resource limits**: memory/CPU limits so one container can't starve the host.
- **Healthcheck** present; no unnecessary ports exposed.

**🚩 grep**: `FROM …:latest`, no `USER `, `ENV .*(SECRET|TOKEN|KEY|PASSWORD)`,
`ADD http` (use `COPY`/verified download), `curl … | sh` in `RUN`, `--privileged`.

## Kubernetes

- **Pod security**: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`,
  `allowPrivilegeEscalation: false`, `privileged: false`, **drop `ALL`** capabilities then
  add back only what's needed — Pod Security Standards *Restricted* permits only
  `NET_BIND_SERVICE` back (see the Docker section above), a seccomp profile set to **`RuntimeDefault` or `Localhost`**
  (`Unconfined` or an **absent** profile is the finding); no
  `hostPath`/`hostNetwork`/`hostPID`/`hostIPC` unless justified.
- **Resource requests/limits** on every container; **liveness/readiness**
  probes.
- **Secrets** via a secret manager (External Secrets / CSI / KMS-encrypted), not
  plaintext `ConfigMap`; RBAC least-privilege (no wildcard `*` verbs/resources,
  no cluster-admin to app service accounts); **`automountServiceAccountToken: false`** on any
  ServiceAccount/Pod that never calls the API server — the token mounts **by default**, so an
  unused one is a free credential any in-pod RCE inherits (and being a *missing* field, no
  bad-value grep catches it — it must be asserted present-and-false); **NetworkPolicy**
  default-deny with explicit allows.
- Images pinned by digest; `imagePullPolicy` sane; admission control enforcing the above —
  the built-in **Pod Security Admission** (a `pod-security.kubernetes.io/enforce: restricted`
  namespace label — the free, zero-dependency way to make the *Baseline*/*Restricted* profile
  non-optional) and/or a policy engine (OPA-Gatekeeper/Kyverno) for rules beyond those profiles.

**🚩 grep**: `privileged: true`, `hostPath:`, `hostIPC: true`, `runAsUser: 0`, `seccompProfile: Unconfined`, `verbs: ["*"]`,
`kind: ClusterRoleBinding` to `cluster-admin`, secrets in a `ConfigMap`.

## Serverless functions & event-source triggers

Read this when the target ships FaaS functions (Lambda, Cloud Functions, Azure
Functions) invoked by a queue, stream, or table trigger wired up in IaC
(Terraform/SAM/CDK/Serverless Framework).

- **Recursive event-source invocation has no call stack — trace the resource
  graph, not the function body.** A function whose output (a write, a republish)
  targets the same resource that triggers it — directly, or transitively through
  a chain of resources — is a self-amplifying invocation loop: each invocation
  causes another, with no call stack and no depth counter, so a generic
  recursion-depth cap does not apply. The cycle is invisible to a review that
  only reads the function's source, because it lives in a **separate resource's
  trigger wiring in IaC** (the event-source-mapping / trigger block between the
  function and its trigger) — a different file, sometimes a different team's
  resource, from the function that looks like the whole story. Left unbroken
  it's a cost/concurrency incident, not merely a logic bug: unintentional loops
  can bill unexpected charges and use all of an account's available concurrency.
  Review action: draw the resource→trigger graph (function → its output target →
  whatever triggers a function from that target) and check for a cycle,
  including a transitive one (function A writes to table T; T's stream triggers
  function B; B writes back to T). Name the platform's actual detection boundary
  rather than assuming protection exists — e.g. AWS Lambda ships on-by-default
  recursive-loop detection (via AWS X-Ray tracing metadata, and only for a
  function built on a supported AWS SDK — a function on an unsupported SDK or
  runtime gets none of it) that currently covers loops between functions, Amazon
  SQS, Amazon S3, and Amazon SNS, stopping the chain at roughly its 16th hop —
  but when another service such as DynamoDB forms part of the loop, Lambda can't
  currently detect or stop it, so the loop runs unchecked until something else (a
  spend alarm, a manual kill) does. Break a confirmed cycle by routing the derived
  write to a resource the trigger ignores (a separate table/attribute), filtering
  the trigger on a system-authored marker so the function's own writes don't
  re-trigger it, or computing the value on read instead of writing it back.
  Cross-ref `domain-checklists.md` §W (topology).

**🚩 grep**: a function's write/publish target is also configured as a trigger
source for the same function or an upstream one — check the event-source-mapping
/ trigger block in the IaC template (Terraform `aws_lambda_event_source_mapping`,
a stream/queue trigger in SAM/CDK/Serverless Framework), not the function's own
source, which never shows the cycle.

## Terraform / IaC

- **Least-privilege IAM**: no `"*"` actions or `"*"` resources; no wildcard
  principals; scoped, named roles. No admin/`Owner` handed to a service.
- **A grant needs a lifecycle, not just correct scope at creation.** An IAM binding, DB grant, or service-account key that is correctly least-privilege **at grant time** but carries no expiry/condition, no owner annotation, and no link to a deprovisioning path (an offboarding hook, a periodic reconciliation against the IdP roster) becomes standing access nothing ever revisits or revokes — the *time* axis, distinct from grant-time scope. NIST SP 800-53 **AC-2** requires accounts be reviewed "for compliance with account management requirements," account managers notified "when users are terminated or transferred," and account management "align[ed] ... with personnel termination and transfer processes." Flag an IaC grant with no expiry/owner/deprovision linkage (AC-2 is an org process control; the reviewable diff artifact is the ungoverned grant — pair it with the AC-5 SoD note in `security-appsec.md`).
- **Network exposure**: no security group / firewall rule open to `0.0.0.0/0`
  (or `::/0`) on sensitive ports (SSH 22, RDP 3389, DB ports, admin panels);
  ingress justified and narrow.
- **Storage**: buckets/blob **not public**; encryption at rest **and** in
  transit enforced; versioning + access logging on sensitive stores; public-access
  block on.
- **State**: remote state is encrypted, access-controlled, and locked; **no
  secrets in state or in `.tf` files** — use a secret manager and mark
  variables `sensitive`. State files often contain plaintext secrets — treat
  them as secret material.
- **Review the plan**: destructive changes (`-/+` replace, `destroy`) are
  read and approved; drift is detected; `prevent_destroy` on stateful/critical
  resources.
- Scan IaC (tfsec/Checkov/KICS) in CI.

**🚩 grep**: `0.0.0.0/0`, `"Action": "*"`, `"Principal": "*"`,
`acl = "public-read"`, `publicly_accessible = true`, `force_destroy = true`,
hard-coded `access_key`/`secret`/`password` in `.tf`.

## CI/CD & supply chain

- Third-party CI actions pinned to a **commit SHA**, not a mutable tag
  (`@v3`/`@main`); auto-updated by a bot that passes the same gates.
- Secrets injected from the CI secret store, **never** echoed in logs
  (`set -x` leaks; mask them); least-privilege CI tokens (a read-only checkout
  where a write isn't needed); protected branches; required status checks.
- **Harden the pipeline *system* itself, not only the app it ships.** The bullets
  around this one secure the code and artifacts flowing *through* the pipeline; this
  one secures the CI/CD system's own runtime posture — the axis OWASP CI/CD Top 10
  **CICD-SEC-7** ("Insecure System Configuration") frames as the "posture and resilience
  of each individual system," and whose own examples include a "self-hosted system that
  has administrative permissions on the underlying OS." Repo-visible signal:
  **`runs-on: self-hosted`** (or any custom label targeting a machine the team runs
  itself). A *persistent* runner reused across jobs carries state between runs —
  environment, the tool-cache, on-disk secrets and credentials, and the prior checkout
  all survive — so an untrusted/fork-PR job that lands on the same runner as a privileged
  job can **read the residue** the privileged job left, or **poison** a cache/tool the
  *next* privileged run consumes (a fork `pull_request` job runs the contributor's code
  even when repo secrets are withheld from it; residue-harvest and cache-poisoning defeat
  that withholding). Prescribe — skill guidance, beyond the OWASP text — **ephemeral,
  single-job runners** torn down after each run, and **never co-schedule untrusted/fork
  PRs on a runner that also serves privileged jobs**; segregate runner pools by trust
  tier. "CI is green and the runners are fast" is not evidence of isolation. Same
  principle, briefly: the CI server's own patch level, unvetted plugins, default-admin
  credentials, and network segmentation between runners and production — all "harden the
  system, not only the app." Keep the finding to what the diff shows (`runs-on`, the
  trust-tier mix across workflows); org runner-group configuration and vendor patching
  live in platform admin, so surface the signal and route the rest. Distinct axes: this
  bounds *where* a job runs; the least-privilege-token bullet above bounds *what* it may
  reach; CIS hardening of the *deployed* app runtime is the separate axis at this file's
  opening (and `security-appsec.md` A05). Untrusted fork-PR **checkout/trigger** risk
  (`pull_request_target`, script injection) is in `security-appsec.md`.
- **Package-signature verification is a blocking gate** (a signature mismatch
  means the artifact is not what the registry signed); transitive-CVE audit is a
  useful **advisory** signal — schedule high/critical, don't block on every
  transitive finding.
- Build provenance/attestation (SLSA) for released artifacts, and the deploy step
  **verifies it as a blocking gate** — subject digest matches the artifact, signer/builder
  trusted, canonical source repo matches, fail closed on a missing/mismatched attestation
  (the same bar as package-signature verification above; a named SLSA level, not a bare
  "SLSA compliant" — depth in
  `security-appsec.md` A03); SBOM published.
- **Verify identifier ownership before deploy**: deploying under a slug /
  app-id / project name another service already owns can silently clobber it.
- A credentialed integration must degrade to a clean no-op without its key
  (a fresh clone and CI both build and run); missing config fails **loudly** at
  startup, never silently mis-behaves.

---

Cross-references: A02/A03 detail in `security-appsec.md`; secret handling in
section N of `SKILL.md` (and M for log-leakage); spend/egress control in
`performance-db-cost.md`.
