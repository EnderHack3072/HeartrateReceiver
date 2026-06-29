import os

c = (
    'python -m nuitka ' \
    #编译设置
    '--windows-icon-from-ico=icon.ico ' \
    '--standalone ' \
    '--mingw64 ' \
    '--windows-console-mode=disable ' \
    #'--onefile ' \
    '--lto=yes ' \
    '--output-dir=F:/HeartrateReceiverDist ' \
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
    '--include-package=core ' \
    '--include-package=system ' \
    '--include-package=persistence ' \
    '--include-package=ui ' \
    '--include-package=win32gui ' \
    '--include-package=win32api ' \
    '--include-package=PIL ' \
    '--include-package=win32con ' \
    '--include-package=win32ui ' \
    '--include-package=psutil ' \
    '--include-data-files=icon.ico=icon.ico ' \
    '--include-data-files=config/config.json=config/config.json ' \
    'main.py'
)

#print(c)
os.system(c)
#--onefile