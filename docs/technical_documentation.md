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
│   ├── cli/                    # 命令行接口模块
│   │   ├── __init__.py
│   │   └── argument_parser.py  # 命令行参数解析
│   ├── core/                   # 核心功能模块
│   │   ├── __init__.py
│   │   ├── base_report.py      # 报表生成基类
│   │   ├── db_handler.py       # 数据库处理模块
│   │   ├── file_handler.py     # 文件处理模块
│   │   ├── inventory_handler.py  # 库存报表处理模块
│   │   ├── statement_handler.py  # 对账单处理模块
│   │   ├── refueling_details_handler.py  # 加注明细处理模块
│   │   ├── report_controller.py  # 报表控制模块
│   │   ├── data_manager.py     # 数据管理模块
│   │   ├── cache_handler.py    # 缓存处理模块
│   │   ├── async_processor.py  # 异步处理模块
│   │   └── dependency_injection.py  # 依赖注入模块
│   ├── handlers/               # 处理器模块
│   │   └── __init__.py
│   ├── monitoring/             # 监控模块
│   │   └── progress_monitor.py # 进度监控模块
│   ├── ui/                     # 用户界面模块
│   │   ├── __init__.py
│   │   ├── mode_selector.py    # 模式选择对话框
│   │   ├── filedialog_selector.py  # 文件对话框选择器
│   │   └── selector.py         # 选择器基类
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
└── zr_daily_report.py          # 主程序文件
```

## 3. 核心模块说明

### 3.1 数据库处理模块 (db_handler.py)
负责与MySQL数据库的连接和数据查询操作，支持连接池管理。

### 3.2 文件处理模块 (file_handler.py)
处理设备信息文件的读取和解析，支持多种编码格式（UTF-8、GBK等）。

### 3.3 库存报表处理模块 (inventory_handler.py)
生成设备库存报表和趋势图表，支持Excel格式输出。

### 3.4 对账单处理模块 (statement_handler.py)
生成客户对账单，支持动态油品列处理，基于Excel模板进行数据填充。

### 3.5 加注明细处理模块 (refueling_details_handler.py)
处理加注订单明细数据，生成详细报表。

### 3.6 报表控制模块 (report_controller.py)
协调库存报表和客户对账单的生成流程，是核心业务逻辑控制器。

## 4. 扩展模块说明

### 4.1 异步处理模块 (async_processor.py)
实现异步任务处理功能，提高大数据量处理性能。

### 4.2 缓存处理模块 (cache_handler.py)
提供缓存功能，减少重复数据库查询，提高系统响应速度。

### 4.3 依赖注入模块 (dependency_injection.py)
实现依赖注入容器，降低模块间耦合度，提高代码可测试性和可维护性。

### 4.4 工具模块 (utils/)
提供各种辅助工具函数，包括配置处理、日期处理等。

### 4.5 Web应用模块 (web/app.py)
提供Web界面访问功能，基于FastAPI构建。

### 4.6 用户界面模块 (ui/)
提供图形用户界面功能，包括模式选择对话框和文件选择对话框。

## 5. 数据流说明

1. 程序启动后读取配置文件
2. 显示模式选择界面（命令行参数或图形界面）
3. 读取设备信息CSV文件
4. 连接数据库查询设备和库存数据
5. 处理数据并生成报表
6. 输出Excel文件

## 6. 配置说明

项目使用JSON格式的配置文件，包含数据库连接信息和查询语句模板。

```json
{
    "db_config": {
        "host": "[加密保护]",
        "port": 3306,
        "user": "[加密保护]",
        "password": "[加密保护]",
        "database": "oil"
    },
    "sql_templates": {
        "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1",
        "device_id_fallback_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s LIMIT 1",
        "inventory_query": "SELECT DATE(create_time) as date, oil_remaining FROM oil.t_device_oil_log WHERE device_id = %s AND create_time >= %s AND create_time <= %s ORDER BY create_time",
        "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
        "refueling_query": "SELECT create_time, oil_name, oil_quantity, unit_price, total_price FROM oil.t_oil_refueling_log WHERE device_id = %s AND create_time >= %s AND create_time <= %s ORDER BY create_time"
    }
}
```