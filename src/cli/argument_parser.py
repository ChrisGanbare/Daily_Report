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
                        choices=['inventory', 'statement', 'both', 'refueling', 'daily_consumption',
                                 'monthly_consumption'],
                        default='both',
                        help='选择执行模式: inventory(库存报表), statement(客户对账单), both(两者都执行), refueling(加注明细), daily_consumption(每日消耗误差), monthly_consumption(每月消耗误差)')
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
    print("生成报表前，请先填写设备信息，填写文件要求")
    print("  1.支持文件格式：csv格式")
    print("  2.设备信息必填项device_code，start_date，end_date")
    print("  3.日期格式需为2025/7/1样式，或2025-7-1样式")
    print("  4.可自己按要求填写设备信息，或在你的软件安装路径获取模板，模板路径：zr_daily_report/test_data/devices_test.csv")
    print("")
    print("请按照如下示例格式填写设备编码、起止日期信息、原液桶数（可选）")
    print("  注意：生成每日消耗误差报表，起止日期范围不能大于2个月；生成每月消耗误差报表，起止日期范围不能大于12个月，不能小于2个月")
    print("  注意：barrel_count(桶数)为选填项，生成每日消耗误差报表或每月消耗误差报表时需要如实填写，不填写将按默认值1计算")
    print("设备信息填写示例:")
    print("  device_code        start_date      end_date         barrel_count")
    print("  MO24032700700011   2025/7/1        2025/7/31        2")
    print("  MO24032700700020   2025-7-1        2025-7-31        (不填)")
    print()