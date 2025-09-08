# ZR Daily Report 构建指南

本文档详细介绍了如何使用 [build_package.py](file://D:\Daily_Report\build_package.py) 脚本来构建 ZR Daily Report 项目。

## 构建脚本概述

[build_package.py](file://D:\Daily_Report\build_package.py) 是项目的构建脚本，提供了多种构建选项：
1. 标准发行版构建 - 使用现代Python构建工具构建wheel和源码发行包
2. 冻结依赖发行版构建 - 创建包含所有依赖的完整发行版，包括生成安装脚本
3. 帮助信息显示 - 提供使用说明

## 使用方法

### 1. 标准发行版构建

构建标准的 Python 包发行版（wheel 和源码包）：

```bash
python build_package.py
```

构建产物将位于项目根目录的 `dist/` 目录中。

### 2. 冻结依赖发行版构建

构建包含所有项目文件和冻结依赖的完整发行版：

```bash
python build_package.py frozen
```

此命令会创建一个 `frozen_dist/` 目录，其中包含：
- 所有项目文件
- 通过 `pip freeze` 生成的 [requirements.txt](file://D:\Daily_Report\requirements.txt) 文件
- Windows 批处理安装脚本 (`install.bat`)
- Unix/Linux/macOS 安装脚本 (`install.sh`)

### 3. 显示帮助信息

显示构建脚本的使用帮助：

```bash
python build_package.py help
```

或者：

```bash
python build_package.py -h
```

## 构建过程详解

### 标准发行版构建过程

1. 检查并安装构建工具（如果尚未安装）
2. 清理旧的构建文件（build、dist目录和egg-info文件）
3. 使用 `python -m build` 命令构建发行版
4. 构建产物保存在 `dist/` 目录中

### 冻结依赖发行版构建过程

1. 创建 `frozen_dist/` 目录
2. 复制项目文件到发行版目录
3. 在发行版目录中冻结当前环境的依赖到 [requirements.txt](file://D:\Daily_Report\requirements.txt)
4. 生成跨平台安装脚本（Windows 的 [.bat](file://D:\Daily_Report\scripts\test_compatibility.bat) 文件和 Unix/Linux/macOS 的 `.sh` 文件）

## 安装构建产物

### 标准发行版安装

标准发行版可以通过 pip 安装：

```bash
pip install dist/zr_daily_report-*.whl
```

或者：

```bash
pip install dist/zr_daily_report-*.tar.gz
```

### 冻结依赖发行版安装

进入 `frozen_dist/` 目录，根据操作系统运行相应的安装脚本：

Windows:
```cmd
install.bat
```

Unix/Linux/macOS:
```bash
./install.sh
```

这些脚本会自动创建虚拟环境、安装依赖并安装项目。

## 注意事项

1. 构建前请确保已安装 Python 3.8 或更高版本
2. 构建冻结依赖发行版时，建议在干净的虚拟环境中进行，以确保依赖列表的准确性
3. 构建产物应根据目标环境选择，生产环境推荐使用冻结依赖发行版