# src/real_estate_mcp/server.py
"""不動産投資分析MCPサーバー"""

import asyncio
import importlib.metadata
import logging
from typing import Any, Dict, List, Optional, Tuple

# 外部依存が lint 環境に無い場合の import-error を抑制
from mcp.server import Server  # pylint: disable=import-error
from mcp.types import Resource, TextContent, Tool  # pylint: disable=import-error

try:  # Optional dependency; provide lightweight fallback to avoid import-error in lint env
    from pydantic import AnyUrl  # type: ignore
except (ImportError, AttributeError):  # pragma: no cover

    class AnyUrl(str):  # type: ignore
        """Fallback AnyUrl 型 (簡易: 単なる str)。pydantic 未導入環境向け。"""


from .models.investor_model import PersonalInvestor
from .models.property_model import Property
from .utils.calculations import calculate_property_analysis, validate_calculation_inputs

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealEstateMCPServer:
    """不動産投資分析MCPサーバー"""

    def __init__(self) -> None:
        self.server = Server("real-estate-investment-mcp")
        self.properties: Dict[str, Property] = {}
        self.investors: Dict[str, PersonalInvestor] = {}

        # ツールとリソースの登録
        self._register_tools()
        self._register_resources()

    def _register_tools(self) -> None:
        """MCPツールの登録 (Server インスタンスへ list / call handlers をバインド)"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """利用可能なツール一覧を返す"""
            return [
                Tool(
                    name="analyze_property",
                    description="物件の収益性分析を実行",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_price": {
                                "type": "number",
                                "description": "物件価格（円）",
                            },
                            "monthly_rent": {
                                "type": "number",
                                "description": "月額賃料（円）",
                            },
                            "initial_cost": {
                                "type": "number",
                                "description": "初期費用（円）",
                                "default": 0,
                            },
                            "loan_ratio": {
                                "type": "number",
                                "description": "融資比率（0.0-1.0）",
                                "default": 0.8,
                            },
                            "interest_rate": {
                                "type": "number",
                                "description": "金利（0.0-1.0）",
                                "default": 0.025,
                            },
                            "loan_period": {
                                "type": "integer",
                                "description": "返済期間（年）",
                                "default": 25,
                            },
                            "annual_expense_rate": {
                                "type": "number",
                                "description": "年間経費率（0.0-1.0）",
                                "default": 0.2,
                            },
                            "investor_tax_bracket": {
                                "type": "number",
                                "description": "投資家の税率（オプション）",
                                "default": 0.2,
                            },
                        },
                        "required": ["property_price", "monthly_rent"],
                    },
                ),
                Tool(
                    name="register_property",
                    description="物件情報をシステムに登録",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_data": {
                                "type": "object",
                                "description": "物件情報（Property モデル準拠）",
                            }
                        },
                        "required": ["property_data"],
                    },
                ),
                Tool(
                    name="compare_properties",
                    description="複数物件の収益性比較",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "比較対象物件ID一覧",
                            }
                        },
                        "required": ["property_ids"],
                    },
                ),
                Tool(
                    name="portfolio_analysis",
                    description="ポートフォリオ全体の分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "investor_id": {"type": "string", "description": "投資家ID"},
                            "property_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "分析対象物件ID一覧（オプション）",
                            },
                        },
                        "required": ["investor_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[TextContent]:  # noqa: D401
            """ツール実行"""
            try:
                if name == "analyze_property":
                    return await self._analyze_property(arguments)
                if name == "register_property":
                    return await self._register_property(arguments)
                if name == "compare_properties":
                    return await self._compare_properties(arguments)
                if name == "portfolio_analysis":
                    return await self._portfolio_analysis(arguments)
                raise ValueError(f"Unknown tool: {name}")
            except (KeyError, ValueError, TypeError) as e:
                logger.warning("Tool input/validation error: %s", e)
                return [TextContent(type="text", text=f"入力エラー: {e}")]
            # 予期しない内部例外は上位へ (テストで検知しやすくする)

    # テストで patch される想定のラッパー (decorator 内関数を直接使わないケース向け)
    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:  # pragma: no cover
        """decorator 外部からのテスト用ディスパッチ (ラップ)。"""
        return await self._dispatch_tool(name, arguments)

    async def _dispatch_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:  # noqa: D401
        """ツール名に応じて内部実装関数へ振り分ける。"""
        if name == "analyze_property":
            return await self._analyze_property(arguments)
        if name == "register_property":
            return await self._register_property(arguments)
        if name == "compare_properties":
            return await self._compare_properties(arguments)
        if name == "portfolio_analysis":
            return await self._portfolio_analysis(arguments)
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    def _register_resources(self) -> None:
        """MCPリソースの登録"""

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """利用可能なリソース一覧"""
            resources: List[Resource] = []
            # AnyUrl バリデーション回避のため host を付与
            for property_id, property_obj in self.properties.items():
                # AnyUrl: host にドットを含める (pydantic のバリデーション回避)
                resources.append(
                    Resource(
                        uri=f"property://local.host/{property_id}",  # type: ignore[arg-type]
                        name=f"物件: {property_obj.name}",
                        description=f"物件ID {property_id} の詳細情報",
                        mimeType="application/json",
                    )
                )
            for investor_id, _investor_obj in self.investors.items():
                resources.append(
                    Resource(
                        uri=f"investor://local.host/{investor_id}",  # type: ignore[arg-type]
                        name="投資家プロファイル",
                        description=f"投資家ID {investor_id} のプロファイル",
                        mimeType="application/json",
                    )
                )
            return resources

        @self.server.read_resource()  # type: ignore[misc]
        async def read_resource(uri: AnyUrl) -> str:  # noqa: D401
            """リソース内容の読み取り (AnyUrl 互換)"""
            uri_str = str(uri)
            if uri_str.startswith("property://local.host/"):
                property_id = uri_str.replace("property://local.host/", "")
                if property_id in self.properties:
                    return str(self.properties[property_id].model_dump_json(indent=2))
                raise ValueError(f"Property not found: {property_id}")
            if uri_str.startswith("investor://local.host/"):
                investor_id = uri_str.replace("investor://local.host/", "")
                if investor_id in self.investors:
                    return str(self.investors[investor_id].model_dump_json(indent=2))
                raise ValueError(f"Investor not found: {investor_id}")
            raise ValueError(f"Unknown resource URI: {uri_str}")

    async def _analyze_property(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """物件分析ツールの実装 (外部入力のキーを内部仕様へマッピング)"""
        try:
            # 外部インターフェース: property_price -> purchase_price に変換
            normalized: Dict[str, Any] = dict(arguments)
            if "property_price" in normalized and "purchase_price" not in normalized:
                normalized["purchase_price"] = normalized.pop("property_price")

            # loan_ratio が 0-1 か 0-100 か曖昧な入力を正規化
            if "loan_ratio" in normalized:
                lr = normalized["loan_ratio"]
                if lr > 1:  # 例: 80 -> 0.8
                    lr = lr / 100
                normalized["loan_amount"] = normalized.get(
                    "loan_amount", normalized["purchase_price"] * lr
                )

            # interest_rate も同様に 2.5 -> 0.025 のケースを補正
            if "interest_rate" in normalized:
                ir = normalized["interest_rate"]
                if ir > 1:
                    normalized["interest_rate"] = ir / 100

            validation_errors = validate_calculation_inputs(normalized)
            if validation_errors:
                error_msg = "入力エラー: " + ", ".join(validation_errors.values())
                return [TextContent(type="text", text=error_msg)]

            investor_data = None
            if "investor_tax_bracket" in normalized:
                investor_data = {"tax_bracket": normalized["investor_tax_bracket"]}

            analysis_result = calculate_property_analysis(normalized, investor_data)
            result_text = self._format_analysis_result(analysis_result, normalized)
            return [TextContent(type="text", text=result_text)]
        except (KeyError, ValueError, TypeError) as e:
            return [TextContent(type="text", text=f"入力エラー: {e}")]

    # 予期しない例外は上位へ

    async def _register_property(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """物件登録ツールの実装"""
        try:
            property_data = arguments["property_data"]
            property_obj = Property(**property_data)
            self.properties[property_obj.id] = property_obj
            return [
                TextContent(
                    type="text",
                    text=f"物件 '{property_obj.name}' (ID: {property_obj.id}) を登録しました。",
                )
            ]
        except (KeyError, TypeError, ValueError) as e:
            return [TextContent(type="text", text=f"登録入力エラー: {e}")]

    # 予期しない例外は上位へ

    async def _compare_properties(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """物件比較ツールの実装"""
        try:
            property_ids = arguments["property_ids"]
            if len(property_ids) < 2:
                return [TextContent(type="text", text="比較には2つ以上の物件が必要です。")]
            comparison_results: List[Dict[str, Any]] = []
            for property_id in property_ids:
                if property_id not in self.properties:
                    return [
                        TextContent(type="text", text=f"物件ID {property_id} が見つかりません。")
                    ]
                property_obj = self.properties[property_id]
                property_data = {
                    "purchase_price": property_obj.purchase_price,
                    "monthly_rent": property_obj.monthly_rent,
                    "loan_amount": property_obj.loan_amount,
                    "interest_rate": property_obj.interest_rate,
                    "loan_period": property_obj.loan_period,
                    "annual_expenses": property_obj.annual_expenses,
                }
                analysis = calculate_property_analysis(property_data)
                analysis["property_name"] = property_obj.name
                analysis["property_id"] = property_id
                comparison_results.append(analysis)
            result_text = self._format_comparison_result(comparison_results)
            return [TextContent(type="text", text=result_text)]
        except (KeyError, ValueError, TypeError) as e:
            return [TextContent(type="text", text=f"比較入力エラー: {e}")]

    # 予期しない例外は上位へ

    async def _portfolio_analysis(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """ポートフォリオ分析ツールの実装"""
        try:
            investor_id = arguments["investor_id"]
            property_ids = arguments.get("property_ids", list(self.properties.keys()))
            if investor_id not in self.investors:
                return [TextContent(type="text", text=f"投資家ID {investor_id} が見つかりません。")]
            investor = self.investors[investor_id]
            portfolio_properties: List[Property] = [
                self.properties[pid] for pid in property_ids if pid in self.properties
            ]
            if not portfolio_properties:
                return [TextContent(type="text", text="分析対象の物件がありません。")]
            result_text = self._analyze_portfolio(portfolio_properties, investor)
            return [TextContent(type="text", text=result_text)]
        except (KeyError, ValueError, TypeError) as e:
            return [TextContent(type="text", text=f"ポートフォリオ入力エラー: {e}")]

    # 予期しない例外は上位へ

    def _format_analysis_result(
        self, analysis: Dict[str, Any], inputs: Dict[str, Any]
    ) -> str:
        """分析結果の整形 (テスト期待値にあわせた表示)"""
        purchase_price = inputs.get("purchase_price", 0)
        monthly_rent = inputs.get("monthly_rent", 0)
        loan_amount = inputs.get(
            "loan_amount", purchase_price * 0.8 if purchase_price else 0
        )
        loan_ratio = loan_amount / purchase_price if purchase_price else 0

        # 推奨メッセージ
        recommendation = ""
        if analysis["gross_yield"] >= 6.0:
            recommendation = "\n💎 高利回り物件: 利回りが高く魅力的です。"
        elif analysis["gross_yield"] <= 4.0:
            recommendation = "\n💔 低利回り物件: 収益性に注意が必要です。"

        # payback を事前算出 (長行回避)
        payback = analysis["payback_period"] if analysis["payback_period"] else "算出不可"
        result = (
            "🏠 不動産投資分析結果\n\n"
            "📊 基本情報\n"
            f"・物件価格: {purchase_price:,}円\n"
            f"・月額賃料: {monthly_rent:,}円\n"
            f"・融資比率: {int(round(loan_ratio * 100))}%\n"
            "\n📈 収益性指標\n"
            f"・表面利回り: {analysis['gross_yield']:.2f}%\n"
            f"・実質利回り: {analysis['net_yield']:.2f}%\n"
            f"・月次キャッシュフロー: {analysis['monthly_cashflow']:,}円\n"
            f"・年間キャッシュフロー: {analysis['annual_cashflow']:,}円\n"
            "\n💰 投資回収\n"
            f"・投資回収期間: {payback}年\n"
            f"・月次ローン返済: {analysis['monthly_loan_payment']:,}円\n"
            "\n🏛️ 税務効果\n"
            f"・年間減価償却: {analysis['annual_depreciation']:,}円\n"
            f"・年間節税効果: {analysis['annual_tax_benefit']:,}円\n"
            f"・税引後年間収益: {analysis['net_annual_income']:,}円"
            f"{recommendation}\n"
        )
        return result

    def _format_comparison_result(self, comparisons: List[Dict[str, Any]]) -> str:
        """比較結果の整形"""
        result = "🔍 物件比較結果\n\n"

        # 利回り順でソート
        sorted_comparisons = sorted(
            comparisons, key=lambda x: x["gross_yield"], reverse=True
        )

        for i, comp in enumerate(sorted_comparisons, 1):
            result += f"{i}位: {comp['property_name']}\n"
            result += f"   表面利回り: {comp['gross_yield']}%\n"
            result += f"   月次CF: {comp['monthly_cashflow']:,}円\n"
            # 回収期間表示 (長行を避けるため一時変数使用)
            _pp = comp["payback_period"] if comp["payback_period"] else "算出不可"
            result += f"   回収期間: {_pp}年\n\n"

        return result

    def _analyze_portfolio(
        self, properties: List[Property], investor: PersonalInvestor
    ) -> str:
        """ポートフォリオ分析の実行"""
        total_investment = sum(prop.purchase_price for prop in properties)
        total_monthly_rent = sum(prop.monthly_rent for prop in properties)
        total_annual_cashflow = 0

        result = f"💼 ポートフォリオ分析 (投資家: {investor.investment_experience.value})\n\n"

        for prop in properties:
            property_data = {
                "purchase_price": prop.purchase_price,
                "monthly_rent": prop.monthly_rent,
                "annual_expenses": prop.annual_expenses,
            }
            analysis = calculate_property_analysis(
                property_data, {"tax_bracket": investor.tax_bracket}
            )
            total_annual_cashflow += analysis["annual_cashflow"]

        result += "📊 ポートフォリオサマリー\n"
        result += f"・総投資額: {total_investment:,}円\n"
        result += f"・総月収: {total_monthly_rent:,}円\n"
        result += f"・総年間CF: {total_annual_cashflow:,}円\n"
        if investor.target_monthly_income:
            result += (
                "・目標月収達成度: "
                f"{(total_monthly_rent/investor.target_monthly_income)*100:.1f}%\n"
            )
        return result

    async def run(
        self,
        streams: Optional[Tuple[Any, Any]] = None,
        initialization_options: Optional[Any] = None,
        *,
        raise_exceptions: bool = False,
        stateless: bool = False,
    ) -> None:  # noqa: D401
        """MCPサーバー起動ヘルパー。

        mcp.Server.run は (read_stream, write_stream, initialization_options) を要求するため、
        ここで stdio 用トランスポートを生成し InitializationOptions を組み立てて呼び出す。

        任意でテスト用に既存の stream / options を受け取れるようにしている。
        """
        from mcp.server.models import (  # pylint: disable=import-error,import-outside-toplevel
            InitializationOptions,
        )
        from mcp.server.stdio import (  # pylint: disable=import-error,import-outside-toplevel
            stdio_server,
        )
        from mcp.types import (  # pylint: disable=import-error,import-outside-toplevel
            ServerCapabilities,
        )

        logger.info("Real Estate Investment MCP Server starting...")

        # InitializationOptions が未指定なら自動生成
        if initialization_options is None:
            try:
                version = importlib.metadata.version("real-estate-investment-mcp")
            except (
                importlib.metadata.PackageNotFoundError
            ):  # pragma: no cover - フォールバック
                version = "0.0.0"
            instructions_text = "不動産投資物件の分析、比較、ポートフォリオ集計ツールを提供します。"
            initialization_options = InitializationOptions(
                server_name=self.server.name,
                server_version=version,
                capabilities=ServerCapabilities(),
                instructions=instructions_text,
            )

        # 既に stream タプルが渡されている (例えばテスト) 場合はそのまま利用
        if streams is not None:
            read_stream, write_stream = streams
            await self.server.run(
                read_stream,
                write_stream,
                initialization_options,
                raise_exceptions=raise_exceptions,
                stateless=stateless,
            )
            return

        # stdio 経由で実行 (通常起動パス)
        async with stdio_server() as (r, w):
            await self.server.run(
                r,
                w,
                initialization_options,
                raise_exceptions=raise_exceptions,
                stateless=stateless,
            )

    # ---------------- 売却価格推定 (テスト互換用内部ヘルパー) -----------------
    async def _estimate_sale_price(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """売却価格推定ツール相当の内部メソッド (tests/test_price_estimation 用)。

        互換要件:
          - property_id から登録済み物件情報を引ける
          - property_data を直接与えた場合はそれを利用
          - estimation_methods に "market_data" / "market" が含まれれば market_based へ正規化
          - include_market_analysis=True なら市場分析 (_get_market_analysis) を並行取得
          - 予期しない例外も握り潰してテキスト化 (テスト要件)
        """
        from .utils.price_estimation import (  # 遅延 import: 起動時依存最小化  # pylint: disable=import-outside-toplevel
            estimate_property_sale_price,
        )

        try:
            # estimation_methods 正規化
            raw_methods = arguments.get("estimation_methods") or [
                "comparable",
                "yield_based",
                "market_based",
            ]
            if raw_methods == ["all"]:
                raw_methods = ["comparable", "yield_based", "market_based"]
            methods = [
                "market_based" if m in ("market_data", "market") else m
                for m in raw_methods
            ]

            include_market = bool(arguments.get("include_market_analysis"))

            # property_data 構築
            property_data: Dict[str, Any] = {}
            if "property_id" in arguments:
                pid = arguments["property_id"]
                if pid not in self.properties:
                    return [TextContent(type="text", text=f"物件ID {pid} が登録されていません。")]
                property_data.update(self.properties[pid].model_dump())
            if "property_data" in arguments:
                property_data.update(dict(arguments["property_data"]))

            if not property_data.get("address"):
                return [TextContent(type="text", text="住所情報が不足しています。")]

            # 推定 & 市場分析 (必要なら並行)
            if include_market:
                estimation, market = await asyncio.gather(
                    estimate_property_sale_price(property_data, methods),
                    self._get_market_analysis(property_data),
                )
            else:
                estimation = await estimate_property_sale_price(property_data, methods)
                market = None

            text = self._format_sale_price_result(property_data, estimation, market)
            return [TextContent(type="text", text=text)]
        except (KeyError, TypeError, ValueError) as e:
            return [TextContent(type="text", text=f"推定入力エラー: {e}")]
        except Exception as e:  # pylint: disable=broad-exception-caught
            return [TextContent(type="text", text=f"売却価格推定エラー: {e}")]

    async def _get_market_analysis(
        self, _property_data: Dict[str, Any]
    ) -> Dict[str, Any]:  # pylint: disable=unused-argument
        """市場分析 (簡易モック)。テストで patch され遅延/値挿入される前提。"""
        # ここでは最低限のキー構造を返す。必要なら将来 API 呼び出しを実装。
        return {
            "land_price": {"price_per_sqm": None},
            "area_yield": None,
            "market_trends": {},
        }

    def _format_sale_price_result(
        self, _property_data: dict, estimation: dict, market: dict | None
    ) -> str:
        """売却価格推定 + 市場分析を段階的に整形し、複雑度を抑制。"""
        final_price, confidence, estimates = self._extract_final_estimate(estimation)
        if final_price is None:
            return "売却価格推定結果: エラー - 推定できませんでした。"
        lines = self._build_estimation_lines(final_price, confidence, estimates)
        if market and not market.get("error"):
            lines.extend(self._build_market_lines(market))
        lines.extend(self._build_recommendation_lines(estimation))
        return "\n".join(lines)

    # --- sale price formatting helpers ---
    def _extract_final_estimate(
        self, estimation: Dict[str, Any]
    ) -> Tuple[Optional[int], Optional[float], Dict[str, Dict[str, Any]]]:
        if (
            "final_estimate" in estimation
            and estimation["final_estimate"].get("price") is not None
        ):
            return (
                estimation["final_estimate"]["price"],
                estimation.get("confidence_score"),
                estimation.get("estimates", {}),
            )
        return (
            estimation.get("estimated_price"),
            estimation.get("confidence_score"),
            {"comparable": estimation},
        )

    def _build_estimation_lines(
        self,
        final_price: int,
        confidence: Optional[float],
        estimates: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        lines = ["🧾 売却価格推定結果", f"・推定売却価格: {final_price:,}円"]
        if confidence is not None:
            lines.append(f"・信頼度スコア: {confidence:.2f}")
        labels = {
            "comparable": "比較事例法",
            "yield_based": "収益還元法",
            "market_based": "市場データ法",
        }
        for key, label in labels.items():
            est = estimates.get(key)
            if est and est.get("estimated_price") is not None:
                lines.append(f"・{label}: {est['estimated_price']:,}円")
        return lines

    def _build_market_lines(self, market: Dict[str, Any]) -> List[str]:
        lines: List[str] = ["", "📊 市場分析"]
        land = market.get("land_price", {})
        if land.get("price_per_sqm"):
            lines.append(f"・地価(㎡): {int(land['price_per_sqm']):,}円")
        if market.get("area_yield") is not None:
            lines.append(f"・エリア利回り: {market['area_yield']:.2f}%")
        trends = market.get("market_trends", {})
        if trends:
            lines.append(f"・市況トレンド: {trends.get('price_trend', '-')}")
        return lines

    def _build_recommendation_lines(self, estimation: Dict[str, Any]) -> List[str]:
        recs = estimation.get("recommendations") or estimation.get("recommendation")
        if not recs:
            return []
        lines: List[str] = ["", "💡 推奨"]
        if isinstance(recs, list):
            lines.extend([f"- {r}" for r in recs])
        else:
            lines.append(f"- {recs}")
        return lines

    # --- lifecycle helpers ---
    async def cleanup(self) -> None:  # pragma: no cover - trivial
        """テスト互換用の後処理フック (外部リソース解放拡張のプレースホルダ)。"""
        # ここでは保持しているリソースが無いため何もしない。
        return None


# サーバー起動用の関数
async def main() -> None:
    """メイン関数"""
    server = RealEstateMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
