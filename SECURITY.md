# Security policy

This repository is a **documentation artifact** — a code-review *skill* written in
Markdown. It ships no runtime service, no server, and no secrets; the only
executable is `install.sh`, a local, network-free file-copy script.

## Reporting a concern

Please report privately via GitHub's **"Report a vulnerability"** button
(the repository's **Security → Advisories** tab) rather than opening a public
issue. In scope:

- a defect in `install.sh` (for example, a path it could clobber or an unsafe
  write);
- text in the skill that would lead a reviewer to a harmful or incorrect action;
- a privacy slip — any real name, secret, or internal identifier that reached a
  committed file or the git history (see the confidentiality rules in
  [`CLAUDE.md`](CLAUDE.md)).

**Out of scope:** findings about a *project you reviewed using this skill* — take
those to that project, not here.

We aim to acknowledge a report within a few days and to fix or explain it
promptly.
