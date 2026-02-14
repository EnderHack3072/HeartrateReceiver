from PyQt5.QtCore import Qt
from qfluentwidgets import (Dialog, CheckBox, PushButton)
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

class CloseConfirmationDialog(Dialog):
    """关闭确认对话框"""
    
    def __init__(self, parent=None):
        super().__init__("关闭确认", "您确定要退出程序吗？", parent)
        
        # 设置对话框大小（更紧凑）
        self.resize(320, 200)
        
        # 初始化选项
        self.option = None  # 初始化为None，通过按钮点击设置
        
        # 创建"下次不再提示"复选框
        self.dont_ask_checkbox = CheckBox("下次不再提示", self)
        
        button_group = self.findChild(type(self), "buttonGroup")
        if button_group is None:
            from PyQt5.QtWidgets import QFrame
            button_group = self.findChild(QFrame, "buttonGroup")
        if button_group:
            button_group.hide()
        
        from PyQt6.QtWidgets import QLabel
        window_title_label = self.findChild(QLabel, "windowTitleLabel")
        if window_title_label:
            window_title_label.hide()
        
        # 移除默认按钮
        self.yesButton.hide()
        self.cancelButton.hide()
        
        # 清空按钮布局
        if hasattr(self, 'buttonLayout'):
            while self.buttonLayout.count() > 0:
                item = self.buttonLayout.itemAt(0)
                self.buttonLayout.removeItem(item)
        
        # 完全清空vBoxLayout中除了标题和内容以外的所有项目
        # 标题和内容实际在第2个项目的子布局中
        while self.vBoxLayout.count() > 2:  # 保留标题和内容相关的前2个项目
            item = self.vBoxLayout.itemAt(self.vBoxLayout.count() - 1)
            self.vBoxLayout.removeItem(item)
        
        # 更新布局以应用所有更改
        self.vBoxLayout.update()
        
        # 创建自定义按钮布局（水平排列）
        self.button_container = QWidget(self)
        self.button_layout = QHBoxLayout(self.button_container)
        # 设置按钮容器边距，确保与窗口边缘有间距
        self.button_layout.setContentsMargins(20, 0, 20, 10)
        self.button_layout.setSpacing(12)
        
        # 创建"退出程序"按钮
        self.exit_button = PushButton("退出程序", self.button_container)
        self.exit_button.setFixedHeight(32)
        self.exit_button.clicked.connect(self.on_exit_clicked)
        
        # 创建"最小化到任务栏"按钮
        self.minimize_button = PushButton("最小化到任务栏", self.button_container)
        self.minimize_button.setFixedHeight(32)
        self.minimize_button.clicked.connect(self.on_minimize_clicked)
        
        # 添加按钮到布局（水平排列）
        self.button_layout.addWidget(self.exit_button)
        self.button_layout.addWidget(self.minimize_button)
        
        # 设置主布局边距，确保整体内容与窗口边缘有间距
        self.vBoxLayout.setContentsMargins(20, 10, 20, 10)
        
        # 将自定义组件添加到对话框
        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.dont_ask_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(self.button_container)
    
    def on_exit_clicked(self):
        """退出程序按钮点击处理"""
        self.option = "close"
        self.accept()
    
    def on_minimize_clicked(self):
        """最小化到任务栏按钮点击处理"""
        self.option = "minimize"
        self.accept()
    
    def get_option(self):
        """获取用户选择的选项"""
        return self.option
    
    def get_dont_ask_again(self):
        """获取是否下次不再提示"""
        return self.dont_ask_checkbox.isChecked()