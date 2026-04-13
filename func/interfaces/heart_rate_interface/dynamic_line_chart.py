from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath
from PyQt6.QtWidgets import QWidget
from collections import deque
import math


class DynamicLineChart(QWidget):
    """动态折线图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 常量定义
        self.GRID_SPACE = 10  # 网格间隔
        self.MOVE_STEP = 1    # 移动步长（能够被间隔整除）
        self.MAX_Y = 200      # Y轴最大值（心率最大刻度）
        self.MIN_Y = 0        # Y轴最小值
        
        # 变量初始化
        self.grid_xp_arr = []  # 网格竖线X坐标数组
        self.point_lst = []     # 点坐标数组
        self.point_values = []  # 每个点对应的原始值（用于等比例缩放）
        self.yp_queue = deque() # 数值队列
        self.x_offset = 0       # 网格偏移量
        self.current_value = 0  # 当前数值
        
        # 自动调节Y轴范围的变量
        self.value_history = deque(maxlen=40)  # 存储最近40个值用于计算范围
        self.auto_adjust_enabled = True        # 是否启用自动调节
        self.min_range = 30                     # 最小范围，确保变化明显
        self.padding_ratio = 0.10               # 上余量比例
        
        # 原始数值历史记录（保存所有点的原始值，用于等比例缩放）
        self.raw_values = deque(maxlen=100)     # 存储最近100个原始值
        
        # 移除平滑过渡，直接更新
        self.target_max_y = 200                 # 目标MAX_Y
        
        # 平均心率相关变量
        self.average_heart_rate = 0             # 当前平均心率
        self.average_data_points = deque(maxlen=100)  # 用于计算平均值的数据点
        self.MIN_POINTS_FOR_AVERAGE = 5         # 计算平均值所需的最小点数
        
        # 初始化Y轴范围
        self.MIN_Y = 0
        self.MAX_Y = 200
        
        # 设置最小高度
        self.setMinimumHeight(180)
        
        # 初始化数据
        self._init_data()
        
        # 接收数据状态标志
        self.is_receiving_data = False
        
        # 设置定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.draw_chart)
        self.timer.start(500)  # 500ms 刷新一次，约 2fps
    
    def set_receiving_state(self, is_receiving):
        """设置接收数据状态"""
        self.is_receiving_data = is_receiving
    
    def _init_data(self):
        """初始化数据结构"""
        # 初始化坐标点个数为宽/步长+1
        point_count = self.width() // self.MOVE_STEP + 1
        self.point_lst = []
        self.point_values = []
        
        # 初始化坐标点为X轴基线位置
        for i in range(point_count):
            point = QPoint(i * self.MOVE_STEP, self.height())
            self.point_lst.append(point)
            self.point_values.append(0)  # 初始值为0
    
    def add_value(self, value):
        """添加新的数值到队列"""
        self.yp_queue.append(value)
        # 添加到历史记录用于自动调节Y轴范围
        self.value_history.append(value)
        # 保存原始值用于等比例缩放
        self.raw_values.append(value)
        # 添加到平均心率计算队列
        self.average_data_points.append(value)
        # 计算平均心率
        self._calculate_average_heart_rate()
    
    def _calculate_average_heart_rate(self):
        """计算平均心率，从5个点开始计算"""
        if len(self.average_data_points) < self.MIN_POINTS_FOR_AVERAGE:
            self.average_heart_rate = 0
            return
        
        # 计算平均值
        self.average_heart_rate = sum(self.average_data_points) / len(self.average_data_points)
    
    def _update_y_range(self):
        """根据所有可见数据点更新Y轴范围，确保所有点都不冲顶"""
        if not self.auto_adjust_enabled:
            self.target_max_y = 200
            self.MAX_Y = self.target_max_y
            self._recalculate_all_points()
            return
        
        # 获取所有可见数据点（包括历史记录和当前显示的点）
        all_visible_values = []
        
        # 1. 添加当前显示在图表上的所有点的值
        if len(self.point_values) > 0:
            all_visible_values.extend(self.point_values)
        
        # 2. 添加原始值历史记录
        if len(self.raw_values) > 0:
            all_visible_values.extend(self.raw_values)
        
        # 3. 添加数值队列中的待显示值
        if len(self.yp_queue) > 0:
            all_visible_values.extend(self.yp_queue)
        
        # 4. 如果数据点不足，使用默认范围
        if len(all_visible_values) < 5:
            self.target_max_y = 200
            self.MAX_Y = self.target_max_y
            self._recalculate_all_points()
            return
        
        # 计算所有可见数据点的最大值和平均值
        max_val = max(all_visible_values)
        avg_val = self.average_heart_rate if self.average_heart_rate > 0 else sum(all_visible_values) / len(all_visible_values)
        
        # 黄金比例（0.618）：平均线应该在总高度的0.618位置
        golden_ratio = 0.618
        golden_based_max = avg_val / golden_ratio
        
        # 确保目标最大值至少比实际最大值大5%，避免点冲顶
        # 增加安全余量到10%，确保所有点都不会冲顶
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
        
        # 直接更新MAX_Y，不使用平滑过渡
        self.MAX_Y = self.target_max_y
        
        # 重新计算所有点的Y坐标，确保每个点都显示正确
        self._recalculate_all_points()
    

    
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
    
    def _recalculate_all_points(self):
        """重新计算所有点的Y坐标（当MAX_Y变化时调用）"""
        if len(self.point_values) == 0:
            return
        
        # 使用point_values中保存的原始值重新计算所有点的Y坐标
        for i in range(len(self.point_values)):
            y_pos = self._normalize_value_to_y(self.point_values[i])
            self.point_lst[i].setY(y_pos)
    
    def draw_chart(self):
        """绘制折线图（优化版本，确保流畅性）"""
        # 仅在接收数据状态时执行刷新
        if not self.is_receiving_data:
            return
        
        # 偏移量计算
        self.x_offset += 1
        if self.x_offset == self.GRID_SPACE // self.MOVE_STEP:
            self.x_offset = 0
        
        # 如果队列中有新的Y坐标点，则输出
        if len(self.yp_queue) > 0:
            self.current_value = self.yp_queue.popleft()
        
        # 每执行一次函数，Y坐标向前移动一位
        for i in range(len(self.point_lst) - 1):
            self.point_lst[i].setY(self.point_lst[i + 1].y())
            # 同步更新point_values
            self.point_values[i] = self.point_values[i + 1]
        
        # 按比例更新最后一位坐标点
        if len(self.point_lst) > 0:
            last_index = len(self.point_lst) - 1
            self.point_lst[last_index].setX(self.width())
            
            # 使用优化的归一化方法计算Y坐标
            y_pos = self._normalize_value_to_y(self.current_value)
            self.point_lst[last_index].setY(y_pos)
            # 保存当前值到point_values
            self.point_values[last_index] = self.current_value
        
        # 重新计算Y轴范围，确保所有可见点都不冲顶
        # 当最大值点离开视线时，Y轴范围会相应缩小
        self._update_y_range()
        
        # 触发重绘
        self.update()
    
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
        
        # 绘制网格
        self._draw_grid(painter, width, height)
        
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
    
    def _draw_grid(self, painter, width, height):
        """绘制网格背景"""
        # 设置网格线颜色（深红色）
        pen = QPen(QColor(220, 220, 220))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 初始化网格竖线X坐标数组
        self.grid_xp_arr = []
        
        # 计算竖线数量，确保覆盖整个宽度
        grid_count = math.ceil(width / self.GRID_SPACE) + 1
        
        # 画竖线（根据偏移量实现动态效果）
        for i in range(grid_count):
            x_pos = self.GRID_SPACE * i - self.x_offset * self.MOVE_STEP
            self.grid_xp_arr.append(x_pos)
            painter.drawLine(int(x_pos), 0, int(x_pos), height)
        
        # 画横线
        for i in range(height // self.GRID_SPACE + 1):
            y_pos = self.GRID_SPACE * i
            painter.drawLine(0, y_pos, width, y_pos)
    
    def _draw_line(self, painter, width, height):
        """绘制折线和填充区域"""
        if len(self.point_lst) < 2:
            return
        

        
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
        
        # 设置填充颜色（半透明红色）
        fill_brush = QBrush(QColor(255,143,143,50))  # 50表示透明度
        painter.setBrush(fill_brush)
        painter.setPen(Qt.PenStyle.NoPen)  # 不绘制边框
        painter.drawPath(fill_path)
        
        # 设置折线颜色（深红色）
        pen = QPen(QColor(220, 9, 9))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 画笔移动到起点位置
        start_point = self.point_lst[0]
        # 连线各个点
        for i in range(len(self.point_lst) - 1):
            p1 = self.point_lst[i]
            p2 = self.point_lst[i + 1]
            painter.drawLine(p1, p2)

    def resizeEvent(self, event):
        """窗口大小改变时重新初始化数据"""
        super().resizeEvent(event)
        self._init_data()