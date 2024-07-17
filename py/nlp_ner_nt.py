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


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需给出尽量准确的分词结果,而本解析器则尝试进行组合覆盖,给出覆盖后的分段特征结果.
    '''

    @staticmethod
    def __nu_rec(lst, mres, typ, offset=0):
        """记录数字匹配结果"""

        def rec(lst, seg):
            """记录匹配结果,规避多条规则的重复匹配分段,保留高优先级结果"""
            for i in range(len(lst)):
                rseg = lst[i]
                if rseg[0] == seg[0] and rseg[1] == seg[1]:
                    if types.cmp(rseg[2], seg[2]) < 0:
                        lst[i] = seg  # 先进行一圈查找,如果存在与新分段重叠的段,则保留高优先级的分段.
                    return
                if rseg[0] <= seg[0] and seg[1] <= rseg[1]:
                    return  # 存在长匹配,则丢弃当前短匹配
            if len(lst) >= 2:
                if lst[-2][1] == seg[0] and types.tags_NS.issubset(lst[-2][2]) and types.tags_NU.issubset(seg[2]):
                    lst.pop(-1)  # 前后是NS+NU,则丢弃中间段
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
    num_re = r'[×\.+○O\d甲乙丙丁戊己庚辛壬癸幺零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾佰百千仟万廿卅IⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]'
    # 数字序号组合模式
    num_rules = [
        (f'([铁农建第笫经纬新ABCDGKSXYZ]*{num_re}{{1,7}}[号级大支#]*)(公里|马路|社区|[道路弄街院里亩线楼栋段桥井闸门渠河沟江坝村区师机片]+)', types.tags_NS, __nu_rec.__func__),
        (f'([铁农建第笫新]*{num_re}{{1,7}}[号]?)([分]?部队|煤矿|[团校院馆局会库矿场])', types.tags_NM, __nu_rec.__func__),
        (f'([铁农建第笫]*{num_re}{{1,7}}[号]?)([分]?营部|工区|分号|[厂店台站园亭部处营连排厅社所船室坊])', types.tags_NB, __nu_rec.__func__),
        (f'([铁农建第笫大小老]*{num_re}{{0,7}}[号]?[分支大中小]?[组队])', types.tags_NB, __nu_rec.__func__),
        (f'([铁农建第笫东南西北]*{num_re}{{1,7}})([职中小高冶路街委米])(?![学])', types.tags_NS, __nu_rec.__func__),
        (f'([铁农建经纬山钢莲光山华司达大中小老江海安星煤宝金城]+{num_re}{{1,7}})', types.tags_NU, __nu_rec.__func__),
        (f'([东南西北]+{num_re}{{1,7}}|{num_re}{{1,7}}[东南西北新]+|[东南西北][分])', types.tags_NA, __nu_rec.__func__),
        (f'([第笫上下新ABCDGKSXYZ]*{num_re}{{1,7}}[號号级大支只届年期次个度批委天时分公度经纬家郎哥幼条代纺化种克针建轻橡棉邦水齿皮客#]?)', types.tags_NU, __nu_rec.__func__),
    ]

    # 为了更好的利用地名组份信息,更好的区分主干部分的类型,引入了"!尾缀标注"模式,规则如下:
    # 1 未标注!的行,整体地名(S)进行使用,并在移除尾缀词后,主干部分作为名称(N)使用,等同于标注了!N
    # 2 标注!的且没有字母的,不拆分,将整体作为:地名(S)
    # 3 标注!后有其他字母的,主干部分按标注类型使用: A-弱化名称/S-地名/M-实体/U-序号/N-名称/Z-专业名词/H-特殊词/B-分支
    tag_labels = {'A': types.tags_NA, 'S': types.tags_NS, 'M': types.tags_NM, 'U': types.tags_NU, 'O': types.tags_NO,
                  'N': types.tags_NN, 'Z': types.tags_NZ, 'H': types.tags_NH, 'B': types.tags_NB}

    # 可进行特殊短语包裹的括号对
    brackets_map = {'<': '>', '(': ')', '[': ']', '"': '"', "'": "'"}
    brackets_rmap = {'>': '<', ')': '(', ']': '[', '"': '"', "'": "'"}

    @staticmethod
    def query_nu(txt, nulst=None, offset=0):
        """查询txt中的数字相关特征模式,nulst可给出外部数字模式匹配列表.返回值:[b,e,{types}]"""
        rst = []
        if not nulst:
            nulst = nt_parser_t.num_rules
        for pat in nulst:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            pat[2](rst, mres, pat[1], offset)

        if not rst:
            return rst

        ret = sorted(rst, key=lambda x: x[0])
        return nt_parser_t._merge_segs(ret, False, False)[0]

    @staticmethod
    def rec_nums(segs, txt, nulst=None):
        """根据预匹配分段列表,尝试进行编号分段的补全.返回值:补充的分段数量"""
        chks = []

        def chk_num_segs(rsts):
            """检查记录可以进行数字匹配的分段"""
            nonlocal chks
            seg = rsts[-1]  # 当前段
            idx = len(rsts) - 1  # 当前段索引
            pseg = rsts[-2] if idx else None  # 前一段
            if pseg and seg[1] <= pseg[1]:
                return  # 如果当前段被前段包含则放弃
            seg_is_NA = seg[2] and types.tags_NA.issubset(seg[2])
            if not seg[2] or (mu.slen(seg) == 1 and txt[seg[0]] not in {'.'} and seg_is_NA):
                chks.append(idx)  # 如果当前是未知段或单字NA段,则记录
            elif mu.slen(seg) > 1 and txt[seg[1] - 1] in {'第', '铁', '农', '建'} and seg_is_NA:
                chks.append(idx)  # 如果当前是特定多字NA段,则记录

        usegs, uc = mu.complete_segs(segs, len(txt), True, cb=chk_num_segs)  # 得到补全的分段列表
        if not chks:
            return 0

        def skip_next(pos, uidx):
            """判断txt[pos]是否还需要向后扩展"""
            if txt[pos:pos + 2] in {'工区', '分号', '部队', '公里', '马路', '社区'}:
                return pos + 2
            if txt[pos:pos + 2] in {'营业', '营销', '营养', '营造', '营部', '矿业', '乡镇', '中学', '五金', '百货', '连锁', '冶金', '船舶', '高地'}:
                return pos
            if uidx + 1 < len(usegs):
                if mu.slen(usegs[uidx]) == 1 and txt[pos - 1] in {'第'}:
                    return pos + 1
                nseg = usegs[uidx + 1]
                if nseg[2]:
                    if nseg[2] & {types.NM, types.NZ, types.NB}:
                        return pos  # 后一段是特殊类型,不扩张

                    if nseg[1] - (pos + 1) == 1 and nseg[2] & {types.NS, types.NH, types.NN}:
                        lseg = usegs[uidx + 2] if uidx + 2 < len(usegs) else None
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

        num_chars2 = {'第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖', '拾', }
        num_chars3 = {'大', '农', '中'}
        num_chars3.update(num_chars2)

        def skip_prev(pos, uidx):
            """判断txt[pos]是否还需要向前扩展"""
            if uidx:
                pseg = usegs[uidx - 1]
                if pseg[2] is None:
                    return pos - 1
                if pseg[2] & {types.NM, types.NZ, types.NB, types.NF, types.NS}:
                    return pos
                if pseg[2] & {types.NN, types.NA}:
                    if uidx >= 2:
                        ppseg = usegs[uidx - 2]
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

            b = skip_prev(useg[0], uidx)  # 向前扩张
            e = skip_next(useg[1], uidx)  # 向后扩张
            nums = nt_parser_t.query_nu(txt[b:e], nulst, b)  # 进行数字序号匹配
            rst.extend(nums)

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

    def __load(self, isend, fname, tags, encode='utf-8', vals_cb=None, chk_cb=None):
        """装载词典文件fname并绑定数据标记tags,返回值:''正常,否则为错误信息."""
        if fname is None:
            return None

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

        return self.__load(isend, fname, types.tags_NM, encode, chk_cb=self._chk_cb) if fname else ''

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
        segs = line.strip().split('!')  # 尝试拆分标注记号
        lbl = segs[1] if len(segs) == 2 else None  # 得到标注字符
        if lbl and lbl not in nt_parser_t.tag_labels:
            print('ERROR:DICT LINE UNKNOWN LABEL CHAR!', line)
            lbl = ''
        name = segs[0]  # 得到原名称
        if lbl:
            lbl = nt_parser_t.tag_labels[lbl]  # 江标注字符转换为对应类型
        return name, lbl

    def load_ns(self, fname=None, encode='utf-8', isend=True, worlds=True, ns_lvl_limit=5, drops_tailchars=None, conv_fname='rule_ns_conv.txt'):
        """装载NS组份词典,worlds告知是否开启全球主要地区.返回值:''正常,否则为错误信息."""
        lvls = {0: types.tags_NS, 1: types.tags_NS1, 2: types.tags_NS2, 3: types.tags_NS3, 4: types.tags_NS4, 5: types.tags_NS5}

        def _load_convs():
            """装载内置地名的简称类型调整字典"""
            if not fname or not conv_fname:
                return {}
            rst = {}
            rfname = os.path.join(os.path.dirname(fname), conv_fname)
            with open(rfname, 'r', encoding='utf-8') as rf:
                for line in rf.readlines():
                    if not line or line[0] == '#':
                        continue
                    aname, typ = nt_parser_t._split_label(line)
                    rst[aname] = typ
            return rst

        def ns_tags(line):
            """根据地名进行行政级别查询,返回对应的类型标记"""
            if line[-2:] in {'林场', '农场', '牧场', '渔场', '水库'}:
                return types.tags_NSNM
            if line[-3:] in {'管理区'}:
                return types.tags_NSNM
            lvl = cai.query_aera_level(line)
            return lvls[lvl]

        # 装入内置的行政区划名称
        if len(self.matcher.do_loop(None, '牡丹江市')) != 4:
            aname_convs = _load_convs()
            for id in cai.map_id_areas:
                alst = cai.map_id_areas[id]
                lvl = cai.query_aera_level(alst[0])  # 根据正式地名得到行政区划级别
                if lvl > ns_lvl_limit:
                    continue  # 可进行层级限制,不装载低层级的区划名称.
                tags = lvls[lvl]
                for name in alst:
                    self.matcher.dict_add(name, ns_tags(name), force=True)  # 进行动态类型计算
                    aname = cai.drop_area_tail(name, drops_tailchars)
                    if name != aname and aname not in nnd.nt_tail_datas:
                        if aname in aname_convs:
                            tags = aname_convs[aname]  # 对内置地名的简称进行类型调整
                        self.matcher.dict_add(aname, tags, force=True)  # 特定尾缀地区名称,放入简称和初始类型

                cnames = cai.make_comb_parent_name(id)
                for name in cnames:
                    self.matcher.dict_add(name, lvls[lvl], force=True)  # 装入市区/市县的组合地名

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
                tags = types.tags_NS
                if state in aname_convs:
                    tags = aname_convs[state]  # 对state地名进行类型调整
                r, ot = self.matcher.dict_add(state, tags, force=True)
                if not r:
                    print(f"nlp_ner_nt.load_ns state is repeat: {state} {ot}")

                city = cai.map_worlds[state]
                if city:
                    tags = types.tags_NS1
                    if city in aname_convs:
                        tags = aname_convs[city]  # 对city地名进行类型调整
                    r, ot = self.matcher.dict_add(city, tags, force=True)
                    if not r:
                        print(f"nlp_ner_nt.load_ns city is repeat: {city} {ot}")

            areas = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚', '东南亚']
            for area in areas:
                r, ot = self.matcher.dict_add(area, types.tags_NN, force=True)
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
            aname = cai.drop_area_tail(name, drops_tailchars)
            if name == aname or aname in nnd.nt_tail_datas:
                return [(name, ns_tags(name))]

            if len(aname) <= 1:
                print(f'<{fname}>:{line} split <{aname}>')
            if tag is None:  # 没有明确标注主干类型时
                if aname[-1] in nt_parser_t.num_re:
                    tag = types.tags_NA  # 弱化类型
                else:
                    tag = nn_tags(aname)  # 根据主干部分决定类型
            return [(name, ns_tags(name)), (aname, tag)]

        return self.__load(isend, fname, types.tags_NS, encode, vals_cb, self._chk_cb) if fname else ''

    def load_nz(self, fname, encode='utf-8', isend=True):
        """装载NZ组份词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NZ, encode, chk_cb=self._chk_cb)

    def load_nn(self, fname, encode='utf-8', isend=True):
        """装载NN尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NN, encode, chk_cb=self._chk_cb)

    def load_na(self, fname, encode='utf-8', isend=True):
        """装载NA尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NA, encode, chk_cb=self._chk_cb)

    def loads(self, dicts_list, path=None, with_end=True):
        """统一装载词典列表dicts_list=[('类型','路径')].返回值:空串正常,否则为错误信息."""
        rst = []
        for i, d in enumerate(dicts_list):
            isend = (i == len(dicts_list) - 1) and with_end
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
                    # if types.cmp(last[2], seg[2]) >= 0:
                    #     return False  # 当前段被包含且优先级较低,不记录
                    # else:
                    #     return True
                    return False
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
                if A[1] >= B[1] and (types.tags_NS.issubset(A[2]) or types.cmp(A[2], B[2]) >= 0):
                    segs.pop(i)  # A包含B且优先级较大,丢弃B
                elif A[1] - B[0] == 1 and B[1] == C[0] and types.tags_NS.issubset(A[2]) and {types.NN, types.NA} & B[2] and {types.NN} & C[2]:
                    segs[i + 1] = (B[0], C[1], C[2])
                    segs.pop(i)  # NS&NN+NN,则合并NN
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

    @staticmethod
    def _adj_tags_NANO(segs, txt):
        """尝试校正最后出现的NA/NO"""

        def adj_NA(C, idx):
            B = segs[idx - 1] if idx > 0 else None  # 前一个分段
            D = segs[idx + 1] if idx + 1 < len(segs) else None  # 后一个分段
            E = segs[idx + 2] if idx + 2 < len(segs) else None  # 后两个分段

            if idx > 0 and idx + 1 < len(segs):
                if E and mu.slen(C) >= 3 and C[1] == E[0] and E[2] & {types.NM, types.NZ}:
                    if D[0] < C[1] and D[1] > E[0]:
                        if D[0] == C[0] and D[1] > C[1]:
                            segs.pop(idx)  # C+E但D@C则丢弃C
                            return 0
                        else:
                            segs.pop(idx + 1)  # C+E则丢弃D
                            return 1

                if B[1] == D[0] and mu.slen(C) > 1 and C[0] < B[1] and D[0] < C[1]:
                    # C是NA分段,且被B/D前后夹击
                    cans = {types.NS, types.NZ, types.NN, types.NO, }
                    if B[2] & cans and D[2] & cans:
                        if types.tags_NO.issubset(D[2]):  # D是NO,则合并BD
                            if txt[C[1] - 2:C[1]] in {'省城', '市城', '县城'}:
                                segs[idx - 1] = (B[0], D[1], B[2])
                            else:
                                segs[idx - 1] = (B[0], D[1], D[2])
                            segs.pop(idx)  # 丢弃C
                            segs.pop(idx)  # 丢弃D
                            return 1
                        else:  # D不是NO
                            segs.pop(idx)  # 则丢弃C
                            return 0
                    else:
                        segs.pop(idx)  # 则丢弃C
                        return 0

            # 较短的分段列表特殊处理,C包含D,且D是NO
            if D and C[0] < D[0] and C[1] == D[1] and types.tags_NO.issubset(D[2]):
                # TODO 需要判断E是否为NM,再决定是否合并CD
                if not E or {types.NM, types.NO, types.NB}.isdisjoint(E[2]):
                    segs[idx] = (C[0], D[1], D[2])  # 合并C@D
                segs.pop(idx + 1)  # 丢弃D
                return 1

            if D and D[2] & {types.NM, types.NB, types.NO}:
                return 1  # 当前NA分段后面是特征尾缀,跳过

            # 当前NA分段尾字是NO,直接校正
            st = txt[C[0]:C[1]]
            sd = nnd.query_tail_data(st[-1])
            if sd and types.tags_NO.issubset(sd['.']) and st[-2:] not in {'县城'}:
                segs[idx] = (C[0], C[1], types.tags_NO)

            return 1

        idx = 0
        while idx < len(segs):
            C = segs[idx]  # 当前分段
            if types.tags_NA.issubset(C[2]):
                idx += adj_NA(C, idx)
            else:
                idx += 1

    @staticmethod
    def _drop_crossing_typs(segs):
        """以typs类型的分段为中心,尝试丢弃与之交叉重叠的部分"""

        def is_trunk(seg, idx, can_ns=3):
            """判断idx处的分段seg可否成为定位主干"""
            if types.NZ in seg[2] or (mu.slen(seg) >= can_ns and types.NS in seg[2]):
                pseg = segs[idx - 1] if idx else (seg[0], seg[0], None)
                nseg = segs[idx + 1] if idx < len(segs) - 1 else (seg[1], seg[1], None)
                return pseg[1] < nseg[0]  # 当前分段没有被前后分段覆盖,则可以作为定位主干

            if idx and idx < len(segs) - 1:  # 当前不是首尾处的分段
                pseg = segs[idx - 1]
                nseg = segs[idx + 1]

                if types.tags_NM.issubset(seg[2]):  # '|馨|美发屋|'=>'|馨美|发屋|'
                    if types.tags_NM.issubset(nseg[2]):
                        if pseg[1] == nseg[0] and pseg[0] < seg[0] < pseg[1]:
                            if idx >= 2 and segs[idx - 2][1] == seg[0]:
                                return True
                            if types.tags_NA.issubset(pseg[2]):
                                return True
                            return False  # 当前NM段与前一段交叉,但后一段NM是与其接续的,则当前段不作为主干

                len_seg = mu.slen(seg)
                if len_seg >= can_ns:
                    len_pseg = mu.slen(pseg)
                    len_nseg = mu.slen(nseg)
                    if len_seg >= len_pseg and len_seg >= len_nseg:
                        return True  # 当前段是前后三段中最长的

            if seg[2] & {types.NM, types.NB, types.NL}:
                return True  # 当前分段是尾缀特征分段,可以作为定位主干

            return False

        def chk_drop(idx):

            def can_drop(idx, bp, ep, isleft):
                """判断是否可以丢弃idx处的分段,避免出现空洞"""
                for i in range(idx - 1, -1, -1):
                    if segs[i][1] == segs[idx][0] and {types.NS, types.NZ, types.NM, types.NB} & segs[i][2]:
                        return False  # 待丢弃的分段前面存在与之相连的重要分段,则不要丢弃

                if isleft:
                    for i in range(idx - 1, -1, -1):
                        pseg = segs[i]
                        if pseg[0] <= bp and ep <= pseg[1]:
                            return True
                        if pseg[1] < bp:
                            break
                return False

            C = segs[idx]  # 中段 C
            if idx < len(segs) - 2:
                D = segs[idx + 1]  # 后段 D
                E = segs[idx + 2]  # 后段 E
                if E[0] == C[1] and C[0] < D[0] and D[1] <= E[1]:  # CE相连
                    if (C[2] & D[2]) & types.tags_NZ:
                        return 1  # CD相交且为NZ,则暂不处理
                    if D[0] == C[1] and idx + 3 < len(segs):
                        F = segs[idx + 3]  # 后段 F
                        if D[1] == F[0] and F[1] > E[1] and (D[2] & E[2]) and types.tags_NA.isdisjoint(F[2]) and {types.NM, types.NB, types.NS} & C[2]:
                            segs.pop(idx + 2)  # F紧邻D且与E相交,D和E类型相同,干掉E
                            return 1  # 为了得到这样的结果 => M:公司|S:南宁|N:市政|B:分公司
                    segs.pop(idx + 1)  # 干掉D
                    return 0
            elif idx < len(segs) - 1 and idx:
                B = segs[idx - 1]  # 前段 B
                D = segs[idx + 1]  # 后段 D
                if C[0] <= D[0] and D[1] <= C[1] and (D[2] & C[2]) and B[1] >= C[0] and types.tags_NA.issubset(B[2]):
                    segs.pop(idx + 1)  # 中预|预制厂|制厂 =>丢弃'制厂'
                    return 0

            if idx >= 2:
                A = segs[idx - 2]  # 前段 A
                B = segs[idx - 1]  # 前段 B
                if A[1] == C[0] and A[0] < B[0] and B[1] <= C[1]:
                    segs.pop(idx - 1)  # AC相连,干掉B
                    return -1
                if B[1] == C[0] and B[0] < A[1] < C[0]:  # BC相连,AB相交
                    if can_drop(idx - 2, A[0], B[0], True):
                        segs.pop(idx - 2)  # 干掉A
                        return -1
            return 1

        # 以ABCDE相邻交叉覆盖的情况为例
        i = 0
        while i < len(segs):
            i += chk_drop(i) if is_trunk(segs[i], i, 3) else 1

    @staticmethod
    def _merge_segs(segs, merge_types=True, combi=False, comboc_txt=None):
        '''处理segs段落列表中交叉/包含/相同组份合并(merge_types)的情况,返回值:(结果列表,前后段关系列表)'''
        rst = []
        clst = []
        if not segs:
            return rst, clst

        def can_combi_NM(pseg, seg):
            """判断特殊序列是否可以合并"""
            if pseg[2] & {types.NZ, types.NS} and types.equ(seg[2], types.tags_NM):
                if merge_types and mu.slen(pseg) <= 6 and mu.slen(seg) < 3:
                    return True  # 要求合并,且前后段比较短,可以合并
                if pseg[1] > seg[0] and seg[1] - pseg[0] < 10:
                    return True  # 交叉(NZ,NS)&NM,且前后段比较短,可以合并
            if types.equ(seg[2], types.tags_NO):
                if pseg[1] == seg[0] and mu.slen(seg) == 1:
                    return True  # 紧邻NO,则强制合并前后段
                if pseg[1] > seg[0] and pseg[1] <= seg[1]:
                    return True  # 交叉NO,则强制合并前后段
            if pseg[1] == seg[0] and types.tags_NU.issubset(pseg[2]) and types.equ(seg[2], types.tags_NB):
                return True  # 紧邻(NU,NM)+NB,则合并前后段
            return False

        def can_tags_merge(pseg, seg, idx):
            """基于当前分段索引idx和分段信息seg,以及前段信息pseg,判断二者是否应该进行类型合并"""
            type_eq = types.equ(pseg[2], seg[2])
            if type_eq:
                if pseg[1] > seg[0]:
                    return True  # 前后两个段是交叉的同类型分段,合并
                if mu.slen(pseg) == 1 and pseg[1] == seg[0] and pseg[2] & {types.NN, types.NA}:
                    return True  # 类型相同的前后段,

            if comboc_txt and mu.slen(pseg) == 1 and pseg[1] == seg[0] and seg[2] & {types.NN, types.NA} and comboc_txt[pseg[0]] in {'新'}:
                return True  # 前面单字相连的前后段,且类型允许则合并

            if not merge_types:
                return False  # 不要求类型合并

            if pseg[1] == seg[0] and types.equ(pseg[2], seg[2]) and types.tags_NMNB & seg[2]:
                return False  # 前后相邻的NM/NB不要合并

            # 允许分段相交合并的类型集合
            can_cross_typesSZF = {types.NS, types.NZ, types.NF}
            can_cross_typesANH = {types.NA, types.NN, types.NH}
            if not type_eq:  # 前后段类型不一致时,需要额外判断
                if pseg[1] > seg[0]:
                    if mu.slen(seg) + mu.slen(pseg) <= 5 and can_cross_typesSZF & seg[2] and can_cross_typesSZF & pseg[2]:
                        return True  # 在要求合并的情况下,两个分段如果在许可的类型范围内且交叉,也合并
                    if comboc_txt and seg[1] - pseg[0] <= 5 and seg[0] - pseg[0] == 1:
                        if (types.tags_NN.issubset(pseg[2]) and types.tags_NZ.issubset(seg[2])) or (types.tags_NA.issubset(pseg[2]) and types.tags_NN.issubset(seg[2])):
                            # NN&NZ相交,且切分后剩余单字
                            if idx >= 2 and mu.slen(segs[idx - 1]) == 1:
                                return False  # 再前面仍然是单字,则这里不合并
                            nums = re.findall(nt_parser_t.num_re, comboc_txt[pseg[0]])
                            if not nums:
                                return True  # NN&NZ相交,且切分后剩余非数字单字,则进行合并
                        if pseg[2] & can_cross_typesANH and seg[2] & can_cross_typesANH:
                            return True
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
            chars_NONS = {'矿', '店', '局'}  # 需要进行NO/NS转换的单字

            def adj_typ_NO(b, e, typ_nhit):
                """根据给定的分段范围与默认类型,进行特定分段类型的校正"""
                if not comboc_txt:
                    return typ_nhit
                w = comboc_txt[b:e]
                if w in chars_NONS:
                    return types.tags_NO
                else:
                    return nnd.nt_tail_datas.get(w, typ_nhit)

            if types.NX not in seg[2]:
                if combi and can_combi_NM(pseg, seg):
                    rst[-1] = (pseg[0], seg[1], seg[2])  # 后段吞并前段
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
                        if types.tags_NU.issubset(seg[2]):
                            seg = (pseg[1], seg[1], seg[2])  # &NU则切除相交部分
                            needadj = False

                    if needadj:
                        if types.cmp(pseg[2], seg[2]) < 0:
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
                areas_chars = {'路', '街', '道', '巷', '前', '后', '旁', '外', '内', '东', '西', '南', '北', '组', '港', '站',
                               '东路', '西路', '南路', '北路', '门前', '居', '办', '县', '乡', '镇', '村', '屯', '区', }
                if mu.slen(p2seg) > 1 and comboc_txt[p1seg[0]:p1seg[1]] in areas_chars:  # 合并'|南京|路|'
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
                    elif {types.NN, types.NS, types.NZ} & p2seg[2] and {types.NM, types.NB, types.NO} & p1seg[2]:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # NN&NM,后段吞并前段
                        rst.pop(-1)
                    elif comboc_txt[p2seg[0]] in {'新', '老', '小', '省', '市', '州', '中', '盟'} and {types.NM, types.NB, types.NO} & p1seg[2]:
                        if {types.NM, types.NB, types.NO} & seg[2]:
                            rst[-2] = (p2seg[0], p1seg[1], p2seg[2])  # NN&NM,后段吞并前段
                            rst.pop(-1)
                        else:
                            rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # NN&NM,后段吞并前段
                            rst.pop(-1)
                    elif types.tags_NA.issubset(p2seg[2]) and {types.NB, types.NO} & p1seg[2]:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # NA&NB,后段吞并前段
                        rst.pop(-1)
                    elif mu.slen(p1seg) % 2 == 1 and p2seg[2] & {types.NN, } and p1seg[2] & {types.NZ}:
                        rst[-2] = (p2seg[0], p1seg[1], p2seg[2])  # 合并: NN单字+NZ奇数
                        rst.pop(-1)
                elif mu.slen(p1seg) == 1 and p1seg[1] == seg[0]:
                    if comboc_txt[p1seg[0]] not in {'和', '驻', '至'} and types.tags_NS.issubset(seg[2]):
                        rst[-1] = (p1seg[0], seg[1], seg[2])  # OC+NS合并为NS
                        return  # 不再重复记录当前分段
                    city_tails = {'县城', '市直', '州直', '市立', '市中', '县立', '区立', '村级', '村庄', '区直', '镇直', '局直', '城中', '镇关', '镇中', '乡野', '村民', '市属'}
                    if (p2seg[2] & p1seg[2]) and p1seg[2] & {types.NN, types.NZ, types.NS}:
                        rst[-2] = (p2seg[0], p1seg[1], p1seg[2])  # 合并相同类型的前后段
                        rst.pop(-1)
                    elif types.NO in p1seg[2] and p2seg[2] & {types.NN, types.NZ, types.NS}:
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
                    rst.append(seg)
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
                if oseg[0] <= nseg[0] and nseg[1] <= oseg[1]:
                    return  # 当前数字分段处于目标分段的内部或重叠,放弃
                if pos + 1 < len(segs):
                    fseg = segs[pos + 1]
                    if oseg[1] == fseg[0] and oseg[0] <= nseg[0] and nseg[1] <= fseg[1]:
                        return  # 当前数字分段处于前后紧邻的两个分段内部,放弃
            if pos:
                pseg = segs[pos - 1]
                if pseg[0] <= nseg[0] and nseg[1] <= pseg[1]:
                    return  # 当前数字分段与前一个分段重叠,放弃

            if pos + 1 < len(segs):
                fseg = segs[pos + 1]
                if fseg[0] <= nseg[0] and nseg[1] <= fseg[1]:
                    return  # 当前数字分段与后一个分段重叠,放弃

            if segs and mu.slen(nseg) == 1 and types.tags_NB.issubset(nseg[2]):
                segs[pos - 1] = (segs[pos - 1][0], nseg[1], nseg[2])  # 单字NB则直接与前面合并
            else:
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
                    if pseg[0] > nseg[0] or pseg[1] > nseg[1]:
                        break

            if pos == len(segs) - 1 and pseg and pseg[0] <= nseg[0]:
                pos += 1  # 末尾处额外后移判断

            rec(segs, pseg, pos, nseg)

    def split(self, txt, nulst=None, with_useg=False, mres=None):
        '''在txt中拆分可能的组份段落
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            mres - 可为list,用于记录所有匹配命中的分段内容
            返回值:分段列表[(b,e,{types})]
        '''
        # 更宽松:两个分段相互包含时,不记录匹配结果的分段类型集合
        nrec_contain_types = {types.NZ, types.NF, types.NS}

        def chk_prorsad(rst, seg):
            """检查rst分段列表中是否存在与seg接续的前向分段"""
            for pseg in reversed(rst):
                if pseg[1] == seg[0]:
                    return True
                elif pseg[1] < seg[0]:
                    return False
            return False

        def cross_ex(rst, pos, node, root):
            """交叉保留,丢弃重叠包含的匹配"""

            def can_drop(o, n):
                """判断新分段n是否应该踢掉旧分段o"""
                if n[0] >= o[1]:
                    return False  # 新旧分段不相邻,不用踢掉旧分段
                if n[0] < o[0]:
                    return True  # 新分段与旧分段相交或包含,踢掉旧分段.
                if n[0] == o[0]:  # 前后段起点相同
                    lo = mu.slen(o)
                    if lo == 1:  # 旧段是单字的,丢弃旧段
                        return True
                    ln = mu.slen(n)
                    if ln - lo >= 2:  # 新段比旧段多两个字的,丢弃旧段
                        return True
                    if types.tags_NZ.issubset(o[2]) and types.tags_NM.issubset(n[2]):
                        return True  # '美食|美食屋'=>NZ&NM,丢弃NZ
                    if types.tags_NM.issubset(o[2]) and types.tags_NZ.issubset(n[2]):
                        return True  # '农业科|农业科技'=>NM&NZ,丢弃NM

                if o[1] - n[0] >= 2 and 3 >= n[0] - o[0] >= 2 and n[1] > o[1] and types.tags_NS.issubset(o[2]) and {types.NN, types.NA} & n[2]:
                    rst[-1] = (o[0], n[0], o[2])  # NS&NA长相交且剩余多字,则进行切分
                    if len(rst) >= 2 and mu.slen(rst[-2]) > mu.slen(rst[-1]) and rst[-2][0] == rst[-1][0]:
                        rst.pop(-2)  # o分段缩短后,如果存在被涵盖的p段,则丢弃p
                    return False

                if len(rst) >= 3:
                    f = rst[-3]
                    p = rst[-2]
                    if f[1] == n[0]:
                        if o[0] == n[0] and n[1] > o[1] and p[0] < f[1] and p[1] < o[1]:
                            if types.tags_NS.issubset(f[2]) and types.tags_NN.issubset(n[2]):
                                rst.pop(-2)  # 常德:S|德鑫|鑫创|鑫创意:N =>干掉中间的两个
                                return True
                        if mu.slen(f) >= 3 and mu.slen(n) >= 3:
                            rst.pop(-2)  # 遇到前后相连的两个长分段,踢掉中间的两个相交分段
                            return True
                        if types.tags_NS.issubset(f[2]) and types.tags_NZ.issubset(n[2]):
                            rst.pop(-2)  # NS+NZ,踢掉中间的两个相交分段
                            return True

                if len(rst) >= 2:
                    p = rst[-2]
                    if o[1] == n[0] + 1 and types.tags_NM.issubset(o[2]) and types.tags_NZ.issubset(n[2]):
                        # '洙河小学校园' => p:小学NM/o:小学校NM/n:校园NZ,踢掉中间的分段
                        if n[0] == p[1] and types.equ(p[2], types.tags_NM):
                            return True
                    if o[1] == n[0] and types.tags_NA.issubset(o[2]):
                        # 'p:学校NM/o:校西NA/n:西餐NZ',踢掉中间的NA分段
                        if p[1] > o[0] and types.tags_NM.issubset(p[2]):
                            return True
                    if p[1] == n[0] and o[0] - p[0] >= 2 and n[1] - o[1] >= 2:
                        return True  # 前p后n长段夹着一个小段o,则丢弃小段
                    if p[1] == n[0] and o[0] > p[0] and o[1] < n[1]:  # p+n,o在中间
                        if mu.slen(n) >= 3 and {types.NZ, types.NM, types.NB, types.NN} & n[2] and types.tags_NM.isdisjoint(o[2]):
                            return True  # n是较长分段,踢掉o
                        if mu.slen(p) >= 3 and types.tags_NS.issubset(p[2]) and types.tags_NM.isdisjoint(o[2]):
                            if p[1] - o[0] >= 2 and types.tags_NS.issubset(o[2]):
                                rst[-2] = (p[0], o[1], p[2])  # 重叠多字的NS,直接合并
                            return True  # p是较长NS分段,踢掉o
                        if p[2] & {types.NM, types.NZ, types.NS} and types.tags_NA.issubset(o[2]):
                            return True  # NS&NA NS+n,踢掉NA
                        if {types.NZ, types.NS} & p[2] and {types.NZ, types.NS} & n[2]:
                            return True  # NS&o NS+NZ,踢掉o

                return False

            def can_rec(o, n):
                """判断新分段n和旧分段o的关系,决定是否记录新分段"""
                if o[0] <= n[0] and n[1] <= o[1]:  # 新段n被旧段o包含时,判断新段是否可以被记录
                    if n[2] & o[2]:
                        if types.tags_NM.issubset(n[2]):  # 前后两段都是NM的时候
                            if mu.slen(n) >= 3 and n[0] - o[0] == 1:
                                return True  # 如果新段够长则保留
                            if len(rst) >= 2 and rst[-2][1] == n[0]:
                                return True  # 如果新段存在前面的接续段,也保留
                        return False  # 其他情况,新段被包含,且与旧段类型相同,不记录
                    if mu.slen(n) == 1 and n[1] == o[1] and types.tags_NA.issubset(n[2]):
                        if txt[n[0]:n[1]] in {'省', '市', '区', '县', '村', '镇', '乡', '州', '旗', '报'}:
                            return False  # 不用重复记录特定尾字
                        if o[2] & {types.NM, types.NB, types.NO}:
                            return False
                    if nrec_contain_types & n[2] and nrec_contain_types & o[2]:
                        return False  # 相包含的两个段是以上类别时,不记录
                    if n[0] - o[0] >= 2 or o[1] - n[1] >= 2 or (mu.slen(n) == 1 and {types.NA, types.NZ} & n[2]):
                        return False  # 长段包含特定短段,不记录
                    if mu.slen(o) >= 4 and n[2] & {types.NA, types.NN}:
                        return False  # 长分段包含短NA,不记录
                    if len(rst) >= 2:
                        p = rst[-2]  # p,o,n三段顺序排列
                        if p[0] >= o[0] and n[1] <= o[1] and p[1] > n[0]:
                            if types.tags_NA.issubset(o[2]) and {types.NM, types.NB} & n[2]:
                                rst.pop(-1)  # NA涵盖了NM的时候丢弃前段
                                return True
                            return False  # "五指|五指山|指山"这样的情况,丢弃后分段
                    if types.tags_NM.issubset(o[2]) and n[2] & {types.NO, types.NA, types.NB}:
                        return False  # NM@NO,放弃NO
                    if types.tags_NB.issubset(o[2]) and n[2] & {types.NO, types.NM, types.NB}:
                        return False  # NB@NM,放弃NM
                    if mu.slen(n) >= 2 and types.tags_NA.issubset(o[2]) and n[2] & {types.NO, types.NM, types.NB}:
                        rst[-1] = (o[0], o[1], n[2])  # NA包含NM,则调整NA的类别,放弃NM
                        return False
                    if not chk_prorsad(rst, n):
                        return False  # n被o包含且没有与之接续的前段,则不记录

                if len(rst) >= 2:
                    p = rst[-2]
                    if p[0] == n[0] and n[1] - p[1] >= 2:
                        rst.pop(-2)  # 新段n与前段p起点相同但更长,则丢弃前段
                    elif p[0] == o[0] and p[1] < o[1] and o[1] == n[0]:
                        rst.pop(-2)  # 前段p与旧段o起点相同且更短,新段n接壤旧段o,则丢弃前段p

                if n[0] - o[0] == 1 and n[1] - o[1] == 1 and types.tags_NS & o[2] and {types.NS, types.NH} & n[2]:
                    if chk_prorsad(rst, n) or txt[o[1]] in {'乡', '村', '镇'}:
                        return True  # 前方有接续的分段,则记录
                    return False  # 天津市&津市市,不记录
                return True

            def rec(node):
                """记录当前节点对应的匹配分段到结果列表"""
                if node is root:
                    return
                # 当前待记录的新匹配分段
                seg = pos - node.words, pos, node.end
                while rst and can_drop(rst[-1], seg):
                    rst.pop(-1)  # 回溯,逐一踢掉旧结果
                if not rst or can_rec(rst[-1], seg):
                    rst.append(seg)

            rec(node.first)
            if node.fail and node.fail.end:
                if node.first != node.fail:
                    rec(node.fail)  # 尝试多记录一下可能有用的次级匹配结果,解决(佛山海关/山海关/海关)的问题
                # else:
                #     node = node.fail  # 尝试再次深入一层记录匹配结果
                #     if node.first != node.fail and node.fail.end:
                #         rec(node.fail)  # 中山路=> 中山|山路|路,用于记录最后的'路'

        segs = self.matcher.do_check(txt, mode=cross_ex)  # 按词典进行完全匹配
        if mres is not None:
            mres.extend(segs)

        self._adj_tags_NANO(segs, txt)  # 校正NO单字
        self._drop_crossing_typs(segs)  # 基于NM分段删除左右交叉重叠的部分
        self.rec_nums(segs, txt, nulst)  # 进行未知分段的数字序号补全

        nres = self._drop_nesting(segs, txt)  # 删除嵌套包含的部分
        self._drop_crossing(nres)  # 删除接续交叉重叠
        self._merge_bracket(nres, txt)  # 合并附加括号

        if with_useg:
            return mu.complete_segs(nres, len(txt), True)[0]
        else:
            return nres

    def parse(self, txt, merge=True, nulst=None, with_useg=False, comboc=True, mres=None):
        '''在txt中解析可能的组份段落
            merge - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            comboc - 是否合并已知的单字
            返回值:(分段列表[(b,e,{types})],分段关系列表[(pseg,rl,nseg,cr)])
        '''
        segs = self.split(txt, nulst, mres=mres)  # 先拆分得到可能的列表
        rlst, clst = nt_parser_t._merge_segs(segs, merge, True, txt if comboc else None)  # 进行完整合并
        if with_useg:
            rlst = mu.complete_segs(rlst, len(txt), True)[0]  # 补全中间的空洞分段

        if merge:
            i = 0
            while i < len(rlst):
                seg = rlst[i]
                if mu.slen(seg) == 1 or not seg[2] or seg[2].isdisjoint({types.NA, types.NH, types.NN}):
                    i += 1
                    continue
                pseg = rlst[i - 1]
                if i > 0 and pseg[2] and types.tags_NN.issubset(pseg[2]):
                    rlst[i - 1] = (pseg[0], seg[1], types.tags_NN)
                    rlst.pop(i)
                else:
                    rlst[i] = (seg[0], seg[1], types.tags_NN)
                    i += 1

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

    def verify(self, name, segs=None, merge_types=False, rec_NL=False, comboc=True, mres=None):
        """对name中出现的多重NT构成特征进行拆分并校验有效性,如附属机构/分支机构/工会
            segs - 可记录组份分段数据的列表.
            返回值:分段列表[(bpos,epos,types)]
                  返回的types只有NM与NB两种组份模式
        """
        cons, _ = self.parse(name, merge_types, comboc=comboc, mres=mres)
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

            if is_brackets(seg) and types.tags_NL.isdisjoint(seg[2]) and types.equ(seg[2], types.tags_NM):
                newr = (seg[0], seg[1], stype)  # 被括号嵌入的NT
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
            islast = i == len(segs) - 1
            if stype is None:
                continue
            if stype & types.tags_NLNM:  # NT/NL/NTNL
                rec(i, seg, bpos, epos, types.NM)
                if rec_NL and types.tags_NL.issubset(stype):  # 在校验输出列表中,是否额外记录尾缀分段信息
                    outs.append((seg[0], seg[1], types.NL))
            elif types.equ(stype, types.NB):
                rec(i, seg, bpos, epos, types.NB)  # 当前段是分支NT结尾
            elif types.equ(stype, types.NO) and islast:
                # 当前段是单字NT结尾,需要判断特例
                pseg = segs[i - 1]
                if mu.slen(seg) == 1 and pseg[2] and pseg[2] & {types.NM, types.NO, types.NA}:
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
