"""Helper package for shared test fixtures and constants.

This module re-exports constants from ``tests.helpers.shared`` so callers can
import them as ``from tests.helpers import DEFAULT_CALCULATION_CASES``. The
``__all__`` makes it clear these names are part of the public package API and
prevents flake8 F401 (imported but unused) warnings in pre-commit.
"""
from .shared import DEFAULT_CALCULATION_CASES, INTEREST_RATE_SCHEMA, LOAN_PERIOD_SCHEMA

__all__ = [
    "DEFAULT_CALCULATION_CASES",
    "INTEREST_RATE_SCHEMA",
    "LOAN_PERIOD_SCHEMA",
]
