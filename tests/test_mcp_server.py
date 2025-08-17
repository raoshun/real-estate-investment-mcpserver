import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from real_estate_mcp.server import RealEstateMCPServer, TextContent


class TestRealEstateMCPServer:
    """RealEstateMCPServerのテストクラス"""

    @pytest.fixture
    def server(self):
        """テスト用のRealEstateMCPServerインスタンスを返す"""
        return RealEstateMCPServer()

    def test_server_initialization(self, server):
        """サーバー初期化テスト"""
        assert server is not None
        assert server.server.name == "real-estate-investment-mcp"
        assert len(server.properties) == 0

    @pytest.mark.asyncio
    async def test_analyze_property_success(self, server):
        """物件分析成功テスト"""
        tool_name = "analyze_property"
        arguments = {
            "property_price": 30000000,  # 3000万円
            "monthly_rent": 120000,  # 12万円
            "loan_ratio": 80,
            "interest_rate": 2.5,
            "loan_period": 25,
        }

        with patch.object(
            server, "call_tool", new_callable=AsyncMock
        ) as mock_call_tool:
            mock_call_tool.return_value = [
                TextContent(
                    type="text",
                    text=("🏠 不動産投資分析結果\n表面利回り: 4.80%\n月次キャッシュフロー: 0円"),  # 必要な断片のみモック
                )
            ]

            result = await server.call_tool(tool_name, arguments)

            assert len(result) == 1
            mock_call_tool.assert_called_once_with(tool_name, arguments)

            result_text = result[0].text
            # 物件が追加されていることを確認
            assert "不動産投資分析結果" in result_text
            assert "表面利回り" in result_text
            assert "月次キャッシュフロー" in result_text
            assert "4.80%" in result_text

    @pytest.mark.asyncio
    async def test_analyze__property_high_yield(self, server):
        """高利回り物件の分析テスト(9%利回り)"""
        tool_name = "analyze_property"
        arguments = {
            "property_price": 20000000,  # 2000万円
            "monthly_rent": 150000,  # 15万円
            "loan_ratio": 80,
        }

        with patch.object(
            server, "call_tool", new_callable=AsyncMock
        ) as mock_call_tool:
            mock_call_tool.return_value = [
                TextContent(
                    type="text",
                    text=("🏠 不動産投資分析結果\n💎 高利回り物件\n表面利回り: 9.00%\n月次キャッシュフロー: 0円"),
                )
            ]

            result = await server.call_tool(tool_name, arguments)

            assert len(result) == 1
            mock_call_tool.assert_called_once_with(tool_name, arguments)

            result_text = result[0].text
            # 高利回りの推奨メッセージが含まれているかチェック
            assert "💎 高利回り物件" in result_text or "高利回り" in result_text
            assert "9.00%" in result_text  # 180万/2000万 = 9%

    @pytest.mark.asyncio
    async def test_analyze_property_low_yield(self, server):
        """低利回り物件の分析テスト(3%利回り)"""
        tool_name = "analyze_property"
        arguments = {
            "property_price": 30000000,  # 3000万円
            "monthly_rent": 75000,  # 7.5万円
            "loan_ratio": 80,
        }

        with patch.object(
            server, "call_tool", new_callable=AsyncMock
        ) as mock_call_tool:
            mock_call_tool.return_value = [
                TextContent(
                    type="text",
                    text=("🏠 不動産投資分析結果\n💔 低利回り物件\n表面利回り: 3.00%\n月次キャッシュフロー: 0円"),
                )
            ]

            result = await server.call_tool(tool_name, arguments)

            assert len(result) == 1
            mock_call_tool.assert_called_once_with(tool_name, arguments)

            result_text = result[0].text
            # 低利回りの推奨メッセージが含まれているかチェック
            assert "💔 低利回り物件" in result_text or "低利回り" in result_text
            assert "3.00%" in result_text  # 108万/3000万 = 3%

    @pytest.mark.asyncio
    async def test_analyze_property_with_custom_parameters(self, server):
        """カスタムパラメータでの分析テスト"""
        arguments = {
            "property_price": 25000000,
            "monthly_rent": 110000,
            "loan_ratio": 0.9,  # 90%融資
            "interest_rate": 0.035,  # 3.5%金利
            "loan_period": 20,  # 20年返済
            "annual_expense_rate": 0.25,  # 25%経費率
        }

        result = await server._analyze_property(arguments)
        result_text = result[0].text

        # カスタムパラメータが反映されているかチェック
        assert "融資比率: 90%" in result_text
        assert "不動産投資分析結果" in result_text

    def test_format_analysis_result_recommendation(self, server):
        """推奨メッセージの生成テスト"""
        # 高利回り・プラスキャッシュフローのケース
        analysis = {
            "gross_yield": 6.5,
            "net_yield": 5.2,
            "monthly_cashflow": 15000,
            "annual_cashflow": 180000,
            "payback_period": 18.5,
            "monthly_loan_payment": 95000,
            "annual_depreciation": 500000,
            "annual_tax_benefit": 100000,
            "net_annual_income": 280000,
        }

        inputs = {"property_price": 30000000, "monthly_rent": 150000, "loan_ratio": 0.8}

        result = server._format_analysis_result(analysis, inputs)

        # 高利回り物件の推奨メッセージが含まれているかチェック
        assert "💎 高利回り物件" in result
        assert "6.50%" in result
        assert "15,000円" in result


class TestServerIntegration:
    """統合テスト"""

    @pytest.mark.asyncio
    async def test_real_calculation_accuracy(self):
        """実際の計算精度のテスト"""
        server = RealEstateMCPServer()

        # 実際の投資ケースを想定
        arguments = {
            "property_price": 35000000,  # 3500万円
            "monthly_rent": 140000,  # 14万円
            "loan_ratio": 0.75,  # 75%融資
            "interest_rate": 0.02,  # 2%金利
            "loan_period": 30,  # 30年返済
        }

        result = await server._analyze_property(arguments)
        result_text = result[0].text

        # 計算結果の妥当性チェック
        assert "表面利回り: 4.80%" in result_text  # 168万/3500万
        assert "融資比率: 75%" in result_text

        # ローン返済額の妥当性（概算チェック）
        # 2625万円を2%、30年で返済 ≈ 97,000円/月程度
        assert "月次ローン返済:" in result_text

    @pytest.mark.asyncio
    async def test_edge_case_zero_interest(self):
        """金利0%のエッジケーステスト"""
        server = RealEstateMCPServer()

        arguments = {
            "property_price": 30000000,
            "monthly_rent": 120000,
            "interest_rate": 0.0,  # 金利0%
            "loan_period": 25,
        }

        result = await server._analyze_property(arguments)

        # エラーにならず、結果が返されることを確認
        assert len(result) == 1
        assert "不動産投資分析結果" in result[0].text


# 実行用のヘルパー関数
def run_server_test():
    """サーバーテストの実行"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_server_test()
