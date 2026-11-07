# Security and financial integrity requirements

**THIS SCAFFOLD IS NOT A PRODUCTION SYSTEM.** No live housing application, PII, grants, loans, or payments may be administered here.

1. **Auth/RBAC:** Production login via identity provider; users may have multiple organization memberships with explicitly scoped permissions. Verify tenant/org access on every resource.
2. **Applicant privacy:** Minimize intake; encrypt sensitive data and private document storage; consent-based disclosure and revocation; retention/deletion policy. Keep employment verification separate from employee income files.
3. **Fair housing:** No protected-class inference or arbitrary urgency score; eligibility and queue ranking only from verified program rules and lawful processes.
4. **Program sourcing:** Official URL, eligibility ruleset version, retrieved date, last verification, funding availability status. Never automatically mark an unverified government program as open.
5. **No automated payments:** Only authorized nonprofit/payment/escrow provider releases money after the appropriate approvals. Use real financial provider ledger/reconciliation only after compliance/legal review.
6. **Restricted funds:** Track source restrictions; donations cannot be redirected contrary to donor terms; employee funding cannot be repurposed for unrelated households.
7. **Financial transaction integrity:** Decimal amounts, immutable events, idempotency keys, authorized transitions, DB transactions and row locks, double-entry accounting when real processing begins.
8. **Audit:** Log access and every application decision, financial approval and rule change; mask personal data.
9. **Data providers:** Do not scrape restricted information, fabricate awards, or claim funds remain based on outdated pages.
10. **Review:** Before production, get legal/compliance review for California housing laws, mortgage lending, tax-deductibility, grants, data protection, payment services, and equitable selection.

## v0.2 Claude-specific controls

- API key read from `ANTHROPIC_API_KEY` in backend process only; never shipped in frontend JS, env public variables or HTTP responses.
- Explicit consent for text/PDF processing. For hackathon, only synthetic or redacted documents should be submitted.
- 4 MiB maximum base64 PDF with `%PDF-` header validation; source instructions are treated as untrusted data. Formal malware checks, PDF sanitization, retention and authenticated access are still TODO(prod).
- AI responses are unverified drafts. Official source verification and applicant review stay with authorized people.
- `messages.parse` Pydantic output currently provides **AI-proposed evidence excerpts**, not source-verified native citations. Add a citation retrieval/validation pass before relying on them operationally.
- Production must add rate limits, quotas, origin-based restrictions, CSRF/auth, logs with PII redaction, prompt injection evaluations and provider compliance review.
- Sponsorship preview reports zero allocatable funds. In-kind valuations aren't cash, and employer matches need employee/donation eligibility and verified money receipt.
