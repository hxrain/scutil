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


class converge_tree_t:
    """基于树结构进行词汇计数聚合分析的工具类"""

    class node_t:
        """树节点"""

        def __init__(self, words='', tag=None):
            self.count = 0  # 当前字符出现的次数,0为root节点
            self.words = words  # 当前级别对应词汇,''为root节点
            self.rate = None  # 当前节点占父节点的数量比率,在end之后才有效
            self.tag = tag  # 该节点首次被创建时对应的源数据标记
            self.childs = {}  # 当前节点的子节点

        def __repr__(self):
            return f"""words={self.words} count={self.count} rate={self.rate} tag={self.tag} childs={len(self.childs)}"""

    def __init__(self, reversed=False):
        self.root = self.node_t()
        self.reversed = reversed  # reversed告知是否为逆向遍历

    def add(self, txt, limited=-1, cnt=1, tag=None):
        """添加文本txt,进行计数累计.limited告知是否限定遍历长度"""
        lmt = 0
        if self.reversed:
            iter = range(len(txt) - 1, -1, -1)
        else:
            iter = range(len(txt))

        node = self.root
        for i in iter:
            if limited != -1 and lmt >= limited:
                break
            lmt += 1
            char = txt[i]
            if char not in node.childs:
                node.childs[char] = self.node_t(txt[i:] if self.reversed else txt[:i], tag)  # 确保当前字符在当前节点的子节点中
            node = node.childs[char]  # 得到当前字符对应的子节点
            node.count += cnt  # 累计字符数量

        return lmt

    def end(self):
        """统计子节点对父节点的占比"""

        def cb_func(paths, child, parent):
            rate = 1 if parent.count == 0 else child.count / parent.count
            child.rate = round(rate, 4)

        self.lookup(1, cb_func)

    def lookup(self, counts=1, cb=None):
        """遍历树节点,使用回调函数cb进行处理.counts限定节点计数."""

        def cb_func(paths, child, parent):
            """返回值:True停止当前分支的继续递归;其他继续递归"""
            print('\t' * (len(paths) - 1), child)
            if child.rate == 1 and len(child.words) > 1:
                return True

        if cb is None:
            cb = cb_func

        paths = []  # 对外输出的节点完整路径信息

        def loop(node):
            chars = sorted(node.childs.keys(), key=lambda k: (node.childs[k].count, k))
            for char in chars:
                child = node.childs[char]
                paths.append((char, child.count))
                stop = None
                if child.count >= counts:
                    stop = cb(paths, child, node)  # 只有超过限额计数的节点,才对外输出
                if not stop:
                    loop(child)  # 递归遍历当前子节点
                paths.pop(-1)

        loop(self.root)  # 从根节点进行遍历


class words_trie_t:
    """轻量级词汇匹配树"""

    def __init__(self, reversed=False):
        self.root = {}
        self.reversed = reversed  # reversed告知是否为逆向遍历

    def add(self, word):
        """添加词汇word"""

        if self.reversed:
            iter = range(len(word) - 1, -1, -1)
        else:
            iter = range(len(word))

        ret = 0
        node = self.root
        for i in iter:
            char = word[i]
            if char not in node:
                node[char] = {}  # 确保当前字符节点存在
                ret += 1
            node = node[char]  # 指向下级节点
        return ret  # 返回值告知新登记的字符数量

    def lookup(self, cb=None):
        """遍历树节点,使用回调函数cb进行处理."""

        def cb_func(paths, child, parent):
            """返回值:True停止当前分支的继续递归;其他继续递归"""
            print(paths, ' ' * (len(paths) - 1), child)

        if cb is None:
            cb = cb_func

        paths = []  # 对外输出的节点完整路径信息

        def loop(node):
            for char in node:
                child = node[char]
                paths.append(char)
                if not cb(paths, child, node):
                    loop(child)  # 递归遍历当前子节点
                paths.pop(-1)

        loop(self.root)  # 从根节点进行遍历

    def find(self, word):
        """查找指定的词汇是否存在.
            返回值:(deep,node)
                deep=0          - 不匹配:node为root;
                deep=len(word)  - node为空字典为完整匹配,否则为不完整匹配;
                0<deep<len(word)- 部分匹配:node为下级节点
        """
        if not word:
            return 0, self.root

        if self.reversed:
            iter = range(len(word) - 1, -1, -1)
        else:
            iter = range(len(word))

        deep = 0
        node = self.root
        for i in iter:
            char = word[i]
            if char not in node:
                return deep, node
            deep += 1
            node = node[char]  # 指向下级节点
        return deep, node

    def query(self, word, strict=False):
        """尝试查找是否有匹配的词汇.
            word - 待匹配的短语
            strict - 是否进行严格的边界匹配
            返回值:(begin,deep,node)
                deep=0           - 不匹配:node为None;
                deep=len(word)   - node为空字典为完整匹配,否则为部分匹配;
                0<deep<len(word) - 部分匹配:node为下级节点
        """
        if not word:
            return 0, self.root

        if self.reversed:
            iter = range(len(word) - 1, -1, -1)
        else:
            iter = range(len(word))

        begin = None
        deep = 0
        node = self.root
        for i in iter:
            char = word[i]
            if char not in node:
                if begin is None and not strict:
                    continue
                else:
                    break
            elif begin is None:
                begin = i
            deep += 1
            node = node[char]  # 指向下级节点
        if self.reversed and begin is not None and deep:
            begin -= deep - 1
        if deep == 0:
            node = None
        return begin, deep, node


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


def complete_segs(mres, slen, isfull=False, segs=None, ext=None, cb=None):
    """在总长度为slen的范围内,获取mres分段列表中未包含的部分,或isfull完整列表
        返回值:[(b,e,v)],rc
        v is None - 未匹配段
        rc告知未匹配段的数量
    """
    pos = 0
    rst = [] if segs is None else segs
    rc = 0

    for seg in mres:
        if seg[0] > pos:
            rst.append((pos, seg[0], ext))
            if cb: cb(rst)
            rc += 1
        pos = seg[1]
        if isfull:
            rst.append(seg)
            if cb: cb(rst)
    if pos != slen:
        rst.append((pos, slen, ext))
        if cb: cb(rst)
        rc += 1
    return rst, rc


def find_none(segs, isnone=True):
    """在segs分段列表中,查找第一个遇到的None未知分段(或已知分段).返回值:分段索引,或未找到返回None"""
    if isnone:
        for i, seg in enumerate(segs):
            if seg[2] is None:
                return i
    else:
        for i, seg in enumerate(segs):
            if seg[2] is not None:
                return i
    return None


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
