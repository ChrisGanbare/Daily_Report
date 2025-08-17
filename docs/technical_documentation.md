# ZR Daily Report 项目技术文档

## 1. 概述

本文档详细描述了 ZR Daily Report 项目的技术架构、模块设计和实现细节。文档旨在帮助开发者理解项目结构、核心组件和扩展功能。

## 2. 项目结构

```
D:\Daily_Report\
├── config/                     # 配置文件目录
│   ├── query_config.json       # 数据库查询配置
│   └── query_config_template.json  # 配置模板
├── data/                       # 数据文件目录
│   ├── devices.csv             # 设备信息模板文件
│   └── devices_example.csv     # 设备信息示例文件
├── docs/                       # 文档目录
│   ├── technical_documentation.md
│   └── version_plan.md
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── core/                   # 核心功能模块
│   │   ├── __init__.py
│   │   ├── db_handler.py       # 数据库处理模块
│   │   ├── file_handler.py     # 文件处理模块
│   │   ├── inventory_handler.py  # 库存报表处理模块
│   │   ├── statement_handler.py  # 对账单处理模块
│   │   └── async_processor.py  # 异步处理模块
│   ├── utils/                  # 工具模块
│   │   ├── __init__.py
│   │   ├── config_encrypt.py   # 配置加密模块
│   │   ├── config_handler.py   # 配置处理模块
│   │   ├── data_validator.py   # 数据验证模块
│   │   └── date_utils.py       # 日期处理模块
│   └── web/                    # Web应用模块
│       └── app.py              # Web应用入口
├── template/                   # 模板目录
│   └── statement_template.xlsx # 对账单模板
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── TESTING.md              # 测试框架文档
│   ├── test_statement_handler.py
│   └── test_zr_daily_report.py
├── .env                        # 环境变量文件
├── .gitignore                  # Git忽略文件
├── defect_fixes/               # 缺陷修复记录
│   ├── 20250808_config_file_reading_issue.md
│   ├── 20250808_statement_multiple_oil_issue.md
│   ├── defect_fixes_index.md
│   └── README.md
├── query_config.json           # 查询配置文件(加密)
├── README.md                   # 项目说明文档
├── requirements.txt            # 依赖包列表
└── ZR_Daily_Report.py          # 主程序文件
```

## 3. 核心模块说明

### 3.1 数据库处理模块 (db_handler.py)
负责与MySQL数据库的连接和数据查询操作。

### 3.2 文件处理模块 (file_handler.py)
处理设备信息文件的读取和解析。

### 3.3 库存报表处理模块 (inventory_handler.py)
生成设备库存报表和趋势图表。

### 3.4 对账单处理模块 (statement_handler.py)
生成客户对账单，支持动态油品列处理。

## 4. 扩展模块说明

### 4.1 异步处理模块 (async_processor.py)
实现异步任务处理功能。

### 4.2 工具模块 (utils/)
提供各种辅助工具函数。

### 4.3 Web应用模块 (web/app.py)
提供Web界面访问功能。

## 5. 数据流说明

1. 程序启动后读取配置文件
2. 从数据库查询设备数据
3. 处理数据并生成报表
4. 输出Excel文件

## 6. 配置说明

项目使用JSON格式的配置文件，包含数据库连接信息和查询语句模板。

```
{
    "host": "[加密保护]",
    "port": 3306,
    "database": "oil",
    "user": "[加密保护]",
    "queries": {
        "device_id": "SELECT device_id FROM devices",
        "inventory_data": "SELECT * FROM inventory WHERE device_id = %s"
    }
}
