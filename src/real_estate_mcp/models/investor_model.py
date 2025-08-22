"""投資家関連データモデル。

Pylint import-error 回避のため pydantic が無い環境では最小限のフォールバックを提供する。
実行時 (テスト) には本物の pydantic が存在することを前提とし、型安全性より lint 安定性を優先。

R0801 duplicate-code: property_model のフォールバック実装と意図的に類似。
"""  # pylint: disable=duplicate-code

import json
from enum import Enum
from typing import Any, Dict, List

try:  # pylint: disable=import-error
    from pydantic import BaseModel, Field  # type: ignore
except ImportError:  # pragma: no cover - lint 環境フォールバック

    class BaseModel:  # type: ignore
        """Fallback BaseModel (validation無しの簡易版)"""

        def __init__(self, **data: Any):
            for k, v in data.items():  # 受け取ったキーをそのまま属性化
                setattr(self, k, v)

        def model_dump(self) -> Dict[str, Any]:  # pydantic 互換最小 API
            """属性辞書を返す (最小限の互換)."""
            return self.__dict__

        def model_dump_json(self, indent: int | None = None) -> str:  # type: ignore[override]
            """JSON 文字列へシリアライズ (最小互換)."""
            return json.dumps(self.model_dump(), ensure_ascii=False, indent=indent)

    from typing import cast

    def Field(default: Any = ..., **_kwargs: Any) -> Any:  # type: ignore  # pylint: disable=invalid-name
        """Fallback Field: 戻り値を Any とし、必須指定(Field(...)) でも型エラーを避ける。"""
        if default is ...:  # 必須指定だったケース
            return cast(Any, None)
        return default


from .property_model import PropertyType


class InvestmentExperience(str, Enum):
    """投資経験レベル列挙。"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"


class RiskTolerance(str, Enum):
    """リスク許容度列挙。"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PersonalInvestor(BaseModel):
    """個人投資家プロファイルモデル。"""

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
