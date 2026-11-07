# Developer 1 — Homebuyer Experience + Claude Document Readiness

**Owner:** Person 1 · **Branch:** `feat/dev1-homebuyer-documents`  
**User archetype:** Prospective Southern California homebuyer  
**Approximate effort:** 20% of team capacity; UI 35%, matching/API 40%, tests/documentation 25%.

## Exclusive file ownership

- `apps/web/src/app/homebuyer/page.tsx`
- `apps/web/src/components/homebuyer/HomebuyerDashboard.tsx`
- `apps/web/src/components/homebuyer/AIDocumentReview.tsx` **(new)**
- `apps/api/app/domains/homebuyers/{router,schemas,service,fixtures,workflow_stubs,ai_document}.py`
- `packages/contracts/src/homebuyers.ts` (homebuyer-specific contracts)
- `apps/api/tests/test_homebuyers.py` + homebuyer-specific tests in a separate `test_homebuyers_ai.py`

**Read-only dependencies:** `packages/contracts/src/ai.ts`, `apps/web/src/lib/documentUpload.ts`, `apps/api/app/core/claude_client.py`, manager programs contract, employer program contract. Dev 5 owns shared AI files; request additions via PR.

## Assigned functions — input → output

1. `match_homebuyer(profile: HomebuyerProfile) -> MatchResponse`: geographic and **verified** eligibility pre-screen; unknown when no rule evidence; never grant eligibility.
2. `assess_program(profile, program) -> MatchResult`: explain which criteria pass/fail or require evidence; collect missing document names.
3. `review_document(request: DocumentReviewRequest) -> DocumentReviewResponse` **(new)**: pass consented text/PDF to shared Claude adapter; show extracted facts, missing items and uncertainties; **human review required**.
4. `AIDocumentReview()` **(new)**: upload <=4 MiB sample PDF OR paste redacted text, checklist, opt-in and labeled AI result.
5. `runMatch()`: submit buyer profile and render conservative matches and official source/availability where known.
6. `save_homebuyer_profile(...)` **(stub)**: later secure profile reuse; DO NOT persist real PII in current demo.

## Deliverables

- [ ] Implement step-by-step onboarding: county, household, income, first-time buyer and optional employer.
- [ ] Show program-specific *potential* matches; display verification date and link supplied by Dev 2.
- [ ] AI document readiness: required-items checklist, factual evidence excerpts, unknowns and a reviewer warning.
- [ ] AI absent-key handling (503) and consent rejection, upload file type/size checks.
- [ ] Add document privacy UI: redaction reminder, no SSNs, no real applicant files in demo.
- [ ] Cover county mismatch, unverified rules, malformed income and missing document scenarios with tests.

## Integration contract

- Existing `POST /api/v1/homebuyers/match`
- New `POST /api/v1/homebuyers/ai-document-review`
- Dev 2 `GET /api/v1/programs` supplies program rules; Dev 4 employer programs are optional matches.
- CLAUDE API key lives on the **backend only**; never read from `NEXT_PUBLIC_*`.

## Definition of done

A fictional buyer can complete the form, receive cautious program matches, submit a redacted fictional PDF/text for AI review when a test key is available, and receive nonbinding evidence and missing-document guidance. With no key, the UI fails gracefully. Automated tests + screenshot + API example accompany PR.
