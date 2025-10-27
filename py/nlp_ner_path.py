from nlp_ner_data import types

# 数字序号基础模式
num_cn = {'零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '幺', '壹', '贰', '貮', '貳', '弍', '叁', '仨', '肆', '伍', '陆', '陸', '柒', '捌', '玖', '拾', '百', '千', '仟', '万'}
num_zh = f'甲乙丙丁戊己庚辛壬癸丑寅卯辰巳午未申酉戌亥廿卅什两参佰伯'
num_re = rf'A-Z×&+○O\dIⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ{num_zh}{"".join(num_cn)}'


def make_tags_txt(segs, txt, usetag=True, sep='|'):
    """根据组份分段列表segs和文本串txt,生成标记表达格式串"""
    rst = []
    for seg in segs:
        if usetag:
            tag = types.type(seg[2])[0][1] if seg[2] else 'X'
            t = f'{tag}:{txt[seg[0]:seg[1]]}'
        else:
            t = txt[seg[0]:seg[1]]
        rst.append(t)
    return sep.join(rst)


def find_right(segs, seg, offset, steps=3):
    """从segs的offset开始向右探察,判断是否存在seg的紧邻分段
        返回值:=0未找到seg的粘连分段;>=1,包含offset在内第几个分段与seg有粘连
    """
    c = 0
    for idx in range(offset, len(segs)):
        nseg = segs[idx]
        c += 1
        if nseg[0] > seg[1] and c > steps:
            return 0
        if seg[0] < nseg[0] == seg[1]:
            return c
    return 0


def find_left(segs, seg, offset, steps=3, can_cross=False):
    """从segs的offset开始向左探察,判断是否存在seg的紧邻分段
        返回值:=0未找到seg的粘连分段;>=1,包含offset在内第几个分段与seg有粘连
    """
    if offset < 0:
        return 0
    c = 0
    for idx in range(offset, -1, -1):
        pseg = segs[idx]
        c += 1
        if pseg[1] < seg[0] and c > steps:
            return 0
        if can_cross:
            if seg[0] <= pseg[1] <= seg[1]:
                return c
        else:
            if seg[0] == pseg[1] < seg[1]:
                return c
    return 0


class tree_paths_t:
    """
        基于树状结构进行segs分段路径的最优寻径.
        核心结构有,segs路径列表,tree路径树,ends树的末端列表,用于回溯.
    """

    class node_t:
        """分段路径的节点类型,用于记录父子节点和路径积分"""

        def __init__(self):
            self.parent = None  # 当前节点的父节点,根节点为空
            self.childs = []  # 当前节点的所有子节点
            self.sidx = None  # 当前节点对应的分段索引
            self.score = (0, 0)  # 当前节点自身的评分
            self.total = (0, 0)  # 当前节点路径的整体评分
            self.deep = 0  # 当前节点路径的深度
            self.variance = 0  # 分段长度差累积

        def __repr__(self):
            return f"total: {self.total}, deep: {self.deep}, variance: {self.variance}"

    score_maps = {'X': 0, 'U': 4, 'A': 5, 'N': 6, 'H': 7, 'S': 8, 'Z': 8, 'O': 8, 'B': 9, 'M': 9, 'L': 9, }
    unchars = {'(', ')', '<', '>', '"', "'"}

    def __init__(self):
        self.clear()

    def clear(self):
        self.root = tree_paths_t.node_t()
        self.ends = []

    @staticmethod
    def ismob(segs, nidx, b, e):
        """在segs分段列表中查找(b,e)位置是否存在M/O/B分段"""
        if not segs:
            return False
        for i in range(nidx, -1, -1):
            seg = segs[i]
            if seg[0] < b:
                return False
            if seg[0] == b and seg[1] == e:
                return seg[2] & {types.NM, types.NO, types.NB}
        return False

    @staticmethod
    def score(seg, nseg, txt, nidx=None, segs=None):
        """根据seg与nseg前后两个分段的关系,计算nseg路径节点的积分,返回值:(奖励积分,惩罚扣分)"""

        def left_break(segs, seg):
            """判断segs中seg左侧是否为断裂的"""
            sidx = None
            for idx in range(nidx - 1, -1, -1):
                if segs[idx] == seg:  # 先根据nidx前向查找seg对应的位置
                    sidx = idx
                    break
            assert sidx is not None
            if sidx == 0:
                return False
            return find_left(segs, seg, sidx - 1, can_cross=True) == 0

        # 根据分段类型得到积分标准
        segt = tree_paths_t.score_maps[types.tag(seg[2])]
        nsegt = tree_paths_t.score_maps[types.tag(nseg[2])]
        seg_len = seg[1] - seg[0]
        nseg_len = nseg[1] - nseg[0]
        txt_len = len(txt)

        if nseg_len == 1:
            if not seg[2] & {types.NM, types.NO, types.NB} or txt[nseg[0]] == '老':
                nsegt -= 1  # 后分段为单字,降分级
        elif nseg_len >= 3 and nseg[1] < txt_len and nseg[2] & {types.NS, } and txt[nseg[1] - 1] in {'县', '乡', '村', '镇'}:
            nsegt += 1  # 带有完整地名尾缀特征字的分段,升分级

        ds = 0  # 初始扣分
        ns = None  # 初始得分
        if nseg[0] > seg[1]:  # 前后段分离
            ds = nseg[0] - seg[1]  # 间隔长度扣分
            if ds == 1 and txt[seg[1]] in tree_paths_t.unchars:
                ds = 0  # 特殊字符的空白间隔不扣分
            else:
                ds *= 3
            ns = nseg_len * nsegt  # 自身长度加分
        elif seg[1] > nseg[0]:  # 前后段交叉
            if seg[1] - nseg[0] >= 2:  # 特定重叠多字的情况
                if seg[2] & nseg[2] & {types.NZ, types.NN}:
                    ds = 0
                elif seg[2] & {types.NN, types.NH} and nseg[2] & {types.NZ, types.NH} and txt[seg[0]] in {'新'}:
                    ds = 0
                    ns = nseg_len * nsegt
                elif seg[2] & {types.NA, types.NU, types.NN, types.NH} and nseg[2] & {types.NA, types.NU, types.NN, types.NH}:
                    ds = 0
                elif not seg[2] & {types.NB} and nseg[2] & {types.NM, types.NO, types.NB}:
                    ds = 0
                    ns = nseg_len * nsegt  # 按正常情况计算完整的后段积分
                else:
                    ds = (seg[1] - nseg[0]) * 2
            elif seg[1] - nseg[0] == 1:
                lseg = segs[nidx + 1] if segs and nidx + 1 < len(segs) else None
                ts_len = nseg[1] - seg[0]
                if ts_len <= 5 and seg[2] & {types.NA, types.NN, types.NU} and nseg[2] & {types.NA, types.NN, types.NU}:
                    ds = 0  # 特定双段相交不扣分:(NA,NU,NN)&(NA,NU,NN)
                    if nseg[2] & seg[2] & types.tags_NU:
                        ns = (nseg[1] - seg[1]) * nsegt
                    elif ts_len <= 3 and (txt[seg[0]] in {'老', '新'} or txt[seg[0]] in num_cn) and not nseg[2] & seg[2] & types.tags_NN:
                        # ns = nseg_len * tree_paths_t.score_maps['N']
                        ns = nseg_len * nsegt - (seg[1] - nseg[0]) * segt
                    elif segs and txt[nseg[0]] in num_cn and (not lseg or not lseg[2] & {types.NO} or seg[1] != lseg[0]):
                        ns = nseg_len * tree_paths_t.score_maps['N']
                elif ts_len >= 3 and seg[2] & {types.NU} and nseg[2] & {types.NB, types.NO}:
                    ds = 0  # 特定双段相交不扣分:NU&(NB,NO)
                    ns = nseg_len * nsegt
                elif ts_len >= 3 and seg[2] & {types.NA} and nseg[2] & {types.NO} and txt[seg[0]] in num_cn:
                    ds = 0  # 特定双段相交不扣分:NA&(NB,NO) 且 NA的首字是数字
                    ns = nseg_len * nsegt
                elif nidx and nidx > 2 and seg[0] and nseg_len >= 3 and left_break(segs, seg) and txt[seg[0] - 1] not in tree_paths_t.unchars:
                    ds = 0  # 特殊情况:seg与nseg相交,而seg的前面是未知分段,则尽量保留更长的nseg分段
                    ns = nseg_len * nsegt
                elif seg[2] & {types.NO, types.NM} and nseg_len <= 2 and not tree_paths_t.ismob(segs, nidx, seg[0], seg[1] - 1) and nidx == len(segs) - 1:
                    ds = 0  # 研究室|室室,相交时,不扣分,但降低nseg得分
                    ns = (nseg_len - 1) * nsegt
                elif nseg[2] & {types.NB, types.NO, types.NM} and nseg_len <= 4:
                    if (seg_len <= 3 or nseg_len <= 2) and txt[nseg[0]] in {'省', '市', '区', '县', '乡', '镇', '村', '州', '旗'}:
                        ds = 0  # 特定尾缀单字相交不扣分,如"红星村|村委会"
                    else:
                        ds = 4
                else:
                    ds = 2  # 其他情况
            elif seg[2] & {types.NM, types.NO, types.NB}:
                ds = (seg[1] - nseg[0]) * 4  # 尾缀分段不应该被交叉,扣分多一些
            else:
                ds = (seg[1] - nseg[0]) * 3  # min(segt, nsegt)  # 根据相交长度与前后类型标准分,进行扣除

            if ns is None:
                ns = (nseg[1] - seg[1]) * nsegt  # 前后相交,仅计算后段剩余部分
        else:  # 前后相邻
            ns = nseg_len * nsegt  # 正常情况,仅计算完整的后段积分
        return ns, ds

    @staticmethod
    def _take_first(offset, segs):
        """从segs的offset开始,查找与之相同起点的节点对应的索引列表"""
        head = segs[offset][0]
        rst = [offset]
        c = 0
        for idx in range(offset + 1, len(segs)):
            if segs[idx][0] == head:
                rst.insert(0, idx)
                c = 0
            elif c > 3:
                break
            c += 1
        return rst

    @staticmethod
    def _take_nexts(pos, segs):
        """基于segs分段列表的pos节点索引,查找pos后的所有粘连分段.返回值:[]分段列表"""
        rst = []
        seg = segs[pos]
        c = 0
        for idx in range(pos + 1, len(segs)):  # 从pos索引向后查找可达分段
            nseg = segs[idx]
            c += 1
            if nseg[0] > seg[1] and c > 3:
                break  # 多次向后试探,遇到分离的分段则停止尝试
            if seg[0] < nseg[0] <= seg[1] and nseg[1] > seg[1]:
                rst.insert(0, idx)  # 遇到与当前分段相交或相连的分段,则记录其索引
                c = 0

        if not rst:
            while pos < len(segs) - 1:
                nseg = segs[pos + 1]  # 上述过程未找到后续分段,则尝试查找分离的后段
                if nseg[0] > seg[0] and nseg[1] > seg[1]:
                    rst = tree_paths_t._take_first(pos + 1, segs)
                    break
                pos += 1

        return rst

    def _drop_path(self, txt, segs, pnode, pseg, nseg):
        """检查当前路径是否需要被放弃"""
        if pnode.parent is None:
            return False
        if pnode.parent.sidx is not None:
            fseg = segs[pnode.parent.sidx]
            if fseg[1] == nseg[0]:
                if fseg[0] < pseg[0] < fseg[1] and nseg[0] < pseg[1] < nseg[1]:
                    return True  # 出现了pseg被fseg和nseg完整涵盖的情况,放弃当前路径
        return False

    def _loop(self, txt, segs, pnode, badlimit=5):
        """核心方法,进行深度优先遍历,构建有效的路径树"""
        pseg = segs[pnode.sidx]
        nexts = tree_paths_t._take_nexts(pnode.sidx, segs)
        if not nexts:  # 没有后续节点了,当前节点就是本路径的终点,记录当前结果
            txtl = len(txt)
            if not self.ends or pseg[1] == txtl or (pseg[1] == txtl - 1 and txt[-1] in {'(', ')', "'", '"'}):
                if self.ends and self.ends[-1].total[1] >= badlimit:
                    self.ends.pop(-1)  # 如果之前存在着临时的坏结果,则丢弃
                self.ends.append(pnode)
            return

        for nidx in nexts:
            nseg = segs[nidx]
            score = tree_paths_t.score(pseg, nseg, txt, nidx, segs)  # 当前路径节点分
            total = (pnode.total[0] + score[0], pnode.total[1] + score[1])
            if total[1] >= badlimit and len(self.ends) >= 1:
                continue  # 发现继续走下去惩罚积分较大,则当前路径被剪枝放弃
            if self._drop_path(txt, segs, pnode, pseg, nseg):
                continue  # 出现了无效匹配的情况,放弃当前路径
            if self.ends:
                lnode = self.ends[-1]  # 已经存在的最新端点
                if total[1] > lnode.total[1] + 2:
                    continue  # 路径走到中间的时候扣分已经大于存在的结果了,那么剩余路径不用尝试了
                if pnode.deep + 1 > lnode.deep and total[0] < lnode.total[0]:
                    continue  # 路径深度大于已有结果,且总分也小于它,则放弃当前路径

            node = tree_paths_t.node_t()  # 生成当前节点
            node.sidx = nidx  # 记录当前节点对应的分段索引
            node.parent = pnode  # 记录父节点
            node.deep = pnode.deep + 1  # 当前路径节点的深度
            node.score = score  # 当前路径节点积分
            node.total = total  # 路径总分
            node.variance = pnode.variance + abs((nseg[1] - nseg[0]) - (pseg[1] - pseg[0]))  # 累积分段长度差
            pnode.childs.append(node)  # 记录当前节点
            self._loop(txt, segs, node)  # 深度遍历新节点路径

    def _path_dbg(self, end, txt, segs):
        """调试,根据路径端点输出完整路径分段信息"""

        def _make_path(node):
            rst = []
            while node.parent is not None:
                rst.insert(0, node)
                node = node.parent
            return rst

        def _make_segs(path):
            rst = []
            for node in path:
                seg = segs[node.sidx]
                rst.append(f'{types.tag(seg[2])}:{txt[seg[0]:seg[1]]}:{node.total[0]}/{node.total[1]}')
            return rst

        return _make_segs(_make_path(end))

    def _path_has_mob(self, end, segs, islast=False):
        """检查当前端点end所对应路径,是否存在MOB分段"""
        node = end
        while node.parent is not None:
            seg = segs[node.sidx]
            if seg[2] & {types.NM, types.NO, types.NB}:
                return True
            if islast:
                break  # 如果要求仅进行最后分段的检查,则这里结束
            node = node.parent
        return False

    def _take(self, rst, txt, segs, showdbg):
        """根据末端列表选取并构造最优路径结果rst,作为最终结果"""
        if showdbg:
            print(f"\n---->{txt}<----")
            print(f"{str(segs).replace(' ', '')}")
            ts = []
            for seg in segs:
                ts.append(f"{types.tag(seg[2])}:{txt[seg[0]:seg[1]]}")
            print(f'{"|".join(ts)}')
            showdbg = len(self.ends)
            for end in self.ends:
                pd = self._path_dbg(end, txt, segs)
                print(f'  {"|".join(pd)}')

        def filter_nt(ends, islast=False):
            """尝试过滤筛除非nt端点路径,若存在NT尾缀端点,则其他非NT尾缀端点均丢弃"""
            rms = []
            mt_score = None

            for i, node in enumerate(ends):
                if self._path_has_mob(node, segs, islast):
                    mt_score = node.total[0] if mt_score is None else min(mt_score, node.total[0])  # 当前路径有MOB分段,记录最小总分
                else:
                    rms.append(i)

            if len(rms) == len(ends):
                return False  # 所有端点都不是nt,则不处理

            for i in reversed(rms):  # 尝试删除非nt尾缀的端点
                end = ends[i]
                seg = segs[end.sidx]
                if end.total[0] <= mt_score or seg[2] & {types.NA, types.NU} or (types.NS in seg[2] and txt[seg[1] - 2:seg[1]] in {'门市'}):  # NS三门市
                    ends.pop(i)  # 丢弃非nt尾缀的路径
            return len(rms) > 0

        def filter_top(ends):
            """对全部端点路径按总分进行分组,只保留该分数下最高分的端点"""
            tops = {}
            rms = []
            for i, node in enumerate(ends):
                ts = node.total[0]  # 根据总分进行分组记录
                if ts not in tops:
                    tops[ts] = [i]
                else:
                    tops[ts].append(i)

            for ts in tops:  # 每个总分的分组内部,只保留扣分最少的结果
                if len(tops[ts]) == 1:
                    continue
                tsl = sorted(tops[ts], key=lambda i: 0 - ends[i].total[1], reverse=True)
                for i in range(1, len(tsl)):
                    if ends[tsl[i]].total != ends[tsl[0]].total:
                        rms.append(tsl[i])

            for i in sorted(rms, reverse=True):
                ends.pop(i)  # 删除所有不被保留的路径节点

        filter_top(self.ends)  # 通过积分评价排序,筛选得到最优结果路径
        if not filter_nt(self.ends, True):  # 尝试预先筛选丢弃非NT结尾的路径
            filter_nt(self.ends)

        if showdbg and showdbg > 1:
            print(f"---->filter<----")
            showdbg = len(self.ends)
            for end in self.ends:
                pd = self._path_dbg(end, txt, segs)
                print(f'  {"|".join(pd)}')

        if len(self.ends) > 1:
            # 排序规则:最少扣分且最短的路径下的最高有效分
            ends = sorted(self.ends, key=lambda x: (0 - x.total[1], 0 - x.deep, x.total[0] - x.total[1], 0 - x.variance), reverse=True)
            e0 = ends[0]
            e1 = ends[1]
            if e1.total[1] <= 2 and e1.total[0] - e1.total[1] > e0.total[0] + 6 and e1.deep <= e0.deep:
                node = e1
            else:
                node = e0
            # node = ends[0]
        else:
            node = self.ends[0]

        if showdbg and showdbg > 1:
            pd = self._path_dbg(node, txt, segs)
            print(f'>>{"|".join(pd)}')

        # 根据最优路径的端点逆向重构完整的分段结果
        while node.parent is not None:
            rst.insert(0, segs[node.sidx])
            node = node.parent
        return rst

    def find(self, txt, segs, showdbg=False, rst=None):
        """基于文本txt的分段匹配列表segs,查找最优路径结果rst"""
        if not txt or not segs:
            return []
        if len(segs) == 1:
            return list(segs)

        nexts = tree_paths_t._take_first(0, segs)
        seg = (0, segs[nexts[0]][0], types.tags_NA)
        for nidx in nexts:
            nseg = segs[nidx]
            node = tree_paths_t.node_t()  # 生成当前节点
            node.sidx = nidx  # 记录当前节点对应的分段索引
            node.deep = self.root.deep + 1
            node.parent = self.root  # 记录根节点
            node.total = node.score = self.score(seg, nseg, txt, nidx, segs)  # 路径节点分
            self.root.childs.append(node)  # 记录当前节点
            self._loop(txt, segs, node)  # 深度遍历新节点路径

        if rst is None:
            rst = []
        return self._take(rst, txt, segs, showdbg)  # 提取最终结果


def split_nt_paths(segs, slen=10):
    """切分过长的nt路径,避免寻径递归崩溃"""
    sl = len(segs)

    def _find_next(pos, n, typ):
        """在segs的pos之后的n个节点内查找typ类型的分段.返回值:新的pos,或-1未找到"""
        r = -1
        for i in range(pos, min(pos + n, sl)):
            pseg = segs[i - 1] if i else None
            if pseg and pseg[1] < segs[i][0]:
                return r  # 出现了断裂的分段
            if segs[i][2] & typ:
                r = i
        return r

    def _find_segs(bpos):
        epos = bpos
        while epos < sl:
            seg = segs[epos]
            if epos:  # 先判断是否断裂
                ppos = epos - 1
                pseg = segs[ppos]
                if pseg[1] < seg[0] and not find_left(segs, seg, epos - 2, can_cross=True):
                    return epos  # 出现了断裂的分段

            if epos - bpos >= slen:  # 再判断是否过长
                if epos + 1 < sl:
                    nseg = segs[epos + 1]
                    if nseg[0] < seg[1] or find_left(segs, nseg, epos - 1, 4, True) or (nseg[0] == seg[1] and nseg[2] & {types.NM, types.NO, types.NB}) or seg[2] & {types.NU, types.NA}:
                        epos += 1
                        continue

                return epos + 1

            if seg[2] & {types.NM, types.NO, types.NB}:  # 判断是否为特征尾缀
                next = _find_next(epos + 1, 4, {types.NM, types.NO, types.NB})
                if next == -1:
                    if epos + 1 < sl and find_left(segs, segs[epos + 1], epos - 1, can_cross=True):
                        epos += 1
                        continue
                    return epos + 1
                elif next == epos + 1:
                    if segs[next][0] <= seg[1]:
                        epos += 1
                        continue
                    return epos + 1
                else:
                    epos = next
                    continue

            epos += 1
        return sl

    rst = []
    bpos = 0
    epos = 0
    while epos < sl:
        epos = _find_segs(bpos + 1)
        rst.append((bpos, epos))
        bpos = epos
    return rst


def find_nt_paths(txt, segs, dbg=False, rst=None):
    """从segs匹配结果列表中,查找构造nt名称的最佳路径rst"""
    tp = tree_paths_t()
    if len(segs) <= 10:  # 不是特别长的分段,可以直接解析.
        return tp.find(txt, segs, dbg, rst)

    # 长分段,进行必要的拆分处理,避免深度递归耗尽内存.
    sps = split_nt_paths(segs)
    if len(sps) == 1:
        return tp.find(txt, segs, dbg, rst)

    def skip(sr, lseg):
        """基于rst[-1]与sr的首部进行拼接调整"""
        ri = find_right(sr, lseg, 0, 4)
        if ri == 1:
            return
        elif ri == 0:
            while sr:
                seg = sr[0]
                if lseg[0] <= seg[0] and seg[1] <= lseg[1]:
                    sr.pop(0)  # 如果新段的首部完全被旧段的尾部包含,则丢弃
                else:
                    return
            return
        for i in range(ri - 1):
            sr.pop(0)

    if rst is None: rst = []
    for sp in sps:
        st = txt[:segs[sp[1] - 1][1]]
        sr = segs[sp[0]:sp[1]]
        if rst:
            skip(sr, rst[-1])
        sr = tp.find(st, sr, dbg)
        rst.extend(sr)  # 记录每个分段中的最佳路径结果
        tp.clear()
    return rst

# segs = [(0, 2, {('NS', 146), ('NS2', 144)}), (1, 3, {('NN', 133)}), (2, 4, {('NN', 133)}), (2, 5, {('NN', 133)}), (3, 5, {('NA', 132)}), (4, 6, {('NN', 133)}), (5, 7, {('NN', 133)}), (6, 8, {('NN', 133)}), (7, 9, {('NN', 133)}), (7, 10, {('NO', 135)}), (8, 10, {('NO', 135)}), (9, 11, {('NN', 133)}), (10, 12, {('NZ', 150)}), (12, 16, {('NM', 154)}), (16, 18, {('NA', 132)}), (18, 24, {('NU', 134)}), (18, 25, {('NO', 135)}), (19, 21, {('NA', 132)}), (22, 24, {('NA', 132)}), (24, 25, {('NO', 135)})]
# txt = '南充嘉宝堂正红大药房连锁有限公司南部第一百四十六店'
# find_nt_paths(txt, segs)
