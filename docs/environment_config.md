# 环境配置指南

## 概述

本文档记录了ZR Daily Report项目已知可以正常工作的环境配置，以及不同运行环境下的依赖配置建议。

## 已验证的环境配置

### 推荐配置（已验证可以正常工作）

| 组件 | 版本 | 备注 |
|------|------|------|
| Python | 3.8 - 3.11 | 推荐使用3.9或3.10 |
| 操作系统 | Windows 10/11, Ubuntu 20.04+, CentOS 7+ | Windows 7+也支持 |
| MySQL | 5.7, 8.0 | 推荐8.0 |
| mysql-connector-python | 8.0.33 | 避免使用9.0+版本 |
| PyMySQL | 1.0.0+ | 作为备选驱动 |

### 数据库驱动选择策略

项目支持两种MySQL数据库驱动：
1. **mysql-connector-python**（优先）- 官方驱动
2. **PyMySQL**（备选）- 纯Python实现，兼容性更好

驱动选择逻辑：
- 程序启动时会优先尝试导入mysql-connector-python
- 如果导入失败，则自动切换到PyMySQL
- 这种双重支持机制可以提高程序在不同环境下的兼容性

## 环境配置建议

### Windows环境

```
# 推荐使用虚拟环境
python -m venv .venv
# 激活虚拟环境
.venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### Linux/macOS环境

```bash
# 推荐使用虚拟环境
python3 -m venv .venv
# 激活虚拟环境
source .venv/bin/activate
# 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 常见问题及解决方案

### 内存访问冲突错误（0xC0000005）

**问题描述**：在Windows环境下运行程序时出现内存访问冲突错误。

**根本原因**：mysql-connector-python 9.0+版本与当前环境存在兼容性问题。

**解决方案**：
1. 项目已实现双驱动支持，自动切换到PyMySQL
2. 在requirements.txt中限制mysql-connector-python版本<9.0.0
3. 确保环境中安装了PyMySQL作为备选驱动

### 数据库连接失败

**问题描述**：无法连接到数据库。

**可能原因及解决方案**：
1. 检查网络连接和防火墙设置
2. 验证数据库配置信息（host, port, user, password, database）
3. 确认数据库服务正在运行
4. 检查用户权限设置

## 依赖版本管理

### 版本更新策略

1. 定期检查依赖项的安全更新
2. 在测试环境中验证新版本的兼容性
3. 更新前备份当前的依赖配置
4. 记录版本变更的原因和影响

### 关键依赖版本说明

| 依赖 | 当前版本 | 版本策略 | 说明 |
|------|----------|----------|------|
| mysql-connector-python | 8.0.33 | 固定版本 | 避免内存访问冲突问题 |
| PyMySQL | >=1.0.0 | 最小版本 | 备选数据库驱动 |
| openpyxl | 3.1.0 | 固定版本 | Excel处理库 |
| pandas | >=1.5.0 | 最小版本 | 数据处理库 |

## 环境维护建议

1. 定期更新依赖项到安全版本
2. 在不同环境中测试程序运行情况
3. 记录环境变更和问题解决过程
4. 保持文档与实际配置同步