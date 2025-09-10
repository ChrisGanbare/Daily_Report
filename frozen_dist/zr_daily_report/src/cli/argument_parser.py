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
    parser.add_argument('--mode', choices=['inventory', 'statement', 'both', 'refueling'], 
                        default='both', help='选择执行模式: inventory(库存报表), statement(客户对账单), both(两者都执行), refueling(加注明细)')
    return parser.parse_args()


def print_usage():
    """
    打印使用说明
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
    print()
    print("示例:")
    print("  python zr_daily_report.py (空)   (启动图形界面模式选择)")
    print("  python zr_daily_report.py --mode both")
    print("  python zr_daily_report.py --mode inventory")
    print("  python zr_daily_report.py --mode statement")
    print("  python zr_daily_report.py --mode refueling")
    print()
    print("=" * 50)
    print("填写设备信息文件要求")
    print("  支持文件格式：csv格式")
    print("  或直接在当前项目获取模板，模板路径：")
    print("  zr_daily_report/test_data/devices_test.csv")
    print("请按照如下示例格式填写设备编码、起止日期信息")
    print("示例:")
    print("  device_code        start_date      end_date")
    print("  MO24032700700019   2025/7/1        2025/7/31")
