"""No actual employer programs are verified in this scaffold."""
from decimal import Decimal
from .schemas import EmployerProgram
SYNTHETIC_EMPLOYER_PROGRAMS = [
    EmployerProgram(
        id="demo-employer-aid", employer_label="FICTIONAL SoCal Employer",
        program_name="DEMO Workforce Down Payment Support", county="Orange",
        assistance_type="EMPLOYEE_DOWN_PAYMENT", award_cap_usd=Decimal("10000.00"),
    ),
    EmployerProgram(
        id="demo-employer-project", employer_label="FICTIONAL SoCal Employer",
        program_name="DEMO Nonprofit Home Sponsorship", county="Orange",
        assistance_type="NONPROFIT_PROJECT_SPONSORSHIP", award_cap_usd=Decimal("30000.00"),
    ),
]
