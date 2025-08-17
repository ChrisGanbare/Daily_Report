# 代码质量保障

## 代码规范

项目遵循PEP 8代码规范，使用以下工具确保代码质量：

1. **flake8**: 代码风格检查工具，用于检查代码是否符合PEP 8规范
2. **black**: 代码格式化工具，确保代码风格一致性
3. **mypy**: 静态类型检查工具，发现潜在的类型错误
4. **isort**: 导入语句排序工具，保持导入语句的一致性

## 代码质量检查

### 使用tox运行检查

```bash
# 运行所有测试环境
tox

# 只运行代码风格检查
tox -e lint

# 只运行类型检查
tox -e typecheck
```

### 使用Makefile运行检查

```bash
# 安装依赖
make install

# 运行所有质量检查（可能修改文件）
make quality

# 运行所有质量检查（只读模式）
make quality-fast

# 分别运行特定检查
make lint
make typecheck
```

### 使用脚本运行检查

```bash
# 运行所有代码质量检查（不修改文件）
python scripts/run_code_quality.py

# 安装代码质量检查工具
python scripts/run_code_quality.py --install
```

## Git Hooks

项目支持Git hooks来在提交前自动运行代码质量检查。可以通过以下方式设置：

```bash
# 运行脚本自动设置Git hooks
python scripts/setup-git-hooks.py
```

设置后，每次提交时会自动运行：
1. 代码格式化 (black 和 isort)
2. 代码风格检查 (flake8)
3. 类型检查 (mypy)

如果任何检查失败，提交将被中止。

## 测试

请参考 [测试指南](TESTING.md) 了解如何编写和运行测试。

## 持续集成

项目使用GitHub Actions进行持续集成。工作流程包括：
1. 在多个Python版本上运行测试
2. 运行代码质量检查
3. 构建Python包