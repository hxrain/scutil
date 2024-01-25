def win32_console_title(title):
    import ctypes
    # 获取kernel32.dll模块
    kernel32 = ctypes.windll.kernel32

    # 定义SetConsoleTitle函数原型
    SetConsoleTitle = kernel32.SetConsoleTitleW
    SetConsoleTitle.argtypes = [ctypes.c_wchar_p]

    try:
        # 调用SetConsoleTitle函数设置控制台标题
        SetConsoleTitle(title)
        return ''
    except Exception as e:
        return str(e)


def win32_console_handle():
    import ctypes
    kernel32 = ctypes.windll.kernel32
    GetConsoleWindow = kernel32.GetConsoleWindow
    GetConsoleWindow.argtypes = []

    try:
        return GetConsoleWindow()
    except Exception as e:
        return str(e)


def win32_window_position(handle, x, y, w, h):
    import ctypes
    dll = ctypes.windll.user32
    SetWindowPos = dll.SetWindowPos
    SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

    try:
        SetWindowPos(handle, 0, x, y, w, h, 0)
        return ''
    except Exception as e:
        return str(e)


def win32_screen_size(isfull=False, withDPI=False):
    """获取屏幕尺寸,isfull是否获取完整屏幕不带状态栏."""
    import ctypes
    dll = ctypes.windll.user32
    GetSystemMetrics = dll.GetSystemMetrics
    GetSystemMetrics.argtypes = [ctypes.c_int]

    try:
        ScaleFactor = 100 if not withDPI else ctypes.windll.shcore.GetScaleFactorForDevice(0)
    except Exception as e:
        ScaleFactor = 100

    if isfull:
        mw = 0
        mh = 1
    else:
        mw = 16
        mh = 17

    try:
        w = (GetSystemMetrics(mw) * ScaleFactor) // 100
        h = (GetSystemMetrics(mh) * ScaleFactor) // 100
        return w, h
    except Exception as e:
        return str(e)
