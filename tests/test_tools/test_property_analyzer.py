"""個人投資家向け物件分析ツール"""

from typing import Dict, Any, Optional
from real_estate_mcp.utils.calculations import calculate_property_analysis


class PropertyAnalyzerTool:
    """物件分析ツール"""

    def __init__(self):
        self.name = "property_analyzer"
        self.description = "個人投資家向けの物件収益性分析"

    async def simple_property_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        簡単物件分析
        
        Args:
            params: 分析パラメータ
                - property_price: 物件価格
                - monthly_rent: 月額賃料
                - initial_cost: 初期費用（デフォルト0）
                - annual_expense_rate: 年間経費率（デフォルト20%）
                - loan_ratio: 融資割合（デフォルト80%）
                - interest_rate: 金利（デフォルト2.5%）
                - loan_period: 返済期間（デフォルト25年）
                - investor_annual_income: 投資家年収（オプション）
                - investor_tax_bracket: 投資家税率（オプション）
                
        Returns:
            Dict[str, Any]: 分析結果
        """
        
        # 入力バリデーション
        required_fields = ['property_price', 'monthly_rent']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"{field} is required")
            if params[field] <= 0:
                raise ValueError(f"{field} must be greater than 0")
        
        # デフォルト値の設定
        property_price = params['property_price']
        monthly_rent = params['monthly_rent']
        initial_cost = params.get('initial_cost', 0)
        annual_expense_rate = params.get('annual_expense_rate', 0.20)
        loan_ratio = params.get('loan_ratio', 0.80)
        interest_rate = params.get('interest_rate', 0.025)
        loan_period = params.get('loan_period', 25)
        
        # 物件データの構築
        loan_amount = property_price * loan_ratio
        down_payment = property_price - loan_amount + initial_cost
        
        property_data = {
            'purchase_price': property_price,
            'monthly_rent': monthly_rent,
            'loan_amount': loan_amount,
            'down_payment': down_payment,
            'interest_rate': interest_rate,
            'loan_period': loan_period,
            'annual_expense_rate': annual_expense_rate,
            'type': 'apartment'  # デフォルト
        }
        
        # 投資家データの構築（オプション）
        investor_data = None
        if 'investor_annual_income' in params or 'investor_tax_bracket' in params:
            investor_data = {
                'annual_income': params.get('investor_annual_income', 0),
                'tax_bracket': params.get('investor_tax_bracket', 0.20)
            }
        
        # 分析実行
        analysis_result = calculate_property_analysis(property_data, investor_data)
        
        # 追加情報の付与
        analysis_result.update({
            'loan_amount': loan_amount,
            'down_payment': down_payment,
            'loan_to_price_ratio': loan_ratio * 100,
            'analysis_date': '2025-01-01',  # 実際は現在日時
            'recommendation': self._generate_recommendation(analysis_result)
        })
        
        return analysis_result
    
    def _generate_recommendation(self, analysis: Dict[str, Any]) -> str:
        """
        分析結果に基づく簡単な推奨事項を生成
        
        Args:
            analysis: 分析結果
            
        Returns:
            str: 推奨事項
        """
        gross_yield = analysis.get('gross_yield', 0)
        net_yield = analysis.get('net_yield', 0)
        monthly_cashflow = analysis.get('monthly_cashflow', 0)
        
        if gross_yield >= 6.0:
            if monthly_cashflow > 0:
                return "高利回りでキャッシュフロープラス。良い投資案件です。"
            else:
                return "高利回りですがキャッシュフロー要注意。運営費用を見直してください。"
        elif gross_yield >= 4.0:
            if monthly_cashflow >= 0:
                return "標準的な利回り。安定した投資として検討できます。"
            else:
                return "利回りは標準的ですが、キャッシュフローが厳しいです。"
        else:
            return "低利回りです。他の物件との比較検討をお勧めします。"


# MCPツール登録用の関数
def create_property_analyzer_tools():
    """Property Analyzer用のMCPツールを作成"""
    analyzer = PropertyAnalyzerTool()
    
    return [
        {
            "name": "simple_property_analysis",
            "description": "個人投資家向けの簡単な物件収益性分析",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "property_price": {
                        "type": "number",
                        "description": "物件価格（円）"
                    },
                    "monthly_rent": {
                        "type": "number", 
                        "description": "月額賃料（円）"
                    },
                    "initial_cost": {
                        "type": "number",
                        "description": "初期費用（円）",
                        "default": 0
                    },
                    "annual_expense_rate": {
                        "type": "number",
                        "description": "年間経費率（0.0-1.0）",
                        "default": 0.20
                    },
                    "loan_ratio": {
                        "type": "number",
                        "description": "融資割合（0.0-1.0）",
                        "default": 0.80
                    },
                    "interest_rate": {
                        "type": "number",
                        "description": "金利（0.0-1.0）",
                        "default": 0.025
                    },
                    "loan_period": {
                        "type": "integer",
                        "description": "返済期間（年）",
                        "default": 25
                    }
                },
                "required": ["property_price", "monthly_rent"]
            },
            "handler": analyzer.simple_property_analysis
        }
    ]