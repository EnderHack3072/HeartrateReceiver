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
    startup_check()
