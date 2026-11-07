"""Shared configuration for demo. Replace with robust settings management."""

from os import getenv

# Purpose: Read basic demo-mode configuration; reject accidental live-money mode.
# Inputs: Environment variable DEMO_MODE (string, default true).
# Outputs: Boolean signaling that all workflows must remain simulated.
def is_demo_mode() -> bool:
    raw = getenv("DEMO_MODE", "true").lower()
    if raw not in {"true", "1", "yes"}:
        raise RuntimeError("Scaffold only supports DEMO_MODE=true; production integration is not implemented")
    return True
