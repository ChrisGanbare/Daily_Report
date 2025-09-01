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
        "protobuf<=3.20.3",  # mysql-connector-python需要特定版本
        "et-xmlfile",        # openpyxl依赖
        "cffi",              # cryptography依赖
        "pycparser"          # cffi依赖
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

    def _download_and_copy_dependencies(self):
        """下载并复制运行时必需的wheel文件"""
        try:
            # 在项目目录中创建依赖目录（使用绝对路径）
            deps_dir = self.package_dir / "zr_daily_report" / "dependencies"
            deps_dir = deps_dir.resolve()  # 转换为绝对路径
            deps_dir.mkdir(exist_ok=True)
            
            # 使用核心依赖列表
            core_dependencies = self.CORE_DEPENDENCIES
            
            logging.info(f"运行时核心依赖: {core_dependencies}")
            
            # 为每个核心依赖创建临时requirements文件
            temp_requirements = self.project_root / "temp_core_requirements.txt"
            try:
                # 写入核心依赖到临时requirements文件
                with open(temp_requirements, 'w', encoding=DEFAULT_ENCODING) as f:
                    for req in core_dependencies:
                        f.write(req + '\n')
                
                logging.info(f"核心依赖条目: {core_dependencies}")
                try:
                    logging.info("正在下载运行时必需的依赖项的wheel文件...")
                    # 使用pip download命令下载核心依赖的wheel文件到dependencies目录
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "download",
                        "-r", str(temp_requirements),
                        "-d", str(deps_dir),
                        "--prefer-binary",
                        "--disable-pip-version-check"
                    ], check=True, capture_output=True, text=True, timeout=300)
                    logging.info("运行时必需的依赖项的wheel文件已下载到dependencies目录")
                    logging.debug(f"pip download output: {result.stdout}")
                    
                    # 验证下载的文件
                    wheel_files = list(deps_dir.glob("*.whl"))
                    tar_files = list(deps_dir.glob("*.tar.gz"))
                    logging.info(f"下载了 {len(wheel_files)} 个wheel文件和 {len(tar_files)} 个源码包")
                    
                    if len(wheel_files) + len(tar_files) == 0:
                        logging.warning("未下载到任何依赖文件")
                        raise PackageError("未能下载依赖文件")
                        
                except subprocess.TimeoutExpired:
                    logging.error("下载依赖超时")
                    raise PackageError("下载依赖超时")
                except subprocess.CalledProcessError as e:
                    logging.error(f"下载依赖项失败: {e}")
                    logging.error(f"错误输出: {e.stderr}")
                    raise PackageError(f"下载依赖失败: {e}")
                except Exception as e:
                    logging.error(f"处理依赖过程中发生错误: {e}")
                    raise PackageError(f"处理依赖失败: {e}")
                    
            finally:
                # 删除临时requirements文件
                if temp_requirements.exists():
                    temp_requirements.unlink()
                
        except Exception as e:
            raise PackageError(f"下载并复制依赖失败: {e}")

    def _create_startup_scripts(self):
        """创建启动脚本，确保使用正确的Windows编码"""
        try:
            # 创建Windows批处理脚本
            bat_script = self.package_dir / "run_report.bat"
            with open(bat_script, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write('@echo off\n')
                f.write('chcp 65001 >nul\n')
                f.write('setlocal\n')
                f.write('title ZR Daily Report\n\n')

                # 设置Python路径
                f.write('set "PYTHONPATH=%~dp0zr_daily_report;%~dp0zr_daily_report\\dependencies;%PYTHONPATH%"\n')
                f.write('cd /d "%~dp0zr_daily_report"\n\n')

                # 先激活虚拟环境
                f.write('if exist "%~dp0venv\\Scripts\\activate.bat" (\n')
                f.write('    call "%~dp0venv\\Scripts\\activate.bat"\n')
                f.write(') else (\n')
                f.write('    echo Error: Virtual environment not found!\n')
                f.write('    echo Please run install.bat first.\n')
                f.write('    pause\n')
                f.write('    exit /b 1\n')
                f.write(')\n\n')

                # 检查依赖
                f.write('python -c "import mysql.connector" >nul 2>&1\n')
                f.write('if errorlevel 1 (\n')
                f.write('    echo Error: MySQL Connector not found!\n')
                f.write('    echo Please run install.bat to install dependencies.\n')
                f.write('    pause\n')
                f.write('    exit /b 1\n')
                f.write(')\n\n')

                # 运行主程序
                f.write('echo Starting ZR Daily Report...\n')
                f.write('echo =====================================\n')
                f.write('python zr_daily_report.py\n')
                f.write('echo =====================================\n')
                f.write('echo.\n')
                f.write('echo Program execution completed.\n')
                f.write('echo Please review the output above.\n')
                f.write('echo Press any key to close this window...\n')
                f.write('pause >nul\n')
                f.write('endlocal\n')

            # 创建PowerShell脚本
            ps_script = self.package_dir / "run_report.ps1"
            with open(ps_script, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write("# ZR Daily Report 启动脚本\n")
                f.write(".\\venv\\Scripts\\Activate.ps1\n")
                f.write("Set-Location -Path \"zr_daily_report\"\n")
                f.write("python zr_daily_report.py\n")

            # 优化安装脚本的输出格式
            install_bat_script = self.package_dir / "install.bat"
            with open(install_bat_script, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write('@echo off\n')
                f.write('chcp 65001 >nul\n')  # 确保使用UTF-8编码
                f.write('title ZR Daily Report Installation\n\n')  # 使用英文标题
                
                # 使用 echo 创建分隔线的函数
                f.write('set "line=echo ====================================="\n')
                f.write('cls\n')
                f.write('%line%\n')
                f.write('echo    ZR Daily Report Environment Setup\n')
                f.write('%line%\n')
                f.write('echo.\n\n')
                
                # 1. 虚拟环境设置
                f.write('echo [1/4] Configuring Virtual Environment\n')
                f.write('%line%\n')
                f.write('echo Creating virtual environment...\n')
                f.write('python -m venv venv\n')
                f.write('if errorlevel 1 goto error\n\n')
                
                f.write('echo Activating virtual environment...\n')
                f.write('call venv\\Scripts\\activate.bat\n')
                f.write('if errorlevel 1 goto error\n\n')
                
                # 2. 环境变量设置
                f.write('echo [2/4] Setting System Environment\n')
                f.write('%line%\n')
                f.write('echo Setting encoding environment variables...\n')
                f.write('set PYTHONIOENCODING=utf-8\n')
                f.write('set PYTHONLEGACYWINDOWSFSENCODING=1\n\n')
                
                # 3. 升级pip
                f.write('echo [3/4] Updating Package Manager\n')
                f.write('%line%\n')
                f.write('python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ >nul 2>&1\n')
                f.write('if errorlevel 1 goto error\n\n')
                
                # 4. 安装依赖
                f.write('echo [4/4] Installing Project Dependencies\n')
                f.write('%line%\n')
                f.write('echo Checking installed dependencies...\n')
                f.write('python -c "import mysql.connector; import openpyxl; import cryptography" >nul 2>&1\n')
                f.write('if %errorlevel% equ 0 (\n')
                f.write('    echo All dependencies are already installed correctly\n')
                f.write('    goto success\n')
                f.write(')\n\n')
                
                # 本地依赖安装
                f.write('echo Starting dependency installation...\n')
                f.write('dir /b zr_daily_report\\dependencies\\*.whl >nul 2>&1\n')
                f.write('if %errorlevel% equ 0 (\n')
                f.write('    echo * Installing from local wheel packages\n')
                f.write('    for %%f in (zr_daily_report\\dependencies\\*.whl) do (\n')
                f.write('        echo   - Installing: %%~nxf\n')
                f.write('        pip install "%%f" --force-reinstall --disable-pip-version-check --no-warn-script-location >nul 2>&1\n')
                f.write('        if errorlevel 1 goto error\n')
                f.write('    )\n')
                f.write(') else (\n')
                f.write('    echo * Installing from online source\n')
                f.write('    pip install -r zr_daily_report\\requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --disable-pip-version-check >nul 2>&1\n')
                f.write('    if errorlevel 1 goto error\n')
                f.write(')\n\n')
                
                # 成功处理
                f.write(':success\n')
                f.write('%line%\n')
                f.write('echo Installation completed successfully!\n')
                f.write('echo You can now run run_report.bat to start the program\n')
                f.write('echo.\n')
                f.write('goto end\n\n')
                
                # 错误处理
                f.write(':error\n')
                f.write('%line%\n')
                f.write('echo An error occurred during installation!\n')
                f.write('echo Please check the error message above and try again\n')
                f.write('exit /b 1\n\n')
                
                # 结束处理
                f.write(':end\n')
                f.write('echo.\n')
                f.write('echo Press any key to exit...\n')
                f.write('pause >nul\n')

            # 更新README.txt文件内容
            readme_file = self.package_dir / "README.txt"
            with open(readme_file, 'w', encoding=DEFAULT_ENCODING, newline='\r\n') as f:
                f.write("# ZR Daily Report Portable Package\n\n")
                f.write("This is a complete portable package containing all files needed to run ZR Daily Report.\n\n")
                f.write("## Installation Steps\n\n")
                f.write("1. Ensure Python 3.8 or higher is installed on the target computer\n")
                f.write("2. Double-click `install.bat` to run the installation script\n")
                f.write("3. Follow the prompts to complete environment setup\n\n")
                f.write("## Running the Program\n\n")
                f.write("After installation is complete, you can run the program by:\n")
                f.write("- Double-clicking `run_report.bat`\n")
                f.write("- Or executing `python zr_daily_report/zr_daily_report.py` in command line\n\n")
                f.write("## Package Structure\n")
                f.write("- `zr_daily_report/` - Main project directory\n")
                f.write("- `venv/` - Virtual environment directory (created after installation)\n")
                f.write("- `install.bat` - Installation script\n")
                f.write("- `run_report.bat` - Launch script\n\n")
                f.write("## System Requirements\n")
                f.write("- Windows 7/8/10/11\n")
                f.write("- Python 3.8 or higher\n")
                f.write("- At least 100MB of free disk space\n\n")
                f.write("## Notes\n")
                f.write("- Do not modify the directory structure\n")
                f.write("- To reinstall, delete the `venv` directory and run `install.bat` again\n")
                f.write("- If installation issues occur, check network connectivity or firewall settings\n")

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
                (self._download_and_copy_dependencies, "下载并复制依赖"),
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
