# devora-security-ci

**One security pipeline for every Devora repo — mobile, backend, frontend.**

Add ~30 lines to any project and every pull request gets scanned for secrets,
vulnerable dependencies, insecure code, and mobile-specific issues — with a
single **Security gate** verdict and a summary table posted on the PR. Rules
live here, centrally: update once, every project picks it up on its next run.

```
Project PR ──► detect stack ──► gitleaks (secrets, incl. git history)
                            ──► semgrep  (SAST, all languages)
                            ──► trivy    (dependency CVEs: pub/npm/composer)
                            ──► trivy    (Docker/IaC config)      [if Docker found]
                            ──► flutter  (analyze + OWASP M1/M2/M5/M9 + mobsfscan)  [if Flutter found]
                                     │
                                     ▼
                        ❌/✅ Security gate + PR comment table
```

Everything is free/open-source. Typical run: 3–6 minutes.

---

## One-time setup (10 minutes)

1. **Stamp your org name** into the workflow references:
   ```bash
   ./setup.sh <your-github-org-or-username>
   ```
2. **Create the repo on GitHub** named `devora-security-ci` under that org and
   push this folder to it (branch `main`).
3. **Allow other repos to use it.** Either make this repo **public** (it
   contains no client data — recommended, zero friction), or keep it private
   and enable: *Settings → Actions → General → Access →* **"Accessible from
   repositories owned by &lt;org&gt;"**. This setting is what lets private
   project repos call the reusable workflows and the OWASP action.
4. **Enable the Renovate app** on the org
   ([github.com/apps/renovate](https://github.com/apps/renovate)) — it reads
   `renovate.json` here and keeps the action SHA pins and the semgrep
   container digest updated weekly. Without it the pins go stale silently.

## Install in a project (2 minutes, any repo)

1. Copy `templates/security.yml` into the project as
   `.github/workflows/security.yml`.
2. Existing project with unknown backlog? Set `enforce: false` inside it.
3. Commit, push, open a PR — the gate appears as a check named
   **Security gate** with a table in the PR comments.
4. *(Optional, projects with staging)*: copy `templates/dast.yml` as
   `.github/workflows/dast.yml` and set the staging URL — weekly passive
   OWASP ZAP scan.
5. *(Recommended)*: branch protection on `main` → require the
   **Security gate** check to pass before merging.

## Rollout plan for existing projects

| Week | Action |
|---|---|
| 1 | Install with `enforce: false`. Read the report. No build breaks. |
| 1–2 | Fix the backlog: rotate any leaked secrets first, then HIGH/CRITICAL deps, then code findings. Use `docs/TRIAGE.md`. |
| 2 | Flip `enforce: true`. Add branch protection requiring the gate. |
| ongoing | Weekly scheduled run catches new CVEs even with no code changes. |

Start permissive, tighten fast, never loosen silently — a repo left on
`enforce: false` after two weeks is itself a finding.

## What blocks vs. what reports

**Blocks the merge:** any secret (gitleaks / OWASP M1), CRITICAL or HIGH
dependency CVEs (trivy), ERROR-severity SAST findings (semgrep / mobsfscan),
CRITICAL/HIGH OWASP M2/M5/M9 findings, CRITICAL/HIGH Docker misconfigs, and
any scanner that crashes (silence never equals pass).

**Reports only:** MEDIUM/LOW severities, WARNING/INFO rules, and
`flutter analyze` issues (unless `strict_flutter_analyze: true`).

False positives: see `docs/TRIAGE.md` — per-project allowlists
(`.gitleaks.toml`, `.trivyignore`, `.semgrepignore`) with written reasons,
never lowered thresholds.

## Inputs reference (`security-scan.yml`)

| Input | Default | Meaning |
|---|---|---|
| `enforce` | `true` | `false` = report-only mode (rollout week) |
| `severity` | `CRITICAL,HIGH` | Trivy severities that block the gate |
| `strict_flutter_analyze` | `false` | Make analyzer issues blocking |

`zap-baseline.yml`: `target_url` (required), `fail_on_findings` (default
`false`).

## Design decisions (why it works this way)

- **PR comment + job summary instead of the GitHub Security tab** — SARIF
  upload requires GitHub Advanced Security on private repos; PR comments are
  free and visible where the review happens. Raw reports are attached as
  workflow artifacts (`secscan-*`) on every run.
- **All scanners always run, one gate decides** — you see the complete
  picture in one run instead of fixing findings one failed job at a time.
- **A crashed scanner blocks** — a scan that didn't finish is not a pass.
- **Everything is pinned immutably** — all third-party actions are pinned to
  full commit SHAs (tags are mutable: the tj-actions/changed-files compromise
  stole secrets from thousands of pipelines via a re-pointed tag). The
  `semgrep/semgrep` container is pinned to a version + digest. Renovate
  (`renovate.json`) keeps SHA pins and the container digest updated weekly.
  The gitleaks binary is version-pinned **and** sha256-checksum-verified;
  bump it manually on monthly patch day — version and checksum together
  (Renovate deliberately does not touch it, a version bump without the
  matching checksum would fail every gate org-wide).

## Costs

All tools are free. GitHub Actions minutes on private repos: free tier is
2,000 min/month — a typical PR run here costs ~10–15 job-minutes, so roughly
130+ PR runs/month free. Public repos: unlimited.

## Repo layout

```
.github/workflows/security-scan.yml   the reusable pipeline (edit rules HERE)
.github/workflows/zap-baseline.yml    reusable weekly DAST
actions/owasp-flutter/                composite action: OWASP M1/M2/M5/M9 scanners
templates/                            files you copy into project repos
config/                               allowlist examples projects copy when needed
docs/TRIAGE.md                        what to do when the gate fails
setup.sh                              one-time org-name stamping
renovate.json                         keeps action SHA pins + container digest fresh
DEVORA_PROJECT_PLAYBOOK.md            full-lifecycle checklist — copy into every client repo
```

## Extending

- New scanner = new job in `security-scan.yml` that writes a
  `secscan/status-<name>.json` (`{"name", "blocking", "info", "note"}`) and
  uploads it as `secscan-<name>` — the gate picks it up automatically.
- Upgrade queue lives in `DEVORA_PROJECT_PLAYBOOK.md` → Appendix A
  ("do now" items were applied 2026-07). Next up: zizmor, harden-runner,
  osv-scanner, SBOM on release tags, `npm audit` / `composer audit` jobs;
  later: MobSF binary scan on release tags, authenticated ZAP, license
  compliance, container image scanning, OpenSSF Scorecard.
