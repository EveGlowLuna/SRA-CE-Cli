#!/usr/bin/env python3
"""
上游同步工具 - 图形化版本
支持文件树视图、多选、预览等功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import re
from pathlib import Path
from typing import List, Dict, Set
import threading

class UpstreamSyncGUI:
    def __init__(self):
        self.repo = Path.cwd()
        self.fetched = False
        self.exclude = [
            r'^\\.github/', r'^SRAFrontend/', r'^setup/',
            r'^README\\.md$', r'^package\\.py$', r'^sync_upstream\\.py$',
            r'^\\.gitattributes$', r'^\\.git'
        ]
        
        self.root = tk.Tk()
        self.root.title("StarRailAssistant 上游同步工具")
        self.root.geometry("1000x700")
        
        # 数据
        self.file_tree = {'added': [], 'modified': [], 'deleted': [], 'binary': []}
        self.selected_files: Set[str] = set()
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📁 上游文件变更", font=('', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # 左侧：文件树
        tree_frame = ttk.LabelFrame(main_frame, text="文件列表", padding="5")
        tree_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # 创建 Treeview
        self.tree = ttk.Treeview(tree_frame, columns=('status', 'path'), show='tree headings', selectmode='extended')
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置列
        self.tree.heading('#0', text='文件')
        self.tree.heading('status', text='状态')
        self.tree.heading('path', text='路径')
        
        self.tree.column('#0', width=300)
        self.tree.column('status', width=80)
        self.tree.column('path', width=400)
        
        # 滚动条
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # 右侧：预览和操作
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # 操作按钮
        btn_frame = ttk.LabelFrame(right_frame, text="操作", padding="5")
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(btn_frame, text="🔄 获取更新", command=self.fetch_updates).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="👁 预览选中", command=self.preview_selected).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="✅ 应用选中", command=self.apply_selected).pack(fill=tk.X, pady=2)
        
        # 选择按钮分组
        select_frame = ttk.Frame(btn_frame)
        select_frame.pack(fill=tk.X, pady=2)
        ttk.Button(select_frame, text="📋 全选安全", command=self.select_safe).pack(fill=tk.X, pady=1)
        ttk.Button(select_frame, text="📋 全选所有", command=self.select_all).pack(fill=tk.X, pady=1)
        ttk.Button(select_frame, text="🗑 清空选择", command=self.clear_selection).pack(fill=tk.X, pady=1)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(right_frame, text="文件预览", padding="5")
        preview_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.NONE, font=('Consolas', 9))
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 绑定事件
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # 配置标签颜色
        self.tree.tag_configure('added', foreground='green')
        self.tree.tag_configure('modified', foreground='blue')
        self.tree.tag_configure('deleted', foreground='red')
        self.tree.tag_configure('binary', foreground='purple')
        
    def run(self, cmd: str) -> str:
        """执行命令"""
        try:
            p = subprocess.run(
                cmd, shell=True, cwd=self.repo,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8'
            )
            return p.stdout
        except Exception as e:
            return f"Error: {e}"
    
    def exists(self, ref: str, path: str) -> bool:
        """检查文件在指定引用中是否存在"""
        return subprocess.run(
            f"git show {ref}:{path}",
            shell=True, cwd=self.repo,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
    
    def file_status(self, path: str) -> str:
        """获取文件状态"""
        in_head = self.exists('HEAD', path)
        in_up = self.exists('upstream/main', path)
        
        if in_up and not in_head:
            return 'added'
        if in_head and not in_up:
            return 'deleted'
        if in_head and in_up:
            stat = self.run(f"git diff --numstat HEAD..upstream/main -- {path}").strip()
            if stat:
                parts = stat.split('\t')
                if len(parts) >= 2 and parts[0] == '-' and parts[1] == '-':
                    return 'binary'
                return 'modified'
            return 'unchanged'
        return 'unknown'
    
    def collect_changes(self) -> Dict[str, List[str]]:
        """收集文件变更"""
        out = self.run("git diff --name-only HEAD..upstream/main")
        tree = {'added': [], 'modified': [], 'deleted': [], 'binary': []}
        
        for f in out.splitlines():
            if not f.strip():
                continue
                
            # 检查排除规则
            if any(re.match(p, f) for p in self.exclude):
                continue
                
            st = self.file_status(f)
            if st in tree:
                tree[st].append(f)
        
        return tree
    
    def fetch_updates(self):
        """获取上游更新"""
        def fetch_thread():
            self.status_var.set("🔄 正在获取 upstream 更新...")
            self.root.update()
            
            if subprocess.run("git fetch upstream", shell=True, cwd=self.repo).returncode != 0:
                messagebox.showerror("错误", "获取 upstream 更新失败")
                self.status_var.set("❌ 获取更新失败")
                return
            
            self.fetched = True
            latest = self.run("git log -1 --oneline upstream/main").strip()
            
            # 收集变更
            self.file_tree = self.collect_changes()
            
            # 更新界面
            self.root.after(0, lambda: self.update_tree_view(latest))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_tree_view(self, latest_commit: str):
        """更新树视图"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 状态图标和颜色映射
        status_info = {
            'added': ('➕', '新增', 'added'),
            'modified': ('📝', '修改', 'modified'),
            'deleted': ('🗑️', '删除', 'deleted'),
            'binary': ('📦', '二进制', 'binary')
        }
        
        total_files = 0
        
        # 添加分类节点
        for status, files in self.file_tree.items():
            if not files:
                continue
                
            icon, label, tag = status_info[status]
            category_id = self.tree.insert('', 'end', 
                text=f"{icon} {label} ({len(files)})",
                values=('', ''),
                tags=(tag,))
            
            # 添加文件
            for file_path in sorted(files):
                file_id = self.tree.insert(category_id, 'end',
                    text=Path(file_path).name,
                    values=(label, file_path),
                    tags=(tag,))
                total_files += 1
        
        # 展开所有节点
        for item in self.tree.get_children():
            self.tree.item(item, open=True)
        
        self.status_var.set(f"✅ 已获取更新 | 最新提交: {latest_commit} | 共 {total_files} 个文件")
    
    def on_tree_select(self, event):
        """树选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # 获取选中的文件路径
        self.selected_files.clear()
        for item in selection:
            values = self.tree.item(item, 'values')
            if len(values) >= 2 and values[1]:  # 有路径的才是文件
                self.selected_files.add(values[1])
        
        # 更新状态
        if self.selected_files:
            self.status_var.set(f"已选择 {len(self.selected_files)} 个文件")
    
    def on_double_click(self, event):
        """双击预览文件"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if len(values) >= 2 and values[1]:
                self.preview_file(values[1])
    
    def preview_file(self, file_path: str):
        """预览单个文件"""
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, f"=== {file_path} ===\n\n")
        
        diff = self.run(f"git diff HEAD..upstream/main -- {file_path}")
        if not diff.strip():
            self.preview_text.insert(tk.END, "(无文本差异或为二进制文件)")
        else:
            self.preview_text.insert(tk.END, diff)
    
    def preview_selected(self):
        """预览选中文件"""
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择要预览的文件")
            return
        
        self.preview_text.delete(1.0, tk.END)
        
        for file_path in sorted(self.selected_files):
            self.preview_text.insert(tk.END, f"\n{'='*60}\n")
            self.preview_text.insert(tk.END, f"文件: {file_path}\n")
            self.preview_text.insert(tk.END, f"{'='*60}\n\n")
            
            diff = self.run(f"git diff HEAD..upstream/main -- {file_path}")
            if not diff.strip():
                self.preview_text.insert(tk.END, "(无文本差异或为二进制文件)\n")
            else:
                self.preview_text.insert(tk.END, diff)
                self.preview_text.insert(tk.END, "\n")
    
    def apply_selected(self):
        """应用选中的文件"""
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择要同步的文件")
            return
        
        # 分类选中的文件
        add_modify_files = []
        delete_files = []
        
        for file_path in self.selected_files:
            for status, files in self.file_tree.items():
                if file_path in files:
                    if status in ['added', 'modified', 'binary']:
                        add_modify_files.append(file_path)
                    elif status == 'deleted':
                        delete_files.append(file_path)
                    break
        
        if not add_modify_files and not delete_files:
            messagebox.showwarning("提示", "选中的文件中没有可同步的文件")
            return
        
        # 构建确认消息
        msg_parts = []
        if add_modify_files:
            msg_parts.append(f"更新/新增 {len(add_modify_files)} 个文件")
        if delete_files:
            msg_parts.append(f"删除 {len(delete_files)} 个文件")
        
        confirm_msg = f"确定要同步以下操作吗？\n\n" + "\n".join(msg_parts)
        if delete_files:
            confirm_msg += f"\n\n⚠️ 删除的文件:\n" + "\n".join(f"  • {f}" for f in delete_files[:5])
            if len(delete_files) > 5:
                confirm_msg += f"\n  ... 还有 {len(delete_files) - 5} 个文件"
        
        if not messagebox.askyesno("确认同步", confirm_msg):
            return
        
        def apply_thread():
            self.status_var.set("🔄 正在应用文件...")
            success_count = 0
            total_count = len(add_modify_files) + len(delete_files)
            
            # 处理新增/修改的文件
            for file_path in add_modify_files:
                if subprocess.run(f"git checkout upstream/main -- {file_path}", 
                                shell=True, cwd=self.repo).returncode == 0:
                    success_count += 1
            
            # 处理删除的文件
            for file_path in delete_files:
                if subprocess.run(f"git rm {file_path}", 
                                shell=True, cwd=self.repo).returncode == 0:
                    success_count += 1
            
            self.root.after(0, lambda: self.on_apply_complete(success_count, total_count))
        
        threading.Thread(target=apply_thread, daemon=True).start()
    
    def on_apply_complete(self, success_count: int, total_count: int):
        """应用完成回调"""
        if success_count == total_count:
            messagebox.showinfo("成功", f"✅ 已成功同步 {success_count} 个文件")
            self.status_var.set(f"✅ 同步完成: {success_count}/{total_count}")
            # 重新获取更新以刷新状态
            self.fetch_updates()
        else:
            messagebox.showwarning("部分成功", f"⚠️ 同步了 {success_count}/{total_count} 个文件")
            self.status_var.set(f"⚠️ 部分同步: {success_count}/{total_count}")
    
    def select_safe(self):
        """选择安全的文件（新增+修改，不包括删除）"""
        # 清空当前选择
        self.tree.selection_remove(self.tree.selection())
        
        # 选择新增和修改的文件
        for item in self.tree.get_children():
            for child in self.tree.get_children(item):
                values = self.tree.item(child, 'values')
                if len(values) >= 2 and values[1]:
                    file_path = values[1]
                    for status, files in self.file_tree.items():
                        if file_path in files and status in ['added', 'modified', 'binary']:
                            self.tree.selection_add(child)
                            break
    
    def select_all(self):
        """选择所有文件（包括删除）"""
        # 清空当前选择
        self.tree.selection_remove(self.tree.selection())
        
        # 选择所有文件
        for item in self.tree.get_children():
            for child in self.tree.get_children(item):
                values = self.tree.item(child, 'values')
                if len(values) >= 2 and values[1]:  # 有路径的才是文件
                    self.tree.selection_add(child)
    
    def clear_selection(self):
        """清空选择"""
        self.tree.selection_remove(self.tree.selection())
        self.selected_files.clear()
        self.status_var.set("已清空选择")
    
    def run_gui(self):
        """运行GUI"""
        if not Path('.git').exists():
            messagebox.showerror("错误", "请在 Git 仓库中运行此工具")
            return
        
        # 自动获取更新
        self.root.after(100, self.fetch_updates)
        
        self.root.mainloop()

if __name__ == '__main__':
    app = UpstreamSyncGUI()
    app.run_gui()