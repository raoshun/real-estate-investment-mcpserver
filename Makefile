.PHONY: test test-coverage lint format type-check setup clean

# テスト関連
test:
	poetry run pytest -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing

test-watch:
	pytest-watch

# コード品質
lint:
	flake8 src tests
	isort --check-only src tests
	black --check src tests

format:
	isort src tests
	black src tests

type-check:
	mypy src

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