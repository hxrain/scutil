'''
    NT组份解析器:进行NER/NT构成组份的分析,并可基于构成组份进行NT校验.
    1 提供NT组分解析功能,可用构建组份词典
    2 基于NT组份词典,提供NT名称校验功能
    3 基于NT组份词典,提供NT名称补全功能
'''
import re
from inspect import isfunction
from copy import deepcopy
from collections.abc import Iterable

import util_base as ub
import uni_blocks as uni
import match_ac as mac
import match_util as mu
import china_area_id as cai
import nlp_ner_data as nnd
from nlp_ner_data import types
import os


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

    def __init__(self):
        self.clear()

    def clear(self):
        self.root = tree_paths_t.node_t()
        self.ends = []

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

    def _score(self, seg, nseg, txt):
        """根据seg与nseg前后两个分段的关系,计算nseg路径节点的积分,返回值:(惩罚扣分,奖励积分)
            1 使用独立的分类积分标准
            2 线性增减积分便于评估,也提高了长段的权重.
            3 原则上仅对有效部分进行积分
        """
        # 根据前后分段的类型得到积分标准
        SS = {'X': 0, 'A': 4, 'U': 4, 'N': 5, 'H': 7, 'S': 7, 'Z': 7, 'F': 6, 'L': 8, 'O': 7, 'B': 6, 'M': 7}
        segt = SS[types.tag(seg[2])]
        nsegt = SS[types.tag(nseg[2])]
        if mu.slen(nseg) == 1:
            nsegt -= 1
        ds = 0
        if nseg[0] > seg[1]:  # 前后段分离
            ds = nseg[0] - seg[1]  # 间隔长度扣分
            if ds == 1 and txt[seg[1]] in {'(', ')', '<', '>', '"', "'"}:
                ds = 0  # 特殊字符的空白间隔不扣分
            else:
                ds *= 5
            ns = (nseg[1] - nseg[0]) * nsegt  # 自身长度加分
        elif seg[1] > nseg[0]:  # 前后段交叉
            if seg[1] - nseg[0] >= 2 and seg[2] & nseg[2] & {types.NZ, types.NN}:
                ds = 0  # 特定重叠双字的情况
            elif seg[1] - nseg[0] >= 2 and seg[2] & {types.NM, types.NO, types.NS, types.NZ, types.NN, types.NU} and nseg[2] & {types.NM, types.NO, types.NB}:
                ds = 0  # 特定重叠多字的情况,不扣分
            elif seg[1] - nseg[0] == 1 and nseg[1] - seg[0] == 3 and seg[2] & {types.NA, types.NN} and nseg[2] & {types.NA, types.NN}:
                ds = 0
            else:
                ds = (seg[1] - nseg[0]) * 3  # min(segt, nsegt)  # 根据相交长度与前后类型标准分,进行扣除
            ns = (nseg[1] - seg[1]) * nsegt  # 前后相交,仅计算后段剩余部分
        else:  # 前后相邻
            ns = (nseg[1] - nseg[0]) * nsegt  # 正常情况,仅计算完整的后段积分
        return ns, ds

    def _chk_path(self, txt, segs, pnode, pseg, nseg):
        """检查当前路径是否需要被放弃"""
        if pnode.parent is None:
            return False
        if pnode.parent.sidx is not None:
            fseg = segs[pnode.parent.sidx]
            if fseg[1] == nseg[0]:
                if fseg[0] < pseg[0] < fseg[1] and nseg[0] < pseg[1] < nseg[1]:
                    return True  # 出现了pseg被fseg和nseg完整涵盖的情况,放弃当前路径
        return False

    def _loop(self, txt, segs, pnode, badlimit=4):
        """核心方法,进行深度优先遍历,构建有效的路径树"""
        pseg = segs[pnode.sidx]
        nexts = tree_paths_t._take_nexts(pnode.sidx, segs)
        if not nexts:  # 没有后续节点了,当前节点就是本路径的终点,记录当前结果
            txtl = len(txt)
            if not self.ends or pseg[1] == txtl or (pseg[1] == txtl - 1 and txt[-1] == ')'):
                if self.ends and self.ends[-1].total[1] >= badlimit:
                    self.ends.pop(-1)  # 如果之前存在着临时的坏结果,则丢弃
                self.ends.append(pnode)
            return

        for nidx in nexts:
            nseg = segs[nidx]
            score = self._score(pseg, nseg, txt)  # 当前路径节点分
            total = (pnode.total[0] + score[0], pnode.total[1] + score[1])
            if total[1] >= badlimit and len(self.ends) >= 1:
                continue  # 发现继续走下去惩罚积分较大,则当前路径被剪枝放弃
            if self._chk_path(txt, segs, pnode, pseg, nseg):
                continue  # 出现了无效匹配的情况,放弃当前路径
            if self.ends:
                lnode = self.ends[-1]  # 已经存在的最新端点
                if total[1] > lnode.total[1] + 1:
                    continue  # 路径走到中间的时候扣分已经大于存在的结果了,那么剩余路径不用尝试了
                if pnode.deep + 1 > lnode.deep and total[0] <= lnode.total[0]:
                    continue  # 路径深度大于已有结果,且总分也小于它,则放弃当前路径

            node = tree_paths_t.node_t()  # 生成当前节点
            node.sidx = nidx  # 记录当前节点对应的分段索引
            node.parent = pnode  # 记录父节点
            node.deep = pnode.deep + 1  # 当前路径节点的深度
            node.score = score  # 当前路径节点积分
            node.total = total  # 路径总分
            node.variance = pnode.variance + abs(mu.slen(nseg) - mu.slen(pseg))  # 累积分段长度差
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

    def _take(self, txt, segs, showdbg):
        """根据末端列表选取最优路径,作为最终结果"""
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

        def filter_nt(ends):
            """尝试过滤筛除非nt端点路径,若存在NT尾缀端点,则其他非NT尾缀端点均丢弃"""
            rms = []
            for i, node in enumerate(ends):
                seg = segs[node.sidx]
                if not seg[2] & {types.NM, types.NO, types.NB}:
                    rms.append(i)
            if len(rms) == len(ends):
                return False  # 所有端点都不是nt,则不处理
            for i in reversed(rms):
                ends.pop(i)  # 否则丢弃非nt尾缀的路径
            return True

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
                tsl = sorted(tops[ts], key=lambda i: 0 - ends[i].total[1], reverse=True)
                for i in range(1, len(tsl)):
                    if ends[tsl[i]].total != ends[tsl[0]].total:
                        rms.append(tsl[i])

            for i in sorted(rms, reverse=True):
                ends.pop(i)  # 删除所有不被保留的路径节点

        # 通过积分评价排序,筛选得到最优结果路径
        filter_top(self.ends)
        have_nt = filter_nt(self.ends)  # 尝试预先筛选丢弃非NT结尾的路径

        if showdbg and showdbg > 1:
            print(f"---->filter<----")
            showdbg = len(self.ends)
            for end in self.ends:
                pd = self._path_dbg(end, txt, segs)
                print(f'  {"|".join(pd)}')

        if len(self.ends) > 1:
            # 排序规则:最少扣分且最短的路径下的最高有效分
            ends = sorted(self.ends, key=lambda x: (0 - x.total[1], 0 - x.deep, x.total[0] - x.total[1], 0 - x.variance), reverse=True)
            node = ends[0]
        else:
            node = self.ends[0]

        if showdbg and showdbg > 1:
            pd = self._path_dbg(node, txt, segs)
            print(f'>>{"|".join(pd)}')

        rst = []
        # 根据最优路径的端点逆向重构完整的分段结果
        while node.parent is not None:
            rst.insert(0, segs[node.sidx])
            node = node.parent
        return rst

    def find(self, txt, segs, showdbg=False):
        """基于文本txt的分段匹配列表segs,查找最优路径"""
        if not txt or not segs:
            return []
        if len(segs) == 1:
            return list(segs)

        nexts = tree_paths_t._take_first(0, segs)
        seg = (0, segs[nexts[0]][0], types.tags_NX)
        for nidx in nexts:
            nseg = segs[nidx]
            node = tree_paths_t.node_t()  # 生成当前节点
            node.sidx = nidx  # 记录当前节点对应的分段索引
            node.deep = self.root.deep + 1
            node.parent = self.root  # 记录根节点
            node.total = node.score = self._score(seg, nseg, txt)  # 路径节点分
            self.root.childs.append(node)  # 记录当前节点
            self._loop(txt, segs, node)  # 深度遍历新节点路径

        return self._take(txt, segs, showdbg)  # 提取最终结果


def find_nt_paths(txt, segs, dbg=False):
    """从segs匹配结果列表中,查找构造nt名称的最佳路径"""
    tp = tree_paths_t()
    return tp.find(txt, segs, dbg)


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需给出尽量准确的分词结果,而本解析器则尝试进行组合覆盖,给出覆盖后的分段特征结果.
    '''

    @staticmethod
    def __nu_rec(lst, mres, typ, offset=0):
        """记录数字匹配结果"""

        def rec(lst: list, seg):
            """记录匹配结果,规避多条规则的重复匹配分段,保留高优先级结果"""
            for i in range(len(lst) - 1, -1, -1):
                pseg = lst[i]
                # if (pseg[1] > seg[0] and pseg[1] <= seg[1]) or (pseg[0] >= seg[0] and pseg[0] < seg[1]):
                if pseg[0] >= seg[0] and pseg[1] <= seg[1]:
                    if types.cmp(pseg[2], seg[2]) < 0 or (types.tags_NU & pseg[2] and types.tags_NO & seg[2]):
                        lst.pop(i)  # 先进行一圈查找,如果存在与新分段重叠的段,则保留高优先级的分段.
                        continue
                if pseg[0] <= seg[0] and seg[1] <= pseg[1]:
                    return  # 存在长匹配,则丢弃当前短匹配
            if len(lst) >= 2:
                fseg = lst[-2]
                if fseg[1] == seg[0] and types.tags_NS.issubset(fseg[2]) and seg[2] & {types.NS, types.NO}:
                    lst.pop(-1)  # 前后是NS+NU,则丢弃NU,记录新的

            for i in range(len(lst)):
                pseg = lst[i]
                if seg[0] <= pseg[0]:
                    lst.insert(i, seg)
                    return
            lst.append(seg)

        if typ & types.tags_NM:
            for m in mres:
                grp2 = m.group(2)
                if grp2[0] in {'分'}:
                    tag = types.tags_NUNB
                else:
                    tag = types.tags_NUNM

                rge = m.span()
                seg = (rge[0] + offset, rge[1] + offset, tag)
                rec(lst, seg)
        else:
            for m in mres:
                rge = m.span()
                seg = (rge[0] + offset, rge[1] + offset, typ)
                rec(lst, seg)

    # 数字序号基础模式
    num_re = r'[A-Z×\.&+○O\d甲乙丙丁戊己庚辛壬癸丑寅卯辰巳午未申酉戌亥零一二三四五六七八九十幺壹贰貮貳两叁参仨肆伍陆柒捌玖拾佰伯百千仟万廿卅IⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]'
    _oc_nums = ['匕', '比', '彼', '必', '毕', '碧', '卞', '变', '表', '别', '宾', '彬', '斌', '滨', '冰', '缤', '兵', '秉', '炳', '并', '波', '伯', '帛', '泊', '铂', '博', '亳', '渤', '搏', '卜', '补', '不', '布',
                '步', '擦', '才', '材', '财', '采', '彩', '菜', '蔡', '餐', '灿', '仓', '璨', '苍', '沧', '藏', '曹', '草', '策', '岑', '层', '曾', '叉', '插', '茶', '茬', '查', '搽', '差', '柴', '婵', '馋', '禅',
                '蝉', '产', '昌', '尝', '常', '昶', '畅', '超', '晁', '朝', '潮', '车', '屮', '澈', '扯', '琛', '臣', '尘', '辰', '沉', '陈', '宸', '晨', '成', '丞', '呈', '诚', '承', '乘', '程', '澄', '橙', '池',
                '驰', '迟', '持', '齿', '尺', '赤', '虫', '崇', '宠', '抽', '仇', '出', '初', '除', '厨', '储', '楚', '褚', '川', '欻', '穿', '传', '船', '串', '闯', '创', '锤', '垂', '春', '纯', '淳', '醇', '词',
                '瓷', '辞', '此', '慈', '次', '聪', '从', '丛', '崔', '催', '脆', '萃', '存', '翠', '寸', '岱', '代', '戴', '丹', '黛', '单', '旦', '但', '淡', '蛋', '当', '刀', '稻', '道', '到', '得', '德', '灯',
                '登', '邓', '滴', '狄', '迪', '荻', '涤', '地', '邸', '弟', '帝', '递', '谛', '蒂', '缔', '棣', '滇', '颠', '典', '点', '电', '佃', '甸', '殿', '惦', '刁', '叼', '叠', '蝶', '碟', '叮', '町', '顶',
                '酊', '鼎', '定', '丢', '冬', '董', '懂', '动', '栋', '冻', '洞', '都', '兜', '抖', '蚪', '斗', '豆', '窦', '逗', '独', '杜', '度', '镀', '渡', '端', '对', '敦', '蹲', '炖', '盾', '顿', '多', '朵',
                '俄', '峨', '娥', '额', '鄂', '诶', '恩', '摁', '嗯', '而', '尔', '珥', '洱', '发', '伐', '阀', '法', '帆', '番', '翻', '凡', '烦', '樊', '繁', '反', '饭', '泛', '范', '梵', '方', '芳', '坊', '房',
                '访', '仿', '纺', '放', '飞', '妃', '非', '菲', '啡', '肥', '斐', '翡', '沸', '废', '费', '分', '芬', '氛', '汾', '粉', '份', '奋', '丰', '风', '沣', '枫', '吖', '阿', '啊', '哎', '埃', '艾', '爱',
                '安', '鞍', '岸', '昂', '凹', '敖', '傲', '奥', '澳', '巴', '叭', '白', '柏', '班', '板', '半', '邦', '帮', '榜', '包', '煲', '保', '贝', '倍', '奔', '贲', '犇', '本', '芭', '泰', '涵', '浩', '合',
                '弘', '辉', '佳', '简', '久', '聚', '君', '俊', '酷', '磊', '廖', '凌', '领', '隆', '米', '楠', '鹏', '启', '秋', '全', '瑞', '睿', '盛', '时', '顺', '威', '吾', '喜', '晓', '欣', '鑫', '熊', '亚',
                '衣', '亿', '意', '哲', '智', '卓', '冯', '福', '伽', '广', '国', '好', '恒', '花', '皇', '嘉', '杰', '京', '静', '酒', '娟', '凯', '康', '可', '来', '林', '霖', '玲', '满', '铭', '念', '牛', '品',
                '萍', '普', '乔', '荣', '锐', '赛', '森', '申', '神', '食', '舒', '思', '涛', '拓', '网', '微', '魏', '悟', '熙', '贤', '祥', '萧', '谢', '雄', '许', '旭', '彦', '艳', '叶', '伊', '依', '易', '银',
                '优', '尤', '圆', '悦', '忠', '子', '谷', '哈', '豪', '黑', '慧', '家', '晋', '景', '巨', '卡', '堃', '黎', '丽', '梁', '琳', '洛', '麦', '曼', '孟', '喵', '苗', '名', '墨', '娜', '胖', '齐', '奇',
                '琪', '琦', '清', '庆', '屈', '融', '茹', '润', '少', '帅', '爽', '素', '速', '太', '覃', '天', '韦', '唯', '维', '温', '吴', '武', '希', '湘', '向', '秀', '徐', '薛', '言', '洋', '耀', '艺', '逸',
                '尹', '勇', '有', '余', '雨', '月', '粤', '增', '真', '正', '钟', '众', '朱', '紫', '峰', '锋', '顾', '贵', '杭', '皓', '禾', '何', '嗨', '宏', '荟', '火', '健', '蒋', '晶', '井', '靖', '菊', '骏',
                '楷', '柯', '魁', '坤', '兰', '蓝', '佬', '亮', '猫', '美', '莫', '木', '纳', '年', '潘', '彭', '其', '乾', '巧', '任', '如', '圣', '晟', '施', '世', '书', '蜀', '树', '索', '淘', '腾', '甜', '婷',
                '童', '薇', '伟', '雯', '舞', '鲜', '香', '学', '颜', '益', '迎', '友', '佑', '媛', '苑', '运', '再', '泽', '珍', '臻', '重', '祖', '凤', '付', '富', '龚', '冠', '桂', '航', '昊', '荷', '泓', '鸿',
                '厚', '欢', '焕', '汇', '集', '冀', '坚', '今', '锦', '恺', '科', '快', '浪', '乐', '雷', '冷', '灵', '卢', '鹿', '禄', '漫', '慢', '茂', '梦', '奈', '宁', '欧', '盘', '庞', '培', '皮', '强', '琼',
                '权', '仁', '日', '阮', '商', '尚', '邵', '胜', '硕', '苏', '孙', '碳', '糖', '陶', '廷', '佟', '图', '途', '翁', '无', '夕', '霞', '仙', '筱', '心', '燕', '夜', '怡', '忆', '英', '盈', '悠', '游',
                '羽', '源', '远', '跃', '云', '詹', '郑', '之', '知', '洲', '宗', '格', '郭', '果', '赫', '横', '虹', '洪', '胡', '虎', '话', '会', '惠', '霍', '吉', '纪', '加', '将', '炯', '均', '克', '腊', '赖',
                '利', '良', '辽', '鲁', '吕', '绿', '梅', '门', '免', '敏', '明', '缪', '沐', '倪', '聂', '派', '祁', '棋', '企', '起', '钱', '蔷', '琴', '勤', '青', '冉', '染', '善', '诗', '石', '仕', '守', '斯',
                '松', '唐', '棠', '特', '添', '恬', '同', '为', '玮', '文', '闻', '午', '享', '项', '幸', '轩', '雅', '延', '严', '岩', '衍', '扬', '姚', '义', '莹', '赢', '应', '永', '由', '玉', '元', '袁', '允',
                '韵', '赞', '章', '兆', '赵', '振', '芝', '仲', '周', '梓', '自', '邹', '佐', '奉', '戈', '歌', '葛', '根', '耿', '宫', '共', '古', '韩', '汉', '行', '郝', '号', '核', '红', '黄', '徽', '季', '济',
                '姜', '津', '进', '精', '军', '咖', '开', '孔', '昆', '辣', '郎', '连', '龙', '伦', '罗', '毛', '么', '蒙', '咪', '蜜', '淼', '魔', '陌', '慕', '乃', '尼', '柠', '诺', '盼', '沛', '佩', '朋', '期',
                '钦', '秦', '沁', '晴', '泉', '雀', '汝', '仨', '什', '沈', '升', '实', '首', '淑', '宋', '谭', '汤', '桃', '滕', '玩', '王', '卫', '沃', '唔', '禧', '细', '现', '翔', '肖', '玄', '炫', '雪', '炎',
                '阳', '杨', '尧', '要', '亦', '懿', '隐', '印', '樱', '营', '俞', '渝', '宇', '昱', '岳', '展', '志', '舟', '珠', '足', '钻', '最', '尊', '改', '钙', '甘', '高', '阁', '观', '归', '锅', '憨', '邯',
                '寒', '亨', '衡', '呼', '怀', '淮', '极', '继', '贾', '尖', '剑', '匠', '瑾', '菁', '璟', '峻', '咔', '客', '空', '扣', '莱', '岚', '力', '栗', '靓', '柳', '珑', '玛', '迈', '芒', '卯', '枚', '弥',
                '觅', '妙', '闽', '茗', '那', '难', '裴', '平', '戚', '祺', '且', '芹', '轻', '卿', '热', '仍', '闰', '绍', '深', '双', '梯', '宛', '晚', '皖', '未', '味', '兮', '夏', '先', '想', '潇', '孝', '形',
                '杏', '绪', '勋', '烟', '晏', '羊', '吆', '业', '以', '谊', '毅', '饮', '颖', '咏', '于', '瑜', '禹', '钰', '喻', '御', '煜', '耘', '翟', '占', '湛', '昭', '浙', '甄', '争', '猪', '住', '祝', '孖',
                '尕', '刚', '哥', '公', '勾', '关', '官', '氿', '贺', '候', '沪', '铧', '化', '幻', '回', '珈', '胶', '洁', '捷', '荆', '旌', '鲸', '敬', '桔', '钧', '亢', '寇', '匡', '拉', '劳', '璃', '里', '立',
                '莉', '俩', '列', '临', '淋', '令', '留', '露', '栾', '茅', '萌', '绵', '闵', '鸣', '摩', '牟', '耐', '攀', '朴', '迁', '倩', '俏', '氢', '邱', '球', '然', '蓉', '儒', '蕊', '若', '桑', '沙', '杉',
                '史', '士', '数', '水', '舜', '泗', '隋', '岁', '琐', '塔', '檀', '体', '挑', '条', '通', '彤', '桐', '铜', '潼', '涂', '丸', '汪', '望', '蔚', '锡', '霄', '芯', '薪', '修', '宣', '讯', '闫', '研',
                '垚', '宜', '奕', '音', '殷', '寅', '鹰', '屿', '语', '裕', '园', '越', '芸', '仔', '在', '侦', '支', '纸', '致', '竹', '庄', '准', '作', '烽', '逢', '伏', '芙', '符', '复', '傅', '盖', '概', '个',
                '亘', '氦', '湖', '骅', '画', '洹', '寰', '煌', '际', '姣', '焦', '节', '解', '介', '巾', '劲', '卷', '隽', '忾', '宽', '阔', '勒', '礼', '李', '廉', '菱', '刘', '鎏', '落', '马', '媚', '魅', '民',
                '默', '牧', '穆', '奶', '能', '妮', '炮', '丕', '拼', '亓', '麒', '丘', '求', '趣', '人', '容', '芮', '衫', '莳', '室', '寿', '瘦', '曙', '述', '丝', '塑', '随', '田', '仝', '土', '佤', '旺', '巍',
                '圩', '惟', '潍', '炜', '巫', '汐', '溪', '习', '显', '馨', '信', '兴', '休', '宿', '序', '悬', '丫', '妍', '仰', '瑶', '野', '屹', '影', '拥', '雍', '油', '又', '柚', '虞', '誉', '豫', '缘', '昀',
                '早', '粥', '著', '综', '服', '附', '淦', '杠', '更', '拱', '贡', '固', '瓜', '管', '瀚', '濠', '鹤', '侯', '扈', '环', '晃', '晖', '机', '姬', '几', '见', '江', '娇', '接', '衿', '婧', '铠', '坎',
                '抗', '蔻', '库', '邝', '况', '葵', '朗', '理', '粮', '妹', '迷', '谜', '面', '冥', '茉', '沫', '睨', '暖', '哦', '磐', '配', '娉', '珀', '蒲', '恰', '虔', '浅', '曲', '圈', '饶', '荏', '扔', '撒',
                '莎', '姗', '珊', '佘', '燊', '生', '师', '是', '术', '束', '搜', '粟', '缇', '醍', '庭', '兔', '弯', '万', '稳', '邬', '梧', '务', '物', '曦', '虾', '侠', '氙', '闲', '宪', '骁', '邢', '醒', '胥',
                '叙', '旋', '迅', '雁', '焱', '窑', '烨', '仪', '已', '映', '用', '敔', '遇', '蕴', '杂', '则', '宅', '战', '召', '照', '者', '政', '枝', '治', '肿', '柱', '抓', '转', '追', '资', '醉', '甫', '辅',
                '阜', '副', '干', '鸽', '艮', '工', '弓', '功', '苟', '狗', '过', '晗', '翰', '灏', '呵', '嘿', '互', '桦', '伙', '鸡', '积', '基', '技', '金', '净', '珺', '珂', '旷', '框', '澜', '狼', '蕾', '梨',
                '逦', '历', '联', '恋', '两', '伶', '苓', '娄', '泸', '卤', '麻', '嫚', '冒', '命', '男', '凝', '钮', '帕', '莆', '璞', '谦', '签', '黔', '茜', '桥', '阙', '群', '苒', '色', '傻', '韶', '绅', '莘',
                '昇', '狮', '饰', '收', '黍', '竖', '税', '绥', '穗', '台', '邰', '藤', '蹄', '统', '推', '婉', '尉', '汶', '乌', '晤', '奚', '纤', '响', '续', '选', '压', '鸭', '沿', '氧', '恙', '漾', '妖', '翼',
                '唷', '渔', '予', '育', '沅', '约', '臧', '枣', '扎', '张', '丈', '钊', '喆', '震', '征', '峥', '直', '走', '遵', '孚', '抚', '负', '该', '各', '耕', '柜', '夯', '琥', '户', '桓', '卉', '绘', '僵',
                '交', '皆', '桀', '婕', '近', '靳', '竟', '汣', '橘', '举', '珏', '阚', '捞', '俪', '脸', '练', '凉', '烈', '猎', '邻', '翎', '浏', '泷', '潞', '仑', '轮', '螺', '律', '玫', '每', '猛', '秒', '旻',
                '磨', '末', '某', '拿', '柰', '偶', '葩', '拍', '蓬', '屏', '坡', '绮', '芊', '遣', '切', '亲', '去', '鹊', '燃', '戎', '榕', '乳', '萨', '晒', '陕', '式', '输', '烁', '淞', '送', '钛', '谈', '潭',
                '探', '韬', '提', '替', '挺', '筒', '头', '问', '窝', '我', '惜', '熹', '玺', '限', '相', '橡', '笑', '效', '协', '忻', '昕', '新', '禤', '盐', '页', '弋', '异', '邑', '燚', '甬', '酉', '员', '赟',
                '砸', '载', '樟', '长', '这', '只', '制', '种', '主', '壮', '封', '夫', '浮', '尬', '垓', '赣', '岗', '港', '皋', '革', '购', '钴', '怪', '皈', '海', '函', '和', '盒', '华', '滑', '槐', '换', '浣',
                '嵇', '即', '剪', '键', '酱', '蛟', '觉', '泾', '鞠', '钜', '郡', '浚', '烤', '奎', '琨', '锟', '鲲', '琅', '廊', '厉', '励', '链', '麟', '蔺', '铃', '聆', '另', '琉', '陇', '楼', '撸', '芦', '庐',
                '璐', '鹭', '乱', '络', '珞', '蔓', '檬', '芈', '幂', '棉', '咩', '谋', '目', '幕', '闹', '糯', '瓯', '芃', '毗', '啤', '濮', '栖', '淇', '骑', '洽', '戗', '倾', '情', '擎', '渠', '让', '柔', '肉',
                '偌', '飒', '厦', '赏', '奢', '笙', '绳', '识', '使', '拴', '瞬', '偲', '嵩', '颂', '俗', '她', '坛', '塘', '忒', '听', '暾', '瓦', '湾', '往', '围', '纹', '雾', '昔', '嘻', '席', '弦', '献', '襄',
                '象', '枭', '校', '蟹', '虚', '栩', '煊', '璇', '巽', '芽', '遥', '椰', '医', '颐', '乂', '驿', '溢', '因', '鄞', '胤', '涌', '郁', '毓', '垣', '雲', '灶', '折', '针', '整', '执', '竺', '筑', '专',
                '字', '纵', '奏', '瞓', '蜂', '否', '孵', '噶', '郜', '咯', '跟', '恭', '巩', '拐', '圭', '鲧', '蒿', '珩', '轰', '猴', '护', '凰', '灰', '挥', '或', '获', '计', '减', '椒', '蕉', '界', '竞', '镜',
                '鸠', '就', '句', '炬', '绝', '竣', '刊', '课', '坑', '夸', '蒯', '筷', '览', '懒', '荔', '粒', '涟', '粱', '量', '岭', '龍', '麓', '骆', '嘛', '买', '玟', '牡', '暮', '泥', '鸟', '弄', '努', '鸥',
                '批', '谝', '票', '破', '浦', '岐', '歧', '潜', '堑', '侨', '谯', '茄', '顷', '铨', '确', '桡', '绒', '入', '软', '洒', '彡', '弎', '扫', '闪', '蛇', '舍', '慎', '嵊', '视', '姝', '熟', '霜', '说',
                '寺', '酥', '溯', '遂', '炭', '滔', '题', '帖', '亭', '蛙', '逶', '嗡', '卧', '屋', '冼', '飨', '斜', '歆', '戌', '需', '萱', '铉', '寻', '峋', '循', '训', '牙', '哑', '鄢', '砚', '央', '养', '曜',
                '冶', '祎', '漪', '贻', '移', '阴', '引', '瀛', '硬', '泳', '攸', '幽', '莜', '榆', '渊', '玥', '阅', '咋', '择', '炸', '彰', '掌', '祯', '怔', '蒸', '指', '铸', '拽', '妆', '桌', '灼', '姿', '淄',
                '租', '昨', '疯', '俸', '弗', '扶', '赋', '嘎', '冈', '罡', '告', '给', '沟', '够', '辜', '骨', '鼓', '故', '洸', '规', '诡', '鬼', '还', '亥', '蚝', '阖', '恨', '哼', '乎', '狐', '壶', '蓟', '迦',
                '葭', '菅', '枧', '检', '骞', '建', '鉴', '角', '矫', '叫', '揭', '芥', '谨', '槿', '缙', '境', '决', '爵', '筠', '慷', '刻', '肯', '口', '喾', '困', '垒', '骊', '溧', '瓴', '陵', '绫', '溜', '录',
                '萝', '雒', '旅', '略', '码', '卖', '盲', '茆', '贸', '眉', '镁', '宓', '秘', '密', '珉', '洺', '酩', '膜', '母', '亩', '睦', '你', '逆', '酿', '甯', '拧', '排', '棚', '郫', '匹', '坪', '颇', '葡',
                '綦', '汽', '器', '羌', '芩', '瞿', '取', '绕', '稔', '嵘', '镕', '裳', '烧', '设', '声', '氏', '事', '侍', '试', '释', '手', '抒', '属', '朔', '笋', '他', '态', '坦', '瑭', '疼', '踢', '僮', '抟',
                '坨', '歪', '菀', '碗', '位', '喔', '勿', '洗', '辖', '携', '锌', '星', '岫', '袖', '绣', '须', '煦', '泫', '旬', '浔', '夭', '邀', '晔', '彝', '倚', '译', '绎', '弈', '羿', '翌', '熠', '茵', '瑛',
                '庸', '忧', '寓', '愿', '匀', '郧', '咱', '轧', '斋', '招', '爪', '肇', '贞', '筝', '证', '栀', '植', '止', '芷', '至', '质', '炙', '挚', '稚', '轴', '诸', '逐', '烛', '助', '赚', '隹', '拙', '琢',
                '孜', '兹', '籽', '恣', '投', '水', '珅', '姐', '桩', '州']
    # 数字序号组合模式
    num_rules = [
        (f'([铁农建经纬纵横山钢莲光山华司达大中小老期江海安星煤宝金城片{"".join(_oc_nums)}]+{num_re}{{1,7}})', types.tags_NU, __nu_rec.__func__),
        (f'([东南西北]+{num_re}{{1,7}}[号]?|{num_re}{{1,7}}[东南西北新]+|[东南西北][分])', types.tags_NU, __nu_rec.__func__),
        (f'([第笫上下新A-Z]*{num_re}{{1,7}}[号]?(分钟|小时)?[冶號级大支只届期工次个度批委天时分秒鲜番房船轮家运花阿核肉茶饭公度录吨经纬家郎哥幼条代纺化种停克田针奶口年月日阀杯表等班调医养缸牛兽酿岁继建酒冷轻橡棉邦斤干水齿皮客阁座层室#℃]?)', types.tags_NU, __nu_rec.__func__),
        (f'([铁农建兵第笫经纬纵横新ABCDGKSXYZ]*{num_re}{{1,7}}[号级大支#]*)(公里|马路|社区|号门|号线|组村|[道路弄街里亩线楼栋段桥井闸渠河沟江坝村区师机片台房田])', types.tags_NS, __nu_rec.__func__),
        (f'([铁农建第笫新]*{num_re}{{1,7}}[号]?)([分]?部队|煤矿)', types.tags_NM, __nu_rec.__func__),
        (f'([铁农建第笫新]*{num_re}{{1,7}}[号]?)([分]?院区|柜组|[团校院馆局会矿场社所部处坊])', types.tags_NO, __nu_rec.__func__),
        (f'([铁农建第笫]*{num_re}{{1,7}}[号]?)([分]?营部|工区|分号|仓库|支部|号店|茶楼|[厂店铺站园亭营连排厅仓库])', types.tags_NB, __nu_rec.__func__),
        (f'([铁农建第笫大小老东西南北]*{num_re}{{0,7}}[号]?[分支大中小]?[组队])', types.tags_NB, __nu_rec.__func__),
        (f'([铁农建第笫东南西北]*{num_re}{{1,7}})(职高|[职中小高路街委米条])(?![学])', types.tags_NS, __nu_rec.__func__),

    ]
    # 附加单字填充占位模式
    att_chars = {'省', '市', '区', '县', '乡', '镇', '村', '州', '盟', '旗', '办', '与', '及', '和', '的', '暨', '新', '老', '原', '女', '驻', '东', '南', '西', '北', '路', '街', '道', '港', '至', '段'}
    att_rules = [
        (f'([{"".join(att_chars)}])', types.tags_NA, __nu_rec.__func__),  # 常用单字填充占位
    ]
    # 为了更好的利用地名组份信息,更好的区分主干部分的类型,引入了"!尾缀"标注模式,规则如下:
    # 1 未标注!的行,整体地名(S)进行使用,并在移除尾缀词后,主干部分作为名称(N)使用,等同于标注了!N
    # 2 标注!的且没有字母的,不拆分,将整体作为:地名(S)
    # 3 标注!后有其他字母的,主干部分按标注类型使用: A-弱化名称/S-地名/M-实体/U-序号/N-名称/Z-专业名词/H-特殊词/B-分支
    tag_labels = {'A': types.tags_NA, 'S': types.tags_NS, 'M': types.tags_NM, 'U': types.tags_NU, 'O': types.tags_NO,
                  'N': types.tags_NN, 'Z': types.tags_NZ, 'H': types.tags_NH, 'B': types.tags_NB}

    # 可进行特殊短语包裹的括号对
    brackets_map = {'<': '>', '(': ')', '[': ']', '"': '"', "'": "'"}
    brackets_rmap = {'>': '<', ')': '(', ']': '[', '"': '"', "'": "'"}

    @staticmethod
    def query_nu(txt, nulst=None, offset=0, merge=True):
        """查询txt中的数字相关特征模式,nulst可给出外部数字模式匹配列表.返回值:[b,e,{types}]"""
        rst = []
        if not nulst:
            nulst = nt_parser_t.num_rules
        for pat in nulst:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            pat[2](rst, mres, pat[1], offset)

        if len(txt) == 1:
            for pat in nt_parser_t.att_rules:
                mres = list(re.finditer(pat[0], txt))
                if not mres:
                    continue
                pat[2](rst, mres, pat[1], offset)

        if not rst or not merge:
            return rst
        return nt_parser_t._merge_segs(None, rst, False, False)[0]

    @staticmethod
    def rec_nums(segs, txt, nulst=None, merge=True):
        """根据预匹配分段列表,尝试进行编号分段的补全.返回值:补充的分段数量"""
        num_chars2 = {'第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖', '拾', '零'}
        num_chars3 = {'大', '农', '中'}
        num_chars3.update(num_chars2)

        chks = []

        def chk_num_segs(rsts):
            """分析需要进行数字匹配的分段"""
            nonlocal chks
            seg = rsts[-1]  # 最新段
            idx = len(rsts) - 1  # 当前段索引
            pseg = rsts[-2] if idx else None  # 前一段
            if pseg and seg[1] <= pseg[1]:
                return  # 如果当前段被前段包含则放弃
            seg_is_NA = True if seg[2] and seg[2] & types.tags_NA else False

            def _rec(idx):
                if pseg and (seg[2] is None or seg_is_NA):
                    if pseg[2] is None or types.tags_NA & pseg[2]:
                        rsts[-2] = (pseg[0], seg[1], None)
                        rsts.pop(-1)
                        idx -= 1

                if not chks or chks[-1] != idx:
                    chks.append(idx)

            if seg[2] is None:
                _rec(idx)  # 如果当前是未知段,则记录
                return

            if not seg_is_NA:
                return

            c0 = txt[seg[0]]
            cl = txt[seg[1] - 1]

            if mu.slen(seg) == 1 and c0 not in {'.'}:
                _rec(idx)  # 如果当前是单字NA段,则记录
            elif mu.slen(seg) > 1 and (cl in {'第', '铁', '农', '建'} or c0 in num_chars2 or cl in num_chars2):
                _rec(idx)  # 如果当前是特定多字NA段,则记录

        usegs, uc = mu.complete_segs(segs, len(txt), True, cb=chk_num_segs)  # 得到补全的分段列表
        if not chks:
            return 0

        def skip_next(pos, uidx, usegs):
            """判断txt[pos]是否还需要向后扩展"""
            w_nexts = {'工区', '分号', '部队', '公里', '马路', '社区', '号仓', '分钟', '小时', '职高', '大道', '院区', '支部', '号店'}
            if txt[pos:pos + 2] in w_nexts:
                return pos + 2
            if txt[pos - 1:pos + 1] in w_nexts:
                return pos + 1
            if txt[pos:pos + 2] in {'三门'}:
                return pos + 3
            w_stops = {'营业', '营销', '营养', '营造', '营部', '矿业', '乡镇', '中学', '五金', '百货', '连锁', '冶金', '船舶', '高地', '组货', '门市'}
            if txt[pos:pos + 2] in w_stops:
                return pos
            if txt[pos - 1:pos + 1] in w_stops:
                return pos - 1
            seg = usegs[uidx]
            fseg = usegs[uidx - 1] if uidx else None
            if uidx + 1 < len(usegs):
                if mu.slen(seg) == 1 and txt[pos - 1] in {'第'}:
                    return pos + 1
                nseg = usegs[uidx + 1]
                lseg = usegs[uidx + 2] if uidx + 2 < len(usegs) else None
                if nseg[2]:
                    if nseg[2] & {types.NM, types.NZ, types.NB} or (mu.slen(nseg) >= 2 and nseg[2] & types.tags_NO):
                        return pos  # 后一段是特殊类型,不扩张
                    if nseg[2] & {types.NN, types.NH, types.NS}:
                        if lseg and not lseg[2]:
                            return pos  # 后一段的后面还有空白分段,不扩张
                        if fseg and fseg[1] == nseg[0]:
                            return pos  # 前段与后段相邻,不扩张

                    if nseg[1] - (pos + 1) == 1 and nseg[2] & {types.NS, types.NH, types.NN}:
                        if lseg and nseg[1] - lseg[0] == 1:
                            return pos + 1  # 后段和再后段相交余一,则扩张
                        elif lseg and lseg[2] and types.tags_NA.issubset(lseg[2]) and mu.slen(lseg) >= 3:
                            return pos + 1
                        else:
                            return pos
                    if mu.slen(nseg) == 1 and types.tags_NA.issubset(nseg[2]):
                        return pos + 1
                else:
                    return nseg[1]
            return min(pos + 2, len(txt))

        def skip_prev(pos, uidx, usegs):
            """判断txt[pos]是否还需要向前扩展"""
            if uidx:
                pseg = usegs[uidx - 1]
                if pseg[2] is None:
                    return pos - 1
                if pseg[2] & {types.NM, types.NZ, types.NB, types.NF, types.NS}:
                    return pos
                if mu.slen(pseg) >= 2 and pseg[2] & types.tags_NO:
                    return pos
                if pseg[2] & {types.NN, types.NA}:
                    if uidx >= 2:
                        ppseg = usegs[uidx - 2]
                        if pseg[1] <= ppseg[1] and ppseg[2] & {types.NM, types.NZ, types.NB, types.NF, types.NS}:
                            return pos  # 浦东|东,不涵盖'东'
                        if txt[pseg[0]] in {'东', '南', '西', '北'}:
                            return pos - mu.slen(pseg)
                        if pseg[1] - ppseg[1] == 1:  # 前面两个分段交叉余一
                            return pos - 1
                    if mu.slen(pseg) >= 3 and txt[pseg[1] - 1] in num_chars3:
                        return pos - 1
                    if mu.slen(pseg) == 2 and txt[pseg[1] - 1] in num_chars2:
                        return pos - 1
                    if mu.slen(pseg) == 1:
                        return pos - 1

                    return pos
                if mu.slen(pseg) == 2:
                    return pos
            return pos - 1 if pos else pos

        rst = []
        for uidx in chks:  # 逐一处理未匹配分段
            useg = usegs[uidx]
            if mu.slen(useg) == 1 and txt[useg[0]] in {'(', ')'}:
                continue  # 如果是单独的括号未匹配分段,不处理.

            # 猜测需要进行数字序号抽取的范围集合,提高可用结果的范围.
            b = skip_prev(useg[0], uidx, usegs)  # 向前扩张
            e = skip_next(useg[1], uidx, usegs)  # 向后扩张
            rgns = {(b, e)}
            if b != useg[0] or e - b > 2:
                rgns.add((b + 1, e))
                rgns.add((b, e - 1))
            if e >= useg[1]:
                rgns.add((useg[0], useg[1]))
            if mu.slen(useg) == 2:
                rgns.add((useg[0], useg[1] - 1))
            if mu.slen(useg) >= 2:
                if txt[useg[0]] in {'(', ')', '>'}:
                    rgns.add((useg[0] + 1, useg[1]))
                if txt[useg[0]] in nt_parser_t.att_chars:
                    rgns.add((useg[0], useg[0] + 1))
                if txt[useg[1] - 1] in nt_parser_t.att_chars:
                    rgns.add((useg[1] - 1, useg[1]))

            for rgn in rgns:
                s = txt[rgn[0]:rgn[1]]
                nums = nt_parser_t.query_nu(s, nulst, rgn[0], merge)  # 进行数字序号匹配
                nt_parser_t._merge_nums(rst, nums)

        nt_parser_t._merge_nums(segs, rst)  # 合并数字序号分段到整体结果中
        return len(rst)

    @staticmethod
    def chk_nums(words, nulst=None):
        """校验words中是否含有序号分段.返回值:[匹配的分段信息]"""
        segs = []
        nt_parser_t.rec_nums(segs, words, nulst)
        return segs

    def __init__(self, light=False):
        self.matcher = mac.ac_match_t()  # 定义ac匹配树
        self._bads = self.make_tails_bads()  # 尾缀坏词匹配器
        self.nsa_type_maps = {}  # 临时使用,地名简称类型转换映射表
        self.listen_cb_wordadd = None  # 监听词汇添加动作的回调方法
        if light:
            self.load_nt(isend=False)
            self.load_ns(isend=True)

    @staticmethod
    def make_tails_bads():
        """利用内置NT组份表构造坏词匹配器"""
        trie = mu.words_trie_t(True)  # 反向匹配器
        for tn in nnd.nt_tails:
            bads = nnd.nt_tails[tn]['-']
            for en in bads:  # 记录排斥词汇
                trie.add(en)
        return trie

    def __load(self, isend, fname, tags, encode='utf-16', vals_cb=None, chk_cb=None):
        """装载词典文件fname并绑定数据标记tags,返回值:''正常,否则为错误信息."""
        if fname is None:
            return None

        def add_word(word, tag, row, txt):
            ret, old = self.add_word(word, tag)
            if chk_cb is not None and not ret:
                chk_cb(fname, row, txt, word, old)

        def add_line(txt, row):
            if not txt or txt[0] == '#':
                return
            if vals_cb:
                vals = vals_cb(txt)
                for val in vals:
                    add_word(val[0], val[1], row, txt)
            else:
                name, tag = nt_parser_t._split_label(txt)  # 内置标注解析处理
                if not tag:
                    tag = tags
                add_word(name, tag, row, txt)

        try:
            if isinstance(fname, str):
                row = -1
                with open(fname, 'r', encoding=encode) as fp:
                    for _line in fp:
                        row += 1
                        txt = _line.strip()
                        add_line(txt, row)
            elif isinstance(fname, list):
                for row, txt in enumerate(fname):
                    add_line(txt, row)
            if isend:
                self.matcher.dict_end()
            return ''
        except Exception as e:
            return e

    def add_word(self, word, tags, force=True):
        """给内部匹配器添加词汇"""
        if self.listen_cb_wordadd and self.listen_cb_wordadd(word, tags):
            return None, None  # 如果要求放弃该词,则直接返回
        return self.matcher.dict_add(word, tags, force=force)

    def add_words(self, words, tags, isend=True):
        """添加指定的词汇列表到匹配树中"""
        for word in words:
            self.add_word(word, tags)
        if isend:
            self.matcher.dict_end()

    def load_nt(self, fname=None, encode='utf-16', isend=True, with_NO=True, keys=None, debars=None):
        """装载NT尾缀词典,返回值:''正常,否则为错误信息."""

        # 初始化构建匹配词表
        if len(self.matcher.do_loop(None, '有限公司')) != 4:
            for k in nnd.nt_tails:
                data = nnd.nt_tails[k]
                assert '.' in data and '+' in data and '-' in data, data
                if keys and k not in keys:
                    continue
                tags = data['.']
                if tags & types.tags_NS:
                    continue  # 不装载内置的区域特征词表
                exts = data['+']
                nobs = data['-']
                if len(k) > 1 or (len(k) == 1 and with_NO):
                    if not debars or k not in debars:
                        r, ot = self.add_word(k, tags)
                        if not r and ot is not None:
                            print(f'nt_parser_t.nt_tails: {k} is repeat! {ot}')
                for e in exts:
                    if debars and e in debars:
                        continue
                    r, ot = self.add_word(e, tags)
                    if not r and ot is not None:
                        print(f'nt_parser_t.nt_tails+: {k}/{e} is repeat! {ot}')

        return self.__load(isend, fname, types.tags_NM, encode, chk_cb=self._chk_cb) if fname else ''

    def _chk_cb(self, fname, row, txt, word, tag):
        """默认的检查词典冲突的输出回调事件处理器"""
        fn = fname if isinstance(fname, str) else f'dict@{fname[0]}'
        if tag is None:
            return
        if txt == word:
            print(f'<{fn}|{row + 1:>8},{len(txt):>2}>:{txt} repeat!<{tag}>')
        else:
            print(f'<{fn}|{row + 1:>8},{len(txt):>2}>:{txt} repeat {word}<{tag}>')

    @staticmethod
    def _split_label(line):
        """拆分字典行,得到名称与标注,返回值:(name,lbl)
            name - 为实际名称
            lbl - 标注对应类型:None无标注;''禁止拆分;其他为标注对应self.tag_labels类型
        """
        segs = line.strip().split('!')  # 尝试拆分标注记号
        lbl = segs[1] if len(segs) == 2 else None  # 得到标注字符
        if lbl and lbl not in nt_parser_t.tag_labels:
            print('ERROR:DICT LINE UNKNOWN LABEL CHAR!', line)
            lbl = ''
        name = segs[0]  # 得到原名称
        if lbl:
            lbl = nt_parser_t.tag_labels[lbl]  # 江标注字符转换为对应类型
        return name, lbl

    def load_nsa(self, rfname, encode='utf-16', isend=None):
        """装载内置地名的简称类型校正字典,避免将'公安县'的'公安'当作地名.需要在调用load_ns之前执行."""
        if isinstance(rfname, str):
            with open(rfname, 'r', encoding=encode) as rf:
                for line in rf.readlines():
                    if not line or line[0] == '#':
                        continue
                    aname, typ = nt_parser_t._split_label(line)
                    self.nsa_type_maps[aname] = typ
        elif isinstance(rfname, list):
            for line in rfname:
                aname, typ = nt_parser_t._split_label(line)
                self.nsa_type_maps[aname] = typ
        return ''

    def load_ns(self, fname=None, encode='utf-16', isend=True, worlds=True):
        """装载NS组份词典,worlds告知是否开启全球主要地区.返回值:''正常,否则为错误信息."""
        lvls = {0: types.tags_NS, 1: types.tags_NS1, 2: types.tags_NS2, 3: types.tags_NS3, 4: types.tags_NS4, 5: types.tags_NS5}

        def ns_tags(line):
            """根据地名进行行政级别查询,返回对应的类型标记"""
            if line[-2:] in {'林场', '农场', '牧场', '渔场', '水库', '灌区'}:
                return types.tags_NSNM
            if line[-3:] in {'管理区'}:
                return types.tags_NSNO
            lvl = cai.query_aera_level(line)
            return lvls[lvl]

        # 装入内置的行政区划名称
        if len(self.matcher.do_loop(None, '牡丹江市')) != 4:
            for id in cai.map_id_areas:
                alst = cai.map_id_areas[id]
                lvl = cai.query_aera_level(alst[0])  # 根据正式地名得到行政区划级别

                for name in alst:
                    tags = lvls[lvl]
                    self.add_word(name, ns_tags(name))  # 进行动态类型计算
                    self.add_word('驻' + name, tags)  # 增加驻地名称模式
                    aname = cai.drop_area_tail(name)
                    if name != aname and aname not in nnd.nt_tail_datas:
                        tags = self.nsa_type_maps.get(aname, tags)  # 对内置地名的简称进行类型调整
                        _, old = self.add_word(aname, tags)  # 特定尾缀地区名称,放入简称和初始类型
                        if old:
                            tmp = old.difference(tags).difference({types.NS1, types.NS2, types.NS3, })
                            if tmp and aname not in {'御道口牧场'}:
                                print(f'cai.map_id_areas: {aname}@{name} is repeat! {tmp}')
                        self.add_word('驻' + aname, tags)  # 增加驻地简称模式

                # cnames = cai.make_comb_parent_name(id)
                # for name in cnames:
                #     self.add_word(name, lvls[lvl])  # 装入市区/市县的组合地名

        # 装入内置的区域特征
        if len(self.matcher.do_loop(None, '嘎查村')) != 3:
            for k in nnd.nt_tails:
                data = nnd.nt_tails[k]
                assert '.' in data and '+' in data and '-' in data, data
                tags = data['.']
                if not types.equ(tags, types.tags_NS):
                    continue
                exts = data['+']
                nobs = data['-']
                r, ot = self.add_word(k, tags)
                if not r:
                    print(f'nt_parser_t.nt_tails: {k} is repeat! {ot}')
                for e in exts:
                    r, ot = self.add_word(e, tags)
                    if not r:
                        print(f'nt_parser_t.nt_tails+: {k}/{e} is repeat! {ot}')

        # 装入内置的世界主要国家与首都
        if worlds and len(self.matcher.do_loop(None, '环太平洋')) != 4:
            for state in cai.map_worlds:
                tags = self.nsa_type_maps.get(state, types.tags_NS)  # 对state地名进行类型调整
                r, ot = self.add_word(state, tags)
                if not r:
                    print(f"nlp_ner_nt.load_ns state is repeat: {state} {ot}")

                city = cai.map_worlds[state]
                if city:
                    tags = self.nsa_type_maps.get(city, types.tags_NS1)  # 对city首都地名进行类型调整
                    r, ot = self.add_word(city, tags)
                    if not r:
                        print(f"nlp_ner_nt.load_ns city is repeat: {city} {ot}")

            areas = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚', '东南亚']
            for area in areas:
                r, ot = self.add_word(area, types.tags_NN)
                if not r:
                    print(f"nlp_ner_nt.load_ns area is repeat: {area} {ot}")

        # 地名的构成很复杂.最简单的模式为'名字+省/市/区/县/乡',还有'主干+街道/社区/村/镇/屯',此时的主干组份的模式就很多,如'xx街/xx路/xx站/xx厂'等.

        def nn_tags(aname):
            """获取指定地名主干的类别"""
            if aname[-1] in cai.ns_tails:
                return ns_tags(aname)  # 如果主干部分的尾字符合地名尾缀特征,则按地名标注
            return types.tags_NN  # 非地名特征的全部作为名字类型

        def vals_cb(line):
            name, tag = nt_parser_t._split_label(line)  # 得到原始地名与对应的标注类型
            if tag == '':  # 不要求进行解析处理
                return [(name, ns_tags(name))]
            # 解析得到主干部分
            aname = cai.drop_area_tail(name)
            if name == aname:
                return [(name, ns_tags(name))]
            if aname in nnd.nt_tail_datas:
                fn = fname if isinstance(fname, str) else f'dict@{fname[0]}'
                print(f'<{fn}> {name}@{aname} is repeat in nt_tail_datas.')
                return [(name, ns_tags(name))]

            if len(aname) <= 1:
                fn = fname if isinstance(fname, str) else f'dict@{fname[0]}'
                print(f'<{fn}>:{line} split <{aname}>')
            if tag is None:  # 没有明确标注主干类型时
                if aname[-1] in nt_parser_t.num_re:  # 简化名称尾缀为数字特征时
                    tag = types.tags_NA  # 则简化名称降级为弱化类型
                else:
                    tag = nn_tags(aname)  # 根据主干部分决定类型
            return [(name, ns_tags(name)), (aname, tag)]

        return self.__load(isend, fname, types.tags_NS, encode, vals_cb, self._chk_cb) if fname else ''

    def load_nz(self, fname, encode='utf-16', isend=True):
        """装载NZ组份词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NZ, encode, chk_cb=self._chk_cb)

    def load_nn(self, fname, encode='utf-16', isend=True):
        """装载NN尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NN, encode, chk_cb=self._chk_cb)

    def load_na(self, fname, encode='utf-16', isend=True):
        """装载NA尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NA, encode, chk_cb=self._chk_cb)

    def load_no(self, fname, encode='utf-16', isend=True):
        """装载NO尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NO, encode, chk_cb=self._chk_cb)

    def loads(self, dicts_list, path=None, with_end=True, dbginfo=False, encode='utf-16'):
        """统一装载词典列表dicts_list=[('类型','路径')].返回值:空串正常,否则为错误信息."""
        map = {"NS": self.load_ns, "NT": self.load_nt, "NZ": self.load_nz, "NN": self.load_nn, "NA": self.load_na, "NO": self.load_no, "SA": self.load_nsa}
        bad = []
        for i, d in enumerate(dicts_list):
            fname = d[1] if path is None else os.path.join(path, d[1])
            ftype = d[0]
            if ftype not in map:
                r = f'BAD<{ftype}>@<{fname if isinstance(fname, str) else i}>'
                bad.append(r)
                if dbginfo:
                    print(r)
                continue

            if dbginfo:
                print(f'loaging dicts: <{ftype}>@<{fname if isinstance(fname, str) else i}>')

            r = map[ftype](fname, encode, isend=False)
            if r != '':
                bad.append(f'ERR<{r}>:<{ftype}>@<{fname if isinstance(fname, str) else i}>')
                if dbginfo:
                    print(r)

        if with_end:
            if dbginfo:
                print('building AC Tree ...')
            self.matcher.dict_end()
        return ''.join(bad)

    @staticmethod
    def _merge_bracket(segs, txt):
        """合并segs段落列表中被左右括号包裹的部分,返回值:结果列表"""

        def _merge_range_seg(bi, ei, segs):
            """合并(bi,ei)分段以及其左右的括号,变为一个大分段"""
            segs[bi] = (segs[bi][0] - 1, segs[ei][1] + 1, segs[ei][2])  # 更新bi处的分段信息
            for i in range(ei - bi):  # 丢弃后续分段
                segs.pop(bi + 1)

            # 需要判断后面是否应该补全报社尾缀分段
            posA = segs[bi][1]
            if posA < len(txt) and txt[posA] in {'社', '室'}:
                if bi + 1 < len(segs):
                    pos = segs[bi + 1][0]
                    if txt[pos] in {'社', '室'}:
                        return  # 如果存在后面的分段,且也为单字尾缀,则不用合并本段了
                segs.insert(bi + 1, (posA, posA + 1, types.tags_NO))

        def _calc_range_seg(b, e, segs):
            """查找segs中(b,e)范围内的seg,返回值:(bi,ei,bool)"""
            bi = None
            ei = None
            # 按括号范围查找包裹的分段范围
            for i, seg in enumerate(segs):
                if bi is None and seg[0] == b + 1:
                    bi = i
                if ei is None and seg[1] == e:
                    ei = i
                if seg[1] > e:
                    break

            if bi is None or ei is None:
                return bi, ei, False
            for i in range(bi + 1, ei + 1):
                pseg = segs[i - 1]
                seg = segs[i]
                if pseg[1] < seg[0]:
                    return bi, ei, False  # 前后分段位置相离
            return bi, ei, True

        def _find_last_brk_seg(segs, pos):
            """在segs分段列表中查找pos前面紧邻的分段"""
            for i in range(len(segs) - 1, -1, -1):
                seg = segs[i]
                if seg[1] > pos:
                    continue
                if seg[1] == pos:
                    return seg
                if seg[1] < pos:
                    return None
            return None

        def _skip_head_brk_seg(result):
            """尝试跳过头尾被包裹的NM整体"""
            if not result or result[-1][0] != 0 or txt[0] not in {'"', '(', "'"}:
                return False
            if txt[result[-1][1] - 1] == ')':
                result.pop(-1)
                return True  # 可能是(公司名(尾缀))这样的情况
            lseg = _find_last_brk_seg(segs, result[-1][1])
            if lseg and lseg[2] & {types.NM, types.NB, types.NO}:
                result.pop(-1)
                return True  # 遇到从头到NM尾整体被包裹的情况了
            return False

        # 进行有深度感知的括号配对,得到每个层级的配对位置

        result = []  # 记录完整的配对结果
        stack = uni.find_brackets_list(txt, result)  # 记录当前深度待配对的信息
        if stack:  # 括号配对失败
            return stack  # 返回待配对层级信息list

        _skip_head_brk_seg(result)  # 尝试丢弃整体包裹的"或(

        for res in result:
            bi, ei, ok = _calc_range_seg(res[0], res[1], segs)
            if not ok:
                if bi is None and ei is None:
                    continue  # 规避'<新疆艺术(汉文)>杂志社'里面的'(汉文)'
                return res  # 括号范围内有未知成分,停止处理,返回tuple(b,e)
            _merge_range_seg(bi, ei, segs)  # 合并括号范围
        return None  # 正常完成

    @staticmethod
    def _merge_segs(matcher, segs, merge_types=True, combi=False, comboc_txt=None, max_merge_len=10):
        '''处理segs段落列表中交叉/包含/相同组份合并(merge_types)的情况,返回值:(结果列表,前后段关系列表)'''
        rst = []
        clst = []
        if not segs:
            return rst, clst

        def can_combi_NM(pseg, seg):
            """判断特殊序列是否可以合并"""
            if pseg[2] & {types.NZ, types.NS} and types.equ(seg[2], types.tags_NM):
                if merge_types and mu.slen(pseg) <= 2 and mu.slen(seg) <= 2:
                    return True  # 要求合并,且前后段比较短,可以合并
                if pseg[1] > seg[0] and seg[1] - pseg[0] < 10:
                    return True  # 交叉(NZ,NS)&NM,且前后段比较短,可以合并
            if types.equ(seg[2], types.tags_NO):
                if pseg[1] == seg[0] and mu.slen(seg) == 1:
                    if comboc_txt and comboc_txt[seg[0] - 1] in {'>'}:
                        return False  # "<xx>社"不合并
                    return True  # 紧邻NO,则强制合并前后段
                if pseg[1] > seg[0] and pseg[1] <= seg[1]:
                    if comboc_txt and comboc_txt[pseg[0]] in {'路', '道', '街'} and types.tags_NA & pseg[2]:
                        return False  # NA&NO,且NA首字是道路特征,不合并
                    if pseg[1] - seg[0] >= 2:
                        return True
                    if mu.slen(seg) >= 4 or mu.slen(pseg) >= 5:
                        return False  # 足够长的NO即便与前词交叉,不合并
                    return True  # 交叉NO,则强制合并前后段
            if pseg[1] == seg[0] and types.tags_NU.issubset(pseg[2]) and types.equ(seg[2], types.tags_NB):
                return True  # 紧邻(NU,NM)+NB,则合并前后段
            return False

        def can_tags_merge(pseg, seg, idx):
            """基于当前分段索引idx和分段信息seg,以及前段信息pseg,判断二者是否应该进行类型合并"""
            type_eq = types.equ(pseg[2], seg[2])
            if type_eq:
                if pseg[1] > seg[0]:
                    if seg[1] - pseg[0] <= max_merge_len:
                        return True  # 前后两个段是交叉的同类型分段,合并后仍然很短,或者后段与当前段相邻
                if mu.slen(pseg) == 1 and pseg[1] == seg[0] and pseg[2] & {types.NN, types.NA}:
                    return True  # 类型相同的前后连接段,前段为NN或NA单字
                if pseg[1] == seg[0] and pseg[2] & types.tags_NO:
                    if mu.slen(seg) != 1 or mu.slen(seg) + mu.slen(pseg) > 4:
                        return False  # 前后相邻的OO,后者不是单字,或合并后较长,则不合并

            if comboc_txt and mu.slen(pseg) == 1 and pseg[1] == seg[0] and seg[2] & {types.NN, types.NA} and comboc_txt[pseg[0]] in {'新'}:
                return True  # 前面单字相连的前后段,且类型允许则合并

            if not merge_types:
                return False  # 不要求类型合并

            if pseg[1] == seg[0] and types.equ(pseg[2], seg[2]) and types.tags_NMNB & seg[2]:
                return False  # 前后相邻的NM/NB不要合并

            # 允许分段相交合并的类型集合
            can_cross_typesSZF = {types.NS, types.NZ, types.NF}
            can_cross_typesANH = {types.NA, types.NN, types.NH, types.NU}
            if not type_eq:  # 前后段类型不一致时,需要额外判断
                if pseg[1] > seg[0]:
                    # if mu.slen(seg) + mu.slen(pseg) <= 5 and can_cross_typesSZF & seg[2] and can_cross_typesSZF & pseg[2]:
                    #     return True  # 在要求合并的情况下,两个分段如果在许可的类型范围内且交叉,也合并
                    if comboc_txt and seg[1] - pseg[0] <= 5 and (seg[0] - pseg[0] == 1 or seg[1] - pseg[1] == 1):
                        if (types.tags_NN.issubset(pseg[2]) and types.tags_NZ.issubset(seg[2])) or (types.tags_NA.issubset(pseg[2]) and types.tags_NN.issubset(seg[2])):
                            # NN&NZ相交,且切分后剩余单字
                            if idx >= 2 and mu.slen(segs[idx - 1]) == 1:
                                return False  # 再前面仍然是单字,则这里不合并
                            nums = re.findall(nt_parser_t.num_re, comboc_txt[pseg[0]])
                            if not nums:
                                return True  # NN&NZ相交,且切分后剩余非数字单字,则进行合并
                            else:
                                return False
                        if pseg[2] & can_cross_typesANH and seg[2] & can_cross_typesANH:
                            return True
                return False  # 否则不合并

            if idx + 1 < len(segs):  # 当前段不是末尾,则向后看一下,进行额外判断
                nseg = segs[idx + 1]
                if types.equ(seg[2], nseg[2]):
                    if nseg[0] == seg[1]:
                        return True  # 后段与当前段类型相同且相邻,当前段可合并
                    else:
                        return False
                if can_combi_NM(seg, nseg):
                    return False  # 后段与当前段类型不同且可组合,则告知当前段不可合并

            return True

        def rec_tags_merge(pseg, seg):
            """记录前后两个段落的合并结果"""
            ac = types.cmp(pseg[2], seg[2])
            if ac > 0:  # 如果前段级别大于后段,使用后段级别
                att = seg[2]
            else:
                att = pseg[2]  # 否则使用前段级别
            rst[-1] = (pseg[0], seg[1], att)  # 记录合并后的新段

        def rec_tags_cross(pseg, seg):
            """记录前后两个段落的相交结果"""
            assert pseg == rst[-1]
            chars_NONS = {'矿', '店', '局'}  # 需要进行NO/NS转换的单字

            def adj_typ_NO(b, e, typ_nhit):
                """根据给定的分段范围与默认类型,进行特定分段类型的校正"""
                if not comboc_txt:
                    return typ_nhit
                w = comboc_txt[b:e]
                if w in chars_NONS:
                    return types.tags_NO
                else:
                    if not matcher:
                        return nnd.nt_tail_datas.get(w, typ_nhit)
                    else:
                        if len(w) == 1 and comboc_txt[b - 1:e] in {'县城'}:
                            return types.tags_NS
                        mres = matcher.do_check(w, mode=mac.mode_t.max_match)
                        if not mres or mu.slen(mres[-1]) != len(w):
                            return typ_nhit
                        return mres[-1][2]

            def can_combi_NS(p, c):
                """判断前段p与当前段c是否可以合并成为NS."""
                if not comboc_txt or p[1] != c[0] or p[2] is None or c[2] is None:
                    return False  # 不要求合并,或者前后段不相邻,不合并

                pt = comboc_txt[p[0]:p[1]]
                ct = comboc_txt[c[0]:c[1]]

                if pt[-1] == ct[0]:
                    return False  # 前后紧邻的叠字,不合并

                if pt[-1] in {'市'} and ct in {'区'}:
                    return True
                if pt[-1] in {'村'} and ct in {'组'}:
                    return True

                if ct in {'路', '街', '道', '巷', '站', '里', '弄', '东路', '西路', '南路', '北路', '中路', '东街', '南街', '西街', '北街', '中街', '大街'}:
                    if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县'}:
                        return False  # 较长地名后面出现道路特征,不合并
                    if p[2] & {types.NS, types.NN, types.NA, types.NZ, types.NH}:
                        return True  # 常规词性后出现道路特征,可合并

                if ct in {'区', '县', '乡', '镇', '村', '屯', '居', '办', '组', '港', '港区', '湾区', '地区', '苏木', '小区', '街道', '社区', '行政村', '自然村'}:
                    if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县', '乡', '镇', '村', }:
                        return False  # 较长地名后面出现村镇特征,不合并
                    if p[2] & {types.NS, types.NN, types.NA, types.NZ, types.NU}:
                        return True  # 常规词性后出现村镇特征,可合并

                if ct in {'东', '西', '南', '北', }:
                    if p[2] & {types.NS, types.NM} or (len(pt) >= 3 and pt[-1] in {'市', '区', '县', '乡', '镇', '村'}):
                        return True  # 较长地名后面出现方向特征,合并
                    if p[2] & {types.NN, types.NA, types.NZ}:
                        return False  # 常规词性后出现方位特征,不合并

                if ct in {'前', '后', '旁', '外', '内', '门前'}:
                    if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县', '乡', '镇', '村', }:
                        return False  # 较长地名后面出现方位特征,不合并
                    if p[2] & {types.NS, types.NM, types.NO}:
                        return True  # 组织词性后出现方位特征,合并

                return False  # 默认不允许合并

            if types.NX not in seg[2]:
                if combi and can_combi_NM(pseg, seg):
                    rst[-1] = (pseg[0], seg[1], seg[2])  # 后段吞并前段
                    return
                elif can_combi_NS(pseg, seg):
                    rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 后段吞并前段
                    return
                elif pseg[1] > seg[0]:
                    needadj = True
                    if types.tags_NU.issubset(pseg[2]) and types.tags_NB.issubset(seg[2]):
                        rst[-1] = (pseg[0], seg[1], seg[2])  # NU|NB => NB
                        return
                    if types.tags_NS.issubset(pseg[2]) and types.tags_NU.issubset(seg[2]):
                        seg = (pseg[1], seg[1], seg[2])  # NS&NU则切除NU相交部分
                        needadj = False

                    if comboc_txt and pseg[1] - seg[0] == 1:
                        if types.tags_NN.issubset(pseg[2]) and types.tags_NS.issubset(seg[2]) and comboc_txt[pseg[0]] not in {'和', '驻'}:
                            rst[-1] = (pseg[0], seg[1], seg[2])  # NN&NS,后段吞并前段
                            return
                        if types.tags_NU.issubset(pseg[2]) and types.tags_NA.issubset(seg[2]):
                            typ = adj_typ_NO(pseg[1], seg[1], pseg[2])
                            rst[-1] = (pseg[0], seg[1], typ)  # NU&NA,后段吞并前段
                            return
                        if types.tags_NU.issubset(seg[2]):
                            seg = (pseg[1], seg[1], seg[2])  # &NU则切除相交部分
                            needadj = False

                    if needadj:
                        if types.cmp(pseg[2], seg[2]) < 0 or (pseg[2] & {types.NN, types.NH, types.NO, types.NU} and mu.slen(seg) > 2 and seg[2] & {types.NO}):
                            if pseg[1] - seg[0] >= 2 and seg[0] - pseg[0] == 1 and seg[1] - pseg[1] > 1 and {types.NM, types.NB}.isdisjoint(seg[2]):
                                seg = (pseg[1], seg[1], seg[2])  # 前后相交大于两个字且前段切分后剩余单字,则调整后段
                            else:
                                typ = adj_typ_NO(pseg[0], seg[0], pseg[2])
                                rst[-1] = (pseg[0], seg[0], typ)  # 后段重要,调整前段范围
                        else:
                            if pseg[1] - seg[0] >= 2 and seg[1] - pseg[1] == 1 and seg[0] - pseg[0] > 1 and {types.NM, types.NB}.isdisjoint(pseg[2]):
                                rst[-1] = (pseg[0], seg[0], pseg[2])  # 前后相交大于两个字且后段切分后剩余单字,则调整前段
                            else:
                                typ = adj_typ_NO(pseg[1], seg[1], seg[2])
                                seg = (pseg[1], seg[1], typ)  # 前段重要,调整后段范围

            # 在第三段到来的时候,进行前两段的强制合并处理.
            if comboc_txt and len(rst) >= 2 and rst[-2][1] == rst[-1][0]:
                p2seg = rst[-2]
                p1seg = rst[-1]
                if mu.slen(p2seg) > 1 and can_combi_NS(p2seg, p1seg):  # 在前一轮北切分剩余单字后,再次尝试 合并'|南京|路|'
                    rst[-2] = (p2seg[0], p1seg[1], types.tags_NS)  # 转换分段类型为NS
                    rst.pop(-1)
                elif mu.slen(p2seg) == 1:
                    if mu.slen(p1seg) == 1:  # 合并双单字
                        b, e = p2seg[0], p1seg[1]
                        nums = nt_parser_t.chk_nums(comboc_txt[b:e])  # 先进行合并词汇的序号分段检验
                        if nums and mu.slen(nums[-1]) == (e - b):
                            rst[-2] = (b, e, nums[-1][2])  # 确实是序号分段
                        else:
                            rst[-2] = (b, e, types.tags_NA)  # 否则就合并降级为NA分段
                        rst.pop(-1)
                    elif mu.slen(seg) == 1 and p1seg[1] == seg[0] and types.tags_NMNB.isdisjoint(p1seg[2]):  # 合并'|桥|西城|瑞|'
                        rst[-2] = (p2seg[0], seg[1], p1seg[2])  # 保留中间段的类型
                        rst.pop(-1)
                        return  # 不再重复记录当前分段
                    elif {types.NN, types.NS, types.NZ} & p2seg[2] and {types.NM, types.NB, types.NO} & p1seg[2] and mu.slen(p1seg) < 3:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # NN&NM,后段吞并前段
                        rst.pop(-1)
                    elif comboc_txt[p2seg[0]] in {'新', '老', '小', '省', '市', '州', '中', '盟'} and {types.NM, types.NB, types.NO} & p1seg[2]:
                        if {types.NM, types.NB, types.NO} & seg[2]:
                            rst[-2] = (p2seg[0], p1seg[1], p2seg[2])  # NN&NM,后段吞并前段
                            rst.pop(-1)
                        else:
                            rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # NN&NM,后段吞并前段
                            rst.pop(-1)
                    elif types.tags_NA.issubset(p2seg[2]) and {types.NB, types.NO} & p1seg[2] and mu.slen(p1seg) <= 2:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # NA&NB,后段吞并前段
                        rst.pop(-1)
                    elif mu.slen(p1seg) % 2 == 1 and p2seg[2] & {types.NN, } and p1seg[2] & {types.NZ}:
                        rst[-2] = (p2seg[0], p1seg[1], p2seg[2])  # 合并: NN单字+NZ奇数
                        rst.pop(-1)
                elif mu.slen(p1seg) == 1 and p1seg[1] == seg[0]:
                    if comboc_txt[p1seg[0]] not in {'和', '驻', '至'} and types.tags_NS.issubset(seg[2]):
                        rst[-1] = (p1seg[0], seg[1], seg[2])  # OC+NS合并为NS
                        return  # 不再重复记录当前分段
                    city_tails = {'县城', '省直', '市直', '州直', '市立', '市中', '县立', '区立', '村级', '村庄', '区直', '镇直', '局直', '城中', '镇关', '镇中', '乡野', '村民', '市属'}
                    if (p2seg[2] & p1seg[2]) and p1seg[2] & {types.NN, types.NZ, types.NS}:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # 合并相同类型的前后段
                        rst.pop(-1)
                    elif types.NO in p1seg[2] and p2seg[2] & {types.NN, types.NZ, types.NS} and comboc_txt[p1seg[0] - 1] != '>':
                        if comboc_txt[p1seg[0]] in chars_NONS and seg[2] & {types.NM, types.NB, types.NO}:
                            typ = types.tags_NS
                        else:
                            typ = types.tags_NO
                        rst[-2] = (p2seg[0], p1seg[1], typ)  # 合并NS+NO
                        rst.pop(-1)
                    elif types.NB in p1seg[2] and p2seg[2] & {types.NN, types.NZ, types.NS}:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # 合并NS+NB
                        rst.pop(-1)
                    elif comboc_txt[p2seg[1] - 1:p1seg[1]] in city_tails and {types.NS, types.NM} & p2seg[2]:
                        rst[-2] = (p2seg[0], p1seg[1], types.tags_NS)  # 转换分段类型为NS
                        rst.pop(-1)
                    elif comboc_txt[p2seg[1] - 1:p1seg[1]] in {'市政', } and {types.NS, types.NM} & p2seg[2]:
                        rst[-2] = (p2seg[0], p2seg[1] - 1, p2seg[2])  # 调整前段的范围 '|锦州市|政|第二|'
                        rst[-1] = (p2seg[1] - 1, p1seg[1], p1seg[2])  # 调整后段的范围 '|锦州|市政|第二|'

            if types.NX not in seg[2]:
                rst.append(seg)  # 记录后段信息

        def rec_tags_cont(pseg, seg):
            """记录seg包含pseg的结果"""
            if types.cmp(pseg[2], seg[2]) < 0:
                rst[-1] = (pseg[0], seg[1], seg[2])  # 后段重要,替换前段范围
            else:
                rst[-1] = (pseg[0], seg[1], pseg[2])  # 前段重要,调整前段范围

        rst.append(segs[0])
        for idx in range(1, len(segs)):
            pseg = rst[-1]
            seg = segs[idx]
            rl, cr = mu.related_segs(pseg, seg)
            clst.append((pseg, rl, seg, cr))  # 记录关联情况

            # 根据前后段的关系进行合并处理
            if rl == 'A&B':  # 前后相交,判断是否可以合并
                if can_tags_merge(pseg, seg, idx):
                    rec_tags_merge(pseg, seg)  # 合并当前段
                else:
                    rec_tags_cross(pseg, seg)  # 记录,前后交叉
            elif rl == 'A+B':  # 前后紧邻,需要判断是否应该合并
                if {types.NB, types.NO, types.NM}.isdisjoint(pseg[2]) and types.equ(seg[2], types.tags_NL):
                    seg = segs[idx] = (seg[0], seg[1], types.tags_NLNM)  # 孤立出现的尾缀NL要当作NM,如:深圳市投控东海一期基金(有限合伙)
                    # rst.append(seg)
                    rec_tags_cross(pseg, seg)
                elif can_tags_merge(pseg, seg, idx):
                    rec_tags_merge(pseg, seg)  # 合并当前段
                else:
                    rec_tags_cross(pseg, seg)  # 记录,前后紧邻
            elif rl == 'A@B':  # 前段包含后段,需要记录NA@NO的情况
                if (types.equ(pseg[2], types.tags_NA) and types.equ(seg[2], types.tags_NO) and can_combi_NM(pseg, seg)):
                    rec_tags_cross(pseg, seg)  # 记录,前包含后
            elif rl == 'B@A':  # 后段包含前段
                if can_tags_merge(pseg, seg, idx):
                    rec_tags_merge(pseg, seg)  # 合并当前段
                else:
                    rec_tags_cont(pseg, seg)  # 记录,后包含前
            else:
                rst.append(seg)  # 其他情况,直接记录当前分段

        lseg = rst[-1]
        rec_tags_cross(lseg, (lseg[1], lseg[1], {types.NX}))  # 使用最后的模拟空段驱动前面的分段合并
        return rst, clst

    @staticmethod
    def _merge_nums(segs, nusegs):
        """将nusegs中的分段信息合并到segs中"""
        if not nusegs:
            return

        def rec(segs, oseg, pos, nseg):
            """oseg是原pos处的分段,nseg是pos处的新分段"""
            if oseg:
                if oseg[0] == nseg[0] and nseg[1] == oseg[1]:
                    if oseg[2] & {types.NA, types.NU} and nseg[2] & {types.NS, types.NO, types.NB}:
                        segs[pos if pos < len(segs) else pos - 1] = nseg  # 相同位置出现新的有效识别分段,直接替换
                    return
                if oseg[0] <= nseg[0] and nseg[1] <= oseg[1] and nseg[2] & oseg[2] & {types.NU}:
                    return  # 当前数字分段处于目标分段的内部或重叠,放弃
                if pos + 1 < len(segs):
                    fseg = segs[pos + 1]
                    if oseg[1] == fseg[0] and oseg[0] <= nseg[0] and nseg[1] <= fseg[1] and oseg[2] & {types.NU}:
                        return  # 当前数字分段处于前后紧邻的两个分段内部,放弃
            # if pos:
            #     pseg = segs[pos - 1]
            #     if pseg[0] == nseg[0] and nseg[1] == pseg[1]:
            #         return
            #     if pseg[0] < nseg[0] and nseg[1] <= pseg[1] and nseg[2] & oseg[2] & {types.NU}:
            #         return  # 当前数字分段与前一个分段重叠,放弃

            if pos + 1 < len(segs):
                fseg = segs[pos + 1]
                if fseg[0] <= nseg[0] and nseg[1] <= fseg[1]:
                    return  # 当前数字分段与后一个分段重叠,放弃

            if pos and segs and mu.slen(nseg) == 1 and oseg[1] == nseg[0] and types.tags_NB.issubset(nseg[2]):
                segs[pos - 1] = (segs[pos - 1][0], nseg[1], nseg[2])  # 单字NB则直接与前面合并
            else:
                if pos == 0 and segs:
                    pseg = segs[0]
                    if pseg[0] < nseg[0] and nseg[1] <= pseg[1]:
                        pos += 1
                segs.insert(pos, nseg)

        for nseg in nusegs:  # 对数字分段进行逐一处理
            pos = 0
            pseg = None if not segs else segs[pos]
            if pseg and nseg[1] <= pseg[1]:
                rec(segs, pseg, pos, nseg)
                continue  # 数字段处于当前段的前面了,直接不找了
            if pseg and nseg[0] >= segs[-1][1]:
                pseg = segs[-1]
                pos = len(segs)
                rec(segs, pseg, pos, nseg)
                continue  # 数字段处于最后面,直接不找了

            for i in range(pos, len(segs)):  # 对已有分段segs进行倒序查找对比
                pseg = segs[i]
                if pseg[1] >= nseg[0]:
                    pos = i  # 遇到第一个可能的插入位置了,还需要向后试探
                    if pseg[0] < nseg[0]:
                        pos += 1  # 数字段完全超越当前段,后延一下
                    break

            for i in range(pos, len(segs)):  # 从当前分段位置继续向后试探
                pseg = segs[i]
                if pseg[0] == nseg[0] and pseg[1] == nseg[1]:
                    break
                if pseg[1] > nseg[0]:
                    pos = i  # 在当前段之后插入
                    if pseg[0] > nseg[0] or pseg[1] > nseg[1]:
                        break

            if pos == len(segs) - 1 and pseg and pseg[0] <= nseg[0]:
                pos += 1  # 末尾处额外后移判断

            rec(segs, pseg, pos, nseg)

    def split(self, txt, nulst=None, with_useg=False, mres=None, pres=None, fp_dbg=False):
        '''在txt中拆分可能的组份段落
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            mres - 记录参与匹配的原始词汇列表
            pres - 记录匹配完成后并清理过的词汇列表
            返回值:分段列表[(b,e,{types})]
        '''

        def find_right(segs, seg, offset):
            """从segs的offset开始向右探察,判断是否存在seg的粘连分段"""
            c = 0
            for idx in range(offset, len(segs)):
                nseg = segs[idx]
                c += 1
                if nseg[0] > seg[1] and c > 2:
                    return False
                if seg[0] < nseg[0] <= seg[1]:
                    return True
            return False

        def find_left(segs, seg, offset):
            """从segs的offset开始向左探察,判断是否存在seg的粘连分段"""
            if offset < 0:
                return False
            for idx in range(offset, -1, -1):
                pseg = segs[idx]
                if pseg[1] < seg[0]:
                    return False
                if seg[0] <= pseg[1] < seg[1]:
                    return True
            return False

        def clean_drop(segs):
            """匹配后再分析并删除分段列表segs中被包含且无接续的无效分段"""

            def adj_NANO(C, idx):
                D = segs[idx + 1] if idx + 1 < len(segs) else None  # 后一个分段

                st = txt[C[0]:C[1]]
                if st[-2:] in {'县城', '东部', '南部', '西部', '北部', '中部'}:
                    return 0
                sd = nnd.query_tail_data(st[-1])
                if sd and types.tags_NO.issubset(sd['.']):  # 当前NA分段尾字是NO,直接校正
                    if len(st) == 2 and st[-1] in {'城', '店'} and D:
                        return 1  # 不在末尾的双字的弱类型,不强制改变类型
                    segs[idx] = (C[0], C[1], types.tags_NO)

                return 1

            rc = 0
            pos = 0
            while pos < len(segs) - 1:
                seg = segs[pos]
                nseg = segs[pos + 1]

                # 尝试对NA词性分段进行尾缀NO校验调整
                if pos and not seg[2] & {types.NA} and mu.slen(nseg) >= 3 and nseg[2] & types.tags_NA:
                    adj_NANO(nseg, pos + 1)

                if nseg[0] == seg[0]:
                    # seg被nseg左贴包含,判断右侧是否有粘连
                    if seg[1] < nseg[1] and not find_right(segs, seg, pos + 2):
                        segs.pop(pos)
                        rc += 1
                        continue
                    if nseg[1] < seg[1] and not find_right(segs, nseg, pos + 2):
                        segs.pop(pos + 1)
                        rc += 1
                        continue

                if seg[1] == nseg[1]:
                    # seg被nseg右贴包含,判断左侧是否有粘连
                    if nseg[0] < seg[0]:
                        if (pos and not find_left(segs, seg, pos - 1)) or not pos:
                            segs.pop(pos)
                            rc += 1
                            continue
                    # nseg被seg右贴包含,判断左侧是否有粘连
                    if seg[0] < nseg[0]:
                        if pos and not find_left(segs, nseg, pos - 1) or not pos:
                            if not (mu.slen(seg) == 2 and seg[2] & types.tags_NA and mu.slen(nseg) == 1 and txt[nseg[0]] in {'店', '矿'}):
                                segs.pop(pos + 1)
                                rc += 1
                                continue

                if pos:
                    pseg = segs[pos - 1]
                    if pseg[1] == nseg[0] and pseg[0] < seg[0] and seg[1] < nseg[1]:  # seg被前后夹击覆盖
                        if not find_left(segs, seg, pos - 2) and not find_right(segs, seg, pos + 2):
                            segs.pop(pos)
                            rc += 1
                            continue

                pos += 1

            return rc

        def rec_ex(rst, pos, node, root):
            """保留分段匹配结果"""

            def can_drop(seg):

                if len(rst):
                    pseg = rst[-1]
                    plen = mu.slen(pseg)
                    slen = mu.slen(seg)
                    if seg[0] < pseg[0]:  # 新段起点早于旧段
                        if plen == 1 or not find_left(rst, pseg, len(rst) - 2):  # 且旧段无左侧粘连
                            return True
                        if pseg[0] - seg[0] >= 2:
                            return True
                    if pseg[0] == seg[0]:  # 前后段起点相同
                        if slen - plen >= 2 and seg[2] & {types.NM, types.NO, types.NB}:
                            return True  # 发电|发电机厂,丢弃前段
                        if plen == 1 < slen and seg[2] & {types.NS}:
                            return True  # 北|北京,丢弃前段
                    if seg[0] <= pseg[0] and pseg[1] < seg[1]:
                        if slen >= 6 and plen <= 4:
                            return True  # 长段包含短段,丢弃短段

                if len(rst) >= 2:
                    fseg = rst[-2]
                    pseg = rst[-1]

                    if mu.slen(pseg) == 1:
                        if fseg[0] < pseg[0] and fseg[1] == pseg[1]:
                            if not find_left(rst, pseg, len(rst) - 2):
                                return True  # 右贴被包含的单字,左侧无粘连则丢弃
                    if fseg[0] < pseg[0] and pseg[0] < fseg[1] < pseg[1] and fseg[2] & types.tags_NS and pseg[2] & types.tags_NS:
                        if len(rst) >= 3:  # NS禁止交叉
                            if find_left(rst, pseg, len(rst) - 3):
                                return False  # 除非前面存在接续分段
                        return True

                    if fseg[0] == pseg[0] == seg[0] and fseg[1] < pseg[1] < seg[1] and mu.slen(fseg) == 1:
                        rst.pop(-2)  # 东|东莞|东莞市,删除'东'
                        return False

                    if mu.slen(seg) >= 3:
                        if fseg[0] < pseg[0] < seg[0] and pseg[1] > seg[0] and fseg[1] == seg[0] and mu.slen(fseg) > 1:
                            if seg[2] & {types.NM, types.NS, types.NF} and not find_left(rst, pseg, len(rst) - 2):
                                return True  # 以当前长段为基准,丢弃前面的交叉分段pseg
                        if fseg[0] == seg[0] and fseg[0] < pseg[0] < seg[1] and fseg[1] <= pseg[1] < seg[1]:
                            return True  # 中华|华人|中华人民共和国,丢弃中间分段
                        if fseg[1] - seg[0] >= 2 and fseg[1] - pseg[0] == 1 and pseg[1] < seg[1]:
                            return True  # 中小企业|业服|企业服务,丢弃中间分段

                    if mu.slen(fseg) >= 3 and fseg[2] & {types.NM, types.NZ, types.NF}:
                        if fseg[0] < pseg[0] < fseg[1] and pseg[1] > fseg[1] and seg[0] == fseg[1] and not find_left(rst, pseg, len(rst) - 2):
                            return True  # 以之前的长段为基准,丢弃后面的交叉分段pseg

                return False

            def can_rec(seg):
                city_tails = {'省', '市', '区', '县', '村', '镇', '乡', '州', '旗', '街', '路', '道'}
                if len(rst) >= 3:
                    f3 = rst[-3]
                    f2 = rst[-2]
                    f1 = rst[-1]

                    if mu.slen(seg) == 1:
                        if f3[1] == seg[0] and f3[0] == f2[0] and seg[1] == f2[1] == f1[1] and not find_left(rst, seg, len(rst) - 4):
                            return False  # Z:小吃|O:小吃店|O:吃店|O:店 不记录最后的单字

                        if f3[1] == f2[1] == f1[1] == seg[1] and not find_left(rst, seg, len(rst) - 4):
                            return False  # O:发电机厂|O:电机厂|O:机厂|O:厂 不记录最后的单字

                if len(rst) >= 2:
                    fseg = rst[-2]
                    pseg = rst[-1]
                    flen = mu.slen(fseg)
                    plen = mu.slen(pseg)
                    slen = mu.slen(seg)
                    if slen == 1:
                        if flen == 1 and seg[0] == fseg[1] and pseg[0] == fseg[0] and pseg[1] == seg[1] and fseg[2] & seg[2] & types.tags_NA:
                            rst.pop(-2)  # 西|西北|北 : 丢弃首段不记录尾段
                            return False
                        if fseg[1] == pseg[1] == seg[1] and not find_left(rst, seg, len(rst) - 3):
                            return False  # O:电子厂|B:子厂|O:厂,不记录最后的单字

                    if plen >= 3 and flen > 1:
                        if fseg[0] == pseg[0] and fseg[1] < pseg[1] and seg[1] == pseg[1]:
                            if seg[2] & {types.NO, types.NM, types.NB}:
                                return True  # 江门|江门市|门市,先记录后段
                            if fseg[1] == seg[0] and not find_left(rst, seg, len(rst) - 3):
                                return False  # 资产|资产管理|管理 : 丢弃首段不记录尾段
                            if pseg[2] & {types.NS} and not find_left(rst, seg, len(rst) - 3):
                                return False  # NS禁止交叉:天津|天津市|津市,不记录最后分段

                if len(rst):
                    pseg = rst[-1]
                    if mu.slen(pseg) >= 3:
                        if seg[1] == pseg[1] and seg[0] > pseg[0] and pseg[2] & {types.NO, types.NM, types.NB} and seg[2] & types.tags_NA:
                            return False  # 被NO/NM/NB右包含的NA不记录
                        if seg[1] == pseg[1] and mu.slen(seg) == 1 and pseg[2] & types.tags_NS and seg[2] & types.tags_NA and txt[seg[0]] in city_tails:
                            return False  # 上海|上海市|市,不记录最后的单字
                    if mu.slen(seg) == 1 and seg[1] == pseg[1] and pseg[2] & {types.NM, types.NO, types.NB} and txt[seg[0]] in {'市'}:
                        return False  # 不记录 '超市/门市' 末尾的单字
                return True

            def rec(node):
                """记录当前节点对应的匹配分段到结果列表"""
                if node is root:
                    return
                # 当前待记录的新匹配分段
                seg = pos - node.words, pos, node.end
                if mres is not None:
                    mres.append(seg)
                while rst and can_drop(seg):
                    rst.pop(-1)  # 回溯,逐一踢掉旧结果
                if can_rec(seg):
                    rst.append(seg)

            vnodes = node.get_fails()
            for node in reversed(vnodes):
                rec(node.first)

        segs = self.matcher.do_check(txt, mode=rec_ex)  # 按词典进行完全匹配
        clean_drop(segs)  # 进行无效匹配结果的丢弃
        if pres is not None and isinstance(pres, list):
            pres.extend(segs)  # 记录预处理后的结果
        self.rec_nums(segs, txt, nulst, False)  # 进行未知分段的数字序号补全
        nres = find_nt_paths(txt, segs, fp_dbg)  # 根据匹配结果查找最佳nt路径
        clean_drop(nres)  # 进行NO校正
        self._merge_bracket(nres, txt)  # 合并附加括号

        if with_useg:
            return mu.complete_segs(nres, len(txt), True)[0]
        else:
            return nres

    def parse(self, txt, merge=True, nulst=None, with_useg=False, comboc=True, mres=None, pres=None, fp_dbg=False):
        '''在txt中解析可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            comboc - 是否合并已知的单字
            mres - 记录匹配过程中的原始词汇列表
            pres - 记录匹配完成后并清理过的词汇列表
            返回值:(分段列表[(b,e,{types})],分段关系列表[(pseg,rl,nseg,cr)])
        '''
        segs = self.split(txt, nulst, mres=mres, pres=pres, fp_dbg=fp_dbg)  # 先拆分得到可能的列表
        rlst, clst = nt_parser_t._merge_segs(self.matcher, segs, merge, True, txt if comboc else None)  # 进行完整合并
        if with_useg:
            rlst = mu.complete_segs(rlst, len(txt), True)[0]  # 补全中间的空洞分段

        if merge:
            i = 1
            while i < len(rlst):  # 合并相邻的 NN/NH/NA
                pseg = rlst[i - 1]
                seg = rlst[i]
                if mu.slen(seg) == 1 or mu.slen(pseg) == 1 or not seg[2] or not pseg[2]:
                    i += 1
                    continue  # 进行合法性检查
                # if not seg[2] or not pseg[2]:
                #     i += 1
                #     continue  # 进行合法性检查

                # 进行分段类型修正,NH/NA变为NN
                if pseg[2] & {types.NA, types.NH}:
                    pseg = rlst[i - 1] = (pseg[0], pseg[1], types.tags_NN)
                if seg[2] & {types.NA, types.NH}:
                    seg = rlst[i] = (seg[0], seg[1], types.tags_NN)

                if not seg[2] & types.tags_NN or not pseg[2] & types.tags_NN:
                    i += 1
                    continue  # 进行前后一致性检查

                rlst[i - 1] = (pseg[0], seg[1], types.tags_NN)
                rlst.pop(i)  # 向前合并,丢弃当前段

        return rlst, clst

    def verify(self, name, segs=None, merge_types=False, rec_NL=False, comboc=True, mres=None, pres=None, strict=False, fp_dbg=False):
        """对给定的name机构名称进行拆分并校验有效性(要求尾缀必须为有效机构特征),如附属机构/分支机构/工会.
            segs - 可记录组份分段数据的列表.
            merge_types - 是否合并相同类型分段
            rec_NL - 是否独立记录后缀分段
            comboc - 是否合并连续已知单字
            mres - 记录参与匹配的原始词汇列表(未处理过的)
            strict - 是否未严格模式,遇到未知分段则不记录
            返回值:分段列表[(bpos,epos,types)]
                  返回的types只有NM与NB两种组份模式
        """
        cons, _ = self.parse(name, merge_types, comboc=comboc, mres=mres, pres=pres, fp_dbg=fp_dbg)
        segs, _ = mu.complete_segs(cons, len(name), True, segs)

        outs = []
        bpos = 0

        def chk_bads(i, seg):
            """检查当前段尾缀是否为坏词.返回值:尾部匹配了坏词"""
            end = len(segs) - 1
            txt = name[seg[0]:seg[1]]
            begin, deep, node = self._bads.query(txt, True)
            if i == end:
                # 最后一段,直接判定
                return deep > 0 and not node
            else:
                # 非最后段,先直接判定
                if deep > 0 and not node:
                    return True
                # 再扩展判定
                txt = name[seg[0]:seg[1] + 3]
                begin, deep, node = self._bads.query(txt, False)
                if begin is None or seg[0] + begin >= seg[1]:
                    return False
                return deep > 0 and not node

        def is_brackets(seg):
            """判断当前seg分段是否为NT嵌入在括号中."""
            return name[seg[0]] == '(' and name[seg[1] - 1] == ')'

        def chk_errs(i, seg):
            """检查当前段是否为错误切分.如'师范学院路'->师范学院/学院路->师范/学院路,此时的'师范'仍是NM,但明显是错误的."""
            if mu.slen(seg) >= 2 and {types.NU, types.NL}.isdisjoint(seg[2]) and types.equ(seg[2], types.tags_NM):
                if is_brackets(seg):
                    txt = name[seg[0] + 1:seg[1] - 1]
                else:
                    p = segs[i - 1][0] if i > 0 else 0
                    txt = name[p:seg[1]]
                mres = self.matcher.do_check(txt)  # 按词典进行全部匹配
                for mr in mres:
                    if mr[1] == len(txt) and types.equ(mr[2], types.tags_NM):
                        return False
                return True  # 外面给出的NM经过检查后发现并不是NM,切分错误,不分段
            return False

        def rec(i, seg, bpos, epos, stype):
            if chk_bads(i, seg):
                return

            if chk_errs(i, seg):
                return

            if epos - bpos < 3:  # 太短的实体名称不记录.
                return

            if is_brackets(seg) and types.tags_NL.isdisjoint(seg[2]) and types.equ(seg[2], types.tags_NM) and outs:
                newr = (seg[0], seg[1], stype)  # 被括号嵌入的NT,且之前存在了已有NT段
            else:
                newr = (bpos, epos, stype)  # 正常的NT分段接续

            if outs and seg[2] & {types.NO, types.NM}:
                oldr = outs[-1]  # 处理特殊情况:火车站/火车站店,保留'火车站店',剔除'火车站'
                if oldr[0] == newr[0] and oldr[1] == newr[1] - 1:
                    outs.pop(-1)  # 后一段结果比前一段结果多一个字,则丢弃前段结果
            outs.append(newr)

        for i, seg in enumerate(segs):
            stype = seg[2]
            epos = seg[1]
            if mu.slen(seg) == 0:
                print(name, segs)
            islast = i == len(segs) - 1
            if stype is None:
                if strict and name[seg[0]] not in {'(', ')'}:
                    break
                continue
            if stype & types.tags_NLNM:  # NT/NL/NTNL
                rec(i, seg, bpos, epos, types.NM)
                if rec_NL and types.tags_NL.issubset(stype):  # 在校验输出列表中,是否额外记录尾缀分段信息
                    outs.append((seg[0], seg[1], types.NL))
            elif types.equ(stype, types.NB):
                rec(i, seg, bpos, epos, types.NB)  # 当前段是分支NT结尾
            elif types.equ(stype, types.NO) and (islast or (is_brackets(segs[i + 1]) and segs[i + 1][2] & types.tags_NLNM)):
                # 当前段是单字NO结尾,需要判断特例
                pseg = segs[i - 1]
                if mu.slen(seg) == 1 and pseg[2] and pseg[2] & {types.NM, types.NO, types.NA}:
                    if name[pseg[1] - 1] != name[seg[0]] or name[seg[0]] in {'店', '站'}:
                        rec(i, seg, bpos, epos, types.NM)  # `NM|NO` 不可以为'图书馆馆'/'经销处处',可以是'马店店'/'哈站站',可以作为NT机构
                elif mu.slen(seg) > 1 or pseg[2] is not None:
                    rec(i, seg, bpos, epos, types.NM)
        return outs

    def ends(self, txt, merge=True, strict=True):
        '''查找txt中出现过的尾缀,merge告知是否合并同类分段,strict指示是否严格尾部对齐.返回值:[(b,e,{types})]或[]'''
        mres = self.parse(txt, merge)[0]
        if strict:
            while mres and mres[0][1] != len(txt):
                mres.pop(0)
        return mres

    def match(self, txt):
        '''判断给定的txt是否为完全匹配的已知组份.返回值:(b,e,{types})或None'''
        mres = self.parse(txt)[0]
        if not mres or mu.slen(mres[0]) != len(txt):
            return None
        return mres[0]

    def pizza(self, txt, nulst=None, rsts=None, crwords={'村'}):
        """判断txt是否由已知组份完整拼装得到(分段无交叉且无缺口),
            nulst可给出外部数字模式匹配列表
            rsts可记录匹配的分段结果列表,无论是否完整拼装
            crwords告知允许交叉叠加的词汇
            返回值: None - 非完整拼装(有缺口); 0 - 完整拼装(有交叉); 1 - 完整拼装(无交叉); 2 - 完整拼装(有允许的交叉)
        """
        mres, clst = self.parse(txt, False, nulst)
        if rsts is not None:
            fres, urc = mu.complete_segs(mres, len(txt), True)
            rsts.extend(fres)  # 记录分段结果
        else:
            urc = not mu.is_full_segs(mres, len(txt))
        if urc:
            return None  # 告知非完整拼装(有缺口)

        if len(clst) == 0:
            return 1  # 告知是完整拼装(无交叉)

        rl = clst[0][1]
        cr = clst[0][3]
        if rl == 'A&B' and txt[cr[0]:cr[1]] in crwords:
            return 2  # 告知是完整拼装(有允许的交叉)
        return 0  # 告知完整拼装(有交叉)

    def front(self, line):
        """根据已知前缀特征line_pre_patts,检查line的前缀特征,判断是否需要丢弃.返回值:需要丢弃的前缀长度"""

        if not line:
            return 0

        def chk_patt(patt):
            mres = re.findall(patt, line)
            if not mres:
                return 0  # 特定模式未匹配,不用跳过首部
            mrst = self.matcher.do_check(mres[0], mode=mac.mode_t.max_match)
            if not mrst:
                return len(mres[0])  # 模式匹配的部分是未知要素,跳过首部
            if mu.slen(mrst[0]) == len(mres[0]) and mrst[0][2] is not None:
                return 0  # 模式匹配的部分是完整的已知要素(用配置的数据规避匹配规则),不用跳过首部
            return len(mres[0])  # 其他情况,跳过首部

        for patt in uni.LINE_PRE_PATTS:
            sc = chk_patt(patt)
            if sc:
                return sc

        if line[0] == '(':
            m = uni.find_brackets(line, '()')
            if m[0] is None:
                return 1
        if line[0] == '[':
            m = uni.find_brackets(line, '[]')
            if m[0] is None:
                return 1
        if line[0] in {')', ']', '>'}:
            return 1
        return 0

    def extend(self, txt, names, lborder=3, rborder=2):
        """在txt文本中针对已经识别出的names实体集合,进行左右border延展分析,用于规避神经网络识别时导致的匹配缺失或错误等问题.
            返回值:[(nb,ne,oldname,ob,oe)],(nb,ne)为延展后新分段位置,oldname为names中传入的原实体名,(ob,oe)为原实体名匹配的位置
        """
        # 先构建全文匹配树
        ac = mac.ac_match_t()
        for name in names:
            ac.dict_add(name)
        ac.dict_end()
        # 进行全文匹配,定位每个名字匹配的位置
        mres = ac.do_check(txt, mode=mac.mode_t.max_match)
        # 进行扩展分析
        return self.expand(txt, mres, lborder, rborder)

    def expand(self, txt, mres, lborder, rborder):
        """在txt文本中针对已经识别出的mres实体分段集合,进行左右border延展分析,用于规避神经网络识别时导致的匹配缺失或错误等问题.
            返回值:[(nb,ne,oldname,ob,oe)],(nb,ne)为延展后新分段位置,oldname为names中传入的原实体名,(ob,oe)为原实体名匹配的位置
        """
        rst = []

        def check(b, e, lborder, rborder):
            """对txt中(b,e)处的实体名进行(b-lborder, e+rborder)延展分析.返回值:(nb,ne,name)
                核心动作:1 判断是否可以被front丢弃前缀;2判断是否可以被verify丢弃尾缀;3是否可以进行前缀补全
            """
            name = txt[b:e]  # 原实体名
            loffset = b - lborder  # 左侧延展后的开始位置
            xname = txt[loffset:e + rborder]  # 延展后的文本

            segs = []
            nts = self.verify(xname, segs)  # 对延展后的文本进行整体校验
            if not nts:
                return None  # 尾部特征校验未通过,直接返回
            ne = nts[-1][1] + loffset  # 记录最长的尾部偏移

            skip = self.front(name)
            if skip:
                nb = b + skip  # 如果原名字存在需丢弃前缀,则可以直接返回了.
                return nb, ne, name, b, e

            # 现在判断是否需要进行首部补全
            idx = 0
            while segs[idx][1] <= lborder:
                idx += 1
            head = segs[idx]  # 选取最接近原首段的新匹配段

            if head[2] & {types.NS, types.NZ, types.NN}:
                nb = head[0] + loffset  # 使用新的首段作为左侧延展位置
            else:
                nb = b

            return nb, ne, name, b, e

        for mr in mres:
            lborder = lborder if mr[0] >= lborder else mr[0]  # 左侧可延展的边界距离
            rborder = rborder if mr[1] + rborder <= len(txt) else len(txt) - mr[1]  # 右侧可延展的边界距离
            nr = check(mr[0], mr[1], lborder, rborder)
            if nr:
                rst.append(nr)

        return rst
