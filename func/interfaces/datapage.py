from PyQt6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget, QLabel
from PyQt6.QtCore import Qt
from qfluentwidgets import Pivot

class DataPage(QFrame):
    """数据页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("dataPage")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(5)
        
        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        
        self.page01 = QLabel('01', self)
        self.page02 = QLabel('02', self)
        self.page03 = QLabel('03', self)
        
        self.addSubInterface(self.page01, 'page01', '01')
        self.addSubInterface(self.page02, 'page02', '02')
        self.addSubInterface(self.page03, 'page03', '03')
        
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.page01)
        self.pivot.setCurrentItem(self.page01.objectName())
        
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)
    
    def addSubInterface(self, widget: QLabel, objectName: str, text: str):
        widget.setObjectName(objectName)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stackedWidget.addWidget(widget)
        
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
    
    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
