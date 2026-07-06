# Devora Project Playbook — Full-Lifecycle Checklist

**Copy this file into every new client project repo as `PROJECT_PLAYBOOK.md` and tick
it off. Nothing ships until every non-optional box in the active phase is checked.**

This is what separates a software house from a freelancer: the client doesn't get
"an app" — they get a running business setup. Accounts they own, environments that
don't fall over, monitoring that pages us before the client notices, a security
gate on every merge, and a handover so complete they could fire us and survive
(which is exactly why they won't).

**Ownership rule (applies to every account below):** the **client owns, Devora
administers**. Every account — Apple, Google Play, domain, hosting, Firebase,
payment gateway — is registered under the client's email/company identity, with
Devora added as admin/developer. No hostage accounts. Client pays vendor bills
directly. All credentials live in a per-client vault (Bitwarden/1Password
collection), never in chat, never in the repo.

---

## Phase 0 — Kickoff & Discovery

- [ ] Signed scope document exists (features in / features out, platforms, languages)
- [ ] Single client point-of-contact named, with decision authority
- [ ] Comms channel created (WhatsApp group / Slack) — all decisions confirmed in writing there
- [ ] Client vault created (Bitwarden/1Password collection: `client-<name>`)
- [ ] Client email identity confirmed for account registrations (company email, not a personal Gmail if avoidable)
- [ ] Repo created under Devora org, `main` protected from day one
- [ ] `PROJECT_PLAYBOOK.md` (this file) copied into repo root
- [ ] Project tier agreed and written here:
  - **Tier 1** — payments / PII / medical / gov → all security items mandatory, no severity exceptions
  - **Tier 2** — accounts + user data, no payments → standard gate
  - **Tier 3** — content/brochure apps → gate mandatory, DAST optional
- [ ] Cross-team contracts flow through handover docs in repo root (`BACKEND_REQUEST_*`, `TAMARA_*` pattern): request/response examples, edge-case table, acceptance criteria, QA checklist
- [ ] Discovery answered in writing: target markets, launch languages (default ar+en, RTL-first), payment providers, login methods, notification needs, offline needs, analytics events the client actually cares about

## Phase 1 — Accounts & Ownership Setup

Register in client's name, add Devora as admin. Record every credential + who owns
what in the vault, and mirror the ownership table into `HANDOVER.md` from day one.

**Stores & publishing**
- [ ] Apple Developer Program — client's D-U-N-S / company enrollment ($99/yr, takes days–weeks: **start at kickoff, not at launch**)
- [ ] Devora added to App Store Connect with Admin/Developer role (not shared password)
- [ ] Google Play Console — client account ($25 once), Devora added as developer/admin
- [ ] App identity reserved early: bundle id / application id (`com.<client>.<app>`), app name checked in both stores

**Infra & domains**
- [ ] Domain registered under client account (registrar login in vault); renewal auto-pay on client card
- [ ] DNS provider decided (Cloudflare recommended); Devora admin access
- [ ] Hosting/VPS provisioned (client-billed); SSH access via Devora team keys, root password in vault
- [ ] Transactional email (Resend/Mailgun/SES) on client domain — SPF, DKIM, DMARC verified
- [ ] SSL on every environment (Let's Encrypt auto-renew or CF proxy) — verified, not assumed

**Platform services**
- [ ] Firebase project under client's Google account, Devora as editor/owner-delegate
- [ ] Payment gateway onboarding started (Tamara / ARB / Stripe / etc.) — client entity, client bank; this has KYC lead time, **start in week 1**
- [ ] Push (FCM/APNs) keys generated and stored in vault
- [ ] Social/OAuth apps (Google, Apple, etc. sign-in) created under client identity

**Growth basics**
- [ ] Landing page domain/subdomain decided (`<app>.com` or `app.<client>.com`)
- [ ] Client social accounts created/collected for launch (even placeholders)
- [ ] App Store / Play Store listing draft started (ar + en): name, subtitle, keywords, description

## Phase 2 — Environments & CI/CD

- [ ] Three environments defined: `dev`, `staging`, `production` — separate backends, separate databases, separate Firebase apps (or at minimum separate projects for prod)
- [ ] Flutter env via `--dart-define=ENV=...`; **release builds default to production** (verify — we shipped a dev-pointing release once)
- [ ] No real secrets in bundled `.env.*` files — they are extractable from the binary
- [ ] Staging URL live and reachable before feature work starts (unblocks DAST + client demos)
- [ ] CI builds on every PR: analyze + tests + debug build
- [ ] CD: tagged release → signed build → store track (internal/TestFlight) automatically
- [ ] Android signing keystore generated, backed up in vault (**losing it = losing the app**), never committed
- [ ] iOS certs/profiles managed via App Store Connect API key (in CI secrets, not a person's laptop)
- [ ] Database backup job configured on prod (daily, off-server, restore **tested once** — an untested backup is a hope, not a backup)
- [ ] Uptime monitor on staging + prod endpoints (UptimeRobot/Better Stack) alerting to team channel

## Phase 3 — Engineering Standards (Flutter default stack)

- [ ] Clean Architecture (`data/` `domain/` `presentation/`) + GetX — or follow existing repo convention
- [ ] Single injected `ApiClient` (Dio) — never a second client instance
- [ ] Tokens/user data in `flutter_secure_storage`; `get_storage` only for non-sensitive prefs
- [ ] API caches cleared on login/logout
- [ ] Typed exceptions (`ApiException.isUnauthorized`) — never substring-match error messages
- [ ] No stubbed/faked success paths — backend not ready ⇒ `UnimplementedError`, fail visibly
- [ ] No `print` of tokens/OTP/PII — `debugPrint` gated by `kDebugMode`
- [ ] l10n: every key in **both** `.arb` files (ar+en), `flutter gen-l10n`, generated files never hand-edited
- [ ] Every new screen explicitly verified in Arabic RTL
- [ ] Payments: server is the only source of truth for "paid" — verify/poll endpoint, idempotency key, `payment_url` loaded verbatim, https only
- [ ] `copyWith` on entity subclasses overridden covariantly
- [ ] Dead code deleted, not commented out

## Phase 4 — Security Pipeline (mandatory, every repo)

- [ ] `templates/security.yml` from `devora-security-ci` installed as `.github/workflows/security.yml`
- [ ] New project → `enforce: true` from commit one. Existing project → `enforce: false` max **2 weeks** (rollout table in security-ci README), then flipped
- [ ] Branch protection on `main`: **Security gate** check required, PRs required, no force-push
- [ ] Staging exists → `templates/dast.yml` installed with staging URL (weekly ZAP baseline)
- [ ] Gitleaks pre-commit hook installed locally by every dev on the project (`gitleaks protect --staged`) — catching a secret pre-push beats rotating it post-push
- [ ] Any allowlist entry (`.gitleaks.toml`, `.trivyignore`, `.semgrepignore`) has a written reason + owner + review date (see `docs/TRIAGE.md`)
- [ ] Weekly scheduled scan verified running (catches new CVEs with zero code changes)
- [ ] Tier 1 projects: severity exceptions forbidden; MEDIUM fixed within the sprint

## Phase 5 — Observability & Support

- [ ] Crash reporting live: Firebase Crashlytics (or Sentry) — verified receiving a **test crash from a release build**, not just added to pubspec
- [ ] Analytics events wired for the funnel the client cares about (signup, activation, order/paid) — agreed list from Phase 0, not "track everything"
- [ ] Backend error tracking (Sentry/Laravel Telescope-equivalent on prod, PII-scrubbed)
- [ ] Uptime + SSL-expiry alerts → Devora team channel
- [ ] Alert routing decided: who gets paged, response-time promise written down
- [ ] Client support channel decided (WhatsApp Business / email) and connected to someone who answers
- [ ] Store review monitoring: bad reviews are incident reports — someone reads them weekly

## Phase 6 — Pre-Launch QA

- [ ] Full pass on real devices: small Android, flagship Android, iPhone (notch), tablet if supported
- [ ] Full pass in **Arabic RTL** — every screen, every new section (RTL is not free; the website needed 4 dir fix commits)
- [ ] Payment flow tested end-to-end on staging with gateway sandbox: success, failure, cancel, double-tap (idempotency), app-killed-mid-payment → server verify recovers state
- [ ] Login/logout/session-expiry paths tested; old-policy passwords still log in
- [ ] Offline / flaky-network behaviour acceptable (no crash, honest error states)
- [ ] Deep links / notifications tap-through tested cold-start and backgrounded
- [ ] Release build (not debug) smoke-tested — env points at production, no debug banners, no test endpoints
- [ ] Security gate green on the release branch; DAST report reviewed
- [ ] Store compliance pass: privacy policy URL live, data-safety forms (Play) + privacy nutrition labels (Apple) filled honestly, account-deletion flow exists (both stores require it)
- [ ] Store listings final in ar + en: screenshots (RTL screenshots for ar!), descriptions, keywords
- [ ] Client walkthrough done; written client acceptance on the release candidate

## Phase 7 — Launch

- [ ] Soft launch first: internal testing → closed track / TestFlight with client team
- [ ] Play: staged rollout (10% → 50% → 100%); Apple: phased release ON
- [ ] Launch-day watch: Crashlytics + uptime + gateway dashboard monitored actively for first 72h; crash-free rate target ≥ 99.5% before rollout expansion
- [ ] Rollback plan written before launch: halt staged rollout / previous AAB ready / backend feature flags
- [ ] Landing page live, social announced, store links verified
- [ ] First-week review: analytics vs the Phase 0 goals, shared with client

## Phase 8 — Handover

The deliverable is `HANDOVER.md` in the repo root + a filled client vault. Handover
is complete when the client could continue without us.

- [ ] Ownership table final: every account, who owns it, who has admin, billing card on file
- [ ] All credentials in client vault; vault ownership transferred/shared to client officially
- [ ] Signing keystore + store API keys delivered to client vault (with a "guard this with your life" note)
- [ ] `HANDOVER.md`: architecture overview, environments + URLs, how to build/release step-by-step, third-party services list with dashboards, known limitations
- [ ] Backend/API docs current (or handover doc per the `BACKEND_REQUEST_*` pattern)
- [ ] 1-hour recorded walkthrough session with client's technical contact (or owner)
- [ ] Renewals calendar handed over: Apple $99/yr, domain, hosting, SSL (if manual), gateway fees — with dates
- [ ] Written acceptance sign-off on the full scope checklist from Phase 0

## Phase 9 — Maintenance (the recurring revenue phase)

Every project leaves launch with a maintenance agreement — even minimal. "Call us
when it breaks" is freelancing; a retainer with SLAs is a company.

- [ ] Maintenance tier agreed and written: response SLA, monthly hours, what's included
- [ ] **Monthly patch day** on the calendar: dependency bumps, pinned-version reviews, allowlist expiry review, OS/store policy changes
- [ ] Weekly security scan results actually looked at (the cron run nobody reads doesn't exist)
- [ ] CVE response SLA: CRITICAL in production dependency → patched ≤ 72h (Tier 1: 24h)
- [ ] Store health check monthly: new policy requirements, target-API-level deadlines (Play raises it yearly), iOS SDK minimums
- [ ] Backup restore re-tested quarterly
- [ ] Quarterly client report: uptime, crash-free rate, work done, recommendations — this report is the sales pitch for the next phase of work

---

## Appendix A — Security Pipeline Upgrade Queue (from July 2026 review)

Current pipeline (gitleaks + semgrep + trivy fs/config + OWASP-Flutter + mobsfscan
+ ZAP, fail-safe gate) is a strong base. Upgrades, in priority order:

### Do now — ✅ applied to this repo 2026-07-07 (#1–#5; Renovate app still needs enabling on the org)
| # | Upgrade | Why |
|---|---|---|
| 1 | **Pin all actions to full commit SHAs** (not tags) in `security-scan.yml`, `zap-baseline.yml`, templates | Tags are mutable — the tj-actions/changed-files compromise exfiltrated secrets from thousands of pipelines via a re-pointed tag. A security pipeline is the worst possible place to trust a tag. |
| 2 | **Pin the `semgrep/semgrep` container to a digest** | README already flags it — it floats on `latest` today. |
| 3 | **Refresh pinned versions** (gitleaks v8.21.2, trivy-action v0.28.0, zap v0.12.0 are 2024-era), then keep them fresh via #4 | Old scanners miss new rules/CVE data. |
| 4 | **Renovate (or Dependabot) on the security-ci repo + all project repos** | Closes the loop: trivy *finds* vulnerable deps, Renovate *opens the fix PR*. Also keeps action SHA pins updated automatically — pinning without automation goes stale. |
| 5 | **Explicit least-privilege `permissions:` per job** in the reusable workflow (only `gate` needs `pull-requests: write`) | Limits blast radius of any compromised step. |

### Do next
| # | Upgrade | Why |
|---|---|---|
| 6 | **zizmor job** — static analysis of the workflow YAML itself | Catches template injection, dangerous triggers, unpinned actions in *our* workflows; cheap to run. |
| 7 | **StepSecurity harden-runner** step in each job | Egress monitoring on runners — this is what detected the tj-actions attack in the wild. Start in `audit` mode, move to `block`. |
| 8 | **osv-scanner job** | Google's OSV database is where Dart/pub security advisories actually live; complements trivy for pub.dev coverage. Emits the same `status-*.json` so the gate picks it up. |
| 9 | **SBOM generation** (`trivy sbom` → CycloneDX) uploaded as artifact on every release tag | When the next big CVE drops, query SBOMs to know which client apps are affected — instead of re-scanning every repo. Sets up Dependency-Track later. |
| 10 | **`composer audit` + `npm audit` jobs** (already queued in README) | Native audit output catches ecosystem advisories trivy occasionally lags on. |

### Do later
| # | Upgrade | Why |
|---|---|---|
| 11 | **MobSF full static scan of the built APK/AAB on release tags** | mobsfscan reads source only; full MobSF analyzes the actual binary (manifest flags, native libs, embedded keys post-build). Run as release-tag job with the MobSF docker image. |
| 12 | **Authenticated ZAP scan** (context + login script) monthly on staging | Baseline scan only sees logged-out surface; most of our apps live behind login. |
| 13 | **License compliance scan** (`trivy license`) | Client-facing IP hygiene — catches GPL surprises before a client's lawyer does. |
| 14 | **Container image scan on release tags** (already queued) | Config scan ≠ image scan; scan what actually deploys. |
| 15 | **OpenSSF Scorecard action on the security-ci repo itself** | The repo every project trusts should measurably meet the standard it enforces. |

### Process (no code)
- **Secret hygiene upstream:** gitleaks pre-commit hook in every dev's clone (Phase 4 box) — the pipeline is the net, not the first line.
- **A repo on `enforce: false` after 2 weeks is an incident** (already house rule — keep enforcing it).
- **Monthly patch day** reviews: action pins, scanner versions, allowlist expiry dates.

## Appendix B — Per-Client Account Ownership Table (template)

Copy into `HANDOVER.md` and keep current from Phase 1 onward:

| Service | Account owner (email) | Devora access | Billing | Renewal | Vault entry |
|---|---|---|---|---|---|
| Apple Developer | client@… | Admin (ASC) | Client card | yyyy-mm-dd ($99/yr) | ✔ |
| Google Play Console | client@… | Admin | Client card ($25 once) | — | ✔ |
| Domain + DNS | client@… | Admin | Client card | yyyy-mm-dd | ✔ |
| Hosting/VPS | client@… | SSH + panel | Client card | monthly | ✔ |
| Firebase / GCP | client@… | Editor | Client card | usage | ✔ |
| Payment gateway | client entity | Dashboard user | Client bank | contract | ✔ |
| Email (transactional) | client@… | Admin | Client card | monthly | ✔ |
| Crash/Analytics | (under Firebase) | — | — | — | ✔ |
| Signing keystore | client (vault) | Devora copy in CI | — | never expires — never lose | ✔ |
