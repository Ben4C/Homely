"""Normalized directory, immutable source/rule history and transactional public-data review."""

from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Purpose: Timestamp directory events in UTC. Inputs: none; outputs: timezone-aware timestamp.
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Area(Base):
    __tablename__ = "directory_areas"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(12))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("directory_areas.id"))
    __table_args__ = (
        UniqueConstraint("parent_id", "kind", "name"),
        CheckConstraint("kind IN ('STATE','COUNTY','CITY','ZIP')"),
    )


class Source(Base):
    __tablename__ = "directory_sources"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_on: Mapped[date | None] = mapped_column(Date)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[str] = mapped_column(Text)
    page_reference: Mapped[str | None] = mapped_column(String(100))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Organization(Base):
    __tablename__ = "directory_organizations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(250))
    display_name: Mapped[str] = mapped_column(String(200), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    website: Mapped[str] = mapped_column(Text, unique=True)
    headquarters: Mapped[str | None] = mapped_column(String(200))
    contact: Mapped[dict] = mapped_column(JSON, default=dict)
    services: Mapped[list] = mapped_column(JSON, default=list)
    charitable_status: Mapped[dict] = mapped_column(JSON, default=dict)
    source_id: Mapped[str] = mapped_column(ForeignKey("directory_sources.id"))
    verification_status: Mapped[str] = mapped_column(
        String(30), default="DRAFT_UNVERIFIED"
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(Integer, default=1)


class OrganizationArea(Base):
    __tablename__ = "directory_organization_areas"
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("directory_organizations.id"), primary_key=True
    )
    area_id: Mapped[str] = mapped_column(
        ForeignKey("directory_areas.id"), primary_key=True
    )


class Program(Base):
    __tablename__ = "directory_programs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(250), index=True)
    description: Mapped[str] = mapped_column(Text)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("directory_organizations.id"), index=True
    )
    originating_source: Mapped[str | None] = mapped_column(String(200))
    government_level: Mapped[str | None] = mapped_column(String(30))
    category: Mapped[str] = mapped_column(String(40))
    assistance_type: Mapped[str] = mapped_column(String(40))
    loan_grant: Mapped[str] = mapped_column(String(30))
    channel: Mapped[str] = mapped_column(String(40))
    funding_track: Mapped[str] = mapped_column(String(20))
    min_assistance_usd: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    max_assistance_usd: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    assistance_formula: Mapped[str | None] = mapped_column(Text)
    application_url: Mapped[str | None] = mapped_column(Text)
    official_url: Mapped[str] = mapped_column(Text, unique=True)
    application_opens_on: Mapped[date | None] = mapped_column(Date)
    application_closes_on: Mapped[date | None] = mapped_column(Date)
    availability: Mapped[str] = mapped_column(String(30), default="UNKNOWN", index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("directory_sources.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    current_rule_version: Mapped[int] = mapped_column(Integer, default=0)
    restrictions: Mapped[list] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        CheckConstraint("max_assistance_usd IS NULL OR max_assistance_usd >= 0"),
        CheckConstraint("min_assistance_usd IS NULL OR min_assistance_usd >= 0"),
        CheckConstraint(
            "min_assistance_usd IS NULL OR max_assistance_usd IS NULL OR min_assistance_usd <= max_assistance_usd"
        ),
        CheckConstraint(
            "availability IN ('VERIFIED_OPEN','VERIFIED_CLOSED','WAITLIST','UNKNOWN','STALE','DRAFT_UNVERIFIED')"
        ),
        CheckConstraint(
            "funding_track IN ('BUYER','DEVELOPMENT','UPSTREAM','REFERRAL')"
        ),
        Index("ix_directory_programs_public_status", "published", "availability"),
    )


class ProgramArea(Base):
    __tablename__ = "directory_program_areas"
    program_id: Mapped[str] = mapped_column(
        ForeignKey("directory_programs.id"), primary_key=True
    )
    area_id: Mapped[str] = mapped_column(
        ForeignKey("directory_areas.id"), primary_key=True
    )
    purpose: Mapped[str] = mapped_column(String(12), primary_key=True)
    __table_args__ = (
        CheckConstraint("purpose IN ('PURCHASE','RESIDENCE')"),
        Index("ix_directory_program_areas_lookup", "area_id", "purpose"),
    )


class RuleSet(Base):
    __tablename__ = "directory_rule_sets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    program_id: Mapped[str] = mapped_column(
        ForeignKey("directory_programs.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[str] = mapped_column(ForeignKey("directory_sources.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_on: Mapped[date | None] = mapped_column(Date)
    reviewer_id: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("program_id", "version"),)


class Rule(Base):
    __tablename__ = "directory_rules"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rule_set_id: Mapped[str] = mapped_column(
        ForeignKey("directory_rule_sets.id"), index=True
    )
    criterion: Mapped[str] = mapped_column(String(40))
    value: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)


class AuditEvent(Base):
    __tablename__ = "directory_audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(80))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    resource_id: Mapped[str] = mapped_column(String(100), index=True)
    resource_kind: Mapped[str] = mapped_column(String(30))
    previous_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str | None] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(String(1000))


class ImportDraft(Base):
    __tablename__ = "directory_import_drafts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(100), index=True)
    resource_kind: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
