<p align="center"><img src="/resources/SRAico.png" alt="icon"></p>
<p align="center">
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="platform">
    <img alt="Static Badge" src="https://img.shields.io/badge/python-3.12-skyblue">
</p>

# SRA-CE-cli
作为[EveGlowLuna/StarRailAssistant-CommunityEdition](https://github.com/EveGlowLuna/StarRailAssistant-CommunityEdition)的子模块，同步上游[Shasnow/StarRailAssistant](https://github.com/Shasnow/StarRailAssistant)代码

## 孩子们，Linux也干了
尝试支持Linux,但只支持X11桌面

## 小白可直接移步至主仓库
[EveGlowLuna/StarRailAssistant-CommunityEdition](https://github.com/EveGlowLuna/StarRailAssistant-CommunityEdition)

## 同步上游更新
在 `SRA-CE-cli` 文件夹中：
```pwsh
git remote add upstream https://github.com/Shasnow/StarRailAssistant.git
```

## 运行、编译
```pwsh
# 运行
pip install -r requirements.txt
python main.py

# 编译（python != 3.13）
# 注意package.py会把生成的文件夹放到SRA-CE-cli上一级
pip install -r requirements.txt
python package.py
# 去上一级文件夹寻找StarRailAssistant文件夹
cd ..
```

## 相关链接

[StarRailAssistant Community Edition](www.starrailassistant.xyz)

[StarRailAssistant](starrailassistant.top)