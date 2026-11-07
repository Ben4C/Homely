# Developer 5 — Claude API Infrastructure + Funding Stack Advisor + Project Finance/Integration

**Owner:** Person 5 (integration lead) · **Branch:** `feat/dev5-claude-funding-advisor`  
**User archetype:** Housing developer / platform administrator  
**Approximate effort:** 20%; AI adapter & infra 35%, project/advisor UI/API 40%, QA/integration 25%.

## Exclusive file ownership

- `apps/web/src/app/{developer,admin}/**`
- `apps/web/src/components/{developer,admin}/**` including **new** `developer/AIFundingAdvisor.tsx`
- `apps/api/app/domains/{developers,admin}/**` including **new** `developers/ai_advisor.py`
- `apps/api/app/core/**` including **new** `core/claude_client.py`
- `apps/api/tests/test_{developers,admin}.py` + `test_new_features.py` API integration tests
- `packages/contracts/src/{developers,admin}.ts`
- Shared: `packages/contracts/src/ai.ts` **(new)**, `apps/web/src/lib/documentUpload.ts` **(new)**, base styling, `apps/api/app/main.py`, env docs, CI, repository docs.

**Cross-domain files:** Do not directly alter other developers' modules without PR review; handle shared contract changes in a coordinated integration PR.

## Assigned functions — input → output

1. `claude_json(system, content, result_type) -> BaseModel` **(new)**: server-only SDK `AsyncAnthropic.messages.parse`, configured via `ANTHROPIC_API_KEY`; 503 if unset; sanitized provider errors. Not a browser function.
2. `document_blocks(source: SourceDocument) -> list` **(new)**: validate one text or base64 PDF <=4 MiB, require consent, return Claude content blocks (trusted instructions separate from untrusted docs).
3. `advise_funding(FundingAdviceRequest) -> FundingAdviceResponse` **(new)**: describe ONLY supplied candidate funding sources and potential conflicts, keeping buyer aid out of developer receipts.
4. `calculate_gap(GapRequest) -> GapResponse`: Decimal arithmetic of project development costs and already-entered sources; don't add unverified candidate awards.
5. `AIFundingAdvisor({financials})` **(new)**: run Claude over fictional funding candidates, show explanations, unknown stackability and deterministic gap.
6. `admin` verification workflow stubs: organization authorization, audit events and cross-role integration.

## Deliverables

- [ ] Support Claude API key via backend environment only; configurable `ANTHROPIC_MODEL`.
- [ ] Modern SDK `messages.parse()` with Pydantic output; keep AI output nonbinding and cite input source identifiers.
- [ ] Robust opt-in / PDF validation / 503 without API key / safe 502 on provider failure.
- [ ] Developer advisor UI using synthetic source cards; source-specific assessments and deterministic gap result.
- [ ] Validate that invented source IDs are filtered; do not confuse buyer grants with development subsidies.
- [ ] Shared route/contracts/types and no React-secret leakage; CI and end-to-end cross-role scenario.
- [ ] Add fake-SDK tests; no network dependency in CI; document live Claude verification as separate opt-in manual step.

## Integration contract

- `POST /api/v1/projects/gap` (existing).
- `POST /api/v1/projects/ai-funding-advice` **(new)**.
- Shared Claude client used by Dev 1's `/homebuyers/ai-document-review` and Dev 2's `/programs/ai-extract`.
- Dev 3/4 preview amounts do not enter project totals until a future manager-controlled commitment ledger is implemented.

## Definition of done

Project manager gets correct deterministic financing gap and separately Claude-authored explanations of supplied hypothetical candidates. AI absent-key behavior is clear, key never reaches frontend, and all smoke/CI tests pass. Dev 5 signs off on all interface contracts before demo freeze.
