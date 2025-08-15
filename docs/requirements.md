# 不動産投資・賃貸経営分析MCPプロジェクト企画書

## プロジェクト概要

### 目的
不動産投資家・賃貸経営者が物件の収益性、リスク、市場動向を総合的に分析し、データドリブンな投資判断を支援するMCPシステムの構築

### ターゲットユーザー
- 個人不動産投資家
- 不動産投資法人
- 賃貸管理会社
- 不動産コンサルタント

## 核心機能領域

### 1. 物件収益性分析
#### 主要指標の算出・追跡
- **表面利回り・実質利回り**：賃料収入対購入価格の収益率
- **キャッシュフロー分析**：月次・年次のキャッシュイン/アウト
- **DCF法による物件評価**：将来キャッシュフロー現在価値
- **ROI・IRR計算**：投資収益率の時間価値を考慮した指標
- **損益分岐点分析**：稼働率・賃料水準の最低ライン

#### 収益構造の可視化
- 賃料収入の安定性評価
- 空室率・回転率の影響シミュレーション
- 修繕費・管理費の適正性チェック

### 2. リスク評価・管理
#### 市場リスク分析
- **立地評価スコア**：交通・商業・教育環境の定量化
- **人口動態分析**：エリアの将来人口予測と賃貸需要
- **競合物件調査**：同一エリア内の供給状況
- **地価動向追跡**：資産価値の変動リスク

#### 運営リスク管理
- 空室期間の予測モデル
- 入居者属性と滞納リスクの相関分析
- 建物老朽化と修繕コスト予測
- 法規制変更の影響評価

### 3. ポートフォリオ管理
#### 保有物件の統合分析
- **分散効果の測定**：地域・物件タイプ・築年数の分散度
- **相関リスク分析**：物件間の収益連動性
- **資金効率性評価**：レバレッジ効果とリスクバランス
- **税務最適化**：減価償却・損益通算の戦略提案

#### パフォーマンス比較
- 物件間の収益性ランキング
- 市場ベンチマークとの比較
- 同業他社との競争力分析

### 4. 市場動向・投資機会発見
#### マクロ経済指標連携
- 金利動向と不動産投資への影響
- インフレ率と賃料上昇の関係性
- GDP成長率と不動産需要の相関

#### 投資機会スクリーニング
- 割安物件の自動検出
- 成長エリアの早期発見
- 売却タイミングの最適化提案

## 技術アーキテクチャ

### MCPサーバー構成
```
real_estate_analysis_mcp/
├── src/
│   ├── tools/
│   │   ├── property_analysis.py      # 物件分析ツール
│   │   ├── market_research.py        # 市場調査ツール
│   │   ├── risk_assessment.py        # リスク評価ツール
│   │   ├── portfolio_management.py   # ポートフォリオ管理
│   │   └── financial_modeling.py     # 財務モデリング
│   ├── resources/
│   │   ├── property_data.py          # 物件データリソース
│   │   ├── market_data.py            # 市場データリソース
│   │   └── portfolio_data.py         # ポートフォリオデータ
│   └── server.py                     # MCPサーバーメイン
├── data/
│   ├── properties/                   # 物件情報
│   ├── market/                       # 市場データ
│   └── external/                     # 外部データ連携
└── config/
    └── settings.yaml                 # 設定ファイル
```

### 外部データソース連携
- **不動産ポータルサイトAPI**：SUUMO、athome、HOME'S等
- **公的統計データ**：国土交通省地価公示、住宅着工統計
- **金融市場データ**：日銀政策金利、国債利回り
- **人口統計**：総務省国勢調査、人口推計

## 主要ツール仕様

### 1. property_valuation
```python
# 物件評価・収益性分析
Parameters:
- property_id: 物件ID
- purchase_price: 購入価格
- monthly_rent: 月額賃料
- expenses: 年間経費
- analysis_period: 分析期間
- discount_rate: 割引率

Returns:
- gross_yield: 表面利回り
- net_yield: 実質利回り
- dcf_value: DCF評価額
- roi_metrics: ROI/IRR指標
```

### 2. risk_analysis
```python
# リスク評価・分析
Parameters:
- property_location: 物件所在地
- property_type: 物件種別
- market_conditions: 市場環境

Returns:
- location_score: 立地評価スコア
- vacancy_risk: 空室リスク評価
- market_risk: 市場リスク指標
- overall_risk_grade: 総合リスク評価
```

### 3. portfolio_optimization
```python
# ポートフォリオ最適化
Parameters:
- current_portfolio: 現在の保有物件
- target_return: 目標収益率
- risk_tolerance: リスク許容度

Returns:
- diversification_score: 分散度評価
- optimization_suggestions: 最適化提案
- rebalancing_plan: リバランス計画
```

### 4. market_intelligence
```python
# 市場動向分析・投資機会発見
Parameters:
- target_areas: 対象エリア
- investment_criteria: 投資基準
- time_horizon: 投資期間

Returns:
- market_trends: 市場トレンド
- growth_areas: 成長エリア
- investment_opportunities: 投資機会
```

## データモデル

### Property（物件）
```yaml
property:
  basic_info:
    id: string
    name: string
    address: string
    type: enum[apartment, house, office, retail]
    construction_year: integer
    total_units: integer

  financial:
    purchase_price: decimal
    current_value: decimal
    monthly_rent: decimal
    annual_expenses: decimal
    mortgage_balance: decimal

  performance:
    occupancy_rate: decimal
    average_vacancy_period: integer
    tenant_turnover_rate: decimal
    maintenance_cost_ratio: decimal
```

### Market（市場データ）
```yaml
market:
  location:
    prefecture: string
    city: string
    district: string
    station_distance: integer

  demographics:
    population: integer
    population_growth_rate: decimal
    age_distribution: object
    household_income: decimal

  supply_demand:
    new_supply: integer
    vacancy_rate: decimal
    average_rent: decimal
    price_trend: array
```

## 実装スケジュール

### Phase 1（基本機能）: 2-3ヶ月
- 物件収益性分析ツール
- 基本的なリスク評価
- データ入力・管理機能

### Phase 2（高度分析）: 2-3ヶ月
- ポートフォリオ最適化
- 市場動向分析
- 外部データ連携

### Phase 3（拡張機能）: 2-3ヶ月
- 予測モデリング
- レポート自動生成
- ダッシュボード機能

## 期待される効果

### 投資判断の精度向上
- データに基づく客観的な物件評価
- 複数物件の定量的比較
- リスクの早期発見・対策

### 運営効率化
- 定期的なパフォーマンス監視
- 問題物件の特定・改善
- 最適な売却タイミング判断

### 収益最大化
- ポートフォリオの最適化
- 新規投資機会の発見
- 税務戦略の最適化

## 今後の発展性

- AIによる価格予測モデル
- IoTデータ連携（スマートメーター等）
- ブロックチェーン技術活用
- 不動産クラウドファンディング連携
