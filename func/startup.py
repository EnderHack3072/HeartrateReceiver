import base64
import ctypes
from io import BytesIO
import win32gui
import win32api
import win32con
import win32ui
from PIL import Image, ImageWin
from func.resources import STARTUP_PNG


def show_system_splash(pre_aware_width=None):
    """创建win32gui系统级轻量闪屏（无QApp依赖，立即显示）

    Args:
        pre_aware_width: 设置DPI感知前的屏幕虚拟宽度，用于计算缩放倍数
    """
    try:
        image_data = base64.b64decode(STARTUP_PNG)
        image_stream = BytesIO(image_data)
        img = Image.open(image_stream)

        # 通过感知前后的屏幕宽度比值计算DPI缩放倍数
        # 不依赖任何DPI API，纯数学计算，最可靠
        scale = 1.0
        if pre_aware_width:
            physical_width = win32api.GetSystemMetrics(0)
            if physical_width and physical_width > pre_aware_width:
                scale = physical_width / pre_aware_width

        print(f"[Splash] DPI scale: {scale} (pre_aware={pre_aware_width}, "
              f"physical={physical_width if pre_aware_width else 'N/A'})")

        if scale != 1.0:
            new_width = max(1, int(img.width * scale))
            new_height = max(1, int(img.height * scale))
            img = img.resize((new_width, new_height), Image.LANCZOS)

        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        width, height = img.size

        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        hwnd = win32gui.CreateWindow(
            "STATIC",
            "Splash",
            win32con.WS_POPUP | win32con.WS_VISIBLE,
            x, y, width, height,
            0, 0, 0, None
        )

        if not hwnd:
            print("Error creating splash window!")
            return None

        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )

        hdc = win32gui.GetDC(hwnd)
        dc = win32ui.CreateDCFromHandle(hdc)

        mem_dc = dc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(dc, width, height)
        mem_dc.SelectObject(bmp)

        dib = ImageWin.Dib(img)
        dib.draw(mem_dc.GetHandleOutput(), (0, 0, width, height))

        dc.BitBlt((0, 0), (width, height), mem_dc, (0, 0), win32con.SRCCOPY)

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
    import sys
    import ctypes

    def is_single_instance():
        """检测是否只有一个实例在运行"""
        if sys.platform == 'win32':
            mutex_name = "Global\\HeartRateMonitorMutex"
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()

            if last_error == 183:
                try:
                    import win32gui
                    import win32con

                    def enum_windows_callback(hwnd, lParam):
                        window_title = win32gui.GetWindowText(hwnd)
                        if "心率监测器" in window_title:
                            if win32gui.IsIconic(hwnd):
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                            return False
                        return True

                    win32gui.EnumWindows(enum_windows_callback, None)
                except Exception as e:
                    print(f"激活现有窗口失败: {e}")
                return False
            return True
        return True

    if not is_single_instance():
        print("程序已经在运行，正在切换到前台...")
        sys.exit(0)


def go():
    # 必须在 DPI 感知前抓取虚拟屏幕宽度，用于后续计算缩放倍数
    pre_aware_width = win32api.GetSystemMetrics(0)

    # 主动声明DPI感知，防止Windows虚拟缩放导致闪屏尺寸异常
    # 必须在创建任何窗口前调用，保证与后续PyQt6的DPI行为一致
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    global syshwnd
    syshwnd = show_system_splash(pre_aware_width)
    startup_check()
