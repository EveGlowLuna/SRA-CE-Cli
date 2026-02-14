#   This file is part of StarRailAssistant.

#   StarRailAssistant is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by the Free Software Foundation,
#   either version 3 of the License, or (at your option) any later version.

#   StarRailAssistant is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License along with StarRailAssistant.
#   If not, see <https://www.gnu.org/licenses/>.

#   yukikage@qq.com

import os
import pwd
import sys
from pathlib import Path


def get_real_home() -> str:
    """
    获取真正的用户主目录，即使在sudo环境下也能正确获取原始用户的home目录
    
    Returns:
        str: 用户的主目录路径
    """
    sudo_user = os.environ.get("SUDO_USER")
    
    if sudo_user:
        # 通过用户名查询 home 目录
        try:
            return pwd.getpwnam(sudo_user).pw_dir
        except KeyError:
            # 如果无法找到sudo用户，回退到普通方式
            return os.path.expanduser("~")
    else:
        # 没用 sudo 运行时
        return os.path.expanduser("~")


def get_sra_config_dir() -> Path:
    """
    获取SRA配置目录路径，自动处理跨平台和sudo环境
    
    Returns:
        Path: SRA配置目录的Path对象
    """
    real_home = get_real_home()
    
    if sys.platform == "win32":
        # Windows平台使用APPDATA环境变量
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "SRA"
        else:
            # 如果APPDATA不可用，使用用户目录下的AppData
            return Path(real_home) / "AppData" / "Roaming" / "SRA"
    else:
        # Linux/macOS平台使用标准配置目录
        return Path(real_home) / ".config" / "SRA"


# 兼容性导出，保持原有接口
def get_app_data_sra_dir() -> Path:
    """
    兼容旧版本的函数名，推荐使用 get_sra_config_dir()
    
    Returns:
        Path: SRA配置目录的Path对象
    """
    return get_sra_config_dir()