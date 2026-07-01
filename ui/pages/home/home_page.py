from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from qfluentwidgets import SubtitleLabel, TitleLabel, BodyLabel, PushButton, PrimaryPushButton, CardWidget, CheckBox, IndeterminateProgressBar, ProgressBar, ListWidget, ToolTipFilter, ToolTipPosition, InfoBar, InfoBarPosition
from ui.charts.line_chart.line_chart_page import LineChartPage
from ui.charts.trend_chart.trend_chart_page import TrendChartPage


class HomePage(QFrame):
    """主页页面 - 通过信号与逻辑层通信，不直接引用 DeviceManager"""

    def __init__(self, parent=None, signals=None, resolve_device_name=None):
        super().__init__(parent)
        self.parent = parent
        self.signals = signals
        # 依赖注入：接收设备名称解析回调，避免直接引用 DeviceManager
        self._resolve_name = resolve_device_name or (lambda addr, name: name if name and name.strip() else addr)
        self.setObjectName("homePage")
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 20, 20, 20)
        self.hBoxLayout.setSpacing(20)

        self.leftCard = CardWidget(self)
        self.leftLayout = QVBoxLayout(self.leftCard)
        self.leftLayout.setContentsMargins(20, 20, 20, 20)
        self.leftLayout.setSpacing(12)

        self.leftTitle = TitleLabel("设备连接")
        self.leftSubtitle = SubtitleLabel("扫描并连接您的心率监测设备")
        self.leftLayout.addWidget(self.leftTitle)
        self.leftLayout.addWidget(self.leftSubtitle)

        self.scanText = BodyLabel("设备扫描")
        self.leftLayout.addWidget(self.scanText)

        self.checkBox = CheckBox("自动筛选心率设备（这可能会大幅增加扫描时间）")
        self.checkBox.setToolTip("开启后，仅显示支持心率监测的设备。\n适合不赶时间并对你的设备不太了解的人使用。\n此功能会延长一到两倍的扫描时间。\n默认关闭")
        self.checkBox.installEventFilter(ToolTipFilter(self.checkBox, showDelay=300, position=ToolTipPosition.TOP))
        self.leftLayout.addWidget(self.checkBox)

        self.scanButton = PrimaryPushButton("扫描设备")
        self.scanButton.clicked.connect(lambda: self.signals.scan_requested.emit(self.checkBox.isChecked()))
        self.leftLayout.addWidget(self.scanButton)

        self.indeterminateBar = IndeterminateProgressBar(start=False)
        self.indeterminateBar.hide()

        self.progressBar = ProgressBar()
        self.progressBar.setValue(100)

        self.leftLayout.addWidget(self.indeterminateBar)
        self.leftLayout.addWidget(self.progressBar)

        self.connectionText = BodyLabel("设备连接")
        self.leftLayout.addWidget(self.connectionText)

        self.listWidget = ListWidget()
        self.listWidget.setSelectRightClickedRow(True)

        self.leftLayout.addWidget(self.listWidget)

        from qfluentwidgets import CaptionLabel
        self.infoLabel = CaptionLabel("为提升您的使用体验，程序会在本地缓存设备名称。")
        self.infoLabel.setStyleSheet("color: gray;")
        self.leftLayout.addWidget(self.infoLabel)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(10)

        self.connectButton = PushButton("连接设备")
        self.connectButton.setEnabled(False)
        self.connectButton.clicked.connect(self._on_connect_clicked)

        self.disconnectButton = PushButton("断开连接")
        self.disconnectButton.setEnabled(False)
        self.disconnectButton.clicked.connect(lambda: self.signals.disconnect_requested.emit())

        self.buttonLayout.addWidget(self.connectButton)
        self.buttonLayout.addWidget(self.disconnectButton)

        self.leftLayout.addLayout(self.buttonLayout)

        self.rightContainer = QFrame(self)
        self.rightContainerLayout = QVBoxLayout(self.rightContainer)
        self.rightContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.rightContainerLayout.setSpacing(20)

        self.rightTopCard = CardWidget(self.rightContainer)
        self.rightTopLayout = QVBoxLayout(self.rightTopCard)
        self.rightTopLayout.setContentsMargins(0, 0, 0, 0)

        self.lineChartPage = LineChartPage()
        self.rightTopLayout.addWidget(self.lineChartPage)

        self.rightBottomCard = CardWidget(self.rightContainer)
        self.rightBottomLayout = QVBoxLayout(self.rightBottomCard)
        self.rightBottomLayout.setContentsMargins(0, 0, 0, 0)

        self.trendChartPage = TrendChartPage()
        self.rightBottomLayout.addWidget(self.trendChartPage)

        self.rightContainerLayout.addWidget(self.rightTopCard, 1)
        self.rightContainerLayout.addWidget(self.rightBottomCard, 1)

        self.hBoxLayout.addWidget(self.leftCard, 1)
        self.hBoxLayout.addWidget(self.rightContainer, 1)

        if self.signals:
            self.signals.device_list_cleared.connect(self._clear_device_list)
            self.signals.device_found.connect(self._on_device_found)
            self.signals.device_updated.connect(self._on_device_updated)
            self.signals.ui_scan_state_changed.connect(self._on_scan_state_changed)
            self.signals.ui_progress_state_changed.connect(self._on_progress_state_changed)
            self.signals.ui_connect_state_changed.connect(self._on_connect_state_changed)
            self.signals.ui_list_enabled_changed.connect(self.listWidget.setEnabled)
            self.signals.ui_checkbox_enabled_changed.connect(self.checkBox.setEnabled)
            self.signals.heart_rate_updated.connect(self._on_heart_rate_updated)
            self.signals.connection_status_changed.connect(self._on_connection_status_changed)
            self.signals.info_bar_requested.connect(self._on_info_bar_requested)

    def _on_connect_clicked(self):
        selected = self._get_selected_text()
        self.signals.connect_requested.emit(selected)

    def _get_selected_text(self):
        if self.listWidget.currentRow() >= 0:
            return self.listWidget.item(self.listWidget.currentRow()).text()
        return ""

    def _clear_device_list(self):
        self.listWidget.clear()

    def _get_device_display_text(self, address, name):
        return self._resolve_name(address, name)

    def _on_device_found(self, device_info):
        address = device_info.address
        display_text = self._get_device_display_text(address, device_info.name)

        self.listWidget.addItem(display_text)
        self._sort_device_list()
        self.connectButton.setEnabled(True)

    def _on_device_updated(self, device_info):
        address = device_info.address
        current_display_text = self._get_device_display_text(address, device_info.name)

        for i in range(self.listWidget.count()):
            item_text = self.listWidget.item(i).text()
            if address in item_text or item_text == current_display_text:
                if item_text != current_display_text:
                    self.listWidget.item(i).setText(current_display_text)
                    self._sort_device_list()
                break

    def _sort_device_list(self):
        items = []
        count = self.listWidget.count()

        for i in range(count):
            item = self.listWidget.item(i)
            if item:
                try:
                    text = item.text()
                    items.append((text, item))
                except Exception:
                    pass

        def sort_key(item_tuple):
            try:
                text, item = item_tuple
                is_mac_only = ':' in text and len(text) == 17
                return (is_mac_only, text)
            except Exception:
                return (True, "")

        sorted_items = sorted(items, key=sort_key)

        self.listWidget.clear()

        for text, item in sorted_items:
            try:
                self.listWidget.addItem(text)
            except Exception:
                pass

    def _on_scan_state_changed(self, enabled, text):
        self.scanButton.setEnabled(enabled)
        self.scanButton.setText(text)

    def _on_progress_state_changed(self, indeterminate_visible, progress_visible):
        if indeterminate_visible:
            self.indeterminateBar.show()
            self.indeterminateBar.start()
        else:
            self.indeterminateBar.stop()
            self.indeterminateBar.hide()

        if progress_visible:
            self.progressBar.setCustomBarColor(QColor(0, 159, 170), QColor(0, 130, 140))
            self.progressBar.setValue(100)
            self.progressBar.show()
        else:
            self.progressBar.hide()

    def _on_connect_state_changed(self, connect_enabled, disconnect_enabled):
        self.connectButton.setEnabled(connect_enabled)
        self.disconnectButton.setEnabled(disconnect_enabled)

    def _on_heart_rate_updated(self, heart_rate):
        if hasattr(self.lineChartPage, 'chart'):
            chart = self.lineChartPage.chart
            chart.add_value(heart_rate)

            if hasattr(self.lineChartPage, 'top_right_label') and hasattr(self.lineChartPage, 'bottom_right_label'):
                if hasattr(chart, 'MAX_Y') and hasattr(chart, 'MIN_Y'):
                    self.lineChartPage.top_right_label.setText(f"{chart.MAX_Y}")
                    self.lineChartPage.bottom_right_label.setText(f"{chart.MIN_Y}")
                else:
                    self.lineChartPage.top_right_label.setText("200")
                    self.lineChartPage.bottom_right_label.setText("0")

        if hasattr(self, 'trendChartPage'):
            self.trendChartPage.update_heart_rate(heart_rate)

    def _on_connection_status_changed(self, status):
        if "设备连接成功" in status:
            if hasattr(self.lineChartPage, 'chart'):
                self.lineChartPage.chart.set_receiving_state(True)
            self.connectionText.setText("设备已连接")
        elif "设备已断开连接" in status or "已断开连接" in status:
            if hasattr(self.lineChartPage, 'chart'):
                self.lineChartPage.chart.set_receiving_state(False)
            self.connectionText.setText("设备已断开连接")
        elif "请先连接设备" in status:
            self.connectionText.setText("请先连接设备")
        else:
            self.connectionText.setText(status)

        if "设备连接成功" in status:
            self.lineChartPage.right_label.setText("已连接")
        elif "设备已断开连接" in status or "请先连接设备" in status:
            self.lineChartPage.right_label.setText("请先连接设备")

    def _on_info_bar_requested(self, info_type, title, content):
        parent = self.window()
        if info_type == "warn":
            InfoBar.warning(title=title, content=content, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif info_type == "error":
            InfoBar.error(title=title, content=content, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=5000, parent=parent)
        elif info_type == "info":
            InfoBar.info(title=title, content=content, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif info_type == "success":
            InfoBar.success(title=title, content=content, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
