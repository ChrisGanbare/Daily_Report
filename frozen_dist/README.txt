
ZR Daily Report 使用说明

欢迎使用 ZR Daily Report 程序！

系统要求:
- Windows 7/8/10/11
- Python 3.8 或更高版本 (下载地址: https://www.python.org/downloads/)

安装步骤:
1. 双击运行 "install_report.bat" 安装程序
2. 等待安装完成

运行程序:
1. 双击运行 "run_report.bat" 启动程序
2. 根据提示选择操作模式

配置文件设置:
安装完成后，配置文件位于 zr_daily_report/config 目录中:
1. 复制 "zr_daily_report/config/.env.example" 文件并重命名为 ".env"
2. 编辑 ".env" 文件，配置数据库连接信息
3. 复制 "zr_daily_report/config/query_config.json.example" 文件并重命名为 "query_config.json"
4. 根据实际需求修改查询语句

注意事项:
- 请勿修改目录结构
- 如需重新安装，请删除 "venv" 目录并重新运行 "install_report.bat"
