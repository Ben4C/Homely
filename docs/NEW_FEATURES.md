# Homely 0.2: Claude + Corporate Sponsorship Feature Specification

> **Scope:** Claude-assisted **draft** analyses, and deterministic *simulated* employer contributions. This repo contains no authentic programs, organizations, applications, or payments. Never demo with unredacted client records.

## A. Claude: Eligibility & Document Intelligence

Two collaborating owner domains:

1. **Developer 2 manager:** `POST /api/v1/programs/ai-extract` takes `{source: {source_label, document_text OR pdf_base64, consent_to_send_to_claude}}`. Claude proposes eligibility criteria, required documents, deadline and assistance limits, with short draft evidence excerpts. `published=false`; human manager must verify original document, source URL, effective date, rules and availability.
2. **Developer 1 homebuyer:** `POST /api/v1/homebuyers/ai-document-review` takes `{source, document_type, required_items[]}`. Claude extracts submitted sample document facts and possible missing evidence. `human_review_required=true`. This is **document readiness**, not actual eligibility approval.

**Important limitations:** Source excerpts are AI-generated labels, not verified API citations. Anthropic structured outputs and native document citations are not usable simultaneously. If you need machine-verifiable citations, implement a second source-citation pass plus excerpt/page validation and review. Do not automatically add extracted rules to the real program registry.

## B. Claude: Funding Stack Advisor

- **Developer 5:** `POST /api/v1/projects/ai-funding-advice`
- Input: `{financials: GapRequest, sources: CandidateFundingSource[], question, consent_to_send_to_claude}`.
- Output: `FundingAdviceResponse` containing a **deterministically calculated** `remaining_gap_usd`, Claude commentary keyed only to supplied source IDs, potential incompatibilities, required verification and explicit unknowns.
- Distinguish `funding_track=BUYER` from `DEVELOPMENT` and `availability=UNVERIFIED` from a confirmed grant.
- Candidate source amounts **never** change deterministic gap. No program is assumed open; the provided synthetic candidates are examples, not a live database.
- Future work: versioned guidelines, date-sensitive income tables, source-by-source legal compatibility checks, and manager approval.

## C. Corporate Sponsorship + Employer Matching

- **Developer 4:** `POST /api/v1/employers/matching-preview`. Illustrative 1:1 match with $500 cap and $20,000 demo budget; returns possible support only, with unverified employee and gift eligibility.
- **Developer 4:** `POST /api/v1/employers/sponsorship-preview`. Cash or in-kind proposed sponsorship for a fictional nonprofit campaign; returns `available_for_allocation_usd=0` until verified and authorized.
- **Developer 3:** Donor portal includes a separate employer matching gift preview consuming Dev 4's endpoint.
- **Developer 5:** Development pro forma has `employer_project_sponsorship_usd`, but no sponsorship preview writes to it. In-kind materials require actual accepted, documented avoided costs; never record as received cash.

## Server-side Claude setup

1. On the backend, `pip install -e '.[dev]'` installs the official `anthropic` Python SDK.
2. Set `ANTHROPIC_API_KEY` **only in the API environment**, not `apps/web/.env.local`, Next.js code, git, or browser local storage.
3. Optional: `ANTHROPIC_MODEL=claude-sonnet-4-6` (configurable; verify model access with your provider).
4. Run `uvicorn app.main:app --reload --port 8000`; UI starts with `npm run dev` in `apps/web`.
5. Opt in for each document request. For safety, use synthetic or manually redacted demo data. PDF limit 4 MiB. All three AI routes return HTTP **503** without a backend key; there is **no fake Claude fallback**.

### Example (macOS/Linux)

```bash
cd apps/api
export ANTHROPIC_API_KEY="<your-secret-key-from-console>"
export ANTHROPIC_MODEL=claude-sonnet-4-6
uvicorn app.main:app --reload --port 8000
```

### Example (Windows PowerShell)

```powershell
cd apps/api
$env:ANTHROPIC_API_KEY = "<your-secret-key-from-console>"
$env:ANTHROPIC_MODEL = "claude-sonnet-4-6"
uvicorn app.main:app --reload --port 8000
```

**Never commit a real key.** Rotate keys exposed in screenshots or commits. API keys incur provider charges. The app needs auth, rate limits, request budgets, secure retention and a privacy/legal review before handling real financial documents.

## Claude transport boundaries

- Only `apps/api/app/core/claude_client.py` imports `AsyncAnthropic` and has access to the key.
- `messages.parse(output_format=PydanticModel)` uses official structured-output helpers, not brittle regex JSON parsing.
- Uploaded document instructions are treated as **untrusted data**.
- The backend doesn't currently store uploaded document bytes, but the request transmits them to the API provider; do not promise zero retention by external services.
- Actual program verification, awards, tax treatment, fund disbursement and employment validation remain human-controlled and unimplemented.

## Test coverage

Run `cd apps/api && pytest -q`. AI endpoints are covered by mocked Claude calls (no external token). Tests check consent, PDF validation, no-key response, conservative gap accounting, sample ID filtering, match cap, zero allocatable sponsor previews, and the SDK adapter arguments.

End-to-end live Claude testing requires a real key and separate human verification. CI deliberately does **not** send test data to Anthropic.

## Official API reference

- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://platform.claude.com/docs/en/build-with-claude/pdf-support
- https://platform.claude.com/docs/en/build-with-claude/citations
