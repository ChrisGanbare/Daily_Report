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
    parser.add_argument('--mode', choices=['inventory', 'statement', 'both'], 
                        default='both', help='选择执行模式: inventory(库存报表), statement(客户对账单), both(两者都执行)')
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
    print("  --mode inventory    只生成库存报表")
    print("  --mode statement    只生成客户对账单")
    print("  --mode both         同时生成库存报表和客户对账单")
    print()
    print("示例:")
    print("  python zr_daily_report.py (空)   (启动图形界面模式选择)")
    print("  python zr_daily_report.py --mode inventory")
    print("  python zr_daily_report.py --mode statement")
    print("  python zr_daily_report.py --mode both")
    print("=" * 50)