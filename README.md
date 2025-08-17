# Real Estate Investment MCP Server

個人投資家向け不動産投資分析を行う Model Context Protocol (MCP) 対応サーバー実装です。表面/実質利回り、キャッシュフロー、減価償却・概算節税効果、投資回収期間など基本指標を計算し、物件比較・簡易ポートフォリオ集計ツールを提供します。

## 現在の実装範囲

- MCP ツール
	- `analyze_property`: 単一物件の収益性分析
	- `register_property`: 物件モデル登録（メモリ保持）
	- `compare_properties`: 複数登録物件の利回り・CF 比較
	- `portfolio_analysis`: 投資家 + 複数物件集計（キャッシュフロー/目標達成度）
- 計算ロジック (`utils/calculations.py`)
	- 表面/実質利回り
	- 月次ローン返済（元利均等, 金利0%対応）
	- 月次/年間キャッシュフロー
	- 投資回収期間（非回収= `None` として表示）
	- 減価償却（建物比率デフォルト 70%, 種別ごとの耐用年数）
	- 概算節税効果（減価償却 + 経費 × 税率）
- モデル: `Property`, `PersonalInvestor`
- テスト: 単体 + サーバーフォーマット/エッジケース（HTML カバレッジ生成）

## 未実装（Backlog 抜粋）

DCF / IRR / リスクスコアリング / 市場データ連携 / 最適レバレッジ提案 / 地域統計 API / 最適化アルゴリズム など。詳細は `docs/requirements.md` を参照。

## セットアップ

Poetry 使用。

```bash
poetry install
```

pre-commit フック（任意）:

```bash
poetry run pre-commit install
```

## テスト

```bash
poetry run pytest -v
```

カバレッジ HTML は `htmlcov/index.html`。

## 使い方（MCP サーバー起動）

CLI から stdio で起動（エディタ/クライアント側が MCP プロトコル経由で接続する想定）。

```bash
poetry run python -m real_estate_mcp.server
```

### 代表ツール: analyze_property

入力例（論理的にクライアントが送信する JSON ペイロード）:

```jsonc
{
	"name": "analyze_property",
	"arguments": {
		"property_price": 30000000,
		"monthly_rent": 120000,
		"loan_ratio": 0.8,          // 80% (80 でも可、自動正規化)
		"interest_rate": 2.5,       // 2.5% (0.025 でも可、自動正規化)
		"loan_period": 25,
		"annual_expense_rate": 0.2,
		"investor_tax_bracket": 0.2 // 任意
	}
}
```

出力（テキスト整形済）には以下指標が含まれます:

- 表面/実質利回り
- 月次/年間キャッシュフロー
- 投資回収期間
- 月次ローン返済額
- 減価償却・概算節税効果・税引後年間収益
- 利回り閾値による簡易推奨 (>=6% 高利回り / <=4% 低利回り)

### 物件登録と比較

1. `register_property` で `Property` モデル項目（id, name など）を登録
2. `compare_properties` で `property_ids` を渡すと利回り順ランキングを返却

### ポートフォリオ分析

`portfolio_analysis` に `investor_id`（事前に `self.investors` へ追加する実装は今後拡張予定）と `property_ids` を渡し、総投資額 / 総月収 / 年間 CF / 目標達成率を算出。

## 設計のポイント

- 経費率は「購入価格」ではなく「年間賃料収入」に適用（過剰経費で極端な赤字になる問題を修正）
- 金利/融資比率は 1.0 超過入力（例: 80, 2.5）を自動的に百分率→少数へ正規化
- バリデーション (`validate_calculation_inputs`) で基本的な境界値検査
- 推奨メッセージは現状ハードコード（将来外部設定化予定）

## 開発タスク状況

`docs/tasks.md` を参照。未着手項目: 追加バリデーション強化 / 丸め規則統一 / 推奨ロジック外部化 など。

## ライセンス / 著作権

（必要に応じ記載）

## 貢献

Issue / PR 歓迎。スタイルは pre-commit & CI を参照してください。
