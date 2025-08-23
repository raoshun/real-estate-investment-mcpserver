"""物件データモデル。

pydantic が無い静的解析 / lint 環境でも import-error を避けるためフォールバックを提供する。
テスト/実行環境では本物の pydantic を利用する想定。

R0801 duplicate-code: investor_model のフォールバックと意図的に類似。
"""  # pylint: disable=duplicate-code

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

try:  # pylint: disable=import-error
    from pydantic import BaseModel, Field  # type: ignore
except ImportError:  # pragma: no cover - lint 環境フォールバック

    class BaseModel:  # type: ignore
        """Fallback BaseModel (最小限: 値をそのまま属性化)"""

        def __init__(self, **data: Any):
            for k, v in data.items():
                setattr(self, k, v)

        def model_dump(self) -> Dict[str, Any]:  # 最小互換
            """属性辞書を返す (最小互換)。"""
            return self.__dict__

        def model_dump_json(self, indent: int | None = None) -> str:  # type: ignore[override]
            """JSON 文字列へシリアライズ (最小互換)。"""
            return json.dumps(self.model_dump(), ensure_ascii=False, indent=indent)

    from typing import cast

    def Field(default: Any = ..., **_kwargs: Any) -> Any:  # type: ignore  # pylint: disable=invalid-name
        """Fallback Field: 戻り値を Any とし必須指定でも型エラー回避。"""
        if default is ...:
            return cast(Any, None)
        return default


class PropertyType(str, Enum):
    """物件種別列挙"""

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
