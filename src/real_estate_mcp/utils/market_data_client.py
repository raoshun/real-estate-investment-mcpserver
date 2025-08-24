# src/real_estate_mcp/utils/market_data_client.py
"""市場データクライアント。

Pylint 指摘改善:
- オプション依存 (aiohttp, yaml) を try-import でラップし import-error を抑制
- 例外の粒度調整 (一部 RuntimeError / ValueError 化)
- ローカル変数削減のため mock comparable 生成ヘルパー抽出
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .optional_deps import aiohttp  # type: ignore

try:  # yaml は optional
    import yaml  # type: ignore  # pylint: disable=unused-import
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class MarketDataClient:
    """市場データ取得クライアント"""

    def __init__(self) -> None:
        # aiohttp が無い環境では遅延エラーにする
        self.session: Optional["aiohttp.ClientSession"] = None  # type: ignore[name-defined]
        self.cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}

        # API設定の読み込み
        self.api_config = self._load_api_config()

    async def __aenter__(self) -> "MarketDataClient":
        """非同期コンテキストマネージャーの開始"""
        # aiohttp が無くても read-only キャッシュ系メソッドは動かせるため graceful degrade
        if aiohttp is not None:  # type: ignore[name-defined]
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),  # type: ignore[attr-defined]
                headers={"User-Agent": "RealEstateInvestmentMCP/1.0"},
            )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()

    def _load_api_config(self) -> Dict[str, Any]:
        """API設定の読み込み

        yaml が利用不可 / 読み込み失敗の場合はデフォルト設定を返す。
        """
        config_path = os.path.join(
            os.path.dirname(__file__), "../../config/api_settings.yaml"
        )

        if not os.path.exists(config_path) or yaml is None:  # type: ignore[name-defined]
            return self._get_default_config()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)  # type: ignore[operator]
            return config if isinstance(config, dict) else self._get_default_config()
        except (OSError, ValueError, TypeError):  # 想定される I/O or parse エラー
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "data_sources": {
                "government_data": {
                    "land_price_api": {
                        "base_url": "https://www.land.mlit.go.jp/webland/api",
                        "enabled": True,
                    }
                }
            },
            "estimation_settings": {
                "yield_estimation": {
                    "default_yield_rates": {
                        "東京都": 4.5,
                        "神奈川県": 5.0,
                        "大阪府": 5.5,
                        "その他": 6.0,
                    }
                }
            },
        }

    def _get_cache_key(self, method: str, **kwargs: Any) -> str:
        """キャッシュキーの生成"""
        params = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return f"{method}_{hash(params)}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """キャッシュの有効性チェック (expiry 辞書を参照)"""
        if cache_key not in self.cache:
            return False

        expiry_time = self.cache_expiry.get(cache_key)
        if not expiry_time:
            return False

        return datetime.now() < expiry_time

    def _set_cache(self, cache_key: str, data: Any, hours: int = 24) -> None:
        """キャッシュの設定"""
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now() + timedelta(hours=hours)

    async def get_land_price_data(self, address: str) -> Dict[str, Any]:
        """地価公示データの取得"""
        cache_key = self._get_cache_key("land_price", address=address)
        if self._is_cache_valid(cache_key):  # 30日キャッシュ
            return dict(self.cache[cache_key])

        try:
            result = await self._fetch_land_price_from_api(address)
        except (ValueError, RuntimeError) as e:  # API 通信エラー
            return {  # フォールバック
                "price_per_sqm": 400000,
                "source": "デフォルト値",
                "error": str(e),
            }
        self._set_cache(cache_key, result, hours=24 * 30)
        return result

    async def _fetch_land_price_from_api(self, address: str) -> Dict[str, Any]:
        """地価公示APIからの実際のデータ取得"""
        if not self.session:
            raise ValueError("Session not initialized")

        # 住所から市区町村コードを取得（簡略化）
        city_code = self._extract_city_code(address)
        # 文字列補間不要のため f-string を使用しない (flake8 F541)
        url = "https://www.land.mlit.go.jp/webland/api/TradeListSearch"
        params = {"area": city_code, "from": "2023", "to": "2024"}

        async with self.session.get(url, params=params) as response:  # type: ignore[union-attr]
            if response.status != 200:
                raise RuntimeError(f"API status {response.status}")
            data = await response.json()
            return self._process_land_price_data(data, address)

    def _extract_city_code(self, address: str) -> str:
        """住所から市区町村コードを抽出（簡略化）"""
        # 都道府県→市区町村コードのマッピング（簡略版）
        prefecture_codes = {
            "東京都": "13",
            "神奈川県": "14",
            "大阪府": "27",
            "愛知県": "23",
            "福岡県": "40",
        }

        for pref, code in prefecture_codes.items():
            if pref in address:
                return code

        return "13"  # デフォルトは東京都

    def _process_land_price_data(
        self,
        api_data: Dict[str, Any],
        _address: str,  # _address: 将来のフィルタ拡張用に保持
    ) -> Dict[str, Any]:
        """地価公示APIレスポンスの処理"""
        try:
            data = api_data.get("data", [])
            if not data:
                return {"price_per_sqm": 400000, "source": "APIデータなし", "count": 0}

            # 価格データの処理
            prices = []
            for item in data[:50]:  # 最新50件
                trade_price = item.get("TradePrice")
                area = item.get("Area")
                if trade_price and area and trade_price != "-" and area != "-":
                    try:
                        price = float(trade_price) * 10000  # 万円→円
                        area_sqm = float(area)
                        if area_sqm > 0:
                            price_per_sqm = price / area_sqm
                            prices.append(price_per_sqm)
                    except ValueError:
                        continue

            if prices:
                avg_price = sum(prices) / len(prices)
                return {
                    "price_per_sqm": int(avg_price),
                    "source": f"地価公示API（{len(prices)}件平均）",
                    "count": len(prices),
                    "price_range": {
                        "min": min(prices),
                        "max": max(prices),
                        "median": sorted(prices)[len(prices) // 2],
                    },
                }
            return {"price_per_sqm": 400000, "source": "価格データ解析不可", "count": 0}

        except (ValueError, TypeError) as e:
            return {"price_per_sqm": 400000, "source": f"処理エラー: {e}", "count": 0}

    async def get_area_yield_rate(self, address: str) -> float:
        """エリア別利回り情報の取得"""
        cache_key = self._get_cache_key("area_yield", address=address)
        if self._is_cache_valid(cache_key):  # 7日キャッシュ
            return float(self.cache[cache_key])

        try:
            yield_rate = await self._fetch_area_yield_from_sources(address)
        except RuntimeError:
            default_rates = (
                self.api_config.get("estimation_settings", {})
                .get("yield_estimation", {})
                .get("default_yield_rates", {})
            )
            for region, rate in default_rates.items():
                if region in address:
                    return float(rate)
            return float(default_rates.get("その他", 6.0))
        self._set_cache(cache_key, yield_rate, hours=24 * 7)
        return yield_rate

    async def _fetch_area_yield_from_sources(self, address: str) -> float:
        """複数ソースからの利回りデータ取得 (return 回数を削減)。"""
        # 実際の実装: 外部不動産投資サイトAPIを問い合わせる想定。ここでは簡略ロジック。
        yield_rate: float = 6.0  # デフォルト全国平均仮値

        if "東京都" in address:
            if any(ward in address for ward in ["港区", "千代田区", "中央区"]):
                yield_rate = 3.8  # 都心部
            elif any(ward in address for ward in ["新宿区", "渋谷区", "品川区"]):
                yield_rate = 4.2  # 準都心
            else:
                yield_rate = 4.8  # その他東京都
        elif "大阪" in address:
            yield_rate = 5.0 if any(area in address for area in ["中央区", "北区"]) else 5.5
        elif "名古屋" in address or "愛知県" in address:
            yield_rate = 5.8
        elif "福岡" in address:
            yield_rate = 6.2

        return yield_rate

    async def search_comparable_sales(  # pylint: disable=too-many-arguments
        self,
        lat: float,
        lon: float,
        property_type: str,
        building_age: int,
        floor_area: float,
    ) -> List[Dict[str, Any]]:
        """類似物件売買事例の検索"""
        cache_key = self._get_cache_key(
            "comparable_sales",
            lat=lat,
            lon=lon,
            type=property_type,
            age=building_age,
            area=floor_area,
        )
        if self._is_cache_valid(cache_key):
            return list(self.cache[cache_key])

        try:
            # 実際のAPIを使用した類似物件検索
            comparables = await self._fetch_comparable_sales_from_api(
                lat, lon, property_type, building_age, floor_area
            )
            self._set_cache(cache_key, comparables, hours=24)
            return comparables
        except (RuntimeError, ValueError):
            return self._generate_mock_comparable_data(
                lat, lon, property_type, building_age, floor_area
            )

    async def _fetch_comparable_sales_from_api(  # pylint: disable=too-many-arguments
        self,
        lat: float,
        lon: float,
        property_type: str,
        building_age: int,
        floor_area: float,
    ) -> List[Dict[str, Any]]:
        """APIからの類似物件データ取得"""
        # 実際の不動産ポータルAPIを使用する場合の実装
        # 現在は模擬データを返す
        return self._generate_mock_comparable_data(
            lat, lon, property_type, building_age, floor_area
        )

    def _generate_mock_comparable_data(  # pylint: disable=too-many-arguments
        self,
        _lat: float,  # 未使用: 将来の距離フィルタ実装時に利用予定
        _lon: float,  # 未使用: ↑
        property_type: str,
        building_age: int,
        floor_area: float,
    ) -> List[Dict[str, Any]]:
        """模擬比較物件データ生成を小関数に分割して可読性と pylint 指摘削減。"""
        import random  # pylint: disable=import-outside-toplevel

        base_price_per_sqm = self._base_price_per_sqm(property_type)
        adjusted_price_per_sqm = base_price_per_sqm * max(
            0.3, 1 - (building_age * 0.015)
        )

        def build_one(idx: int) -> Dict[str, Any]:
            comp_area = floor_area * random.uniform(0.8, 1.3)
            comp_age = building_age + random.randint(-3, 5)
            distance = random.randint(100, 800)
            distance_factor = max(0.9, 1 - (distance / 1000) * 0.05)
            price_per_sqm = (
                adjusted_price_per_sqm * distance_factor * random.uniform(0.9, 1.1)
            )
            return {
                "id": f"comp_{idx+1:03d}",
                "price": int(price_per_sqm * comp_area),
                "floor_area": round(comp_area, 1),
                "building_age": max(0, comp_age),
                "distance": distance,
                "sale_date": (
                    datetime.now() - timedelta(days=random.randint(30, 365))
                ).strftime("%Y-%m-%d"),
                "property_type": property_type,
                "price_per_sqm": int(price_per_sqm),
            }

        return sorted(
            (build_one(i) for i in range(random.randint(3, 8))),
            key=lambda x: x["distance"],
        )

    @staticmethod
    def _base_price_per_sqm(property_type: str) -> int:
        mapping = {
            "apartment": 600000,
            "house": 500000,
            "small_building": 700000,
        }
        return mapping.get(property_type, 600000)

    async def get_market_trends(
        self, address: str, _property_type: str  # _property_type: 将来のポータル分岐用
    ) -> Dict[str, Any]:
        """市場トレンド情報の取得"""
        cache_key = self._get_cache_key(
            "market_trends", address=address, type=_property_type
        )
        if self._is_cache_valid(cache_key):
            return dict(self.cache[cache_key])

        try:
            trends = await self._fetch_market_trends(address, _property_type)
        except RuntimeError as e:
            return {
                "price_trend": "横ばい",
                "demand_level": "中程度",
                "supply_level": "中程度",
                "market_outlook": "安定",
                "confidence": "低",
                "error": str(e),
            }
        self._set_cache(cache_key, trends, hours=24)
        return trends

    async def _fetch_market_trends(
        self,
        address: str,
        _property_type: str,  # _property_type: 将来の詳細分類で利用予定
    ) -> Dict[str, Any]:
        """市場トレンドデータの取得"""
        # 実装では不動産市況レポートAPI等を使用
        # 現在は住所ベースの簡易判定

        trends = {
            "price_trend": "横ばい",
            "demand_level": "中程度",
            "supply_level": "中程度",
            "market_outlook": "安定",
            "confidence": "中",
        }

        # 地域別の市況調整
        if "東京都" in address:
            if any(area in address for area in ["港区", "千代田区", "中央区"]):
                trends.update(
                    {
                        "price_trend": "上昇",
                        "demand_level": "高",
                        "supply_level": "少",
                        "market_outlook": "良好",
                        "confidence": "高",
                    }
                )
            else:
                trends.update(
                    {
                        "price_trend": "微増",
                        "demand_level": "中程度",
                        "market_outlook": "やや良好",
                    }
                )
        elif any(region in address for region in ["大阪", "名古屋", "福岡"]):
            trends.update(
                {
                    "price_trend": "微増",
                    "demand_level": "中程度",
                    "market_outlook": "安定",
                    "confidence": "中",
                }
            )

        return trends

    # ---- test compatibility placeholders ----
    def _comparable_sales_approach(
        self, property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テストで patch される互換用フック。デフォルトは簡易推定を返す。

        PriceEstimator 側では estimated_price キーが存在する場合そのまま採用される。
        ここではモック生成データの平均を用いた概算値を low confidence で返す。
        """
        property_type = property_data.get("type", "apartment")
        floor_area = property_data.get("floor_area", 50.0)
        construction_year = property_data.get("construction_year")
        building_age = (
            datetime.now().year - construction_year if construction_year else 15
        )
        # 座標はダミー (将来拡張でジオコーディング)
        comparables = self._generate_mock_comparable_data(
            0.0, 0.0, property_type, building_age, floor_area
        )
        prices = [c["price"] for c in comparables]
        avg_price = int(sum(prices) / len(prices)) if prices else None
        return {
            "estimated_price": avg_price,
            "comparable_count": len(comparables),
            "confidence": "low",
            "comparables": comparables[:5],
        }

    def _yield_based_approach(
        self, _property_data: Dict[str, Any]
    ) -> Dict[str, Any]:  # patched in tests / 引数未使用
        """収益還元法フック (デフォルトは未実装を示す None 結果)。

        テストで patch され完全な dict を返すケースを想定。
        """
        return {"estimated_price": None, "area_yield": None, "confidence": "low"}


# 使用例とテスト用関数
async def test_market_data_client() -> None:
    """MarketDataClientのテスト"""
    async with MarketDataClient() as client:
        # 地価データテスト
        land_data = await client.get_land_price_data("東京都新宿区西新宿1-1-1")
        print(f"地価データ: {land_data}")

        # 利回りデータテスト
        yield_rate = await client.get_area_yield_rate("東京都新宿区")
        print(f"エリア利回り: {yield_rate}%")

        # 類似物件検索テスト
        comparables = await client.search_comparable_sales(
            35.6762, 139.6503, "apartment", 5, 50.0
        )
        print(f"類似物件数: {len(comparables)}")

        # 市況トレンドテスト
        trends = await client.get_market_trends("東京都港区", "apartment")
        print(f"市況トレンド: {trends}")


if __name__ == "__main__":
    asyncio.run(test_market_data_client())
