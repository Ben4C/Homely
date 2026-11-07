"""Synthetic campaign proposals; unrelated to any real nonprofit."""
from decimal import Decimal
from .schemas import Campaign
SYNTHETIC_CAMPAIGNS = [
    Campaign(id="demo-campaign-1", organization_id="demo-oc-nonprofit", project_id="demo-project-1", title="DEMO Santa Ana Home", remaining_project_gap_usd=Decimal("25000.00")),
    Campaign(id="demo-campaign-2", organization_id="demo-oc-nonprofit", project_id="demo-project-2", title="DEMO Garden Grove Home", remaining_project_gap_usd=Decimal("40000.00")),
]
