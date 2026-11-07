"""Directory tests run on an isolated SQLite file or explicitly named PostgreSQL test database."""

import copy
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from app.main import app
from app.core.database import directory_session, legacy_directory_session
from app.data.models import (
    Base,
    Program,
    Organization,
    RuleSet,
    Rule,
    AuditEvent,
    ImportDraft,
    Source,
)
from app.data.schemas import CatalogInput
from app.data.ingestion import import_catalog

pytestmark = pytest.mark.registry


# Purpose: Keep rule amounts safe for exact currency display across numeric and exponent-form source inputs.
# Inputs: validated published income/price values; outputs: canonical decimal strings, distinct from assistance caps.
def test_rule_money_normalized_to_decimal_strings():
    from app.data.schemas import RuleInput

    income = RuleInput(
        criterion="MAX_INCOME",
        value={"by_household_size": {"1": 100000, "2": "1.2e5"}},
        explanation="Verified example table",
    )
    price = RuleInput(
        criterion="MAX_PRICE",
        value={"amount_usd": "5e5"},
        explanation="Verified example price limit",
    )
    assert income.value["by_household_size"] == {"1": "100000.00", "2": "120000.00"}
    assert price.value["amount_usd"] == "500000.00"


# Purpose: Provide isolated transactional records without resetting a real production store.
# Inputs: optional TEST_DATABASE_URL ending in _test; outputs: API client/session with all writes rolled back per test.
@pytest.fixture
def registry(tmp_path, monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        assert make_url(url).database.endswith(
            "_test"
        ), "Refusing to run directory tests against a non-test database"
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
        monkeypatch.setenv("DATABASE_URL", url)
        command.upgrade(config, "head")
        engine = create_engine(url)
    else:
        engine = create_engine(
            "sqlite:///" + str(tmp_path / "isolated-directory.sqlite"),
            connect_args={"check_same_thread": False},
        )

        # Purpose: Enforce relational constraints in the lightweight test dialect. Inputs: connection; outputs: foreign keys enabled.
        @event.listens_for(engine, "connect")
        def foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(engine)
    monkeypatch.setenv("REGISTRY_MODE", "database")
    reviewers = {
        hashlib.sha256(token.encode()).hexdigest(): identity
        for token, identity in [
            ("synthetic-admin-token", {"actor_id": "test-admin", "role": "ADMIN"}),
            (
                "synthetic-manager-token",
                {
                    "actor_id": "test-manager",
                    "role": "MANAGER",
                    "organization_ids": ["city-garden-grove"],
                },
            ),
        ]
    }
    monkeypatch.setenv("HOMELY_REVIEWERS_JSON", json.dumps(reviewers))
    catalog = CatalogInput.model_validate_json(
        (
            Path(__file__).parents[1] / "app/data/seed/southern_california.json"
        ).read_text()
    )
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    import_catalog(session, catalog, True, "test-source-review")
    session.commit()

    # Purpose: Route test requests into the rollback-only transaction. Inputs: none; outputs: isolated session.
    def isolated_session():
        yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[directory_session] = isolated_session
    app.dependency_overrides[legacy_directory_session] = isolated_session
    try:
        with TestClient(app) as client:
            yield client, session, catalog
    finally:
        app.dependency_overrides = previous
        session.close()
        outer.rollback()
        connection.close()
        engine.dispose()


# Purpose: Create an explicit authenticated source attestation. Inputs: current revision/status; outputs: supported review payload.
def review_body(revision=1, status="UNKNOWN"):
    return {
        "expected_revision": revision,
        "status": status,
        "reason": "Verified current official source during isolated test",
        "source": {
            "url": "https://ggcity.org/neighborhood-improvement/first-time-home-buyer-program",
            "title": "Synthetic reviewer evidence",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "evidence": "Synthetic evidence for isolated tests only",
            "verified": True,
        },
    }


# Purpose: Check source-backed imports persist and are idempotent. Inputs: repeat same catalog; outputs: no duplicate rows or rule versions.
def test_catalog_idempotent(registry):
    _, session, catalog = registry
    before = session.scalar(select(func.count()).select_from(RuleSet))
    result = import_catalog(session, catalog, True, "test-reviewer")
    assert result["unchanged"] == 16 and result["programs_inserted"] == 0
    assert session.scalar(select(func.count()).select_from(Program)) == 8
    assert session.scalar(select(func.count()).select_from(RuleSet)) == before


# Purpose: Reject fresh-availability claims from old catalog evidence and retain new retrieval history.
# Inputs: old source snapshot followed by a genuinely new retrieval; outputs: stale then refreshed evidence, with immutable history.
def test_old_source_cannot_be_refreshed_by_import_attestation(registry):
    client, session, _ = registry
    program = session.get(Program, "garden-grove-first-home")
    source = session.get(Source, program.source_id)
    source.retrieved_at = datetime.now(timezone.utc) - timedelta(days=45)
    program.availability = "VERIFIED_OPEN"
    program.reviewed_at = datetime.now(timezone.utc)
    session.commit()
    response = client.get("/api/v1/funding-programs/garden-grove-first-home").json()
    assert response["availability"] == "STALE"
    assert not client.get(
        "/api/v1/funding-programs/search?accepting_applications=true"
    ).json()["programs"]
    old_id = program.source_id
    payload = review_body(program.revision)
    response = client.post(
        "/api/v1/directory/programs/garden-grove-first-home/review",
        json=payload,
        headers={"Authorization": "Bearer synthetic-admin-token"},
    )
    assert response.status_code == 200
    session.refresh(program)
    assert program.source_id != old_id
    assert session.get(Source, old_id).retrieved_at == source.retrieved_at
    assert (
        client.get("/api/v1/funding-programs/garden-grove-first-home").json()[
            "availability"
        ]
        == "UNKNOWN"
    )


# Purpose: Preserve reviewed data when an upstream record changes. Inputs: changed program draft; outputs: pending review, original untouched.
def test_changed_import_stages_without_overwrite(registry):
    _, session, catalog = registry
    changed = catalog.model_copy(deep=True)
    changed.programs[0].description = "Changed source needs human review"
    result = import_catalog(session, changed, True, "importer")
    assert result["staged"] == 1
    assert (
        session.get(Program, "calhfa-myhome").description
        != "Changed source needs human review"
    )
    assert (
        session.scalar(select(ImportDraft).where(ImportDraft.status == "PENDING"))
        is not None
    )


# Purpose: Match geography with distinct city restrictions and statewide coverage. Inputs: county/city; outputs: relevant persisted IDs.
def test_county_city_search(registry):
    client, _, _ = registry
    r = client.get("/api/v1/funding-programs/search?county=Orange&city=Garden%20Grove")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()["programs"]}
    assert (
        "garden-grove-first-home" in ids
        and "my-anaheim-home" not in ids
        and "calhfa-myhome" in ids
    )
    assert (
        client.get(
            "/api/v1/funding-programs/search?county=Los%20Angeles&city=Garden%20Grove"
        ).status_code
        == 422
    )
    assert (
        client.get("/api/v1/funding-programs/search?zip_code=99999").status_code == 422
    )


# Purpose: Never infer income limits from award caps. Inputs: actual household-size thresholds; outputs: explicit pass/failure by known criteria.
@pytest.mark.parametrize(
    "income,size,outcome",
    [
        ("65000", 3, "POTENTIALLY_ELIGIBLE"),
        ("150000", 3, "KNOWN_CRITERIA_NOT_MET"),
        ("150000", 4, "POTENTIALLY_ELIGIBLE"),
        ("65000", 9, "ADDITIONAL_INFORMATION_REQUIRED"),
    ],
)
def test_household_income_threshold(registry, income, size, outcome):
    client, _, _ = registry
    r = client.get(
        f"/api/v1/funding-programs/search?q=Garden%20Grove&city=Garden%20Grove&household_income={income}&household_size={size}&first_time_buyer=true"
    )
    p = r.json()["programs"][0]
    assert p["outcome"] == outcome
    assert p["max_assistance_usd"] == "110000.00"
    assert p["source_url"].startswith("https://ggcity.org/")


# Purpose: Keep closed/stale sources out of accepting-applications results. Inputs: status changes; outputs: fresh status only.
def test_closed_and_stale_filter(registry):
    client, session, _ = registry
    assert (
        client.get(
            "/api/v1/funding-programs/search?accepting_applications=true"
        ).json()["total"]
        == 0
    )
    p = session.get(Program, "garden-grove-first-home")
    p.availability = "VERIFIED_OPEN"
    session.commit()
    assert (
        client.get(
            "/api/v1/funding-programs/search?accepting_applications=true"
        ).json()["total"]
        == 1
    )
    p.reviewed_at = datetime.now(timezone.utc) - timedelta(days=60)
    session.commit()
    assert (
        client.get(
            "/api/v1/funding-programs/search?accepting_applications=true"
        ).json()["total"]
        == 0
    )
    assert (
        client.get("/api/v1/funding-programs/search?status=STALE").json()["total"] == 1
    )


# Purpose: Paginate stable alphabetical results without fallback. Inputs: page/query filters; outputs: distinct pages and zero exact misses.
def test_pagination_and_empty_results(registry):
    client, _, _ = registry
    one = client.get("/api/v1/funding-programs/search?page_size=2").json()
    two = client.get("/api/v1/funding-programs/search?page_size=2&page=2").json()
    assert one["total"] == two["total"] == 8
    assert not {p["id"] for p in one["programs"]} & {p["id"] for p in two["programs"]}
    assert (
        client.get("/api/v1/funding-programs/search?q=does-not-exist").json()[
            "programs"
        ]
        == []
    )
    assert (
        client.get("/api/v1/funding-programs/search?page_size=101").status_code == 422
    )


# Purpose: Expose organizations without claiming partnership/tax status/funds. Inputs: nonprofit location search; outputs: real affiliate facts.
def test_nonprofit_search_and_detail(registry):
    client, _, _ = registry
    r = client.get("/api/v1/organizations/search?county=Orange&kind=NONPROFIT").json()
    assert [o["id"] for o in r["organizations"]] == ["habitat-oc"]
    org = client.get("/api/v1/organizations/habitat-oc").json()
    assert (
        org["homely_partner"] is False
        and org["charitable_status"]["status"] == "NOT_INDEPENDENTLY_CHECKED"
    )
    assert org["programs"][0]["id"] == "habitat-oc-homeownership"


# Purpose: Require trusted reviewer identity and enforce organization scope. Inputs: missing/invalid/scoped tokens; outputs: 401/403 or persisted review.
def test_authorized_review_and_conflict(registry):
    client, session, _ = registry
    path = "/api/v1/directory/programs/garden-grove-first-home/review"
    assert client.post(path, json=review_body()).status_code == 401
    assert (
        client.post(
            path, json=review_body(), headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 403
    )
    headers = {"Authorization": "Bearer synthetic-manager-token"}
    assert (
        client.post(
            "/api/v1/directory/programs/calhfa-myhome/review",
            json=review_body(),
            headers=headers,
        ).status_code
        == 403
    )
    r = client.post(path, json=review_body(status="VERIFIED_OPEN"), headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["revision"] == 2
    assert client.post(path, json=review_body(), headers=headers).status_code == 409
    assert (
        client.get(
            "/api/v1/funding-programs/search?accepting_applications=true"
        ).json()["total"]
        == 1
    )
    event_row = session.scalar(
        select(AuditEvent).where(AuditEvent.action == "REVIEW_PROGRAM")
    )
    assert (
        event_row.actor_id == "test-manager"
        and event_row.previous_status == "UNKNOWN"
        and event_row.new_status == "VERIFIED_OPEN"
    )


# Purpose: Append reviewed rules without destroying earlier versions. Inputs: canonical review; outputs: two immutable versions and new screening behavior.
def test_versioned_rules_and_no_unreviewed_publication(registry):
    client, session, _ = registry
    headers = {"Authorization": "Bearer synthetic-admin-token"}
    body = review_body()
    body["rules"] = [
        {
            "criterion": "FIRST_TIME_BUYER",
            "value": {"required": False},
            "explanation": "Synthetic changed rule for test",
        }
    ]
    r = client.post(
        "/api/v1/directory/programs/garden-grove-first-home/review",
        json=body,
        headers=headers,
    )
    assert r.status_code == 200, r.text
    versions = list(
        session.scalars(
            select(RuleSet).where(RuleSet.program_id == "garden-grove-first-home")
        )
    )
    assert {v.version for v in versions} == {1, 2}
    assert (
        session.scalar(
            select(func.count())
            .select_from(Rule)
            .where(Rule.rule_set_id == next(v.id for v in versions if v.version == 1))
        )
        == 2
    )
    body = review_body(revision=2, status="VERIFIED_OPEN")
    body["source"]["verified"] = False
    assert (
        client.post(
            "/api/v1/directory/programs/garden-grove-first-home/review",
            json=body,
            headers=headers,
        ).status_code
        == 422
    )


# Purpose: Separate residence from intended purchase geography in the legacy matching contract.
# Inputs: LA resident purchasing in Garden Grove; outputs: city-specific match from persistence, no fixture fallback.
def test_homebuyer_matching_uses_directory(registry):
    client, _, _ = registry
    body = {
        "profile": {
            "profile_id": "synthetic",
            "county": "Los Angeles",
            "purchase_county": "Orange",
            "purchase_city": "Garden Grove",
            "household_size": 3,
            "annual_income_usd": "65000",
            "first_time_buyer": True,
        }
    }
    result = client.post("/api/v1/homebuyers/match", json=body)
    assert result.status_code == 200, result.text
    assert result.json()["demo"] is False
    assert (
        next(
            p
            for p in result.json()["matches"]
            if p["program_id"] == "garden-grove-first-home"
        )["outcome"]
        == "POTENTIALLY_ELIGIBLE"
    )
    assert client.get("/api/v1/programs?county=Orange").json()["demo"] is False


# Purpose: Deny manager organization verification and append administrator reviews. Inputs: role-scoped credentials; outputs: correct privilege/audit behavior.
def test_organization_review_scope(registry):
    client, session, _ = registry
    body = review_body(status="OFFICIAL_SITE_VERIFIED")
    path = "/api/v1/directory/organizations/habitat-oc/review"
    assert (
        client.post(
            path, json=body, headers={"Authorization": "Bearer synthetic-manager-token"}
        ).status_code
        == 403
    )
    r = client.post(
        path, json=body, headers={"Authorization": "Bearer synthetic-admin-token"}
    )
    assert r.status_code == 200, r.text
    assert session.get(Organization, "habitat-oc").revision == 2


# Purpose: Fail clearly instead of fictional fallback when persistence is unavailable. Inputs: no DB URL and database mode; outputs: 503.
def test_missing_database_no_fictional_fallback(monkeypatch):
    monkeypatch.setenv("REGISTRY_MODE", "database")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as client:
        assert client.get("/api/v1/funding-programs/search").status_code == 503
        assert client.get("/api/v1/programs").status_code == 503


# Purpose: Apply changed metadata only after explicit scoped draft review, retaining rule history and idempotence.
# Inputs: changed source catalog and authenticated acceptance; outputs: updated public detail plus audit.
def test_accept_changed_import_and_idempotence(registry):
    client, session, catalog = registry
    changed = catalog.model_copy(deep=True)
    changed.programs[0].description = "Reviewed changed public description"
    import_catalog(session, changed, True, "importer")
    session.commit()
    draft = session.scalar(select(ImportDraft).where(ImportDraft.status == "PENDING"))
    response = client.post(
        "/api/v1/directory/import-drafts/" + draft.id + "/review",
        json={
            "expected_revision": 1,
            "decision": "ACCEPT",
            "reason": "Verified the changed official public description",
            "source_checked": True,
        },
        headers={"Authorization": "Bearer synthetic-admin-token"},
    )
    assert response.status_code == 200, response.text
    assert (
        client.get("/api/v1/funding-programs/calhfa-myhome").json()["description"]
        == "Reviewed changed public description"
    )
    assert import_catalog(session, changed, True, "importer")["unchanged"] == 16


# Purpose: Stage organization metadata changes even when source URL/evidence remains unchanged.
# Inputs: changed services; outputs: pending draft, unchanged reviewed organization.
def test_organization_metadata_change_requires_review(registry):
    _, session, catalog = registry
    changed = catalog.model_copy(deep=True)
    changed.organizations[0].services.append("NEW_UNREVIEWED_SERVICE")
    result = import_catalog(session, changed, True, "importer")
    assert result["staged"] == 1
    assert "NEW_UNREVIEWED_SERVICE" not in session.get(Organization, "calhfa").services


# Purpose: Reject malformed rule values as validation errors rather than internal exceptions.
# Inputs: invalid household-income rule payload; outputs: HTTP 422.
def test_malformed_rule_is_validation_error(registry):
    client, _, _ = registry
    body = review_body()
    body["rules"] = [
        {
            "criterion": "MAX_INCOME",
            "value": {"by_household_size": "invalid"},
            "explanation": "Malformed test",
        }
    ]
    assert (
        client.post(
            "/api/v1/directory/programs/garden-grove-first-home/review",
            json=body,
            headers={"Authorization": "Bearer synthetic-admin-token"},
        ).status_code
        == 422
    )
