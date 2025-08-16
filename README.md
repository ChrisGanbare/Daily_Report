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
- Windows 7+ 操作系统
- MySQL数据库访问权限

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

# 方式3: 配置永久使用阿里云镜像源，然后正常安装
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt

# 方式4: 安装锁定版本的依赖（确保环境一致性，推荐用于生产环境）
pip install -r requirements-lock.txt

# 方式5: 直接安装（可能较慢，特别是中国大陆用户）
pip install -r requirements.txt
```

推荐中国大陆用户使用阿里云镜像源安装依赖，可以显著提高下载速度。

## 文档

本项目使用 MkDocs 和 Material for MkDocs 构建文档。

### 预览文档

```bash
# 启动本地服务器预览文档
mkdocs serve
```

Then in your browser open http://localhost:8000 to view the documentation.

### 构建文档

```bash
# 构建静态文档站点
mkdocs build
```

构建后的文档将位于 [site](file:///D:/pythonfile/Daily_Report/site) 目录中。

## 环境配置

项目支持双重数据库驱动以提高兼容性：
- 优先使用 `mysql-connector-python`（版本8.0.33）
- 备选使用 `PyMySQL`（版本1.0.0+）

详细环境配置信息请参考 [环境配置文档](docs/environment_config.md)。

## 使用方法

### 运行程序

```bash
# 生成库存报表和客户对账单（默认）
python ZR_Daily_Report.py

# 只生成库存报表
python ZR_Daily_Report.py --mode inventory

# 只生成客户对账单
python ZR_Daily_Report.py --mode statement
```

## 项目结构
```
.
├── config/              # 配置文件目录
├── data/                # 数据文件目录
├── defect_fixes/        # 缺陷修复记录目录
├── docs/                # 文档目录
├── src/                 # 源代码目录
│   ├── core/            # 核心功能模块
│   ├── handlers/        # 处理器模块
│   ├── monitoring/      # 监控模块
│   ├── utils/           # 工具模块
│   └── web/             # Web应用模块
├── template/            # 报表模板目录
├── test_output/         # 测试输出目录
├── tests/               # 测试用例目录
│   └── TESTING.md       # 测试框架文档
├── ZR_Daily_Report.py   # 主程序
├── requirements.txt     # 依赖配置文件
└── requirements-lock.txt # 锁定版本的依赖配置文件
```

## 依赖管理最佳实践

本项目遵循以下依赖管理最佳实践：

### 1. 虚拟环境强制使用
- 所有开发必须在虚拟环境中进行
- 虚拟环境目录(.venv)必须加入.gitignore

### 2. 依赖版本控制
- 使用requirements.txt管理依赖
- 对关键依赖指定具体版本号(如`package==1.2.3`)
- 使用`requirements-lock.txt`锁定所有依赖的确切版本

### 3. 依赖安装验证
- 新开发者应使用`pip install -r requirements.txt`验证依赖安装
- 使用阿里云镜像加速安装: `pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

### 4. 自动化验证流程
- 在CI/CD中集成依赖安装和测试流程
- 使用GitHub Actions等工具自动验证不同Python版本的依赖兼容性

### 5. 依赖管理工具
- 推荐使用pipenv或poetry进行依赖管理
- 使用tox进行多环境测试

### 6. 文档化要求
- 在README.md中明确记录环境设置和依赖安装步骤
- 包含虚拟环境创建、激活和依赖安装的完整流程说明

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


### 配置文件
1. 创建加密密钥文件 `config/.env`
2. 创建明文配置文件 `config/query_config.json`
3. 运行工具脚本生成加密配置文件 `config/query_config_encrypted.json`

## 8. 测试

运行测试:
```bash
python -m pytest tests/ -v
```



## 11. 许可证

[待定]