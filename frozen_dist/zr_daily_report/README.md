# ZR Daily Report

ZR Daily Report 是一个用于生成切削液设备日常库存报告的Python应用程序。

## 功能特性

- 多设备批量数据处理
- 自动化数据库查询
- Excel报表生成（含图表）
- 客户对账单自动生成
- 动态列数调整（适应不同油品数量）
- 配置文件加密存储
- 完整日志记录

## 项目依赖

- Python 3.8+
- Windows 7+ 操作系统（Linux/macOS也支持部分功能）
- MySQL数据库访问权限

核心依赖：
- openpyxl == 3.1.0 (Excel处理)
- mysql-connector-python >= 8.0.33, < 9.0.0 (MySQL数据库连接)
- pandas >= 1.5.0 (数据处理)

Web框架依赖：
- fastapi == 0.104.1 (Web API框架)
- uvicorn[standard] == 0.24.0 (ASGI服务器)
- jinja2 == 3.1.2 (模板引擎)
- python-multipart == 0.0.6 (文件上传支持)

缓存支持依赖：
- redis == 5.0.1
- aioredis == 2.0.1

监控和日志依赖：
- prometheus-client == 0.19.0
- structlog == 23.2.0

测试依赖：
- pytest == 8.3.2
- pytest-cov == 5.0.0
- pytest-asyncio == 0.21.1
- httpx == 0.25.2
- mock >= 4.0.0
- tox >= 3.25.0

开发工具依赖：
- black == 24.8.0
- mypy >= 0.971
- isort == 5.12.0
- pre-commit >= 3.3.0

文档生成依赖：
- mkdocs == 1.5.3
- mkdocs-material == 9.4.8

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/ChrisGanbare/Daily_Report.git
```

### 2. 创建虚拟环境并激活

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

有多种方式可以安装项目依赖：

```bash
# 方式1: Windows一键安装（推荐）
install_deps.bat

# 方式2: 使用阿里云镜像源安装（推荐，特别是中国大陆用户）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 方式3: 使用pip安装基础依赖
pip install .

# 方式4: 安装所有依赖（包括测试和开发依赖）
pip install .[all]

# 方式5: 分别安装特定功能依赖
pip install .[test]     # 测试依赖
pip install .[dev]      # 开发依赖
pip install .[docs]     # 文档依赖
```

### 4. 构建项目（可选）

项目提供了构建脚本 [build_package.py](file://D:\Daily_Report\build_package.py) 来创建发行版：

```bash
# 构建标准发行版（wheel 和源码包）
python build_package.py

# 构建包含冻结依赖的完整发行版
python build_package.py frozen

# 显示帮助信息
python build_package.py help
```

更多构建信息请参考 [构建指南](docs/build_guide.md)。

### 5. 配置环境

1. 复制环境配置文件：
   ```bash
   copy .env.example .env
   ```

2. 编辑 .env 文件，配置数据库连接信息

3. 配置 query_config.json 文件，设置数据库查询语句

## 使用方法

### 命令行模式

```bash
# 生成库存报表和客户对账单（默认模式）
python zr_daily_report.py

# 只生成库存报表
python zr_daily_report.py --mode inventory

# 只生成客户对账单
python zr_daily_report.py --mode statement
```

### 配置说明

程序需要正确配置数据库连接信息和查询语句。详细配置说明请参考 [环境配置文档](docs/environment_config.md)。

## 项目结构
```
zr_daily_report/
├── config/              # 配置文件目录
├── data/                # 数据文件目录
├── defect_fixes/        # 缺陷修复记录目录
├── docs/                # 文档目录
├── src/                 # 源代码目录
│   ├── core/            # 核心功能模块
│   ├── handlers/        # 处理器模块
│   ├── monitoring/      # 监控模块
│   ├── utils/           # 工具模块
├── template/            # 模板目录
├── tests/               # 测试目录
├── .env                 # 环境变量文件
├── .gitignore           # Git忽略文件
├── query_config.json    # 查询配置文件(加密)
├── README.md            # 项目说明文档
├── requirements.txt     # 依赖包列表
└── zr_daily_report.py   # 主程序文件
```

## 核心功能模块

### 数据库处理模块
负责与MySQL数据库的连接和数据查询操作。

### 文件处理模块
处理设备信息文件的读取和解析。

### 库存报表处理模块
生成设备库存报表和趋势图表。

### 对账单处理模块
生成客户对账单，支持动态油品列处理。

## 配置文件

项目使用加密的配置文件存储数据库连接信息和查询语句。配置文件位于 `config/` 目录下。

## 代码质量

项目使用多种工具来确保代码质量：

1. **black**: 代码格式化工具，确保代码风格一致性
2. **mypy**: 静态类型检查工具，发现潜在的类型错误
3. **isort**: 导入语句排序工具，保持导入语句的一致性

### 本地运行代码质量检查

使用tox运行所有检查：

```bash
# 运行所有测试环境
tox


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
2. 类型检查 (mypy)

如果任何检查失败，提交将被中止。

## 持续集成/持续部署 (CI/CD)

项目使用GitHub Actions进行持续集成。工作流程包括：
1. 在多个Python版本上运行测试
2. 运行代码质量检查
3. 构建Python包

## 测试

项目包含全面的测试套件，详情请参考 [测试文档](tests/TESTING.md)。

## 缺陷修复记录

项目开发过程中发现并修复的重要缺陷记录请参考 [缺陷修复记录](docs/defect_fixes/defect_fixes_index.md)

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。