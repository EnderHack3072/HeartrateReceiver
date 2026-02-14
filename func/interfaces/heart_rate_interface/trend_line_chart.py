from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt6.QtWidgets import QWidget
from collections import deque


class TrendLineChart(QWidget):
    """趋势折线图组件，数据添加时会逐渐被左右压扁"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 常量定义
        self.MAX_Y = 200      # Y轴最大值（心率最大刻度）
        self.MIN_Y = 0        # Y轴最小值
        
        # 变量初始化
        self.point_lst = []     # 点坐标数组
        self.point_values = []  # 每个点对应的原始值
        self.yp_queue = deque() # 数值队列
        self.current_value = 0  # 当前数值
        
        # 自动调节Y轴范围的变量
        self.auto_adjust_enabled = True        # 是否启用自动调节
        self.min_range = 30                     # 最小范围，确保变化明显
        self.padding_ratio = 0.10               # 上余量比例
        
        # 所有历史值（不限制长度，用于趋势显示）
        self.all_history_values = []           # 保存所有历史值
        self.display_points_count = 0           # 实际显示的点数
        self.max_display_points = 100           # 初始最大显示点数
        
        # 目标值和边界检查
        self.target_max_y = 200                 # 目标MAX_Y
        
        # 平均心率相关变量
        self.average_heart_rate = 0             # 当前平均心率
        self.MIN_POINTS_FOR_AVERAGE = 5         # 计算平均值所需的最小点数
        
        # 初始化Y轴范围
        self.MIN_Y = 0
        self.MAX_Y = 200
        
        # 设置最小高度
        self.setMinimumHeight(180)
        
        # 初始化数据
        self._init_data()
        
        # 设置定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.draw_chart)
        self.timer.start(500)  # 500ms 刷新一次，约 2fps
    
    def _init_data(self):
        """初始化数据结构"""
        # 初始化为空
        self.point_lst = []
        self.point_values = []
        self.all_history_values = []
        self.display_points_count = 0
    
    def add_value(self, value):
        """添加新的数值到队列"""
        self.yp_queue.append(value)
        # 保存到所有历史值中（不限制长度）
        self.all_history_values.append(value)
        # 计算平均心率（基于所有历史点）
        self._calculate_average_heart_rate()
    
    def _calculate_average_heart_rate(self):
        """计算平均心率，从5个点开始计算"""
        if len(self.all_history_values) < self.MIN_POINTS_FOR_AVERAGE:
            self.average_heart_rate = 0
            return
        
        # 计算所有历史点的平均值
        self.average_heart_rate = sum(self.all_history_values) / len(self.all_history_values)
    
    def _update_y_range(self):
        """根据所有历史数据更新Y轴范围，确保所有点都不冲顶"""
        if not self.auto_adjust_enabled:
            self.target_max_y = 200
            self.MAX_Y = self.target_max_y
            return
        
        # 获取所有历史数据
        all_values = self.all_history_values.copy()
        
        # 如果数据点不足，使用默认范围
        if len(all_values) < 5:
            self.target_max_y = 200
            self.MAX_Y = self.target_max_y
            return
        
        # 计算所有数据点的最大值和平均值
        max_val = max(all_values)
        avg_val = self.average_heart_rate if self.average_heart_rate > 0 else sum(all_values) / len(all_values)
        
        # 黄金比例（0.618）：平均线应该在总高度的0.618位置
        golden_ratio = 0.618
        golden_based_max = avg_val / golden_ratio
        
        # 确保目标最大值至少比实际最大值大10%，避免点冲顶
        safe_padding = max_val * 0.10  # 10%的安全余量
        safe_max = max_val + safe_padding
        
        # 取两者的最大值
        self.target_max_y = max(golden_based_max, safe_max)
        
        # 边界检查：确保范围在合理范围内
        self._check_range_bounds()
        
        # 四舍五入到最近的10（如144->150）
        self.target_max_y = round(self.target_max_y / 10) * 10
        
        # 最终边界检查
        self._check_range_bounds()
        
        # 直接更新MAX_Y
        self.MAX_Y = self.target_max_y
    
    def _check_range_bounds(self):
        """边界检查机制，防止极端缩放比例"""
        # 确保MIN_Y固定为0
        self.MIN_Y = 0
        
        # 确保MAX_Y至少为min_range
        if self.MAX_Y < self.min_range:
            self.MAX_Y = self.min_range
        
        if self.target_max_y < self.min_range:
            self.target_max_y = self.min_range
        
        # 确保MAX_Y不超过生理极限（心率一般不超过250）
        max_limit = 250
        if self.MAX_Y > max_limit:
            self.MAX_Y = max_limit
        
        if self.target_max_y > max_limit:
            self.target_max_y = max_limit
    
    def _normalize_value_to_y(self, value):
        """将数值归一化并转换为Y坐标（等比例缩放，MIN_Y固定为0）"""
        range_y = self.MAX_Y - self.MIN_Y
        
        # 边界检查：防止除零错误
        if range_y <= 0:
            range_y = self.min_range
        
        # 归一化到0-1范围
        normalized_value = (value - self.MIN_Y) / range_y
        
        # 限制在0-1范围内（防止超出边界）
        normalized_value = max(0.0, min(1.0, normalized_value))
        
        # 转换为Y坐标（垂直方向等比例）
        y_pos = self.height() - int(normalized_value * self.height())
        
        # 边界检查：确保Y坐标在可视区域内
        y_pos = max(0, min(self.height(), y_pos))
        
        return y_pos
    
    def draw_chart(self):
        """绘制趋势折线图，数据添加时会逐渐被左右压扁"""
        
        # 如果队列中有新的Y坐标点，则处理
        if len(self.yp_queue) > 0:
            self.current_value = self.yp_queue.popleft()
        
        # 更新Y轴范围
        self._update_y_range()
        
        # 重新计算所有点的坐标
        self._recalculate_all_points()
        
        # 触发重绘
        self.update()
    
    def _recalculate_all_points(self):
        """重新计算所有点的坐标，实现数据压缩效果"""
        if not self.all_history_values:
            return
        
        width = self.width()
        height = self.height()
        
        # 计算当前需要显示的点数
        total_points = len(self.all_history_values)
        self.display_points_count = total_points
        
        # 清空现有点
        self.point_lst = []
        self.point_values = []
        
        # 生成所有点的坐标
        for i in range(total_points):
            value = self.all_history_values[i]
            
            # 计算X坐标，确保两端贴到边缘
            if total_points == 1:
                # 只有一个点时，居中显示
                x_pos = width / 2
            else:
                # 线性映射：将0到total_points-1映射到0到width
                x_pos = (i / (total_points - 1)) * width
            
            # 计算Y坐标
            y_pos = self._normalize_value_to_y(value)
            
            self.point_lst.append(QPoint(int(x_pos), y_pos))
            self.point_values.append(value)
    
    def paintEvent(self, event):
        """绘制事件（双缓冲绘图）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取画布尺寸
        width = self.width()
        height = self.height()
        
        # 设置裁剪区域，限制在卡片范围内
        painter.setClipRect(0, 0, width, height)
        
        # 绘制浅红色背景
        painter.fillRect(0, 0, width, height, QColor(255, 255, 255))
        
        # 绘制折线
        self._draw_line(painter, width, height)
        
        # 绘制平均心率线
        self._draw_average_line(painter, width, height)
        
        # 绘制1px黑色边框
        border_pen = QPen(QColor(0, 0, 0))
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, width - 1, height - 1)
    
    def _draw_average_line(self, painter, width, height):
        """绘制平均心率线，1px深蓝色横线，并在右端显示数值"""
        if self.average_heart_rate == 0:
            return
        
        # 计算平均线的Y坐标
        average_y = self._normalize_value_to_y(self.average_heart_rate)
        
        # 深蓝色
        deep_blue = QColor(0, 60, 135)
        
        # 设置深蓝色1px线
        average_pen = QPen(deep_blue)
        average_pen.setWidth(1)
        painter.setPen(average_pen)
        
        # 绘制横线
        painter.drawLine(0, average_y, width, average_y)
        
        # 绘制平均心率数值（线的上方，右对齐）
        painter.setPen(deep_blue)
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        
        # 格式化平均心率数值（添加前缀"平均 "，四舍五入为整数）
        avg_text = f"平均 {round(self.average_heart_rate)}"
        
        # 获取文本宽度
        text_rect = painter.boundingRect(0, 0, 100, 20, Qt.AlignmentFlag.AlignRight, avg_text)
        text_width = text_rect.width()
        
        # 计算文本位置：线的上方，右边缘与线的右边缘平齐
        text_x = width - text_width - 5  # 右对齐，距离边缘5px
        text_y = average_y - 5  # 线的上方，距离线5px
        
        painter.drawText(text_x, text_y, avg_text)
    
    def _draw_line(self, painter, width, height):
        """绘制折线和填充区域，与折线图配色保持一致"""
        if len(self.point_lst) < 2:
            return
        
        # 先绘制填充区域（半透明红色）
        # 创建填充路径
        fill_path = QPainterPath()
        fill_path.moveTo(self.point_lst[0].x(), self.point_lst[0].y())
        
        # 添加所有折线点
        for i in range(1, len(self.point_lst)):
            fill_path.lineTo(self.point_lst[i].x(), self.point_lst[i].y())
        
        # 闭合路径到底部
        fill_path.lineTo(width, height)
        fill_path.lineTo(0, height)
        fill_path.closeSubpath()
        
        # 设置填充颜色（半透明红色），与折线图保持一致
        fill_brush = QBrush(QColor(255, 143, 143, 50))  # 50表示透明度
        painter.setBrush(fill_brush)
        painter.setPen(Qt.PenStyle.NoPen)  # 不绘制边框
        painter.drawPath(fill_path)
        
        # 设置折线颜色（深红色），与折线图保持一致
        pen = QPen(QColor(220, 9, 9))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 连线各个点
        for i in range(len(self.point_lst) - 1):
            p1 = self.point_lst[i]
            p2 = self.point_lst[i + 1]
            painter.drawLine(p1, p2)

    def resizeEvent(self, event):
        """窗口大小改变时重新计算所有点的坐标"""
        super().resizeEvent(event)
        # 重新计算所有点的坐标
        self._recalculate_all_points()