import math


class point2_t:
    """二维平面坐标点"""

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.x + other.x, self.y + other.y)
        else:
            return self.__class__(self.x + other, self.y + other)

    def __mul__(self, other):
        return self.__class__(int(self.x * other), int(self.y * other))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __str__(self):
        return f'({self.x},{self.y})'


def calc_distance(p1, p2):
    """计算p1和p2的距离"""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return math.sqrt(dx * dx + dy * dy)


def make_beizer2_path(startPoint, controlPoint, endPoint, segmentNum=None):
    """生成二阶贝塞尔曲线路径:
        startPoint - 开始点
        controlPoint - 控制点
        endPoint - 结束点
        segmentNum - >0 路径结果点数量;<0路径点分段步长
        返回值:[point2_t]
    """

    def chk(p):
        return point2_t(p[0], p[1]) if isinstance(p, tuple) else p

    def bezier2(p0, p1, p2, t):
        r = 1 - t
        return r * (r * p0 + t * p1) + t * (r * p1 + t * p2)

    def segs(segmentNum):
        if segmentNum > 0:
            return segmentNum
        elif not segmentNum:
            segmentNum = -10
        d1 = calc_distance(startPoint, controlPoint)
        d2 = calc_distance(controlPoint, endPoint)
        return int(d1 + d2) // (0 - segmentNum)

    startPoint = chk(startPoint)
    controlPoint = chk(controlPoint)
    endPoint = chk(endPoint)
    segmentNum = segs(segmentNum)

    result = [startPoint]
    for i in range(1, segmentNum):
        t = i / segmentNum
        pixel = bezier2(startPoint, controlPoint, endPoint, t)
        result.append(pixel)
    result.append(endPoint)

    return result


def calc_angle_slope(p1, p2):
    """计算线段p1->p2的斜率角.返回值:斜率角的弧度"""
    dy = p2.y - p1.y
    dx = p2.x - p1.x
    if dx == 0:
        return math.pi / 2 if dy > 0 else 2 * math.pi - math.pi / 2
    if dy == 0:
        return 0 if dx > 0 else math.pi
    return math.atan(dy / dx)


def calc_line_point(p1, p2, distance):
    """在p1->p2构成的直线上,获取距离p1点距离为distance的点"""
    agl = calc_angle_slope(p1, p2)
    dx = math.cos(agl) * distance
    dy = math.sin(agl) * distance
    return point2_t(p1.x + dx, p1.y + dy)


def calc_point_rotate(p1, p0, agl):
    """计算p1围绕p0旋转agl弧度后的新位置坐标"""
    dsin = math.sin(agl)
    dcos = math.cos(agl)

    dx = p1.x - p0.x
    dy = p1.y - p0.y

    x = dx * dcos + dy * dsin + p0.x
    y = dx * dsin + dy * dcos + p0.y
    return point2_t(round(x, 2), round(y, 2))


def calc_vertex_normal(p1, p2, distance):
    """计算线段p1->p2,距离p1为distance处的等长法线段的顶点"""
    p0 = calc_line_point(p1, p2, distance)
    return calc_point_rotate(p1, p0, -math.pi / 2)


def make_ctrl_point(p1, p2, posrate=0.6, highrate=0.2):
    """生成p1->p2线段对应的贝塞尔曲线的控制点,要求分割率为posrate,隆起率为highrate(>0正向,<0反向)"""
    distance = calc_distance(p1, p2)  # 贝塞尔曲线起止点间的直线距离
    dir = -1 if highrate > 0 else 1
    highrate = math.fabs(highrate)
    high = distance * highrate  # 控制点的隆起高度
    slen = distance * posrate  # 控制点在p1->p2上的垂点距离
    spoint = calc_line_point(p1, p2, slen)  # 控制点在p1->p2上的垂点
    tpoint = calc_line_point(p1, p2, slen - high)  # 控制点在p1->p2上的伪点
    return calc_point_rotate(tpoint, spoint, dir * math.pi / 2)  # 伪点围绕垂点顺时针旋转90度,得到法线段定点


def make_beizer2_path2(p1, p2, posrate=0.6, highrate=-0.2, segmentNum=-12):
    """生成起止点p1->p2的贝塞尔曲线点路径.
        posrate 隆起点在线段上的位置分割比率
        highrate 隆起点的高度与线段距离的比率(>0正向,<0反向)
        segmentNum 生成的贝塞尔曲线的点间隔步长
        返回值:[point2_t]
    """
    cp = make_ctrl_point(p1, p2, posrate, highrate)
    return make_beizer2_path(p1, cp, p2, segmentNum)
