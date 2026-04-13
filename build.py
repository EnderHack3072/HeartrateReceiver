#python -m nuitka --standalone --mingw64 --windows-console-mode=disable --enable-plugin=pyqt6 --include-package=PyQt6 --include-package=PyQt6.QtCore --include-package=PyQt6.QtGui --include-package=PyQt6.QtWidgets --include-package=qfluentwidgets --include-package=bleak --include-package=winrt --include-package=winrt.runtime --include-package=winrt.system --include-package=winrt.windows --include-package=func --include-package=win32com --include-data-files=icon.ico=icon.ico --include-data-files=config/config.json=config/config.json --output-dir=dist --output-filename=HeartRateMonitor.exe --remove-output --follow-imports --assume-yes-for-downloads main.py
import os

c = (
    'python -m nuitka ' \
    #编译设置
    '--windows-icon-from-ico=icon.ico ' \
    '--standalone ' \
    '--mingw64 ' \
    #'--windows-console-mode=disable ' \
    #'--onefile ' \
    '--lto=yes ' \
    '--output-dir=dist ' \
    '--output-filename=HeartRateMonitor.exe ' \
    '--remove-output ' \
    '--follow-imports ' \
    '--assume-yes-for-downloads ' \
    '--enable-plugin=pyqt6 ' \
    #引入插件
    '--include-package=PyQt6 ' \
    '--include-package=PyQt6.QtCore ' \
    '--include-package=PyQt6.QtGui ' \
    '--include-package=PyQt6.QtWidgets ' \
    '--include-package=qfluentwidgets ' \
    '--include-package=bleak ' \
    '--include-package=winrt ' \
    '--include-package=winrt.runtime ' \
    '--include-package=winrt.system ' \
    '--include-package=winrt.windows ' \
    '--include-package=func ' \
    '--include-package=win32com ' \
    '--include-data-files=icon.ico=icon.ico ' \
    '--include-data-files=config/config.json=config/config.json ' \
    'main.py'
)

#print(c)
os.system(c)
#--onefile