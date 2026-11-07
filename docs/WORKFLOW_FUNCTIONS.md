# Function-level implementation backlog

Read each function's **Purpose / Inputs / Outputs** comment immediately above it. Every future method intentionally raises `NotImplementedError` and is NOT imported into the running API.

| Dev | Working demo service | Future workflow skeleton |
|---|---|---|
| 1 | `domains/homebuyers/service.py` | `domains/homebuyers/workflow_stubs.py` — buyer profile, income tables, stacking, documents |
| 2 | `domains/funding_manager/service.py` | `domains/funding_manager/workflow_stubs.py` — program drafts, source verification, rules, reviews, awards, referrals |
| 3 | `domains/donors/service.py` | `domains/donors/ledger_stubs.py` — pledges, receiving, reserves, commitments, reconciliation, impact |
| 4 | `domains/employers/service.py` | `domains/employers/workflow_stubs.py` — org registration, EAH, attestation, sponsorship, impact |
| 5 | `domains/developers/service.py`, `domains/admin/service.py` | `domains/developers/workflow_stubs.py`, `domains/admin/workflow_stubs.py` — pro forma, delay, fund stacking, project milestones, org trust, auth |

**Never expose unimplemented workflow stubs as live routes**. Replace method bodies with authorized, tested implementation and update the matching schema + typed TS contract + UI + tests in the same PR.
