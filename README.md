# ZR Daily Report

ZR Daily Report 是一个用于生成切削液设备日常库存报告的Python应用程序。

## 功能特性

- 多设备批量数据处理
- 自动化数据库查询
- 多种Excel报表生成（含图表）
  - **库存报表**: 生成包含每日原油剩余量和趋势图的报表。
  - **客户对账单**:
    - **动态列数调整**：当同一客户拥有多台使用不同油品的设备时，对账单能自动为每种油品创建独立的统计列，清晰地汇总和展示各油品用量。
  - 每日消耗误差分析
  - 每月消耗误差分析
  - 多设备消耗误差汇总
  - 加注细节记录
- 完整日志记录

## 业务流程概述

该程序的核心业务流程旨在自动化处理设备数据并生成多种分析报表。

1.  **启动与模式选择**:
    -   程序启动后，用户可以通过图形界面或命令行参数选择需要生成的报表类型（如库存报表、对账单等）。

2.  **数据输入**:
    -   **误差消耗汇总报表**：通过日期选择对话框选择日期范围，通过设备筛选对话框选择设备。
    -   **其他报表（每日/每月消耗误差、库存、对账单、加注明细）**：通过日期选择对话框选择日期范围，通过设备筛选对话框选择设备。
    -   **注意**：所有选中的设备使用相同的日期范围。

3.  **数据处理**:
    -   程序根据用户选择的日期范围和设备列表，连接到MySQL数据库。
    -   针对选中的每一台设备，在指定的日期范围内，从数据库中查询相关的库存、消耗和加注数据。
    -   **消耗误差类型报表**：自动从 `test_data/device_config.csv` 读取设备桶数配置。

4.  **报表生成**:
    -   程序将查询到的原始数据进行计算和格式化。
    -   根据用户选择的报表类型，调用相应的报表生成器（如 `InventoryHandler`, `StatementHandler` 等）。
    -   使用 `template/` 目录下的Excel模板作为基础，将处理后的数据和图表填充到模板中。

5.  **结果输出**:
    -   最终生成的 `*.xlsx` 报表文件将保存到用户通过对话框指定的输出目录中。
    -   同时，程序会生成一份详细的日志文件，记录本次操作的所有步骤和结果。

## 系统要求

- **操作系统**:
  - **Windows**: Windows 7 或更高版本 (主要支持和测试平台)。
  - **Linux/macOS**: 支持，但**必须拥有图形用户界面 (GUI) 环境** (如 GNOME, KDE, Aqua 等)，因为程序需要通过文件对话框选择文件和目录。无法在纯命令行服务器上运行。
- **Python**: 3.8 或更高版本。
- **数据库**: MySQL 访问权限。

## 项目依赖

### 核心依赖
- `openpyxl==3.1.0`: 用于处理Excel文件。版本被锁定以**避免图表坐标轴显示异常**，确保库存报表图表功能稳定。
- `mysql-connector-python==8.0.33`: 用于连接MySQL数据库。版本被锁定以**避免已知的内存访问冲突问题**。

### 可选依赖

- **测试依赖 (`[test]`)**: 用于运行自动化测试和生成代码覆盖率报告。
  - `pytest>=7.0.0`
  - `pytest-cov>=4.0.0`
  - `mock>=4.0.0`

- **开发依赖 (`[dev]`)**: 用于代码格式化、静态类型检查和项目打包。
  - `build>=0.10.0`
  - `black>=22.0.0`
  - `mypy>=0.971`

## 安装与配置

### 1. 克隆项目
```bash
# 请将 "https://gitee.com/your-organization/zr-daily-report.git" 替换为您的真实仓库地址
git clone https://gitee.com/your-organization/zr-daily-report.git
cd zr-daily-report
```

### 2. 创建并激活虚拟环境

```bash
# Windows (在命令提示符 cmd.exe 中)
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 1. 安装核心依赖 (运行程序所必需)
pip install .

# 2. 安装所有可选依赖 (推荐开发人员使用)
pip install .[test,dev]
```

### 4. 配置环境

项目的核心配置位于 `config/query_config.json` 文件中，该文件包含数据库连接信息和SQL查询模板。

由于此文件包含敏感信息，它已被 gitignore 规则忽略，不会包含在版本库中。您需要根据示例文件手动创建它：

1.  **复制示例文件**:
    ```bash
    # Windows
    copy config\query_config.example.json config\query_config.json

    # Linux / macOS
    cp config/query_config.example.json config/query_config.json
    ```

2.  **编辑配置文件**:
    打开 `config/query_config.json` 文件，将 `db_config` 对象中的 `"your_database_host"`, `"your_database_user"`, `"your_database_password"` 等占位符替换为您的真实数据库信息。

## 使用方法

### 命令行模式

在项目根目录运行：
```bash
# 交互式选择报表模式 (推荐)
python zr_daily_report.py

# 直接指定报表模式
python zr_daily_report.py --mode <mode_name>
```

可用的 `mode_name` 包括：
- `inventory`: 生成设备库存报表。
- `statement`: 生成客户对账单。
- `refueling`: 生成设备加注细节报表。
- `daily_consumption`: 生成每日消耗误差报表。
- `monthly_consumption`: 生成每月消耗误差报表。
- `error_summary`: 生成多设备消耗误差汇总报表。

如果项目已通过 `pip install .` 安装，还可以使用 `zr-report` 命令代替 `python zr_daily_report.py`。

### 报表生成流程

#### 通用流程（所有报表）

1. **选择报表模式**：启动程序后，选择要生成的报表类型。

2. **选择日期范围**：
   - 系统会弹出日期选择对话框
   - 输入开始日期和结束日期（格式：YYYY-MM-DD）
   - 各报表的日期跨度限制：
     - **每日消耗误差报表**：最大62天（2个月）
     - **每月消耗误差报表**：最大365天（12个月）
     - **库存报表**：最大31天（1个月）
     - **客户对账单**：最大31天（1个月）
     - **加注明细报表**：最大1095天（3年）
   - 如果日期跨度超过限制，系统会提示错误并阻止继续

3. **选择设备**：
   - 系统会弹出设备筛选对话框
   - 在"客户筛选"区域输入客户名称进行搜索
   - 勾选一个或多个客户
   - 系统会自动显示选中客户的所有设备
   - 各报表的设备数量限制：
     - **每月消耗误差报表**：最多50台设备
     - **加注明细报表**：最多50台设备
     - **其他报表**：最多200台设备
   - 点击"确定"确认选择

4. **选择输出目录**：
   - 系统会弹出目录选择对话框
   - 选择报表文件的保存位置

5. **生成报表**：
   - 系统自动为每个设备生成报表文件
   - 所有设备使用相同的日期范围
   - 报表文件命名格式：`{客户名称}_{设备编码}_{开始日期}_to_{结束日期}_{报表类型}.xlsx`

#### 特殊说明

- **消耗误差报表（每日/每月）**：
  - 系统会自动从 `test_data/device_config.csv` 读取设备桶数配置
  - 如果设备未在配置文件中，使用默认值1
  - 桶数配置用于计算消耗误差

- **客户对账单和加注明细报表**：
  - 支持通过程序参数传入设备数据（兼容旧版本调用方式）
  - 如果不传入设备数据，则使用对话框选择

#### 设备桶数配置

对于消耗误差报表，系统需要知道每个设备的油桶数量。配置文件位于 `test_data/device_config.csv`，格式如下：

```csv
device_code,barrel_count
MO24032700700011,2
MO24032700700020,3
```

- `device_code`: 设备编码
- `barrel_count`: 油桶数量（整数，默认为1）

如果设备未在配置文件中，系统会自动使用默认值1。

## 项目结构
```
zr_daily_report/
├── config/              # 配置文件目录
│   ├── query_config.example.json  # 配置文件模板
│   └── error_summary_query.json   # (特定功能配置)
├── src/                 # 源代码目录
│   ├── cli/             # 命令行界面模块
│   ├── core/            # 核心功能模块
│   ├── ui/              # 图形用户界面模块 (文件对话框等)
│   └── utils/           # 工具模块
├── template/            # Excel模板目录
├── tests/               # 测试代码目录
├── test_data/           # 测试数据目录
├── .gitignore           # Git忽略文件
├── pyproject.toml       # 项目配置文件 (PEP 621)
├── README.md            # 项目说明文档
└── zr_daily_report.py   # 主程序入口
```

## 核心功能模块

项目核心逻辑位于 `src/core/` 目录下，主要包括：

- **`report_controller.py`**: 报表控制器，负责协调整个报表生成流程。
- **`data_manager.py`**: 数据管理器，负责数据的获取、缓存和预处理。
- **`db_handler.py`**: 数据库处理器，负责与MySQL数据库的交互。
- **`file_handler.py`**: 文件处理器，处理设备信息等文件的读取。
- **`base_report.py`**: 所有报表生成器的抽象基类，定义了通用的接口和结构。
- **`inventory_handler.py`**: 库存报表处理器，生成包含每日原油剩余量和趋势图的报表。
- **`statement_handler.py`**: 对账单处理器，生成客户对账单。其核心特性是能够动态调整报表列数，当一个客户拥有多台使用不同油品的设备时，它能为每种油品创建专属的数据列进行汇总。
- **`consumption_error_handler.py`**: 包含多个消耗误差报表的生成器：
  - **`DailyConsumptionErrorReportGenerator`**: 生成每日物料消耗的误差分析报表。
  - **`MonthlyConsumptionErrorReportGenerator`**: 生成每月物料消耗的误差分析报表。
  - **`ConsumptionErrorSummaryGenerator`**: 汇总多个设备的消耗误差数据，生成摘要报表。
- **`refueling_details_handler.py`**: 加注细节报表生成器，用于创建详细的设备加注记录。

## 代码质量

项目使用 **black** 进行代码格式化，使用 **mypy** 进行静态类型检查，以保证代码的规范性和健壮性。

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。