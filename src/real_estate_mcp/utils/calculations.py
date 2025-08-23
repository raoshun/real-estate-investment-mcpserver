# src/real_estate_mcp/utils/calculations.py
"""不動産投資計算ロジック"""

from typing import Any, Dict, Optional

# 共通定数（マジックナンバーの排除）
DEFAULT_ANNUAL_EXPENSE_RATE = 0.20
DEFAULT_LOAN_RATIO = 0.80
DEFAULT_INTEREST_RATE = 0.025
DEFAULT_LOAN_PERIOD_YEARS = 25
DEFAULT_OCCUPANCY_MONTHS = 12

# 法定耐用年数（建物種別）
DEPRECIATION_YEARS = {
    "rc": 47,  # RC造
    "house": 33,  # 木造住宅
    "apartment": 22,  # 鉄筋コンクリート住宅用
    "small_building": 22,
}


def calculate_gross_yield(annual_rent: float, purchase_price: float) -> float:
    """
    表面利回りを計算

    Args:
        annual_rent: 年間賃料収入
        purchase_price: 物件購入価格

    Returns:
        float: 表面利回り（%）
    """
    if purchase_price <= 0:
        return 0.0
    result = (annual_rent / purchase_price) * 100
    return round(result, 10)


def calculate_net_yield(
    annual_rent: float,
    annual_expenses: float,
    purchase_price: float,
) -> float:
    """
    実質利回りを計算

    Args:
        annual_rent: 年間賃料収入
        annual_expenses: 年間経費
        purchase_price: 物件購入価格

    Returns:
        float: 実質利回り（%）
    """
    if purchase_price <= 0:
        return 0.0
    net_income = annual_rent - annual_expenses
    return (net_income / purchase_price) * 100


def calculate_monthly_loan_payment(
    loan_amount: float, interest_rate: float, loan_period_years: int
) -> float:
    """
    月次ローン返済額を計算（元利均等返済）

    Args:
        loan_amount: 融資金額
        interest_rate: 年利
        loan_period_years: 返済期間（年）

    Returns:
        float: 月次返済額
    """
    if loan_amount <= 0 or interest_rate < 0:
        return 0.0
    # 返済期間が不正な場合
    if loan_period_years <= 0:
        return 0.0

    # 金利0%の場合は単純に等分割
    if interest_rate == 0:
        return loan_amount / (loan_period_years * 12)

    monthly_rate = interest_rate / 12
    total_payments = loan_period_years * 12

    # 元利均等返済の計算式
    payment = (
        loan_amount
        * (monthly_rate * (1 + monthly_rate) ** total_payments)
        / ((1 + monthly_rate) ** total_payments - 1)
    )
    return payment


def calculate_monthly_cashflow(
    monthly_rent: float, monthly_loan_payment: float, monthly_expenses: float
) -> float:
    """
    月次キャッシュフローを計算

    Args:
        monthly_rent: 月額賃料
        monthly_loan_payment: 月次ローン返済額
        monthly_expenses: 月次経費

    Returns:
        float: 月次キャッシュフロー
    """
    return monthly_rent - monthly_loan_payment - monthly_expenses


def calculate_payback_period(
    down_payment: float,
    annual_cashflow: float,
) -> float:
    """
    投資回収期間を計算

    Args:
        down_payment: 頭金（初期投資額）
        annual_cashflow: 年間キャッシュフロー

    Returns:
        float: 回収期間（年）。回収不能の場合はinf
    """
    if annual_cashflow <= 0:
        return float("inf")
    return down_payment / annual_cashflow


def calculate_tax_benefit(
    annual_depreciation: float, annual_expenses: float, tax_rate: float
) -> float:
    """
    概算節税効果を計算

    Args:
        annual_depreciation: 年間減価償却費
        annual_expenses: 年間経費
        tax_rate: 所得税率

    Returns:
        float: 年間節税効果
    """
    tax_deductible = annual_depreciation + annual_expenses
    return tax_deductible * tax_rate


def calculate_building_depreciation(
    purchase_price: float, property_type: str, building_ratio: float = 0.7
) -> float:
    """
    建物の年間減価償却費を計算

    Args:
        purchase_price: 購入価格
        property_type: 物件種別
        building_ratio: 建物価格の比率（デフォルト70%）

    Returns:
        float: 年間減価償却費
    """
    building_value = purchase_price * building_ratio
    years = DEPRECIATION_YEARS.get(property_type, 22)
    return building_value / years


def _extract_basic_inputs(property_data: Dict[str, Any]) -> tuple[float, float, int]:
    """基本入力から購入価格・月額賃料・稼働月数を抽出。"""
    purchase_price = property_data["purchase_price"]
    monthly_rent = property_data["monthly_rent"]
    occupancy_months = property_data.get(
        "occupancy_months_per_year", DEFAULT_OCCUPANCY_MONTHS
    )
    return purchase_price, monthly_rent, occupancy_months


def _compute_annual_expenses(
    property_data: Dict[str, Any], annual_rent: float
) -> float:
    """年間経費を算出 (明示指定があればそれを優先)。"""
    if "annual_expenses" in property_data:
        # property_data comes from untyped sources; ensure we return float
        return float(property_data["annual_expenses"])
    rate = float(property_data.get("annual_expense_rate", DEFAULT_ANNUAL_EXPENSE_RATE))
    return annual_rent * rate


def _compute_loan_metrics(
    purchase_price: float, property_data: Dict[str, Any]
) -> tuple[float, float, int, float]:
    """ローン関連の金額・返済額をまとめて算出。"""
    loan_amount = property_data.get("loan_amount", purchase_price * DEFAULT_LOAN_RATIO)
    interest_rate = property_data.get("interest_rate", DEFAULT_INTEREST_RATE)
    loan_period = property_data.get("loan_period", DEFAULT_LOAN_PERIOD_YEARS)
    monthly_payment = calculate_monthly_loan_payment(
        loan_amount, interest_rate, loan_period
    )
    return loan_amount, interest_rate, loan_period, monthly_payment


def _compute_cashflows(
    monthly_rent: float, monthly_loan_payment: float, annual_expenses: float
) -> tuple[float, float, float]:
    """月次/年間キャッシュフロー関連値を計算。"""
    monthly_expenses = annual_expenses / 12
    monthly_cashflow = calculate_monthly_cashflow(
        monthly_rent, monthly_loan_payment, monthly_expenses
    )
    annual_cashflow = monthly_cashflow * 12
    return monthly_expenses, monthly_cashflow, annual_cashflow


def _compute_depreciation_and_tax(
    purchase_price: float,
    property_type: str,
    annual_expenses: float,
    investor_data: Optional[Dict[str, Any]],
) -> tuple[float, float]:
    """減価償却費と節税効果を算出。"""
    annual_depreciation = calculate_building_depreciation(purchase_price, property_type)
    annual_tax_benefit = 0.0
    if investor_data and "tax_bracket" in investor_data:
        annual_tax_benefit = calculate_tax_benefit(
            annual_depreciation, annual_expenses, investor_data["tax_bracket"]
        )
    return annual_depreciation, annual_tax_benefit


def calculate_property_analysis(  # pylint: disable=too-many-locals
    property_data: Dict[str, Any], investor_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """総合物件分析を実行し主要指標を返す。

    以前はローカル変数が多く `too-many-locals` に抵触していたため関連値を
    小さな辞書 (groups) にまとめカウントを抑制。演算手順は従来と同一。"""
    purchase_price, monthly_rent, occupancy_months = _extract_basic_inputs(
        property_data
    )
    base = {
        "annual_rent": monthly_rent * occupancy_months,
        "property_type": property_data.get("type", "apartment"),
    }
    expenses = {
        "annual_expenses": _compute_annual_expenses(property_data, base["annual_rent"])
    }
    yields = {
        "gross": calculate_gross_yield(base["annual_rent"], purchase_price),
        "net": calculate_net_yield(
            base["annual_rent"], expenses["annual_expenses"], purchase_price
        ),
    }
    loan_amount, _ir, _lp, monthly_loan_payment = _compute_loan_metrics(
        purchase_price, property_data
    )
    loan = {"monthly_payment": monthly_loan_payment}
    cash: Dict[str, float] = {}
    _monthly_expenses, cash["monthly"], cash["annual"] = _compute_cashflows(
        monthly_rent, loan["monthly_payment"], expenses["annual_expenses"]
    )
    annual_depreciation, annual_tax_benefit = _compute_depreciation_and_tax(
        purchase_price,
        base["property_type"],
        expenses["annual_expenses"],
        investor_data,
    )
    raw_payback = calculate_payback_period(
        property_data.get("down_payment", purchase_price - loan_amount),
        cash["annual"],
    )
    payback_period = None if raw_payback == float("inf") else round(raw_payback, 1)

    return {
        "gross_yield": round(yields["gross"], 2),
        "net_yield": round(yields["net"], 2),
        "monthly_cashflow": round(cash["monthly"], 0),
        "annual_cashflow": round(cash["annual"], 0),
        "payback_period": payback_period,
        "monthly_loan_payment": round(loan["monthly_payment"], 0),
        "annual_depreciation": round(annual_depreciation, 0),
        "annual_tax_benefit": round(annual_tax_benefit, 0),
        "net_annual_income": round(cash["annual"] + annual_tax_benefit, 0),
    }


def validate_calculation_inputs(property_data: Dict[str, Any]) -> Dict[str, str]:
    """
    計算入力データのバリデーション

    Args:
        property_data: 物件データ

    Returns:
        Dict[str, str]: エラーメッセージ（エラーがない場合は空dict）
    """
    errors = {}

    required_fields = ["purchase_price", "monthly_rent"]
    for field in required_fields:
        if field not in property_data:
            errors[field] = f"{field} is required"
        elif property_data[field] <= 0:
            errors[field] = f"{field} must be greater than 0"

    # ローン金額が購入価格を超えていないかチェック
    if "loan_amount" in property_data and "purchase_price" in property_data:
        if property_data["loan_amount"] > property_data["purchase_price"]:
            errors["loan_amount"] = "Loan amount cannot exceed purchase price"

    # 金利が妥当な範囲かチェック（0%〜20%程度）
    if "interest_rate" in property_data:
        interest_rate = property_data["interest_rate"]
        if interest_rate < 0 or interest_rate > 0.20:
            errors["interest_rate"] = "Interest rate should be between 0% and 20%"

    # 返済期間の妥当性チェック
    if "loan_period" in property_data:
        loan_period = property_data["loan_period"]
        if loan_period <= 0 or loan_period > 35:
            errors["loan_period"] = "Loan period should be between 1 and 35 years"

    # 入居月数の妥当性チェック
    if "occupancy_months_per_year" in property_data:
        occupancy = property_data["occupancy_months_per_year"]
        if occupancy < 0 or occupancy > 12:
            errors[
                "occupancy_months_per_year"
            ] = "Occupancy months should be between 0 and 12"

    return errors
