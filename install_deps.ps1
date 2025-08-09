# PowerShell 脚本用于安装项目依赖
Write-Host "使用阿里云镜像源安装项目依赖..." -ForegroundColor Green

try {
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if ($LASTEXITCODE -eq 0) {
        Write-Host "依赖安装成功！" -ForegroundColor Green
    } else {
        Write-Host "依赖安装失败，请检查网络连接或手动安装。" -ForegroundColor Red
    }
} catch {
    Write-Host "安装过程中出现错误: $_" -ForegroundColor Red
}

Write-Host "按任意键继续..." -ForegroundColor Yellow
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")