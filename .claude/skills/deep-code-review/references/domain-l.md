# Domain L checklist

Read this when domain L (Infrastructure as code, containers & cloud) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### L. Infrastructure as code, containers & cloud → `references/infra-iac-containers.md`
Apply if the target ships Dockerfiles, K8s/Helm, Terraform/Pulumi/CloudFormation,
or cloud config. (OWASP A02/A03; benchmark against CIS.)
- Containers: non-root, pinned-by-digest minimal base, **no secrets in image
  layers/env/build-args**, resource limits, dropped capabilities. K8s: pod
  security context, RBAC least-privilege (no wildcard verbs), default-deny
  NetworkPolicy, secrets via a manager. Terraform: least-privilege IAM (no `*`
  actions/principals), no `0.0.0.0/0` to sensitive ports, no public buckets,
  encryption at rest+in transit, **no secrets in state or `.tf`** (state is
  secret material). Scan IaC in CI.
- 🚩 `FROM …:latest`, no `USER`, `privileged: true`, `hostPath`, `verbs:["*"]`,
  `0.0.0.0/0`, `"Action":"*"`, public-read ACL, secrets in `.tf`/state.
