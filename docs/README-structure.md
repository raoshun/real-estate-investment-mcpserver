# プロジェクト構成

現在の実装済み構成を示します（将来拡張は `requirements.md` の Backlog を参照）。

```text
real-estate-investment-mcpserver/
├── docs/                              # ドキュメント（要件 / 設計 / タスク / 構成）
│   ├── requirements.md                # 機能要件（実装済/予定の整理付き）
│   ├── design.md                      # 技術設計（計算ロジック / MCP ツール）
│   ├── tasks.md                       # 作業タスクリスト
│   └── README-structure.md            # このファイル
├── src/
│   └── real_estate_mcp/               # パッケージ本体
│       ├── server.py                  # MCP サーバーエントリ（ツール/リソース登録）
│       ├── models/                    # Pydantic モデル（Property / PersonalInvestor）
│       ├── utils/                     # 計算ロジック（calculations.py）
│       ├── tools/                     # （現状: 空。テスト用クラスは tests 配下に定義）
│       └── resources/                 # 予約ディレクトリ（未使用）
├── tests/                             # pytest テスト
│   ├── test_utils/                    # 計算ロジック単体テスト
│   ├── test_tools/                    # ツール相当（簡易分析クラス）のテスト
│   └── test_mcp_server.py             # サーバー統合/フォーマットテスト
├── config/
│   └── settings.yaml                  # 設定サンプル（現時点でコード未参照）
├── data/                              # データ置き場（Git 管理は用途に応じ取捨）
│   ├── market/
│   ├── properties/
│   └── templates/
├── .github/workflows/ci.yml           # CI（lint / type-check / test / coverage）
├── .pre-commit-config.yaml            # 事前フック（black, isort 等）
├── Makefile                           # 開発補助ターゲット
├── pyproject.toml                     # Poetry / ツール設定
├── poetry.lock
├── README.md                          # 利用/起動方法など（実装済）
└── htmlcov/                           # 直近テストの HTML Coverage レポート
```

## 命名に関する注意

旧案 `real_estate_investment_mcp` ではなく、実際のパッケージ名は `real_estate_mcp` です。ドキュメント内で古い名前が残っていた箇所は順次更新済みです。

## 実装済み / 未実装 の境界

- 実装済み: 物件収益性分析（利回り / CF / 減価償却 / 節税効果）と MCP ツール 4 種（`analyze_property`, `register_property`, `compare_properties`, `portfolio_analysis`）。
- 未実装（Backlog）: DCF / IRR / 高度リスク評価 / 市場データ連携 / 最適化アルゴリズム等。

## 補足

- `tests/test_tools/test_property_analyzer.py` 内の `PropertyAnalyzerTool` は概念検証用の独立クラスで、MCP サーバーへまだ組み込まれていません（将来 `src/real_estate_mcp/tools/` へ移動予定）。
- `resources/` ディレクトリは将来の外部データ/API ラップ用プレースホルダです。
