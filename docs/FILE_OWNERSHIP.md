# Homely 0.2 — Nonoverlapping File Ownership

| Developer | Exclusive backend | Exclusive frontend | Exclusive contracts/tests |
|---|---|---|---|
| **1** | `apps/api/app/domains/homebuyers/**` (including `ai_document.py`) | `apps/web/src/app/homebuyer/**`, `apps/web/src/components/homebuyer/**` | `packages/contracts/src/homebuyers.ts`, `test_homebuyers*` |
| **2** | `apps/api/app/domains/funding_manager/**` (including `ai_program.py`) | `apps/web/src/app/manager/**`, `apps/web/src/components/manager/**` | `packages/contracts/src/funding_manager.ts`, `test_funding_manager*`, `test_manager_ai*` |
| **3** | `apps/api/app/domains/donors/**` | `apps/web/src/app/donor/**`, `apps/web/src/components/donor/**` | `packages/contracts/src/donors.ts`, `test_donors*` |
| **4** | `apps/api/app/domains/employers/**` (including `sponsorship.py`) | `apps/web/src/app/employer/**`, `apps/web/src/components/employer/**` | `packages/contracts/src/employers.ts`, `test_employers*` |
| **5** | `apps/api/app/domains/{developers,admin}/**`, `apps/api/app/core/**` | `apps/web/src/app/{developer,admin}/**`, `apps/web/src/components/{developer,admin}/**` | `packages/contracts/src/{developers,admin,ai}.ts`, `apps/web/src/lib/**`, `test_new_features.py`, `test_{developers,admin}*` |

## Shared files — Developer 5 coordinates any edits

`apps/api/app/main.py`, `.env.example`, `apps/api/pyproject.toml`, `apps/web/src/app/globals.css`, `apps/web/src/app/page.tsx`, `apps/web/src/app/layout.tsx`, `packages/contracts/src/index.ts`, `.github/`, root configs, `docs/`.

## Rules to avoid conflicting PRs

- No developer modifies another domain's server code or frontend pages directly. Consume only its published endpoints/types.
- `packages/contracts/src/ai.ts` and `core/claude_client.py` are shared **read-only** from Devs 1/2. Propose changes through Dev 5.
- Each function must have a preceding purpose / inputs / outputs comment. Do not implement stub by returning a fake final financial commitment.
- Build with the synthetic demonstration fixtures; replace them only with reviewed real program records.
- All PRs need tests, screenshots and documentation, with no leaked Claude key or real applicant data.

## Explicit integration dependencies

Dev 1 relies on Dev 2's program rules. Dev 3 consumes Dev 4's employer matching preview. Dev 4 proposes project sponsorships to Dev 5 but never writes the developer's received funding. Dev 5 provides Claude client, PDF helper, contracts and review for all teams.
