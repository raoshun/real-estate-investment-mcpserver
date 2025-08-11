# 設計（real-estate-investment-mcpserver）

## アーキテクチャ概要

- パッケージ構成: src/real_estate_mcp/
  - models: Pydanticモデル（Property, PersonalInvestor など）
  - utils: 計算ロジック（calculations）
  - tools: MCPツール定義（PropertyAnalyzerTool など）
  - resources: 予約（設定/外部連携など）
- 依存管理: Poetry（pyproject.toml）
- 品質管理: pre-commit（Black, isort, 基本フック）
- テスト: pytest（tests/ 配下）

## データモデル

- Property
  - 基本情報: id, name, address, type, construction_year, room_layout, floor_area
  - 購入: purchase_price, down_payment, loan_amount, interest_rate, loan_period
  - 収支: monthly_rent, management_fee, repair_reserve, property_tax, insurance
  - 運用: occupancy_months_per_year, tenant_turnover_cost, major_repair_reserve
  - 付帯: created_at, updated_at, notes
- PersonalInvestor
  - プロファイル: annual_income, tax_bracket, investment_experience, risk_tolerance
  - 財務: available_cash, current_debt, monthly_savings
  - 目標: target_monthly_income, investment_period, preferred_property_types, preferred_locations

## 計算ロジック（utils/calculations.py）

- 表面利回り: annual_rent / purchase_price * 100（10桁に丸め）
- 実質利回り: (annual_rent - annual_expenses) / purchase_price * 100
- 月次返済額（元利均等）: 金利0%時は等分割
- 月次CF: rent - payment - expenses
- 回収期間: down_payment / annual_cashflow（<=0 の場合は inf）
- 減価償却: 種別→耐用年数（定数表）で年間額
- 節税効果: (減価償却 + 年間経費) * 税率
- 総合分析: 上記を組み合わせ、丸めルールに沿って出力

### 定数

- DEFAULT_ANNUAL_EXPENSE_RATE=0.20, DEFAULT_LOAN_RATIO=0.80, DEFAULT_INTEREST_RATE=0.025, DEFAULT_LOAN_PERIOD_YEARS=25, DEFAULT_OCCUPANCY_MONTHS=12
- DEPRECIATION_YEARS: {'house':33,'apartment':22,'small_building':22}

## MCPツール（tests/test_tools/test_property_analyzer.py）

- simple_property_analysis(params)
  - 必須: property_price, monthly_rent
  - 任意: initial_cost, annual_expense_rate, loan_ratio, interest_rate, loan_period, investor_annual_income, investor_tax_bracket
  - 出力: gross_yield, net_yield, monthly_cashflow, annual_cashflow, payback_period など

## エラーハンドリング/バリデーション

- validate_calculation_inputs(property_data)
  - 必須項目/>0チェック、loan_amount<=purchase_price、interest_rate[0,0.2]、loan_period[1,35]、occupancy[0,12]
- ツール側では必須項目と>0チェックを事前検証

## テスト戦略

- 単体テスト: 基本ケース/ゼロ・負・極端値/精度確認
- ツールテスト: ハッピーパスと入力エラー
- カバレッジ: addopts で HTML 出力、最低ラインは現状維持（約79%）

## 非機能

- コードスタイル: Black + isort、改行や末尾空行は pre-commit で統制
- 実行性能: 単発呼び出しは < 1s（現行テスト実測）
- セキュリティ: 秘密情報は環境変数/設定ファイル管理（現状は機微データなし）
