"""Explainable location search and conservative screening of persisted directory records."""

import os
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import (
    Area,
    Source,
    Organization,
    OrganizationArea,
    Program,
    ProgramArea,
    RuleSet,
    Rule,
)


# Purpose: Normalize SQLite/PostgreSQL timestamps for freshness comparisons. Inputs: stored timestamp; outputs: UTC-aware time.
def aware(value):
    return (
        value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value
    )


# Purpose: Evaluate configured review freshness. Inputs: timestamp; outputs: false for missing, future or stale evidence.
def fresh(value) -> bool:
    if value is None:
        return False
    days = (datetime.now(timezone.utc) - aware(value)).total_seconds() / 86400
    return 0 <= days <= int(os.getenv("REGISTRY_REVERIFY_DAYS", "30"))


# Purpose: Resolve normalized geography without guessing postal/city coverage. Inputs: county/city/ZIP; outputs: requested area or safe 422.
def resolve_area(session: Session, county=None, city=None, zip_code=None):
    if zip_code:
        postal = session.scalar(
            select(Area).where(Area.kind == "ZIP", Area.name == zip_code)
        )
        if not postal:
            raise HTTPException(
                422,
                "No verified ZIP mapping is available. Select a county and city instead.",
            )
        if county or city:
            selected = resolve_area(session, county, city)
            if selected and selected.id not in lineage(session, postal.id):
                raise HTTPException(422, "ZIP does not match the selected county/city")
        return postal
    selected = None
    if county:
        county = county.strip()
        if county.lower().endswith(" county"):
            county = county[:-7]
        selected = session.scalar(
            select(Area).where(
                Area.kind == "COUNTY", func.lower(Area.name) == county.casefold()
            )
        )
        if selected is None:
            raise HTTPException(422, "County is not supported by this directory")
    if city:
        query = select(Area).where(
            Area.kind == "CITY", func.lower(Area.name) == city.strip().casefold()
        )
        if selected:
            query = query.where(Area.parent_id == selected.id)
        matches = session.scalars(query).all()
        if len(matches) != 1:
            raise HTTPException(
                422, "City is unknown or does not belong to the selected county"
            )
        selected = matches[0]
    return selected


# Purpose: Walk normalized ancestors with cycle protection. Inputs: area ID; outputs: exact city/county/state lineage.
def lineage(session: Session, area_id: str) -> set[str]:
    result = set()
    while area_id and area_id not in result:
        result.add(area_id)
        area = session.get(Area, area_id)
        area_id = area.parent_id if area else None
    return result


# Purpose: Separate exact compatibility from incomplete county-only queries. Inputs: area IDs and selected target; outputs: true/false/unknown.
def compatibility(session: Session, covered: list[str], target) -> bool | None:
    if not covered:
        return None
    if target is None:
        return None
    ancestors = lineage(session, target.id)
    if set(covered) & ancestors:
        return True
    if any(target.id in lineage(session, item) for item in covered):
        return None
    return False


# Purpose: Derive safe current availability from evidence and dates. Inputs: persistent program; outputs: display status without database mutation.
def availability(session: Session, program: Program) -> str:
    source = session.get(Source, program.source_id)
    if not program.published:
        return "DRAFT_UNVERIFIED"
    if (
        not source.verified
        or not fresh(source.retrieved_at)
        or not fresh(program.reviewed_at)
    ):
        return "STALE" if program.reviewed_at else "UNKNOWN"
    today = datetime.now(timezone.utc).date()
    if program.application_closes_on and program.application_closes_on < today:
        return "VERIFIED_CLOSED"
    if program.application_opens_on and program.application_opens_on > today:
        return "UNKNOWN"
    return program.availability


# Purpose: Evaluate only explicitly sourced versioned criteria, without approvals or AI scores.
# Inputs: program, location and minimum household facts; outputs: preliminary category and specific reasons.
def screen(
    session: Session,
    program: Program,
    purchase,
    residence=None,
    income=None,
    household_size=None,
    first_time_buyer=None,
    employer=None,
    purchase_price=None,
) -> dict:
    coverage = session.scalars(
        select(ProgramArea.area_id).where(
            ProgramArea.program_id == program.id, ProgramArea.purpose == "PURCHASE"
        )
    ).all()
    geo = compatibility(session, coverage, purchase)
    reasons = []
    missing = []
    failed = []
    if geo is False:
        return {
            "outcome": "OUTSIDE_SERVICE_AREA",
            "explanations": [
                "Intended purchase location is outside the published service area."
            ],
        }
    if geo is None:
        missing.append(
            "Select the intended purchase city to resolve the published geographic restriction."
        )
    else:
        reasons.append(
            "Intended purchase location matches the published service geography; this alone is not full eligibility."
        )
    current = availability(session, program)
    if current in {"VERIFIED_CLOSED", "WAITLIST"}:
        return {
            "outcome": "PROGRAM_UNAVAILABLE",
            "explanations": reasons
            + [
                f"Application status is {current}; this is not an accepting-applications result."
            ],
        }
    if program.funding_track in {"UPSTREAM", "DEVELOPMENT", "REFERRAL"}:
        return {
            "outcome": "ADDITIONAL_INFORMATION_REQUIRED",
            "explanations": reasons
            + [
                "This listing is not a direct individual homebuyer grant. Follow the specified administrator/referral channel."
            ],
        }
    if current in {"STALE", "DRAFT_UNVERIFIED"}:
        return {
            "outcome": "ELIGIBILITY_NOT_VERIFIED",
            "explanations": reasons
            + [
                "Source verification is missing or stale. Confirm current rules and availability."
            ],
        }
    resident_areas = session.scalars(
        select(ProgramArea.area_id).where(
            ProgramArea.program_id == program.id, ProgramArea.purpose == "RESIDENCE"
        )
    ).all()
    if resident_areas:
        compatible = compatibility(session, resident_areas, residence)
        if compatible is False:
            failed.append(
                "Current residence does not meet the separately published residency restriction."
            )
        elif compatible is None:
            missing.append(
                "Current residence is needed to check a separate residency requirement."
            )
        else:
            reasons.append(
                "Current residence matches the published residency requirement."
            )
    ruleset = session.scalar(
        select(RuleSet).where(
            RuleSet.program_id == program.id,
            RuleSet.version == program.current_rule_version,
        )
    )
    if (
        not ruleset
        or not fresh(ruleset.reviewed_at)
        or not session.get(Source, ruleset.source_id).verified
        or (
            ruleset.effective_on
            and ruleset.effective_on > datetime.now(timezone.utc).date()
        )
    ):
        return {
            "outcome": (
                "KNOWN_CRITERIA_NOT_MET" if failed else "ELIGIBILITY_NOT_VERIFIED"
            ),
            "explanations": reasons
            + failed
            + missing
            + [
                "Current verified eligibility rules are not available; no income limit is inferred from the assistance award."
            ],
        }
    rules = list(session.scalars(select(Rule).where(Rule.rule_set_id == ruleset.id)))
    if not any(r.criterion == "MAX_INCOME" for r in rules):
        missing.append(
            "Verified income and household-size thresholds are unavailable. An assistance award is not an income limit."
        )
    for rule in rules:
        value = rule.value
        if rule.criterion == "MAX_INCOME":
            limit = value.get("by_household_size", {}).get(str(household_size))
            if limit is None or income is None:
                missing.append(
                    "A verified income threshold for this household size and the household income are required."
                )
            elif Decimal(str(income)) > Decimal(str(limit)):
                failed.append(
                    f"Household income exceeds the published ${limit} limit for {household_size} people."
                )
            else:
                reasons.append(
                    f"Income is within the published ${limit} limit for {household_size} people; assistance amount is a separate field."
                )
        elif rule.criterion == "FIRST_TIME_BUYER" and value["required"]:
            if first_time_buyer is None:
                missing.append("First-time buyer status must be confirmed.")
            elif not first_time_buyer:
                failed.append(
                    "The published first-time homebuyer requirement is not met."
                )
            else:
                reasons.append(
                    "Reported first-time buyer status matches this known requirement."
                )
        elif rule.criterion == "EMPLOYER":
            if not employer:
                missing.append("Employer information is required for this program.")
            elif employer.casefold() != value["name"].casefold():
                failed.append(
                    "Reported employer does not meet the published restriction."
                )
        elif rule.criterion == "MAX_PRICE":
            if purchase_price is None:
                missing.append("Intended purchase price is required.")
            elif Decimal(str(purchase_price)) > Decimal(value["amount_usd"]):
                failed.append("Purchase price exceeds the published cap.")
        elif rule.criterion in {"MIN_HOUSEHOLD", "MAX_HOUSEHOLD"}:
            if household_size is None:
                missing.append("Household size is required.")
            elif (
                rule.criterion == "MIN_HOUSEHOLD" and household_size < value["size"]
            ) or (rule.criterion == "MAX_HOUSEHOLD" and household_size > value["size"]):
                failed.append("Household size does not meet the published requirement.")
    outcome = (
        "KNOWN_CRITERIA_NOT_MET"
        if failed
        else ("ADDITIONAL_INFORMATION_REQUIRED" if missing else "POTENTIALLY_ELIGIBLE")
    )
    return {
        "outcome": outcome,
        "explanations": reasons
        + failed
        + missing
        + [
            "Only known verified criteria were screened. Lender/administrator review and current funding confirmation remain required."
        ],
    }


# Purpose: Serialize a source-backed program with public provenance, normalized geography and preliminary screening.
# Inputs: persistent row and optional household/location; outputs: JSON-compatible public detail.
def program_view(session: Session, program: Program, **profile) -> dict:
    source = session.get(Source, program.source_id)
    org = session.get(Organization, program.organization_id)
    areas = session.execute(
        select(Area, ProgramArea.purpose)
        .join(ProgramArea, ProgramArea.area_id == Area.id)
        .where(ProgramArea.program_id == program.id)
    ).all()
    ruleset = session.scalar(
        select(RuleSet).where(
            RuleSet.program_id == program.id,
            RuleSet.version == program.current_rule_version,
        )
    )
    rules = (
        session.scalars(select(Rule).where(Rule.rule_set_id == ruleset.id)).all()
        if ruleset
        else []
    )
    return {
        "id": program.id,
        "name": program.name,
        "description": program.description,
        "organization_id": org.id,
        "organization_name": org.display_name,
        "organization_type": org.kind,
        "originating_source": program.originating_source,
        "government_level": program.government_level,
        "category": program.category,
        "assistance_type": program.assistance_type,
        "loan_grant": program.loan_grant,
        "channel": program.channel,
        "funding_track": program.funding_track,
        "max_assistance_usd": (
            str(program.max_assistance_usd)
            if program.max_assistance_usd is not None
            else None
        ),
        "min_assistance_usd": (
            str(program.min_assistance_usd)
            if program.min_assistance_usd is not None
            else None
        ),
        "assistance_formula": program.assistance_formula,
        "application_url": program.application_url,
        "official_url": program.official_url,
        "application_opens_on": program.application_opens_on,
        "application_closes_on": program.application_closes_on,
        "availability": availability(session, program),
        "last_verified_at": program.reviewed_at,
        "source_url": source.url,
        "source_title": source.title,
        "source_retrieved_at": source.retrieved_at,
        "source_published_on": source.published_on,
        "source_evidence": source.evidence,
        "source_page_reference": source.page_reference,
        "source_content_hash": source.content_hash,
        "source_verified": source.verified and fresh(program.reviewed_at),
        "revision": program.revision,
        "eligibility_rule_version": program.current_rule_version,
        "rules": [
            {"criterion": r.criterion, "value": r.value, "explanation": r.explanation}
            for r in rules
        ],
        "rule_history": [
            {
                "version": v.version,
                "reviewed_at": v.reviewed_at,
                "effective_on": v.effective_on,
                "source_url": session.get(Source, v.source_id).url,
            }
            for v in session.scalars(
                select(RuleSet)
                .where(RuleSet.program_id == program.id)
                .order_by(RuleSet.version)
            )
        ],
        "restrictions": program.restrictions,
        "areas": [
            {"id": a.id, "name": a.name, "kind": a.kind, "purpose": purpose}
            for a, purpose in areas
        ],
        **screen(session, program, **profile),
    }


# Purpose: Query persisted programs with validated location, truthful status filters, pagination and deterministic sorting.
# Inputs: search/household filters; outputs: page of source-backed programs and total, never fixture fallback.
def search_programs(
    session: Session,
    *,
    county=None,
    city=None,
    zip_code=None,
    residence_county=None,
    residence_city=None,
    q=None,
    category=None,
    assistance_type=None,
    organization_type=None,
    channel=None,
    status=None,
    accepting_applications=False,
    funding_track=None,
    first_time_buyer=None,
    household_income=None,
    household_size=None,
    employer=None,
    purchase_price=None,
    page=1,
    page_size=10,
    sort="name",
    include_drafts=False,
) -> dict:
    purchase = resolve_area(session, county, city, zip_code)
    residence = resolve_area(session, residence_county, residence_city)
    query = select(Program).join(Organization)
    if not include_drafts:
        query = query.where(Program.published.is_(True))
    if q:
        query = query.where(
            func.lower(Program.name + " " + Organization.display_name).contains(
                q.casefold().strip(), autoescape=True
            )
        )
    if category:
        query = query.where(Program.category == category)
    if assistance_type:
        query = query.where(Program.assistance_type == assistance_type)
    if organization_type:
        query = query.where(Organization.kind == organization_type)
    if channel:
        query = query.where(Program.channel == channel)
    if funding_track:
        query = query.where(Program.funding_track == funding_track)
    programs = []
    for record in session.scalars(query):
        coverage = session.scalars(
            select(ProgramArea.area_id).where(
                ProgramArea.program_id == record.id, ProgramArea.purpose == "PURCHASE"
            )
        ).all()
        if compatibility(session, coverage, purchase) is False:
            continue
        view = program_view(
            session,
            record,
            purchase=purchase,
            residence=residence,
            income=household_income,
            household_size=household_size,
            first_time_buyer=first_time_buyer,
            employer=employer,
            purchase_price=purchase_price,
        )
        if status and view["availability"] != status:
            continue
        if accepting_applications and view["availability"] != "VERIFIED_OPEN":
            continue
        programs.append(view)
    programs.sort(
        key=(
            (lambda p: (str(p["last_verified_at"] or ""), p["id"]))
            if sort == "reviewed"
            else (lambda p: (p["name"].casefold(), p["id"]))
        ),
        reverse=sort == "reviewed",
    )
    return {
        "demo": False,
        "programs": programs[(page - 1) * page_size : page * page_size],
        "total": len(programs),
        "page": page,
        "page_size": page_size,
        "disclaimer": "Source-backed directory; preliminary screening is not approval or a guarantee of funding.",
    }


# Purpose: Query real organizations independently from whether funding is offered. Inputs: geography/name; outputs: public organizations.
def search_organizations(
    session: Session, county=None, city=None, q=None, kind=None, page=1, page_size=10
) -> dict:
    target = resolve_area(session, county, city)
    query = select(Organization)
    if kind:
        query = query.where(Organization.kind == kind)
    if q:
        query = query.where(
            func.lower(Organization.display_name).contains(
                q.casefold().strip(), autoescape=True
            )
        )
    items = []
    for org in session.scalars(query):
        areas = session.scalars(
            select(OrganizationArea.area_id).where(
                OrganizationArea.organization_id == org.id
            )
        ).all()
        if compatibility(session, areas, target) is False:
            continue
        source = session.get(Source, org.source_id)
        items.append(
            {
                "id": org.id,
                "legal_name": org.legal_name,
                "name": org.display_name,
                "kind": org.kind,
                "website": org.website,
                "headquarters": org.headquarters,
                "contact": org.contact,
                "services": org.services,
                "charitable_status": org.charitable_status,
                "verification_status": (
                    org.verification_status
                    if (fresh(org.reviewed_at) and fresh(source.retrieved_at))
                    or not org.reviewed_at
                    else "STALE"
                ),
                "last_verified_at": org.reviewed_at,
                "source_url": source.url,
                "source_title": source.title,
                "source_evidence": source.evidence,
                "source_retrieved_at": source.retrieved_at,
                "areas": [{"id": a, "name": session.get(Area, a).name} for a in areas],
                "revision": org.revision,
                "homely_partner": False,
            }
        )
    items.sort(key=lambda o: (o["name"].casefold(), o["id"]))
    return {
        "demo": False,
        "organizations": items[(page - 1) * page_size : page * page_size],
        "total": len(items),
        "page": page,
        "page_size": page_size,
    }
