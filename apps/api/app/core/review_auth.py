"""Opt-in local reviewer credentials; production identity-provider integration remains external."""

import hashlib
import hmac
import json
import os
from typing import Literal
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field


class Reviewer(BaseModel):
    actor_id: str = Field(min_length=1, max_length=100)
    role: Literal["ADMIN", "MANAGER"]
    organization_ids: list[str] = Field(default_factory=list)


# Purpose: Authenticate a server-configured reviewer without trusting client actor IDs.
# Inputs: Bearer credential and server-only hash-to-role map; outputs: scoped reviewer or safe denial.
def require_reviewer(authorization: str | None = Header(default=None)) -> Reviewer:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            401,
            "A reviewer credential is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        configured = json.loads(os.getenv("HOMELY_REVIEWERS_JSON", "{}"))
        if not isinstance(configured, dict):
            raise ValueError("Invalid reviewer map")
        digest = hashlib.sha256(authorization[7:].encode()).hexdigest()
        for expected, identity in configured.items():
            if hmac.compare_digest(digest, expected):
                return Reviewer.model_validate(identity)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            503, "Reviewer authorization is not configured correctly"
        ) from exc
    raise HTTPException(403, "Reviewer credential is not authorized")


# Purpose: Enforce administrator or owning-manager authority. Inputs: trusted identity and resource owner; outputs: denial on mismatch.
def authorize_review(
    actor: Reviewer, organization_id: str, admin_only: bool = False
) -> None:
    if actor.role != "ADMIN" and (
        admin_only or organization_id not in actor.organization_ids
    ):
        raise HTTPException(
            403, "This reviewer cannot modify that organization or program"
        )
