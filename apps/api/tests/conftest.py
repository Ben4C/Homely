"""Legacy domain tests explicitly exercise demo compatibility; directory tests opt into isolated persistence."""

import pytest


# Purpose: Keep synthetic legacy test assumptions explicit. Inputs: test marker; outputs: selected compatibility mode only in tests.
@pytest.fixture(autouse=True)
def explicit_legacy_demo(request, monkeypatch):
    if request.node.get_closest_marker("registry") is None:
        monkeypatch.setenv("REGISTRY_MODE", "demo")
