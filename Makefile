.PHONY: test test-coverage lint format type-check setup clean

# テスト関連
test:
	poetry run pytest -v

test-coverage:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

test-watch:
	poetry run pytest-watch

# コード品質
lint:
	poetry run flake8 src tests
	poetry run isort --check-only src tests
	poetry run black --check src tests

format:
	poetry run isort src tests
	poetry run black src tests

type-check:
	poetry run mypy src

# 環境構築
setup:
	poetry install
	poetry run pre-commit install

# クリーンアップ
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 全チェック実行
check-all: format type-check lint test
