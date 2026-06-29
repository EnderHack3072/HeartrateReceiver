import sys

# 闪屏必须在任何 PyQt 加载前执行，覆盖 PyQt 的初始化耗时
import system.startup.app_startup as app_startup
app_startup.start()

from PyQt6.QtCore import qInstallMessageHandler
from PyQt6.QtWidgets import QApplication

from ui.main_window.main_window import HeartRateMonitorWindow


def _qt_msg_handler(mode, context, message):
    if "QFont::setPointSize" not in message:
        print(message)


def run():
    app = QApplication(sys.argv)
    qInstallMessageHandler(_qt_msg_handler)

    window = HeartRateMonitorWindow()
    window.show()

    app_startup.close_system_splash(app_startup.syshwnd)

    sys.exit(app.exec())
