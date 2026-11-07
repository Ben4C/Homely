# Homely — Southern California Affordable Homeownership (Claude + Sponsorship Starter v0.2)

> **Scaffold / demo only.** All seeded programs, organizations, people and money amounts are **synthetic**. No live funds are transferred, no applicant is actually approved, and no source is represented as currently open.

**Team:** The Agents
**Members:** Ben Choi, Olivia Jeung, Shogo Stuck, Jim Truong, Hamza Vaid
**Lane:** 3 Fund it
**Built At:** Claude Impact Lab: UCI × SoCal Affordable Housing, November 7, 2026

Homely is a six-role platform spanning homebuyers, donors, employers, nonprofit funding managers, housing developers, and platform administrators. This repo gives a five-programmer team demo foundations, typed domain interfaces, route skeletons, integration contracts, tests, and non-overlapping file assignments. **New:** server-only Claude document intelligence, rule extraction and funding advice, plus corporate matching gifts and project sponsorship previews.

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
