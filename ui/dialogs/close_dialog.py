from PyQt6.QtWidgets import QWidget
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PushButton, CheckBox, PrimaryPushButton


class CloseConfirmationDialog(MessageBoxBase):
    """关闭确认对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel("关闭确认", self)
        self.viewLayout.addWidget(self.titleLabel)

        self.messageLabel = SubtitleLabel("您确定要关闭应用程序吗？", self)
        self.messageLabel.setStyleSheet("font-size: 14px; font-weight: normal;")
        self.viewLayout.addWidget(self.messageLabel)

        self.dontAskAgainCheckBox = CheckBox("以后不再提示", self)
        self.viewLayout.addWidget(self.dontAskAgainCheckBox)

        self.hideYesButton()
        self.hideCancelButton()

        self.minimizeButton = PushButton("最小化到任务栏", self)
        self.exitButton = PrimaryPushButton("退出", self)

        self.buttonLayout.addWidget(self.minimizeButton)
        self.buttonLayout.addWidget(self.exitButton)

        self.minimizeButton.clicked.connect(self.accept)
        self.exitButton.clicked.connect(lambda: self.done(2))

        self.widget.setMinimumWidth(350)

    def get_dont_ask_again(self):
        """获取是否不再提示的状态"""
        return self.dontAskAgainCheckBox.isChecked()
