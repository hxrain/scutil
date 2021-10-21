from tkinter import *
from tkinter import ttk

# 屏蔽暂时不使用的代码,否则会导致打包后的exe达到500M
'''
from PIL import Image, ImageTk
def make_image(w=1, h=1, c=0xFFFFFF):
    """生成UI使用的空图像,便于进行像素宽高模式调整"""
    img = Image.new('RGB', (w, h), c)
    return ImageTk.PhotoImage(img)
'''


def center_window(root, width, height):
    """设定窗口的尺寸,并进行屏幕居中"""
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    root.geometry(size)
    root.update()


def num_limit(min, max, val):
    """对val进行限定,不能小于min,不能大于max"""
    if val < min:
        return min
    if val > max:
        return max
    return val


def make_tooltip(widget, text):
    """在指定的控件上,创建tip提示"""

    class ToolTip(object):
        def __init__(self, widget, msg):
            self.widget = widget
            self.msg = msg
            self.tipwindow = None

        def show(self, event):
            "Display text in tooltip window"
            if self.tipwindow or not self.msg:
                return
            # 得到目标控件的坐标范围
            x, y, _cx, _cy = self.widget.bbox("insert")
            # 计算tip窗口应该出现的位置
            nx = x + self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            ny = y + self.widget.winfo_rooty() + self.widget.winfo_height()

            # 创建tip顶层窗口
            self.tipwindow = Toplevel(self.widget)
            self.tipwindow.overrideredirect(1)  # 隐藏窗口外壳

            # 在tip窗口内创建文本标签
            label = Label(self.tipwindow, text=self.msg, justify=LEFT,
                          background="#ffffe0", relief=SOLID, borderwidth=1)
            label.pack(ipadx=1)
            # 控制tip不要超过屏幕可见范围
            if nx + self.tipwindow.winfo_reqwidth() > self.tipwindow.winfo_screenwidth():
                nx = self.tipwindow.winfo_screenwidth() - self.tipwindow.winfo_reqwidth()
            self.tipwindow.geometry("+%d+%d" % (nx, ny))  # 调整窗口位置

        def hide(self, event):
            if self.tipwindow:
                self.tipwindow.destroy()
                self.tipwindow = None

    toolTip = ToolTip(widget, text)
    widget.bind('<Enter>', toolTip.show)
    widget.bind('<Leave>', toolTip.hide)


class memo_t:
    """带有双向滚动条的文本框"""

    def __init__(self, parent,scrx=True):
        # 背景容器
        self.ui_frame = ttk.Frame(parent)
        self.ui_frame.pack()
        # 文本框,最后布局,优先计算滚动条的布局
        self.ui_txt = Text(self.ui_frame, wrap=None, relief=GROOVE)
        # 垂直滚动条
        self.ui_scrbar_y = Scrollbar(self.ui_frame, command=self.ui_txt.yview, orient=VERTICAL)
        self.ui_scrbar_y.pack(side=RIGHT, fill=Y)

        # 水平滚动条
        if scrx:
            self.ui_scrbar_x = Scrollbar(self.ui_frame, command=self.ui_txt.xview, orient=HORIZONTAL)
            self.ui_scrbar_x.pack(side=BOTTOM, fill=X)
            self.ui_txt.config(xscrollcommand=self.ui_scrbar_x.set)
        # 文本框绑定滚动条
        self.ui_txt.config(yscrollcommand=self.ui_scrbar_y.set)

        # 文本框布局
        self.ui_txt.pack(fill=BOTH, expand=True)

    def root(self):
        """根容器"""
        return self.ui_frame


def ui_value_set(w, v):
    """给控件w设置值v"""
    if isinstance(w, Entry) or isinstance(w, Text):
        w.delete(0, END)
        w.insert(0, v)
    elif isinstance(w, ttk.Combobox):
        w.set(v)
    elif isinstance(w, memo_t):
        w.ui_txt.delete('1.0', END)
        w.ui_txt.insert('1.0', v)
    else:
        print('unknown widget type! %s' % type(w).__name__)


def ui_value_get(w):
    if isinstance(w, Entry):
        return w.get()
    elif isinstance(w, Text):
        return w.get(0, END)
    elif isinstance(w, ttk.Combobox):
        return w.get()
    elif isinstance(w, memo_t):
        return w.ui_txt.get('1.0', END)
    else:
        return None
