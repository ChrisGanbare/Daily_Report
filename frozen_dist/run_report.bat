@echo off
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
