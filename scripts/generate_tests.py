#!/usr/bin/env python3
"""
自动测试生成脚本
此脚本可以自动生成单元测试和集成测试用例模板
"""

import os
import sys
import ast
import argparse
from pathlib import Path
from typing import List, Dict, Set

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def get_existing_test_files(test_dir: str) -> Set[str]:
    """
    获取已存在的测试文件名（不包括扩展名）
    
    Args:
        test_dir: 测试目录路径
        
    Returns:
        Set[str]: 已存在的测试文件名集合
    """
    existing_files = set()
    test_path = Path(test_dir)
    
    if test_path.exists():
        for file in test_path.glob("test_*.py"):
            # 移除扩展名，只保留文件名主体部分
            file_stem = file.stem  # 移除 .py 扩展名
            existing_files.add(file_stem)
    
    return existing_files

def get_project_structure() -> Dict[str, List[str]]:
    """
    获取项目结构，返回模块和函数列表
    
    Returns:
        Dict[str, List[str]]: 模块路径和其中的函数名列表
    """
    project_root = Path(__file__).parent.parent / "src"
    modules = {}
    
    for py_file in project_root.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
            
        # 获取模块相对路径
        rel_path = py_file.relative_to(project_root)
        module_name = ".".join(rel_path.with_suffix("").parts)
        
        # 解析Python文件获取函数列表
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
                
            functions = []
            classes = {}
            
            # 查找类定义
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_methods = []
                    for class_node in ast.iter_child_nodes(node):
                        if isinstance(class_node, ast.FunctionDef):
                            # 只包括公共方法（不以下划线开头）
                            if not class_node.name.startswith("_"):
                                class_methods.append(class_node.name)
                    if class_methods:
                        classes[node.name] = class_methods
                
                # 查找模块级别的函数
                elif isinstance(node, ast.FunctionDef):
                    # 只包括公共函数（不以下划线开头）
                    if not node.name.startswith("_"):
                        functions.append(node.name)
            
            modules[module_name] = {
                'functions': functions,
                'classes': classes
            }
        except Exception as e:
            print(f"警告: 无法解析文件 {py_file}: {e}")
    
    return modules

def generate_unit_test_template(module_name: str, module_info: dict) -> str:
    """
    为给定模块生成单元测试模板
    
    Args:
        module_name: 模块名称
        module_info: 模块信息（包含函数和类）
        
    Returns:
        str: 测试文件内容
    """
    # 将模块名转换为导入路径
    import_path = f"src.{module_name}"
    
    # 生成测试类名
    class_name_parts = [part.capitalize() for part in module_name.split(".")]
    test_class_name = f"Test{''.join(class_name_parts)}"
    
    # 构建导入语句
    imports = [f"from {import_path} import "]
    class_imports = []
    function_imports = []
    
    for class_name in module_info['classes'].keys():
        class_imports.append(class_name)
    
    for func_name in module_info['functions']:
        function_imports.append(func_name)
    
    if class_imports:
        imports[0] += ", ".join(class_imports)
        if function_imports:
            imports[0] += ", " + ", ".join(function_imports)
    elif function_imports:
        imports[0] += ", ".join(function_imports)
    else:
        imports[0] += "*"
    
    template = f'''import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

{chr(10).join(imports)}
from tests.base_test import BaseTestCase


class {test_class_name}(BaseTestCase):
    """
    {module_name} 模块的单元测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        # TODO: 初始化测试所需的对象
        
'''

    # 为每个类生成测试方法模板
    for class_name, methods in module_info['classes'].items():
        template += f'''    def test_{class_name.lower()}_initialization(self):
        """
        测试 {class_name} 类的初始化
        """
        # TODO: 实现 {class_name} 类初始化测试
        pass

'''
        
        for method_name in methods:
            template += f'''    def test_{class_name.lower()}_{method_name}(self):
        """
        测试 {class_name}.{method_name} 方法
        """
        # TODO: 实现 {class_name}.{method_name} 方法的测试用例
        pass

'''

    # 为每个函数生成测试方法模板
    for func_name in module_info['functions']:
        template += f'''    def test_{func_name}(self):
        """
        测试 {func_name} 函数
        """
        # TODO: 实现 {func_name} 函数的测试用例
        pass

'''

    template += '''
if __name__ == "__main__":
    unittest.main()
'''
    
    return template

def generate_integration_test_template(modules: Dict[str, dict]) -> str:
    """
    生成集成测试模板
    
    Args:
        modules: 模块字典
        
    Returns:
        str: 集成测试文件内容
    """
    template = '''import os
import sys
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.base_test import BaseTestCase

class TestIntegration(BaseTestCase):
    """
    集成测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        # TODO: 初始化集成测试所需的对象
    
    def tearDown(self):
        """测试后清理"""
        super().tearDown()
        # TODO: 清理集成测试资源
    
'''

    # 为模块间交互生成测试方法模板
    module_names = list(modules.keys())
    for i, module_name in enumerate(module_names):
        import_path = f"src.{module_name}"
        class_name_parts = [part.capitalize() for part in module_name.split(".")]
        test_class_name = f"Test{''.join(class_name_parts)}"
        
        template += f'''    def test_{module_name.replace(".", "_")}_integration(self):
        """
        测试 {module_name} 模块的集成
        """
        # TODO: 实现 {module_name} 模块与其他模块的集成测试
        pass

'''

    template += '''
if __name__ == "__main__":
    unittest.main()
'''
    
    return template

def write_test_files(modules: Dict[str, dict], output_dir: str = "tests"):
    """
    写入测试文件
    
    Args:
        modules: 模块字典
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True)
    
    # 获取已存在的测试文件
    existing_test_files = get_existing_test_files(output_dir)
    
    # 为每个模块生成单元测试文件
    for module_name, module_info in modules.items():
        # 检查是否有需要测试的内容
        has_content = module_info['functions'] or module_info['classes']
        if not has_content:
            continue
            
        # 生成测试文件名
        test_filename = f"test_{'_'.join(module_name.split('.'))}"
        test_filepath = output_path / f"{test_filename}.py"
        
        # 检查是否与现有测试文件冲突
        if test_filename in existing_test_files:
            # 如果冲突，则添加.template后缀
            test_filename = f"test_{'_'.join(module_name.split('.'))}.template"
            test_filepath = output_path / f"{test_filename}.py"
            print(f"检测到同名测试文件，生成模板文件: {test_filename}.py")
        else:
            print(f"生成测试文件: {test_filename}.py")
            
        test_content = generate_unit_test_template(module_name, module_info)
        with open(test_filepath, "w", encoding="utf-8") as f:
            f.write(test_content)
    
    # 生成集成测试文件
    integration_test_filename = "test_integration_generated"
    integration_test_filepath = output_path / f"{integration_test_filename}.py"
    
    # 检查是否与现有测试文件冲突
    if integration_test_filename in existing_test_files:
        integration_test_filename = "test_integration_generated.template"
        integration_test_filepath = output_path / f"{integration_test_filename}.py"
        print(f"检测到同名集成测试文件，生成模板文件: {integration_test_filename}.py")
    else:
        print(f"生成集成测试文件: {integration_test_filename}.py")
        
    integration_content = generate_integration_test_template(modules)
    with open(integration_test_filepath, "w", encoding="utf-8") as f:
        f.write(integration_content)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="自动测试生成脚本")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="tests/generated",
        help="测试文件输出目录 (默认: tests/generated)"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="覆盖已存在的测试文件"
    )
    
    args = parser.parse_args()
    
    print("开始分析项目结构...")
    modules = get_project_structure()
    
    if not modules:
        print("未找到任何模块")
        return
    
    print("发现以下模块:")
    for module_name, module_info in modules.items():
        func_count = len(module_info['functions'])
        class_count = len(module_info['classes'])
        method_count = sum(len(methods) for methods in module_info['classes'].values())
        total_count = func_count + class_count + method_count
        print(f"  - {module_name}: {total_count} 个函数/类/方法")
    
    print(f"\n生成测试文件到目录: {args.output_dir}")
    write_test_files(modules, args.output_dir)
    
    print("\n测试文件生成完成！")
    print("注意：生成的测试文件仅包含模板，需要手动完善测试逻辑。")
    print("如果检测到同名文件，已生成.template.py后缀的模板文件以避免冲突。")

if __name__ == "__main__":
    main()