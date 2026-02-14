from PyQt6.QtWidgets import QFrame, QVBoxLayout

class WidgetPage(QFrame):
    """小组件页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("widgetPage")
        self.vBoxLayout = QVBoxLayout(self)
        # 设置边距，确保内容避开标题栏
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(5)