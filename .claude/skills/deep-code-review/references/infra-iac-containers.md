# Infrastructure, IaC, containers & cloud review

Read this when the target ships Dockerfiles, Kubernetes manifests/Helm,
Terraform/Pulumi/CloudFormation, CI/CD workflows, or any cloud configuration.
Misconfiguration here is the highest-frequency real-world breach cause (OWASP
Top 10:2025 A02) and a supply-chain surface (A03). Benchmark against the
relevant **CIS Benchmarks**; adopt **SLSA** for build provenance.

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
  `allowPrivilegeEscalation: false`, `privileged: false`, dropped capabilities,
  a seccomp profile; no `hostPath`/`hostNetwork`/`hostPID` unless justified.
- **Resource requests/limits** on every container; **liveness/readiness**
  probes.
- **Secrets** via a secret manager (External Secrets / CSI / KMS-encrypted), not
  plaintext `ConfigMap`; RBAC least-privilege (no wildcard `*` verbs/resources,
  no cluster-admin to app service accounts); **NetworkPolicy** default-deny with
  explicit allows.
- Images pinned by digest; `imagePullPolicy` sane; admission control / policy
  (OPA-Gatekeeper/Kyverno) enforcing the above.

**🚩 grep**: `privileged: true`, `hostPath:`, `runAsUser: 0`, `verbs: ["*"]`,
`kind: ClusterRoleBinding` to `cluster-admin`, secrets in a `ConfigMap`.

## Terraform / IaC

- **Least-privilege IAM**: no `"*"` actions or `"*"` resources; no wildcard
  principals; scoped, named roles. No admin/`Owner` handed to a service.
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
- **Package-signature verification is a blocking gate** (a signature mismatch
  means the artifact is not what the registry signed); transitive-CVE audit is a
  useful **advisory** signal — schedule high/critical, don't block on every
  transitive finding.
- Build provenance/attestation (SLSA) for released artifacts; SBOM published.
- **Verify identifier ownership before deploy**: deploying under a slug /
  app-id / project name another service already owns can silently clobber it.
- A credentialed integration must degrade to a clean no-op without its key
  (a fresh clone and CI both build and run); missing config fails **loudly** at
  startup, never silently mis-behaves.

---

Cross-references: A02/A03 detail in `security-appsec.md`; secret handling in
section N of `SKILL.md` (and M for log-leakage); spend/egress control in
`performance-db-cost.md`.
