<p align="center"><img src="/resources/SRAico.png" alt="icon"></p>
<p align="center">
    <img src="https://img.shields.io/badge/platform-Windows-blue" alt="platform">
    <img alt="Static Badge" src="https://img.shields.io/badge/python-3.12-skyblue">
</p>

# SRA-CE-cli
作为[EveGlowLuna/StarRailAssistant-CommunityEdition](https://github.com/EveGlowLuna/StarRailAssistant-CommunityEdition)的子模块，同步上游[Shasnow/StarRailAssistant](https://github.com/Shasnow/StarRailAssistant)代码

## 小白可直接移步至主仓库
[EveGlowLuna/StarRailAssistant-CommunityEdition](https://github.com/EveGlowLuna/StarRailAssistant-CommunityEdition)

或使用原版SRA:

[Shasnow/StarRailAssistant](https://github.com/Shasnow/StarRailAssistant)

## 同步上游更新
在 `SRA-CE-cli` 文件夹中：
```pwsh
git remote add upstream https://github.com/Shasnow/StarRailAssistant.git

python sync_upstream.py
# 或者
./sync.ps1
# 注意 sync.ps1 停止维护
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