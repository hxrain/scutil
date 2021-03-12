"""
设计一个简单的box二分切割布局管理器,便于计算UI控件布局的范围.
从最初的box开始,每次切割都是新出现两个子box,上下或左右分布.
多次切分,最终生成一颗二叉树,每个叶子节点都代表了一个box空间.
    定位查询类型:
    'T'  # 上边box
    'B'  # 下边box
    'L'  # 左边box
    'R'  # 右边box
    分割动作类型:
    'H'  # 水平线分割,得到上下两个box
    'V'  # 垂直线分割,得到左右两个box

"""


def box_split(rect, op, sp):
    """对rect按op类型进行sp比例分割,得到两个新的rect"""

    def calc(a, b, sp):
        """计算数轴a,b两点间的分割点,sp为float时,分割按百分比;sp为int时分割按相对a的距离."""
        if isinstance(sp, float):
            return int(a + (b - a) * sp)
        else:
            return min(a + sp, b)

    if op == 'H':
        np = calc(rect[1], rect[3], sp)  # 水平线分割时,需要对top,bottom进行sp分割计算
        rect_1 = [rect[0], rect[1], rect[2], np]
        rect_2 = [rect[0], np, rect[2], rect[3]]
    else:
        np = calc(rect[0], rect[2], sp)  # 垂直线分割时,需要对left,right进行sp分割计算
        rect_1 = [rect[0], rect[1], np, rect[3]]
        rect_2 = [np, rect[1], rect[2], rect[3]]
    return rect_1, rect_2


class box:
    """布局使用的box对象,含有核心信息"""

    def __init__(self, parent):
        self.parent = parent
        self.rect = None  # 自身的矩形范围[left,top,right,bottom]
        self.op = None  # 子box的分割方向H或V
        self.sp = None  # 分割的比例 float为百分比;int为像素
        self.child1 = None  # 子box1
        self.child2 = None  # 子box2

    # 获取box的宽度
    def width(self):
        return self.rect[2] - self.rect[0]

    # 获取box的高度
    def height(self):
        return self.rect[3] - self.rect[1]

    # 获取box的左坐标值
    def left(self):
        return self.rect[0]

    # 获取box的右坐标值
    def right(self):
        return self.rect[2]

    # 获取box的上坐标值
    def top(self):
        return self.rect[1]

    # 获取box的下坐标值
    def bottom(self):
        return self.rect[3]

    # 获取box的宽高尺寸
    def size(self):
        return (self.width(), self.height())

    def __getitem__(self, item):
        """访问当前box的子box,根据子box的布局名字,以及实际的布局进行检查输出."""
        if self.op == 'H':
            if item == 'T':
                return self.child1
            elif item == 'B':
                return self.child2
        else:
            if item == 'L':
                return self.child1
            elif item == 'R':
                return self.child2
        return None

    def __str__(self):
        """调试方便,用于显示内部核心数据"""
        if self.rect is None:
            return 'empty'
        if self.op:
            return '(%d,%d)-(%d,%d)|%dx%d|%s:%s' % (self.rect[0], self.rect[1], self.rect[2], self.rect[3], self.width(), self.height(), self.op, self.sp)
        else:
            return '(%d,%d)-(%d,%d)|%dx%d' % (self.rect[0], self.rect[1], self.rect[2], self.rect[3], self.width(), self.height())

    def __call__(self, *args, **kwargs):
        """对当前节点,按op类型,进行sp比例分割.返回值:当前节点,或None(已经分割过的节点不能再次分割)"""
        if self.op or len(args) != 2:
            return None  # 已经分割过,不能再分割;入参错误不能分割.

        op = args[0]
        sp = args[1]

        if op not in {'H', 'V'}:
            return None
        if not isinstance(sp, float) and not isinstance(sp, int):
            return None

        self.op = op
        self.sp = sp
        self.child1 = box(self)  # 新分割得到两个子box对象
        self.child2 = box(self)
        # 对新的子box对象计算分割后的矩形范围
        self.child1.rect, self.child2.rect = box_split(self.rect, op, sp)
        return self

    def query(self, path):
        """根据路径查询当前节点下的box节点"""
        if path == '/' or path == '':
            return self

        if path[0] == '/': path = path[1:]
        if path[-1] == '/': path = path[:-1]

        path = path.split('/')
        node = self
        for p in path:
            node = node[p]
        return node


class box_layout(box):
    """box布局管理器,其自身就是根节点"""

    def __init__(self, width, height):
        super().__init__(self)
        self.refresh(width, height)

    def refresh(self, width, height):
        """对布局树进行刷新计算,所有子节点的box范围进行更新."""
        self.rect = [0, 0, width, height]

        def recalc(node):
            """对指定的节点node与其对应的全部子节点进行递归调用,重新计算box范围矩形"""
            if node.op is None:
                return
            node.child1.rect, node.child2.rect = box_split(node.rect, node.op, node.sp)
            if node.child1.op:
                recalc(node.child1)
            if node.child2.op:
                recalc(node.child2)

        # 从根节点进行深度递归
        recalc(self)