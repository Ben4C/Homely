"""Public directory endpoints and opt-in, scoped reviewer operations."""

from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import directory_session
from app.core.review_auth import Reviewer, require_reviewer, authorize_review
from .models import (
    Area,
    Source,
    Organization,
    OrganizationArea,
    Program,
    ProgramArea,
    AuditEvent,
    ImportDraft,
    utcnow,
)
from .schemas import (
    ReviewInput,
    OrganizationReviewInput,
    DraftReviewInput,
    ProgramInput,
    OrganizationInput,
    ProgramView,
    ProgramSearchResponse,
)
from .ingestion import store_source, append_rules, audit
from .repository import search_programs, search_organizations, program_view, fresh

router = APIRouter()


# Purpose: Commit a validated review atomically and report relational conflicts safely. Inputs: request session; outputs: committed transaction or 409.
def commit_review(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            409,
            "Conflicting directory data; reload and review the record identifiers and source URLs",
        ) from exc


# Purpose: Search persistent source-backed programs. Inputs: bounded query filters; outputs: paginated, explainable discovery.
@router.get("/funding-programs/search", response_model=ProgramSearchResponse)
def search(
    county: str | None = Query(None, max_length=120),
    city: str | None = Query(None, max_length=120),
    zip_code: str | None = Query(None, pattern=r"^\d{5}$"),
    residence_county: str | None = Query(None, max_length=120),
    residence_city: str | None = Query(None, max_length=120),
    q: str | None = Query(None, max_length=120),
    category: str | None = Query(None, max_length=40),
    assistance_type: str | None = Query(None, max_length=40),
    organization_type: Literal["GOVERNMENT", "NONPROFIT"] | None = None,
    channel: str | None = Query(None, max_length=40),
    status: (
        Literal[
            "VERIFIED_OPEN",
            "VERIFIED_CLOSED",
            "WAITLIST",
            "UNKNOWN",
            "STALE",
            "DRAFT_UNVERIFIED",
        ]
        | None
    ) = None,
    accepting_applications: bool = False,
    funding_track: (
        Literal["BUYER", "DEVELOPMENT", "UPSTREAM", "REFERRAL"] | None
    ) = None,
    first_time_buyer: bool | None = None,
    household_income: Decimal | None = Query(
        None, ge=0, max_digits=16, decimal_places=2
    ),
    household_size: int | None = Query(None, ge=1, le=30),
    employer: str | None = Query(None, max_length=120),
    purchase_price: Decimal | None = Query(None, ge=0, max_digits=16, decimal_places=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: Literal["name", "reviewed"] = "name",
    session: Session = Depends(directory_session),
) -> dict:
    filters = locals().copy()
    filters.pop("session")
    return search_programs(session, **filters)


# Purpose: Supply known internal geographic identifiers without invented ZIP mapping. Inputs: none; outputs: supported areas.
@router.get("/funding-programs/locations")
def locations(session: Session = Depends(directory_session)) -> dict:
    return {
        "areas": [
            {"id": a.id, "name": a.name, "kind": a.kind, "parent_id": a.parent_id}
            for a in session.scalars(select(Area).order_by(Area.name))
        ]
    }


# Purpose: Expose one published program and its source/rule history. Inputs: stable ID; outputs: public detail or 404.
@router.get("/funding-programs/{program_id}", response_model=ProgramView)
def detail(program_id: str, session: Session = Depends(directory_session)) -> dict:
    program = session.get(Program, program_id)
    if not program or not program.published:
        raise HTTPException(404, "Published program not found")
    return program_view(session, program, purchase=None)


# Purpose: Search real organizations independently from financial opportunities. Inputs: bounded location/name filters; outputs: directory page.
@router.get("/organizations/search")
def organizations(
    county: str | None = Query(None, max_length=120),
    city: str | None = Query(None, max_length=120),
    q: str | None = Query(None, max_length=120),
    kind: Literal["GOVERNMENT", "NONPROFIT"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: Session = Depends(directory_session),
) -> dict:
    return search_organizations(session, county, city, q, kind, page, page_size)


# Purpose: Show one source-backed organization with related programs. Inputs: ID; outputs: public detail without partner/funding claims.
@router.get("/organizations/{organization_id}")
def organization_detail(
    organization_id: str, session: Session = Depends(directory_session)
) -> dict:
    items = search_organizations(session, page_size=10000)["organizations"]
    org = next((item for item in items if item["id"] == organization_id), None)
    if not org:
        raise HTTPException(404, "Organization not found")
    org["programs"] = [
        program_view(session, p, purchase=None)
        for p in session.scalars(
            select(Program).where(
                Program.organization_id == organization_id, Program.published.is_(True)
            )
        )
    ]
    return org


# Purpose: Provide authorized public-data review and audit queues. Inputs: trusted identity; outputs: scoped records, drafts and audit events.
@router.get("/directory/review-queue")
def review_queue(
    actor: Reviewer = Depends(require_reviewer),
    session: Session = Depends(directory_session),
) -> dict:
    query = select(Program)
    if actor.role != "ADMIN":
        query = query.where(Program.organization_id.in_(actor.organization_ids))
    programs = list(session.scalars(query))
    allowed = {p.id for p in programs}
    org_query = select(Organization)
    if actor.role != "ADMIN":
        org_query = org_query.where(Organization.id.in_(actor.organization_ids))
    orgs = list(session.scalars(org_query))
    allowed |= {o.id for o in orgs}
    allowed |= {p.source_id for p in programs} | {o.source_id for o in orgs}
    return {
        "programs": [program_view(session, p, purchase=None) for p in programs],
        "organizations": [
            {
                "id": o.id,
                "name": o.display_name,
                "revision": o.revision,
                "status": o.verification_status,
                "source_url": session.get(Source, o.source_id).url,
            }
            for o in orgs
        ],
        "drafts": [
            {
                "id": d.id,
                "resource_id": d.resource_id,
                "kind": d.resource_kind,
                "status": d.status,
                "payload": d.payload,
            }
            for d in session.scalars(
                select(ImportDraft).where(ImportDraft.status == "PENDING")
            )
            if actor.role == "ADMIN" or d.resource_id in allowed
        ],
        "audit": [
            {
                "id": a.id,
                "actor_id": a.actor_id,
                "action": a.action,
                "occurred_at": a.occurred_at,
                "resource_id": a.resource_id,
                "resource_kind": a.resource_kind,
                "previous_status": a.previous_status,
                "new_status": a.new_status,
                "reason": a.reason,
            }
            for a in session.scalars(
                select(AuditEvent)
                .where(AuditEvent.resource_id.in_(allowed))
                .order_by(AuditEvent.occurred_at.desc())
                .limit(100)
            )
        ],
        "actor_id": actor.actor_id,
        "role": actor.role,
    }


# Purpose: Atomically publish/review source evidence and optional new rule version under owner authorization.
# Inputs: current revision, reviewed evidence, status/rules; outputs: updated record; conflicts return 409.
@router.post("/directory/programs/{program_id}/review")
def review_program(
    program_id: str,
    body: ReviewInput,
    actor: Reviewer = Depends(require_reviewer),
    session: Session = Depends(directory_session),
) -> dict:
    program = session.scalar(
        select(Program).where(Program.id == program_id).with_for_update()
    )
    if not program:
        raise HTTPException(404, "Program not found")
    authorize_review(actor, program.organization_id)
    if program.revision != body.expected_revision:
        raise HTTPException(409, "The program changed; reload before reviewing")
    if body.status != "DRAFT_UNVERIFIED" and (
        not body.source.verified or not fresh(body.source.retrieved_at)
    ):
        raise HTTPException(
            422, "Publication requires recently retrieved verified source evidence"
        )
    old = program.availability
    source_id = store_source(session, body.source, True)
    program.source_id = source_id
    program.availability = body.status
    program.reviewed_at = utcnow()
    program.published = body.status != "DRAFT_UNVERIFIED"
    program.revision += 1
    if body.rules is not None:
        if not body.source.verified:
            raise HTTPException(
                422, "Unverified extraction cannot become a published rule version"
            )
        append_rules(session, program, body.rules, source_id, actor.actor_id)
    audit(
        session,
        actor.actor_id,
        "REVIEW_PROGRAM",
        program.id,
        "PROGRAM",
        old,
        body.status,
        body.reason,
    )
    commit_review(session)
    return program_view(session, program, purchase=None)


# Purpose: Record administrator-only organization evidence reviews. Inputs: trusted actor and revision; outputs: auditable status change.
@router.post("/directory/organizations/{organization_id}/review")
def review_organization(
    organization_id: str,
    body: OrganizationReviewInput,
    actor: Reviewer = Depends(require_reviewer),
    session: Session = Depends(directory_session),
) -> dict:
    org = session.scalar(
        select(Organization).where(Organization.id == organization_id).with_for_update()
    )
    if not org:
        raise HTTPException(404, "Organization not found")
    authorize_review(actor, org.id, admin_only=True)
    if org.revision != body.expected_revision:
        raise HTTPException(409, "Organization changed; reload before reviewing")
    if body.status == "OFFICIAL_SITE_VERIFIED" and (
        not body.source.verified or not fresh(body.source.retrieved_at)
    ):
        raise HTTPException(422, "Recent source evidence is required")
    old = org.verification_status
    org.source_id = store_source(session, body.source, True)
    org.verification_status = body.status
    org.reviewed_at = utcnow()
    org.revision += 1
    audit(
        session,
        actor.actor_id,
        "REVIEW_ORGANIZATION",
        org.id,
        "ORGANIZATION",
        old,
        body.status,
        body.reason,
    )
    commit_review(session)
    return {"id": org.id, "status": org.verification_status, "revision": org.revision}


# Purpose: Resolve changed-import drafts without overwriting manually reviewed records automatically.
# Inputs: scoped actor, source attestation and expected revision; outputs: reviewed import plus immutable audit.
@router.post("/directory/import-drafts/{draft_id}/review")
def review_import(
    draft_id: str,
    body: DraftReviewInput,
    actor: Reviewer = Depends(require_reviewer),
    session: Session = Depends(directory_session),
) -> dict:
    draft = session.scalar(
        select(ImportDraft).where(ImportDraft.id == draft_id).with_for_update()
    )
    if not draft or draft.status != "PENDING":
        raise HTTPException(409, "Draft is missing or already reviewed")
    program = (
        session.get(Program, draft.resource_id)
        if draft.resource_kind == "PROGRAM"
        else None
    )
    organization = (
        session.get(Organization, draft.resource_id)
        if draft.resource_kind == "ORGANIZATION"
        else None
    )
    authorize_review(
        actor,
        program.organization_id if program else draft.resource_id,
        admin_only=program is None,
    )
    if not body.source_checked:
        raise HTTPException(422, "Explicit original-source review is required")
    if body.decision == "ACCEPT" and draft.resource_kind not in {
        "PROGRAM",
        "ORGANIZATION",
    }:
        raise HTTPException(
            422,
            "Source/lead notifications can be acknowledged; consequential publication requires a program review",
        )
    record = program or organization
    if record and body.expected_revision != record.revision:
        raise HTTPException(409, "Resource changed; reload before resolving the draft")
    if body.decision == "ACCEPT":
        item = (ProgramInput if program else OrganizationInput).model_validate(
            draft.payload
        )
        if not item.source.verified or not fresh(item.source.retrieved_at):
            raise HTTPException(422, "Fresh verified source evidence is required")
        source_id = store_source(session, item.source, True)
        if program:
            if (
                actor.role != "ADMIN"
                and item.organization_id != program.organization_id
            ):
                raise HTTPException(
                    403, "Only an administrator can change program ownership"
                )
            values = item.model_dump(
                mode="json",
                exclude={
                    "source",
                    "purchase_area_ids",
                    "residence_area_ids",
                    "rules",
                    "effective_on",
                    "application_opens_on",
                    "application_closes_on",
                    "id",
                },
            )
            for key, value in values.items():
                setattr(program, key, value)
            program.application_opens_on = item.application_opens_on
            program.application_closes_on = item.application_closes_on
            program.source_id = source_id
            program.published = True
            program.reviewed_at = utcnow()
            program.revision += 1
            session.query(ProgramArea).filter(
                ProgramArea.program_id == program.id
            ).delete()
            for purpose, ids in [
                ("PURCHASE", item.purchase_area_ids),
                ("RESIDENCE", item.residence_area_ids),
            ]:
                for area_id in set(ids):
                    session.add(
                        ProgramArea(
                            program_id=program.id, area_id=area_id, purpose=purpose
                        )
                    )
            append_rules(
                session,
                program,
                item.rules,
                source_id,
                actor.actor_id,
                item.effective_on,
            )
        else:
            for key, value in item.model_dump(
                mode="json", exclude={"source", "area_ids", "id"}
            ).items():
                setattr(organization, key, value)
            organization.source_id = source_id
            organization.reviewed_at = utcnow()
            organization.verification_status = "OFFICIAL_SITE_VERIFIED"
            organization.revision += 1
            session.query(OrganizationArea).filter(
                OrganizationArea.organization_id == organization.id
            ).delete()
            for area_id in set(item.area_ids):
                session.add(
                    OrganizationArea(organization_id=organization.id, area_id=area_id)
                )
    draft.status = {
        "ACCEPT": "ACCEPTED",
        "REJECT": "REJECTED",
        "ACKNOWLEDGE": "ACKNOWLEDGED",
    }[body.decision]
    audit(
        session,
        actor.actor_id,
        "REVIEW_IMPORT",
        draft.resource_id,
        draft.resource_kind,
        "PENDING",
        draft.status,
        body.reason,
    )
    commit_review(session)
    return {"id": draft.id, "status": draft.status}


# Purpose: Report public directory counts without applicant or financial data. Inputs: persistent session; outputs: truthful overview metrics.
@router.get("/directory/overview")
def overview(session: Session = Depends(directory_session)) -> dict:
    from .repository import availability

    statuses = [
        availability(session, p)
        for p in session.scalars(select(Program).where(Program.published.is_(True)))
    ]
    return {
        "organizations": session.scalar(select(func.count()).select_from(Organization)),
        "published_programs": len(statuses),
        "stale_programs": statuses.count("STALE"),
        "unknown_availability": statuses.count("UNKNOWN"),
        "pending_source_reviews": session.scalar(
            select(func.count())
            .select_from(ImportDraft)
            .where(ImportDraft.status == "PENDING")
        ),
    }
