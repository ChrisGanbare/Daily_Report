# ZR Daily Report 启动脚本

# 获取当前脚本所在的目录
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 切换到项目目录
Set-Location "$ProjectDir\zr_daily_report"

# 激活虚拟环境
..\venv\Scripts\Activate.ps1

# 运行主程序
python ZR_Daily_Report.py $args

# 如果程序正常结束也暂停，防止窗口关闭
Read-Host -Prompt "按Enter键退出"
