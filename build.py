#python -m nuitka --standalone --onefile --mingw64 --windows-console-mode=disable --enable-plugin=pyqt5 --include-package=PyQt5 --include-package=PyQt5.QtCore --include-package=PyQt5.QtGui --include-package=PyQt5.QtWidgets --include-package=qfluentwidgets --include-package=bleak --include-package=winrt --include-package=winrt.runtime --include-package=winrt.system --include-package=winrt.windows --include-package=func --include-data-file=src/cp2.png=src/cp2.png --output-dir=dist --output-filename=HeartRateMonitor.exe --remove-output --follow-imports --assume-yes-for-downloads main.py
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
    '--enable-plugin=pyqt5 ' \
    #引入插件
    '--include-package=PyQt5 ' \
    '--include-package=PyQt5.QtCore ' \
    '--include-package=PyQt5.QtGui ' \
    '--include-package=PyQt5.QtWidgets ' \
    '--include-package=qfluentwidgets ' \
    '--include-package=bleak ' \
    '--include-package=winrt ' \
    '--include-package=winrt.runtime ' \
    '--include-package=winrt.system ' \
    '--include-package=winrt.windows ' \
    '--include-package=func ' \
    '--include-data-files=icon.ico=icon.ico ' \
    'main.py'
)

#print(c)
os.system(c)
#--onefile