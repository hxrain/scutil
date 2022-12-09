import math
import random


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
        return round((d1 + d2) // (0 - segmentNum))

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
    rad = math.atan(dy / dx)
    if rad < 0:
        rad += math.pi
    return rad


def calc_line_point(p1, p2, distance):
    """在p1->p2构成的直线上,获取距离p1点距离为distance的点"""
    total = calc_distance(p1, p2)
    rate = distance / total
    dx = (p2.x - p1.x) * rate
    dy = (p2.y - p1.y) * rate
    return point2_t(p1.x + dx, p1.y + dy)


def calc_point_rotate(p1, p0, agl):
    """计算p1围绕p0旋转agl弧度后的新位置坐标"""
    dsin = math.sin(agl)
    dcos = math.cos(agl)

    dx = p1.x - p0.x
    dy = p1.y - p0.y

    x = dx * dcos - dy * dsin + p0.x
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


def make_beizer2_path2(p1, p2, posrate=0.6, highrate=-0.2, segmentNum=-12, toPoint=False):
    """生成起止点p1->p2的贝塞尔曲线点路径.
        posrate 隆起点在线段上的位置分割比率
        highrate 隆起点的高度与线段距离的比率(>0正向,<0反向)
        segmentNum 生成的贝塞尔曲线的点间隔步长
        返回值:[point2_t]或[(x,y)]
    """
    if isinstance(p1, tuple):
        p1 = point2_t(p1[0], p1[1])
    if isinstance(p2, tuple):
        p2 = point2_t(p2[0], p2[1])

    cp = make_ctrl_point(p1, p2, posrate, highrate)
    path = make_beizer2_path(p1, cp, p2, segmentNum)
    if toPoint:
        return path
    rst = []
    for p in path:
        rst.append((p.x, p.y))
    return rst


def make_beizer2_path3(p1, p2, posrate=(0.4, 0.7), highrate=(-0.2, -0.25), segmentNum=(-5, -10), toPoint=False):
    """在指定的参数范围内随机生成p1->p2的贝塞尔曲线点路径"""
    if isinstance(p1, tuple):
        p1 = point2_t(p1[0], p1[1])
    if isinstance(p2, tuple):
        p2 = point2_t(p2[0], p2[1])

    def calc_rand(range):
        r = random.random()
        return range[0] + r * (range[1] - range[0])

    prate = calc_rand(posrate)
    hrate = calc_rand(highrate)
    stNum = calc_rand(segmentNum)
    return make_beizer2_path2(p1, p2, prate, hrate, stNum, toPoint)


def calc_points_offset(points, offsetX, offsetY, outPoint=False):
    """将点集points中每个点都进行偏移调整."""
    rst = []
    for p in points:
        if isinstance(p, point2_t):
            r = (p.x + offsetX, p.y + offsetY)
        else:
            r = (p[0] + offsetX, p[1] + offsetY)

        if outPoint:
            rst.append(point2_t(r[0], r[1]))
        else:
            rst.append(r)

    return rst


def make_rect_center(p1, p2, rand=True, outPoint=False):
    """生成矩形范围(p1,p2)中的一个随机点(结果不为边缘上的点)."""
    if isinstance(p1, point2_t):
        p1 = (p1.x, p1.y)

    if isinstance(p2, point2_t):
        p2 = (p2.x, p2.y)

    dx = max(p2[0] - p1[0] - 2, 0)
    dy = max(p2[1] - p1[1] - 2, 0)
    if rand:
        x = round(p1[0] + random.random() * dx)
        y = round(p1[1] + random.random() * dy)
    else:
        x = round(p1[0] + dx / 2)
        y = round(p1[1] + dy / 2)

    x += 1
    y += 1

    if outPoint:
        return point2_t(x, y)
    else:
        return (x, y)


def make_rand_point(p0, range, outPoint=False):
    """生成以p0为中心,偏移范围<range内的点坐标"""
    if isinstance(p0, point2_t):
        p0 = (p0.x, p0.y)
    dir = 1 if random.random() > 0.5 else -1
    x = p0[0] + dir * range * random.random()
    dir = 1 if random.random() > 0.5 else -1
    y = p0[1] + dir * range * random.random()

    x = max(0, round(x))
    y = max(0, round(y))

    if outPoint:
        return point2_t(x, y)
    else:
        return (x, y)
