"""
命令行参数解析模块
"""
import argparse


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的命令行参数
    """
    parser = argparse.ArgumentParser(description='ZR Daily Report Generator')

    parser.add_argument('--mode',
                        choices=['inventory', 'statement', 'refueling', 'daily_consumption', 'monthly_consumption',
                                 'error_summary'],
                        default='inventory',
                        help='选择执行模式: inventory(库存报表), statement(客户对账单), refueling(加注明细), daily_consumption(每日消耗误差), monthly_consumption(每月消耗误差), error_summary(误差汇总报表)')
    return parser.parse_args()


def print_usage():
    """
    打印使用说明
    """
    """
    print("ZR Daily Report Generator 命令行终端使用说明:")
    print("=" * 50)
    print("命令行终端使用方式:")
    print("  命令行终端不带参数运行: 显示图形界面模式选择对话框")
    print("  命令行终端携带参数运行: 直接执行指定模式")
    print()
    print("命令行参数选项:")
    print("  --mode both         同时生成库存报表和客户对账单")
    print("  --mode inventory    只生成库存报表")
    print("  --mode statement    只生成客户对账单")
    print("  --mode refueling    只生成加注明细报表")
    print("  --mode consumption  只生成每日消耗误差报表")
    print()
    print("示例:")
    print("  python zr_daily_report.py (空)   (启动图形界面模式选择)")
    print("  python zr_daily_report.py --mode both")
    print("  python zr_daily_report.py --mode inventory")
    print("  python zr_daily_report.py --mode statement")
    print("  python zr_daily_report.py --mode refueling")
    print("  python zr_daily_report.py --mode consumption")
    print()
    print("=" * 50)
    """
    print("Intelligent Oiltank Data Analysis Terminal 使用说明:")
    print("=" * 50)
    print("报表生成流程:")
    print("  1. 选择报表模式（通过图形界面或命令行参数）")
    print("  2. 选择日期范围（通过日期选择对话框）")
    print("  3. 选择设备（通过设备筛选对话框）")
    print("  4. 选择输出目录")
    print("  5. 系统自动生成报表")
    print()
    print("日期跨度限制:")
    print("  - 每日消耗误差报表：最大62天（2个月）")
    print("  - 每月消耗误差报表：最大365天（12个月）")
    print("  - 库存报表：最大31天（1个月）")
    print("  - 客户对账单：最大31天（1个月）")
    print("  - 加注明细报表：最大1095天（3年）")
    print()
    print("设备桶数配置（仅消耗误差类型报表:")
    print("  - 系统自动从 test_data/device_config.csv 读取设备桶数")
    print("  - 配置文件格式：device_code,barrel_count")
    print("  - 未配置的设备使用默认值1")
    print("  - 配置文件示例：")
    print("    device_code,barrel_count")
    print("    MO24032700700011,2")
    print("    MO24032700700020,3")
    print()