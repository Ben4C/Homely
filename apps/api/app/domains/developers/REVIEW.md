# Developer 5 code review

Review date: November 7, 2026. Scope: `core`, developer/admin domains, their dashboards/layouts/styles, document-upload utility and paired contracts. The findings below describe the pre-fix review; see the resolution addendum for fixes and validation. All examples use synthetic data; provider calls were mocked.

Eight reproducible findings: six P2 (medium), two P3 (low). No P0/P1 defect was established in the tested synthetic workflows. Existing authentication/persistence gaps are documented separately and are not counted as newly discovered defects.

## 1. P2 — Accepted monetary strings cause HTTP 500

Location: `apps/api/app/core/money.py:15`, called from `apps/api/app/domains/developers/service.py:24`; request declarations in `developers/schemas.py:42` and the `Money` alias.

Pydantic's decimal-place constraint accepts mathematically cent-exact strings with redundant trailing zeros, retaining their Decimal exponent. `usd` rejects any exponent below -2 and raises an uncaught ValueError after request validation.

Reproduction: submit an otherwise valid `POST /api/v1/projects/gap` with `cost_to_create_usd="1.2300"`. Actual: HTTP 500, `Internal Server Error`. The same occurs for `"1.000"`, `"0.000"` and `"0e-100000"`. It also occurs in itemized costs and classified source amounts. Ordinary `"1.00"` succeeds; genuinely fractional-cent `"0.001"` correctly returns 422.

Expected: normalize redundant zeros without rounding nonzero fractional cents, or consistently reject the request with 422 before business logic. Align the schema and shared money helper, then test every monetary entry point. Do not silently round `1.231`.

## 2. P2 — Already-entered funding is counted twice in scenarios

Location: `apps/api/app/domains/developers/ai_advisor.py:103`–`106`.

The scenario generator always subtracts the candidate's full amount from the current balance. It does not compare candidate IDs with confirmed/received funding IDs already used by `calculate_gap`.

Reproduction: project cost $100, a confirmed development-cash funding record `{id:"same", amount_usd:"40.00"}`, and a candidate with the same ID and $40 proposed amount. Actual authoritative gap: $60. Actual scenario gap: $20, counting the same $40 twice. Both IDs and statuses are available to detect this overlap.

Expected: reject or exclude candidates already included as confirmed/received development cash; define an explicit replacement/increment policy if existing sources may be increased. An assumption saying “without duplicating entered sources” does not enforce this constraint.

## 3. P2 — In-kind candidates become cash scenarios

Location: `apps/api/app/domains/developers/ai_advisor.py:11`–`19` and `104`–`106`.

`CandidateFundingSource` has no contribution-kind field. The model silently ignores an extra `contribution_kind="IN_KIND"`; the scenario generator converts every nonclosed development candidate amount into `hypothetical_cash_usd` regardless of terms.

Reproduction: $100 unfunded cost; candidate named “In-kind lumber”, amount $40, terms “IN-KIND ONLY: $40 of donated lumber. No cash will be paid.” Include `contribution_kind:"IN_KIND"` as well. Actual: the API returns a $40 hypothetical-cash scenario and a $60 hypothetical gap. The actual gap remains $100, but the financial scenario contradicts the supplied restriction.

Expected: add typed contribution classification to candidate contracts and gate cash scenarios on supported cash classification. In-kind or unknown-kind sources should receive a separate noncash/unknown assessment. Do not rely on prose restrictions to drive deterministic classification.

## 4. P2 — Project selection reuses another project's financial state

Location: `apps/web/src/components/developer/DeveloperDashboard.tsx:45` and `127`–`128`.

There is one `form` object for all projects. Clicking “Model this project” changes only the selected ID and clears the result. It neither restores a model keyed by that project nor resets the form.

Browser reproduction: enter $999,999 for project A, select project B, then calculate without further edits. Actual: B's card displays $999,999 cost and $559,999 gap using A's entered assumptions. No explicit “copy model to this project” action occurred. Switching back likewise cannot restore A's earlier independent model after edits to B.

Expected: maintain separate session models per project, or clearly reset and explicitly offer copying when selection changes. Database persistence is not needed to isolate session state.

## 5. P2 — A hidden invalid aggregate blocks valid itemized costs

Location: `apps/web/src/components/developer/DeveloperDashboard.tsx:156`–`165` and `176`–`183`; backend required field at `developers/schemas.py:42`.

Itemized mode hides the aggregate cost input, but still sends its previous value. That value remains required by the backend.

Browser reproduction: clear “Total development cost”; enable itemized mode; fill visible Construction with `535000.00`. All visible costs are now valid. Calculate. Captured payload still has `cost_to_create_usd:""` plus valid itemized costs. Passing that captured payload to the actual API returns 422 at `body.cost_to_create_usd`, a field the active form hides.

Expected: keep a valid compatibility aggregate in the request while itemized mode is active, or adapt the owned validation so itemized costs can replace an invalid aggregate without breaking existing clients. Keep source-of-truth calculations on the backend.

## 6. P2 — Toggling itemized mode silently erases cost edits

Location: `apps/web/src/components/developer/DeveloperDashboard.tsx:156`–`165`.

Every enable action creates a fresh itemized object; disabling sets it to null. Neither action retains the previous itemized draft or reconciles it to the aggregate.

Browser reproduction: enable itemized mode, set Land acquisition to `12345.67`, disable and re-enable it. Actual: Land is `0.00`; other itemized edits are also discarded. The aggregate remains the earlier total, so a user can unintentionally recalculate a materially different budget.

Expected: keep the itemized draft when switching modes. Define and communicate whether the aggregate represents an independent alternative or the itemized total. Require an explicit reset to discard edits.

## 7. P3 — An obsolete AI request can show an error for new inputs

Location: `apps/web/src/components/developer/AIFundingAdvisor.tsx:68`–`71`, `95`–`99`, and the unconditional error rendering near line 170.

Successful results are gated by `analyzedSnapshot === snapshot`; errors are not. The input-change effect clears an existing error but cannot prevent an older in-flight request from later writing a new error.

Browser reproduction: delay the advice response, edit a parent financial input while the request is pending, then return a 502 for that old request. Actual: its error appears on the changed model, which was never submitted.

Expected: associate errors with a request identity/snapshot and ignore obsolete completions, or abort/invalidate pending work on input changes. Apply the same policy to result, error and busy state.

## 8. P3 — Advisor formatting loses monetary precision

Location: `apps/web/src/components/developer/AIFundingAdvisor.tsx:181`–`183`.

The advisor converts a Decimal string to JavaScript Number, unlike the dashboard's exact string/BigInt formatter.

Reproduction: the actual gap API accepts cost `99999999999999.99` and returns that exact remaining gap. The advisor expression `Number("99999999999999.99").toLocaleString()` produces `99,999,999,999,999.98` on this host. The advisor and project dashboard therefore disagree by a cent for a valid input. The advisor also omits consistent two-decimal currency formatting for small/whole amounts.

Expected: use a shared owned decimal-string currency formatter for both displays. No financial Number conversion is needed for rendering.

## Verification and limits

- Existing full Python suite: **53 passed**. It does not cover the cases above; green baseline tests do not invalidate the reproduced defects.
- Additional randomized probe: **1,000 passed** for ordinary two-decimal cost/source inputs, totals, nonnegative gap/surplus, and potential/excluded classifications. No general arithmetic mismatch was found for correctly normalized inputs.
- TypeScript check: **passed**.
- Isolated Chromium probes reproduced project-state carryover, hidden invalid aggregate payloads, lost itemized drafts and stale async errors. Browser finance responses were explicitly synthetic transport mocks; captured invalid input was separately replayed against FastAPI's actual TestClient.
- Layout checks at 390, 360 and 320 CSS pixels: no document-level horizontal overflow in the probed developer state.
- Production build: **failed on existing misplaced `"use client"` directives in the homebuyer, manager, donor and employer dashboards**, outside Developer 5 ownership. These files were not changed.
- Admin source-freshness and queue tests passed. Real admin authorization/decisions/audit storage remain unavailable as previously documented. No privileged endpoint was introduced or treated as implemented.
- PDF signature validation remains deliberately limited, as already documented; this review did not claim it provides structural PDF validation or malware scanning.
- Live provider behavior, a formal accessibility audit and deployment security were not tested. No real Anthropic key or paid call was used.

Local diagnostic scripts and screenshots are stored under ignored `apps/api/.venv/dev5-review/`: `backend_probe.py`, `randomized_probe.py`, `extra_probe.py`, `browser_probe.cjs`, `developer-320.png`. Backend probes can be rerun from the repository root with `PYTHONPATH=apps/api` and the repository virtual-environment Python. The browser probe requires Playwright and the isolated Next.js server at localhost:3105; all its AI calls are intercepted.

This review added this report and ignored diagnostic artifacts only. Application code and existing tests were not changed or disabled. The temporary test server was stopped; pre-existing working-tree changes were preserved.

## Resolution — November 7, 2026

All eight findings above have been fixed within Developer 5 ownership. The original findings are retained as the pre-fix audit record.

| Finding | Implemented fix | Regression evidence |
| --- | --- | --- |
| 1: trailing-zero HTTP 500 | `core/money.py` now compares a cent-quantized value with the original Decimal, accepting redundant zeros and rejecting nonzero fractional cents without rounding. | Tests cover all six legacy fields, itemized costs, classified sources, extreme zero exponents, and invalid helper inputs. |
| 2: duplicate scenario funding | Candidate IDs already counted as confirmed/received development cash are excluded from additional-cash scenarios. | Tests cover confirmed/received duplicates, distinct additional sources, and same-ID unverified/pledged proposals. |
| 3: in-kind scenarios | Optional candidate `contribution_kind` is mirrored in Python/TypeScript; defaults to `UNKNOWN`. Only explicit `CASH` candidates generate cash scenarios. | Tests cover omitted/unknown/in-kind classifications plus buyer and closed candidates. Existing request shapes remain accepted; callers must explicitly classify cash to obtain a cash scenario. |
| 4: project state carryover | Editable pro formas and additional funding records are stored separately by project ID in session state. | Browser switches A/B/A and checks independent totals and source drafts. |
| 5: hidden invalid aggregate | Owned `prepareFinancials` supplies a zero compatibility aggregate when authoritative itemized costs are active, for both gap and advice requests. Backend still performs all totals. | Browser submits a cleared hidden aggregate with valid itemized costs against the actual API, including the advisor's deterministic financial context. |
| 6: lost itemized drafts | Itemized drafts are retained per project when toggling modes. Aggregate and itemized modes retain their independent assumptions. | Browser verifies land edits survive toggles and project switches. |
| 7: stale asynchronous errors | Advisor request versions invalidate old completions on input changes/unmount. Only the current request can write a result, error or busy state. | Delayed old failure cannot overwrite newer advice or clear a newer request's pending state. |
| 8: imprecise display | New owned `finance.ts` formats decimal strings using integer grouping and exact cents; both dashboard and advisor use it. | Browser verifies the exact large valid amount returned by the real finance API. |

Validation after fixes: full Python suite **94 passed** (41 additional parametrized regression cases); TypeScript check **passed**; **1,000 randomized financial cases passed**; new browser regression groups **passed**. The browser harness adapts CORS only for isolated ports and mocks every Claude response, so no paid provider calls occur. The shared CORS configuration is unchanged.

New source files: `apps/web/src/components/developer/finance.ts` and `apps/api/tests/test_dev5_browser_regressions.cjs`. Other fixes are confined to `core/money.py`, developer advisor/backend/UI files, the owned AI contract and Developer 5 tests. No other developer's implementation, shared manifest, global styling or router registration was changed.

Rerun browser regressions with local API at `127.0.0.1:18081`, Next.js at `localhost:3105` configured with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:18081/api/v1`, and `PLAYWRIGHT_MODULE` pointing to an installed Playwright package. Run `node apps/api/tests/test_dev5_browser_regressions.cjs`. URLs can be overridden using `DEV5_API_URL` and `DEV5_WEB_URL`.

Production integration blockers from the implementation report remain separate: other domains' client-directive build errors, authentication, persistence, verified registry import and global branding. Shared `next-env.d.ts` already had a pre-existing change at the start of this fix pass; its contents were preserved.
