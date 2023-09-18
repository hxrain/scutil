# match_dfa和match_ac使用的公共基础功能
from copy import deepcopy


class pos_t:
    """匹配位置信息记录"""

    def __init__(self, begin, end, txt, txtl=None, txtr=None):
        self.begin = begin  # 开始位置[
        self.end = end  # 结束位置)
        self.txt = txt  # 开始结束对应的文本
        self.txt_left = txtl  # 开始位置左侧的文本
        self.txt_right = txtr  # 结束位置右侧的文本


class rep_t:
    """文本替换信息记录"""

    def __init__(self):
        self.src = None  # 匹配的源信息
        self.dst = None  # 替换后的信息
        self.tag = None  # 可选的标记

    def rec_src(self, begin, end, txt, txtl='', txtr=''):
        self.src = pos_t(begin, end, txt, txtl, txtr)

    def rec_dst(self, begin, end, txt):
        self.dst = pos_t(begin, end, txt)

    def __repr__(self):
        if self.src is None or self.dst is None:
            return 'EMPTY'
        return f"[{self.src.begin}:{self.src.end}='{self.src.txt}']=>[{self.dst.begin}:{self.dst.end}='{self.dst.txt}']"


class rep_rec_t:
    """文本替换信息的持续记录器"""

    def __init__(self, txt=None, rst=None, lr_len=3):
        self.adj = 0  # 目标偏移增量
        self.txt = txt  # 原始文本串
        self.lr_len = lr_len  # 额外记录的原始串左右内容长度
        self.rst = rst

    def make(self, begin, end, dst_txt, tag=None):
        """生成替换记录对象.将[begin,end)的内容替换为dst_txt"""
        if begin > end:
            return None
        ri = rep_t()
        ri.tag = tag

        # 匹配位置的左右内容
        txtl = self.txt[0:begin] if begin <= self.lr_len else self.txt[begin - self.lr_len:begin]
        txtr = self.txt[end: end + self.lr_len]
        # 记录匹配信息
        ri.rec_src(begin, end, self.txt[begin:end], txtl, txtr)

        # 计算替换后的位置信息,需要持续考虑"替换目标的长度增量"
        dst_begin = begin + self.adj
        dst_end = dst_begin + len(dst_txt)
        ri.rec_dst(dst_begin, dst_end, dst_txt)

        # 迭代更新结果文本中的长度增量
        self.adj += len(dst_txt) - (end - begin)
        if self.rst is not None:
            if len(self.rst) > 0:
                assert (ri.src.begin >= self.rst[-1].src.end)
                assert (ri.dst.begin >= self.rst[-1].dst.end)
            self.rst.append(ri)
        return ri


def lookup(reps, begin, end=None, by_src=True):
    """在reps替换记录列表中,查找与[begin,end)相交的部分.返回值:[idx]列表"""
    siz = len(reps)
    if siz == 0:
        return []

    def val(m, is_begin=True):
        """获取列表中m处元素begin或end属性的值."""
        if by_src:
            return reps[m].src.begin if is_begin else reps[m].src.end
        else:
            return reps[m].dst.begin if is_begin else reps[m].dst.end

    if end == -1:
        end = val(-1, False)
    if end is None:
        end = begin
    if begin > end:
        return []

    lo = 0
    hi = siz
    pos = None
    # 先用二分法定位begin最初的位置
    while lo < hi:
        mid = (lo + hi) // 2
        vb = val(mid, True)
        ve = val(mid, False)
        if begin >= vb and begin < ve:
            pos = mid
            break
        elif begin < vb:
            hi = mid
        else:
            lo = mid + 1

    if pos is None:
        if lo >= siz:
            return []
        ve = val(lo, False)
        if ve < begin:
            return []
        else:
            pos = lo

    # 从初始位置向后查找
    rst = []
    for i in range(pos, siz):
        vb = val(i, True)
        if vb >= end:
            if begin >= vb:
                rst.append(i)
            break
        rst.append(i)

    return rst


def take_match_text(message, matchs):
    """根据匹配结果[(b,e,v)]列表matchs,在原信息文本message中查找对应的文本内容段.
        返回值:[(b,e,v,t)]
    """
    rst = []
    for m in matchs:
        rst.append((*m, message[m[0]:m[1]]))
    return rst


def merge_match_segs(mres, keepback=False):
    """合并匹配分段(对于all匹配结果)得到最终重叠被合并的结果,keepback告知保持前值还是后值.返回值:[(b,e,v)]"""
    if len(mres) <= 1:
        return mres
    rst = []
    seg = mres[0]

    def add(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a + b
        if isinstance(a, (set, list, dict)) and isinstance(b, (set, list, dict)):
            r = deepcopy(a)
            r.update(b)
            return r
        return a

    for i in range(1, len(mres)):
        nseg = mres[i]
        if nseg[0] <= seg[1]:
            v = nseg[2] if keepback else add(nseg[2], seg[2])
            seg = min(nseg[0], seg[0]), max(nseg[1], seg[1]), v  # 合并新旧两个段
        else:
            rst.append(seg)  # 将结果段保留,准备进行新的合并尝试
            seg = nseg

        if i == len(mres) - 1:
            rst.append(seg)  # 最后一个别忘了

    return rst


def complete_segs(mres, slen, isfull=False, segs=None, ext=None):
    """在总长度为slen的范围内,获取mres分段列表中未包含的部分,或isfull完整列表
        返回值:[(b,e,v)],rc
        v is None - 未匹配段
        rc告知未匹配段的数量
    """
    pos = 0
    rst = [] if segs is None else segs
    rc = 0

    for seg in mres:
        if seg[0] != pos:
            rst.append((pos, seg[0], ext))
            rc += 1
        pos = seg[1]
        if isfull:
            rst.append(seg)
    if pos != slen:
        rst.append((pos, slen, ext))
        rc += 1
    return rst, rc


def take_unsegs(segs):
    """获取分段列表segs中的未知分段.返回值:[未知分段索引]"""
    rst = []
    for i, seg in enumerate(segs):
        if seg[2] is None:
            rst.append(i)
    return rst


def is_full_segs(mres, slen):
    """判断分段列表mres是否完整的涵盖了slen的长度"""
    begin = 0
    for seg in mres:
        if seg[0] > begin:
            return False
        begin = max(begin, seg[1])
    return begin >= slen


def related_segs(a, b):
    """
        分析两个分段a和b的相对关系: + 紧邻; ~ 离开; & 相交; @ 包含; = 相同
        返回值:
            'A=B',(a1,a2) - a1=b1,a2=b2 A等于B
            'A+B',(a1,b2) - a1,a2=b1,b2 A邻右B(B邻左A)
            'A~B',(a2,b1) - a1,a2,b1,b2 A左离B(B右离A)
            'A&B',(b1,a2) - a1,b1,a2,b2 A交右B(B交左A)
            'A@B',(b1,b2) - a1,b1,b2,a2 A包含B
            'B@A',(a1,a2) - b1,a1,a2,b2 B包含A
            'B&A',(a1,b2) - b1,a1,b2,a2 B交右A(A交左B)
            'B~A',(b2,a1) - b1,b2,a1,a2 B左离A(A右离B)
            'B+A',(b1,a2) - b1,b2=a1,a2 B邻右A(A邻左B)
    """
    a1 = a[0]
    a2 = a[1]
    b1 = b[0]
    b2 = b[1]
    if a1 == b1 and a2 == b2:
        return 'A=B', (a1, a2)
    if a2 == b1:
        return 'A+B', (a1, b2)
    if a2 < b1:
        return 'A~B', (a2, b1)
    if a1 <= b1 < a2:
        if b2 > a2:
            if a1 == b1:
                return 'B@A', (a1, a2)
            else:
                return 'A&B', (b1, a2)
        else:
            return 'A@B', (b1, b2)

    if b2 == a1:
        return 'B+A', (b1, a2)
    if b2 < a1:
        return 'B~A', (b2, a1)
    if b1 <= a1 < b2:
        if a2 > b2:
            if b1 == a1:
                return 'A@B', (b1, b2)
            else:
                return 'B&A', (a1, b2)
        else:
            return 'B@A', (a1, a2)
    assert False, '!!!'


def slen(seg):
    """计算seg段的长度"""
    return seg[1] - seg[0]


def drop_nesting(segs):
    """丢弃segs段落列表中被完全包含嵌套的部分"""
    rst = []

    def chk(seg):
        while rst:
            r, s = related_segs(rst[-1], seg)
            if r == 'A@B':
                return False
            elif r == 'B@A':
                rst.pop(-1)
            else:
                return True
        return True

    for seg in segs:
        if chk(seg):
            rst.append(seg)
    return rst


def max_seg(segs):
    """在segs分段列表中,查找第一个最长的段.返回值:索引"""
    rst = 0
    for i in range(1, len(segs)):
        if slen(segs[i]) > slen(segs[rst]):
            rst = i
    return rst
