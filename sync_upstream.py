#!/usr/bin/env python3
"""
上游同步工具 - StarRailAssistant 专用（交互选择 + 状态安全版）

特性：
- 提供【diff 树状图】显示（基于真实文件存在性，修复误判删除）
- 支持 diff 预览（彩色，高亮增删）
- 支持【选择性同步文件】
- 操作顺序清晰，终端输出美化（Windows / Linux）
- 修复 f-string 语法错误
"""

# ============================================================================
# imports
# ============================================================================
import subprocess
import sys
import re
from pathlib import Path
from typing import List, Dict

# ============================================================================
# color
# ============================================================================
try:
    from colorama import init, Fore, Style, just_fix_windows_console
    just_fix_windows_console()
    init(autoreset=True)

    class C:
        H = Fore.MAGENTA + Style.BRIGHT
        T = Fore.CYAN + Style.BRIGHT
        OK = Fore.GREEN + Style.BRIGHT
        WARN = Fore.YELLOW + Style.BRIGHT
        ERR = Fore.RED + Style.BRIGHT
        INFO = Fore.BLUE
        P = Fore.YELLOW
        R = Style.RESET_ALL
        ADD = Fore.GREEN
        DEL = Fore.RED
        MOD = Fore.CYAN
        BIN = Fore.MAGENTA
        HUNK = Fore.YELLOW

        @staticmethod
        def diff(line: str) -> str:
            if line.startswith('@@'):
                return C.HUNK + line + C.R
            if line.startswith('+') and not line.startswith('+++'):
                return C.ADD + line + C.R
            if line.startswith('-') and not line.startswith('---'):
                return C.DEL + line + C.R
            return line
except Exception:
    class C:
        H=T=OK=WARN=ERR=INFO=P=ADD=DEL=MOD=BIN=HUNK=R=""
        diff = staticmethod(lambda x: x)

# ============================================================================
# core
# ============================================================================
class UpstreamSync:
    def __init__(self):
        self.repo = Path.cwd()
        self.fetched = False
        self.exclude = [
            r'^\\.github/', r'^SRAFrontend/', r'^setup/',
            r'^README\\.md$', r'^package\\.py$', r'^sync_upstream\\.py$',
            r'^\\.gitattributes$', r'^\\.git'
        ]

    # ------------------------------------------------------------------
    def run(self, cmd: str) -> str:
        p = subprocess.run(
            cmd,
            shell=True,
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return p.stdout.decode('utf-8', errors='ignore')

    # ------------------------------------------------------------------
    def ensure_fetch(self) -> bool:
        if self.fetched:
            return True
        print(f"{C.INFO}🔄 获取 upstream 更新中…{C.R}")
        if subprocess.run("git fetch upstream", shell=True).returncode != 0:
            print(f"{C.ERR}❌ fetch upstream 失败{C.R}")
            return False
        self.fetched = True
        latest = self.run("git log -1 --oneline upstream/main").strip()
        print(f"{C.OK}✅ 已同步 upstream{C.R}")
        if latest:
            print(f"{C.INFO}   最新提交: {latest}{C.R}")
        return True

    # ------------------------------------------------------------------
    def exists(self, ref: str, path: str) -> bool:
        return subprocess.run(
            f"git show {ref}:{path}",
            shell=True,
            cwd=self.repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ).returncode == 0

    # ------------------------------------------------------------------
    def file_status(self, path: str) -> str:
        in_head = self.exists('HEAD', path)
        in_up = self.exists('upstream/main', path)

        # 从 upstream 角度看变更：
        # upstream 有但 HEAD 没有 = upstream 新增了文件
        # HEAD 有但 upstream 没有 = upstream 删除了文件
        if in_up and not in_head:
            return 'added'
        if in_head and not in_up:
            return 'deleted'
        if in_head and in_up:
            stat = self.run(f"git diff --numstat HEAD..upstream/main -- {path}").strip()
            if stat:
                a, d, *_ = stat.split('\t')
                if a == '-' and d == '-':
                    return 'binary'
                return 'modified'
            return 'unchanged'
        return 'unknown'

    # ------------------------------------------------------------------
    def collect(self) -> Dict[str, List[str]]:
        out = self.run("git diff --name-only HEAD..upstream/main")
        tree = {'added': [], 'modified': [], 'deleted': [], 'binary': []}

        for f in out.splitlines():
            if any(re.match(p, f) for p in self.exclude):
                continue
            st = self.file_status(f)
            if st in tree:
                tree[st].append(f)
        return tree

    # ------------------------------------------------------------------
    def show_tree(self, tree: Dict[str, List[str]]):
        print(f"\n{C.H}📁 文件变更树状图{C.R}")
        for k, icon, color in [
            ('added', '➕ 新增', C.ADD),
            ('modified', '📝 修改', C.MOD),
            ('deleted', '🗑️ 删除', C.DEL),
            ('binary', '📦 二进制', C.BIN)
        ]:
            files = tree[k]
            if not files:
                continue
            print(f"{color}{icon} ({len(files)}){C.R}")
            for f in files:
                print(f"   └── {f}")

    # ------------------------------------------------------------------
    def preview(self, files: List[str]):
        for f in files:
            print(f"\n{C.T}--- {f} ---{C.R}")
            diff = self.run(f"git diff HEAD..upstream/main -- {f}")
            if not diff.strip():
                print(f"{C.WARN}(无文本 diff 或为二进制){C.R}")
                continue
            for l in diff.splitlines():
                print(C.diff(l))

    # ------------------------------------------------------------------
    def choose_files(self, files: List[str]) -> List[str]:
        print(f"{C.INFO}📁 可同步文件：{C.R}")
        for i, f in enumerate(files, 1):
            print(f" {C.P}{i:>2}.{C.R} {f}")
        raw = input(f"\n{C.P}输入编号（如 1,3,5 或 all）：{C.R}").strip()
        if raw.lower() == 'all':
            return files
        idx = {int(x)-1 for x in raw.split(',') if x.strip().isdigit()}
        return [f for i, f in enumerate(files) if i in idx]

    # ------------------------------------------------------------------
    def apply(self, files: List[str]):
        for f in files:
            print(f"{C.INFO}➡ 更新 {f}{C.R}")
            subprocess.run(f"git checkout upstream/main -- {f}", shell=True)
        print(f"{C.OK}✅ 已应用 {len(files)} 个文件{C.R}")

    # ------------------------------------------------------------------
    def menu(self):
        if not self.ensure_fetch():
            return

        tree = self.collect()
        self.show_tree(tree)

        files = tree['added'] + tree['modified']
        if not files:
            print(f"{C.OK}🎉 当前已是最新{C.R}")
            return

        while True:
            print(f"\n{C.INFO}1. 预览 diff{C.R}")
            print(f"{C.INFO}2. 选择文件并同步{C.R}")
            print(f"{C.INFO}3. 全部同步（不含删除）{C.R}")
            print(f"{C.INFO}0. 退出{C.R}")

            c = input(f"{C.P}请选择操作: {C.R}").strip()
            if c == '0':
                return
            if c == '1':
                self.preview(files)
            elif c == '2':
                sel = self.choose_files(files)
                if sel:
                    self.apply(sel)
            elif c == '3':
                self.apply(files)
            else:
                print(f"{C.WARN}无效选择{C.R}")

# ============================================================================
# entry
# ============================================================================
if __name__ == '__main__':
    if not Path('.git').exists():
        print("请在 Git 仓库中运行")
        sys.exit(1)
    UpstreamSync().menu()
