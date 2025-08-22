"""価格推定ユニット/統合テスト群。

本ファイルはテスト目的で protected メンバーへアクセスし挙動検証を行うため
一部 pylint 規約 (protected-access / import-outside-toplevel 等) を明示的に許容する。

許容理由:
 - protected メソッド: テストで内部ロジックの安定性を検証
 - import-outside-toplevel: 動的遅延 import による依存削減
 - broad-exception-caught: 例外経路網羅で堅牢性を検証
 - import-error: CI 環境の optional 依存を無視
 - reimported/ungrouped-imports: テストシナリオ毎の独立性確保
 - unused-argument: patch 用ダミー coroutine のシグネチャ維持
"""

# pylint: disable=protected-access,import-outside-toplevel,
# pylint: disable=broad-exception-caught,import-error,reimported,
# pylint: disable=ungrouped-imports,unused-argument,duplicate-code

import asyncio
from unittest.mock import patch

import pytest  # pylint: disable=import-error

from real_estate_mcp.utils.market_data_client import MarketDataClient
from real_estate_mcp.utils.price_estimation import PropertyPriceEstimator


class TestPropertyPriceEstimator:
    """PropertyPriceEstimatorのテストクラス"""

    @pytest.fixture
    def sample_property_data(self):  # noqa: D401 - fixture simple
        """代表的な物件データフィクスチャ。"""
        return {
            "id": "test-prop-001",
            "address": "東京都新宿区西新宿1-1-1",
            "type": "apartment",
            "construction_year": 2015,
            "floor_area": 50.0,
            "monthly_rent": 120000,
            "purchase_price": 30000000,
        }

    @pytest.mark.asyncio
    async def test_estimate_price_basic(self, sample_property_data):
        """複数手法 (比較+収益) 指定時の基本推定フロー動作を検証。"""
        async with PropertyPriceEstimator() as estimator:
            # モックを設定
            with patch.object(
                MarketDataClient, "_comparable_sales_approach"
            ) as mock_comp, patch.object(
                MarketDataClient, "_yield_based_approach"
            ) as mock_yield:
                mock_comp.return_value = {
                    "estimated_price": 28000000,
                    "comparable_count": 5,
                    "confidence": "high",
                }

                mock_yield.return_value = {
                    "estimated_price": 29000000,
                    "area_yield": 4.0,
                    "confidence": "high",
                }

                result = await estimator.estimate_price(
                    sample_property_data, ["comparable", "yield_based"]
                )

                # 結果の検証
                assert "final_estimate" in result
                assert "estimates" in result
                assert "confidence" in result
                assert "recommendation" in result

                final_price = result["final_estimate"]["price"]
                assert final_price is not None
                assert isinstance(final_price, (int, float))
                assert 25000000 <= final_price <= 32000000  # 妥当な範囲

    @pytest.mark.asyncio
    async def test_comparable_sales_approach(self, sample_property_data):
        """レガシー comparable パス (methods 未指定) の推定結果構造を検証。"""
        async with PropertyPriceEstimator() as estimator:
            # モックを設定
            with patch.object(
                estimator, "_get_coordinates"
            ) as mock_coords, patch.object(
                estimator, "_comparable_sales_approach"
            ) as mock_fetch:
                mock_coords.return_value = (35.6762, 139.6503)
                mock_fetch.return_value = [
                    {
                        "id": "comp1",
                        "price": 28000000,
                        "floor_area": 48.0,
                        "building_age": 8,
                        "distance": 200,
                    },
                    {
                        "id": "comp2",
                        "price": 30000000,
                        "floor_area": 52.0,
                        "building_age": 10,
                        "distance": 350,
                    },
                ]

                result = await estimator.estimate_price(sample_property_data)

                # 結果の検証
                assert "estimated_price" in result
                assert result["estimated_price"] is not None
                assert result["comparable_count"] == 2
                assert "price_range" in result

    @pytest.mark.asyncio
    async def test_yield_based_approach(self, sample_property_data):
        """収益還元法のテスト"""
        async with PropertyPriceEstimator() as estimator:
            with patch.object(estimator, "_get_area_yield_rate") as mock_yield:
                mock_yield.return_value = 4.5  # 4.5%利回り

                result = await estimator._yield_based_approach(sample_property_data)

                assert "estimated_price" in result
                assert result["estimated_price"] is not None
                assert "area_yield_rate" in result
                assert result["area_yield_rate"] == 4.5

                # 計算の妥当性チェック
                annual_rent = sample_property_data["monthly_rent"] * 12
                expected_price = annual_rent / (4.5 / 100)
                assert abs(result["estimated_price"] - expected_price) < 100000

    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self):
        """データ不足時の処理テスト"""
        async with PropertyPriceEstimator() as estimator:
            # 住所のみの不完全なデータ
            incomplete_data = {"address": "東京都渋谷区"}

            result = await estimator.estimate_sale_price(
                incomplete_data, ["yield_based"]
            )

            # エラーハンドリングの確認
            assert "estimates" in result
            yield_result = result["estimates"]["yield_based"]
            assert yield_result["estimated_price"] is None
            assert "error" in yield_result

    def test_price_adjustment_logic(self, sample_property_data):
        """価格調整ロジックのテスト"""
        estimator = PropertyPriceEstimator()

        comparable = {
            "price": 30000000,
            "floor_area": 60.0,  # 20%大きい
            "building_age": 12,  # 3年古い
            "distance": 500,  # 500m
        }

        adjusted_price = estimator._adjust_comparable_price(
            comparable, sample_property_data
        )

        # 面積調整（50/60 = 0.833倍）
        # 築年数調整（築年差3年 → 3% up）
        # 距離調整（500m → 若干down）
        assert adjusted_price != comparable["price"]
        assert 20000000 <= adjusted_price <= 35000000

    def test_confidence_score_calculation(self):
        """信頼度スコア計算のテスト"""
        estimator = PropertyPriceEstimator()

        # 複数手法で推定価格が近い場合
        results = {
            "estimates": {
                "comparable": {"estimated_price": 28000000, "comparable_count": 5},
                "yield_based": {"estimated_price": 29000000},
                "market_data": {"estimated_price": 28500000},
            }
        }

        confidence = estimator._calculate_confidence_score(results)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # 複数手法で近い値なので高めの信頼度


class TestMarketDataClient:
    """MarketDataClientのテストクラス"""

    @pytest.mark.asyncio
    async def test_get_land_price_data(self):
        """地価データ取得のテスト"""
        async with MarketDataClient() as client:
            # キャッシュをクリア
            client.cache.clear()

            with patch.object(client, "_fetch_land_price_from_api") as mock_api:
                mock_api.return_value = {
                    "price_per_sqm": 500000,
                    "source": "地価公示API",
                    "count": 10,
                }

                result = await client.get_land_price_data("東京都新宿区")

                assert "price_per_sqm" in result
                assert result["price_per_sqm"] > 0
                assert "source" in result

    @pytest.mark.asyncio
    async def test_cache_mechanism(self):
        """キャッシュ機能のテスト"""
        async with MarketDataClient() as client:
            address = "東京都港区"

            # 1回目の呼び出し
            result1 = await client.get_area_yield_rate(address)

            # キャッシュヒット確認用にAPIモックを設定
            with patch.object(client, "_fetch_area_yield_from_sources") as mock_api:
                mock_api.return_value = 999.9  # 明らかに異なる値

                # 2回目の呼び出し（キャッシュから取得されるはず）
                result2 = await client.get_area_yield_rate(address)

                assert result1 == result2
                assert mock_api.call_count == 0  # APIは呼ばれない

    @pytest.mark.asyncio
    async def test_comparable_sales_generation(self):
        """類似物件データ生成のテスト"""
        async with MarketDataClient() as client:
            comparables = await client.search_comparable_sales(
                35.6762, 139.6503, "apartment", 5, 50.0
            )

            assert len(comparables) >= 3
            for comp in comparables:
                assert "id" in comp
                assert "price" in comp
                assert "floor_area" in comp
                assert "building_age" in comp
                assert "distance" in comp
                assert comp["price"] > 0


class TestMCPServerIntegration:
    """MCPサーバー統合テスト"""

    @pytest.fixture
    def server(self):
        """テスト用サーバーインスタンス"""
        from real_estate_mcp.server import RealEstateMCPServer

        return RealEstateMCPServer()

    @pytest.mark.asyncio
    async def test_estimate_sale_price_tool_registered_property(self, server):
        """登録済み物件の売却価格推定ツールテスト"""
        # テスト用物件を登録
        test_property = {
            "id": "test-001",
            "name": "テスト物件",
            "address": "東京都新宿区西新宿1-1-1",
            "type": "apartment",
            "construction_year": 2015,
            "room_layout": "1LDK",
            "floor_area": 50.0,
            "purchase_price": 30000000,
            "down_payment": 6000000,
            "loan_amount": 24000000,
            "monthly_rent": 120000,
        }

        await server._register_property({"property_data": test_property})

        # 売却価格推定の実行
        arguments = {
            "property_id": "test-001",
            "estimation_methods": ["comparable", "yield_based"],
            "include_market_analysis": True,
        }

        with patch(
            "real_estate_mcp.utils.price_estimation.estimate_property_sale_price"
        ) as mock_estimate:
            mock_estimate.return_value = {
                "final_estimate": {"price": 28500000},
                "confidence_score": 0.75,
                "estimates": {
                    "comparable": {"estimated_price": 28000000, "comparable_count": 4},
                    "yield_based": {
                        "estimated_price": 29000000,
                        "area_yield_rate": 4.5,
                    },
                },
                "recommendations": ["高い信頼度で推定されました"],
            }

            result = await server._estimate_sale_price(arguments)

            assert len(result) == 1
            result_text = result[0].text
            assert "売却価格推定結果" in result_text
            assert "28,500,000円" in result_text
            assert "比較事例法" in result_text
            assert "収益還元法" in result_text

    @pytest.mark.asyncio
    async def test_estimate_sale_price_tool_direct_data(self, server):
        """直接データ指定での売却価格推定ツールテスト"""
        arguments = {
            "property_data": {
                "address": "東京都港区六本木1-1-1",
                "type": "apartment",
                "construction_year": 2018,
                "floor_area": 60.0,
                "monthly_rent": 180000,
            },
            "estimation_methods": ["yield_based"],
        }

        with patch(
            "real_estate_mcp.utils.price_estimation.estimate_property_sale_price"
        ) as mock_estimate:
            mock_estimate.return_value = {
                "final_estimate": {"price": 48000000},
                "confidence_score": 0.6,
                "estimates": {
                    "yield_based": {"estimated_price": 48000000, "area_yield_rate": 4.5}
                },
                "recommendations": ["収益還元法による推定"],
            }

            result = await server._estimate_sale_price(arguments)

            assert len(result) == 1
            result_text = result[0].text
            assert "売却価格推定結果" in result_text
            assert "48,000,000円" in result_text

    @pytest.mark.asyncio
    async def test_parallel_api_calls(self, server):
        """並行API呼び出しのパフォーマンステスト"""
        import time

        arguments = {
            "property_data": {
                "address": "東京都新宿区新宿1-1-1",
                "type": "apartment",
                "construction_year": 2010,
                "floor_area": 45.0,
                "monthly_rent": 150000,
            },
            "estimation_methods": ["comparable", "yield_based", "market_data"],
            "include_market_analysis": True,
        }

        # 各APIモックに遅延を追加してパフォーマンス測定
        async def mock_slow_estimation(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms遅延
            return {
                "final_estimate": {"price": 32000000},
                "confidence_score": 0.8,
                "estimates": {
                    "comparable": {"estimated_price": 31000000},
                    "yield_based": {"estimated_price": 33000000},
                    "market_data": {"estimated_price": 32000000},
                },
                "recommendations": [],
            }

        async def mock_slow_market_analysis(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms遅延
            return {
                "land_price": {"price_per_sqm": 600000},
                "area_yield": 5.0,
                "market_trends": {"price_trend": "上昇"},
            }

        with patch(
            "real_estate_mcp.utils.price_estimation.estimate_property_sale_price",
            mock_slow_estimation,
        ), patch.object(server, "_get_market_analysis", mock_slow_market_analysis):
            start_time = time.time()
            result = await server._estimate_sale_price(arguments)
            end_time = time.time()

            # 並行実行により200ms未満で完了すること
            execution_time = end_time - start_time
            assert execution_time < 0.2  # 200ms未満

            assert len(result) == 1
            assert "32,000,000円" in result[0].text

    @pytest.mark.asyncio
    async def test_error_handling_robustness(self, server):
        """エラー処理の堅牢性テスト"""
        arguments = {
            "property_data": {"address": "無効な住所", "type": "invalid_type"},
            "estimation_methods": ["all"],
        }

        # API呼び出しでエラーが発生する場合をシミュレート
        with patch(
            "real_estate_mcp.utils.price_estimation.estimate_property_sale_price"
        ) as mock_estimate:
            mock_estimate.side_effect = Exception("API接続エラー")

            result = await server._estimate_sale_price(arguments)

            assert len(result) == 1
            result_text = result[0].text
            assert "エラー" in result_text


# 統合テスト用のヘルパー関数
async def run_end_to_end_test():
    """エンドツーエンドテスト"""
    from real_estate_mcp.server import RealEstateMCPServer

    server = RealEstateMCPServer()

    try:
        # 1. 物件の登録
        property_data = {
            "id": "e2e-test-001",
            "name": "E2Eテスト物件",
            "address": "東京都渋谷区神南1-1-1",
            "type": "apartment",
            "construction_year": 2020,
            "room_layout": "1LDK",
            "floor_area": 45.0,
            "purchase_price": 35000000,
            "down_payment": 7000000,
            "loan_amount": 28000000,
            "interest_rate": 0.02,
            "loan_period": 30,
            "monthly_rent": 140000,
        }

        register_result = await server._register_property(
            {"property_data": property_data}
        )
        print("物件登録結果:", register_result[0].text)

        # 2. 収益性分析の実行
        analysis_args = {
            "property_price": property_data["purchase_price"],
            "monthly_rent": property_data["monthly_rent"],
            "loan_ratio": 0.8,
            "interest_rate": 2.0,
            "investor_tax_bracket": 0.2,
        }

        analysis_result = await server._analyze_property(analysis_args)
        print("収益性分析結果:", analysis_result[0].text[:200] + "...")

        # 3. 売却価格推定の実行
        estimation_args = {
            "property_id": "e2e-test-001",
            "estimation_methods": ["comparable", "yield_based"],
            "include_market_analysis": True,
        }

        # 推定機能をモック
        with patch(
            "real_estate_mcp.utils.price_estimation.estimate_property_sale_price"
        ) as mock_estimate:
            mock_estimate.return_value = {
                "final_estimate": {"price": 36500000, "confidence": "high"},
                "confidence_score": 0.82,
                "estimates": {
                    "comparable": {"estimated_price": 36000000, "comparable_count": 6},
                    "yield_based": {
                        "estimated_price": 37000000,
                        "area_yield_rate": 4.2,
                    },
                },
                "recommendations": [
                    "購入時から約4.3%の値上がりが見込まれます。",
                    "推定の信頼度は高いです。売却検討の参考値として活用できます。",
                    "低利回りエリアのため、実需（居住用）での売却を検討してください。",
                ],
            }

            estimation_result = await server._estimate_sale_price(estimation_args)
            print("売却価格推定結果:", estimation_result[0].text)

        # 4. 結果の検証
        assert "物件を登録しました" in register_result[0].text
        assert "不動産投資分析結果" in analysis_result[0].text
        assert "36,500,000円" in estimation_result[0].text
        assert "4.3%" in estimation_result[0].text

        print("✅ エンドツーエンドテスト成功")
        return True

    except Exception as e:
        print(f"❌ エンドツーエンドテスト失敗: {e}")
        return False
    finally:
        await server.cleanup()


# パフォーマンステスト用の関数
async def run_performance_test():
    """パフォーマンステスト"""
    import time

    print("🚀 パフォーマンステスト開始")

    # 複数物件の並行処理テスト
    test_properties = [
        {"address": f"東京都新宿区西新宿{i}-{i}-{i}", "monthly_rent": 100000 + i * 5000}
        for i in range(1, 11)
    ]

    async def estimate_single_property(prop_data):
        # 模擬的な推定処理
        await asyncio.sleep(0.05)  # 50ms の処理時間をシミュレート
        return {
            "address": prop_data["address"],
            "estimated_price": prop_data["monthly_rent"] * 12 / 0.05,  # 5%利回りで逆算
            "processing_time": 0.05,
        }

    # 1. 順次実行
    start_time = time.time()
    sequential_results = []
    for prop in test_properties:
        result = await estimate_single_property(prop)
        sequential_results.append(result)
    sequential_time = time.time() - start_time

    # 2. 並行実行
    start_time = time.time()
    parallel_results = await asyncio.gather(
        *[estimate_single_property(prop) for prop in test_properties]
    )
    parallel_time = time.time() - start_time

    print(f"順次実行時間: {sequential_time:.2f}秒")
    print(f"並行実行時間: {parallel_time:.2f}秒")
    print(f"性能向上率: {sequential_time/parallel_time:.1f}x")

    assert parallel_time < sequential_time / 5  # 5倍以上の高速化
    assert len(parallel_results) == len(test_properties)

    print("✅ パフォーマンステスト成功")


# メイン実行関数
if __name__ == "__main__":
    import pytest

    print("🧪 売却価格推定機能テスト実行")

    # 単体テストの実行
    pytest.main([__file__, "-v", "--tb=short"])

    # エンドツーエンドテストの実行
    asyncio.run(run_end_to_end_test())

    # パフォーマンステストの実行
    asyncio.run(run_performance_test())
