"""計算ロジックのテスト"""

import math

import pytest

from real_estate_mcp.utils.calculations import (
    calculate_gross_yield,
    calculate_monthly_cashflow,
    calculate_monthly_loan_payment,
    calculate_net_yield,
    calculate_payback_period,
    calculate_property_analysis,
    calculate_tax_benefit,
)


class TestBasicCalculations:
    """基本計算機能のテスト"""

    def test_calculate_gross_yield_normal_case(self):
        """表面利回り計算 - 正常ケース"""
        annual_rent = 1440000  # 年144万円
        purchase_price = 30000000  # 3000万円
        expected_yield = 4.8  # 144/3000 * 100 = 4.8%

        result = calculate_gross_yield(annual_rent, purchase_price)
        assert result == expected_yield

    def test_calculate_gross_yield_zero_price(self):
        """表面利回り計算 - 購入価格0の異常ケース"""
        result = calculate_gross_yield(1440000, 0)
        assert result == 0.0

    def test_calculate_net_yield_normal_case(self):
        """実質利回り計算 - 正常ケース"""
        annual_rent = 1440000
        annual_expenses = 156000
        purchase_price = 30000000
        expected_yield = 4.28  # (1440000-156000)/30000000 * 100

        result = calculate_net_yield(annual_rent, annual_expenses, purchase_price)
        assert abs(result - expected_yield) < 0.01

    def test_calculate_monthly_loan_payment_normal_case(self):
        """月次ローン返済額計算 - 正常ケース"""
        loan_amount = 24000000
        interest_rate = 0.025
        loan_period_years = 25

        # 元利均等返済の計算式
        monthly_rate = interest_rate / 12
        total_payments = loan_period_years * 12
        expected_payment = (
            loan_amount
            * (monthly_rate * (1 + monthly_rate) ** total_payments)
            / ((1 + monthly_rate) ** total_payments - 1)
        )

        result = calculate_monthly_loan_payment(
            loan_amount, interest_rate, loan_period_years
        )
        assert abs(result - expected_payment) < 1

    def test_calculate_monthly_loan_payment_zero_interest(self):
        """月次ローン返済額計算 - 金利0%のケース"""
        loan_amount = 24000000
        interest_rate = 0.0
        loan_period_years = 25
        expected_payment = loan_amount / (loan_period_years * 12)  # 80,000円

        result = calculate_monthly_loan_payment(
            loan_amount, interest_rate, loan_period_years
        )
        assert abs(result - expected_payment) < 1

    def test_calculate_monthly_cashflow(self):
        """月次キャッシュフロー計算"""
        monthly_rent = 120000
        monthly_loan_payment = 107000  # 概算値
        monthly_expenses = 13000
        expected_cashflow = 120000 - 107000 - 13000  # = 0

        result = calculate_monthly_cashflow(
            monthly_rent, monthly_loan_payment, monthly_expenses
        )
        assert result == expected_cashflow

    def test_calculate_payback_period_positive_cashflow(self):
        """投資回収期間計算 - 正のキャッシュフロー"""
        down_payment = 6000000
        annual_cashflow = 240000  # 年24万円
        expected_period = 25  # 6000000/240000 = 25年

        result = calculate_payback_period(down_payment, annual_cashflow)
        assert result == expected_period

    def test_calculate_payback_period_zero_cashflow(self):
        """投資回収期間計算 - キャッシュフロー0（回収不能）"""
        down_payment = 6000000
        annual_cashflow = 0

        result = calculate_payback_period(down_payment, annual_cashflow)
        assert result == float("inf")

    def test_calculate_tax_benefit(self):
        """節税効果計算"""
        annual_depreciation = 900000  # 年90万円
        annual_expenses = 156000  # 年15.6万円
        tax_rate = 0.23
        expected_benefit = (900000 + 156000) * 0.23  # 242,880円

        result = calculate_tax_benefit(annual_depreciation, annual_expenses, tax_rate)
        assert abs(result - expected_benefit) < 1


class TestPropertyAnalysis:
    """総合物件分析のテスト"""

    def test_calculate_property_analysis_basic(self, calculation_test_data):
        """基本物件分析テスト"""
        property_data = {
            "purchase_price": 30000000,
            "monthly_rent": 120000,
            "occupancy_months_per_year": 12,
            "annual_expenses": 156000,
            "loan_amount": 24000000,
            "interest_rate": 0.025,
            "loan_period": 25,
            "down_payment": 6000000,
            "type": "apartment",
        }

        investor_data = {"tax_bracket": 0.23}

        result = calculate_property_analysis(property_data, investor_data)

        # 結果の検証
        assert "gross_yield" in result
        assert "net_yield" in result
        assert "monthly_cashflow" in result
        assert "annual_cashflow" in result
        assert "payback_period" in result
        assert "monthly_loan_payment" in result
        assert "annual_depreciation" in result
        assert "annual_tax_benefit" in result
        assert "net_annual_income" in result

        # 具体的な値の検証
        assert result["gross_yield"] == 4.8  # 144万/3000万 * 100
        assert result["net_yield"] > 0  # 実質利回りは正の値
        assert isinstance(result["monthly_cashflow"], (int, float))
        assert result["annual_tax_benefit"] > 0  # 節税効果あり

    def test_calculate_property_analysis_without_investor(self):
        """投資家データなしの分析テスト"""
        property_data = {
            "purchase_price": 30000000,
            "monthly_rent": 120000,
        }

        result = calculate_property_analysis(property_data)

        # 基本的な計算は実行される
        assert "gross_yield" in result
        assert "net_yield" in result
        assert result["annual_tax_benefit"] == 0  # 投資家データなしなので節税効果は0


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_negative_values_handling(self):
        """負の値に対する処理"""
        # 負の賃料（あり得ないが）
        result = calculate_gross_yield(-100000, 30000000)
        assert result < 0  # 負の利回り

    def test_very_large_numbers(self):
        """非常に大きな数値の処理"""
        large_price = 1000000000000  # 1兆円
        large_rent = 1000000000  # 10億円/年

        result = calculate_gross_yield(large_rent, large_price)
        assert result == 0.1  # 0.1%

    def test_precision_handling(self):
        """精度の処理"""
        # 小数点以下の精度チェック
        result = calculate_gross_yield(1234567, 98765432)
        assert isinstance(result, float)
        assert len(str(result).split(".")[-1]) <= 10  # 小数点以下10桁以内
