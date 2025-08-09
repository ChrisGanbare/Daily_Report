@echo off
chcp 65001 >nul
echo 使用阿里云镜像源安装项目依赖...
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% == 0 (
    echo 依赖安装成功！
) else (
    echo 依赖安装失败，请检查网络连接或手动安装。
)
pause