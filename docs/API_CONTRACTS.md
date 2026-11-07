# API contract inventory (v1)

Base URL: `http://localhost:8000/api/v1`. Interactive OpenAPI docs: `/docs`.

| Role | Method | Endpoint | Request | Response | Notes |
|---|---|---|---|---|---|
| Platform | GET | `/health` | none | `HealthResponse` | no auth in demo |
| Homebuyer | POST | `/homebuyers/match` | `MatchRequest` | `MatchResponse` | conservative preliminary-only match |
| Homebuyer | GET | `/homebuyers/profile-template` | none | `HomebuyerProfile` | synthetic demo sample |
| Manager | GET | `/programs` | optional `county` | `ProgramListResponse` | persisted source-backed programs; explicit demo mode available |
| Manager | POST | `/programs/check` | `ProgramCheckRequest` | `ProgramCheckResponse` | manual verification placeholder |
| Manager | POST | `/applications` | `ApplicationCreate` | `ApplicationResponse` | preview only, not real submission |
| Manager | GET | `/applications` | none | `ApplicationListResponse` | synthetic queue |
| Donor | GET | `/donors/campaigns` | none | `CampaignListResponse` | synthetic campaign options |
| Donor | POST | `/donors/pledge-preview` | `PledgePreviewRequest` | `PledgePreviewResponse` | **no transfer or reservation** |
| Donor | POST | `/donors/allocate-preview` | `AllocationPreviewRequest` | `AllocationPreviewResponse` | no actual decisions |
| Employer | GET | `/employers/programs` | none | `EmployerProgramListResponse` | synthetic |
| Employer | POST | `/employers/check` | `EmployerCheckRequest` | `EmployerCheckResponse` | no HR lookup |
| Developer | GET | `/projects` | none | `ProjectListResponse` | synthetic |
| Developer | POST | `/projects/gap` | `GapRequest` | `GapResponse` | exact math; assumptions labelled |
| Admin | GET | `/admin/review-queue` | none | `AdminReviewResponse` | synthetic |

### Contract discipline

Pydantic schemas are in the domain's `schemas.py`. Mirrored TypeScript types live in `packages/contracts/src/<domain>.ts`. **Developers own their types**, and CI checks basic API validity; future work should generate TS clients directly from OpenAPI.

Cross-team references use stable string IDs: `program_id`, `organization_id`, `project_id`. Avoid direct imports from another team's *fixtures*. Dev 1 may consume Dev 2's public `GET /programs`, not mutate manager data.

### Error semantics (target)

- `400` invalid request shape/business impossibility
- `401` authentication required
- `403` organization role/consent insufficient
- `404` ID missing
- `409` concurrent budget/commitment conflict
- `422` request validation error
- `503` source data unavailable or stale for decisive real-time claim

Starter runs without authentication, and no endpoint may be used to make a real funding decision.

## Additions in v0.2: Claude and Corporate Sponsorship

See [NEW_FEATURES](NEW_FEATURES.md) and `packages/contracts/src/ai.ts` for full DTO definitions.

| Endpoint | Owner | Request type | Response type | Live side effects |
|---|---|---|---|---|
| `POST /api/v1/homebuyers/ai-document-review` | Dev 1 | `DocumentReviewRequest` | `DocumentReviewResponse` | Claude API call only, no approval |
| `POST /api/v1/programs/ai-extract` | Dev 2 | `ProgramExtractRequest` | `ProgramExtractResponse` | Claude API call only, no publication |
| `POST /api/v1/projects/ai-funding-advice` | Dev 5 | `FundingAdviceRequest` | `FundingAdviceResponse` | Claude API call only, no awards |
| `POST /api/v1/employers/matching-preview` | Dev 4 | `MatchingGiftRequest` | `MatchingGiftResponse` | None |
| `POST /api/v1/employers/sponsorship-preview` | Dev 4 | `SponsorshipPreviewRequest` | `SponsorshipPreviewResponse` | None |

Source PDFs are base64-encoded in `SourceDocument.pdf_base64`, at most 4 MiB decoded. Alternatively use `SourceDocument.document_text`. Explicit consent required for document processing; do not supply both. All AI endpoints need `ANTHROPIC_API_KEY` **on the server**. No prompt or preview is a verified funding offer.

#### Manager extraction example

`POST /api/v1/programs/ai-extract` accepts one explicitly consented text or PDF source:

```json
{
  "source": {
    "source_label": "Fictional 2026 program guidelines",
    "document_text": "Fictional sample: applicants must live in Orange County. The deadline is not stated.",
    "consent_to_send_to_claude": true
  }
}
```

The response is an unpublished draft (`published: false`, `human_review_required: true`). Proposed excerpts are AI-generated evidence candidates, not verified citations. Reviewers must verify the original source, program year, legal authority, rules, deadline and funding availability. No draft or local UI edit is stored or exported as an offer.

The demo program list downgrades `VERIFIED_OPEN`, `VERIFIED_CLOSED`, and `WAITLIST` to `UNKNOWN` when the source URL or verification timestamp is missing, malformed, in the future, or more than 30 days old. The 30-day window is a conservative demo freshness rule; production should make the freshness policy configurable and audit reviewer/source evidence.

Dev 2 artifacts: [manager dashboard screenshot](assignments/DEV2_MANAGER_SCREENSHOT.png) and [Dev 1 verified-rule schema proposal](assignments/DEV2_PROGRAM_RULE_SCHEMA_PROPOSAL.md).


## Source-backed directory APIs (2026-11 integration)

Types: `packages/contracts/src/directory.ts`; server import/review/public-program schemas: `app/data/schemas.py`. Money is transmitted as decimal strings or null, never inferred from income limits. Null means not established by this record.

| Method | Endpoint | Behavior |
|---|---|---|
| GET | `/funding-programs/search` | Published database records, deterministic preliminary screening, total/page/page_size |
| GET | `/funding-programs/locations` | Normalized supported areas and parent IDs; no guessed ZIP mapping |
| GET | `/funding-programs/{id}` | Published detail, provenance, current rules and immutable rule history |
| GET | `/organizations/search` | Source-backed services, geography, contacts and independent charitable-status metadata |
| GET | `/organizations/{id}` | Organization detail with related published programs |
| GET | `/directory/overview` | Persistent public-directory integrity counts |
| GET | `/directory/review-queue` | Bearer authorization; manager organization scope or administrator |
| POST | `/directory/programs/{id}/review` | Source evidence/status and optional structured rule version; atomic audit |
| POST | `/directory/organizations/{id}/review` | Administrator-only source review and audited verification |
| POST | `/directory/import-drafts/{id}/review` | Scoped ACCEPT/REJECT/ACKNOWLEDGE; changed metadata never auto-published |

Program filters: `county`, `city`, `zip_code`, `residence_county`, `residence_city`, `q`, `category`, `assistance_type`, `organization_type`, `channel`, `status`, `accepting_applications`, `funding_track`, `first_time_buyer`, `household_income`, `household_size`, `employer`, `purchase_price`, `page`, `page_size` (1..100), `sort` (name/reviewed). Geography is California-only in this initial catalog. Unknown or conflicting city/ZIP mappings return 422. Search matches program or administering-organization name. Organization filters: county/city/q/kind/page/page_size.

`POST /homebuyers/match` retains legacy `county` (purchase fallback) and adds explicit purchase county/city/ZIP/price and current residence county/city. It returns `POTENTIALLY_ELIGIBLE`, `KNOWN_CRITERIA_NOT_MET`, `ADDITIONAL_INFORMATION_REQUIRED`, `PROGRAM_UNAVAILABLE`, `ELIGIBILITY_NOT_VERIFIED`, or `OUTSIDE_SERVICE_AREA` with reasons and source/detail/channel links. These are preliminary outcomes. Legacy `NEEDS_MANUAL_REVIEW` remains in the union for explicit demo compatibility. Unknown criteria cannot yield approval.

Review payloads require `expected_revision`, reason and dated official-source evidence. Program review optionally accepts `rules: RuleInput[]`; absent rules retain the current version. Organization review is separate from IRS verification. Invalid/missing authorization returns 401/403, stale revisions or conflicting identifiers 409, invalid evidence/rules 422, unavailable database 503. Errors do not expose database credentials or raw submitted documents. No client-supplied actor identity is trusted.

Example:

```text
GET /api/v1/funding-programs/search?county=Orange&city=Garden%20Grove&household_income=65000.00&household_size=3&first_time_buyer=true
```

The original `/admin/review-queue` remains a synthetic read-only compatibility endpoint; the Admin GUI uses the persistent `/directory` workflows. `/applications` remains an explicit preview even when its program ID comes from the real directory.
