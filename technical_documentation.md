# ZR Daily Report 技术文档

## 1. 项目概述
ZR Daily Report 是一个专门用于生成切削液设备日常库存报告的Python应用程序。主要功能包括数据库查询、Excel报表生成和图表可视化。

## 2. 技术栈
- Python >= 3.8
- openpyxl >= 3.1.0（Excel文件处理）
- mysql-connector-python >= 8.0.26（数据库连接）
- datetime（日期处理）
- pandas（数据处理）

## 3. 文件结构

```
Daily_Report/ 
├── ZR_Daily_Report.py          # 主程序 
├── db_handler.py               # 数据库处理模块
├── excel_handler.py            # Excel处理模块
├── config_handler.py           # 配置处理模块
├── file_handler.py             # 文件处理模块
├── data_validator.py           # 数据验证模块
├── statement_handler.py        # 对账单处理模块
├── date_utils.py               # 日期处理工具 
├── devices_template.csv        # 设备信息模板 
├── query_config.json           # 数据库配置 
├── technical_documentation.md  # 技术文档 
├── test_zr_daily_report.py     # 主测试用例 
├── test_statement_handler.py   # 对账单处理模块测试用例 
└── test_output/                # 测试输出目录 
  ├── test_无效数据测试.xlsx 
  ├── test_多设备测试.xlsx 
  ├── test_单设备测试.xlsx 
  └── test_对账单测试.xlsx 
```

## 4. 核心模块说明
```

```

