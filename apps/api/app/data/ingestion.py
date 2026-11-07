"""Idempotent imports never overwrite reviewed program/organization data."""

import hashlib
import json
from uuid import uuid4
from sqlalchemy import select
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
    AuditEvent,
    ImportDraft,
    utcnow,
)
from .schemas import CatalogInput, SourceInput, ProgramInput


# Purpose: Identify unchanged source content across imports. Inputs: canonical JSON-able record; outputs: stable content identity.
def fingerprint(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


# Purpose: Retain immutable retrieval snapshots. Inputs: validated source and review flag; outputs: existing/new source ID.
def store_source(session: Session, source: SourceInput, reviewed: bool) -> str:
    data = source.model_dump(mode="json")
    key = fingerprint(data)
    if session.get(Source, key) is None:
        values = source.model_dump()
        values["url"] = str(source.url)
        session.add(
            Source(
                id=key,
                **values,
                reviewed_at=utcnow() if reviewed and source.verified else None
            )
        )
        session.flush()
    return key


# Purpose: Append immutable eligibility history. Inputs: program, validated rules and reviewed source; outputs: new rule version.
def append_rules(
    session: Session,
    program: Program,
    rules: list,
    source_id: str,
    actor_id: str,
    effective_on=None,
) -> None:
    program.current_rule_version += 1
    rule_set = RuleSet(
        id=uuid4().hex,
        program_id=program.id,
        version=program.current_rule_version,
        source_id=source_id,
        reviewed_at=utcnow(),
        reviewer_id=actor_id,
        effective_on=effective_on,
    )
    session.add(rule_set)
    session.flush()
    for rule in rules:
        session.add(Rule(id=uuid4().hex, rule_set_id=rule_set.id, **rule.model_dump()))


# Purpose: Record only public resource changes, never credentials or household data.
# Inputs: authenticated/local-operator actor and transition; outputs: appended audit event in the same transaction.
def audit(
    session: Session,
    actor: str,
    action: str,
    resource: str,
    kind: str,
    old: str | None,
    new: str | None,
    reason: str,
) -> None:
    session.add(
        AuditEvent(
            id=uuid4().hex,
            actor_id=actor,
            action=action,
            resource_id=resource,
            resource_kind=kind,
            previous_status=old,
            new_status=new,
            reason=reason,
        )
    )


# Purpose: Stage source changes for human review instead of mutating published records.
# Inputs: canonical record; outputs: deduplicated pending draft.
def stage_change(session: Session, kind: str, resource_id: str, payload: dict) -> None:
    key = fingerprint({"kind": kind, "record": payload})
    if session.get(ImportDraft, key) is None:
        session.add(
            ImportDraft(
                id=key, resource_id=resource_id, resource_kind=kind, payload=payload
            )
        )


# Purpose: Atomically normalize/store a catalog with source-based deduplication and retained review history.
# Inputs: validated catalog and explicit local-operator reviewed publication; outputs: insertion/unchanged/staged counts.
# Constraints: The CLI is an operator interface. HTTP imports/edits must independently require reviewer authorization.
def import_catalog(
    session: Session,
    catalog: CatalogInput,
    publish_reviewed: bool = False,
    actor_id: str = "catalog-import",
) -> dict:
    counts = {
        "organizations_inserted": 0,
        "programs_inserted": 0,
        "unchanged": 0,
        "staged": 0,
    }
    for area in catalog.areas:
        existing = session.get(Area, area.id)
        if existing is None:
            session.add(Area(**area.model_dump()))
            session.flush()
        elif (existing.name, existing.kind, existing.parent_id) != (
            area.name,
            area.kind,
            area.parent_id,
        ):
            raise ValueError("Geographic identifiers cannot be reassigned")
    for item in catalog.organizations:
        source_id = store_source(session, item.source, publish_reviewed)
        existing = session.get(Organization, item.id) or session.scalar(
            select(Organization).where(Organization.website == str(item.website))
        )
        if existing:
            if existing.id != item.id:
                raise ValueError(
                    "Organization website already belongs to a different ID"
                )
            if (
                existing.source_id == source_id
                and all(
                    getattr(existing, k) == v
                    for k, v in item.model_dump(
                        mode="json", exclude={"source", "area_ids"}
                    ).items()
                )
                and set(
                    session.scalars(
                        select(OrganizationArea.area_id).where(
                            OrganizationArea.organization_id == item.id
                        )
                    )
                )
                == set(item.area_ids)
            ):
                counts["unchanged"] += 1
            else:
                stage_change(
                    session, "ORGANIZATION", item.id, item.model_dump(mode="json")
                )
                counts["staged"] += 1
            continue
        values = item.model_dump(exclude={"source", "area_ids"})
        values["website"] = str(item.website)
        reviewed = publish_reviewed and item.source.verified
        org = Organization(
            **values,
            source_id=source_id,
            verification_status=(
                "OFFICIAL_SITE_VERIFIED" if reviewed else "DRAFT_UNVERIFIED"
            ),
            reviewed_at=utcnow() if reviewed else None
        )
        session.add(org)
        session.flush()
        for area in item.area_ids:
            session.add(OrganizationArea(organization_id=item.id, area_id=area))
        audit(
            session,
            actor_id,
            "IMPORT",
            item.id,
            "ORGANIZATION",
            None,
            org.verification_status,
            "Source-backed catalog import",
        )
        session.add(
            ImportDraft(
                id=fingerprint({"organization": item.model_dump(mode="json")}),
                resource_id=item.id,
                resource_kind="ORGANIZATION",
                payload=item.model_dump(mode="json"),
                status="IMPORTED",
            )
        )
        counts["organizations_inserted"] += 1
    session.flush()
    for item in catalog.programs:
        source_id = store_source(session, item.source, publish_reviewed)
        existing = session.get(Program, item.id) or session.scalar(
            select(Program).where(Program.official_url == str(item.official_url))
        )
        if existing:
            if existing.id != item.id:
                raise ValueError("Program URL already belongs to a different ID")
            # Compare the complete candidate payload so changed rules/metadata sharing a URL are not lost.
            payload = item.model_dump(mode="json")
            payload_key = fingerprint(payload)
            initial_event = session.scalar(
                select(ImportDraft).where(ImportDraft.id == payload_key)
            )
            accepted = session.get(
                ImportDraft, fingerprint({"kind": "PROGRAM", "record": payload})
            )
            if initial_event is not None or (
                accepted and accepted.status == "ACCEPTED"
            ):
                counts["unchanged"] += 1
            else:
                stage_change(session, "PROGRAM", item.id, payload)
                counts["staged"] += 1
            continue
        values = item.model_dump(
            exclude={
                "source",
                "purchase_area_ids",
                "residence_area_ids",
                "rules",
                "effective_on",
            }
        )
        values["official_url"] = str(item.official_url)
        values["application_url"] = (
            str(item.application_url) if item.application_url else None
        )
        reviewed = publish_reviewed and item.source.verified
        values["availability"] = item.availability if reviewed else "DRAFT_UNVERIFIED"
        program = Program(
            **values,
            source_id=source_id,
            published=reviewed,
            reviewed_at=utcnow() if reviewed else None
        )
        session.add(program)
        session.flush()
        for purpose, areas in [
            ("PURCHASE", item.purchase_area_ids),
            ("RESIDENCE", item.residence_area_ids),
        ]:
            for area in set(areas):
                session.add(
                    ProgramArea(program_id=item.id, area_id=area, purpose=purpose)
                )
        if reviewed and item.rules:
            append_rules(
                session, program, item.rules, source_id, actor_id, item.effective_on
            )
        payload = item.model_dump(mode="json")
        session.add(
            ImportDraft(
                id=fingerprint(payload),
                resource_id=item.id,
                resource_kind="PROGRAM",
                payload=payload,
                status="IMPORTED",
            )
        )
        audit(
            session,
            actor_id,
            "IMPORT",
            item.id,
            "PROGRAM",
            None,
            program.availability,
            "Source-backed catalog import; availability separate from program existence",
        )
        counts["programs_inserted"] += 1
    session.flush()
    return counts
