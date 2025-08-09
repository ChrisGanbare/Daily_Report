# ZR Daily Report 测试框架

## 测试框架概述

本项目采用现代化的测试框架，基于pytest构建，包含单元测试、集成测试和功能测试。

## 测试结构

```
tests/
├── __init__.py              # 包初始化文件
├── base_test.py            # 测试基类，提供通用测试工具
├── test_inventory_reports.py  # 库存报表功能测试
├── test_statement_handler.py  # 对账单处理模块测试
├── test_zr_daily_report.py    # 主程序功能测试
└── README.md               # 测试文档
```

## 测试依赖

测试框架依赖以下工具：

- pytest: 主要测试框架
- pytest-cov: 代码覆盖率工具
- mock: 模拟对象库
- flake8: 代码风格检查工具

## 运行测试

### 使用pytest直接运行

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_inventory_reports.py

# 运行特定测试类
pytest tests/test_inventory_reports.py::TestInventoryReports

# 运行特定测试方法
pytest tests/test_inventory_reports.py::TestInventoryReports::test_generate_excel_with_chart_success

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 使用测试运行脚本

```bash
# 运行所有测试
python run_tests.py

# 运行单元测试
python run_tests.py --unit

# 运行集成测试
python run_tests.py --integration

# 运行测试并生成覆盖率报告
python run_tests.py --coverage

# 运行代码风格检查
python run_tests.py --lint
```

## 测试类型

### 单元测试

单元测试针对单个函数或类进行测试，不依赖外部系统。

标记: `@pytest.mark.unit`

### 集成测试

集成测试验证多个模块协同工作的情况。

标记: `@pytest.mark.integration`

### 功能测试

功能测试验证整个功能模块的正确性。

## 测试覆盖率

项目要求测试覆盖率达到80%以上。覆盖率报告会自动生成在`htmlcov`目录中。

## 编写测试

### 测试基类

所有测试应继承`BaseTestCase`类，它提供了：

- 临时目录管理
- 常用测试数据生成
- 通用断言方法

### 测试命名规范

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

### 测试数据

测试应使用模拟数据，避免依赖真实数据库或外部服务。

## 持续集成

项目支持使用tox进行多Python版本测试：

```bash
# 运行所有支持的Python版本测试
tox

# 运行特定Python版本测试
tox -e py38

# 运行代码风格检查
tox -e lint
```