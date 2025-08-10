# src/real_estate_mcp/models/investor_model.py
"""投資家データモデル"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from .property_model import PropertyType


class InvestmentExperience(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PersonalInvestor(BaseModel):
    """個人投資家プロファイル"""

    # プロファイル
    annual_income: float = Field(..., description="年収")
    tax_bracket: float = Field(..., description="所得税率")
    investment_experience: InvestmentExperience = Field(..., description="投資経験")
    risk_tolerance: RiskTolerance = Field(..., description="リスク許容度")

    # 財務状況
    available_cash: float = Field(..., description="投資可能現金")
    current_debt: float = Field(default=0, description="既存借入")
    monthly_savings: float = Field(..., description="月間貯蓄可能額")

    # 投資目標
    target_monthly_income: float = Field(..., description="目標月収")
    investment_period: int = Field(..., description="投資期間（年）")
    preferred_property_types: List[PropertyType] = Field(
        default=[], description="希望物件種別"
    )
    preferred_locations: List[str] = Field(default=[], description="希望地域")

    def get_investment_budget(self) -> float:
        """投資予算を計算"""
        # 年収の5-7倍程度を目安とする簡易計算
        income_multiple = {
            RiskTolerance.CONSERVATIVE: 5,
            RiskTolerance.MODERATE: 6,
            RiskTolerance.AGGRESSIVE: 7,
        }
        return self.annual_income * income_multiple[self.risk_tolerance]

    def get_recommended_loan_ratio(self) -> float:
        """推奨融資比率"""
        ratio_by_experience = {
            InvestmentExperience.BEGINNER: 0.7,
            InvestmentExperience.INTERMEDIATE: 0.8,
            InvestmentExperience.EXPERIENCED: 0.85,
        }
        return ratio_by_experience[self.investment_experience]
