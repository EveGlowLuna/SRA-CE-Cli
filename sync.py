#!/usr/bin/env python3
"""
上游同步工具启动器
支持命令行和图形化两种模式
"""

import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--gui', '-g']:
            # 启动图形化版本
            subprocess.run([sys.executable, 'sync_upstream_gui.py'])
        elif sys.argv[1] in ['--cli', '-c']:
            # 启动命令行版本
            subprocess.run([sys.executable, 'sync_upstream.py'])
        elif sys.argv[1] in ['--help', '-h']:
            print("""
StarRailAssistant 上游同步工具

用法:
  python sync.py [选项]

选项:
  -g, --gui     启动图形化界面版本
  -c, --cli     启动命令行版本
  -h, --help    显示此帮助信息

不带参数时会询问选择模式。
            """)
        else:
            print(f"未知选项: {sys.argv[1]}")
            print("使用 --help 查看帮助")
    else:
        # 交互式选择
        print("StarRailAssistant 上游同步工具")
        print("1. 图形化界面 (推荐)")
        print("2. 命令行界面")
        print("0. 退出")
        
        while True:
            choice = input("请选择模式 [1]: ").strip()
            if choice == '' or choice == '1':
                subprocess.run([sys.executable, 'sync_upstream_gui.py'])
                break
            elif choice == '2':
                subprocess.run([sys.executable, 'sync_upstream.py'])
                break
            elif choice == '0':
                break
            else:
                print("无效选择，请重新输入")

if __name__ == '__main__':
    main()