from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import time
import bisect
import math

# 屏蔽暂时不使用的代码,否则会导致打包后的exe达到500M
'''
from PIL import Image, ImageTk
def make_image(w=1, h=1, c=0xFFFFFF):
    """生成UI使用的空图像,便于进行像素宽高模式调整"""
    img = Image.new('RGB', (w, h), c)
    return ImageTk.PhotoImage(img)
'''


def parse_geometry_size(geo):
    """解析几何位置信息,得到(宽,高,x,y)"""
    m = re.findall(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geo)
    if len(m) == 0:
        return None
    r = m[0]
    return int(r[0]), int(r[1]), int(r[2]), int(r[3])


def calc_geometry_center(geo):
    """计算几何尺寸的中心坐标"""
    if isinstance(geo, str):
        geo = parse_geometry_size(geo)
        if geo is None:
            return None
    return geo[2] + geo[0] // 2, geo[3] + geo[1] // 2


def calc_distance(x1, y1, x2, y2):
    """计算两个点之间的距离"""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def center_window(root, width, height):
    """设定窗口的尺寸,并进行屏幕居中"""
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    root.geometry(size)
    root.update()


def center_widget(root, widget):
    """将已有的widget相对于root主容器进行居中显示"""
    widget.update()
    root.update()
    if root.state() == 'zoomed':
        cx = root.winfo_screenwidth() // 2
        cy = root.winfo_screenheight() // 2
    else:
        cx, cy = calc_geometry_center(root.geometry())
    x = cx - widget.winfo_reqwidth() // 2
    y = cy - widget.winfo_reqheight() // 2
    widget.geometry('+%d+%d' % (int(x), int(y)))


def num_limit(min, max, val):
    """对val进行限定,不能小于min,不能大于max"""
    if val < min:
        return min
    if val > max:
        return max
    return val


def tabs_current_tab(tabs):
    """获取ttk.Notebook的当前tab页对象"""
    idx = tabs.select()
    return tabs.nametowidget(idx)


def tabs_current_idx(tabs):
    """获取ttk.Notebook的当前tab页对象"""
    idx = tabs.select()
    return tabs.index(idx)


class ToolTip(object):
    def __init__(self, widget, msg, evt_pos=False):
        self.widget = widget  # 父容器控件
        self.msg = msg  # 待显示的消息
        self.evt_pos = evt_pos  # 是否依据事件位置进行弹出
        self.showing = None  # 是否正在被显示

        # 创建tip顶层窗口
        self.tipwindow = Toplevel(self.widget)
        self.tipwindow.overrideredirect(1)  # 隐藏窗口外壳

        # 在tip窗口内创建文本标签
        self.label = Label(self.tipwindow, text=self.msg, justify=LEFT,
                           background="#ffffe0", relief=SOLID, borderwidth=1)
        self.label.pack(ipadx=1)
        self.hide(None)
        # 获取消息的回调函数
        self.msg_cb = None

    def show(self, event, msg=None):
        "Display text in tooltip window"
        if msg is not None:
            # 明确给出了显示内容,进行更新
            self.msg = msg
            self.label.config(text=self.msg)
        elif self.msg_cb:
            # 存在内容生成回调函数,进行更新
            self.msg = self.msg_cb(event)
            self.label.config(text=self.msg)

        if self.evt_pos:
            # 按鼠标位置进行tip显示
            nx = event.x_root + 4
            ny = event.y_root + 4
            # time.sleep(0.01)  # 为了避免事件反复发生,怀疑是tk的bug
        else:
            # 按目标控件的坐标范围进行tip显示
            x, y, _cx, _cy = self.widget.bbox("insert")
            nx = x + self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            ny = y + self.widget.winfo_rooty() + self.widget.winfo_height()

        # 限定tip不要超过屏幕可见范围
        if nx + self.tipwindow.winfo_reqwidth() > self.tipwindow.winfo_screenwidth():
            nx = self.tipwindow.winfo_screenwidth() - self.tipwindow.winfo_reqwidth()
        # 调整窗口位置
        self.tipwindow.geometry("+%d+%d" % (nx, ny))
        # 让tip窗口可见
        self.tipwindow.update()
        self.tipwindow.deiconify()
        self.showing = True

    def hide(self, *args):
        """隐藏tip窗口"""
        self.tipwindow.withdraw()
        self.showing = False


def event_handle_warp(fun, dat):
    """对事件处理函数进行额外数据绑定,返回包装后的函数"""

    def warp_func(event):
        """包装后的事件处理函数"""
        event.__dict__['usrdat'] = dat  # 给动态事件对象绑定闭包内的上值数据
        return fun(event)  # 再调用真正的事件处理函数

    return warp_func  # 返回包装后的事件处理函数


def make_tooltip(widget, text, evtpos=False):
    """在指定的控件上,创建tip提示,告知是否按鼠标事件位置进行显示"""
    toolTip = ToolTip(widget, text, evtpos)
    widget.bind('<Enter>', toolTip.show)
    widget.bind('<Leave>', toolTip.hide)


def tag_color(ui_txt, tag_name, fg=None, bg=None):
    """设定标签文本的前景色和背景色;默认清除."""
    if tag_name is None:
        return
    if fg is None and bg is None:
        ui_txt.tag_config(tag_name, foreground=None, background=None)
        return

    if fg is not None:
        ui_txt.tag_config(tag_name, foreground=fg)
    if bg is not None:
        ui_txt.tag_config(tag_name, background=bg)


def text_next_idx(ui_txt, idx):
    """计算文本框指定索引位置出的后一个字符索引"""
    if not idx:
        return '1.0'
    return ui_txt.index('%s +1 chars' % idx)


def tag_search_color(ui_txt, begin, cnt, color=None):
    """给文本框搜索结果着色,color为None则清除"""
    if not begin:
        return
    if isinstance(cnt, IntVar):
        cnt = cnt.get()
    end = ui_txt.index('%s +%d chars' % (begin, cnt))
    tagname = '_search_txttag_%s_%s' % (begin, end)
    if color is None:
        ui_txt.tag_delete(tagname)
    else:
        ui_txt.tag_add(tagname, begin, end)
        tag_color(ui_txt, tagname, color)


class TextTagTooltip_t:
    """对text文本框中的tag标签进行tip管理"""

    def __init__(self, ui_txt, msg_func=None):
        self.ui_txt = ui_txt  # 文本框控件
        self._msg_func = msg_func  # 消息生成函数
        self._tip = ToolTip(ui_txt.master, '', True)  # 提示窗控件
        self._tip.msg_cb = self._msg_cb  # 挂接消息生成回调函数
        self.ui_txt.bind('<Motion>', self._on_mouse_move)  # 绑定鼠标移动事件

    def _on_mouse_move(self, event):
        '''鼠标移动事件,主要是为了隐藏tip'''
        if not self._tip.showing:
            return

        # 得到tip窗口尺寸
        tipbox = parse_geometry_size(self._tip.tipwindow.geometry())
        # 计算tip窗口中心点
        cp = calc_geometry_center(tipbox)
        # 计算当前鼠标位置和tip窗口中心点的距离
        dis = calc_distance(cp[0], cp[1], event.x_root, event.y_root)
        # 如果距离过大则隐藏tip窗口
        if dis > 100 + tipbox[0] // 2:
            self._tip.hide()

    def _msg_cb(self, event):
        """转接外面的消息生成函数"""
        if self._msg_func is None:
            return event.usrdat
        return self._msg_func(event.usrdat)

    def tag_name(self, idx1, idx2):
        """根据tag坐标范围生成tag名字"""
        return '_txttag_%s_%s' % (idx1, idx2)

    def tag_tip(self, idx1, idx2, canRep=False):
        """根据tag坐标范围生成tag,并进行tip绑定"""
        if not canRep:
            ot1 = self.ui_txt.tag_names(idx1)
            ot2 = self.ui_txt.tag_names(idx2)
            if ot1 or ot2:
                return None

        tag_name = self.tag_name(idx1, idx2)  # 生成唯一名字
        tag_txt = self.ui_txt.get(idx1, idx2)  # 获取坐标范围内的文本

        self.ui_txt.tag_add(tag_name, idx1, idx2)  # 生成指定名字和范围的标签
        # 给标签挂载鼠标进出事件,进入事件的回调函数进行了值包装
        self.ui_txt.tag_bind(tag_name, '<Enter>', event_handle_warp(self._tip.show, tag_txt))
        self.ui_txt.tag_bind(tag_name, '<Leave>', self._tip.hide)
        return tag_name

    def tag_color(self, tag_name, fg=None, bg=None):
        """设定标签文本的前景色和背景色;默认清除."""
        tag_color(self.ui_txt, tag_name, fg, bg)

    def tag_clean(self, tag_name=None):
        """清除指定的标签,或全部标签."""
        if tag_name:
            self.ui_txt.tag_delete(tag_name)
        else:
            for tn in self.ui_txt.tag_names():
                self.ui_txt.tag_delete(tn)


class memo_t:
    """带有双向滚动条的文本框"""

    # 告知父容器parent,是否有水平滚动条scrx,是否为只读onlyrd
    def __init__(self, parent, scrx=False, onlyrd=False, fontsize=12, fontfamily='Consolas'):
        # 背景容器
        self.ui_frame = ttk.Frame(parent)
        self.ui_frame.pack()
        # 文本框,最后布局,优先计算滚动条的布局
        self.ui_txt = Text(self.ui_frame, wrap=NONE if scrx else None, relief=GROOVE, state=DISABLED if onlyrd else None)
        self.set_font(fontsize, fontfamily)
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

    def set_color(self, fg=None, bg=None):
        """设定文本的前景色和背景色;默认清除."""
        if fg is None and bg is None:
            self.ui_txt.config(foreground=None, background=None)
            return

        if fg is not None:
            self.ui_txt.config(foreground=fg)
        if bg is not None:
            self.ui_txt.config(background=bg)

    def set_font(self, size, family='Consolas'):
        """设置字体"""
        self.ui_txt.config(font=Font(size=size, family=family))

    def root(self):
        """根容器"""
        return self.ui_frame


def ui_value_set(w, v):
    """给控件w设置显示内容v"""
    if isinstance(w, Entry) or isinstance(w, Text):
        w.delete(0, END)
        w.insert(0, v)
    elif isinstance(w, ttk.Combobox):
        w.set(v)
    elif isinstance(w, memo_t):
        onlyrd = False
        if w.ui_txt['state'] == DISABLED:
            w.ui_txt['state'] = NORMAL
            onlyrd = True
        w.ui_txt.delete('1.0', END)
        w.ui_txt.insert('1.0', v)
        if onlyrd:
            w.ui_txt['state'] = DISABLED
    else:
        print('unknown widget type! %s' % type(w).__name__)


def ui_value_get(w):
    """取出控件的显示内容"""
    if isinstance(w, Entry):
        return w.get()
    elif isinstance(w, Text):
        return w.get('1.0', END)
    elif isinstance(w, ttk.Combobox):
        return w.get()
    elif isinstance(w, memo_t):
        return w.ui_txt.get('1.0', END)
    else:
        return None


class text_indexer_t:
    """tkinter/text控件行列坐标计算器"""

    def __init__(self, txt=None):
        self.lines = None
        self.length = None
        self.parse(txt)

    def parse(self, txt):
        """解析文本,得到分行索引"""
        """解析文本,"""
        self.lines = []
        segs = txt.split('\n')
        self.length = len(txt)
        for line_no, line_txt in enumerate(segs):
            offset = len(line_txt) + 1
            if line_no != 0:
                offset += self.lines[line_no - 1]
            self.lines.append(offset)

    def index(self, pos):
        """通过文本的线性字符位置,得到tk/text的行列坐标"""
        row = bisect.bisect_right(self.lines, pos)
        if row >= len(self.lines):
            return None

        if row == 0:
            col = pos
        else:
            col = pos - self.lines[row - 1]

        return '%d.%d' % (row + 1, col)