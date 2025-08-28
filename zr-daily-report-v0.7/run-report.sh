#!/bin/bash
# ZR Daily Report 启动脚本

# 获取当前脚本所在的目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到项目目录
cd "$PROJECT_DIR/zr_daily_report"

# 激活虚拟环境
source "../venv/bin/activate"

# 运行主程序
python ZR_Daily_Report.py "$@"

# 如果程序正常结束也暂停，防止窗口关闭
read -p "按Enter键退出"
