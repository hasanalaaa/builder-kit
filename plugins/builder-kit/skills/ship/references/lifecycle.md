# Lifecycle map

## 1. NEW product: stages and gates

| # | Stage | Skill | Output | Gate to move on |
|---|-------|-------|--------|-----------------|
| 0 | Idea → spec | `product-spec` | `SPEC.md` (problem, scope Must/Later/Never, stories with acceptance criteria, non-functional targets, slices) | User agreed to scope + assumptions |
| 1 | Stack | `stack-picker` | `docs/adr/0001-stack.md`, versions + commands in project `CLAUDE.md` | Every Must story buildable; costs noted |
| 2 | Architecture | `project-architecture` (NEW) | `ARCHITECTURE.md`, folder skeleton, boundary rules, `arch_check.py` in CI | Walking skeleton deploys; `arch_check` 0 ERROR |
| 3 | Security baseline | `launch-security` (BUILD) | `SECURITY_MAP.md`, ASVS level, secure patterns in place (env validation, requireUser, error boundary, headers, RLS) | `security_scan` 0 ERROR |
| 4 | Data | `data-design` | schema + migrations + RLS | `schema_check` 0 ERROR |
| 5 | Design | `design-system` (DIRECTION) + `i18n-rtl` + `accessibility` | `DESIGN.md`, tokens, core components, locales | `design_lint`, `contrast`, `a11y_lint`, `rtl_lint` 0 ERROR |
| 6 | Pipeline | `deploy-release` + `observability` + `testing-strategy` | CI, previews, error tracking, health, first tests | `release_check`, `obs_check`, `audit_tests` 0 ERROR |
| 7 | Build slices | `ai-workflow` loop + specialists per slice | features with tests | Per-slice gate (§2) |
| 8 | Launch | §3 | live product | LAUNCH checklist |
| 9 | Operate | `observability`, `launch-security` maintenance, `performance`, `seo-discoverability` | dashboards, reviews | Maintenance rhythm |

Specialists by feature type during stage 7: payments → `payments-billing`; email/push/SMS → `email-notifications`; AI → `ai-features`; API → `api-contracts`; UI → `design-system` + `frontend-quality`; errors → `error-handling`; mobile → `mobile-release`; public pages → `seo-discoverability` + `performance`; legal-sensitive data → `legal-compliance`.

## 2. FEATURE (per slice)

1. Mini/feature spec (`product-spec` §3).
2. Where it lives (`project-architecture` BUILD), search before creating.
3. Security rules for what it touches (`launch-security` §2–§3).
4. Data/API/UI per specialist skill.
5. Tests from acceptance criteria (`testing-strategy`).
6. **Per-slice gate**: project tests green + `ship_check.py . --only security,architecture,errors,frontend,design,a11y,rtl,data` 0 ERROR + UI looked at (375/1280, ar/en, light/dark).
7. Update `SPEC.md` / `ARCHITECTURE.md` / `DESIGN.md` if changed; commit.

## 3. LAUNCH checklist

- [ ] `ship_check.py . --with-tests` → SHIP.
- [ ] Real pages checked in a browser: `frontend-quality/scripts/verify_ui.py --url <preview or prod url> --routes <key routes>` (add `--rtl` for Arabic) → 0 ERROR; skim the screenshots of key templates.
- [ ] `launch-security` AUDIT complete: `SECURITY_REVIEW.md` no open Critical/High; `SECURITY_REPORT.md` written; live checks (`check-headers.sh`, `check-exposed.sh`) pass.
- [ ] Performance: Core Web Vitals good on key templates (`performance`); `perf_budget` within budget.
- [ ] SEO/social: `seo_check.py <prod urls>` 0 ERROR; Search Console verified (`seo-discoverability`).
- [ ] Payments live mode tested with a real small charge + refund (`payments-billing` §13).
- [ ] Email DNS passes (`check-email-dns.sh`), templates tested (`email-notifications`).
- [ ] Legal pages, consent, account deletion, data export live (`legal-compliance`).
- [ ] Observability: errors, uptime, alerts, dashboards (`observability`); rollback rehearsed (`deploy-release` §13).
- [ ] Mobile: store submission checklist (`mobile-release` §13).
- [ ] Docs: README, CLAUDE.md, runbooks (`docs-handoff`).

## 4. RESCUE

`project-rescue`: intake → `ship_check.py --report RESCUE_SCAN.md` → stop the bleeding → stabilize → safety net → untangle → improve → handoff.

## 5. Scanner index (what ship_check runs)

| Key | Script | Skill | Runs when |
|-----|--------|-------|-----------|
| security | `launch-security/scripts/security_scan.py` | launch-security | always |
| architecture | `project-architecture/scripts/arch_check.py` | project-architecture | always |
| errors | `error-handling/scripts/error_scan.py` | error-handling | always |
| data | `data-design/scripts/schema_check.py` | data-design | SQL or Prisma files exist |
| tests | `testing-strategy/scripts/audit_tests.py` | testing-strategy | always |
| frontend | `frontend-quality/scripts/fe_check.py` | frontend-quality | JS/TS UI files exist |
| design | `design-system/scripts/design_lint.py` | design-system | UI files exist |
| a11y | `accessibility/scripts/a11y_lint.py` | accessibility | UI files exist |
| rtl | `i18n-rtl/scripts/rtl_lint.py` | i18n-rtl | UI files exist |
| ai | `ai-features/scripts/ai_check.py` | ai-features | AI SDK detected |
| perf | `performance/scripts/perf_budget.py` | performance | package.json or assets exist |
| seo | `seo-discoverability/scripts/seo_check.py` | seo-discoverability | built HTML found |
| release | `deploy-release/scripts/release_check.py` | deploy-release | always |
| obs | `observability/scripts/obs_check.py` | observability | always |
| legal | `legal-compliance/scripts/legal_check.py` | legal-compliance | UI exists |
| mobile | `mobile-release/scripts/mobile_release_check.py` | mobile-release | Expo/RN/Flutter/native project |
| docs | `docs-handoff/scripts/docs_check.py` | docs-handoff | always |

## 6. Skill router (request → skill)

| The user says / the task is | Skill |
|-----------------------------|-------|
| idea, MVP, requirements, "build me an app like" | product-spec |
| which framework/host/DB | stack-picker |
| folders, structure, messy code, where does this go, simplify | project-architecture |
| security, auth, keys, RLS, launch audit, leak | launch-security |
| tables, migrations, slow queries | data-design |
| endpoints, API, webhooks out, versioning | api-contracts |
| crashes, try/catch, timeouts, retries | error-handling |
| tests, QA, coverage, flaky | testing-strategy |
| look & feel, colors, fonts, UX, polish, critique | design-system |
| React/Next code quality, state, forms | frontend-quality |
| Arabic, RTL, translations | i18n-rtl |
| WCAG, screen readers, keyboard | accessibility |
| chatbot, LLM, RAG, agents, AI costs | ai-features |
| checkout, subscriptions, IAP | payments-billing |
| emails, push, SMS, spam | email-notifications |
| slow, Lighthouse, bundle size | performance |
| Google, meta tags, sitemap, OG | seo-discoverability |
| CI/CD, deploy, rollback, environments | deploy-release |
| logs, Sentry, alerts, analytics | observability |
| privacy policy, GDPR/PDPL, cookies, deletion | legal-compliance |
| App Store/Play submission, TestFlight, EAS | mobile-release |
| AI keeps breaking things, prompts, CLAUDE.md | ai-workflow |
| inherited/AI-built mess | project-rescue |
| bug, error, works locally not prod | debugging |
| README, handover, runbooks | docs-handoff |
| everything / launch / full check | ship |
