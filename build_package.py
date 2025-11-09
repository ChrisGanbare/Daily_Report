#!/usr/bin/env python3
"""
Package building script for the new Web-based ZR Daily Report
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
import zipfile


class PackageBuilder:
    """
    ZR Daily Report 包构建器 (V2 - Web App)
    负责创建包含冻结依赖的发行版和生成压缩包
    """

    def __init__(self):
        """初始化构建器"""
        self.project_root = Path(__file__).parent.absolute()
        self.dist_dir = self.project_root / "dist"  # 使用标准的 'dist' 目录
        self.version = self._get_version()

    def _get_version(self):
        """获取当前版本号"""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip().lstrip('v')
            return version
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "2.0.0" # Fallback version

    def create_dist(self):
        """创建发行版"""
        print("创建发行版...")

        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir()

        # 复制必要的源码和资源
        self._copy_project_files(self.project_root, self.dist_dir)

        # 创建并写入新的 requirements.txt
        self._create_requirements_txt(self.dist_dir)

        # 创建用户友好的双击安装和运行脚本
        self._create_user_friendly_scripts(self.dist_dir)

        # 创建压缩包
        self._create_zip_package()

        print(f"发行版创建完成: {self.dist_dir}")

    def _copy_project_files(self, project_root, dist_dir):
        """复制项目文件到发行版目录"""
        # 新架构下需要复制的文件和目录
        items_to_copy = [
            "src",
            "config",
            "static",
            "templates",
            "README.md",
        ]

        for item in items_to_copy:
            src_path = project_root / item
            dst_path = dist_dir / item

            if src_path.exists():
                if src_path.is_dir():
                    # 排除不再需要的旧模块
                    if item == "src":
                        shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns(
                            '__pycache__',
                            'ui', # 忽略旧的UI目录
                            'core/db_handler.py', # 忽略旧的DB处理器
                            'utils/config_handler.py' # 忽略旧的配置处理器
                        ))
                    else:
                        shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns('__pycache__'))
                else:
                    shutil.copy2(src_path, dst_path)

    def _create_requirements_txt(self, dist_dir):
        """创建新的 requirements.txt 文件"""
        print("创建新的 requirements.txt...")
        # 从主项目的 requirements.txt 读取核心依赖
        # 这里我们简化为直接写入已知的新依赖
        requirements_content = """
# 核心运行依赖
openpyxl
SQLAlchemy
aiomysql
fastapi
uvicorn
pydantic
python-dotenv
# 添加其他必要的运行依赖
"""
        with open(dist_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content.strip())
        print("requirements.txt 创建完成。")

    def _create_user_friendly_scripts(self, dist_dir):
        """创建用户友好的双击安装和运行脚本"""
        install_bat_content = r"""@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

@echo --------------------------------------------------
@echo         ZR Daily Report (Web版) 安装程序
@echo --------------------------------------------------
@echo.

@echo 正在检查Python环境 (需要 Python 3.8+)...
@python --version >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 未找到Python环境。请先安装Python 3.8或更高版本。
    @echo 下载地址: https://www.python.org/downloads/
    @pause
    @exit /b 1
)

@echo Python环境检查通过。
@echo.

@echo 创建虚拟环境 (venv)...
@python -m venv venv >nul
@if %errorlevel% NEQ 0 (
    @echo 错误: 创建虚拟环境失败。
    @pause
    @exit /b 1
)

@echo 虚拟环境创建成功。
@echo.

@echo 激活虚拟环境并安装依赖包...
@call venv\Scripts\activate.bat
@pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
@if %errorlevel% NEQ 0 (
    @echo 错误: 安装依赖包失败。请检查网络连接。
    @pause
    @exit /b 1
)

@echo 依赖包安装成功。
@echo.

@echo --------------------------------------------------
@echo                     安装完成！
@echo --------------------------------------------------
@echo.
@echo 双击 "run_webreport.bat" 即可运行程序。
@echo.
@pause
"""
        with open(dist_dir / "install_webreport.bat", "w", encoding="utf-8-sig") as f:
            f.write(install_bat_content)

        run_bat_content = r"""@echo off
chcp 65001 >nul
@echo -----------------------------------------
@echo      启动 ZR Daily Report (Web版)
@echo -----------------------------------------
@echo.
@echo 正在启动Web服务，您的浏览器将自动打开应用页面。
@echo 请勿关闭此窗口，关闭此窗口将终止程序。
@echo.

@if not exist "venv\Scripts\python.exe" (
    @echo 错误: 未找到虚拟环境。请先运行 install_webreport.bat 安装程序。
    @pause
    @exit /b 1
)

@rem 直接运行新的主程序入口
@venv\Scripts\python.exe src\main.py

@echo.
@echo 程序已退出。
@pause
"""
        with open(dist_dir / "run_webreport.bat", "w", encoding="utf-8-sig") as f:
            f.write(run_bat_content)

    def _create_zip_package(self):
        """创建发行版的ZIP压缩包"""
        print("创建ZIP压缩包...")
        zip_filename = self.project_root / f"zr_daily_report_web_v{self.version}.zip"
        if zip_filename.exists():
            zip_filename.unlink()

        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.dist_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(self.dist_dir)
                    zipf.write(file_path, arc_path)
        print(f"ZIP压缩包创建完成: {zip_filename}")

    def show_help(self):
        """显示帮助信息"""
        print("""
ZR Daily Report 构建工具 (Web App)

用法:
    python build_package.py dist   # 构建Web应用发行版
    python build_package.py help   # 显示此帮助信息
""")

def main():
    """主函数"""
    builder = PackageBuilder()
    if len(sys.argv) > 1:
        if sys.argv[1] == "dist":
            builder.create_dist()
        else:
            builder.show_help()
    else:
        builder.show_help()

if __name__ == "__main__":
    main()
