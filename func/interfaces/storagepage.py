from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.QtCore import Qt

class StoragePage(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("storagePage")
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)
        self.vBoxLayout.setSpacing(10)
