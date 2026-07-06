# Triage Guide — what to do when the gate fails

The gate fails when any scanner reports **blocking** findings (CRITICAL/HIGH, or
ERROR-severity for SAST tools). This page is the playbook: read the finding,
decide *real* or *false positive*, act. Full raw reports for every run are in
the workflow's **Artifacts** (`secscan-*`).

The one rule that keeps the system honest: **a false positive gets an
allowlist entry with a written reason and an owner — never a lowered
threshold, never `enforce: false` left on permanently.**

---

## 1. Gitleaks (secrets)

**Report:** `gitleaks-report.json` — each entry has file, line, rule, and a
redacted match.

- **Real secret, current code** → rotate the credential FIRST (assume it is
  burned), then move it to env/secret storage, then re-run.
- **Real secret, only in old git history** → it is still burned. Rotate it.
  Rewriting history (`git filter-repo`) is optional cleanup; rotation is not.
- **False positive** (test key, example value) → copy
  `config/gitleaks.example.toml` into the project root as `.gitleaks.toml`
  and allowlist the specific path or pattern, with a comment: why + who + when.
  Never allowlist a pattern as broad as `password`.

## 2. Semgrep (SAST)

**Report:** `semgrep.json` — rule id, file, line, message. ERROR = blocking,
WARNING/INFO = informational.

- **Real** → fix the code; the rule message links to remediation guidance.
- **False positive on one line** → add `// nosemgrep: <rule-id>` on that line
  with a short justification comment beside it.
- **False positive across a path** (generated code, vendored libs) → add the
  path to `.semgrepignore` in the project root (see
  `config/semgrepignore.example`).

## 3. Trivy (dependency CVEs)

**Report:** `trivy-deps.json` — package, installed version, fixed version,
CVE id, severity.

- **Fix available** → bump the package (`flutter pub upgrade <pkg>`,
  `npm update <pkg>`, `composer update <pkg>`). This is the answer 90% of
  the time.
- **No fix released yet** → check if the vulnerable code path is reachable in
  our usage. If genuinely not, add the CVE to `.trivyignore` in the project
  root with reason + owner + a review date, and add a calendar reminder to
  remove it.
- **Transitive dependency** → override/pin the transitive version, or bump the
  direct parent.

## 4. Trivy (Docker/IaC config)

**Report:** `trivy-config.json` — misconfiguration id, file, resolution.
Common real hits: containers running as root, missing healthcheck, `latest`
base images, exposed secrets in compose files. Fix per the resolution text;
these are almost never false positives.

## 5. OWASP Mobile scanners (M1/M2/M5/M9)

**Reports:** `owasp_m1_secrets_scan.json`, `owasp_m2_dependencies_scan.json`,
`owasp_m5_network_scan.json`, `owasp_m9_storage_scan.json`.

- **M1 hardcoded secrets** → same rules as gitleaks: rotate, move to
  `--dart-define` / backend, re-run. Test placeholder values that trip the
  regexes should be renamed to obviously-fake values (`YOUR_API_KEY` style is
  already excluded).
- **M2 dependencies** → outdated/vulnerable pub packages; upgrade.
- **M5 network** → `http://` URLs, disabled TLS validation, cleartext config.
  Real in almost every case — fix rather than allowlist. Localhost/dev URLs
  belong behind a build flag, not in release code paths.
- **M9 storage** → sensitive values in SharedPreferences or plaintext files.
  Move tokens/PII to `flutter_secure_storage`. Non-sensitive prefs (theme,
  locale) flagged by pattern → rename keys so they don't look like secrets
  (e.g. `auth_token_hint` → `onboarding_seen`).

## 6. mobsfscan (mobile SAST)

**Report:** `mobsfscan.json` — rule id with OWASP MASVS mapping, files, lines.
ERROR = blocking. Typical real hits: cleartext traffic enabled, debuggable
release manifests, allowBackup on sensitive apps, weak crypto usage. Fix in
the manifest/code; rule metadata links to the exact MASVS requirement.

## 7. flutter analyze

Informational by default (`strict_flutter_analyze: false`). Treat it as code
health signal; flip strict on per-project once the project is warning-clean.

---

## Severity policy (house rule)

| Finding class | Gate behaviour | SLA |
|---|---|---|
| CRITICAL / HIGH / ERROR | Blocks merge | Fix before merge — no exceptions on Tier 1 projects |
| MEDIUM / WARNING | Reported, not blocking | Fix within the sprint |
| LOW / INFO | Reported | Batch into monthly patch day |

`enforce: false` exists for **rollout week on existing projects only**. If a
repo still has it after two weeks, that is an incident of its own.
