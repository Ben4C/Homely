# API contract inventory (v1)

Base URL: `http://localhost:8000/api/v1`. Interactive OpenAPI docs: `/docs`.

| Role | Method | Endpoint | Request | Response | Notes |
|---|---|---|---|---|---|
| Platform | GET | `/health` | none | `HealthResponse` | no auth in demo |
| Homebuyer | POST | `/homebuyers/match` | `MatchRequest` | `MatchResponse` | conservative preliminary-only match |
| Homebuyer | GET | `/homebuyers/profile-template` | none | `HomebuyerProfile` | synthetic demo sample |
| Manager | GET | `/programs` | optional `county` | `ProgramListResponse` | synthetic, **not open funding** |
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
