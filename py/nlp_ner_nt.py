'''
    基于HMM进行完整NER/NT功能实现,并提供一些相关工具.
    1 定义NT行业类型
    2 定义常见NT尾缀,并标注行业类型/常见扩展/排除词表
    3 提供NT名称校验功能,用于剔除无效名称
    4 提供NT组分处理功能,用于NER识别
    5 提供最终的NER/NT识别工具
'''
import re
from inspect import isfunction
from copy import deepcopy
from collections.abc import Iterable

import match_ac as mac
import match_util as mu
import china_area_id as cai
import nlp_ner_hmm as nnh
import nlp_ner_data as nnd
import nlp_util as nu
from nlp_ner_data import types
import util_base as ub
import uni_blocks as uni


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需给出尽量准确的分词结果,而本解析器则尝试进行组合覆盖,给出覆盖后的分段特征结果.
    '''
    tags_NM = {types.NM}  # 组织机构/后缀
    tags_NZ = {types.NZ}  # 专业名词
    tags_NN = {types.NN}  # 名称字号
    tags_NU = {types.NU}  # 数字序号
    tags_NA = {types.NA}  # 弱化名字
    tags_NO = {types.NO}  # 单独尾字
    tags_NB = {types.NB}  # 分支机构
    tags_NS = {types.NS}  # 地域名称
    tags_NS1 = {types.NS, types.NS1}
    tags_NS2 = {types.NS, types.NS2}
    tags_NS3 = {types.NS, types.NS3}
    tags_NS4 = {types.NS, types.NS4}
    tags_NS5 = {types.NS, types.NS5}
    tags_NSNM = {types.NS, types.NM}

    @staticmethod
    def __nu_nm(lst, mres):
        """构造数字分支匹配结果"""
        for m in mres:
            # 先将数字部分放入结果列表
            span = m.span(1)
            b = span[0]
            if m.groups()[0] == '第':
                b -= 1
            lst.append((b, span[1], nt_parser_t.tags_NU))

            # 再放入后面的尾缀
            span = m.span(2)
            lst.append((span[0], span[1], nt_parser_t.tags_NO if mu.slen(span) == 1 else nt_parser_t.tags_NB))

    @staticmethod
    def __nu_ns(lst, mres):
        """构造数字地名匹配结果"""
        for m in mres:
            rge = m.span()
            lst.append((rge[0], rge[1], nt_parser_t.tags_NS))

    @staticmethod
    def __nu(lst, mres):
        """构造数字和序号的匹配结果"""
        for m in mres:
            rge = m.span()
            lst.append((rge[0], rge[1], nt_parser_t.tags_NU))

    # 数字序号分支归一化
    num_norm = [
        (r'第?([○O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟廿卅]{1,6})([分号大]*[厂店部亭号组校院馆台处师村团营局园队所站区会厅库连矿])(?![件河乡镇])', 1, __nu_nm.__func__),
        (r'([○O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟廿卅]{1,6})(分公司|公司|采区|医院|门市|分行|队组|牧场|监狱|食堂)', 1, __nu_nm.__func__),
        (r'[第东南西北GSX]*([○O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟廿卅]{1,6})(公里|号院|马路|[路弄街里亩线楼室栋段])', 1, __nu_ns.__func__),
        (r'第?([○O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟廿卅]{1,6})([中小])(?![学])', 1, __nu_ns.__func__),
        (r'第([○O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟廿卅]{1,6})[号届]?', 1, __nu.__func__),
        (r'([○O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟廿卅]{2,6})[号]?', 1, __nu.__func__),
    ]

    # 行前缀检查模式
    line_pre_patts = [r'^([\s\n\._①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇]+)']

    @staticmethod
    def nums(txt, nulst=None):
        """查找文本txt中出现的数字部分,nulst可给出外部数字模式匹配列表.返回值:[(b,e)]"""
        rst = []
        if not nulst:
            nulst = nt_parser_t.num_norm
        for pat in nulst:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            for m in mres:
                span = m.span(pat[1])
                if span not in rst:
                    rst.append(span)
        return sorted(rst, key=lambda x: x)

    @staticmethod
    def query_nu(txt, nulst=None):
        """查询txt中的数字相关特征模式,nulst可给出外部数字模式匹配列表.返回值:[b,e,{types}]"""
        rst = []
        if not nulst:
            nulst = nt_parser_t.num_norm
        for pat in nulst:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            pat[2](rst, mres)
        ret = sorted(rst, key=lambda x: x[0])
        return nt_parser_t.__merge_segs(ret)[0]

    def __init__(self, light=False):
        self._load_check_cb = None  # 检查词典回调输出函数
        self.matcher = mac.ac_match_t()  # 定义ac匹配树
        self._loaded_base_nt = False  # 是否装载过内置NT数据
        self._bads = self.make_tails_bads()  # 尾缀坏词匹配器
        self.matcher.dict_add('.', self.tags_NZ)  # NT中的连字符,被统一替换为'.'之后,认为其是一个专属组份
        if light:
            self.load_nt(isend=False)
            self.load_ns(isend=True)

    @staticmethod
    def make_tails_bads():
        """利用内置NT组份表构造坏词匹配器"""
        trie = nu.words_trie_t(True)  # 反向匹配器
        for tn in nnd.nt_tails:
            bads = nnd.nt_tails[tn]['-']
            for en in bads:  # 记录排斥词汇
                trie.add(en)
        return trie

    def __load(self, fname, tags, encode='utf-8', vals_cb=None):
        """装载词典文件fname并绑定数据标记tags,返回值:''正常,否则为错误信息."""

        def add(txt, tag, row):
            ret = self.matcher.dict_add(txt, tag, force=True)
            if self._load_check_cb is not None and ret is False:
                b, e, ctag = self.matcher.do_check(txt)[0]
                self._load_check_cb(fname, row, txt, tag, ctag.difference(tag))

        try:
            row = -1
            with open(fname, 'r', encoding=encode) as fp:
                for _line in fp:
                    row += 1
                    txt = _line.strip()
                    if not txt or txt[0] == '#':
                        continue
                    if vals_cb:
                        vals = vals_cb(txt)
                        for val in vals:
                            add(val[0], val[1], row)
                    else:
                        tag = tags(txt) if isfunction(tags) else tags
                        add(txt, tag, row)
            return ''
        except Exception as e:
            return e

    def add_words(self, words, tags, isend=True):
        """添加指定的词汇列表到匹配树中"""
        for word in words:
            self.matcher.dict_add(word, tags, force=True)
        if isend:
            self.matcher.dict_end()

    def load_nt(self, fname=None, encode='utf-8', isend=True, with_NO=True, keys=None, debars=None):
        """装载NT尾缀词典,返回值:''正常,否则为错误信息."""
        ret = self.__load(fname, self.tags_NM, encode) if fname else ''

        # 初始化构建匹配词表
        if not self._loaded_base_nt:
            for k in nnd.nt_tails:
                data = nnd.nt_tails[k]
                assert '.' in data and '+' in data and '-' in data, data
                if keys and k not in keys:
                    continue
                tags = data['.']
                exts = data['+']
                nobs = data['-']
                if len(k) > 1 or (len(k) == 1 and with_NO):
                    if not debars or k not in debars:
                        self.matcher.dict_add(k, tags, force=True)
                for e in exts:
                    if debars and e in debars:
                        continue
                    r = self.matcher.dict_add(e, tags, force=True)
                    if not r:
                        print(f'nt_parser_t.nt_tails+: {k}/{e} is repeat!')
            self._loaded_base_nt = True

        if isend:
            self.matcher.dict_end()
        return ret

    def load_ns(self, fname=None, encode='utf-8', isend=True, worlds=True, lv_limit=5, drops_tailchars={'省', '市', '区', '县', '州', '盟', '旗', '乡', '村', '镇'}):
        """装载NS组份词典,worlds告知是否开启全球主要地区.返回值:''正常,否则为错误信息."""
        lvls = {0: self.tags_NS, 1: self.tags_NS1, 2: self.tags_NS2, 3: self.tags_NS3, 4: self.tags_NS4, 5: self.tags_NS5}
        for id in cai.map_id_areas:  # 装入内置的行政区划名称
            alst = cai.map_id_areas[id]
            lvl = cai.query_aera_level(alst[0])  # 根据正式地名得到行政区划级别
            if lvl > lv_limit:
                continue
            tags = lvls[lvl]
            for name in alst:
                self.matcher.dict_add(name, tags, force=True)
                aname = cai.drop_area_tail(name, drops_tailchars)
                if name != aname and aname not in nnd.nt_tail_datas:
                    self.matcher.dict_add(aname, tags, force=True)  # 特定尾缀地区名称,放入简称

        if worlds:
            for state in cai.map_worlds:  # 装入内置的世界主要国家与首都
                city = cai.map_worlds[state]
                self.matcher.dict_add(state, self.tags_NS, force=True)
                self.matcher.dict_add(city, self.tags_NS1, force=True)

            stats = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚', '东南亚']
            for state in stats:
                self.matcher.dict_add(state, self.tags_NS, force=True)

        def ns_tags(line):
            """根据地名进行行政级别查询,返回对应的标记"""
            if line[-2:] in {'社区', '林场', '农场', '牧场', '渔场'}:
                return self.tags_NSNM
            lvl = cai.query_aera_level(line)
            return lvls[lvl]

        labels = {'A': self.tags_NA, 'S': self.tags_NS, 'M': self.tags_NM, 'N': self.tags_NN, 'Z': self.tags_NZ}

        def vals_cb(line):
            segs = line.split('!')  # 尝试拆分标注记号
            name = segs[0]  # 得到原始地名
            lbl = segs[1] if len(segs) == 2 else 'N'  # 得到标注记号
            if lbl and lbl not in labels:
                print('ERROR:NS/FILE/LABEL:', line)
                lbl = ''

            if lbl == '':  # 不要求进行解析处理
                return [(name, ns_tags(name))]
            # 解析得到主干部分
            aname = cai.drop_area_tail(name, drops_tailchars)
            if name != aname and aname not in nnd.nt_tail_datas:
                return [(name, ns_tags(name)), (aname, labels[lbl])]
            return [(name, self.tags_NS)]

        ret = self.__load(fname, self.tags_NS, encode, vals_cb) if fname else ''
        if isend:
            self.matcher.dict_end()
        return ret

    def load_nz(self, fname, encode='utf-8', isend=True):
        """装载NZ组份词典,返回值:''正常,否则为错误信息."""
        ret = self.__load(fname, self.tags_NZ, encode)
        if isend:
            self.matcher.dict_end()
        return ret

    def load_nn(self, fname, encode='utf-8', isend=True):
        """装载NN尾缀词典,返回值:''正常,否则为错误信息."""
        ret = self.__load(fname, self.tags_NN, encode)
        if isend:
            self.matcher.dict_end()
        return ret

    def loads(self, dicts):
        """统一装载词典列表dicts=[('类型','路径')].返回值:空串正常,否则为错误信息."""
        rst = []
        for i, d in enumerate(dicts):
            isend = i == len(dicts) - 1
            if d[0] == 'NS':
                r = self.load_ns(d[1], isend=isend)
            elif d[0] == 'NT':
                r = self.load_nt(d[1], isend=isend)
            elif d[0] == 'NZ':
                r = self.load_nz(d[1], isend=isend)
            elif d[0] == 'NN':
                r = self.load_nn(d[1], isend=isend)
            if r != '':
                rst.append(r)
        return ''.join(rst)

    @staticmethod
    def merge_bracket(segs, txt):
        """合并segs段落列表中被左右括号包裹的部分,返回值:结果列表"""
        rst = []
        pos = 0

        def is_brackets(a, b):
            if a == '(' and b == ')':
                return True
            if a == '<' and b == '>':
                return True
            if a == '"' and b == '"':
                return True
            return False

        for seg in segs:  # 对待记录的段落逐一进行检查
            if seg[0] > 0 and seg[1] < len(txt):
                p = seg[0] - 1
                n = seg[1]
                if is_brackets(txt[p], txt[n]):
                    rst.append((p, n + 1, {a for a in seg[2]}))  # 当前是"(北京)"这样的括号地区,那么需要进行范围修正
                    continue
            rst.append((seg[0], seg[1], {a for a in seg[2]}))  # 记录原有段落,重新构造新元素,规避对原始对象的涂改.

        return rst

    @staticmethod
    def drop_nesting(segs, txt):
        """丢弃segs段落列表中被完全包含嵌套的部分,返回值:结果列表"""
        rst = []

        def chk(rst, seg):
            """检查并处理当前段在已记录结果中的重叠情况.返回值:是否记录当前段"""
            while rst:
                last = rst[-1]
                r = mu.related_segs(last, seg)[0]
                if r in {'A@B', 'A=B'}:
                    if nnd.types.cmp(last[2], seg[2]) >= 0:
                        return False  # 当前段被包含且优先级较低,不记录
                    else:
                        return True
                elif r == 'B@A':
                    rst.pop(-1)  # 前一个段落被包含,丢弃
                else:
                    return True
            return True  # 默认情况,记录当前段

        for seg in segs:  # 对待记录的段落逐一进行检查
            if chk(rst, seg):
                rst.append(seg)  # 记录合法的段落
        return rst

    @staticmethod
    def drop_crossing(segs, bylvl=False):
        """丢弃segs段落列表中被交叉重叠的部分"""
        drops = []
        # for i in range(len(segs) - 2, 0, -1):
        #     c = segs[i]  # 当前段
        #     p = segs[i - 1]  # 前段
        #     n = segs[i + 1]  # 后段
        #     if p[1] == n[0]:  # 当前段被前后段重叠接续
        #         if bylvl and mu.related_segs(c, n)[0] in {'A@B', 'A==B'} and nnd.types.cmp(c[2], n[2]) > 0:
        #             # 如果判断分段优先级,并且后段被中段包含,则丢弃后段
        #             drops.append(n)
        #             segs.pop(i + 1)
        #             continue
        #
        #         # 否则丢弃中段
        #         drops.append(c)
        #         segs.pop(i)
        i = 1
        while i < len(segs) - 1:
            p = segs[i - 1]  # 前段
            c = segs[i]  # 当前段
            n = segs[i + 1]  # 后段
            if p[1] != n[0]:
                i += 1
                continue
            # 当前段被前后段重叠接续
            if bylvl and mu.related_segs(c, n)[0] in {'A@B', 'A==B'} and nnd.types.cmp(c[2], n[2]) > 0:
                # 如果判断分段优先级,并且后段被中段包含,则丢弃后段
                drops.append(n)
                segs.pop(i + 1)
            else:
                # 否则丢弃中段
                drops.append(c)
                segs.pop(i)

        return drops

    @staticmethod
    def __merge_segs(segs, merge_types=True, combi=False):
        '''处理segs段落列表中交叉/包含/相同组份合并(merge_types)的情况,返回值:(结果列表,叠加次数)'''
        rst = []
        clst = []

        def rec_tags_merge(pseg, seg):
            """记录前后两个段落的合并结果"""
            att = set(pseg[2])
            att.update(seg[2])  # 合并标记集合
            rst[-1] = (pseg[0], seg[1], att)  # 记录合并后的新段

        def can_combi_NM(pseg, seg):
            if types.joint(pseg[2], (types.NZ, types.NS)) and types.equ(seg[2], types.NM) and pseg[1] > seg[0]:
                return True  # NZ交叉NM/NS交叉NM,则强制合并前后段
            if types.joint(pseg[2], (types.NZ,)) and types.equ(seg[2], types.NO) and pseg[1] == seg[0]:
                return True  # NZ紧邻NO/NS紧邻NO,则强制合并前后段
            return False

        def rec_tags_cross(pseg, seg):
            """记录前后两个段落的相交结果"""
            assert pseg == rst[-1]
            if combi and can_combi_NM(pseg, seg):
                rst[-1] = (pseg[0], seg[1], seg[2])  # NM交叉或NO紧邻,则强制合并前后段
                return
            elif pseg[1]>seg[0]:
                if types.type(pseg[2]) < types.type(seg[2]):
                    rst[-1] = (pseg[0], seg[0], pseg[2])  # 后段重要,调整前段范围即可
                else:
                    seg = (pseg[1], seg[1], seg[2])  # 前段重要,调整后段范围
            rst.append(seg)  # 记录后段信息

        def rec_tags_cont(pseg, seg):
            """记录seg包含pseg的结果"""
            if types.type(pseg[2]) < types.type(seg[2]):
                rst[-1] = (pseg[0], seg[1], seg[2])  # 后段重要,替换前段范围
            else:
                rst[-1] = (pseg[0], seg[1], pseg[2])  # 前段重要,调整前段范围

        for seg in segs:
            if not rst:
                rst.append(seg)
                continue
            pseg = rst[-1]
            rl, cr = mu.related_segs(pseg, seg)
            if rl != 'A+B':
                clst.append((pseg, rl, seg, cr))  # 不是顺序连接,那就记录关联情况
            if rl in {'A+B', 'A&B'}:
                if merge_types and types.equ(pseg[2], seg[2]):
                    rec_tags_merge(pseg, seg)
                else:
                    rec_tags_cross(pseg, seg)
            elif rl == 'A@B':
                continue  # 丢弃后面被包含的段
            elif rl == 'B@A':
                if merge_types and types.equ(pseg[2], seg[2]):
                    rec_tags_merge(pseg, seg)
                else:
                    rec_tags_cont(pseg, seg)
            else:
                rst.append(seg)

        return rst, clst

    @staticmethod
    def __merge_nums(segs, nums):
        """将nums中的分段信息合并到segs中"""
        begin = 0

        def find(pos):
            """在segs中查找begin索引之后出现pos位置的索引"""
            nonlocal begin
            for i in range(begin, len(segs)):
                seg = segs[i]
                if seg[0] >= pos:
                    begin = i + 1
                    return i
            return len(segs)

        for nu in nums:
            idx = find(nu[0])
            segs.insert(idx, nu)

    def parse(self, txt, merge=True, nulst=None, combi=False):
        '''在txt中解析可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            combi - 是否合并NZ&NM的交叉情况
            返回值:(分段列表[(b,e,{types})],分段关系列表[(pseg,rl,nseg,cr)])
        '''

        def cross_ex(rst, pos, node, root):
            """交叉保留,丢弃重叠包含的匹配"""

            def can_drop_old(n, o):
                """判断新分段n是否应该踢掉旧分段o:
                    1 如果新分段的起点小于已有分段的起点
                    2 新分段与旧分段相交,且新分段的类型优先级更高.
                """
                if n[0] < o[0]:
                    return True
                if n[0] >= o[1]:
                    return False
                return n[0] == o[0] and types.cmp(n[2], o[2]) >= 0

            def rec(node):
                """记录当前节点对应的匹配分段到结果列表"""
                if node == root:
                    return
                # 当前待记录的新匹配分段
                seg = pos - node.words, pos, node.end
                while rst and can_drop_old(seg, rst[-1]):
                    rst.pop(-1)  # 踢掉旧结果
                # if rst and seg[1] <= rst[-1][1]:
                #     return
                rst.append(seg)

            rec(node.first)
            if node.first != node.fail and node.fail.end:
                rec(node.fail)  # 尝试多记录一下可能有用的次级匹配结果,解决(佛山海关/山海关/海关)的问题

        segs = self.matcher.do_check(txt, mode=cross_ex)  # 按词典进行完全匹配
        mres = self.merge_bracket(segs, txt)  # 合并附加括号
        if not mu.is_full_segs(mres, len(txt)):
            nums = self.query_nu(txt, nulst)  # 进行数字序号匹配
            if nums:
                self.__merge_nums(mres, nums)
        self.drop_crossing(mres, True)  # 删除接续交叉重叠
        nres = self.drop_nesting(mres, txt)  # 删除嵌套包含的部分
        self.drop_crossing(nres)  # 删除接续交叉重叠
        return self.__merge_segs(nres, merge, combi)

    def query(self, txt, merge=True, nulst=None, with_useg=False, combi=False):
        '''在txt中查找可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否进行未使用分段的填充
            返回值:[(b,e,{types})]或[]
        '''
        rst, ext = self.parse(txt, merge, nulst, combi)
        if with_useg:
            return mu.complete_segs(rst, len(txt), True)[0]
        else:
            return rst

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

    def verify(self, name, segs=None, merge_types=False, combi=True):
        """对name中出现的多重NT构成特征进行拆分并校验有效性,如附属机构/分支机构/工会
            segs - 可记录组份分段数据的列表.
            返回值:分隔点列表[(bpos,epos,types)]
                  返回的types只有NM与NB两种组份模式
        """
        cons, _ = self.parse(name, merge_types, combi=combi)
        segs, _ = mu.complete_segs(cons, len(name), True, segs)
        opos = []
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

        def chk_errs(i, seg):
            """检查当前段是否为错误切分.如'师范学院路'->师范学院/学院路->师范/学院路,此时的'师范'仍是NM,但明显是错误的."""
            if types.equ(seg[2], types.NM) and mu.slen(seg) >= 2:
                p = segs[i - 1][0] if i > 0 else 0
                txt = name[p:seg[1]]
                mres = self.matcher.do_check(txt)  # 按词典进行全部匹配
                for mr in mres:
                    if mr[1] == len(txt) and types.equ(mr[2], types.NM):
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
            newr = (bpos, epos, stype)
            if opos and types.joint(seg[2], (types.NO, types.NM)):
                oldr = opos[-1]  # 当前段是NO单字尾缀,需要尝试剔除前一个紧邻的结果分段
                if oldr[0] == newr[0] and oldr[1] == newr[1] - 1:
                    opos.pop(-1)  # 后一段结果比前一段结果多一个字,则丢弃前段结果
            opos.append(newr)

        for i, seg in enumerate(segs):
            stype = seg[2]
            epos = seg[1]
            islast = i == len(segs) - 1
            if types.joint(stype, (types.NM, types.NL)):
                rec(i, seg, bpos, epos, types.NM)  # 当前段是普通NT结尾,记录
            elif types.equ(stype, types.NB):
                rec(i, seg, bpos, epos, types.NB)  # 当前段是分支NT结尾,记录
            elif types.equ(stype, types.NO) and i > 0 and islast:
                # 当前段是单字NT结尾,需要判断特例
                pseg = segs[i - 1]
                if types.joint(pseg[2], (types.NZ, types.NU, types.NS, types.NN, types.NB)):
                    rec(i, seg, bpos, epos, types.NM)  # `NZ|NO`/`NU|NO`/`NS|NO`/`NN|NO`/`NB/NO`可以作为NT机构
                elif types.joint(pseg[2], (types.NM, types.NO, types.NA)):
                    if name[pseg[1] - 1] != name[seg[0]] or name[seg[0]] in {'店', '站'}:
                        rec(i, seg, bpos, epos, types.NM)  # `NM|NO` 不可以为'图书馆馆'/'经销处处',可以是'马店店'/'哈站站',可以作为NT机构
        return opos

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
                return 0  # 模式匹配的部分是完整的已知要素,不用跳过首部
            return len(mres[0])  # 其他情况,跳过首部

        for patt in self.line_pre_patts:
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

            if types.joint(head[2], (types.NS, types.NZ, types.NN)):
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


def make_segs_chars(txt, segs, offset=0, nx=False):
    """将txt文本的segs分段列表,转换为字符列表与对应的分段属性列表.
        nx - 控制是否使用NX标记代替未知短语
        返回值:([字符列表],[字符对应的分段属性(b,e,att)])
    """
    chars = []
    ranges = []
    for seg in segs:
        if seg[2] is None:
            if nx:
                chars.append(chr(types.NX.value))
                ranges.append((offset + seg[0], offset + seg[1], types.NX))
            else:
                for i in range(seg[0], seg[1]):
                    chars.append(txt[i])
                    ranges.append((offset + i, offset + i + 1, None))
        else:
            t = types.type(seg[2])
            chars.append(chr(t.value))
            ranges.append((offset + seg[0], offset + seg[1], t))
    return chars, ranges


def make_segs_tags(line, segs, nx=False):
    """根据组份分段列表segs和文本串line,生成标记表达格式串
        nx - 控制是否使用NX标记代替未知短语
        返回值:[标记或未知短语]
    """
    usegs = []
    for useg in segs:
        if useg[2] is None:
            if nx:
                t = nnd.types.NX.name
            else:
                t = line[useg[0]:useg[1]]
        else:
            t = nnd.types.type(useg[2]).name
        usegs.append(t)
    return usegs


def calc_range_map(bidx, eidx, ranges):
    """获取make_segs_chars返回的分段映射对应的实际范围"""
    return ranges[bidx][0], ranges[eidx][1]


def conv_names_list(fn_name, out_name, dicts, tag=False, nx=False):
    """转换nt样例文件fn_names中的每行值为组份要素构成,输出到out_name文件中.
        fn_names = 命名实体样例文件名称
        out_name = 输出文件名称
        dicts = 解析组份需要的词典数据列表
        tag = 是否输出带有类型标记的可阅读文本串,或输出不可阅读的类型字符文本串
        nx = 是否未知短语也被NX类型替代.(最大化压缩)
    """
    mchk = nt_parser_t(False)
    mchk.loads(dicts)

    stats = {}
    rc = 0
    with open(fn_name, 'r', encoding='utf-8') as fn:
        line = fn.readline().strip()
        while line:
            mres = mchk.query(line, with_useg=True)
            if tag:
                chars = make_segs_tags(line, mres, nx)
                out = '|'.join(chars)
            else:
                chars, segs = make_segs_chars(line, mres, nx)
                out = ''.join(chars)
            ub.inc(stats, out)
            line = fn.readline().strip()
            rc += 1
            if rc % 1000 == 0:
                print(rc)

    keys = sorted(stats.keys(), key=lambda x: (stats[x], x))
    with open(out_name, 'w+', encoding='utf-8') as out:
        for key in keys:
            out.write(f'{key}:{stats[key]}\n')


def load_tags_tree(fn_name, ac=None, end=True):
    """装载nt样本组份文件fn_name到ac匹配树.返回值:ac匹配树对象"""
    if ac is None:
        ac = mac.ac_match_t()
    with open(fn_name, 'r', encoding='utf-8') as fn:
        line = fn.readline()
        while line:
            seg, frq = line.split(':')
            ac.dict_add(seg, int(frq))
            line = fn.readline()
    if end:
        ac.dict_end()
    return ac
