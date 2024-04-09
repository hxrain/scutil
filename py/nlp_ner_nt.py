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
import nlp_ner_data as nnd
from nlp_ner_data import types
import nlp_util as nu
import util_base as ub
import uni_blocks as uni
import os


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
    tags_NUNM = {types.NU, types.NM}  # 序号机构
    tags_NUNB = {types.NU, types.NB}  # 序号分支
    tags_NS = {types.NS}  # 地域名称
    tags_NS1 = {types.NS, types.NS1}
    tags_NS2 = {types.NS, types.NS2}
    tags_NS3 = {types.NS, types.NS3}
    tags_NS4 = {types.NS, types.NS4}
    tags_NS5 = {types.NS, types.NS5}
    tags_NSNM = {types.NS, types.NM}
    tags_NH = {types.NH}  # 特殊名称

    @staticmethod
    def __nu_rec(lst, seg):
        """记录数字匹配结果,规避多条规则的重复匹配分段,保留高优先级结果"""
        for i in range(len(lst)):
            rseg = lst[i]
            if rseg[0] == seg[0] and rseg[1] == seg[1]:
                if types.cmp(rseg[2], seg[2]) < 0:
                    lst[i] = seg  # 先进行一圈查找,如果存在与新分段重叠的段,则保留高优先级的分段.
                return
        lst.append(seg)

    @staticmethod
    def __nu_nm(lst, mres):
        """构造数字实体匹配结果"""
        for m in mres:
            grp2 = m.group(2)
            if grp2[0] in {'分'}:
                tag = nt_parser_t.tags_NUNB
            else:
                tag = nt_parser_t.tags_NUNM

            # 先将数字部分放入结果列表
            span = m.span()
            nt_parser_t.__nu_rec(lst, (span[0], span[1], tag))

    @staticmethod
    def __nu_nb(lst, mres):
        """构造数字分支匹配结果"""
        for m in mres:
            span = m.span()
            nt_parser_t.__nu_rec(lst, (span[0], span[1], nt_parser_t.tags_NUNB))

    @staticmethod
    def __nu_ns(lst, mres):
        """构造数字地名匹配结果"""
        for m in mres:
            rge = m.span()
            nt_parser_t.__nu_rec(lst, (rge[0], rge[1], nt_parser_t.tags_NS))

    @staticmethod
    def __nu_default(lst, mres, offset=0):
        """构造数字和序号的匹配结果"""
        for m in mres:
            rge = m.span()
            nt_parser_t.__nu_rec(lst, (rge[0] + offset, rge[1] + offset, nt_parser_t.tags_NU))

    # 数字序号基础模式
    num_re = r'[○O\d甲乙丙丁戊己庚辛壬癸幺零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾佰百千仟廿卅IⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{1,6}'
    # 数字序号常见模式
    num_norm = [
        (f'([经纬农第笫ABCDGKSXYZ]*{num_re}[号级大支#]*)(公里|马路|社区|[路弄街院里亩线楼栋段桥井闸门渠河沟江坝村区师机]+)', 1, __nu_ns.__func__),
        (f'([第笫]*{num_re}[号]?)([分]?部队|[团校院馆局会库矿场])', 1, __nu_nm.__func__),
        (f'([第笫]*{num_re}[号]?)([分]?[厂店台处站园亭部营连排厅社所组队船]|工区|分号)', 1, __nu_nb.__func__),
        (f'([第笫]*{num_re})([职中小高]+)(?![学])', 1, __nu_ns.__func__),
        (f'([第笫ABCDGKSXYZ]*{num_re}[号级大支只届年期次个度批委分#]*)', 1, __nu_default.__func__),
    ]

    # 行前缀章节号模式
    line_pre_patts = [r'^([\s\n\._①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇]+)']

    # 为了更好的利用地名组份信息,更好的区分主干部分的类型,引入了"!尾缀标注"模式,规则如下:
    # 1 未标注!的行,整体地名(S)进行使用,并在移除尾缀词后,主干部分作为名称(N)使用,等同于标注了!N
    # 2 标注!的且没有字母的,不拆分,将整体作为:地名(S)
    # 3 标注!后有其他字母的,主干部分按标注类型使用: A-弱化名称/S-地名/M-实体/U-序号/N-名称/Z-专业名词/H-特殊词/B-分支
    tag_labels = {'A': tags_NA, 'S': tags_NS, 'M': tags_NM, 'U': tags_NU,
                  'N': tags_NN, 'Z': tags_NZ, 'H': tags_NH, 'B': tags_NB}

    # 可进行特殊短语包裹的括号对
    brackets_map = {'<': '>', '(': ')', '[': ']', '"': '"', "'": "'"}
    brackets_rmap = {'>': '<', ')': '(', ']': '[', '"': '"', "'": "'"}

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
        return nt_parser_t._merge_segs(ret, False, False)[0]

    def __init__(self, light=False):
        self.matcher = mac.ac_match_t()  # 定义ac匹配树
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

    def __load(self, isend, fname, tags, encode='utf-8', vals_cb=None, chk_cb=None):
        """装载词典文件fname并绑定数据标记tags,返回值:''正常,否则为错误信息."""

        def add(word, tag, row, txt):
            ret, old = self.matcher.dict_add(word, tag, force=True)
            if chk_cb is not None and not ret:
                chk_cb(fname, row, txt, word, old)

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
                            add(val[0], val[1], row, txt)
                    else:
                        name, tag = nt_parser_t._split_label(txt)  # 内置标注解析处理
                        if not tag:
                            tag = tags
                        add(name, tag, row, txt)
            if isend:
                self.matcher.dict_end()
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

        # 初始化构建匹配词表
        if len(self.matcher.do_loop(None, '有限公司')) != 4:
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
                        r, ot = self.matcher.dict_add(k, tags, force=True)
                        if not r:
                            print(f'nt_parser_t.nt_tails: {k} is repeat! {ot}')
                for e in exts:
                    if debars and e in debars:
                        continue
                    r, ot = self.matcher.dict_add(e, tags, force=True)
                    if not r:
                        print(f'nt_parser_t.nt_tails+: {k}/{e} is repeat! {ot}')

        return self.__load(isend, fname, self.tags_NM, encode, chk_cb=self._chk_cb) if fname else ''

    def _chk_cb(self, fname, row, txt, word, tag):
        """默认的检查词典冲突的输出回调事件处理器"""
        if txt == word:
            print(f'<{fname}|{row + 1:>8},{len(txt):>2}>:{txt} repeat!<{tag}>')
        else:
            print(f'<{fname}|{row + 1:>8},{len(txt):>2}>:{txt} repeat {word}<{tag}>')

    @staticmethod
    def _split_label(line):
        """拆分字典行,得到名称与标注,返回值:(name,lbl)
            name - 为实际名称
            lbl - 标注对应类型:None无标注;''禁止拆分;其他为标注对应self.tag_labels类型
        """
        segs = line.split('!')  # 尝试拆分标注记号
        lbl = segs[1] if len(segs) == 2 else None  # 得到标注字符
        if lbl and lbl not in nt_parser_t.tag_labels:
            print('ERROR:DICT LINE UNKNOWN LABEL CHAR!', line)
            lbl = ''
        name = segs[0]  # 得到原名称
        if lbl:
            lbl = nt_parser_t.tag_labels[lbl]  # 江标注字符转换为对应类型
        return name, lbl

    def load_ns(self, fname=None, encode='utf-8', isend=True, worlds=True, lv_limit=5, drops_tailchars=None):
        """装载NS组份词典,worlds告知是否开启全球主要地区.返回值:''正常,否则为错误信息."""
        lvls = {0: self.tags_NS, 1: self.tags_NS1, 2: self.tags_NS2, 3: self.tags_NS3, 4: self.tags_NS4, 5: self.tags_NS5}
        # 装入内置的行政区划名称
        if len(self.matcher.do_loop(None, '牡丹江市')) != 4:
            for id in cai.map_id_areas:
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

        # 装入内置的区域名称
        if len(self.matcher.do_loop(None, '嘎查村')) != 3:
            for k in nnd.nt_tails:
                data = nnd.nt_tails[k]
                assert '.' in data and '+' in data and '-' in data, data
                tags = data['.']
                if not nnd.types.equ(tags, nnd.types.NS):
                    continue
                exts = data['+']
                nobs = data['-']
                r, ot = self.matcher.dict_add(k, tags, force=True)
                if not r:
                    print(f'nt_parser_t.nt_tails: {k} is repeat! {ot}')
                for e in exts:
                    r, ot = self.matcher.dict_add(e, tags, force=True)
                    if not r:
                        print(f'nt_parser_t.nt_tails+: {k}/{e} is repeat! {ot}')

        # 装入内置的世界主要国家与首都
        if worlds and len(self.matcher.do_loop(None, '环太平洋')) != 4:
            for state in cai.map_worlds:
                city = cai.map_worlds[state]
                r, ot = self.matcher.dict_add(state, self.tags_NS, force=True)
                if not r:
                    print(f"nlp_ner_nt.load_ns state is repeat: {state} {ot}")

                if city:
                    r, ot = self.matcher.dict_add(city, self.tags_NS1, force=True)
                    if not r:
                        print(f"nlp_ner_nt.load_ns city is repeat: {city} {ot}")

            areas = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚', '东南亚']
            for area in areas:
                r, ot = self.matcher.dict_add(area, self.tags_NS, force=True)
                if not r:
                    print(f"nlp_ner_nt.load_ns area is repeat: {area} {ot}")

        def ns_tags(line):
            """根据地名进行行政级别查询,返回对应的标记"""
            if line[-2:] in {'林场', '农场', '牧场', '渔场', '管理区'}:
                return nt_parser_t.tags_NSNM
            lvl = cai.query_aera_level(line)
            return lvls[lvl]

        # 地名的构成很复杂.最简单的模式为'名字+省/市/区/县/乡',还有'主干+街道/社区/村/镇/屯',此时的主干组份的模式就很多,如'xx街/xx路/xx站/xx厂'等.

        def vals_cb(line):
            name, tag = nt_parser_t._split_label(line)  # 得到原始地名与对应的标注类型
            if tag == '':  # 不要求进行解析处理
                return [(name, ns_tags(name))]
            # 解析得到主干部分
            aname = cai.drop_area_tail(name, drops_tailchars)
            if name != aname and aname not in nnd.nt_tail_datas:
                if len(aname) <= 1:
                    print(f'<{fname}>:{line} split <{aname}>')
                if tag is None:  # 没有明确标注主干类型时
                    if aname[-1] in cai.ns_tails:
                        tag = nt_parser_t.tags_NS  # 如果主干部分的尾字符合地名尾缀特征,则按地名标注
                    else:
                        tag = nt_parser_t.tags_NN if len(aname) == 2 else nt_parser_t.tags_NS  # 否则根据主干部分的长度认定主干部分的类型,<=2的为名字N,>2的为地名S
                return [(name, ns_tags(name)), (aname, tag)]
            return [(name, nt_parser_t.tags_NS)]

        return self.__load(isend, fname, self.tags_NS, encode, vals_cb, self._chk_cb) if fname else ''

    def load_nz(self, fname, encode='utf-8', isend=True):
        """装载NZ组份词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, self.tags_NZ, encode, chk_cb=self._chk_cb)

    def load_nn(self, fname, encode='utf-8', isend=True):
        """装载NN尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, self.tags_NN, encode, chk_cb=self._chk_cb)

    def load_na(self, fname, encode='utf-8', isend=True):
        """装载NA尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, self.tags_NA, encode, chk_cb=self._chk_cb)

    def loads(self, dicts_list, path=None):
        """统一装载词典列表dicts_list=[('类型','路径')].返回值:空串正常,否则为错误信息."""
        rst = []
        for i, d in enumerate(dicts_list):
            isend = i == len(dicts_list) - 1
            fname = d[1] if path is None else os.path.join(path, d[1])
            if d[0] == 'NS':
                r = self.load_ns(fname, isend=isend)
            elif d[0] == 'NT':
                r = self.load_nt(fname, isend=isend)
            elif d[0] == 'NZ':
                r = self.load_nz(fname, isend=isend)
            elif d[0] == 'NN':
                r = self.load_nn(fname, isend=isend)
            elif d[0] == 'NA':
                r = self.load_na(fname, isend=isend)
            if r != '':
                rst.append(r)
        return ''.join(rst)

    @staticmethod
    def _merge_bracket(segs, txt):
        """合并segs段落列表中被左右括号包裹的部分,返回值:结果列表"""

        def _merge_brackets_segs(bi, ei, segs):
            """合并(bi,ei)分段以及其左右的括号,变为一个大分段"""
            segs[bi] = (segs[bi][0] - 1, segs[ei][1] + 1, segs[ei][2])  # 更新bi处的分段信息
            for i in range(ei - bi):  # 丢弃到ei的分段
                segs.pop(bi + 1)

        def _find_brackets_segs(b, e, segs):
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

        # 进行有深度感知的括号配对,得到每个层级的配对位置
        stack = []  # 记录当前深度待配对的信息
        result = []  # 记录完整的配对结果

        def can_push(char):
            """判断当前左括号是否可以push积累"""
            if char not in nt_parser_t.brackets_map:
                return False  # 不是左括号
            rchar = nt_parser_t.brackets_map[char]
            if char == rchar and stack:  # 左右括号是同一种字符的时候
                if stack[-1][1] == char:
                    return False  # 如果stack的最后已经存在当前字符,则不能push累积
            return True

        for pos in range(len(txt)):
            char = txt[pos]  # 对文本串进行逐一遍历
            if can_push(char):
                stack.append((pos, char))  # 如果遇到了左括号则记录到stack中
            elif char in nt_parser_t.brackets_rmap:
                pchar = nt_parser_t.brackets_rmap[char]
                if stack and stack[-1][1] == pchar:  # 如果遇到了右括号,并且真的与stack中最后的配对相吻合
                    result.append((stack[-1][0], pos))  # 则记录最内侧的括号范围
                    stack.pop(-1)  # 并剔除stack中已经用过的待配对信息
                else:
                    break  # 出现错层现象了,放弃当前配对分析

        if stack:  # 括号配对失败
            return stack  # 返回待配对层级信息list

        for res in result:
            bi, ei, ok = _find_brackets_segs(res[0], res[1], segs)
            if not ok:
                if bi is None and ei is None:
                    continue  # 规避'<新疆艺术(汉文)>杂志社'里面的'(汉文)'
                return res  # 括号范围内有未知成分,停止处理,返回tuple(b,e)
            _merge_brackets_segs(bi, ei, segs)  # 合并括号范围
        return None  # 正常完成

    @staticmethod
    def _drop_nesting(segs, txt):
        """丢弃segs段落列表中被完全包含嵌套的部分,返回值:结果列表"""
        rst = []

        def chk(rst, seg):
            """检查并处理当前段在已记录结果中的重叠情况.返回值:是否记录当前段"""
            while rst:
                last = rst[-1]
                r = mu.related_segs(last, seg)[0]
                if r in {'A@B', 'A=B'}:
                    if types.cmp(last[2], seg[2]) >= 0:
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
    def _drop_crossing(segs, bylvl=False):
        """丢弃segs段落列表中被交叉重叠的部分"""

        def chk_over(idx, ext=False):
            """检查segs中的idx段,是否被前后分段完全交叉重叠覆盖.返回值:
                None - idx分段未被覆盖
                0 - 丢弃idx
                1 - 丢弃idx+1
            """
            if idx < 1 or idx >= len(segs) - 1:
                return None  # 下标范围错误
            p = segs[idx - 1]  # 前段
            c = segs[idx]  # 中段
            n = segs[idx + 1]  # 后段
            if p[1] != n[0]:  # 前后段没有覆盖中段
                return None
            if ext and c[1] >= n[1]:
                return None  # 后段被中段包含
            if c[0] <= p[0] and c[1] >= n[1]:
                return None  # 中段覆盖前后段
            cn_cmp = types.cmp(c[2], n[2]) if bylvl else None  # 中段与后段的优先级关系
            if cn_cmp and cn_cmp > 0 and c[1] >= n[1]:
                return 1  # 需要判断优先级,并且中段包含后段,则丢弃后段
            return 0  # 否则丢弃中段

        # 以ABCD相邻交叉覆盖的情况为例
        i = 1
        while i < len(segs) - 1:
            A = segs[i - 1]  # 前段 A
            B = segs[i]  # 中段 B
            C = segs[i + 1]  # 后段 C

            m = chk_over(i)
            if m is None:
                if A[1] >= B[1] and (types.cmp(A[2], B[2]) >= 0 or types.joint(A[2], (types.NS,))):
                    segs.pop(i)  # A包含B且优先级较大,丢弃B
                else:
                    i += 1  # AC未覆盖B,跳过
                continue
            if m == 1:  # 计划丢弃C,直接处理
                segs.pop(i + 1)
            else:  # ABC计划丢弃B,则需向后再看
                m = chk_over(i + 1, True)  # 判断BCD需要丢弃谁
                if m == 0 and types.cmp(C[2], B[2]) < 0:  # 如果后面判定想丢弃C并且C的优先级较小,丢弃C
                    segs.pop(i + 1)
                else:
                    segs.pop(i)  # 否则丢弃B
            # i += 1

    @staticmethod
    def _merge_segs(segs, merge_types=True, combi=False):
        '''处理segs段落列表中交叉/包含/相同组份合并(merge_types)的情况,返回值:(结果列表,前后段关系列表)'''
        rst = []
        clst = []

        def can_combi_NM(pseg, seg):
            """判断特殊序列是否可以合并"""
            if types.joint(pseg[2], (types.NZ, types.NS)) and types.equ(seg[2], types.NM):
                if pseg[1] > seg[0] or (merge_types and mu.slen(seg) < 3):
                    return True  # 交叉(NZ,NS)&NM,或相连的NM较短,则强制合并前后段
            if pseg[2] is not None and types.equ(seg[2], types.NO):
                if pseg[1] == seg[0] and mu.slen(seg) == 1:
                    return True  # 紧邻NO,则强制合并前后段
                if pseg[1] > seg[0] and pseg[1] <= seg[1]:
                    return True  # 交叉NO,则强制合并前后段
            if pseg[1] == seg[0] and types.joint(pseg[2], (types.NU,)) and types.equ(seg[2], types.NB):
                return True  # 紧邻(NU,NM)+NB,则合并前后段
            return False

        def can_tags_merge(pseg, seg, idx):
            """基于当前分段索引idx和分段信息seg,以及前段信息pseg,判断二者是否应该进行类型合并"""
            type_eq = types.equ(pseg[2], seg[2])
            if type_eq and pseg[1] > seg[0]:
                return True  # 前后两个段是交叉的同类型分段,合并

            if not merge_types:
                return False  # 不要求类型合并

            if types.equ(pseg[2], seg[2]) and types.equ(types.NM, seg[2]) and pseg[1] == seg[0]:
                return False  # 前后相邻的NM不要合并

            # 允许分段相交合并的类型集合
            can_cross_types = {types.NS, types.NZ, types.NA, types.NF}
            if not type_eq:  # 前后段类型不一致时,需要额外判断
                if merge_types and can_cross_types.intersection(seg[2]) and can_cross_types.intersection(pseg[2]) and pseg[1] > seg[0] and mu.slen(seg) + mu.slen(pseg) <= 5:
                    return True  # 在要求合并的情况下,两个分段如果在许可的类型范围内且交叉,也合并
                return False  # 否则不合并

            if idx + 1 < len(segs):  # 当前段不是末尾,则向后看一下,进行额外判断
                nseg = segs[idx + 1]
                if types.equ(seg[2], nseg[2]):
                    return True  # 后段与当前段类型相同,告知可以合并
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
            if combi and can_combi_NM(pseg, seg):
                rst[-1] = (pseg[0], seg[1], seg[2])  # 后段合并前段
                return
            elif pseg[1] > seg[0]:
                if types.cmp(pseg[2], seg[2]) < 0:
                    rst[-1] = (pseg[0], seg[0], pseg[2])  # 后段重要,调整前段范围即可
                else:
                    seg = (pseg[1], seg[1], seg[2])  # 前段重要,调整后段范围
            rst.append(seg)  # 记录后段信息

        def rec_tags_cont(pseg, seg):
            """记录seg包含pseg的结果"""
            if types.cmp(pseg[2], seg[2]) < 0:
                rst[-1] = (pseg[0], seg[1], seg[2])  # 后段重要,替换前段范围
            else:
                rst[-1] = (pseg[0], seg[1], pseg[2])  # 前段重要,调整前段范围

        for idx, seg in enumerate(segs):
            if not rst:
                rst.append(seg)
                continue
            pseg = rst[-1]
            rl, cr = mu.related_segs(pseg, seg)
            clst.append((pseg, rl, seg, cr))  # 记录关联情况

            # 根据前后段的关系进行合并处理
            if rl == 'A&B':  # 前后相交,判断是否可以合并
                if can_tags_merge(pseg, seg, idx):
                    rec_tags_merge(pseg, seg)  # 合并当前段
                else:
                    rec_tags_cross(pseg, seg)  # 记录,前后交叉
            elif rl == 'A+B':  # 前后紧邻,需要判断是否应该合并
                if can_tags_merge(pseg, seg, idx):
                    rec_tags_merge(pseg, seg)  # 合并当前段
                else:
                    rec_tags_cross(pseg, seg)  # 记录,前后紧邻
            elif rl == 'A@B':  # 前段包含后段,需要记录NA@NO的情况
                if types.equ(seg[2], types.NM) or (types.equ(pseg[2], types.NA) and types.equ(seg[2], types.NO) and can_combi_NM(pseg, seg)):
                    rec_tags_cross(pseg, seg)  # 记录,前包含后
            elif rl == 'B@A':  # 后段包含前段
                if can_tags_merge(pseg, seg, idx):
                    rec_tags_merge(pseg, seg)  # 合并当前段
                else:
                    rec_tags_cont(pseg, seg)  # 记录,后包含前
            else:
                rst.append(seg)  # 其他情况,直接记录当前分段

        return rst, clst

    @staticmethod
    def _merge_nums(segs, nusegs):
        """将nusegs中的分段信息合并到segs中"""
        if not nusegs:
            return

        def rec(segs, oseg, pos, nseg):
            """oseg是原pos处的分段,nseg是pos处的新分段"""
            if oseg and oseg[0] <= nseg[0] and oseg[1] >= nseg[1]:
                return  # 当前数字分段处于目标分段的内部,放弃
            if pos:
                pseg = segs[pos - 1]
                if pseg[0] == nseg[0] and pseg[1] == nseg[1]:
                    return  # 当前数字分段与前一个分段完全重叠,放弃
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
                if pseg[1] > nseg[0]:
                    pos = i  # 在当前段之后插入
                    if pseg[0] != nseg[0] or pseg[1] > nseg[1]:
                        break

            if pos == len(segs) - 1 and pseg[0] <= nseg[0]:
                pos += 1  # 末尾处额外后移判断

            rec(segs, pseg, pos, nseg)

    @staticmethod
    def _adj_last_tag(segs, txt):
        """尝试校正最后出现的NA/NO"""
        if len(segs) < 2:
            return
        lseg = segs[-1]
        fseg = segs[-2]
        if types.equ(lseg[2], types.NO) and types.equ(fseg[2], types.NA) and lseg[1] == fseg[1] and lseg[0] > fseg[0]:
            # 直接合并NA/NO
            segs.pop(-1)
            lseg = segs[-1]
            segs[-1] = (lseg[0], lseg[1], nt_parser_t.tags_NO)
            return

        if not types.equ(segs[-1][2], types.NA):
            return
        while len(segs) >= 2:  # 先尝试删除最后边被重叠包含的NA
            if not types.equ(segs[-1][2], types.NA):
                break
            lseg = segs[-1]
            fseg = segs[-2]
            if fseg[0] < lseg[0] and lseg[1] <= fseg[1]:
                segs.pop(-1)
                continue
            break
        # 再进行最后NA/NO的校正
        lseg = segs[-1]
        lpos = lseg[1] - 1
        if not types.equ(lseg[2], types.NA) or not nnd.query_tail_data(txt[lpos]):
            return
        segs[-1] = (lseg[0], lseg[1], nt_parser_t.tags_NO)

    def split(self, txt, nulst=None, with_useg=False):
        '''在txt中拆分可能的组份段落
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            返回值:分段列表[(b,e,{types})]
        '''
        # 更宽松:两个分段相互包含时,不记录匹配结果的分段类型集合
        nrec_contain_types = {types.NZ, types.NF, types.NS}

        def cross_ex(rst, pos, node, root):
            """交叉保留,丢弃重叠包含的匹配"""

            def can_drop_old(n, o):
                """判断新分段n是否应该踢掉旧分段o"""
                if n[0] >= o[1]:
                    return False  # 新旧分段不相邻,不用踢掉旧分段
                if n[0] < o[0]:
                    return True  # 新分段与旧分段相交或包含,踢掉旧分段.
                if n[0] == o[0]:
                    if n[1] > o[1] and not types.equ(n[2], types.NM) and not types.equ(o[2], types.NM):
                        return True  # 如果两个分段都不是NM,且新分段长于旧分段,则踢掉旧分段
                    if types.joint(n[2], (types.NS, types.NZ)) or types.cmp(n[2], o[2]) > 0:
                        return True  # 新旧分段起点相同,新分段为NS或NZ,或新分段优先级更高,则踢掉旧分段
                if o[1] == n[0] + 1 and len(rst) >= 2 and types.equ(o[2], types.NM) and types.equ(n[2], types.NZ):
                    p = rst[-2]  # '洙河小学校园' => 小学NM/小学校NM/校园NZ,踢掉中间的分段
                    if n[0] == p[1] and types.equ(p[2], types.NM):
                        return True
                return False

            def can_rec(n, o):
                """判断新分段n和旧分段o的关系,决定是否记录新分段"""
                if o[0] <= n[0] and n[1] <= o[1]:
                    if types.cmp(n[2], o[2]) == 0:
                        return False  # 被包含的相同类型新分段,不记录
                    if nrec_contain_types.intersection(n[2]) and nrec_contain_types.intersection(o[2]):
                        return False  # 相包含的两个段是以上类别时,不记录
                return True

            def rec(node):
                """记录当前节点对应的匹配分段到结果列表"""
                if node == root:
                    return
                # 当前待记录的新匹配分段
                seg = pos - node.words, pos, node.end
                while rst and can_drop_old(seg, rst[-1]):
                    rst.pop(-1)  # 回溯,逐一踢掉旧结果
                if not rst or can_rec(seg, rst[-1]):
                    rst.append(seg)

            rec(node.first)
            if node.first != node.fail and node.fail.end:
                rec(node.fail)  # 尝试多记录一下可能有用的次级匹配结果,解决(佛山海关/山海关/海关)的问题

        def intercept_break(segs, txt):
            """截取segs中未匹配的前半部分(丢弃已知的后半部分).返回值:截止点,0代表完全匹配"""
            slen = len(txt)
            ep = slen  # 最后的结束点
            for i in range(len(segs) - 1, -1, -1):
                seg = segs[i]
                if seg[1] < ep:
                    break  # 当前分段的结束点小于最后的结束点
                ep = seg[0]

            stops = {'件', '河', '乡', '镇', '业', '学', '区'}
            c = 0
            while ep < slen and c <= 2:  # 再向后延伸一下下,涵盖所有的数字部分
                if re.findall(self.num_re, txt[ep]):
                    ep = min(ep + 1, slen)
                    c += 1
                elif txt[ep] not in stops:
                    if ep + 1 < slen and txt[ep + 1] in stops:
                        break
                    ep = min(ep + 1, slen)
                    c += 1
                else:
                    break
            return ep

        segs = self.matcher.do_check(txt, mode=cross_ex)  # 按词典进行完全匹配
        ep = intercept_break(segs, txt)
        if ep:
            nums = self.query_nu(txt[:ep], nulst)  # 进行数字序号匹配
            self._merge_nums(segs, nums)

        self._adj_last_tag(segs, txt)  # 尝试校正最后应该匹配的NO单字
        self._drop_crossing(segs, True)  # 删除接续交叉重叠
        nres = self._drop_nesting(segs, txt)  # 删除嵌套包含的部分
        self._drop_crossing(nres)  # 删除接续交叉重叠
        self._merge_bracket(nres, txt)  # 合并附加括号

        if with_useg:
            return mu.complete_segs(nres, len(txt), True)[0]
        else:
            return nres

    def parse(self, txt, merge=True, nulst=None, with_useg=False):
        '''在txt中解析可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            返回值:(分段列表[(b,e,{types})],分段关系列表[(pseg,rl,nseg,cr)])
        '''
        segs = self.split(txt, nulst)  # 先拆分得到可能的列表
        rlst, clst = self._merge_segs(segs, merge, True)  # 进行完整合并
        if with_useg:
            rlst = mu.complete_segs(rlst, len(txt), True)[0]  # 补全中间的空洞分段
        return rlst, clst

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

    def verify(self, name, segs=None, merge_types=False, rec_NL=False):
        """对name中出现的多重NT构成特征进行拆分并校验有效性,如附属机构/分支机构/工会
            segs - 可记录组份分段数据的列表.
            返回值:分隔点列表[(bpos,epos,types)]
                  返回的types只有NM与NB两种组份模式
        """
        cons, _ = self.parse(name, merge_types)
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
            if types.equ(seg[2], types.NM) and mu.slen(seg) >= 2 and not types.joint(seg[2], (types.NU,)):
                if is_brackets(seg):
                    txt = name[seg[0] + 1:seg[1] - 1]
                else:
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

            if is_brackets(seg) and types.equ(seg[2], types.NM):
                newr = (seg[0], seg[1], stype)  # 被括号嵌入的NT
            else:
                newr = (bpos, epos, stype)  # 正常的NT分段接续

            if outs and types.joint(seg[2], (types.NO, types.NM)):
                oldr = outs[-1]  # 处理特殊情况:火车站/火车站店,保留'火车站店',剔除'火车站'
                if oldr[0] == newr[0] and oldr[1] == newr[1] - 1:
                    outs.pop(-1)  # 后一段结果比前一段结果多一个字,则丢弃前段结果
            outs.append(newr)

        for i, seg in enumerate(segs):
            stype = seg[2]
            epos = seg[1]
            islast = i == len(segs) - 1
            if types.equ(stype, types.NM):
                rec(i, seg, bpos, epos, types.NM)  # 当前段是普通NT结尾
            elif types.equ(stype, types.NL):
                rec(i, seg, bpos, epos, types.NM)  # 当前段是NL结尾
                if rec_NL:  # 是否额外记录尾缀分段信息
                    outs.append((seg[0], seg[1], types.NL))
            elif types.equ(stype, types.NB):
                rec(i, seg, bpos, epos, types.NB)  # 当前段是分支NT结尾
            elif types.equ(stype, types.NO) and islast:
                # 当前段是单字NT结尾,需要判断特例
                pseg = segs[i - 1]
                if types.joint(pseg[2], (types.NM, types.NO, types.NA)) and mu.slen(seg) == 1:
                    if name[pseg[1] - 1] != name[seg[0]] or name[seg[0]] in {'店', '站'}:
                        rec(i, seg, bpos, epos, types.NM)  # `NM|NO` 不可以为'图书馆馆'/'经销处处',可以是'马店店'/'哈站站',可以作为NT机构
                elif mu.slen(seg) > 1 or pseg[2] is not None:
                    rec(i, seg, bpos, epos, types.NM)
        return outs

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
                chars.append(chr(types.NX[1]))
                ranges.append((offset + seg[0], offset + seg[1], types.NX[0]))
            else:
                for i in range(seg[0], seg[1]):
                    chars.append(txt[i])
                    ranges.append((offset + i, offset + i + 1, None))
        else:
            t = types.type(seg[2])
            chars.append(chr(t[1]))
            ranges.append((offset + seg[0], offset + seg[1], t[0]))
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
                t = types.NX.name
            else:
                t = line[useg[0]:useg[1]]
        else:
            t = types.type(useg[2]).name
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
            mres = mchk.parse(line, with_useg=True)[0]
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
