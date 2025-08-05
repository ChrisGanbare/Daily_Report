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
├── ZR_Daily_Report.py # 主程序 
├── date_utils.py # 日期处理工具 
├── devices_template.csv # 设备信息模板 
├── query_config.json # 数据库配置 
├── technical_documentation.md # 技术文档 
├── test_zr_daily_report.py # 测试用例 
└── test_output/ # 测试输出目录 
  ├── test_无效数据测试.xlsx 
  ├── test_空数据测试.xlsx 
  ├── test_缺失数据测试.xlsx 
  └── test_连续数据测试.xlsx
```
## 4. 功能特性
1. 支持多设备批量处理
2. 自动生成库存趋势图表
3. 生成增强版对账单
4. 详细的执行日志
5. 完善的错误处理机制
6. 支持多种日期格式

## 5. 数据库配置

### 5.1 连接信息
- 主机：[加密保护]
- 端口：3306
- 数据库：oil
- 用户：[加密保护]

### 主要查询模板
1. 设备ID查询
2. 库存数据查询
3. 客户信息查询

## 6. 输入要求

### 设备信息文件(CSV)
- 文件编码：UTF-8
- 必需字段：
  - device_no（设备编号）
  - start_date（开始日期）
  - end_date（结束日期）
- 日期格式支持：
  - YYYY-MM-DD
  - YYYY/M/D

## 7. 输出规范

### Excel文件命名
1. 标准格式：`油品名称_设备编码_年月.xlsx`
2. 对账单格式：`客户名称年月对账单.xlsx`

### Excel内容格式
- 字体：Arial/等线
- 数值：保留2位小数
- 日期：YYYY-MM-DD
- 图表：折线图（库存趋势）

## 8. 程序执行流程
1. 读取配置和设备信息
2. 数据库连接与查询
3. 生成Excel报表
4. 保存结果文件

## 9. 错误处理
1. 文件读取错误
2. 数据库连接错误
3. 无效设备信息
4. 日期格式错误
5. 数据查询异常
6. 文件保存错误

## 10. 日志规范
- 格式：程序执行日志_YYYYMMDD_HHMMSS.txt
- 内容分段：
  - 步骤1：配置读取
  - 步骤2：数据库操作
  - 步骤3：报表生成
  - 步骤4：文件保存

## 11. 测试用例
1. 数据验证测试
2. 日期处理测试
3. 图表生成测试
4. 异常处理测试

## 12. 版本历史
| 版本 | 日期 | 更新内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2025-07-14 | 初始版本 | Lingma |
| 1.1 | 2025-08-01 | 数据库功能 | Lingma |
| 1.2 | 2025-08-02 | 测试用例 | Lingma |
| 1.3 | 2025-08-03 | 日期处理优化 | Lingma |
| 1.4 | 2025-08-04 | 图表优化 | Lingma |

## 13. 常见问题
1. 日期格式错误
2. 数据库连接超时
3. 文件权限问题
4. 中文编码问题

## 14. 维护建议
1. 定期备份配置文件
2. 监控数据库连接
3. 检查日志文件大小
4. 更新测试用例

## 15. 部署说明

### 15.1 环境要求
- Python >= 3.8
- pip（Python包管理器）
- Git（版本控制）

### 15.2 安装步骤
1. 克隆代码仓库
```bash
git clone https://github.com/ChrisGanbare/Daily_Report.git
cd Daily_Report
2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate
3. 安装依赖包
pip install -r requirements.txt

### 15.3 配置文件设置
1. 复制配置模板
```bash
cp query_config_template.json query_config.json
2. 修改配置文件 query_config.json 填入实际配置
3. 运行配置加密工具
python encrypt_config.py
4. 确认加密后的配置文件 query_config.json 已正确生成
.env（密钥文件）
query_config_encrypted.json（加密配置）

### 15.4 运行程序
Daily_Report/
├── .env                        # 加密密钥（不要提交到Git）
├── config_encrypt.py          # 配置加密工具
├── query_config.json          # 原始配置（不要提交到Git）
├── query_config_encrypted.json # 加密后的配置
└── query_config_template.json  # 配置模板

## 16使用说明
### 16.1 准备工作
1.准备设备信息文件
使用 devices_template.csv 作为模板
确保UTF-8编码
填写正确的设备编号和日期范围

2.确认配置文件
检查数据库连接配置
验证SQL模板正确性

### 16.2 运行程序
1.激活虚拟环境
.venv\Scripts\activate
2.运行程序
python ZR_Daily_Report.py
3.生成报表
报表生成完成，结果保存在当前目录下。
4.查看日志
日志保存在当前目录下，文件名为程序执行日志_YYYYMMDD_HHMMSS.txt
5.查看错误  
错误信息保存在当前目录下，文件名为程序错误日志_YYYYMMDD_HHMMSS.txt
6.查看测试用例
测试用例保存在当前目录下，文件名为test_output/test_*.xlsx
7.查看版本历史
版本历史保存在当前目录下，文件名为版本历史.md
8.查看常见问题
常见问题保存在当前目录下，文件名为常见问题.md

### 16.3 安全建议
妥善保管 .env 文件
定期更新加密密钥
不要提交敏感信息到版本控制
定期备份配置文件