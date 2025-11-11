# 打包操作实战手册

> 本文档包含真实的、可直接执行的打包步骤和命令

---

## 场景1: 为Windows用户构建冻结版本

### 背景
- 当前在 `development-copy` 分支
- 需要发布给不懂Python的Windows用户
- 希望用户只需双击两个批处理文件即可安装和运行

### 详细步骤

#### 第1步: 准备环境
```bash
# 进入项目目录
cd D:\Daily_Report

# 确认在development-copy分支
git branch
# 输出: * development-copy

# 更新本地代码
git pull origin development-copy

# 确认所有测试通过
python -m pytest tests/ -v

# 如果测试失败，修复问题后重新运行
# 不要继续后续步骤！
```

**检查清单**:
- [ ] 在development-copy分支上
- [ ] git pull没有冲突
- [ ] pytest全部通过
- [ ] 没有git status的未提交更改

#### 第2步: 验证配置文件
```bash
# 确认config/query_config.json存在
ls -la config/query_config.json

# 如果不存在，运行:
# python 创建config_file_fix_report.md 中的步骤
```

**预期输出**:
```
-rw-r--r-- 1 user group 1234 Nov 11 12:34 config/query_config.json
```

#### 第3步: 清理旧构建
```bash
# 删除旧的frozen_dist
rm -rf frozen_dist/

# 删除旧的压缩包 (可选)
rm -f zr_daily_report_v*.zip
```

#### 第4步: 执行打包
```bash
# 构建冻结版本
python build_package.py frozen

# 这会输出:
# 创建包含冻结依赖的发行版...
# 创建ZIP压缩包...
# ZIP压缩包创建完成: D:\Daily_Report\zr_daily_report_v1.0.0.zip
```

**预期输出**:
```
创建包含冻结依赖的发行版...
创建ZIP压缩包...
ZIP压缩包创建完成: D:\Daily_Report\zr_daily_report_v1.0.0.zip
```

**时间**: 2-3分钟

#### 第5步: 验证输出
```bash
# 检查ZIP文件是否存在
ls -lh zr_daily_report_v*.zip

# 验证ZIP文件完整性
unzip -t zr_daily_report_v1.0.0.zip

# 预览ZIP内容
unzip -l zr_daily_report_v1.0.0.zip
```

**预期输出** (ls):
```
-rw-r--r-- 1 user group 15.2M Nov 11 12:45 zr_daily_report_v1.0.0.zip
```

**预期输出** (unzip -t):
```
testing: install_report.bat     OK
testing: run_report.bat         OK
testing: README.txt             OK
...
No errors detected in compressed data of zr_daily_report_v1.0.0.zip.
```

#### 第6步: 本地测试 (可选但强烈推荐)

在Windows环境中:
```bash
# 1. 创建临时目录
mkdir %TEMP%\zr_daily_report_test
cd %TEMP%\zr_daily_report_test

# 2. 解压ZIP
"C:\Program Files\7-Zip\7z.exe" x D:\Daily_Report\zr_daily_report_v1.0.0.zip

# 3. 运行安装脚本
install_report.bat

# 4. 等待安装完成 (5-10分钟)
# 脚本会自动创建虚拟环境并安装依赖

# 5. 运行程序
run_report.bat

# 6. 验证程序能否正常启动
```

#### 第7步: 分发

**本地分发** (USB, 邮件, 局域网共享):
```bash
# 复制ZIP文件到分发位置
cp zr_daily_report_v1.0.0.zip /mnt/shared_drive/releases/

# 或上传到云存储
# 用户下载链接: https://example.com/zr_daily_report_v1.0.0.zip
```

**提供给用户的说明**:
```
1. 下载 zr_daily_report_v1.0.0.zip
2. 解压到一个新文件夹
3. 双击 install_report.bat (首次安装)
4. 等待安装完成
5. 双击 run_report.bat 运行程序
```

---

## 场景2: 发布到PyPI (给Python开发者)

### 背景
- 项目已在PyPI上 (https://pypi.org/project/zr-daily-report/)
- 需要发布新版本
- Python开发者可以通过 pip install zr-daily-report 安装

### 详细步骤

#### 第1步: 准备版本号
```bash
# 确认当前版本
cd D:\Daily_Report

cat pyproject.toml | grep version

# 输出: version = "1.0.0"

# 如果需要升级版本，编辑pyproject.toml
# 版本规则:
# - 主版本 (主要功能变更): 1.0.0 → 2.0.0
# - 副版本 (新功能): 1.0.0 → 1.1.0
# - 补丁版 (bug修复): 1.0.0 → 1.0.1

# 例如：升级到1.1.0
vim pyproject.toml
# 修改: version = "1.0.0" → version = "1.1.0"
```

#### 第2步: 运行完整测试
```bash
# 安装完整依赖
pip install -e .[dev,test,docs]

# 运行单元测试
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 代码质量检查
black --check src tests
flake8 src tests --max-complexity=10 --max-line-length=127
mypy src

# 如果任何检查失败，修复后重新运行
```

**检查清单**:
- [ ] pytest全部通过
- [ ] 代码覆盖率≥80%
- [ ] black检查通过
- [ ] flake8无critical错误
- [ ] mypy类型检查通过

#### 第3步: 提交版本更新
```bash
# 查看变更
git status

# 暂存文件
git add pyproject.toml

# 提交
git commit -m "Bump version to 1.1.0"

# 验证提交
git log -1 --oneline
```

**预期输出**:
```
1a2b3c4 Bump version to 1.1.0
```

#### 第4步: 创建Git标签
```bash
# 创建带注解的标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 验证标签
git tag -l -n1 | head -5

# 预期输出:
# v1.1.0          Release version 1.1.0
# v1.0.0          Release version 1.0.0
# ...
```

#### 第5步: 推送到GitHub
```bash
# 推送代码
git push origin development-copy

# 推送标签
git push origin v1.1.0

# 验证
git describe --tags
# 输出: v1.1.0 (如果当前在标签提交上)
```

#### 第6步: 构建包
```bash
# 清理旧构建
rm -rf dist/ build/

# 构建新包
python -m build

# 验证输出
ls -lh dist/
# 预期输出:
# zr_daily_report-1.1.0-py3-none-any.whl
# zr_daily_report-1.1.0.tar.gz
```

#### 第7步: 上传到PyPI

**选项A: 手动上传 (使用Twine)**
```bash
# 安装twine
pip install twine

# 上传 (需要PyPI账户和token)
twine upload dist/*

# 输出:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading zr_daily_report-1.1.0-py3-none-any.whl [100%]
# Uploading zr_daily_report-1.1.0.tar.gz [100%]
# View at:
# https://pypi.org/project/zr-daily-report/1.1.0/
```

**选项B: GitHub Actions自动发布**
```bash
# 只需推送到master分支并创建标签
git push origin master
git push origin v1.1.0

# GitHub Actions会自动:
# 1. 运行所有测试
# 2. 检查代码质量
# 3. 构建包
# 4. 发布到PyPI

# (需要在GitHub Settings中配置PyPI API Token)
```

#### 第8步: 验证发布
```bash
# 在新的虚拟环境中测试
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 从PyPI安装
pip install zr-daily-report==1.1.0

# 验证包内容
python -c "import zr_daily_report; print(zr_daily_report.__version__)"

# 访问PyPI验证
# https://pypi.org/project/zr-daily-report/1.1.0/
```

---

## 场景3: 持续集成 (GitHub Actions自动打包)

### 背景
- CI/CD流程已在 `.github/workflows/ci-cd.yml` 中配置
- 代码推送时自动运行测试和构建
- master分支推送时自动发布到PyPI

### 工作流程

#### 事件1: 代码推送到development分支
```bash
# 本地开发
git add .
git commit -m "feat: 添加新功能"
git push origin development

# GitHub Actions自动执行:
# 1. Test (Python 3.8-3.11)
#    - 运行pytest
#    - 上传覆盖率
# 2. Code Quality
#    - Flake8/Black/MyPy检查
#    - 覆盖率门禁 (≥80%)
# 3. Documentation
#    - MkDocs构建
#    - 上传文档制品
# 4. Build
#    - python -m build
#    - 生成wheel和sdist
```

#### 事件2: Pull Request到master分支
```bash
# 相同的测试流程
# 在PR中可看到检查结果

# 检查状态:
# ✓ Test
# ✓ Code Quality
# ✓ Documentation
# ✓ Build
```

#### 事件3: Push到master分支
```bash
# 触发完整流程 + 自动发布
git push origin master

# GitHub Actions自动执行:
# 1-4. 前面所有步骤
# 5. Deploy
#    - 从build任务下载制品
#    - twine上传到PyPI
#    - 需要PYPI_API_TOKEN secret
```

#### 监控构建状态
```bash
# 访问Actions标签
# https://github.com/ChrisGanbare/Daily_Report/actions

# 查看工作流详情
# - 点击最新的工作流运行
# - 查看Test、Code Quality等任务的输出
# - 查看制品下载链接
```

---

## 场景4: 故障排查和恢复

### 问题1: build_package.py失败

**症状**: 运行 `python build_package.py frozen` 出错

**排查步骤**:
```bash
# 1. 检查Python版本
python --version
# 需要 ≥ 3.8

# 2. 检查依赖
pip list | grep -E "setuptools|wheel|build"

# 3. 运行详细模式
python -u build_package.py frozen 2>&1 | tee build.log

# 4. 查看日志
cat build.log

# 5. 常见错误及修复
# 错误1: ModuleNotFoundError: No module named 'build'
pip install build wheel setuptools

# 错误2: Permission denied
# Windows: 以管理员身份运行
# Linux: 检查目录权限 chmod -R 755 .

# 错误3: 磁盘空间不足
# 需要至少500MB可用空间
df -h  # Linux
dir C:\  # Windows
```

### 问题2: ZIP文件损坏

**症状**: 解压失败或文件缺失

**恢复步骤**:
```bash
# 1. 验证ZIP完整性
unzip -t zr_daily_report_v1.0.0.zip

# 2. 如果提示错误，删除并重新生成
rm zr_daily_report_v1.0.0.zip
rm -rf frozen_dist/

# 3. 重新打包
python build_package.py frozen

# 4. 验证新生成的ZIP
unzip -t zr_daily_report_v1.0.0.zip
```

### 问题3: 虚拟环境创建失败

**症状**: install_report.bat运行到"创建虚拟环境"时失败

**用户解决步骤**:
```bash
# 在用户机器上:

# 1. 检查Python环境
python --version

# 2. 确认磁盘空间充足 (最少1GB)
dir C:\ | findstr "Total"

# 3. 手动创建虚拟环境
cd zr_daily_report
python -m venv venv

# 4. 激活虚拈环境
venv\Scripts\activate.bat

# 5. 安装依赖
pip install -r ..\requirements.txt

# 6. 安装程序
pip install .

# 7. 运行
python zr_daily_report.py
```

### 问题4: 依赖安装失败

**症状**: pip install 提示网络错误或包不可用

**修复步骤**:
```bash
# 编辑 install_report.bat
# 找到这一行:
# pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 改为其他镜像源:
# 官方源: https://pypi.org/simple/
# 清华源: https://mirrors.tsinghua.edu.cn/pypi/web
# 中科大源: https://mirrors.ustc.edu.cn/pypi/web

# 或者手动安装
pip install openpyxl==3.1.0
pip install mysql-connector-python==8.0.33
```

---

## 场景5: 版本管理和发布策略

### 定期发布周期
```
周期: 每月发布一次 (或功能完成时)

步骤:
1. 在development-copy分支上完成功能
2. 月末: 更新pyproject.toml版本号
3. 提交并push (触发CI/CD)
4. 创建Git标签
5. push标签到GitHub
6. GitHub Actions自动发布到PyPI
7. 生成Windows冻结版本分发
```

### 版本号规划
```
当前: 1.0.0

2025年发布计划:
- 2025-11: 1.1.0 (消耗误差报表完善)
- 2025-12: 1.2.0 (UI改进)
- 2026-01: 2.0.0 (重大重构)

规则:
- 大版本 (主功能变更): X.0.0
- 小版本 (新功能): 1.X.0
- 补丁版 (bug修复): 1.0.X
```

### 发布检查清单
```bash
发布前:
☐ 所有测试通过 (pytest -v)
☐ 代码覆盖率 ≥ 80%
☐ 代码质量检查通过
☐ 文档已更新
☐ CHANGELOG已更新
☐ 版本号已更新
☐ Git标签已创建

发布后:
☐ PyPI上显示新版本
☐ GitHub releases已更新
☐ 冻结版本已上传到分发位置
☐ 用户已通知
☐ 文档已发布
```

---

## 快速参考卡片

### 最常用命令速查

```bash
# 查看当前版本
git describe --tags

# 快速打包Windows版本
python build_package.py frozen

# 快速打包PyPI版本
python -m build

# 快速测试
pytest tests/ -v --cov=src

# 快速提交
git add . && git commit -m "message" && git push

# 快速标签
git tag -a vX.X.X -m "message" && git push origin vX.X.X
```

### 关键文件位置

```
项目根: D:\Daily_Report\

打包脚本:
- build_package.py          # 冻结版本打包脚本

配置文件:
- pyproject.toml            # 版本号 + 元数据
- requirements.txt          # 完整依赖
- setup.py                  # 安装配置

输出位置:
- frozen_dist/              # 冻结版本目录
- dist/                     # Python包目录
- zr_daily_report_v*.zip    # 最终压缩包

CI/CD配置:
- .github/workflows/ci-cd.yml  # 自动化流程
```

---

**手册版本**: 1.0  
**最后更新**: 2025-11-11  
**维护者**: GitHub Copilot

