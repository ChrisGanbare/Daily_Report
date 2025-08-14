# ZR Daily Report

ZR Daily Report 是一个用于生成切削液设备日常库存报告的Python应用程序。

## 1. 项目概述

### 项目背景
目标用户: 需要设备库存管理的工业设备管理人员和财务对账人员

### 核心问题
- 需要自动化生成设备库存报告
- 需要可视化库存趋势图表
- 需要自动生成客户对账单
- 需要处理不同油品数量的设备数据

## 2. 系统功能

### 主要功能
- 多设备批量数据处理
- 自动化数据库查询
- Excel报表生成（含图表）
- 客户对账单自动生成
- 动态列数调整（适应不同油品数量）
- 配置文件加密存储
- 完整日志记录

### 关键特性
- 支持加密配置文件
- 支持动态油品处理
- 提供详细的缺陷修复记录

## 3. 技术架构

### 技术选型
- 语言: Python 3.8+
- Excel处理: openpyxl 3.1.0+
- 数据库连接: mysql-connector-python 8.0.26+
- 数据处理: pandas 1.5.0+
- 测试框架: pytest 7.0.0+
- 代码规范: flake8 5.0.0+, black 22.0.0+
- 类型检查: mypy 0.971+

### 目录结构
```
.
├── config/                 # 配置文件目录
├── data/                   # 数据文件目录
├── defect_fixes/           # 缺陷修复记录目录
├── docs/                   # 文档目录
├── src/                    # 源代码目录
│   ├── core/               # 核心功能模块
│   ├── handlers/           # 处理器模块
│   └── utils/              # 工具模块
├── template/               # 报表模板目录
├── tests/                  # 测试用例目录
├── test_output/            # 测试输出目录
├── .github/workflows/      # GitHub Actions工作流
├── ZR_Daily_Report.py      # 主程序
├── requirements.txt        # 项目依赖
├── Dockerfile              # Docker配置文件
├── docker-compose.yml      # Docker编排文件
└── README.md               # 项目说明文件
```

## 4. 开发环境搭建

### 必需工具
- Python 3.8+
- Windows 7+ 操作系统或Linux/macOS
- MySQL数据库访问权限

### 搭建步骤
1. 克隆项目:
   ```bash
   git clone https://github.com/ChrisGanbare/Daily_Report.git
   ```
2. 创建虚拟环境:
   ```bash
   python -m venv .venv
   ```
3. 激活虚拟环境:
   - Windows: `.venv\Scripts\activate`
   - Linux/macOS: `source .venv/bin/activate`
4. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

## 5. 安装

使用以下命令安装依赖：

```bash
pip install -r requirements.txt
```

或者安装开发依赖：

```bash
pip install -r requirements.txt[dev]
```

## 6. 代码质量检查

本项目使用多种工具来确保代码质量：

1. **flake8**: 代码风格检查工具，用于检查代码是否符合PEP 8规范
2. **black**: 代码格式化工具，确保代码风格一致性
3. **mypy**: 静态类型检查工具，发现潜在的类型错误
4. **isort**: 导入语句排序工具，保持导入语句的一致性

### 本地运行代码质量检查

使用tox运行所有检查：

```bash
# 运行所有测试环境
tox

# 只运行代码风格检查
tox -e lint

# 只运行类型检查
tox -e typecheck
```

或者使用Makefile：

```bash
# 安装依赖
make install

# 运行所有质量检查（可能修改文件）
make quality

# 运行所有质量检查（只读模式）
make quality-fast

# 分别运行特定检查
make lint
make typecheck
```

或者使用专门的脚本：

```bash
# 运行所有代码质量检查（不修改文件）
python scripts/run_code_quality.py

# 安装代码质量检查工具
python scripts/run_code_quality.py --install
```

### Git Hooks

项目支持Git hooks来在提交前自动运行代码质量检查。可以通过以下方式设置：

```bash
# 运行脚本自动设置Git hooks
python scripts/setup-git-hooks.py
```

设置后，每次提交时会自动运行：
1. 代码格式化 (black 和 isort)
2. 代码风格检查 (flake8)
3. 类型检查 (mypy)

如果任何检查失败，提交将被中止。

## 持续集成/持续部署 (CI/CD)

项目使用GitHub Actions进行持续集成。工作流程包括：
1. 在多个Python版本上运行测试
2. 运行代码质量检查
3. 构建Python包
4. 在满足条件时部署到PyPI

代码质量门禁包括：
- 必须通过所有测试
- 代码覆盖率必须达到80%以上
- 必须通过所有代码质量检查

## 7. 使用说明

### 程序运行模式
```bash
# 生成库存报表和客户对账单（默认）
python ZR_Daily_Report.py

# 只生成库存报表
python ZR_Daily_Report.py --mode inventory

# 只生成客户对账单
python ZR_Daily_Report.py --mode statement
```

### 配置文件
1. 创建加密密钥文件 `config/.env`
2. 创建明文配置文件 `config/query_config.json`
3. 运行工具脚本生成加密配置文件 `config/query_config_encrypted.json`

## 8. 测试

运行测试:
```bash
python -m pytest tests/ -v
```

## 9. 部署

### Docker部署
构建Docker镜像:
```bash
docker build -t zr-daily-report .
```

运行容器:
```bash
docker run -d --name zr-report zr-daily-report
```

### Docker Compose部署
```bash
docker-compose up -d
```

## 10. 贡献

欢迎提交Issue和Pull Request来改进项目。

## 11. 许可证

[待定]