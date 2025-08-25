@echo off
REM ZR Daily Report 启动脚本

REM 获取当前脚本所在的目录
set PROJECT_DIR=%~dp0

REM 切换到项目目录
cd /d "%PROJECT_DIR%zr_daily_report"

REM 激活虚拟环境
call "..\venv\Scripts\activate.bat"

REM 运行主程序
python ZR_Daily_Report.py %*

REM 如果程序正常结束也暂停，防止窗口关闭
pause
