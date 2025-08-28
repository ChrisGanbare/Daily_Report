# 获取脚本所在的目录（即项目根目录）
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 切换到项目目录
Set-Location -Path $ProjectDir

Write-Host "正在运行 ZR Daily Report 程序..."

# 检查是否存在虚拟环境并激活
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "激活虚拟环境..."
    . ".venv\Scripts\Activate.ps1"
}

# 运行主程序并传递所有参数
$Arguments = $args -join " "
Invoke-Expression "python zr_daily_report.py $Arguments"

# 检查运行结果
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "程序运行出现错误，请查看上面的错误信息。" -ForegroundColor Red
    pause
}