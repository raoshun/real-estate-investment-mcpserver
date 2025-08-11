# プロジェクト構成

```text
real-estate-investment-mcpserver/
├── docs/                      # 設計・要件・タスクのドキュメント
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── src/
│   └── real_estate_mcp/       # アプリ本体
│       ├── models/
│       ├── utils/
│       ├── tools/
│       └── resources/
├── tests/                     # テスト
├── config/                    # 設定（例: settings.yaml）
├── data/                      # データ（Git管理は基本除外推奨）
├── Makefile
├── pyproject.toml
├── poetry.lock
├── .pre-commit-config.yaml
├── .gitignore
└── README.md
```

メモ:

- `real_estate_investment_mcp/` は旧構成と思われるため、未使用であれば削除/除外を検討してください。
