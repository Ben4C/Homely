"""Strict, source-backed import and review contracts."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=2)]
Status = Literal[
    "VERIFIED_OPEN",
    "VERIFIED_CLOSED",
    "WAITLIST",
    "UNKNOWN",
    "STALE",
    "DRAFT_UNVERIFIED",
]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceInput(StrictInput):
    url: HttpUrl
    title: str = Field(min_length=1, max_length=300)
    retrieved_at: datetime
    published_on: date | None = None
    evidence: str = Field(min_length=1, max_length=2000)
    page_reference: str | None = None
    content_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    verified: bool = False

    # Purpose: Prevent undated/future source verification claims. Inputs: retrieval time; outputs: valid UTC-aware provenance.
    @model_validator(mode="after")
    def validate_time(self):
        if self.retrieved_at.tzinfo is None or self.retrieved_at > datetime.now(
            timezone.utc
        ):
            raise ValueError(
                "Source retrieval must be timezone-aware and not in the future"
            )
        return self


class AreaInput(StrictInput):
    id: str = Field(pattern=r"^[a-z0-9:-]+$", max_length=120)
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["STATE", "COUNTY", "CITY", "ZIP"]
    parent_id: str | None = None


class OrganizationInput(StrictInput):
    id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    legal_name: str = Field(min_length=1, max_length=250)
    display_name: str = Field(min_length=1, max_length=200)
    kind: Literal["GOVERNMENT", "NONPROFIT"]
    website: HttpUrl
    headquarters: str | None = None
    contact: dict[str, str] = Field(default_factory=dict)
    services: list[str] = Field(default_factory=list)
    charitable_status: dict = Field(default_factory=dict)
    source: SourceInput
    area_ids: list[str] = Field(min_length=1)


class RuleInput(StrictInput):
    criterion: Literal[
        "MAX_INCOME",
        "FIRST_TIME_BUYER",
        "MAX_PRICE",
        "MIN_HOUSEHOLD",
        "MAX_HOUSEHOLD",
        "EMPLOYER",
    ]
    value: dict
    explanation: str = Field(min_length=1, max_length=1000)

    # Purpose: Validate deterministic supported criteria, keeping income and award caps distinct.
    # Inputs: criterion-specific values; outputs: safe rule or validation error.
    @model_validator(mode="after")
    def validate_rule(self):
        if self.criterion == "MAX_INCOME":
            limits = self.value.get("by_household_size", {})
            if (
                not isinstance(limits, dict)
                or not limits
                or any(not str(k).isdigit() or not 1 <= int(k) <= 30 for k in limits)
            ):
                raise ValueError(
                    "Income rules require household-size-specific thresholds"
                )
            for amount in limits.values():
                from app.core.money import usd

                usd(str(amount))
            self.value = {
                **self.value,
                "by_household_size": {
                    str(size): str(usd(str(amount))) for size, amount in limits.items()
                },
            }
        elif self.criterion == "MAX_PRICE":
            from app.core.money import usd

            self.value = {
                **self.value,
                "amount_usd": str(usd(str(self.value.get("amount_usd")))),
            }
        elif (
            self.criterion == "FIRST_TIME_BUYER"
            and type(self.value.get("required")) is not bool
        ):
            raise ValueError("First-time buyer requirement must be a boolean")
        elif self.criterion in {"MIN_HOUSEHOLD", "MAX_HOUSEHOLD"} and (
            type(self.value.get("size")) is not int or not 1 <= self.value["size"] <= 30
        ):
            raise ValueError("Household size must be 1 to 30")
        elif self.criterion == "EMPLOYER" and not self.value.get("name"):
            raise ValueError("Employer name is required")
        return self


class ProgramInput(StrictInput):
    id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    name: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=3000)
    organization_id: str
    originating_source: str | None = None
    government_level: str | None = None
    category: str
    assistance_type: str
    loan_grant: Literal["LOAN", "GRANT", "MIXED", "REFERRAL"]
    channel: Literal[
        "DIRECT_HOMEBUYER",
        "PARTICIPATING_LENDER",
        "PARTICIPATING_NONPROFIT",
        "LOCAL_ADMINISTERING_AGENCY",
        "DEVELOPMENT_FINANCING",
        "EXTERNAL_REFERRAL",
    ]
    funding_track: Literal["BUYER", "DEVELOPMENT", "UPSTREAM", "REFERRAL"]
    min_assistance_usd: Money | None = None
    max_assistance_usd: Money | None = None
    assistance_formula: str | None = None
    application_url: HttpUrl | None = None
    official_url: HttpUrl
    application_opens_on: date | None = None
    application_closes_on: date | None = None
    availability: Status = "UNKNOWN"
    source: SourceInput
    purchase_area_ids: list[str] = Field(min_length=1)
    residence_area_ids: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    rules: list[RuleInput] = Field(default_factory=list)
    effective_on: date | None = None

    # Purpose: Reject contradictory amount/date ranges and unverified availability claims.
    # Inputs: program fields; outputs: coherent import record.
    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.min_assistance_usd is not None
            and self.max_assistance_usd is not None
            and self.min_assistance_usd > self.max_assistance_usd
        ):
            raise ValueError("Minimum assistance exceeds maximum")
        if (
            self.application_opens_on
            and self.application_closes_on
            and self.application_opens_on > self.application_closes_on
        ):
            raise ValueError("Opening date exceeds closing date")
        if self.availability.startswith("VERIFIED_") and not self.source.verified:
            raise ValueError("Verified availability requires verified source evidence")
        return self


class CatalogInput(StrictInput):
    areas: list[AreaInput]
    organizations: list[OrganizationInput]
    programs: list[ProgramInput]


class ReviewInput(StrictInput):
    expected_revision: int = Field(ge=1)
    status: Status
    reason: str = Field(min_length=10, max_length=1000)
    source: SourceInput
    rules: list[RuleInput] | None = None


class OrganizationReviewInput(StrictInput):
    expected_revision: int = Field(ge=1)
    status: Literal["OFFICIAL_SITE_VERIFIED", "DRAFT_UNVERIFIED", "REJECTED"]
    reason: str = Field(min_length=10, max_length=1000)
    source: SourceInput


class DraftReviewInput(StrictInput):
    expected_revision: int | None = Field(default=None, ge=1)
    decision: Literal["ACCEPT", "REJECT", "ACKNOWLEDGE"]
    reason: str = Field(min_length=10, max_length=1000)
    source_checked: bool


class ProgramView(BaseModel):
    id: str
    name: str
    description: str
    organization_id: str
    organization_name: str
    organization_type: str
    originating_source: str | None
    government_level: str | None
    category: str
    assistance_type: str
    loan_grant: str
    channel: str
    funding_track: str
    max_assistance_usd: str | None
    min_assistance_usd: str | None
    assistance_formula: str | None
    application_url: str | None
    official_url: str
    application_opens_on: date | None
    application_closes_on: date | None
    availability: Status
    last_verified_at: datetime | None
    source_url: str
    source_title: str
    source_retrieved_at: datetime
    source_published_on: date | None
    source_evidence: str
    source_page_reference: str | None
    source_content_hash: str | None
    source_verified: bool
    revision: int
    eligibility_rule_version: int
    rules: list[RuleInput]
    restrictions: list[str]
    areas: list[dict[str, str]]
    outcome: Literal[
        "POTENTIALLY_ELIGIBLE",
        "OUTSIDE_SERVICE_AREA",
        "KNOWN_CRITERIA_NOT_MET",
        "ADDITIONAL_INFORMATION_REQUIRED",
        "PROGRAM_UNAVAILABLE",
        "ELIGIBILITY_NOT_VERIFIED",
    ]
    explanations: list[str]
    rule_history: list[dict] = Field(default_factory=list)


class ProgramSearchResponse(BaseModel):
    demo: Literal[False] = False
    programs: list[ProgramView]
    total: int
    page: int
    page_size: int
    disclaimer: str
