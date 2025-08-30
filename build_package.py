#!/usr/bin/env python3
"""
项目打包脚本，用于创建可移植的完整包，可以在其他电脑上直接运行
"""

import os
import sys
import shutil
import zipfile
import logging
import time
from pathlib import Path
import subprocess

# 根据操作系统设置合适的编码
if sys.platform.startswith('win'):
    # Windows系统使用UTF-8或者mbcs编码
    DEFAULT_ENCODING = 'utf-8'  # 或者使用 'mbcs' 以适配Windows默认编码
else:
    DEFAULT_ENCODING = 'utf-8'

# 配置日志记录，确保兼容Windows系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 明确指定stdout
        logging.FileHandler('release/package_build.log', encoding=DEFAULT_ENCODING)
    ]
)


class PackageError(Exception):
    """打包过程中的自定义异常"""
    pass


class PackageBuilder:
    """打包工具类，处理整个打包流程"""

    # 定义核心依赖列表
    CORE_DEPENDENCIES = [
        "openpyxl",
        "mysql-connector-python",
        "cryptography",
        # 其他必要的核心依赖
    ]

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.version = self._get_project_version()
        self.package_name = f"zr_daily_report_v{self.version}"
        self.release_dir = self.project_root / "release"
        self.package_dir = self.release_dir / self.package_name
        self.zip_path = self.release_dir / f"{self.package_name}.zip"

    def _get_project_version(self) -> str:
        """获取项目版本号"""
        try:
            # 尝试从Git标签获取版本号
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True, text=True, cwd=self.project_root,
                timeout=5  # 添加超时限制
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return version[1:] if version.startswith('v') else version
        except (subprocess.SubprocessError, TimeoutError) as e:
            logging.warning(f"从Git获取版本号失败: {e}")

        # 如果无法从Git获取，返回默认版本
        return "1.0.0"

    def _safe_remove(self, path: Path) -> None:
        """安全删除文件或目录，处理Windows文件锁定问题"""
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
        except PermissionError:
            # 在Windows上，如果文件被占用可能需要等待
            time.sleep(0.1)
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
            except Exception as e:
                raise PackageError(f"无法删除 {path}: {e}")
        except Exception as e:
            raise PackageError(f"删除 {path} 失败: {e}")

    def _create_directory_structure(self):
        """创建目录结构"""
        try:
            # 创建必要的目录
            self.release_dir.mkdir(exist_ok=True)
            self.package_dir.mkdir(exist_ok=True)
        except Exception as e:
            raise PackageError(f"创建目录结构失败: {e}")

    def _copy_project_files(self):
        """复制项目文件到构建目录"""
        # 创建项目文件目录
        project_dir = self.package_dir / "zr_daily_report"
        project_dir.mkdir(exist_ok=True)

        # 完整的必需文件和目录列表
        source_items = [
            "zr_daily_report.py",
            "pyproject.toml",
            "setup.py",  # 如果存在
            "README.md",
            "LICENSE",  # 如果存在
            "requirements.txt",  # 依赖配置文件
            "config/",  # 配置文件目录
            "src/",  # 所有源代码
            "template/",  # 模板文件目录
            "data/",  # 数据文件目录（如果存在）
        ]

        # 过滤掉不存在的文件和目录
        for item in source_items:
            source_path = self.project_root / item
            dest_path = project_dir / item

            # 检查源文件/目录是否存在
            if not source_path.exists():
                logging.warning(f"源文件或目录不存在，跳过: {item}")
                continue

            try:
                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            except Exception as e:
                raise PackageError(f"复制文件失败 {source_path} -> {dest_path}: {e}")

    def _create_virtual_environment(self):
        """创建虚拟环境"""
        try:
            # 虚拟环境将在安装时创建，这里不预先创建
            pass
        except Exception as e:
            raise PackageError(f"创建虚拟环境失败: {e}")

    def _install_dependencies(self):
        """安装依赖"""
        # 依赖将在安装脚本中安装，这里不预先安装
        pass

    def _copy_dependencies(self):
        """复制依赖"""
        try:
            # 在项目目录中创建依赖目录
            deps_dir = self.package_dir / "zr_daily_report" / "dependencies"
            deps_dir.mkdir(exist_ok=True)
            
            # 使用pip下载依赖项到dependencies目录
            requirements_path = self.project_root / "requirements.txt"
            if requirements_path.exists():
                try:
                    # 下载依赖项到dependencies目录
                    subprocess.run([
                        sys.executable, "-m", "pip", "download", 
                        "-r", str(requirements_path), 
                        "-d", str(deps_dir)
                    ], check=True, cwd=self.project_root)
                    logging.info("依赖项已下载到dependencies目录")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"下载依赖项失败: {e}")
                    logging.info("依赖项将在安装时下载")
            else:
                logging.warning("未找到requirements.txt文件")
                
        except Exception as e:
            raise PackageError(f"复制依赖失败: {e}")

    def _create_startup_scripts(self):
        """创建启动脚本，确保使用正确的Windows编码"""
        try:
            # 创建Windows批处理脚本
            bat_script = self.package_dir / "run_report.bat"
            with open(bat_script, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write("@echo off\n")
                f.write("chcp 65001 >nul\n")  # 设置代码页为UTF-8
                f.write("echo 设置环境以使用本地依赖...\n")
                f.write("set PYTHONPATH=%~dp0zr_daily_report;%~dp0zr_daily_report\\dependencies;%PYTHONPATH%\n")
                f.write("cd zr_daily_report\n")
                f.write("python zr_daily_report.py\n")
                f.write("pause\n")

            # 创建PowerShell脚本
            ps_script = self.package_dir / "run_report.ps1"
            with open(ps_script, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write("# ZR Daily Report 启动脚本\n")
                f.write(".\\venv\\Scripts\\Activate.ps1\n")
                f.write("Set-Location -Path \"zr_daily_report\"\n")
                f.write("python zr_daily_report.py\n")

            # 创建安装脚本
            install_bat_script = self.package_dir / "install.bat"
            with open(install_bat_script, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write("@echo off\n")
                f.write("chcp 65001 >nul\n")  # 设置代码页为UTF-8
                f.write("echo 创建虚拟环境...\n")
                f.write("python -m venv venv\n")
                f.write("echo 激活虚拟环境...\n")
                f.write("call venv\\Scripts\\activate.bat\n")
                f.write("echo 设置编码环境变量...\n")
                f.write("set PYTHONIOENCODING=utf-8\n")
                f.write("set PYTHONLEGACYWINDOWSFSENCODING=1\n")
                f.write("echo 升级pip...\n")
                f.write("python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/\n")
                f.write("echo 安装本地依赖...\n")
                f.write("pip install zr_daily_report/dependencies/*.whl --force-reinstall || pip install -r zr_daily_report/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/\n")
                f.write("echo 安装完成!\n")
                f.write("pause\n")

            # 创建README.txt文件
            readme_file = self.package_dir / "README.txt"
            with open(readme_file, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write("# ZR Daily Report 可移植包\n\n")
                f.write("这是一个完整的可移植包，包含了运行ZR Daily Report所需的所有文件。\n\n")
                f.write("## 安装步骤\n\n")
                f.write("1. 在目标计算机上确保已安装Python 3.8或更高版本\n")
                f.write("2. 双击运行 `install.bat` 脚本\n")
                f.write("3. 按照提示完成环境安装\n\n")
                f.write("## 运行程序\n\n")
                f.write("安装完成后，可以通过以下方式运行程序：\n")
                f.write("- 双击 `run_report.bat` 运行程序\n")
                f.write("- 或在命令行中执行 `python zr_daily_report.py`\n\n")
                f.write("## 项目结构\n")
                f.write("- `zr_daily_report/` - 项目主目录\n")
                f.write("- `venv/` - 虚拟环境目录（安装后创建）\n")
                f.write("- `install.bat` - 安装脚本\n")
                f.write("- `run_report.bat` - 启动脚本\n")
                f.write("- `run_report.ps1` - PowerShell启动脚本\n\n")
                f.write("## 系统要求\n")
                f.write("- Windows 7/8/10/11\n")
                f.write("- Python 3.8或更高版本\n")
                f.write("- 至少100MB可用磁盘空间\n\n")
                f.write("## 注意事项\n")
                f.write("- 请勿修改目录结构\n")
                f.write("- 如需重新安装，请删除 `venv` 目录并重新运行 `install.bat`\n")

        except Exception as e:
            raise PackageError(f"创建启动脚本失败: {e}")


    def _create_zip_package(self):
        """创建ZIP压缩包"""
        try:
            with zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.package_dir)
                        zipf.write(file_path, arcname)
        except Exception as e:
            raise PackageError(f"创建ZIP包失败: {e}")

    def create_package(self) -> None:
        """创建可移植包的主函数"""
        try:
            logging.info(f"开始创建可移植包: {self.package_name}")

            # 创建必要的目录
            self.release_dir.mkdir(exist_ok=True)

            # 清理旧文件
            for path in [self.package_dir, self.zip_path]:
                if path.exists():
                    self._safe_remove(path)

            # 创建包目录结构
            self._create_directory_structure()

            # 执行打包步骤
            steps = [
                (self._copy_project_files, "复制项目文件"),
                (self._copy_dependencies, "复制依赖"),
                (self._create_startup_scripts, "创建启动脚本"),
                (self._create_zip_package, "创建压缩包")
            ]

            for step_func, step_name in steps:
                try:
                    logging.info(f"正在{step_name}...")
                    step_func()
                except Exception as e:
                    raise PackageError(f"{step_name}失败: {e}")

            # 清理临时文件
            logging.info("清理临时文件...")
            self._safe_remove(self.package_dir)

            logging.info(f"打包完成！可移植包位置: {self.zip_path}")

        except Exception as e:
            logging.error(f"打包过程失败: {e}")
            # 清理未完成的文件
            self._cleanup_on_error()
            raise

    def _cleanup_on_error(self) -> None:
        """错误发生时的清理操作"""
        try:
            if self.package_dir.exists():
                self._safe_remove(self.package_dir)
            if self.zip_path.exists():
                self._safe_remove(self.zip_path)
        except Exception as e:
            logging.error(f"清理临时文件失败: {e}")


def main():
    """主函数"""
    try:
        builder = PackageBuilder()
        builder.create_package()
    except PackageError as e:
        logging.error(f"打包失败: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception("发生未预期的错误")
        sys.exit(1)


if __name__ == "__main__":
    main()
