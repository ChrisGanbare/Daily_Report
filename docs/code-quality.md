# 代码质量保障体系

本文档详细说明了项目中使用的代码质量保障工具和流程。

## 工具链组成

项目使用以下工具来确保代码质量：

1. **Black**: 代码格式化工具，确保代码风格一致性
2. **isort**: 导入语句排序工具，保持导入语句的一致性
3. **flake8**: 代码风格检查工具，用于检查代码是否符合PEP 8规范
4. **mypy**: 静态类型检查工具，发现潜在的类型错误
5. **pre-commit**: Git钩子管理工具，用于在提交前自动运行检查

## 本地开发流程

### 安装依赖

```bash
pip install -r requirements.txt
```

### 手动运行检查

在提交代码前，建议手动运行所有检查：

```bash
# 使用tox运行所有检查
tox -e lint,typecheck

# 或使用Makefile
make quality-fast

# 或单独运行每个工具
black --check src tests
isort --check-only src tests
flake8 src tests
mypy src tests
```

### 自动运行检查

项目支持两种方式在提交前自动运行检查：

#### 方法1: 使用自定义Git Hooks

运行以下脚本设置Git hooks：

```bash
python scripts/setup-git-hooks.py
```

#### 方法2: 使用pre-commit框架

安装pre-commit：

```bash
pre-commit install
```

之后每次提交时会自动运行所有检查。

## 持续集成 (CI) 流程

GitHub Actions会在每次推送和创建Pull Request时自动运行以下检查：

1. 在多个Python版本上运行测试
2. 运行所有代码质量检查工具
3. 检查代码覆盖率（要求至少80%）
4. 构建Python包

只有所有检查都通过，代码才能合并到主分支。

## 代码质量门禁

项目设置了以下质量门禁：

1. **测试覆盖率**: 必须达到80%以上
2. **代码风格**: 必须通过flake8检查
3. **类型检查**: 必须通过mypy检查
4. **导入排序**: 必须通过isort检查
5. **代码格式**: 必须通过black格式化

## 工具配置

### Black配置

Black使用默认配置，最大行长度为88个字符。

### isort配置

isort配置在[pyproject.toml](../pyproject.toml)文件中：

```toml
[tool.isort]
profile = "black"
```

### flake8配置

flake8配置在[tox.ini](../tox.ini)文件中：

```ini
[testenv:lint]
deps = 
    flake8
commands = 
    flake8 src tests
```

### mypy配置

mypy配置在[tox.ini](../tox.ini)文件中：

```ini
[testenv:typecheck]
deps = 
    mypy
    -r{toxinidir}/requirements.txt
commands = 
    mypy src tests
```

## 最佳实践

1. **定期检查**: 在开发过程中定期运行代码质量检查工具
2. **提交前检查**: 在提交代码前进行完整的代码质量检查
3. **CI/CD集成**: 将这些检查集成到持续集成/持续部署流程中
4. **代码格式一致性**: 使用 black 和 isort 保持代码风格一致性
5. **类型注解**: 为所有函数和变量添加类型注解，帮助mypt发现潜在问题
6. **修复所有问题**: 修复所有 flake8 和 mypy 发现的问题

## 常见问题解决

### 1. 检查失败怎么办？

如果检查失败，请根据错误信息进行修复：

- **flake8错误**: 通常是代码风格问题，根据提示修改
- **mypy错误**: 通常是类型不匹配问题，添加或修正类型注解
- **black错误**: 代码格式不符合规范，运行black自动格式化
- **isort错误**: 导入语句排序不正确，运行isort自动排序

### 2. 如何跳过检查？

在特殊情况下，可以使用以下方式跳过检查：

```bash
# 跳过Git hooks提交
git commit --no-verify -m "提交信息"

# 跳过特定行的flake8检查
# noqa: E501

# 跳过特定行的mypy检查
# type: ignore
```

但强烈建议不要跳过检查，除非有充分的理由。