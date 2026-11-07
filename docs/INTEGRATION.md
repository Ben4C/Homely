# Integration + definition of done

## Shared contracts freeze

Complete program registry / buyer profile payload review before teams modify API responses. Domain owners update their paired FastAPI Pydantic schema and TypeScript contract in one PR. Dev 5 reviews any shared files.

## Acceptance scenario (persistent directory)

1. Apply Alembic to PostgreSQL and explicitly import the reviewed source catalog and manual-review leads.
2. Homebuyer searches Orange County/Garden Grove with income 65000 and household size 3; city-restricted Anaheim records are excluded, source references and conservative unknowns remain visible.
3. Current residence and purchase location are evaluated separately. A confirmed closed listing never appears as accepting applications. Unknown ZIP mappings return an actionable error.
4. Open program and nonprofit detail pages; review source dates, rule versions, channels, services, and charitable-status uncertainty.
5. Manager previews intake without submitting an application. An authorized reviewer checks sources and records a revision/audit event; unauthorized and stale-revision writes fail.
6. Employer and donor financial workflows remain clearly synthetic. Developer gap math remains deterministic; source candidates come from the persistent registry.
7. Restart the API and PostgreSQL; records, rule versions, and audit events remain. Repeat imports produce no duplicates and changed imports require review.
8. Check all six workspaces and the homepage on desktop/mobile, light/dark, single header/main/navigation, keyboard access, and no horizontal overflow.

## Pre-merge quality gate

```bash
cd apps/api && python -m pytest -q
cd apps/web && npm run typecheck && npm run build
```

## Done when

- UI works at mobile and desktop widths; empty/loading/error states exist.
- Inputs validated server-side; monetary values use Decimal (Python) and string values in JSON.
- Every business function has a comment block explicitly stating Purpose, Inputs, Outputs.
- Program source/verification/availability surfaced in UI.
- One happy path and at least one rejection/edge-case test for each feature.
- No public access to real PII and no payment execution.
- `DEMO`/`SYNTHETIC` labels remain wherever seeded data is shown.

## Future release gates

Real identity + RBAC, PostgreSQL migrations, transactional ledger, e-signatures/secure documents, integration partner agreements, external payment setup, data correctness and compliance audits, security review, privacy impact analysis.


## PostgreSQL and browser verification

Set `TEST_DATABASE_URL` to a separate PostgreSQL database ending `_test`, then run the full suite. No test resets the populated directory. The registry fixture wraps each case in rollback-only transactions. For fast local runs without PostgreSQL, only registry tests use temporary SQLite stores; original compatibility tests explicitly select demo fixtures.

Browser scripts require Playwright (install separately for development) and running API/web servers. Set `PLAYWRIGHT_MODULE` if Playwright is available outside the project. Set `HOMELY_WEB_URL` (default localhost:3105) for all-role checks, and `DEV5_WEB_URL`/`DEV5_API_URL` for developer regression checks. The frontend's `NEXT_PUBLIC_API_BASE_URL` must target the running API, with matching CORS.

```powershell
node apps/api/tests/test_integration_browser.cjs
node apps/api/tests/test_dev5_browser.cjs
node apps/api/tests/test_dev5_browser_regressions.cjs
# Optional authorized local review: ignored JSON file containing {"token":"..."}
$env:HOMELY_REVIEWER_FILE='path/to/ignored-local-credential.json'
node apps/api/tests/test_directory_review_browser.cjs
```

All-role checks read actual persisted records. Developer-specific AI rendering/regression checks explicitly intercept only AI responses, avoiding paid provider calls. Authorized review retains UNKNOWN status and existing rules for the real Garden Grove listing. Availability-change and rule-publication cases use isolated test transactions. Screenshots are written under ignored `apps/api/.venv/integration/screenshots` and `apps/api/.venv/dev5-previews`.

See [the integration report](INTEGRATION_REPORT.md) for executed results, exclusions, and the full changed-file inventory.
