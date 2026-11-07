# Directory operations

The `app/data` package separates strict import schemas, immutable source/rule storage, ingestion, deterministic screening, HTTP review, and presentation contracts. `DATABASE_URL` belongs in the API process; never expose it through `NEXT_PUBLIC_` variables.

## Database and catalog

From `apps/api`, install `pip install -e '.[dev]'`, set a PostgreSQL/psycopg `DATABASE_URL`, and run `python -m alembic upgrade head`. The frozen migration creates normalized areas, organizations, organization areas, programs, purchase/residence program areas, source evidence, rule sets/rules, import drafts, and audit events. It includes foreign keys, source/URL uniqueness, amount/status constraints, and search indexes. API startup never creates schema implicitly.

```powershell
python -m app.data.cli import app/data/seed/southern_california.json --publish-reviewed --reviewer local-source-review
python -m app.data.cli import-leads app/data/seed/manual_review_leads.json
```

The publication flag is an explicit local operator attestation, not a fresh scrape. Inspect source evidence/dates first. Without it, newly imported program records stay unpublished. Source retrieval dates are retained; rerunning an old catalog cannot prove current availability. Reimports are idempotent. Changed records become review drafts rather than overwriting reviewed fields. New rule publications append versions. The CLI transaction rolls back on validation/relational failures.

The three inaccessible municipal pages remain **manual-review leads**, with no invented program terms: Santa Ana, Fullerton, and Costa Mesa. Review access restrictions manually; do not bypass them.

## Reviewer access

By default, no HTTP caller can review records. Configure `HOMELY_REVIEWERS_JSON` in the server environment as a JSON object mapping **SHA-256 digests of random access tokens** to identities:

```json
{
  "<sha256-of-a-random-token>": {
    "actor_id": "your-reviewer-id",
    "role": "MANAGER",
    "organization_ids": ["city-garden-grove"]
  }
}
```

Use cryptographically random tokens (for example `secrets.token_urlsafe(32)`), keep them in an untracked secret store, hash them with `hashlib.sha256(token.encode()).hexdigest()`, and supply the raw token only in the manager/admin reviewer password field. An `ADMIN` can review all public-directory resources; a `MANAGER` can review programs owned by configured organization IDs. Only admins can verify organizations. This is a local operator mechanism, not production account management. Use TLS and an identity provider before external deployment.

The UI keeps credentials in component memory only. It requires original-source evidence, a reason, current revision, and explicit attestation. Save operations lock records, reject stale revisions with `409`, and commit record/source/rule/audit changes together. The server records the configured actor. Review does not approve applicants or authorize funds.

To publish AI-derived rules, independently check the original source, normalize the extracted draft to supported `RuleInput` JSON, and use the optional structured-rules field. Rules support household-size income tables, first-time status, household-size bounds, employer, and purchase price. Unsupported restrictions remain explicit text requiring human verification.

## Freshness and scheduled monitoring

`REGISTRY_REVERIFY_DAYS` defaults to **30**. Missing/future/expired review evidence cannot produce an accepting-applications result. Closed dates take precedence. This is evaluated on reads without silently rewriting history.

Run the bounded, official-host allowlisted monitor from `apps/api`:

```powershell
python -m app.data.cli check-sources
```

The monitor uses HTTPS, disallows redirects, caps documents at 5 MiB, times out requests, and deduplicates change/error drafts. It never publishes changes or interprets a new page as open intake. An absent baseline hash produces a manual-review flag. Source excerpts in the starter catalog were manually curated, so hashes are absent where raw document retrieval was not retained.

Suggested schedule: daily in the deployment scheduler, running under a restricted service identity. Example cron, after supplying `DATABASE_URL` through a service secret:

```cron
15 6 * * * cd /srv/homely/apps/api && .venv/bin/python -m app.data.cli check-sources
```

No machine-level scheduler was installed by this change. Staff the review queue and adjust cadence to each source's update frequency. An informational page does not prove funds are available.

## Testing and rollback

Use `TEST_DATABASE_URL` pointing only to a separate database whose name ends `_test`. Directory tests apply migrations, import source records, and roll back individual test writes. Without that variable they use temporary SQLite files for fast tests. Existing domain fixtures are enabled explicitly by the compatibility-test fixture.

```powershell
python -m pytest -q
# Only on a disposable, explicitly selected test database:
python -m alembic downgrade base
python -m alembic upgrade head
```

Downgrade removes directory tables and their data. Back up a real store and review migrations before operational changes; do not use the disposable-test rollback procedure against a populated deployment.

This workspace was also tested with an ignored portable PostgreSQL installation because Docker was unavailable. Its persistent cluster is `apps/api/.venv/integration/pgdata`, bound to `127.0.0.1:55432`; it uses local trust authentication for isolated development only. Use the password-authenticated Compose configuration or managed PostgreSQL for deployment. The portable binaries, cluster, reviewer token, internal audit, and screenshots are excluded from Git.
