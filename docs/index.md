# ZR Daily Report 文档

ZR Daily Report 是一个用于生成切削液设备日常库存报告的Python应用程序。

## 快速开始

### 安装步骤
请参考 [README.md](../README.md#安装步骤) 了解如何安装和配置项目。

### 运行程序
```bash
# 生成库存报表和客户对账单（默认模式）
python ZR_Daily_Report.py

# 只生成库存报表
python ZR_Daily_Report.py --mode inventory

# 只生成客户对账单
python ZR_Daily_Report.py --mode statement
```

详细使用说明请参考 [README.md](../README.md#运行程序)。

## 文档目录

- [安装与配置](../README.md#安装步骤) - 项目安装和基本配置
- [使用说明](../README.md#运行程序) - 如何运行程序和使用各项功能
- [技术文档](technical_documentation.md) - 项目架构和技术细节
- [测试指南](TESTING.md) - 如何运行和编写测试
- [缺陷修复记录](defect_fixes/defect_fixes_index.md) - 已知问题和修复记录
- [开发指南](code-quality.md) - 开发环境和代码质量要求

## 功能特性

- 多设备批量数据处理
- 自动化数据库查询
- Excel报表生成（含图表）
- 客户对账单自动生成
- 动态列数调整（适应不同油品数量）
- 配置文件加密存储
- 完整日志记录

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。