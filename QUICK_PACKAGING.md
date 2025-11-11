# 快速打包操作指南

## 🚀 最常用命令

### 1. 构建Windows冻结版本 (推荐)
```bash
python build_package.py frozen
```
输出: `zr_daily_report_v1.0.0.zip`  
用途: 分发给Windows用户  
时间: 2-3分钟

### 2. 构建标准Python包 (用于PyPI)
```bash
python -m build
```
输出: `dist/zr_daily_report-1.0.0-py3-none-any.whl` + `.tar.gz`  
用途: 发布到PyPI  
时间: 30秒

### 3. 本地安装 (开发使用)
```bash
pip install -e .[dev,test,docs]
```
用途: 安装所有开发依赖  
时间: 1-2分钟

---

## 📦 完整打包流程

### 流程A: 发布Windows用户版本

```bash
# 1. 确认在正确分支
git checkout development-copy
git pull origin development-copy

# 2. 验证测试通过
python -m pytest tests/ -v

# 3. 构建冻结版本
python build_package.py frozen

# 4. 验证输出
ls -la zr_daily_report_v*.zip

# 5. 分发或备份
# 将 zr_daily_report_v1.0.0.zip 保存到安全位置
```

**预期输出**:
```
zr_daily_report_v1.0.0.zip  (~15-20MB)
```

### 流程B: 发布PyPI版本

```bash
# 1. 准备版本
git checkout development-copy
git pull origin development-copy

# 2. 更新版本号
vim pyproject.toml
# 修改 version = "1.0.0" 为 version = "1.1.0"

# 3. 运行测试
make test

# 4. 构建包
python -m build

# 5. 上传到PyPI (需要token)
twine upload dist/*

# 6. 创建Git标签
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

**预期输出**:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading zr_daily_report-1.1.0-py3-none-any.whl [100%]
Uploading zr_daily_report-1.1.0.tar.gz [100%]
View at:
https://pypi.org/project/zr-daily-report/1.1.0/
```

---

## 🔍 验证打包结果

### 验证Windows冻结版本
```bash
# 1. 检查ZIP文件完整性
unzip -t zr_daily_report_v1.0.0.zip

# 2. 检查文件结构
unzip -l zr_daily_report_v1.0.0.zip | head -20
```

**应包含的文件**:
```
install_report.bat
run_report.bat
README.txt
requirements.txt
zr_daily_report/
├── src/
├── config/
├── template/
├── zr_daily_report.py
└── pyproject.toml
```

### 验证PyPI包
```bash
# 1. 解压检查
tar -tzf dist/zr_daily_report-1.0.0.tar.gz | head -20

# 2. 检查wheel文件
unzip -l dist/zr_daily_report-1.0.0-py3-none-any.whl | head -20

# 3. 本地安装测试
pip install dist/zr_daily_report-1.0.0-py3-none-any.whl
zr-report --help  # 测试命令行工具
```

---

## 📝 清理和重置

### 清理构建产物
```bash
make clean
```

清理内容:
- `build/` 目录
- `dist/` 目录
- `*.egg-info/` 目录
- `__pycache__/` 目录
- `.pytest_cache/` 目录
- `.mypy_cache/` 目录
- `*.pyc` 文件

### 重新初始化frozen_dist
```bash
# 完全删除frozen_dist
rm -rf frozen_dist/

# 重新生成
python build_package.py frozen
```

### 清理虚拟环境
```bash
# 删除venv
rm -rf .venv/ venv/

# 重建虚拈环境
python -m venv .venv
source .venv/bin/activate  # 或 .venv\Scripts\activate (Windows)
pip install -e .[dev,test,docs]
```

---

## 🐛 常见问题排查

### 问题1: build_package.py找不到Python
```bash
# 解决方案
python --version  # 确认Python可用
python -m build_package frozen  # 用-m调用
```

### 问题2: ZIP文件损坏
```bash
# 验证
unzip -t zr_daily_report_v1.0.0.zip

# 重新生成
rm -rf frozen_dist/
python build_package.py frozen
```

### 问题3: 虚拟环境创建失败
```bash
# 原因: 磁盘空间不足或权限问题
# 解决:
1. 检查磁盘空间: df -h (Linux) 或 dir C:\ (Windows)
2. 检查权限: ls -ld . (Linux) 或 attrib . (Windows)
3. 使用--system-site-packages: python -m venv .venv --system-site-packages
```

### 问题4: 依赖安装失败
```bash
# 原因: 网络或镜像源问题
# 解决: 修改install_report.bat中的镜像源

# 修改前:
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 改为:
pip install -r requirements.txt -i https://pypi.org/simple/  # 官方源
# 或
pip install -r requirements.txt -i https://mirrors.tsinghua.edu.cn/pypi/web  # 清华源
```

---

## 📊 版本对应关系

### 当前状态
```
Git分支: development-copy
Git标签: v0.9
距离标签: 11个提交
版本描述: v0.9-11-g75a0085

pyproject.toml版本: 1.0.0
```

### 版本更新规则
```
major.minor.patch

例如: 1.2.3
      ↑ ↑ ↑
      │ │ └─ patch (修复bug) → 1.2.4
      │ └─── minor (新功能) → 1.3.0
      └───── major (破坏性改变) → 2.0.0
```

### 更新版本的步骤
```bash
# 1. 编辑pyproject.toml
vim pyproject.toml
# 版本号修改为 X.X.X

# 2. 测试
make test

# 3. 提交
git add pyproject.toml
git commit -m "Release version X.X.X"

# 4. 创建标签
git tag -a vX.X.X -m "Release version X.X.X"

# 5. 推送
git push origin development-copy
git push origin vX.X.X

# 6. 打包
python build_package.py frozen
```

---

## 🔐 安全检查清单

打包前检查:

- [ ] 没有提交敏感信息 (密码、密钥等)
- [ ] config/query_config.json 在 .gitignore 中
- [ ] .env 文件不在版本控制中
- [ ] 所有测试通过
- [ ] 代码质量检查通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] 依赖列表已同步

---

## 📞 支持

如需帮助，请参考:
- 详细文档: `PACKAGING_GUIDE.md`
- CI/CD配置: `.github/workflows/ci-cd.yml`
- 构建脚本: `build_package.py`
- 项目主页: https://github.com/ChrisGanbare/Daily_Report

---

**最后更新**: 2025-11-11  
**当前版本**: development-copy (v0.9-11-g75a0085)

