#!/usr/bin/env python3
"""
Package building script
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
import zipfile


class PackageBuilder:
    """
    ZR Daily Report 包构建器
    负责创建包含冻结依赖的发行版和生成压缩包
    """

    def __init__(self):
        """初始化构建器"""
        self.project_root = Path(__file__).parent.absolute()
        self.dist_dir = self.project_root / "frozen_dist"
        self.version = self._get_version()

    def _get_version(self):
        """
        获取当前版本号
        """
        try:
            # 尝试获取最新的git标签
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            # 移除可能的'v'前缀
            if version.startswith('v'):
                version = version[1:]
            return version
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 如果无法获取git标签，则从pyproject.toml中读取版本
            return self._get_version_from_pyproject()

    def _get_version_from_pyproject(self):
        """
        从pyproject.toml文件中获取版本号
        """
        pyproject_path = self.project_root / "pyproject.toml"
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("version ="):
                        version = line.split("=")[1].strip().strip('"')
                        return version
        except FileNotFoundError:
            pass
        # 默认版本
        return "1.0.0"

    def create_frozen_dist(self):
        """
        创建包含冻结依赖的发行版
        """
        print("创建包含冻结依赖的发行版...")

        # 删除已存在的发行版目录
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)

        # 创建发行版目录
        self.dist_dir.mkdir()

        # 创建项目源码目录
        source_dir = self.dist_dir / "zr_daily_report"
        source_dir.mkdir()

        # 复制项目文件到源码目录
        self._copy_project_files_flat(self.project_root, source_dir)

        # 冻结依赖
        original_cwd = os.getcwd()
        os.chdir(str(self.dist_dir))
        try:
            self._freeze_dependencies()
        finally:
            os.chdir(original_cwd)

        # 创建用户友好的双击安装和运行脚本（放在根目录）
        self._create_user_friendly_scripts(self.dist_dir)

        # 创建压缩包
        self._create_zip_package()

        print(f"冻结发行版创建完成: {self.dist_dir}")

    def _copy_project_files_flat(self, project_root, source_dir):
        """
        复制项目文件到源码目录，保持扁平化结构
        """
        # 需要复制的文件和目录列表
        items_to_copy = [
            "README.md",
            "pyproject.toml", 
            "setup.py",
            "zr_daily_report.py",
            "config",
            "src",
            "template",
            "test_data"
        ]

        for item in items_to_copy:
            src_path = project_root / item
            dst_path = source_dir / item

            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)

        # 更新pyproject.toml中的入口点配置
        pyproject_path = source_dir / "pyproject.toml"
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 替换入口点配置，使用正确的模块路径
        content = content.replace(
            'zr-report = "zr_daily_report:main"',
            'zr-report = "zr_daily_report:main"'
        )

        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _freeze_dependencies(self):
        """
        创建包含核心依赖的requirements.txt文件
        """
        print("创建核心依赖文件...")
        requirements_content = """openpyxl==3.1.0
mysql-connector-python==8.0.33
python-dateutil>=2.8.2
"""

        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)

        print("核心依赖已写入requirements.txt")
        return True

    def _create_user_friendly_scripts(self, dist_dir):
        """
        创建用户友好的双击安装和运行脚本，放在发行版根目录，确保兼容中文
        """
        # 创建双击安装脚本 (简化版)，添加chcp 65001确保UTF-8编码支持
        install_bat_content = r"""@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

@echo --------------------------------------------------
@echo                ZR Daily Report 安装程序
@echo --------------------------------------------------
@echo.

@echo 正在检查Python环境...
@python --version >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 未找到Python环境,请先安装Python 3.8或更高版本
    @echo.
    @echo 下载地址: https://www.python.org/downloads/
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

REM 检查Python版本
@python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
@if %errorlevel% NEQ 0 (
    @for /f "tokens=*" %%i in ('python --version 2^>nul') do set "PYTHON_VERSION=%%i"
    @echo 错误: Python版本不符合要求,需要Python 3.8或更高版本
    @echo 当前Python版本: !PYTHON_VERSION!
    @echo.
    @echo 下载地址: https://www.python.org/downloads/
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo Python环境检查通过
@echo.

@echo 创建虚拟环境...
@python -m venv venv >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 创建虚拟环境失败
    @echo.
    @echo 可能的原因:
    @echo 1. Python安装不完整
    @echo 2. 磁盘空间不足
    @echo 3. 当前目录没有写入权限
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 虚拟环境创建成功
@echo.

@echo 激活虚拟环境...
@call venv\Scripts\activate.bat >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 激活虚拟环境失败
    @echo.
    @echo 可能的原因:
    @echo 1. 虚拟环境创建不完整
    @echo 2. 脚本文件权限问题
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 虚拟环境激活成功
@echo.

@echo 安装依赖包...
@pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 安装依赖包失败
    @echo.
    @echo 可能的原因:
    @echo 1. 网络连接问题
    @echo 2. 阿里云镜像源暂时不可用
    @echo 3. 依赖包版本不兼容
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 依赖包安装成功
@echo.

@echo 安装ZR Daily Report程序...
@pip install ./zr_daily_report >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 安装程序失败
    @echo.
    @echo 可能的原因:
    @echo 1. 项目文件损坏
    @echo 2. 安装脚本权限问题
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 程序安装成功
@echo.

@echo --------------------------------------------------
@echo                     安装完成！
@echo --------------------------------------------------
@echo.
@echo 双击 "run_report.bat" 运行程序
@echo.
@echo 按任意键退出当前窗口
@pause >nul
"""

        # 使用UTF-8-BOM编码写入批处理文件，确保在Windows上正确显示中文
        with open(dist_dir / "install_report.bat", "w", encoding="utf-8-sig") as f:
            f.write(install_bat_content)

        # 创建双击运行脚本，使用Python直接运行主程序文件
        run_bat_content = r"""@echo off
chcp 65001 >nul
@echo 运行ZR Daily Report程序...
@echo.


@if not exist "venv\Scripts\python.exe" (
    @echo 错误: 未找到虚拟环境，请先运行 install_report.bat 安装程序
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@venv\Scripts\python.exe zr_daily_report\zr_daily_report.py
@echo.
@echo 程序已退出
@echo.
@echo 按任意键退出当前窗口
@pause >nul
"""

        # 使用UTF-8-BOM编码写入批处理文件，确保在Windows上正确显示中文
        with open(dist_dir / "run_report.bat", "w", encoding="utf-8-sig") as f:
            f.write(run_bat_content)

        # 创建README.txt文件
        readme_content = """
ZR Daily Report 使用说明

欢迎使用 ZR Daily Report 程序！

系统要求:
- Windows 7/8/10/11
- Python 3.8 或更高版本 (下载地址: https://www.python.org/downloads/)

安装步骤:
1. 双击运行 "install_report.bat" 安装程序
2. 等待安装完成

运行程序:
1. 双击运行 "run_report.bat" 启动程序
2. 根据提示选择操作模式


注意事项:
- 请勿修改目录结构
- 如需重新安装，请删除 "venv" 目录并重新运行 "install_report.bat"
"""

        with open(dist_dir / "README.txt", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_zip_package(self):
        """
        创建发行版的ZIP压缩包，不包含frozen_dist层级
        """
        print("创建ZIP压缩包...")

        # 使用版本号命名压缩包
        zip_filename = self.project_root / f"zr_daily_report_v{self.version}.zip"

        # 如果压缩包已存在，先删除
        if zip_filename.exists():
            zip_filename.unlink()

        # 创建新的压缩包，直接包含根目录下的文件和目录
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 遍历frozen_dist目录中的所有文件和目录
            for root, dirs, files in os.walk(self.dist_dir):
                for file in files:
                    file_path = Path(root) / file
                    # 计算在zip中的路径，移除frozen_dist层级
                    arc_path = file_path.relative_to(self.dist_dir)
                    zipf.write(file_path, arc_path)

        print(f"ZIP压缩包创建完成: {zip_filename}")

    def show_help(self):
        """
        显示帮助信息
        """
        help_text = """
ZR Daily Report 构建工具

用法:
    python build_package.py frozen       # 构建包含冻结依赖的发行版
    python build_package.py help         # 显示此帮助信息
"""
        print(help_text)

    def cleanup_build(self):
        """清理构建目录"""
        build_dirs = ["build", "dist", "*.egg-info"]
        for pattern in build_dirs:
            # 使用pathlib处理路径匹配
            if "*" in pattern:
                # 处理通配符模式
                for file_path in Path(".").glob(pattern):
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
            else:
                # 处理普通目录/文件
                path = Path(pattern)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()


def main():
    """主函数"""
    builder = PackageBuilder()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "frozen":
            builder.create_frozen_dist()
        elif sys.argv[1] in ["help", "-h", "--help"]:
            builder.show_help()
        else:
            print(f"未知参数: {sys.argv[1]}")
            builder.show_help()
            sys.exit(1)
    else:
        # 默认行为改为显示帮助信息
        builder.show_help()


if __name__ == "__main__":
    main()
