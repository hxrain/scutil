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
import china_area_id as ca
import nlp_ner_hmm as nnh
import nlp_ner_data as nnd
import nlp_util as nu
from nlp_ner_data import types
import util_base as ub


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需要给出尽量准确的分词结果,而本解析器则尽可能的对目标串进行组合覆盖,给出覆盖后的分段列表.
    '''
    tags_NM = {types.NM}  # 组织机构/后缀
    tags_NZ = {types.NZ}  # 专业名词
    tags_NN = {types.NN}  # 名称字号
    tags_NU = {types.NU}  # 数字序号
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
        (r'第?([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)([分号]*[小中厂店部亭号组校院馆台处师村团局园队所站区会厅库连矿届])(?![件河乡镇])', 1, __nu_nm.__func__),
        (r'([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)(分公司|公司)', 1, __nu_nm.__func__),
        (r'[第东南西北]*([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)(马路|路|弄|街|里|亩|线)', 1, __nu_ns.__func__),
        (r'第([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)[号]?', 1, __nu.__func__),
        (r'([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]{2,})[号]?', 1, __nu.__func__),
    ]

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

        def add(txt, tag):
            ret = self.matcher.dict_add(txt, tag, force=True)
            if self._load_check_cb is not None and ret is False:
                b, e, ctag = self.matcher.do_check(txt)[0]
                self._load_check_cb(fname, row, txt, tag, ctag.difference(tag))

        try:
            row = -1
            with open(fname, 'r', encoding=encode) as fp:
                for line in fp:
                    row += 1
                    if not line:
                        continue
                    txt = line[:-1] if line[-1] == '\n' else line
                    if vals_cb:
                        vals = vals_cb(txt)
                        for val in vals:
                            add(val[0], val[1])
                    else:
                        tag = tags(txt) if isfunction(tags) else tags
                        add(txt, tag)
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
        for id in ca.map_id_areas:  # 装入内置的行政区划名称
            alst = ca.map_id_areas[id]
            lvl = ca.query_aera_level(alst[0])  # 根据正式地名得到行政区划级别
            if lvl > lv_limit:
                continue
            tags = lvls[lvl]
            for name in alst:
                self.matcher.dict_add(name, tags, force=True)
                aname = ca.drop_area_tail(name, drops_tailchars)
                if name != aname and aname not in nnd.nt_tail_datas:
                    self.matcher.dict_add(aname, tags, force=True)  # 特定尾缀地区名称,放入简称

        if worlds:
            for state in ca.map_worlds:  # 装入内置的世界主要国家与首都
                city = ca.map_worlds[state]
                self.matcher.dict_add(state, self.tags_NS, force=True)
                self.matcher.dict_add(city, self.tags_NS1, force=True)

            stats = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚', '东南亚']
            for state in stats:
                self.matcher.dict_add(state, self.tags_NS, force=True)

        def ns_tags(line):
            """根据地名进行行政级别查询,返回对应的标记"""
            if line[-2:] in {'社区', '林场', '农场', '牧场', '渔场'}:
                return self.tags_NSNM
            lvl = ca.query_aera_level(line)
            return lvls[lvl]

        def vals_cb(name):
            if name[-1] == '!':
                return [(name[:-1], ns_tags(name[:-1]))]  # 特殊地名,不进行尾缀移除处理
            aname = ca.drop_area_tail(name, drops_tailchars)
            if name != aname and aname not in nnd.nt_tail_datas:
                return [(name, ns_tags(name)), (aname, self.tags_NN)]
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
                    rst.append((p, n + 1, deepcopy(seg[2])))  # 当前是"(北京)"这样的括号地区,那么需要进行范围修正
                    continue
            rst.append((seg[0], seg[1], deepcopy(seg[2])))  # 记录原有段落,重新构造新元素,规避对原始对象的涂改.

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
    def drop_crossing(segs):
        """丢弃segs段落列表中被交叉重叠的部分"""
        drops = []
        for i in range(len(segs) - 2, 0, -1):
            c = segs[i]  # 当前匹配分段
            p = segs[i - 1]  # 前匹配分段
            n = segs[i + 1]  # 后匹配分段
            if p[1] == n[0]:  # 当前匹配分段恰好被前后分段重叠接续,则放弃当前分段
                drops.append(c)
                segs.pop(i)
        return drops

    @staticmethod
    def __merge_segs(segs, merge_types=True):
        '''处理segs段落列表中交叉/包含/相同组份合并(merge_types)的情况,返回值:(结果列表,叠加次数)'''
        rst = []
        clst = []

        def rec_tags_merge(pseg, seg):
            """记录前后两个段落的合并结果"""
            pseg[2].update(seg[2])  # 合并标记集合
            rst[-1] = (pseg[0], seg[1], pseg[2])  # 记录合并后的新段

        def rec_tags_cross(pseg, seg):
            """记录前后两个段落的相交结果"""
            assert pseg == rst[-1]
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
                clst.append((pseg, rl, seg, cr))  # 不是顺序连接,那就记录交叉情况
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

    def parse(self, txt, merge=True, nulst=None):
        '''在txt中解析可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
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
        nres = self.drop_nesting(mres, txt)  # 删除嵌套包含的部分
        self.drop_crossing(nres)  # 删除交叉重叠
        return self.__merge_segs(nres, merge)

    def query(self, txt, merge=True, nulst=None, with_useg=False):
        '''在txt中查找可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否进行未使用分段的填充
            返回值:[(b,e,{types})]或[]
        '''
        rst, ext = self.parse(txt, merge, nulst)
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

    def verify(self, name, segs=None, merge_types=False):
        """对name中出现的多重NT构成进行分组并校验有效性,如附属机构/分支机构/工会
            segs - 可记录组份分段数据的列表.
            返回值:分隔点列表[(bpos,epos,types)]
                  返回的types只有NM与NB两种机构类型
        """
        cons, _ = self.parse(name, merge_types)
        segs, _ = mu.complete_segs(cons, len(name), True, segs)
        opos = []
        bpos = 0

        def rec(bpos, epos, stype):
            opos.append((bpos, epos, stype))

        def chk_bads(i, seg):
            """检查当前段尾缀是否为坏词.返回值:尾部匹配了坏词"""
            end = len(segs) - 1
            if i == end:
                # 最后一段,直接判定
                txt = name[bpos:seg[1]]
                begin, deep, node = self._bads.query(txt, True)
                return deep > 0 and not node
            else:
                # 非最后段,先直接判定
                txt = name[bpos:seg[1]]
                begin, deep, node = self._bads.query(txt, True)
                if deep > 0 and not node:
                    return True
                # 再扩展判定
                txt += name[seg[1]:seg[1] + 3]
                begin, deep, node = self._bads.query(txt, False)
                return deep > 0 and not node

        for i, seg in enumerate(segs):
            stype = seg[2]
            epos = seg[1]
            if chk_bads(i, seg):
                bpos = epos  # 当前段含有坏词,跳过
            elif types.joint(stype, (types.NM, types.NL)):
                rec(bpos, epos, types.NM)  # 当前段是普通NT结尾,记录
            elif types.equ(stype, types.NB):
                rec(bpos, epos, types.NB)  # 当前段是分支NT结尾,记录
            elif types.equ(stype, types.NO) and i > 0 and i == len(segs) - 1:
                # 当前段是单字NT结尾,需要判断特例
                pseg = segs[i - 1]
                if types.joint(pseg[2], (types.NZ, types.NU, types.NS, types.NN, types.NB)):
                    rec(bpos, epos, types.NM)  # `NZ|NO`/`NU|NO`/`NS|NO`/`NN|NO`可以作为NT机构
                elif types.joint(pseg[2], (types.NM, types.NO)):
                    if name[pseg[1] - 1] != name[seg[0]] or name[seg[0]] in {'店', '站'}:
                        rec(bpos, epos, types.NM)  # `NM|NO` 不可以为'图书馆馆'/'经销处处',可以是'马店店'/'哈站站',可以作为NT机构
        return opos
