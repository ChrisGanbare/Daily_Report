# Daily_Report 项目打包流程完整梳理

## 📋 项目概览

**项目名称**: ZR Daily Report  
**当前分支**: `development-copy`  
**当前版本**: v0.9-11-g75a0085 (距离v0.9版本11个提交)  
**项目类型**: Python应用程序 (GUI + 数据处理)  
**目标平台**: Windows + Linux (CI/CD测试Python 3.8-3.11)

---

## 🏗️ 打包方式概览

项目有**两种主要打包方式**：

| 打包方式 | 用途 | 平台 | 分发方式 |
|---------|------|------|---------|
| **标准Python包** | PyPI发布、pip安装 | Linux/Windows | PyPI (远程) |
| **冻结发行版** | 独立Windows应用 | Windows | ZIP压缩包 (本地) |

---

## 📦 打包方式详解

### 方式1: 标准Python包 (PyPI发布)

#### 构建流程
```
源代码 → Python build系统 → dist/目录 → pyproject.toml配置 → 上传PyPI
```

#### 核心配置文件
- **pyproject.toml** - 项目元数据和构建配置
  - 项目名称: `zr-daily-report`
  - 版本: `1.0.0` (需手动更新)
  - 核心依赖: `openpyxl==3.1.0`, `mysql-connector-python==8.0.33`
  - 入口点: `zr-report = "zr_daily_report:main"`

#### 构建命令
```bash
# 方式1: 使用Python标准构建工具
python -m build

# 输出结果
dist/
├── zr_daily_report-1.0.0-py3-none-any.whl
└── zr_daily_report-1.0.0.tar.gz
```

#### 发布命令
```bash
# 需要PyPI API Token
twine upload dist/*
```

#### 优点和缺点
✅ 优点:
- 跨平台支持
- 通过pip安装简单
- 版本管理规范

❌ 缺点:
- 用户需要安装Python环境
- 依赖项需要编译

---

### 方式2: 冻结发行版 (Windows独立应用)

#### 构建流程
```
源代码 
  ↓
build_package.py frozen
  ↓
frozen_dist/目录
  ├── zr_daily_report/          ← 项目代码
  ├── requirements.txt           ← 核心依赖
  ├── install_report.bat         ← 安装脚本
  ├── run_report.bat            ← 运行脚本
  └── README.txt                ← 说明文档
  ↓
zr_daily_report_v{version}.zip  ← 最终压缩包
```

#### 构建命令
```bash
# 在Windows上执行
python build_package.py frozen

# 输出结果
zr_daily_report_v1.0.0.zip  (15-20MB，取决于依赖)
```

#### 特点说明

**frozen_dist/ 目录结构**:
```
frozen_dist/
├── zr_daily_report/
│   ├── src/                    ← 项目源代码
│   ├── config/                 ← 配置文件 (query_config.json等)
│   ├── template/               ← Excel模板
│   ├── test_data/              ← 测试数据
│   ├── zr_daily_report.py      ← 主程序入口
│   ├── pyproject.toml          ← 项目配置
│   └── setup.py
├── requirements.txt            ← 核心依赖列表
├── install_report.bat          ← Windows安装批处理
├── run_report.bat              ← Windows运行批处理
└── README.txt                  ← 用户说明文档
```

**install_report.bat 功能**:
1. ✓ 检查Python环境 (需要Python 3.8+)
2. ✓ 创建虚拟环境 (venv)
3. ✓ 安装依赖包 (使用阿里云镜像)
4. ✓ 安装项目本身

**run_report.bat 功能**:
1. ✓ 激活虚拟环境
2. ✓ 运行 zr_daily_report.py 主程序

#### 优点和缺点
✅ 优点:
- 完全独立，无需手动安装依赖
- 用户体验好 (双击安装和运行)
- 包含所有必需的配置文件和模板
- 适合非技术用户

❌ 缺点:
- 包体积较大 (ZIP压缩包15-20MB)
- 仅支持Windows
- 需要Python环境 (虚拟环境方式)

---

## 🔄 CI/CD 工作流 (.github/workflows/ci-cd.yml)

### 触发条件
- ✓ Push到 `master` 或 `development` 分支
- ✓ Pull Request到 `master` 分支
- ✓ 手动触发 (workflow_dispatch)

### 工作流组成

#### 1️⃣ Test (测试任务)
**运行平台**: Ubuntu最新版本  
**Python版本**: 3.8, 3.9, 3.10, 3.11

步骤:
- 代码检出
- Python环境配置
- 依赖安装
- 自动生成测试用例
- Flake8代码风格检查
- Pytest单元测试 + 覆盖率报告
- Codecov覆盖率上传

#### 2️⃣ Code Quality (代码质量门禁)
**运行平台**: Ubuntu最新版本  
**Python版本**: 3.10

步骤:
- Flake8检查 (排除指定模块)
- Black代码格式化检查
- isort导入排序检查
- MyPy类型检查
- 代码覆盖率检查 (需要≥80%)

**排除的模块** (故意跳过):
- `src/api/`
- `src/core/async_processor.py`
- `src/core/cache_handler.py`
- `src/core/dependency_injection.py`
- `src/monitoring/progress_monitor.py`
- `src/web/app.py`

#### 3️⃣ Documentation (文档构建)
**运行平台**: Ubuntu最新版本  
**Python版本**: 3.10

步骤:
- 代码检出
- MkDocs文档生成
- 文档作为制品上传

#### 4️⃣ Build (包构建)
**依赖**: Test + Code Quality + Documentation 全部通过  
**运行平台**: Ubuntu最新版本  
**Python版本**: 3.10

步骤:
- 代码检出
- 安装构建工具 (build)
- 执行 `python -m build`
- 上传dist目录制品

#### 5️⃣ Deploy (部署到PyPI)
**条件**: 仅当推送到 master 分支时触发  
**依赖**: Build任务通过  
**运行平台**: Ubuntu最新版本

步骤:
- 下载build任务的制品
- 使用PyPI token发布到PyPI

---

## 📝 版本管理策略

### Git标签管理
```bash
# 查看所有标签
git tag -l --sort=-version:refname

# 输出示例
v0.9  ← 当前最新版本 (2025-09-11)
v0.8
v0.7
...
v0.1.0
```

### 版本获取方式 (build_package.py)

**优先级顺序**:
1. Git标签 (git describe --tags)
   ```bash
   git describe --tags --abbrev=0
   # v0.9
   ```

2. pyproject.toml中的version字段
   ```toml
   version = "1.0.0"
   ```

3. 默认值: "1.0.0"

### 版本号格式
- **标签版本**: v{major}.{minor} (如v0.9)
- **包版本**: {major}.{minor}.{patch} (如1.0.0)
- **描述版本**: v{tag}-{commits}-g{hash} (如v0.9-11-g75a0085)

---

## 🚀 发布流程指南

### 本地打包步骤 (当前development-copy分支)

#### 步骤1: 准备版本
```bash
# 确保在development-copy分支
git checkout development-copy

# 查看当前版本
git describe --tags
# 输出: v0.9-11-g75a0085

# 更新版本号 (如需要)
# 编辑 pyproject.toml
# 修改 version = "1.0.0" → version = "1.1.0"
```

#### 步骤2: 构建冻结发行版 (推荐用于Windows用户)
```bash
# 在项目根目录执行
python build_package.py frozen

# 输出:
# 创建包含冻结依赖的发行版...
# 创建ZIP压缩包...
# ZIP压缩包创建完成: D:\Daily_Report\zr_daily_report_v1.0.0.zip
```

#### 步骤3: 分发
- **Windows用户**: 分发 `zr_daily_report_vX.X.X.zip`
- **Python用户**: 分发 dist/ 中的 .whl 或 .tar.gz

#### 步骤4: 创建Git标签 (可选)
```bash
# 创建新标签
git tag -a v1.0 -m "Release version 1.0"

# 推送标签
git push origin v1.0
```

---

## 📊 文件对比: development-copy vs v0.9

### 统计信息
| 指标 | 数值 |
|------|------|
| 距离v0.9的提交数 | 11个 |
| 修改的文件数 | 21个 |
| 新增行数 | 2,622 |
| 删除行数 | 65 |

### 核心变更
✨ **新增功能**:
- 消耗误差报表处理 (880行新代码)
- 报表控制器增强 (913行改动)
- 日期对话框 (59行)
- 测试用例 (237行)

🔧 **改动模块**:
- 数据管理器 (276行改动)
- 日期工具库 (96行改动)
- 命令行参数解析 (36行改动)

---

## ⚙️ 打包脚本详解 (build_package.py)

### 类: PackageBuilder

#### 初始化 (__init__)
```python
self.project_root      # 项目根目录
self.dist_dir          # frozen_dist目录
self.version           # 项目版本
```

#### 关键方法

**_get_version()**
- 尝试从Git标签获取版本
- 回退到pyproject.toml
- 默认返回 "1.0.0"

**_copy_project_files_flat()**
- 复制源代码到frozen_dist/zr_daily_report/
- 复制项目: README.md, pyproject.toml, zr_daily_report.py
- 复制目录: config/, src/, template/, test_data/

**_freeze_dependencies()**
- 生成requirements.txt (仅核心依赖)
- 内容:
  ```
  openpyxl==3.1.0
  mysql-connector-python==8.0.33
  ```

**_create_user_friendly_scripts()**
- 生成 install_report.bat (UTF-8-BOM编码)
- 生成 run_report.bat (UTF-8-BOM编码)
- 生成 README.txt

**_create_zip_package()**
- 将frozen_dist内容打包为ZIP
- 文件名: zr_daily_report_v{version}.zip
- 移除frozen_dist层级 (ZIP根目录直接是文件)

---

## 📋 配置文件清单

### 打包相关配置

**pyproject.toml**
```toml
[project]
name = "zr-daily-report"
version = "1.0.0"
requires-python = ">=3.8"
dependencies = [
    "openpyxl==3.1.0",
    "mysql-connector-python==8.0.33",
]
```

**requirements.txt** (开发环境完整依赖)
```
openpyxl==3.1.0
mysql-connector-python==8.0.33
pytest==8.3.2
pytest-cov==5.0.0
black==24.8.0
mypy>=0.971
mkdocs==1.5.3
```

**frozen_dist/requirements.txt** (运行时最小依赖)
```
openpyxl==3.1.0
mysql-connector-python==8.0.33
```

**Makefile** (本地开发命令)
```makefile
install      - 安装项目
dev-install  - 安装开发依赖
test         - 运行测试
test-cov     - 生成覆盖率报告
clean        - 清理临时文件
docs         - 生成文档
```

---

## 🔐 .gitignore 配置

```gitignore
# 构建产物
build/
dist/
*.egg-info/

# 测试和覆盖率
.coverage
htmlcov/
.pytest_cache/

# 配置文件 (敏感信息)
config/*.json          # ← 排除所有JSON配置
.env
*.key
*.pem

# IDE
.idea/
.vscode/

# 虚拟环境
.venv/
venv/

# 打包制品
*.tar.gz
*.zip
zr-daily-report-portable/
```

**注意**: `config/*.json` 被排除，因为包含数据库密码等敏感信息

---

## 📊 打包方案对比

### 场景1: 发布给Python开发者
```
方案: PyPI发布
命令: python -m build && twine upload dist/*
输出: PyPI上的zr-daily-report包
安装: pip install zr-daily-report
优点: 规范、跨平台、版本管理
```

### 场景2: 发布给Windows用户
```
方案: 冻结发行版
命令: python build_package.py frozen
输出: zr_daily_report_v{version}.zip
安装: 解压 → 双击install_report.bat → 双击run_report.bat
优点: 完整、独立、用户友好
```

### 场景3: CI/CD自动发布
```
方案: GitHub Actions
触发: Push to master
流程: Test → Code Quality → Build → Deploy to PyPI
管理: 自动版本、自动测试、自动发布
```

---

## ✅ 打包检查清单

在执行打包前，请确认：

- [ ] 所有测试通过 (`pytest`)
- [ ] 代码质量检查通过 (`flake8`, `black`, `mypy`)
- [ ] 配置文件已正确放置 (`config/query_config.json`)
- [ ] 版本号已更新 (pyproject.toml)
- [ ] Git标签已创建 (可选)
- [ ] README和文档已更新
- [ ] 依赖列表已同步 (requirements.txt)

---

## 🔗 相关文档

- **CI/CD流程**: `.github/workflows/ci-cd.yml`
- **构建脚本**: `build_package.py`
- **项目配置**: `pyproject.toml`, `setup.py`
- **项目说明**: `README.md`
- **文档**: `docs/build_guide.md`, `docs/ci_cd_guide.md`

---

## 📞 常见问题

### Q1: 如何更新版本号？
A: 编辑 `pyproject.toml` 中的 `version` 字段，或创建Git标签 `git tag vX.X`

### Q2: 冻结版本为什么这么大？
A: 包含了所有Python依赖（openpyxl, mysql-connector-python等），解决用户Python环境问题

### Q3: 能在Linux上使用冻结版本吗？
A: 不能，冻结版本中的批处理脚本仅支持Windows。Linux用户应使用pip安装

### Q4: 如何自定义虚拟环境位置？
A: 修改install_report.bat中的`python -m venv venv`命令

### Q5: 如何离线部署？
A: 下载frozen_dist目录，将其复制到目标机器，运行install_report.bat即可

---

**文档生成时间**: 2025-11-11  
**适用版本**: v0.9-11-g75a0085 (development-copy分支)

