# RunCat_py


# Introductoin

RunCat_for_windows项目的python实现。

# Install & Run

## method 1
脚本运行
```bash
# 建议用python3.6，如果版本过高请自行安装依赖
# step 1:
pip install -f requirements.txt
# step 2: 下载猫片 地址:https://github.com/Kyome22/RunCat_for_windows/tree/master/RunCat/resources/cat
# 放在一个文件夹中，修改running_cat.py中的路径为存放猫片的文件夹
# step 3:
python running_cat.py
```

## method 2
自行编译
```bash
# [Option]
pip install pyinstaller
pyinstaller -F -w -i cat/light_cat_1.ico running_cat.py --add-data .\cat\*;.\cat\
# double click running_cat.exe
```

## method 3 (TODO)
下载release里的exe
```
download running_cat.exe
double click running_cat.exe
```
# Reference

灵感来源: https://github.com/Kyome22/RunCat_for_windows

代码实现参考: https://github.com/samclane/LIFX-Control-Panel 历史版本中的SysTrayIcon.py 最新版本中已无这个文件
