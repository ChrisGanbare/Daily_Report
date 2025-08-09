# ZR Daily Report - Development Branch

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 项目简介

ZR Daily Report 是一个专门用于生成切削液设备日常库存报告的Python应用程序。该程序能够从数据库中查询设备数据，生成包含库存趋势图表和详细数据的Excel报表，并支持生成客户对账单。

此为开发分支，包含最新的功能开发和改进。

## 功能特性

- **多设备批量处理**：支持同时处理多个设备的数据
- **自动化数据查询**：从MySQL数据库自动查询设备库存数据
- **Excel报表生成**：生成包含数据表格和趋势图表的Excel文件
- **智能对账单生成**：根据设备数据自动生成客户对账单
- **动态油品处理**：支持不同数量油品的设备，自动调整表格列数
- **详细日志记录**：完整的执行日志和错误记录
- **配置加密支持**：支持数据库配置文件加密存储

## 技术栈

- Python >= 3.8
- openpyxl >= 3.1.0（Excel文件处理）
- mysql-connector-python >= 8.0.26（数据库连接）
- datetime（日期处理）
- pandas（数据处理）

## 目录结构

```
Daily_Report/
├── ZR_Daily_Report.py              # 主程序
├── README.md                       # 项目说明文档
├── config/                         # 配置文件目录
│   ├── .env                        # 加密密钥
│   ├── query_config.json           # 数据库配置
│   └── query_config_encrypted.json # 加密的数据库配置
├── data/                           # 数据文件目录
│   ├── devices.csv                 # 设备信息文件
│   └── devices_template.csv        # 设备信息模板
├── defect_fixes/                   # 缺陷修复记录目录
│   ├── 20250808_config_file_reading_issue.md  # 配置文件读取问题记录
│   ├── 20250808_statement_multiple_oil_issue.md  # 多油品处理问题记录
│   └── README.md                   # 缺陷修复记录索引
├── docs/                           # 文档目录
│   ├── technical_documentation.md  # 技术文档
│   └── release_plan.md             # 发布计划文档
├── src/                            # 源代码目录
│   ├── core/                       # 核心模块目录
│   │   ├── db_handler.py           # 数据库处理模块
│   │   ├── excel_handler.py        # Excel处理模块
│   │   ├── file_handler.py         # 文件处理模块
│   │   └── statement_handler.py    # 对账单处理模块
│   ├── utils/                      # 工具模块目录
│   │   ├── config_encrypt.py       # 配置加密工具
│   │   ├── config_handler.py       # 配置处理模块
│   │   ├── data_validator.py       # 数据验证模块
│   │   └── date_utils.py           # 日期处理工具
│   └── handlers/                   # 处理器模块目录（预留）
│       └── __init__.py             # 包初始化文件
├── template/                       # 模板目录
│   └── statement_template.xlsx     # 对账单模板
├── tests/                          # 测试目录
│   ├── test_zr_daily_report.py     # 主测试用例
│   └── test_statement_handler.py   # 对账单处理模块测试用例
└── test_output/                    # 测试输出目录
    ├── test_无效数据测试.xlsx
    ├── test_空数据测试.xlsx
    ├── test_缺失数据测试.xlsx
    └── test_连续数据测试.xlsx
```

## 安装说明

### 环境要求

- Python 3.8 或更高版本
- Windows 7 或更高版本操作系统
- 可访问的MySQL数据库

### 安装步骤

1. 克隆项目代码：
```bash
git clone https://github.com/ChrisGanbare/Daily_Report.git
cd Daily_Report
```

2. 创建虚拟环境：
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. 安装依赖（推荐使用阿里云镜像源）：
   ```bash
   # 方法1: 使用批处理脚本（Windows）
   install_deps.bat
   
   # 方法2: 手动安装（单次使用阿里云镜像）
   pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
   
   # 方法3: 永久配置pip源
   pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
   pip install -r requirements.txt
   ```
   
   > 💡 提示：方法1适用于Windows系统一键安装，方法2适用于临时使用阿里云镜像，方法3适用于长期配置

## 配置说明

1. 复制配置模板：
```bash
cp config/query_config_template.json config/query_config.json
```

2. 修改配置文件 `config/query_config.json` 填入实际配置

3. 运行配置加密工具：
```bash
python src/utils/config_encrypt.py
```

4. 确认加密后的配置文件 `config/query_config_encrypted.json` 已正确生成

## 使用说明

1. 准备设备信息文件
   - 使用 `data/devices_template.csv` 作为模板
   - 确保UTF-8编码
   - 填写正确的设备编号和日期范围

2. 激活虚拟环境：
```bash
.venv\Scripts\activate
```

3. 运行程序：
```bash
python ZR_Daily_Report.py
```

4. 生成的报表将保存在当前目录下

## 开发指南

### 分支策略

- **master**：主分支，用于发布正式版本
- **development**：开发分支，用于日常开发和优化（当前分支）

### 开发流程

1. 从development分支创建功能分支
2. 在功能分支上进行开发
3. 提交更改并推送
4. 创建Pull Request合并到development分支

### 代码规范

- 遵循PEP 8 Python代码规范
- 添加适当的注释和文档字符串
- 编写单元测试以确保代码质量
- 使用类型提示提高代码可读性

### 测试

运行所有测试：
```bash
python -m unittest discover tests
```

## 版本管理

项目采用语义化版本控制，当前处于子版本阶段（v0.x.x）。

详细版本规划请参考 [docs/release_plan.md](docs/release_plan.md) 文件。

## 文档

- [技术文档](docs/technical_documentation.md)：详细的项目技术说明
- [发布计划](docs/release_plan.md)：项目发布计划和版本规划
- [缺陷修复记录](defect_fixes/)：历史缺陷修复记录

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 许可证

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。