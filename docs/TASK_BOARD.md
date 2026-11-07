# Homely 0.2 — 5-Developer Parallel Sprint Board

Each contributor owns **one GUI + one backend domain + its tests**, with Developer 5 coordinating shared contracts and infrastructure. Use [FILE_OWNERSHIP](FILE_OWNERSHIP.md), [NEW_FEATURES](NEW_FEATURES.md), and the individual files in `assignments/`.

| Milestone | Dev 1: Homebuyer | Dev 2: Funding manager | Dev 3: Donor | Dev 4: Employer | Dev 5: Finance + Integration |
|---|---|---|---|---|---|
| **Sprint 1 — GUI and contracts** | Buyer profile + AI document uploader | Source PDF/text rule extractor | Donor campaign + match preview | Employer match + sponsorship forms | Project gap + advisor candidate list + Claude client |
| **Sprint 2 — Core behavior** | Safe document readiness + preliminary matching | Draft program rules + human review gate | Restricted allocations + ledger states | Matching caps, project sponsor cash/in-kind distinctions | Funding advisor, deterministic calculations, provider errors |
| **Sprint 3 — Validation** | Missing docs and consent tests | Stale/unknown program tests | Over-allocation and repeated requests | Max cap/in-kind tests | Cross-role E2E, demo setup, key handling, release |

## Must-align interface checkpoints

1. **Day 1 / contract freeze:** Devs 1 + 2 agree on program rule data (county, income, effective date, evidence, funding status). Devs 3 + 4 agree on match preview DTOs. Devs 4 + 5 agree cash vs in-kind developer accounting.
2. **Day 2 / integration:** All routes return 503 without Claude key; no AI-powered endpoint accepts a document without opt-in; `DEVELOPMENT` vs `BUYER` sources never mix.
3. **Before judging:** Run all tests and `npm run build`, replay sample journey, record uncertainties and unimplemented functionality on a visible demo disclaimer.

## End-to-end judge demo

1. Developer 2 extracts fictional rule guidance via Claude and flags it for manual verification.
2. Developer 1 uses an invented household and sample document to see an AI readiness checklist.
3. Developer 5 uses the $535k synthetic cost model and analyzes candidate funding sources; output gap is not changed by unverified sources.
4. Developer 4 previews $10k cash or materials and a sample matching-gift calculation.
5. Developer 3 explains donor matching and queue allocations, **without** recording real payments.

## Non-negotiable scope

No real applicant accounts, payment collection, employer HR integration, real-time verified program funding, auto-approval, or auto-routing of restricted money. These require production security, governance, and partner authorization.
