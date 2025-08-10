from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    SMALL_BUILDING = "small_building"


class Property(BaseModel):
    """個人投資家向け物件モデル"""

    # 基本情報
    id: str = Field(..., description="物件ID")
    name: str = Field(..., description="物件名")
    address: str = Field(..., description="住所")
    type: PropertyType = Field(..., description="物件種別")
    construction_year: int = Field(..., description="築年")
    room_layout: str = Field(..., description="間取り（1K, 2LDK等）")
    floor_area: float = Field(..., description="床面積（㎡）")

    # 購入情報
    purchase_price: float = Field(..., description="購入価格")
    down_payment: float = Field(..., description="頭金")
    loan_amount: float = Field(..., description="融資額")
    interest_rate: float = Field(default=0.025, description="金利")
    loan_period: int = Field(default=25, description="返済期間（年）")

    # 収支情報
    monthly_rent: float = Field(..., description="月額賃料")
    management_fee: float = Field(default=0, description="管理費")
    repair_reserve: float = Field(default=0, description="修繕積立金")
    property_tax: float = Field(default=0, description="年間固定資産税")
    insurance: float = Field(default=0, description="年間保険料")

    # 運用実績
    occupancy_months_per_year: int = Field(default=12, description="年間入居月数")
    tenant_turnover_cost: float = Field(default=0, description="入退去費用")
    major_repair_reserve: float = Field(default=0, description="大規模修繕積立")

    # メタデータ
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = Field(None, description="備考")

    @property
    def age(self) -> int:
        """築年数を計算"""
        return datetime.now().year - self.construction_year

    @property
    def annual_rent(self) -> float:
        """年間賃料収入"""
        return self.monthly_rent * self.occupancy_months_per_year

    @property
    def annual_expenses(self) -> float:
        """年間経費合計"""
        monthly_expenses = self.management_fee + self.repair_reserve
        annual_expenses = (monthly_expenses * 12) + self.property_tax + self.insurance
        return annual_expenses
