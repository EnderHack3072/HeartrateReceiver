import base64
from io import BytesIO
import win32gui
import win32api
import win32con
import win32ui
from PIL import Image, ImageWin
from func.resources import STARTUP_PNG


def show_system_splash():
    """创建win32gui系统级轻量闪屏（无QApp依赖，立即显示）"""
    try:
        # 解码base64字符串
        image_data = base64.b64decode(STARTUP_PNG)
        # 创建BytesIO对象
        image_stream = BytesIO(image_data)
        # 加载图片
        img = Image.open(image_stream)
        
        # 转换为RGB格式（避免透明度问题）
        if img.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            # 粘贴图片，使用alpha通道作为蒙版
            background.paste(img, mask=img.split()[3])
            img = background
        
        # 获取图片尺寸
        width, height = img.size
        
        # 计算屏幕中心位置
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 创建窗口（使用预定义的STATIC类）
        hwnd = win32gui.CreateWindow(
            "STATIC",  # 使用预定义的STATIC类
            "Splash",
            win32con.WS_POPUP | win32con.WS_VISIBLE,  # 无标题栏窗口
            x, y, width, height,
            0, 0, 0, None
        )
        
        if not hwnd:
            print("Error creating splash window!")
            return None
        
        # 设置窗口始终置顶
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,  # 置顶
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE  # 不改变位置和大小
        )
        
        # 获取设备上下文
        hdc = win32gui.GetDC(hwnd)
        dc = win32ui.CreateDCFromHandle(hdc)
        
        # 创建兼容DC和位图
        mem_dc = dc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(dc, width, height)
        mem_dc.SelectObject(bmp)
        
        # 绘制图片
        dib = ImageWin.Dib(img)
        dib.draw(mem_dc.GetHandleOutput(), (0, 0, width, height))
        
        # 复制到位图
        dc.BitBlt((0, 0), (width, height), mem_dc, (0, 0), win32con.SRCCOPY)
        
        # 释放资源
        mem_dc.DeleteDC()
        dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        
        print("splash show")
        return hwnd
        
    except Exception as e:
        print(f"Error creating splash: {e}")
        import traceback
        traceback.print_exc()
        return None

def close_system_splash(hwnd):
    """关闭系统级闪屏"""
    if hwnd:
        win32gui.DestroyWindow(hwnd)

def startup_check():
    # 单实例检测
    import sys
    import ctypes

    def is_single_instance():
        """检测是否只有一个实例在运行"""
        if sys.platform == 'win32':
            # 创建命名互斥体
            mutex_name = "Global\\HeartRateMonitorMutex"
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()
            
            # 如果互斥体已存在，说明已有实例在运行
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                # 尝试找到并激活现有窗口
                try:
                    import win32gui
                    import win32con
                    
                    def enum_windows_callback(hwnd, lParam):
                        window_title = win32gui.GetWindowText(hwnd)
                        if "心率监测器" in window_title:
                            # 显示窗口（如果最小化）
                            if win32gui.IsIconic(hwnd):
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            # 激活窗口
                            win32gui.SetForegroundWindow(hwnd)
                            return False  # 停止枚举
                        return True
                    
                    win32gui.EnumWindows(enum_windows_callback, None)
                except Exception as e:
                    print(f"激活现有窗口失败: {e}")
                return False
            return True
        return True

    # 检查是否已有实例在运行
    if not is_single_instance():
        print("程序已经在运行，正在切换到前台...")
        sys.exit(0)

def go():
    global syshwnd
    syshwnd = show_system_splash()
    startup_check()
