from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from qfluentwidgets import SubtitleLabel, TitleLabel, BodyLabel, PushButton, PrimaryPushButton, CardWidget, CheckBox, IndeterminateProgressBar, ProgressBar, ListWidget, ToolTipFilter, ToolTipPosition
from func.interfaces.heart_rate_interface.line_chart_page import LineChartPage
from func.interfaces.heart_rate_interface.trend_chart_page import TrendChartPage

class HomePage(QFrame):
    """主页页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("homePage")
        self.hBoxLayout = QHBoxLayout(self)
        # 增加上边距，确保卡片避开标题栏
        self.hBoxLayout.setContentsMargins(20, 20, 20, 20)
        self.hBoxLayout.setSpacing(20)
        
        # 左半屏卡片
        self.leftCard = CardWidget(self)
        self.leftLayout = QVBoxLayout(self.leftCard)
        self.leftLayout.setContentsMargins(20, 20, 20, 20)
        self.leftLayout.setSpacing(12)
        
        # 左侧卡片标题和副标题
        self.leftTitle = TitleLabel("设备连接")
        self.leftSubtitle = SubtitleLabel("扫描并连接您的心率监测设备")
        self.leftLayout.addWidget(self.leftTitle)
        self.leftLayout.addWidget(self.leftSubtitle)
        
        # 添加设备扫描文本
        self.scanText = BodyLabel("设备扫描")
        self.leftLayout.addWidget(self.scanText)
        
        # 添加复选框
        self.checkBox = CheckBox("自动筛选心率设备（这可能会大幅增加扫描时间）")
        self.checkBox.setToolTip("开启后，仅显示支持心率监测的设备。\n适合不赶时间并对你的设备不太了解的人使用。\n此功能会延长一到两倍的扫描时间。\n默认关闭")
        self.checkBox.installEventFilter(ToolTipFilter(self.checkBox, showDelay=300, position=ToolTipPosition.TOP))
        self.leftLayout.addWidget(self.checkBox)
        
        # 添加按钮，使用系统主题色
        self.scanButton = PrimaryPushButton("扫描设备")
        # PrimaryPushButton会自动使用系统主题色
        self.scanButton.clicked.connect(self.parent.device_manager.start_scan)
        self.leftLayout.addWidget(self.scanButton)
        
        # 添加不确定进度条（默认隐藏）
        self.indeterminateBar = IndeterminateProgressBar(start=False)
        self.indeterminateBar.hide()
        
        # 添加普通进度条（默认显示，100%）
        self.progressBar = ProgressBar()
        self.progressBar.setValue(100)
        
        self.leftLayout.addWidget(self.indeterminateBar)
        self.leftLayout.addWidget(self.progressBar)
        
        # 添加设备连接文本
        self.connectionText = BodyLabel("设备连接")
        self.leftLayout.addWidget(self.connectionText)
        
        # 添加列表框
        self.listWidget = ListWidget()
        # 设置右键单击选中
        self.listWidget.setSelectRightClickedRow(True)
        
        self.leftLayout.addWidget(self.listWidget)
        
        # 添加灰色小字
        from qfluentwidgets import CaptionLabel
        from PyQt6.QtGui import QColor
        self.infoLabel = CaptionLabel("为提升您的使用体验，程序会在本地缓存设备名称。")
        self.infoLabel.setStyleSheet("color: gray;")
        self.leftLayout.addWidget(self.infoLabel)
        
        # 添加按钮布局
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(10)
        
        # 添加连接设备按钮
        self.connectButton = PushButton("连接设备")
        self.connectButton.setEnabled(False)
        self.connectButton.clicked.connect(self.parent.connect_device)
        
        # 添加断开连接按钮
        self.disconnectButton = PushButton("断开连接")
        self.disconnectButton.setEnabled(False)
        self.disconnectButton.clicked.connect(self.parent.disconnect_device)
        
        self.buttonLayout.addWidget(self.connectButton)
        self.buttonLayout.addWidget(self.disconnectButton)
        
        self.leftLayout.addLayout(self.buttonLayout)
        
        # 右半屏卡片区域，使用垂直布局容纳两个卡片
        self.rightContainer = QFrame(self)
        self.rightContainerLayout = QVBoxLayout(self.rightContainer)
        self.rightContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.rightContainerLayout.setSpacing(20)
        
        # 右上卡片
        self.rightTopCard = CardWidget(self.rightContainer)
        self.rightTopLayout = QVBoxLayout(self.rightTopCard)
        self.rightTopLayout.setContentsMargins(0, 0, 0, 0)
        
        # 添加折线图页面到右上卡片
        self.lineChartPage = LineChartPage()
        self.rightTopLayout.addWidget(self.lineChartPage)
        
        # 右下卡片
        self.rightBottomCard = CardWidget(self.rightContainer)
        self.rightBottomLayout = QVBoxLayout(self.rightBottomCard)
        self.rightBottomLayout.setContentsMargins(0, 0, 0, 0)
        
        # 添加趋势折线图页面到右下卡片
        self.trendChartPage = TrendChartPage()
        self.rightBottomLayout.addWidget(self.trendChartPage)
        
        # 添加两个卡片到右侧容器布局
        self.rightContainerLayout.addWidget(self.rightTopCard, 1)
        self.rightContainerLayout.addWidget(self.rightBottomCard, 1)
        
        # 添加卡片到水平布局，各占一半空间
        self.hBoxLayout.addWidget(self.leftCard, 1)
        self.hBoxLayout.addWidget(self.rightContainer, 1)
