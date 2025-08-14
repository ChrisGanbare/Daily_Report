.PHONY: help install test quality quality-fast lint typecheck clean docs doc-serve doc-build

help:
	@echo "Available targets:"
	@echo "  install     Install all dependencies"
	@echo "  test        Run tests"
	@echo "  quality     Run all quality checks (may modify files)"
	@echo "  quality-fast  Run all quality checks (read-only)"
	@echo "  lint        Run style checks"
	@echo "  typecheck   Run type checks"
	@echo "  clean       Clean build artifacts"
	@echo "  docs        Build documentation"
	@echo "  doc-serve   Start documentation server"
	@echo "  doc-build   Build documentation"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/

quality:
	black src tests
	isort src tests
	flake8 src tests
	mypy src tests

quality-fast:
	black --check src tests
	isort --check-only src tests
	flake8 src tests
	mypy src tests

lint:
	flake8 src tests

typecheck:
	mypy src tests

clean:
	rm -rf .tox .pytest_cache .mypy_cache .coverage htmlcov *.egg-info dist build site
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docs: doc-build

doc-serve:
	python scripts/build_docs.py serve

doc-build:
	python scripts/build_docs.py build