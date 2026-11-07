# Developer 2 — Funding Manager + Claude Program Rule Extraction

**Owner:** Person 2 · **Branch:** `feat/dev2-program-rule-intelligence`  
**User archetype:** Authorized nonprofit / government program manager  
**Approximate effort:** 20%; UI 30%, API/business rules 45%, tests/docs 25%.

## Exclusive file ownership

- `apps/web/src/app/manager/page.tsx`
- `apps/web/src/components/manager/ManagerDashboard.tsx`
- `apps/web/src/components/manager/ProgramRuleExtractor.tsx` **(new)**
- `apps/api/app/domains/funding_manager/{router,schemas,service,fixtures,workflow_stubs,ai_program}.py`
- `packages/contracts/src/funding_manager.ts`
- `apps/api/tests/test_funding_manager.py` + domain-specific `test_manager_ai.py`

**Read-only:** shared Claude adapter / PDF helper / shared AI contract (Dev 5), homebuyer profile (Dev 1), donor ledger (Dev 3).

## Assigned functions — input → output

1. `extract_program(ProgramExtractRequest) -> ProgramExtractResponse` **(new)**: Claude reads consented sample guideline text or PDF; outputs **UNPUBLISHED** rule draft, evidence excerpts, caps, required docs, deadlines and unknowns.
2. `ProgramRuleExtractor()` **(new)**: upload/paste official document, consent, review draft and mark `human_review_required`.
3. `list_programs(county: str|None) -> ProgramListResponse`: filter and version programs by county; distinguish closed/unverified/open only with evidence.
4. `verify_and_publish_program(program_id, source_url, reviewer_id)` **(stub)**: manager checks official source, version, legal authority and funding availability; atomically creates verified program version.
5. `save_eligibility_rule_version(program_id, rules, effective_at)` **(stub)**: preserve historical source/effective date and in-flight application behavior.
6. `review_application(...)` + `commit_program_award(...)` **(stubs)**: authorized review and a separately approved ledger commitment; no AI auto-approval.

## Deliverables

- [ ] Program rule extraction and user-visible source excerpts from PDF/text; label excerpts *AI-proposed*, not verified citations.
- [ ] Show confidence limits: missing program year, missing funding availability, absent income table.
- [ ] Add editable program review workflow, but **do not auto-publish** model output.
- [ ] Clear manager application statuses, incomplete-document queue, audit fields.
- [ ] Write tests: contradictory guidance, missing deadline, no-source, stale program, no key, consent rejected.
- [ ] Produce a program-rule schema proposal for Dev 1 before editing cross-domain contracts.

## Integration contract

- `POST /api/v1/programs/ai-extract` **(new)**
- `GET /api/v1/programs`, `POST /api/v1/programs/check`, `GET /api/v1/applications` (existing)
- Exports validated *program facts* to Dev 1/Dev 5; never exposes unpublished AI drafts as offers.

## Definition of done

A nonprofit reviewer can use fictional or published/redacted guidance to produce a Claude draft, inspect every proposed rule and uncertainty, and then explicitly verify (future workflow) before it affects matching. No automated funding approval. Automated tests + screenshot + API example accompany PR.
