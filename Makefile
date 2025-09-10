# Makefile for ZR Daily Report project

# 默认目标
.PHONY: help
help:
	@echo "ZR Daily Report - Makefile Commands"
	@echo "===================================="
	@echo "install      - 安装项目依赖"
	@echo "dev-install  - 安装开发依赖"
	@echo "test         - 运行测试"
	@echo "test-cov     - 运行测试并生成覆盖率报告"
	@echo "generate-tests - 自动生成测试用例"
	@echo "clean        - 清理临时文件和缓存"
	@echo "docs         - 生成文档"

# 安装项目依赖
.PHONY: install
install:
	pip install -e .

# 安装开发依赖
.PHONY: dev-install
dev-install:
	pip install -e .[dev,test,docs]

# 运行测试
.PHONY: test
test:
	python -m pytest tests/ -v

# 运行测试并生成覆盖率报告
.PHONY: test-cov
test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=html:htmlcov --cov-report=term-missing

# 自动生成测试用例
.PHONY: generate-tests
generate-tests:
	python scripts/generate_tests.py

# 清理临时文件和缓存
.PHONY: clean
clean:
	rm -rf *.egg-info
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# 生成文档
.PHONY: docs
docs:
	mkdocs build

# 格式化代码
.PHONY: format
format:
	black src/ tests/

# 运行类型检查
.PHONY: type-check
type-check:
	mypy src/