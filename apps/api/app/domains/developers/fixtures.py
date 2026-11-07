"""Synthetic project example from the challenge (not a real development)."""
from .schemas import HousingProject
SYNTHETIC_PROJECTS = [
    HousingProject(id="demo-project-1", project_name="DEMO Santa Ana Single Home", county="Orange", units=1, status="SYNTHETIC"),
    HousingProject(id="demo-project-2", project_name="DEMO Garden Grove Home", county="Orange", units=1, status="SYNTHETIC"),
]
