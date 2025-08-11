# ZR Daily Report

ZR Daily Report 是一个用于生成切削液设备日常库存报告的Python应用程序。

## 1. 项目概述

### 项目背景
目标用户: 需要设备库存管理的工业设备管理人员和财务对账人员

### 核心问题
- 需要自动化生成设备库存报告
- 需要可视化库存趋势图表
- 需要自动生成客户对账单
- 需要处理不同油品数量的设备数据

## 2. 系统功能

### 主要功能
- 多设备批量数据处理
- 自动化数据库查询
- Excel报表生成（含图表）
- 客户对账单自动生成
- 动态列数调整（适应不同油品数量）
- 配置文件加密存储
- 完整日志记录

### 关键特性
- 支持加密配置文件
- 支持动态油品处理
- 提供详细的缺陷修复记录

## 3. 技术架构

### 技术选型
- 语言: Python 3.8+
- Excel处理: openpyxl 3.1.0+
- 数据库连接: mysql-connector-python 8.0.26+
- 数据处理: pandas 1.5.0+
- 测试框架: pytest 7.0.0+
- 代码规范: flake8 5.0.0+, black 22.0.0+
- 类型检查: mypy 0.971+

### 目录结构
```
.
├── config/                 # 配置文件目录
├── data/                   # 数据文件目录
├── defect_fixes/           # 缺陷修复记录目录
├── docs/                   # 文档目录
├── src/                    # 源代码目录
│   ├── core/               # 核心功能模块
│   ├── handlers/           # 处理器模块
│   └── utils/              # 工具模块
├── template/               # 报表模板目录
├── tests/                  # 测试用例目录
├── test_output/            # 测试输出目录
├── .github/workflows/      # GitHub Actions工作流
├── ZR_Daily_Report.py      # 主程序
├── requirements.txt        # 项目依赖
├── Dockerfile              # Docker配置文件
├── docker-compose.yml      # Docker编排文件
└── README.md               # 项目说明文件
```

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

## 5. CI/CD 流程

本项目使用GitHub Actions实现CI/CD流程，包括以下步骤：

### 持续集成(CI)
1. 代码推送或创建Pull Request时自动触发
2. 在多个Python版本(3.8, 3.9, 3.10, 3.11)上运行测试
3. 执行代码质量检查(flake8, black)
4. 运行单元测试

### 持续部署(CD)
1. 当代码推送到master分支时自动触发
2. 构建Python包
3. 发布到PyPI(需要配置PYPI_API_TOKEN密钥)

### 本地开发环境
可以使用Docker Compose快速搭建本地开发环境：
```bash
docker-compose up -d
```

## 6. 使用说明

### 程序运行模式
```
# 生成库存报表和客户对账单（默认）
python ZR_Daily_Report.py

# 只生成库存报表
python ZR_Daily_Report.py --mode inventory

# 只生成客户对账单
python ZR_Daily_Report.py --mode statement
```

### 配置文件
1. 创建加密密钥文件 `config/.env`
2. 创建明文配置文件 `config/query_config.json`
3. 运行工具脚本生成加密配置文件 `config/query_config_encrypted.json`

## 7. 测试

运行测试:
```
python -m pytest tests/ -v
```

## 8. 部署

### Docker部署
构建Docker镜像:
```
docker build -t zr-daily-report .
```

运行容器:
```
docker run -d --name zr-report zr-daily-report
```

### Docker Compose部署
```
docker-compose up -d
```

## 9. 贡献

欢迎提交Issue和Pull Request来改进项目。

## 10. 许可证

[待定]
