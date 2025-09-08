@echo off
chcp 65001 >nul
@echo 运行ZR Daily Report程序...
@echo.

@python zr_daily_report\zr_daily_report.py
@echo.
@echo 程序已退出
@echo.
@echo 按任意键退出当前窗口
@pause >nul
