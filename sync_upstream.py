#!/usr/bin/env python3
"""
上游同步工具 - 专为 StarRailAssistant 定制
作者：EveGlowLuna
功能：同步上游更新，自动排除指定目录/文件，支持手动冲突处理
"""

# ============================================================================
# 导入模块
# ============================================================================
import subprocess
import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

# ============================================================================
# 颜色和样式配置
# ============================================================================
try:
    from colorama import init, Fore, Back, Style, just_fix_windows_console
    just_fix_windows_console()
    init(autoreset=True)
    
    class Colors:
        """控制台颜色和样式"""
        HEADER = Fore.MAGENTA + Style.BRIGHT
        TITLE = Fore.CYAN + Style.BRIGHT
        SUCCESS = Fore.GREEN + Style.BRIGHT
        WARNING = Fore.YELLOW + Style.BRIGHT
        ERROR = Fore.RED + Style.BRIGHT
        INFO = Fore.BLUE
        PROMPT = Fore.YELLOW
        
        # Git diff 特定颜色
        DIFF_ADD = Fore.GREEN
        DIFF_DEL = Fore.RED
        DIFF_FILE = Fore.CYAN
        DIFF_HUNK = Fore.YELLOW
        DIFF_META = Fore.BLUE
        
        RESET = Style.RESET_ALL
        
        @staticmethod
        def colorize_diff_line(line: str) -> str:
            """为diff行添加颜色"""
            if line.startswith('diff --git'):
                return Colors.DIFF_FILE + line + Colors.RESET
            elif line.startswith('index'):
                return Colors.DIFF_META + line + Colors.RESET
            elif line.startswith('---'):
                return Colors.DIFF_DEL + line + Colors.RESET
            elif line.startswith('+++'):
                return Colors.DIFF_ADD + line + Colors.RESET
            elif line.startswith('@@'):
                return Colors.DIFF_HUNK + line + Colors.RESET
            elif line.startswith('+'):
                return Colors.DIFF_ADD + line + Colors.RESET
            elif line.startswith('-'):
                return Colors.DIFF_DEL + line + Colors.RESET
            return line
                
except ImportError:
    # 回退到 ANSI 颜色
    class Colors:
        HEADER = "\033[95;1m"
        TITLE = "\033[96;1m"
        SUCCESS = "\033[92;1m"
        WARNING = "\033[93;1m"
        ERROR = "\033[91;1m"
        INFO = "\033[94m"
        PROMPT = "\033[93m"
        
        DIFF_ADD = "\033[32m"
        DIFF_DEL = "\033[31m"
        DIFF_FILE = "\033[36m"
        DIFF_HUNK = "\033[33m"
        DIFF_META = "\033[34m"
        RESET = "\033[0m"
        
        @staticmethod
        def colorize_diff_line(line: str) -> str:
            if line.startswith('diff --git'):
                return Colors.DIFF_FILE + line + Colors.RESET
            elif line.startswith('index'):
                return Colors.DIFF_META + line + Colors.RESET
            elif line.startswith('---'):
                return Colors.DIFF_DEL + line + Colors.RESET
            elif line.startswith('+++'):
                return Colors.DIFF_ADD + line + Colors.RESET
            elif line.startswith('@@'):
                return Colors.DIFF_HUNK + line + Colors.RESET
            elif line.startswith('+'):
                return Colors.DIFF_ADD + line + Colors.RESET
            elif line.startswith('-'):
                return Colors.DIFF_DEL + line + Colors.RESET
            return line

# ============================================================================
# 工具类：上游同步器
# ============================================================================
class UpstreamSync:
    def __init__(self):
        """初始化同步器"""
        self.repo_path = Path.cwd()
        
        # 需要排除的文件和目录模式（使用正则表达式）
        self.excluded_patterns = [
            r'^\.github/',          # GitHub 工作流
            r'^SRAFrontend/',       # 原 C# 前端
            r'^setup/',             # 安装脚本目录
            r'^README\.md$',        # 说明文档
            r'^package\.py$',       # 包配置
            r'^\.gitignore$',       # Git 忽略文件
            r'^\.gitattributes$',   # Git 属性文件
        ]
        
        # 设置合并策略保护排除的文件
        self._setup_merge_protection()
    
    # ========================================================================
    # 核心工具方法
    # ========================================================================
    def run_cmd(self, cmd: str, capture: bool = True, keep_color: bool = False) -> Tuple[str, int]:
        """
        执行 shell 命令
        
        Args:
            cmd: 要执行的命令
            capture: 是否捕获输出
            keep_color: 是否保留颜色代码
            
        Returns:
            (输出内容, 返回码)
        """
        try:
            if capture:
                if keep_color:
                    # 保留颜色输出
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        cwd=self.repo_path
                    )
                    try:
                        output = result.stdout.decode('utf-8', errors='ignore')
                    except:
                        output = result.stdout.decode('gbk', errors='ignore')
                    return output.strip(), result.returncode
                else:
                    # 普通捕获模式
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        cwd=self.repo_path
                    )
                    return result.stdout.strip(), result.returncode
            else:
                # 直接输出到控制台
                result = subprocess.run(cmd, shell=True, cwd=self.repo_path, encoding='utf-8')
                return "", result.returncode
                
        except Exception as e:
            print(f"{Colors.ERROR}❌ 命令执行失败: {cmd}{Colors.RESET}")
            print(f"{Colors.ERROR}   错误: {e}{Colors.RESET}")
            return "", 1
    
    def _setup_merge_protection(self):
        """设置合并保护，确保排除的文件不会被覆盖"""
        try:
            # 创建 .gitattributes 文件（如果不存在）
            gitattributes_path = self.repo_path / ".gitattributes"
            if not gitattributes_path.exists():
                content = "# 合并保护配置\n"
                for pattern in self.excluded_patterns:
                    # 转换正则模式为 Git 路径模式
                    clean_pattern = pattern.strip('^$').replace(r'\.', '.')
                    if clean_pattern.endswith('/'):
                        content += f"{clean_pattern}* merge=ours\n"
                    else:
                        content += f"{clean_pattern} merge=ours\n"
                
                gitattributes_path.write_text(content, encoding='utf-8')
                print(f"{Colors.INFO}📝 已创建合并保护配置{Colors.RESET}")
            
            # 配置合并策略
            self.run_cmd("git config merge.ours.driver true")
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  合并保护设置失败: {e}{Colors.RESET}")
    
    # ========================================================================
    # 同步流程方法
    # ========================================================================
    def fetch_upstream(self) -> bool:
        """获取上游仓库的最新更新"""
        print(f"{Colors.INFO}🔄 正在获取上游更新...{Colors.RESET}")
        output, code = self.run_cmd("git fetch upstream")
        
        if code == 0:
            # 获取最新提交信息
            latest_commit, _ = self.run_cmd("git log -1 --oneline upstream/main")
            if latest_commit:
                print(f"{Colors.SUCCESS}✅ 上游更新获取完成{Colors.RESET}")
                print(f"{Colors.INFO}   最新提交: {latest_commit[:60]}{Colors.RESET}")
            else:
                print(f"{Colors.SUCCESS}✅ 上游更新获取完成{Colors.RESET}")
            return True
        else:
            print(f"{Colors.ERROR}❌ 获取失败，请检查远程配置{Colors.RESET}")
            return False
    
    def get_changed_files(self) -> List[str]:
        """获取需要更新的文件列表（自动排除指定项）"""
        cmd = "git diff --name-only HEAD..upstream/main"
        output, _ = self.run_cmd(cmd)
        
        if not output:
            return []
        
        all_files = [f.strip() for f in output.split('\n') if f.strip()]
        filtered_files = []
        
        for file in all_files:
            # 检查是否匹配排除模式
            exclude = False
            for pattern in self.excluded_patterns:
                if re.match(pattern, file):
                    exclude = True
                    break
            
            if not exclude:
                filtered_files.append(file)
        
        return filtered_files
    
    # ========================================================================
    # 操作选项方法
    # ========================================================================
    def preview_changes(self, files: List[str]):
        """选项1：预览所有变更（带彩色diff输出）"""
        if not files:
            print(f"{Colors.WARNING}⚠️  没有可更新的文件{Colors.RESET}")
            return
        
        print(f"\n{Colors.INFO}📊 共发现 {len(files)} 个可更新文件{Colors.RESET}")
        
        # 按目录分组显示
        groups = {}
        for file in files:
            parts = file.split('/')
            if len(parts) > 1:
                group = parts[0]
            else:
                group = "根目录"
            
            if group not in groups:
                groups[group] = []
            groups[group].append(file)
        
        # 显示文件列表
        for group in sorted(groups.keys()):
            print(f"\n{Colors.TITLE}{group}/{Colors.RESET}")
            for file in sorted(groups[group]):
                print(f"  {Colors.INFO}• {file}{Colors.RESET}")
        
        # 询问是否查看具体变更
        preview = input(f"\n{Colors.PROMPT}🔍 查看具体变更？(y/N): {Colors.RESET}").lower()
        if preview != 'y':
            return
        
        # 逐个文件显示变更
        for idx, file in enumerate(files, 1):
            self._print_section_header(f"文件 {idx}/{len(files)}: {file}")
            
            # 获取并显示diff
            diff_cmd = f"git diff HEAD..upstream/main -- {file}"
            diff_output, _ = self.run_cmd(diff_cmd, keep_color=True)
            
            if diff_output:
                # 如果输出包含颜色代码，直接显示
                if '\033[' in diff_output or '\x1b[' in diff_output:
                    print(diff_output)
                else:
                    # 否则手动添加颜色
                    for line in diff_output.split('\n'):
                        print(Colors.colorize_diff_line(line))
                
                # 统计变更行数
                added = sum(1 for line in diff_output.split('\n') 
                          if line.startswith('+') and not line.startswith('+++'))
                removed = sum(1 for line in diff_output.split('\n') 
                            if line.startswith('-') and not line.startswith('---'))
                
                print(f"\n{Colors.INFO}📈 变更统计: +{added} -{removed}{Colors.RESET}")
            else:
                print(f"{Colors.WARNING}(无文本变更或二进制文件){Colors.RESET}")
            
            # 询问是否继续
            if idx < len(files):
                cont = input(f"\n{Colors.PROMPT}按回车继续下一个文件，或输入 q 退出: {Colors.RESET}").lower()
                if cont == 'q':
                    break
    
    def apply_all_changes(self, files: List[str]):
        """选项2：应用所有更新"""
        if not files:
            print(f"{Colors.WARNING}⚠️  没有可更新的文件{Colors.RESET}")
            return
        
        print(f"\n{Colors.WARNING}⚠️  即将应用 {len(files)} 个文件的更新{Colors.RESET}")
        print(f"{Colors.INFO}将要更新的文件:{Colors.RESET}")
        for file in files:
            print(f"  • {file}")
        
        # 确认操作
        confirm = input(f"\n{Colors.PROMPT}确定要应用所有更新吗？(y/N): {Colors.RESET}").lower()
        if confirm != 'y':
            print(f"{Colors.INFO}操作已取消{Colors.RESET}")
            return
        
        print(f"\n{Colors.INFO}🔄 正在应用更新...{Colors.RESET}")
        
        # 使用合并策略，然后恢复排除的文件
        merge_cmd = "git merge --no-commit --no-ff upstream/main"
        _, code = self.run_cmd(merge_cmd, capture=False)
        
        if code != 0:
            print(f"{Colors.ERROR}❌ 合并失败，可能存在冲突{Colors.RESET}")
            return
        
        # 恢复排除的文件
        for pattern in self.excluded_patterns:
            clean_pattern = pattern.strip('^$').replace(r'\.', '.')
            if clean_pattern.endswith('/'):
                dir_name = clean_pattern.rstrip('/')
                self.run_cmd(f"git checkout HEAD -- {dir_name}", capture=False)
            else:
                self.run_cmd(f"git checkout HEAD -- {clean_pattern}", capture=False)
        
        # 显示状态
        print(f"\n{Colors.SUCCESS}✅ 更新已暂存{Colors.RESET}")
        self.show_status()
        
    def interactive_select(self, files: List[str]):
        """选项3：交互式选择文件更新"""
        if not files:
            print(f"{Colors.WARNING}⚠️  没有可更新的文件{Colors.RESET}")
            return
        
        print(f"\n{Colors.INFO}📁 请选择要更新的文件 (共 {len(files)} 个):{Colors.RESET}")
        
        # 显示文件列表
        file_map = {}
        for i, file in enumerate(files, 1):
            print(f"  [{i:2d}] {file}")
            file_map[str(i)] = file
        
        while True:
            choice = input(f"\n{Colors.PROMPT}输入文件编号 (多个用逗号分隔，a=全选，q=退出): {Colors.RESET}").strip()
            
            if choice.lower() == 'q':
                return
            elif choice.lower() == 'a':
                selected = files
                break
            else:
                selected = []
                valid = True
                for num in choice.split(','):
                    num = num.strip()
                    if num in file_map:
                        selected.append(file_map[num])
                    else:
                        print(f"{Colors.ERROR}❌ 无效编号: {num}{Colors.RESET}")
                        valid = False
                        break
                
                if valid and selected:
                    break
        
        # 应用选择的更新
        print(f"\n{Colors.INFO}🔄 正在应用选中文件...{Colors.RESET}")
        for file in selected:
            print(f"  {Colors.INFO}• {file}{Colors.RESET}")
            cmd = f"git checkout upstream/main -- {file}"
            self.run_cmd(cmd, capture=False)
        
        print(f"\n{Colors.SUCCESS}✅ 已更新 {len(selected)} 个文件{Colors.RESET}")
        self.show_status()
    
    def check_conflicts(self):
        """选项4：检查合并冲突"""
        print(f"\n{Colors.INFO}🔍 正在检查冲突...{Colors.RESET}")
        
        # 检查未解决的冲突
        cmd = "git diff --name-only --diff-filter=U"
        output, _ = self.run_cmd(cmd)
        
        if output:
            conflict_files = [f.strip() for f in output.split('\n') if f.strip()]
            print(f"{Colors.ERROR}⚠️  发现 {len(conflict_files)} 个冲突文件:{Colors.RESET}")
            for file in conflict_files:
                print(f"  {Colors.ERROR}⚡ {file}{Colors.RESET}")
            
            print(f"\n{Colors.WARNING}🛠️  解决步骤:{Colors.RESET}")
            print(f"  1. 查看冲突: {Colors.INFO}git diff{Colors.RESET}")
            print(f"  2. 编辑文件，解决冲突标记 ({Colors.ERROR}<<<<<<<{Colors.RESET}, {Colors.WARNING}======={Colors.RESET}, {Colors.SUCCESS}>>>>>>>{Colors.RESET})")
            print(f"  3. 标记为已解决: {Colors.INFO}git add <文件>{Colors.RESET}")
            print(f"  4. 完成合并: {Colors.INFO}git commit{Colors.RESET}")
            
            # 提供打开编辑器的选项
            open_editor = input(f"\n{Colors.PROMPT}用 VSCode 打开冲突文件？(y/N): {Colors.RESET}").lower()
            if open_editor == 'y':
                for file in conflict_files:
                    if Path(file).exists():
                        subprocess.run(["code", file], cwd=self.repo_path)
        else:
            print(f"{Colors.SUCCESS}✅ 无未解决的冲突{Colors.RESET}")
            
            # 检查是否有未提交的合并
            status_output, _ = self.run_cmd("git status")
            if "All conflicts fixed" in status_output:
                print(f"{Colors.INFO}💡 所有冲突已解决，可以提交合并{Colors.RESET}")
    
    def show_status(self):
        """选项5：显示当前Git状态"""
        print(f"\n{Colors.INFO}📋 当前Git状态:{Colors.RESET}")
        self.run_cmd("git status", capture=False)
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    def _print_section_header(self, text: str):
        """打印区块标题"""
        print(f"\n{Colors.TITLE}{'='*60}{Colors.RESET}")
        print(f"{Colors.TITLE}{text:^60}{Colors.RESET}")
        print(f"{Colors.TITLE}{'='*60}{Colors.RESET}")
    
    def show_summary(self, files: List[str]):
        """显示更新摘要"""
        if not files:
            return
        
        print(f"\n{Colors.INFO}📋 更新摘要:{Colors.RESET}")
        print(f"{Colors.INFO}📁 文件总数: {len(files)}{Colors.RESET}")
        
        # 按扩展名统计
        extensions = {}
        for file in files:
            ext = Path(file).suffix
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
            else:
                extensions["无扩展名"] = extensions.get("无扩展名", 0) + 1
        
        if extensions:
            print(f"{Colors.INFO}📊 文件类型分布:{Colors.RESET}")
            for ext, count in sorted(extensions.items()):
                print(f"  {Colors.INFO}{ext}: {count}{Colors.RESET}")
    
    # ========================================================================
    # 主循环
    # ========================================================================
    def main_loop(self):
        """主循环 - 持续显示菜单直到用户退出"""
        while True:
            # 显示主标题
            self._print_section_header("🔄 上游同步工具")
            
            # 检查远程配置
            remotes, _ = self.run_cmd("git remote -v")
            if "upstream" not in remotes:
                print(f"{Colors.WARNING}⚠️  未配置 upstream 远程{Colors.RESET}")
                setup = input(f"{Colors.PROMPT}是否添加？(Y/n): {Colors.RESET}").lower()
                if setup in ['y', '']:
                    self.run_cmd("git remote add upstream https://github.com/Shasnow/StarRailAssistant.git")
                    print(f"{Colors.SUCCESS}✅ 已添加上游远程{Colors.RESET}")
                else:
                    print(f"{Colors.ERROR}请手动运行: git remote add upstream <url>{Colors.RESET}")
                    continue
            
            # 获取更新
            if not self.fetch_upstream():
                print(f"{Colors.ERROR}❌ 无法继续，请检查网络或权限{Colors.RESET}")
                break
            
            # 获取可更新文件列表
            files = self.get_changed_files()
            
            if not files:
                print(f"\n{Colors.SUCCESS}✅ 已经是最新，无需同步{Colors.RESET}")
                print(f"{Colors.INFO}排除的文件: {', '.join([p.strip('^$').replace(r'\.', '.') for p in self.excluded_patterns])}{Colors.RESET}")
            else:
                self.show_summary(files)
            
            # 显示主菜单
            print(f"\n{Colors.TITLE}🛠️  请选择操作:{Colors.RESET}")
            print(f"  {Colors.INFO}1. 预览所有变更（彩色diff）{Colors.RESET}")
            print(f"  {Colors.INFO}2. 应用所有更新{Colors.RESET}")
            print(f"  {Colors.INFO}3. 交互式选择文件{Colors.RESET}")
            print(f"  {Colors.INFO}4. 检查冲突{Colors.RESET}")
            print(f"  {Colors.INFO}5. 显示状态{Colors.RESET}")
            print(f"  {Colors.INFO}6. 重新获取更新{Colors.RESET}")
            print(f"  {Colors.INFO}0. 退出{Colors.RESET}")
            
            choice = input(f"\n{Colors.PROMPT}选择操作 (0-6): {Colors.RESET}").strip()
            
            if choice == "0":
                print(f"{Colors.SUCCESS}👋 感谢使用，再见！{Colors.RESET}")
                break
            elif choice == "1":
                self.preview_changes(files)
            elif choice == "2":
                self.apply_all_changes(files)
            elif choice == "3":
                self.interactive_select(files)
            elif choice == "4":
                self.check_conflicts()
            elif choice == "5":
                self.show_status()
            elif choice == "6":
                continue  # 重新开始循环，会重新获取更新
            else:
                print(f"{Colors.ERROR}❌ 无效选择，请重试{Colors.RESET}")
            
            # 操作完成后显示后续步骤提示
            if choice in ["2", "3"]:
                print(f"\n{Colors.TITLE}💡 后续步骤:{Colors.RESET}")
                print(f"  1. {Colors.INFO}解决可能存在的冲突{Colors.RESET}")
                print(f"  2. {Colors.INFO}提交更改: git commit -m 'sync: 上游更新'{Colors.RESET}")
                print(f"  3. {Colors.INFO}推送: git push origin main{Colors.RESET}")
                print(f"  4. {Colors.INFO}在主仓库更新子模块引用{Colors.RESET}")
            
            # 询问是否继续
            if choice != "0":
                cont = input(f"\n{Colors.PROMPT}按回车返回主菜单，或输入 0 退出: {Colors.RESET}").strip()
                if cont == "0":
                    print(f"{Colors.SUCCESS}👋 感谢使用，再见！{Colors.RESET}")
                    break

# ============================================================================
# 程序入口
# ============================================================================
def main():
    """主函数"""
    # 检查是否在Git仓库中
    if not Path(".git").exists():
        print(f"{Colors.ERROR}❌ 请在Git仓库中运行此脚本{Colors.RESET}")
        print(f"{Colors.INFO}当前目录: {Path.cwd()}{Colors.RESET}")
        return 1
    
    # 检查Git是否可用
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except:
        print(f"{Colors.ERROR}❌ Git不可用，请先安装Git{Colors.RESET}")
        return 1
    
    try:
        sync = UpstreamSync()
        sync.main_loop()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  用户中断操作{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.ERROR}❌ 程序发生错误: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())