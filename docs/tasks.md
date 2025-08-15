# タスクリスト（real-estate-investment-mcpserver）

## 1. 環境/品質

- [x] Poetry のセットアップ（pyproject.toml）
- [x] pre-commit 導入／インストール（Black, isort, hooks）
- [x] Makefile タスク整備（test, lint, format, type-check, check-all）

## 2. データモデル

- [ ] Property モデルのフィールド/バリデーション見直し（型定義は実装済・追加バリデーション未）
- [ ] PersonalInvestor モデルのバリデーション/境界値処理（未実装）

## 3. 計算ロジック（utils/calculations.py）

- [x] マジックナンバーの定数化（済）
- [x] 月次返済ロジックの境界条件（期間<=0）の防御（済）
- [ ] 丸め規則の一貫化（表面利回り10桁、出力は丸め箇所を明確化）※最終出力で gross_yield が 2桁丸め
- [ ] validate_calculation_inputs のエラーメッセージ定数化（任意）
- [x] 追加テスト（ゼロ・負・極端値の組合せ）

## 4. MCPツール

- [x] simple_property_analysis の入力スキーマと説明を README/docs に明記（design.md に記載）
- [ ] 推奨メッセージのルールを外部化（任意）

## 5. データ/設定

- [x] config/settings.yaml のサンプル雛形（設定ファイルあり）
- [ ] data/ 配下の扱いを整理（バージョン管理しない/するの基準）

## 6. CI（任意）

- [x] GitHub Actions で lint/test を実行（.github/workflows/ci.yml）

## 7. ドキュメント

- [x] docs/requirements.md（済）
- [x] docs/design.md（済）
- [x] docs/tasks.md（本ファイル）
