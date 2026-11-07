"""Fictional buyer profile; never use actual customer data for testing."""
from decimal import Decimal
from .schemas import HomebuyerProfile
SYNTHETIC_PROFILE = HomebuyerProfile(
    profile_id="demo-buyer", county="Orange", household_size=3,
    annual_income_usd=Decimal("52000.00"), first_time_buyer=True,
    employer_name=None,
)
