"""
Shared test schemas and test data to avoid duplicate-code (used by multiple tests).

This module centralizes small, stable pieces of test data and JSON-schema
fragments so tests can import them instead of duplicating identical literals
across multiple files (avoids pylint R0801 duplicate-code complaints).
"""

INTEREST_RATE_SCHEMA = {
    "type": "number",
    "description": "金利（0.0-1.0）",
    "default": 0.025,
}

LOAN_PERIOD_SCHEMA = {
    "type": "integer",
    "description": "返済期間（年）",
    "default": 25,
}

# Common calculation test cases (numbers are representative sample fixtures)
DEFAULT_CALCULATION_CASES = {
    "basic_case": {
        "purchase_price": 30000000,
        "monthly_rent": 120000,
        "annual_expenses": 156000,
        "loan_amount": 24000000,
        "interest_rate": 0.025,
        "loan_period": 25,
        "down_payment": 6000000,
    },
    "high_yield_case": {
        "purchase_price": 20000000,
        "monthly_rent": 150000,
        "annual_expenses": 200000,
        "loan_amount": 16000000,
        "interest_rate": 0.03,
        "loan_period": 20,
        "down_payment": 4000000,
    },
    "low_yield_case": {
        "purchase_price": 50000000,
        "monthly_rent": 200000,
        "annual_expenses": 400000,
        "loan_amount": 40000000,
        "interest_rate": 0.02,
        "loan_period": 30,
        "down_payment": 10000000,
    },
}
