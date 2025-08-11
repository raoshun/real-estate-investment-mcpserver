"""共通テストフィクスチャとセットアップ"""


from typing import Any, Dict

import pytest

from real_estate_mcp.models.investor_model import (
    InvestmentExperience,
    PersonalInvestor,
    RiskTolerance,
)
from real_estate_mcp.models.property_model import Property, PropertyType


@pytest.fixture
def sample_property_data() -> Dict[str, Any]:
    """サンプル物件データ"""
    return {
        "id": "test-property-001",
        "name": "テスト物件",
        "address": "東京都新宿区西新宿1-1-1",
        "type": PropertyType.APARTMENT,
        "construction_year": 2020,
        "room_layout": "1K",
        "floor_area": 25.5,
        "purchase_price": 30000000,
        "down_payment": 6000000,
        "loan_amount": 24000000,
        "interest_rate": 0.025,
        "loan_period": 25,
        "monthly_rent": 120000,
        "management_fee": 8000,
        "repair_reserve": 5000,
        "property_tax": 120000,
        "insurance": 30000,
    }


@pytest.fixture
def sample_property(sample_property_data) -> Property:
    """サンプル物件インスタンス"""
    return Property(**sample_property_data)


@pytest.fixture
def sample_investor_data() -> Dict[str, Any]:
    """サンプル投資家データ"""
    return {
        "annual_income": 8000000,
        "tax_bracket": 0.23,
        "investment_experience": InvestmentExperience.INTERMEDIATE,
        "risk_tolerance": RiskTolerance.MODERATE,
        "available_cash": 10000000,
        "current_debt": 0,
        "monthly_savings": 200000,
        "target_monthly_income": 100000,
        "investment_period": 20,
        "preferred_property_types": [PropertyType.APARTMENT],
        "preferred_locations": ["東京都", "神奈川県"],
    }


@pytest.fixture
def sample_investor(sample_investor_data) -> PersonalInvestor:
    """サンプル投資家インスタンス"""
    return PersonalInvestor(**sample_investor_data)


@pytest.fixture
def calculation_test_data() -> Dict[str, Dict[str, Any]]:
    """計算テスト用データ"""
    return {
        "basic_case": {
            "purchase_price": 30000000,
            "annual_rent": 1440000,  # 月12万 × 12ヶ月
            "annual_expenses": 156000,  # 管理費8000 + 修繕5000) × 12 + 固定資産税12万 + 保険3万
            "loan_amount": 24000000,
            "interest_rate": 0.025,
            "loan_period": 25,
            "down_payment": 6000000,
        },
        "high_yield_case": {
            "purchase_price": 20000000,
            "annual_rent": 1800000,  # 月15万 × 12ヶ月
            "annual_expenses": 200000,
            "loan_amount": 16000000,
            "interest_rate": 0.03,
            "loan_period": 20,
            "down_payment": 4000000,
        },
        "low_yield_case": {
            "purchase_price": 50000000,
            "annual_rent": 2400000,  # 月20万 × 12ヶ月
            "annual_expenses": 400000,
            "loan_amount": 40000000,
            "interest_rate": 0.02,
            "loan_period": 30,
            "down_payment": 10000000,
        },
    }
