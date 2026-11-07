# What's functional now vs TODO

## Functional demo behavior

- FastAPI app boots with six domain routers and synthetic fixtures.
- Homebuyer preliminary matching with county-based reason and clearly unverified eligibility.
- Manager program registry and consent-required preview application endpoint.
- Donor pledge validation and queue recommendation arithmetic (no transactions).
- Employer geography/consent pre-screen without HR verification.
- Developer financial gap and surplus math using decimal strings.
- Admin fictional verification queue.
- Responsive Next.js landing/dashboard pages wired to the demo API.
- Unit/API tests for key safe/negative paths.

## Skeleton / explicitly unimplemented

- Persisting new users, nonprofits, programs, applications, budgets or payments.
- Real program eligibility rules, actual up-to-date income limits, confirmed open funding.
- Login, organizations, RBAC, document vault, source synchronization, audit events.
- Genuine payment processing or donations; formal financial ledger.
- Real loan underwriting, home closing, program adjudication, legal compliance.

See domain function comments and `docs/assignments/` for explicit developer tasks.
