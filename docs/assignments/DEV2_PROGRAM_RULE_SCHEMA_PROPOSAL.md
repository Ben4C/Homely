# Dev 2 proposal: validated program rule facts for matching

**Status:** Proposal for Dev 1 review. No cross-domain contract was changed by this proposal.

The manager extraction response is an AI draft and must never be consumed by matching. Matching should accept only facts from a manager-verified program version. Suggested payload:

```ts
type VerifiedProgramRuleVersion = {
  program_id: string;
  version_id: string;
  version_number: number;
  effective_at: string; // ISO 8601 date/time
  source: {
    url: string;
    title: string;
    published_at: string | null;
    retrieved_at: string;
    content_hash: string;
    authority: string;
  };
  reviewer: { reviewer_id: string; verified_at: string };
  eligibility_rules: Array<{
    criterion: string;
    operator: "eq" | "in" | "lte" | "gte" | "exists";
    value: string | number | boolean | string[];
    evidence_excerpt: string;
    evidence_locator: string | null;
  }>;
  required_documents: string[];
  deadline: string | null;
  assistance_limit_usd: string | null;
  availability: "VERIFIED_OPEN" | "VERIFIED_CLOSED" | "WAITLIST" | "UNKNOWN";
  funding_checked_at: string | null;
  status: "VERIFIED";
};
```

Proposed matching behavior:

- Require `status: "VERIFIED"`, an effective rule version, and a source/reviewer audit record.
- Evaluate against the historical version applicable to the application date; pin the version on each application so later edits do not silently change in-flight reviews.
- Treat missing values as unknown and return `NEEDS_REVIEW`; never infer eligibility or availability from missing facts.
- Keep funding availability separate from eligibility and require a recent manager verification for an open offer.
- Do not provide a conversion path from `ProgramExtractResponse` to this type. A human must confirm every fact against the official source.

This proposal is for integration discussion with Dev 1 before adding shared matching contracts.
