import psutil
import platform
import subprocess
from typing import Union


def Popen(arg: Union[str, list[str]], shell: bool = False, **kwargs) -> bool:
    """
    启动进程的跨平台函数

    Args:
        arg: 可执行文件路径或参数列表
        shell: 是否使用shell执行命令

    Returns:
        bool: 进程是否成功启动
    """
    try:
        if isinstance(arg, str):
            subprocess.Popen(arg, shell=shell, **kwargs)
        else:
            subprocess.Popen(arg, shell=shell, **kwargs)
        return True
    except (FileNotFoundError, OSError):
        return False



def is_process_running(process_name: str) -> bool:
    """
    检查指定进程是否在运行（跨平台）

    Args:
        process_name: 进程名

    Returns:
        bool: 进程是否在运行
    """
    current_platform = platform.system().lower()

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            # 用cmdline检查进程
            if current_platform == 'linux':
                cmdline = proc.info.get('cmdline')
                if cmdline and process_name.lower() in ' '.join(cmdline).lower():
                    return True

            # 检查进程名（适用于Windows和部分Linux进程）
            proc_name = proc.info.get('name')
            if proc_name and process_name.lower() in proc_name.lower():
                return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def task_kill(process_name: str) -> bool:
    """
    关闭指定进程（跨平台）

    Args:
        process_name: 进程名

    Returns:
        bool: 是否成功关闭
    """
    current_platform = platform.system().lower()
    killed = False

    for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
        try:
            proc_info = proc.info
            match = False

            # 平台特定的匹配逻辑
            if current_platform == 'linux':
                cmdline = proc_info.get('cmdline')
                if cmdline and process_name.lower() in ' '.join(cmdline).lower():
                    match = True
            elif current_platform == 'windows':
                proc_name = proc_info.get('name')
                if proc_name and process_name.lower() in proc_name.lower():
                    match = True
            if match:
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return killed


def shutdown(time: int):
    """关机

    Args:
        time (int): 延时关机时间，单位分
    """
    if time < 0:
        time = 0
    if platform.system() == "Windows":
        Popen(f"shutdown -s -t {time * 60}", shell=True)
    else:
        if time == 0:
            Popen("sudo shutdown -h now", shell=True)
        else:
            Popen(f"sudo shutdown -h +{time}", shell=True)


def shutdown_cancel():
    """取消关机"""
    if platform.system() == "Windows":
        Popen("shutdown -a", shell=True)
    else:
        Popen("shutdown -c", shell=True)