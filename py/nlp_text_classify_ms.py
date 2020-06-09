# 对提取的高频短语重新进行词频计算后,再统计BM25需要的IDF词频词典

import mean_shift as ms
import nlp_tiny_bm25 as tb

Q = tb.BM25_Core(tb.TDF_IDF())


# 过滤txts列表中的相互包含的行
def filter_repsub(txts):
    rst = []
    cnt = len(txts)
    for i in range(cnt):
        s1 = txts[i]
        flag = False
        for j in range(i + 1, cnt):
            s2 = txts[j]
            if s2.find(s1) != -1:
                flag = True
                break
        if not flag:
            rst.append(s1)
    return rst


# 计算两个短句的BM25相似度
def sim_bm25_set(set1, set2):
    return Q.sim2p(set1, set2)


# 计算两个短句字列表的杰卡德相似度(字集)
def sim_jaccrad_set(set1, set2):
    icount = 0  # 统计交集数量
    for i in set1:
        if i in set2:
            icount += 1
    ucount = len(set1) + len(set2) - icount  # 计算并集数量
    return icount / ucount


# 基于txts短语列表的文字合集的相对距离进行短语的整体排序
def sims_xsort_distance(txts, txts_dict, sim_fn):
    """txts:短语列表['短语1','短语2',...]
       txts_dict:短语与对应的字集映射
       sim_fn:相似度计算函数,入参为字集
       返回值:结果列表[(短语n,距离n),(短语k,距离k),...]
    """
    cnt = len(txts)

    tolset = set()
    for i in range(cnt):
        s = txts[i]
        txts_dict[s] = set(tb.preproc_doc(s))  # 记录短语对应的字集
        tolset = tolset.union(txts_dict[s])  # 记录短句的合并字集

    # 全部短句与合并字集进行相似度距离计算
    dnlst = [(txts[i], int((1 - sim_fn(txts_dict[txts[i]], tolset)) * 100)) for i in range(cnt)]
    # 根据相似度距离进行排序
    return sorted(dnlst, key=lambda x: x[1])


# 基于文字合集的y向距离进行排序
def sims_ysort_distance(txts, txts_dict, sim_fn):
    """txts:短语列表['短语1','短语2',...]
       txts_dict:短语与对应的字集映射
       sim_fn:相似度计算函数,入参为字集
    """
    cnt = len(txts)

    tolset = set()
    for i in range(cnt):
        s = txts[i]
        if len(tolset) == 0:
            tolset = tolset.union(txts_dict[s])  # 记录短句的合并字集
        else:
            tolset = tolset.intersection(txts_dict[s])

    # 全部短句与合并字集进行相似度距离计算
    dnlst = [(txts[i], int((1 - sim_fn(txts_dict[txts[i]], tolset)) * 100)) for i in range(cnt)]
    # 根据相似度距离进行排序
    return sorted(dnlst, key=lambda x: x[1])


def mean_result_sort(ids):
    """对最终结果进行分拣"""
    rst = {}
    for i in range(len(ids)):
        k = ids[i]
        if k in rst:
            rst[k].append(i)
        else:
            rst[k] = [i]
    return rst


def mean_ptx_sort(txts_lst):
    """对初步的x分布结果进行分拣"""
    rst = {}
    for i in txts_lst:
        k = i[1]
        if k in rst:
            rst[k].append(i[0])
        else:
            rst[k] = [i[0]]
    return rst


# 在词典dct中给定的key位置k的上下,寻找最接近的k(先下后上)
def find_int_key_pos(dct, k, ulimit=100):
    if k in dct:
        return k
    for p in range(k, -1, -1):
        if p in dct:
            return p
    for p in range(k, ulimit):
        if p in dct:
            return p
    return -1


# 基于meanshift算法的短语分类器功能封装
class ss_mean_shift_t:
    def __init__(self, mode='BM25'):
        self.txts_dct = {}
        self.txts_pts = {}
        if mode == 'BM25':
            self.sim_fn = sim_bm25_set
        else:
            self.sim_fn = sim_jaccrad_set

        self.mean = ms.MeanShift(self._sim_distance)
        self.mean.usrdat = self
        self.mean.CLUSTER_THRESHOLD = 35
        self.mean.STOP_THRESHOLD = 10
        self.mean.bandwidth = 2

    # 给meanshift提供两个短句的距离计算函数
    @staticmethod
    def _sim_distance(usrdat, a, b):
        ax = find_int_key_pos(usrdat.txts_pts, round(a[0]))
        ay = find_int_key_pos(usrdat.txts_pts[ax], round(a[1]))
        bx = find_int_key_pos(usrdat.txts_pts, round(b[0]))
        by = find_int_key_pos(usrdat.txts_pts[bx], round(b[1]))
        sa = usrdat.txts_dct[usrdat.txts_pts[ax][ay]]
        sb = usrdat.txts_dct[usrdat.txts_pts[bx][by]]
        sim = usrdat.sim_fn(sa, sb)
        return (1 - sim) * 100

    def _dist_points(self,txts_lst):
        """进行短句的坐标点分布计算"""
        x_map = mean_ptx_sort(txts_lst)  # 先按原点距离进行分类
        self.txts_pts = {}

        for x in x_map:  # 再按原点距离分类结果进行x正向遍历
            txts = x_map[x]  # 得到当前x处的y轴正向短语列表
            if len(txts) == 1:
                self.txts_pts[x] = {0: txts[0]}
            else:
                ylst = sims_ysort_distance(txts, self.txts_dct, self.sim_fn)  # 对当前短语列表进行y方向距离排序
                self.txts_pts[x] = {}
                for t in ylst:
                    self.txts_pts[x][len(self.txts_pts[x])] = t[0]

        txts_points = []
        for x in self.txts_pts:
            ydct = self.txts_pts[x]
            for y in ydct:
                txts_points.append([x, y])
        return txts_points

    def _make_result(self, clsdct, points):
        """根据分拣结果与伪坐标,生成最终的分类结果"""
        rst = {}
        cnt = len(points)
        for c in clsdct:
            lst = clsdct[c]
            rst[c] = []
            for l in lst:
                if l >= cnt:
                    break
                p = points[l]
                rst[c].append(self.txts_pts[p[0]][p[1]])
        return rst

    def fit(self, txts):
        """对txts短语列表进行分类计算"""
        self.txts_dct.clear()
        txts = filter_repsub(txts)  # 过滤掉相互包含的短语
        txts_lst = sims_xsort_distance(txts, self.txts_dct, self.sim_fn)  # 进行短语在x方向上的排序
        points = self._dist_points(txts_lst)  # 再进行短语在y方向上的分布处理,得到映射后的伪坐标

        sp, ids = self.mean.fit(points)  # 基于伪坐标进行短语的相似度分类
        clsdct = mean_result_sort(ids)  # 对分类结果进行分拣
        return self._make_result(clsdct, points)  # 生成最终的短句分拣结果


if __name__ == '__main__':
    txts = ['玻璃器皿',
            '实验室 玻璃器皿',
            '玻璃器皿 清洗',
            '玻璃器皿 耗材',
            '玻璃器皿 检定',
            '实验室 玻璃器皿 清洗',
            '全自动 玻璃器皿',
            '玻璃器皿 类',
            '用 玻璃器皿',
            '玻璃器皿 清洗机',
            '玻璃器皿 清洗 消毒机',
            '玻璃器皿 材料',
            '全自动 玻璃器皿 清洗机',
            '化学试剂 和 玻璃器皿',
            '餐饮 玻璃器皿',
            '君正 化工 玻璃器皿',
            '玻璃器皿 耗材 试剂',
            '实验 用 玻璃器皿',
            '不锈钢 餐具 台面 用具 玻璃器皿 酒吧',
            '实验室 玻璃器皿 清洗 消毒机',
            '化学试剂 玻璃器皿',
            '玻璃器皿 实验教学 物资',
            '玻璃器皿 框架',
            '玻璃器皿 类 实训 耗材',
            '化验室 玻璃器皿',
            '玻璃器皿 代储',
            '玻璃器皿 清洗 消毒 系统',
            '常规 玻璃器皿',
            '类 玻璃器皿',
            '化验 玻璃器皿',
            '玻璃器皿 检定 服务项目',
            '不锈钢 玻璃器皿',
            '玻璃器皿 全段 整',
            '化学药品 玻璃器皿']


    def dbg_print_result(rst):
        """调试输出分类结果"""
        for c in rst:
            lst = rst[c]
            for l in lst:
                print(l)
            print('---')


    Q.idf_dict.load('./data/title_ss_rc')
    m = ss_mean_shift_t()
    rst = m.fit(txts)
    dbg_print_result(rst)
