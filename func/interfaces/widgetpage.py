from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget, QLabel
from qfluentwidgets import Pivot
from .widgets_interface import WidgetsInterface


class WidgetPage(QFrame):
    """小组件页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("widgetPage")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(5)

        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)

        self.mainSettingsPage = WidgetsInterface(self)
        self.presetThemePage = QLabel('开发中……', self)
        self.presetThemePage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.customThemePage = QLabel('开发中……', self)
        self.customThemePage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addSubInterface(self.mainSettingsPage, 'mainSettingsPage', '主要设置')
        self.addSubInterface(self.presetThemePage, 'presetThemePage', '预制主题')
        self.addSubInterface(self.customThemePage, 'customThemePage', '自定义主题')

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.mainSettingsPage)
        self.pivot.setCurrentItem(self.mainSettingsPage.objectName())

        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)

    def addSubInterface(self, widget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)

        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
