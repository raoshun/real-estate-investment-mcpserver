# タスクリスト（real-estate-investment-mcpserver）

## 1. 環境/品質

- [ ] Poetry のセットアップ（pyproject.toml）
- [ ] pre-commit 導入／インストール（Black, isort, hooks）
- [ ] Makefile タスク整備（test, lint, format, type-check, check-all）

## 2. データモデル

- [ ] Property モデルのフィールド/バリデーション見直し
- [ ] PersonalInvestor モデルのバリデーション/境界値処理

## 3. 計算ロジック（utils/calculations.py）

- [ ] マジックナンバーの定数化（済）
- [ ] 月次返済ロジックの境界条件（期間<=0）の防御（済）
- [ ] 丸め規則の一貫化（表面利回り10桁、出力は丸め箇所を明確化）
- [ ] validate_calculation_inputs のエラーメッセージ定数化（任意）
- [ ] 追加テスト（ゼロ・負・極端値の組合せ）

## 4. MCPツール

- [ ] simple_property_analysis の入力スキーマと説明を README/docs に明記
- [ ] 推奨メッセージのルールを外部化（任意）

## 5. データ/設定

- [ ] config/settings.yaml のサンプル雛形（必要に応じて）
- [ ] data/ 配下の扱いを整理（バージョン管理しない/するの基準）

## 6. CI（任意）

- [ ] GitHub Actions で lint/test を実行

## 7. ドキュメント

- [ ] docs/requirements.md（済）
- [ ] docs/design.md（済）
- [ ] docs/tasks.md（本ファイル）
