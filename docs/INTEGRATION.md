# Integration + definition of done

## Shared contracts freeze

Complete program registry / buyer profile payload review before teams modify API responses. Domain owners update their paired FastAPI Pydantic schema and TypeScript contract in one PR. Dev 5 reviews any shared files.

## First demo acceptance scenario

1. `/programs` returns synthetic program(s), each with source status explicitly `DEMO_UNVERIFIED`.
2. Buyer fills sample profile and receives matching results labelled **manual review required**.
3. Manager sees application preview and can inspect program intake fields; no live submission.
4. Employer displays a test workforce assistance program; employee match is preliminary.
5. Donor views an organization/project campaign and previews a pledge/allocation; no funds move.
6. Developer enters cost, buyer proceeds, and confirmed-like *synthetic* financing amounts and sees a calculated remaining gap.
7. Admin sees a synthetic review queue.

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
