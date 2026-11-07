# Homely — Southern California Affordable Homeownership (Claude + Sponsorship Starter v0.2)

> Homely helps Southern California residents pursue affordable homeownership by connecting buyers, donors, employers, nonprofits, and housing developers with AI-assisted guidance and funding options.

**Team:** The Agents
**Members:** Ben Choi, Olivia Jeung, Shogo Stuck, Jim Truong, Hamza Vaid
**Lane:** 3 Fund it
**Built At:** Claude Impact Lab: UCI × SoCal Affordable Housing, November 7, 2026

## The real user
The primary user is a nonprofit housing finance manager or development director trying to secure enough funding to build affordable homes for eligible families.
**Before:** They manually search through city, state, and federal funding programs, compare eligibility requirements, track changing mortgage rates, and coordinate with donors and funding organizations, making it difficult to identify available resources and close funding gaps.
**After:** Homely brings these resources into one platform, automatically matches housing projects and eligible families with potential funding sources, and provides transparent funding tracking so managers can coordinate contributions and ensure money reaches the people who need it.

## What we built
Homely is a six-role platform spanning homebuyers, donors, employers, nonprofit funding managers, housing developers, and platform administrators. This repo gives a five-programmer team demo foundations, typed domain interfaces, route skeletons, integration contracts, tests, and non-overlapping file assignments. **New:** server-only Claude document intelligence, rule extraction and funding advice, plus corporate matching gifts and project sponsorship previews.

## How Claude is used
Claude helped plan and prototype the project: it researched income limits, a concept brief, and the Homely template site with a homepage, and drafted the backend code and tests.

## Try it
Open the Homely website using the provided website link.

## Sources and assumptions
| Item | Source or assumption | Date checked |
| :---:        |     :---:      |         :---: |
| Mortgage Rates  | https://www.freddiemac.com/pmms?stream=top&utm_source  | Nov 7, 2026   |
| Income limit datase     | https://data.ca.gov/%40california-department-of-housing-and-community-development/income-limits-by-county?utm_source      | Nov 7, 2026     |
| HOME-funded buyer income caps    | https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/2026-california-HOME-income-limits_0.pdf       | Nov 7, 2026     |

## Where it gets things wrong
Homely may show outdated or inaccurate funding information if organizations do not regularly update their program listings, available funds, eligibility requirements, and application deadlines. The platform also cannot guarantee that someone will qualify for a program or receive funding, since final approval depends on the funding organization's review and available budget. We would not trust Homely to automatically approve applicants, distribute donations, or make final eligibility decisions without human verification. We also do not yet know how accurately the platform can match recipients with multiple funding sources or how quickly organizations would update their information.

## Next steps
For a nonprofit or city to start using Homely next month, we would first partner with one local housing organization in Orange County to upload and verify available funding programs, eligibility requirements, application deadlines, and remaining funds. We would also create a simple onboarding process for donors, funding managers, and prospective homeowners so they can begin using the platform.

With one more week, we would focus on building a working prototype of Homely's main features, including the funding database, recipient eligibility matching system, and donor transparency dashboard. We would also test the platform using our synthetic housing deal and a real Orange County housing project to identify gaps, improve accuracy, and gather feedback from potential users.

## Data and privacy
This project uses only public or provided data. It contains no personal information about real tenants, buyers or residents. It does not file applications or contact any city or person.

## License
MIT, see the LICENSE file in this repo (or tell us what you chose).

## Architecture

- **Web:** Next.js App Router + React + TypeScript (`apps/web`)
- **API:** Python + FastAPI + Pydantic (`apps/api`)
- **Contracts:** TypeScript request/response definitions (`packages/contracts`)
- **Database plan:** PostgreSQL (optional local container; **not yet connected**). API uses **in-memory, synthetic fixtures**.
- **Payments:** **No actual payments**. The donation and fund ledgers are plans / preview records, not an implemented payment system.

## Local setup

**Prerequisites:** Node.js 20+, npm, Python 3.11+; Docker only if you want to start the future PostgreSQL dependency.

**Terminal A — API**

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
# For real Claude analysis only, set a server-side API key first:
# macOS/Linux: export ANTHROPIC_API_KEY="<your key>"
# PowerShell: $env:ANTHROPIC_API_KEY = "<your key>"
# Optional: ANTHROPIC_MODEL=claude-sonnet-4-6
uvicorn app.main:app --reload --port 8000
```

**Terminal B — Web**

```bash
cd apps/web
npm install
npm run dev
```

- UI: http://localhost:3000
- API documentation: http://localhost:8000/docs
- API health check: http://localhost:8000/api/v1/health
- Optionally run `docker compose up -d db` (the API **still uses fixtures** until persistence is implemented).

The browser API client defaults to `http://127.0.0.1:8000/api/v1`. Override `NEXT_PUBLIC_API_BASE_URL` in `apps/web/.env.local` for a different API host. **Never put `ANTHROPIC_API_KEY` in a `NEXT_PUBLIC_` variable or frontend `.env` file.**

## Three added features (v0.2)

1. **Claude Eligibility & Document Intelligence:** Residents use `/homebuyers/ai-document-review` to find possible missing evidence; managers use `/programs/ai-extract` to create unpublished, reviewable rules from text/PDFs. AI is advisory, never an approver.
2. **Claude Funding Stack Advisor:** Developers call `/projects/ai-funding-advice` with hypothetical source restrictions; Claude describes possible options/conflicts while the server calculates the gap deterministically.
3. **Corporate Sponsorship & Employer Matching:** `/employers/matching-preview` returns capped fictional match estimates; `/employers/sponsorship-preview` distinguishes cash from in-kind contributions and never books unverified dollars.

**Claude configuration:** `ANTHROPIC_API_KEY` and optional `ANTHROPIC_MODEL` are read by the FastAPI backend. Without a key, AI calls return `503` (not mock AI responses). The official `anthropic` Python SDK is installed via `pip install -e '.[dev]'`. The demo uses only simulated programs and no live funding activity. Read [NEW_FEATURES](docs/NEW_FEATURES.md) for exact API request/response types, privacy boundaries, and example workflows.

## Five programmer work packages

| Developer | Main ownership | Web route | API domain | Assignment |
|---|---|---|---|---|
| **1** | Homebuyer + Claude document readiness | `/homebuyer` | `homebuyers/` | [Developer 1](docs/assignments/DEV1_HOMEBUYER.md) |
| **2** | Funding manager + Claude program rule extraction | `/manager` | `funding_manager/` | [Developer 2](docs/assignments/DEV2_FUNDING_MANAGER.md) |
| **3** | Donor + gift matching preview + funding ledger | `/donor` | `donors/` | [Developer 3](docs/assignments/DEV3_DONOR.md) |
| **4** | Corporate sponsorship + employer matching | `/employer` | `employers/` | [Developer 4](docs/assignments/DEV4_EMPLOYER.md) |
| **5** | Funding stack Claude advisor + API client + developer/admin | `/developer`, `/admin` | `developers/`, `admin/`, `core/` | [Developer 5](docs/assignments/DEV5_DEVELOPER_ADMIN.md) |

Every teammate owns the corresponding web component, API router, service, schema, domain contract, fixture, and tests. Review [FILE_OWNERSHIP](docs/FILE_OWNERSHIP.md) to avoid merge conflicts. Shared code changes require developer 5 review.

## Sprint integration

1. Each developer branches from `main` using `feat/devN-<feature>`.
2. Do not rename an existing API URL or response field without a contract PR.
3. Implement API business logic and tests before connecting complex UI interactions.
4. Use synthetic data for demos; add source URLs, verification timestamps, and explicit uncertainty before real program data.
5. PR acceptance: `pytest`, `npm run typecheck`, and `npm run build` all pass; include screenshots and one curl example.
6. Integrate in order: **program registry (2)** → **buyer matching (1)** → **employer (4)** and **donor (3)** → **developer finance (5)** → end-to-end demo.

## Start here

- [Architecture and flows](docs/ARCHITECTURE.md)
- [Function-level implementation backlog](docs/WORKFLOW_FUNCTIONS.md)
- [API contracts and ownership](docs/API_CONTRACTS.md)
- [Team file ownership](docs/FILE_OWNERSHIP.md)
- [Security, financial, and program boundaries](docs/SECURITY.md)
- [Acceptance tests and release checklist](docs/INTEGRATION.md)

## Known missing production capabilities

Real authentication and RBAC, database migrations/persistence, nonprofit verification, authoritative program ingestion, PII encryption, secure document access, payment processing, lender/closing integrations, fraud prevention, actual eligibility adjudication, live availability, compliance and legal review. A live Claude request has **not** been exercised without a user-supplied API key; tests mock the provider. **Do not enter real user data or collect live money in this scaffold.**
