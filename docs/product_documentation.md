# ZR Daily Report 产品文档

## 1. 项目概述

ZR Daily Report 是一个用于生成切削液设备日常库存报告和客户对账单的Python应用程序。该项目主要服务于工业设备管理领域，特别是针对切削液设备的库存监控和客户对账需求。

## 2. 核心功能

### 2.1 多设备批量数据处理
- 支持从CSV文件批量读取多个设备信息
- 支持设备编码、开始日期、结束日期等关键信息配置
- 支持多种文件编码格式（UTF-8、GBK等）

### 2.2 自动化数据库查询
- 自动连接MySQL数据库
- 支持双数据库驱动（mysql-connector-python和PyMySQL）
- 根据设备编码查询设备ID、客户ID等信息
- 获取设备库存数据

### 2.3 Excel报表生成
- 生成设备库存报表（包含图表）
- 生成客户对账单（基于模板）
- 支持动态列数调整，适应不同油品数量
- 支持多种日期格式解析

### 2.4 配置文件加密存储
- 支持加密配置文件存储数据库连接信息
- 使用cryptography库进行配置文件加密
- 支持明文配置文件作为备选方案

### 2.5 完整日志记录
- 详细记录处理过程中的关键步骤
- 记录错误信息和异常情况
- 生成处理日志文件供后续分析

## 3. 业务流程

### 3.1 库存报表生成流程
1. 用户选择设备信息CSV文件
2. 程序读取并验证设备信息
3. 连接数据库并查询设备库存数据
4. 为每个设备生成库存报表Excel文件（包含图表）
5. 保存处理日志

### 3.2 客户对账单生成流程
1. 用户选择设备信息CSV文件
2. 程序读取并验证设备信息
3. 连接数据库并查询所有相关设备库存数据
4. 按客户分组整理数据
5. 基于模板生成客户对账单Excel文件
6. 保存处理日志

### 3.3 数据处理流程
```uml
@startuml
actor User
participant "ZR Daily Report" as App
database MySQL
file "设备信息CSV" as CSV
file "库存报表" as InventoryReport
file "客户对账单" as Statement
file "处理日志" as Log

User -> App: 启动程序
App -> User: 显示模式选择对话框
User -> App: 选择执行模式
App -> CSV: 读取设备信息文件
CSV --> App: 返回设备信息数据
App -> App: 验证设备信息数据
App -> MySQL: 连接数据库
MySQL --> App: 返回数据库连接
loop 每个设备
    App -> MySQL: 查询设备和客户信息
    MySQL --> App: 返回设备ID、客户ID
    App -> MySQL: 查询库存数据
    MySQL --> App: 返回库存数据
    App -> App: 处理库存数据
end
App -> User: 选择输出目录
App -> InventoryReport: 生成库存报表(可选)
App -> Statement: 生成客户对账单(可选)
App -> Log: 生成处理日志
@enduml
```

## 4. 技术架构

### 4.1 核心模块

#### 4.1.1 主程序模块 (ZR_Daily_Report.py)
- 程序入口点
- 协调各模块工作
- 处理命令行参数和用户交互

#### 4.1.2 数据库处理模块 (src/core/db_handler.py)
- 负责数据库连接和数据查询
- 提供设备信息、客户信息和库存数据查询接口
- 支持连接池管理

#### 4.1.3 文件处理模块 (src/core/file_handler.py)
- 读取设备信息CSV文件
- 支持多种编码格式
- 验证数据完整性

#### 4.1.4 库存报表处理模块 (src/core/inventory_handler.py)
- 生成设备库存报表
- 创建库存变化趋势图表
- 支持Excel和CSV格式导出

#### 4.1.5 对账单处理模块 (src/core/statement_handler.py)
- 生成客户对账单
- 基于Excel模板进行数据填充
- 更新图表数据源

#### 4.1.6 配置处理模块 (src/utils/config_handler.py)
- 加载和解密配置文件
- 管理数据库连接配置和SQL模板

#### 4.1.7 数据验证模块 (src/utils/data_validator.py)
- 验证日期格式和逻辑关系
- 验证CSV数据完整性

#### 4.1.8 UI工具模块 (src/utils/ui_utils.py)
- 提供文件和目录选择对话框
- 统一用户界面交互体验

### 4.2 依赖组件
- **openpyxl**: Excel文件处理
- **mysql-connector-python/PyMySQL**: MySQL数据库连接
- **cryptography**: 配置文件加密
- **pandas**: 数据处理（备用）

## 5. 配置说明

### 5.1 环境配置
项目通过`.env`文件存储加密密钥，通过[query_config.json](file://D:/Daily_Report/config/query_config.json)或[query_config_encrypted.json](file://D:/Daily_Report/config/query_config_encrypted.json)存储数据库配置和SQL查询模板。

### 5.2 数据库配置
```json
{
  "db_config": {
    "host": "数据库主机地址",
    "port": 3306,
    "user": "用户名",
    "password": "密码",
    "database": "数据库名"
  }
}
```

### 5.3 SQL模板配置
```json
{
  "sql_templates": {
    "device_id_query": "设备ID查询SQL",
    "device_id_fallback_query": "备用设备ID查询SQL",
    "inventory_query": "库存数据查询SQL",
    "customer_query": "客户信息查询SQL"
  }
}
```

### 5.4 查询模板参数说明
- `device_id_query`: 根据设备编码查询设备ID和客户ID
- `device_id_fallback_query`: 备用设备ID查询SQL（当主查询失败时使用）
- `inventory_query`: 根据设备ID和日期范围查询库存数据
- `customer_query`: 根据客户ID查询客户名称

### 5.5 库存查询模板占位符
- `{device_id}`: 设备ID
- `{start_date}`: 开始日期
- `{end_condition}`: 结束日期条件

## 6. 使用说明

### 6.1 基本用法
```bash
# 生成库存报表和客户对账单（默认模式）
python zr_daily_report.py

# 只生成库存报表
python zr_daily_report.py --mode inventory

# 只生成客户对账单
python zr_daily_report.py --mode statement
```

### 6.2 CSV文件格式
设备信息CSV文件应包含以下列：
- `device_code`: 设备编码
- `start_date`: 开始日期（格式：YYYY-MM-DD或YYYY/M/D）
- `end_date`: 结束日期（格式：YYYY-MM-DD或YYYY/M/D）

示例：
```csv
device_code,start_date,end_date
DEV001,2025-08-01,2025-08-31
DEV002,2025/08/01,2025/08/31
```

## 7. 错误处理与日志

程序具有完善的错误处理机制：
- 数据库连接失败处理
- 文件读取错误处理
- 数据验证失败处理
- 详细错误日志记录

所有处理过程都会生成日志文件，便于问题排查和审计。

## 8. 扩展性设计

项目采用模块化设计，易于扩展：
- 各功能模块职责清晰，遵循单一职责原则
- 通过接口抽象实现松耦合
- 支持配置化管理，便于适应不同环境