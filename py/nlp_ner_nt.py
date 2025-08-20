'''
    NT组份解析器:进行NER/NT构成组份的分析,并可基于构成组份进行NT校验.
    1 提供NT组分解析功能,可用构建组份词典
    2 基于NT组份词典,提供NT名称校验功能
    3 基于NT组份词典,提供NT名称补全功能
'''
import re
import os

import util_base as ub
import uni_blocks as uni
import match_ac as mac
import match_util as mu
import china_area_id as cai
import nlp_ner_data as nnd
import nlp_ner_path as nnp
from nlp_ner_data import types


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需给出尽量准确的分词结果,而本解析器则尝试进行组合覆盖,给出覆盖后的分段特征结果.
    '''

    @staticmethod
    def __nu_rec(lst, mres, typ, offset=0):
        """记录数字匹配结果"""

        def _rec(lst, pos, seg, append):
            if not append:
                pseg = lst[pos]
                if pseg[0] == seg[0] and pseg[1] == seg[1]:
                    return False
            else:
                pseg = lst[pos - 1] if pos and lst else None

            if pseg and pseg[0] == seg[0] and pseg[2] & seg[2] & types.tags_NU:
                if pseg[1] < seg[1]:
                    lst.pop(pos if not append else pos - 1)
                    pos -= 1
                elif seg[1] < pseg[1]:
                    return False
            lst.insert(pos, seg)
            return True

        rc = 0
        for m in mres:
            rge = m.span()
            seg = (rge[0] + offset, rge[1] + offset, typ)
            pos = mu.insert_pos(lst, seg)
            if _rec(lst, pos, seg, pos == len(lst)):
                rc += 1
        return rc

    # 数字序号组合模式
    num_rules = [(f'([第笫苐新老大小东西南北省市区县村镇乡附]?[\\.{nnp.num_re}]{{1,7}}[#号户轮块度角毛分秒吨届座级期船至元克机天年℃]?)', types.tags_NU, __nu_rec.__func__),
                 (f'([第笫苐新老大小东西南北]?[{nnp.num_re}]{{1,7}}[#号级大支]*)(公里|经路|纬路|经街|纬街|马路|路段|社区|组村|队组|组组|职高|职中|[职委米条轮船道路弄街口里亩线层楼栋幢段桥井闸渠河沟江坝村区片门台房田居营连排])',
                  types.tags_NS, __nu_rec.__func__),
                 (f'([第笫苐新老大小东西南北]*[{nnp.num_re}]{{1,7}}[号]?)(营部|院区|柜组|部队|煤矿|船队|茶楼|[团校院馆局会矿场社所部处坊店园摊厂铺站园亭厅仓库])', types.tags_NO, __nu_rec.__func__),
                 (f'([第笫苐新老大小东西南北]*[{nnp.num_re}]{{1,7}})(工区|分号|仓库|支部|[分][团校院馆局会矿场社所部处坊店园摊厂铺站园亭厅仓库])', types.tags_NB, __nu_rec.__func__),
                 (f'([第笫苐新老大小东西南北]*[{nnp.num_re}]{{0,7}}[号分中小]*[组队])', types.tags_NB, __nu_rec.__func__),
                 (f'([第笫苐农兵]*[{nnp.num_re}]{{1,7}}[师])([零一二三四五六七八九十]+团)?', types.tags_NS, __nu_rec.__func__), ]
    # 附加单字填充占位模式
    att_chars = {'省', '市', '区', '县', '乡', '镇', '村', '屯', '州', '盟', '旗', '办', '与', '及', '和', '的', '暨', '新', '老', '原', '女', '驻', '东', '南', '西', '北', '路', '街', '道', '港', '至', '段'}
    att_rules = [(f'([{"".join(att_chars)}])', types.tags_NA, __nu_rec.__func__), ]  # 常用单字填充占位

    # 为了更好的利用地名组份信息,更好的区分主干部分的类型,引入了"!尾缀"标注模式,规则如下:
    # 1 未标注!的行,整体地名(S)进行使用,并在移除尾缀词后,主干部分作为名称(N)使用,等同于标注了!N
    # 2 标注!的且没有字母的,不拆分,将整体作为:地名(S)
    # 3 标注!后有其他字母的,主干部分按标注类型使用: A-弱化名称/S-地名/M-实体/U-序号/N-名称/Z-专业名词/H-特殊词/B-分支
    tag_labels = {'A': types.tags_NA, 'S': types.tags_NS, 'M': types.tags_NM, 'U': types.tags_NU, 'O': types.tags_NO, 'N': types.tags_NN, 'Z': types.tags_NZ, 'H': types.tags_NH, 'B': types.tags_NB}

    # 可进行特殊短语包裹的括号对
    brackets_map = {'<': '>', '(': ')', '[': ']', '"': '"', "'": "'"}
    brackets_rmap = {'>': '<', ')': '(', ']': '[', '"': '"', "'": "'"}

    @staticmethod
    def query_nu(txt, rst, offset=0):
        """查询txt中的数字相关特征模式,结果记录在rst中:[b,e,{types}],b的起始偏移为offset"""
        rc = 0
        for pat in nt_parser_t.num_rules:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            rc += pat[2](rst, mres, pat[1], offset)

        if len(txt) == 1:
            for pat in nt_parser_t.att_rules:
                mres = list(re.finditer(pat[0], txt))
                if not mres:
                    continue
                rc += pat[2](rst, mres, pat[1], offset)

        return rc

    @staticmethod
    def rec_nums(segs, txt):
        """根据预匹配分段列表,尝试进行编号分段的补全.返回值:补充的分段数量"""
        num_chars3 = {'组', '第', '大', '中', '铁', '农', '建'}
        num_chars3.update(nnp.num_cn)

        chks = []

        def chk_num_segs(rsts):
            """分析需要进行数字匹配的分段"""
            nonlocal chks
            seg = rsts[-1]  # 最新段
            idx = len(rsts) - 1  # 当前段索引
            pseg = rsts[-2] if idx else None  # 前一段
            if pseg:
                if seg[1] <= pseg[1]:
                    return  # 如果当前段被前段包含则放弃
                if pseg[2] and seg[2] and not pseg[2] & {types.NA, types.NU, types.NN} and seg[2] & {types.NA} and pseg[1] - seg[0] == 1:
                    seg = (seg[0] + 1, seg[1], seg[2])  # 销售中心|心一处,校正后分段的范围,尝试序号识别.

            seg_is_NA = True if seg[2] and seg[2] & {types.NA, types.NU} else False

            def _rec(idx):
                if pseg and (seg[2] is None or seg_is_NA):
                    if pseg[2] is None or {types.NA, types.NU} & pseg[2]:
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
            slen = seg[1] - seg[0]
            if slen == 1 and c0 not in {'.'}:
                _rec(idx)  # 如果当前是单字NA段,则记录
            elif slen > 1 and (c0 in nnp.num_cn or cl in num_chars3 or c0 in {'和'}):
                _rec(idx)  # 如果当前是特定多字NA段,则记录

        usegs, uc = mu.complete_segs(segs, len(txt), True, cb=chk_num_segs)  # 得到补全的分段列表
        if not chks:
            return []

        def skip_next(pos, uidx, usegs):
            """判断txt[pos]是否还需要向后扩展"""
            w_stops = {'营业', '营销', '营养', '营造', '营部', '矿业', '乡镇', '中学', '五金', '百货', '连锁', '冶金', '船舶', '高地', '组货', '门市', '江苏', '江西',
                       '农场', '房产', '仓库', '厂区', '路边', '仓储', '厂房', '居家', '排挡', '排档', '铺子', '营口', '桥头'}
            w_stops3 = {'房地产', '公里处'}
            if txt[pos:pos + 2] in w_stops:
                return pos
            if txt[pos:pos + 3] in w_stops3:
                return pos
            if txt[pos - 1:pos + 1] in w_stops:
                return pos - 1
            if txt[pos - 1:pos + 2] in w_stops3:
                return pos - 1

            w_nexts = {'工区', '分号', '部队', '公里', '马路', '社区', '号仓', '分钟', '小时', '职高', '大道', '院区', '支部', '号店', '船队', '号楼', '分场', '路段', '分店', '分仓'}
            if txt[pos:pos + 2] in w_nexts:
                return pos + 2
            if txt[pos - 1:pos + 1] in w_nexts:
                return pos + 1
            if txt[pos:pos + 2] in {'三门'}:
                return pos + 3
            if pos < len(txt) and txt[pos] in {'团'}:
                return pos + 1

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
                        if nseg[2] & {types.NN} and txt[nseg[0]] in nnp.num_cn:
                            return pos + 1

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
                pseg_slen = pseg[1] - pseg[0]
                if pseg[2] is None:
                    return pos - 1
                if pseg[2] & {types.NM, types.NZ, types.NB, types.NS}:
                    return pos
                if pseg_slen >= 2 and pseg[2] & types.tags_NO:
                    return pos
                if pseg[2] & {types.NN, types.NA}:
                    if uidx >= 2:
                        ppseg = usegs[uidx - 2]
                        if pseg[1] <= ppseg[1] and ppseg[2] and ppseg[2] & {types.NM, types.NZ, types.NB, types.NS}:
                            return pos  # 浦东|东,不涵盖'东'
                        if pos >= pseg_slen and txt[pseg[0]] in {'东', '南', '西', '北'}:
                            return pos - pseg_slen
                        if pseg[1] - ppseg[1] == 1:  # 前面两个分段交叉余一
                            return pos - 1
                    if pseg_slen >= 3 and txt[pseg[1] - 1] in num_chars3:
                        return pos - 1
                    if pseg_slen == 2 and txt[pseg[1] - 1] in nnp.num_cn:
                        return pos - 1
                    if pseg_slen == 1:
                        return pos - 1

                    return pos
                if pseg_slen == 2:
                    return pos
            return pos - 1 if pos else pos

        nums = []
        for uidx in chks:  # 逐一处理未匹配分段
            useg = usegs[uidx]
            useg_slen = useg[1] - useg[0]
            if useg_slen == 1 and txt[useg[0]] in {'(', ')'}:
                continue  # 如果是单独的括号未匹配分段,不处理.

            # 猜测需要进行数字序号抽取的范围集合,提高可用结果的范围.
            b = skip_prev(useg[0], uidx, usegs)  # 向前扩张
            e = skip_next(useg[1], uidx, usegs)  # 向后扩张
            rgns = {(b, e)}
            if b != useg[0] or e - b > 2:
                rgns.add((b + 1, e))
                rgns.add((b, e - 1))
            if e - b >= 4:
                rgns.add((b + 2, e))
            if e >= useg[1]:
                rgns.add((useg[0], useg[1]))
            if useg_slen == 2:
                rgns.add((useg[0], useg[1] - 1))
            if useg_slen >= 2:
                if txt[useg[0]] in {'(', ')', '>'}:
                    rgns.add((useg[0] + 1, useg[1]))
                if txt[useg[0]] in nt_parser_t.att_chars:
                    rgns.add((useg[0], useg[0] + 1))
                if txt[useg[1] - 1] in nt_parser_t.att_chars:
                    rgns.add((useg[1] - 1, useg[1]))

            for rgn in rgns:
                s = txt[rgn[0]:rgn[1]]
                nt_parser_t.query_nu(s, nums, rgn[0])  # 进行数字序号匹配

        return nums

    @staticmethod
    def chk_nums(words):
        """校验words中是否含有序号分段.返回值:[匹配的分段信息]"""
        return nt_parser_t.rec_nums([], words)

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

        def add_line(txt, row):
            if not txt or txt[0] == '#':
                return
            if vals_cb:
                vals = vals_cb(txt)
                for val in vals:
                    ret, old = self.add_word(val[0], val[1])
                    if chk_cb is not None and not ret:
                        chk_cb(fname, row, txt, val[0], old)
            else:
                name, tag = nt_parser_t._split_label(txt)  # 内置标注解析处理
                if not tag:
                    tag = tags
                ret, old = self.add_word(name, tag)
                if chk_cb is not None and not ret:
                    chk_cb(fname, row, txt, name, old)

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

    def add_word(self, word, tags, chk_cb=None):
        """给内部匹配器添加词汇"""
        if self.listen_cb_wordadd and self.listen_cb_wordadd(word, tags):
            return None, None  # 如果要求放弃该词,则直接返回
        ret, old = self.matcher.dict_add(word, tags)
        if ret:
            return True, None
        else:
            if old != tags:
                self.matcher.dict_add(word, tags.union(old))
            return False, old

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
            if line[-2:] in {'林场', '农场', '牧场', '渔场'}:
                return types.tags_NM
            if line[-2:] in {'水库', '灌区'}:
                return {types.NS, types.NM}
            if line[-3:] in {'管理区'}:
                return {types.NS, types.NO}
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
                    if len(name) <= 5:
                        self.add_word('驻' + name, tags)  # 增加驻地名称模式
                    aname = cai.drop_area_tail(name)
                    if name != aname and aname not in nnd.nt_tail_datas:
                        tags = self.nsa_type_maps.get(aname, tags)  # 对内置地名的简称进行类型调整
                        _, old = self.add_word(aname, tags)  # 特定尾缀地区名称,放入简称和初始类型
                        if old:
                            tmp = old.difference(tags).difference({types.NS1, types.NS2, types.NS3, })
                            if tmp and aname not in {'御道口牧场'}:
                                print(f'cai.map_id_areas: {aname}@{name} is repeat! {tmp}')
                        if len(aname) <= 4:
                            self.add_word(f'驻{aname}', types.tags_NS)  # 增加驻地简称模式

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
                r, ot = self.add_word(area, types.tags_NZ)
                if not r:
                    print(f"nlp_ner_nt.load_ns area is repeat: {area} {ot}")

        # 地名的构成很复杂.最简单的模式为'名字+省/市/区/县/乡',还有'主干+街道/社区/村/镇/屯',此时的主干组份的模式就很多,如'xx街/xx路/xx站/xx厂'等.

        def nn_tags(aname):
            """获取指定地名主干的类别"""
            if aname[-1] in cai.ns_tails:
                return ns_tags(aname)  # 如果主干部分的尾字符合地名尾缀特征,则按地名标注
            # return {types.NN, types.NS}  # 非地名特征的全部作为名字类型
            return types.tags_NN

        def vals_cb(line):
            name, tag = nt_parser_t._split_label(line)  # 得到原始地名与对应的标注类型
            ns_typ = ns_tags(name)
            if tag == '':  # 不要求进行解析处理
                return [(name, ns_typ)]
            # 解析得到主干部分
            aname = cai.drop_area_tail(name)
            if name == aname:
                return [(name, ns_typ)]
            if aname in nnd.nt_tail_datas:
                fn = fname if isinstance(fname, str) else f'dict@{fname[0]}'
                print(f'<{fn}> {name}@{aname} is repeat in nt_tail_datas.')
                return [(name, ns_typ)]

            if tag is None:  # 没有明确标注主干类型时
                if aname[-1] in nnp.num_cn:  # 简化名称尾缀为数字特征时
                    tag = types.tags_NA  # 则简化名称降级为弱化类型
                else:
                    tag = nn_tags(aname)  # 根据主干部分决定类型

            rst = [(name, ns_typ), (aname, tag)]
            if len(name) > 4 and name[-3:] in {'嘎查村', '苏木乡'}:
                rst.append((name[:-1], ns_typ))  # 增加特殊简化名称
            return rst

        return self.__load(isend, fname, types.tags_NS, encode, vals_cb, self._chk_cb) if fname else ''

    def load_nz(self, fname, encode='utf-16', isend=True):
        """装载NZ组份词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NZ, encode, chk_cb=self._chk_cb)

    def load_nn(self, fname, encode='utf-16', isend=True):
        """装载NN尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NN, encode, chk_cb=self._chk_cb)

    def load_nh(self, fname, encode='utf-16', isend=True):
        """装载NH尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NH, encode, chk_cb=self._chk_cb)

    def load_na(self, fname, encode='utf-16', isend=True):
        """装载NA尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NA, encode, chk_cb=self._chk_cb)

    def load_nu(self, fname, encode='utf-16', isend=True):
        """装载NU尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NU, encode, chk_cb=self._chk_cb)

    def load_no(self, fname, encode='utf-16', isend=True):
        """装载NO尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NO, encode, chk_cb=self._chk_cb)

    def loads(self, dicts_list, path=None, with_end=True, dbginfo=False, encode='utf-16'):
        """统一装载词典列表dicts_list=[('类型','路径')].返回值:空串正常,否则为错误信息."""
        map = {"NS": self.load_ns, "NT": self.load_nt, "NZ": self.load_nz, "NN": self.load_nn, "NH": self.load_nh, "NA": self.load_na, "NU": self.load_nu, "NO": self.load_no, "SA": self.load_nsa}
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
    def _tidy_segs(matcher, segs, merge_seg, line_txt):
        '''处理segs段落列表中交叉/包含/相同组份合并(merge_seg)的情况,返回值:(结果列表,前后段关系列表)'''
        rst = []
        clst = []
        if not segs:
            return rst, clst

        def can_combi_NS(pseg, seg, txt):
            """判断前段p与当前段c是否可以合并成为NS."""
            if not txt or pseg[1] != seg[0] or pseg[2] is None or seg[2] is None:
                return False  # 不要求合并,或者前后段不相邻,不合并

            pt = txt[pseg[0]:pseg[1]]
            ct = txt[seg[0]:seg[1]]

            if pt[-1] == ct[0]:
                return False  # 前后紧邻的叠字,不合并

            if pt[-1] in {'市'} and ct in {'区'}:
                return True
            if pt[-1] in {'村'} and ct in {'组'}:
                return True

            if ct in {'路', '街', '道', '巷', '站', '里', '弄', '东路', '西路', '南路', '北路', '中路', '东街', '南街', '西街', '北街', '中街', '大街'}:
                if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县'}:
                    return False  # 较长地名后面出现道路特征,不合并
                if pseg[2] & {types.NS, types.NN, types.NA, types.NZ, types.NH}:
                    return True  # 常规词性后出现道路特征,可合并

            if ct in {'区', '县', '乡', '镇', '村', '屯', '居', '办', '组', '港', '港区', '湾区', '地区', '苏木', '嘎查', '小区', '街道', '社区', '行政村', '自然村'}:
                if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县', '乡', '镇', '村', }:
                    return False  # 较长地名后面出现村镇特征,不合并
                if pseg[2] & {types.NS, types.NN, types.NA, types.NZ, types.NU}:
                    return True  # 常规词性后出现村镇特征,可合并

            if ct in {'东', '西', '南', '北', }:
                if pseg[2] & {types.NS, types.NM} or (len(pt) >= 3 and pt[-1] in {'市', '区', '县', '乡', '镇', '村'}):
                    return True  # 较长地名后面出现方向特征,合并
                if pseg[2] & {types.NN, types.NA, types.NZ}:
                    return False  # 常规词性后出现方位特征,不合并

            if ct in {'前', '后', '旁', '外', '内', '门前'}:
                if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县', '乡', '镇', '村', }:
                    return False  # 较长地名后面出现方位特征,不合并
                if pseg[2] & {types.NS, types.NM, types.NO}:
                    return True  # 组织词性后出现方位特征,合并

            return False  # 默认不允许合并

        area0_chars = {'县', '乡', '镇', '村', '路', '街', '道', '港'}  # 区以下地域特征尾缀
        areas_chars = {'新', '老', '小', '省', '市', '区', '州', '盟', '县', '乡', '镇', '村', }  # 地域特征字

        def rec_merge(pseg, seg, idx):
            """基于当前分段索引idx和分段信息seg,以及前段信息pseg,尝试进行分段合并"""
            if pseg[1] > seg[0]:
                # 前后两段相交
                if pseg[1] - seg[0] == 1:
                    # 前后单字交叉, 前段剩余单字且为前缀单字, 后段为特定尾缀, 合并: "市人|人民医院" 或 "芒市|市委"
                    if seg[2] & {types.NO, types.NM}:
                        if (seg[0] - pseg[0] == 1 and line_txt[pseg[0]] in areas_chars) or line_txt[seg[0]] in areas_chars:
                            rst[-1] = (pseg[0], seg[1], seg[2])
                            return True
                    if seg[0] - pseg[0] == 1 and line_txt[seg[1] - 1] in area0_chars:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)
                        return True

                score = nnp.tree_paths_t.score(pseg, seg, line_txt)
                if score[1] == 0:
                    rst[-1] = (pseg[0], seg[1], seg[2])  # 与路径分析保持一致,前后交叉且不扣分,则合并
                    return True

                if pseg[2] & {types.NN, types.NA} and seg[2] & {types.NN, types.NA}:
                    if line_txt[seg[1] - 1] in area0_chars:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)
                    else:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                    return True  # 前后交叉,且为特定类型,合并: "百家|家幸"

                if pseg[2] & {types.NS, types.NZ, types.NH} and seg[2] & {types.NS, types.NN, types.NA}:
                    if line_txt[seg[1] - 1] in area0_chars:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 特定模式,"凉山|山村"合并
                        return True

                if pseg[2] & {types.NS} and seg[2] & {types.NS, types.NN, types.NA}:
                    if line_txt[seg[0]] in area0_chars and line_txt[seg[0]:seg[1]] in {'镇中', '镇内'}:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 特定模式,"太平镇|镇中"合并
                        return True

                if pseg[2] & {types.NU, types.NA} and seg[2] & {types.NU, types.NA}:
                    rst[-1] = (pseg[0], seg[1], seg[2])
                    return True  # 前后交叉,且为特定序号类型,合并


            elif pseg[1] == seg[0]:  # 前后两段相连
                if {types.NB, types.NO, types.NM}.isdisjoint(pseg[2]) and seg[2].issuperset(types.tags_NL):
                    seg = segs[idx] = (seg[0], seg[1], {types.NM, types.NL})  # 孤立出现的尾缀NL要当作NM,如:深圳市投控东海一期基金(有限合伙)
                    rst.append(seg)
                    return True

                if pseg[2] & seg[2] and not seg[2] & {types.NO, types.NB}:
                    rst.append(seg)  # 前后连接且类型相同,直接记录,等待后续二次合并
                    return True

                if seg[1] - seg[0] == 1:
                    if seg[2] & {types.NO, types.NB}:
                        tw = line_txt[pseg[1] - 1:seg[1]]
                        if tw == '>社':
                            rst.append(seg)  # "<xx>|社"不合并
                            return True
                        elif tw in {'县城'}:
                            rst[-1] = (pseg[0], seg[1], pseg[2])
                            return True
                        else:
                            rst[-1] = (pseg[0], seg[1], seg[2])
                            return True  # 单字特征尾缀,合并

                if not merge_seg:
                    return False  # 不要求类型合并,则后面的合并分析不执行

                if can_combi_NS(pseg, seg, line_txt):
                    rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 进行NS地名合并
                    return True

                if pseg[1] - pseg[0] == 1:
                    if line_txt[pseg[0]] in areas_chars and seg[2] & {types.NB, types.NO, types.NM}:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                        return True  # 特定前置单字连接特征尾缀,合并

                    if seg[2] & {types.NN, types.NA} and line_txt[pseg[0]] in {'新'}:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                        return True  # 前后相连的特定单字前缀

                if pseg[1] - pseg[0] <= 3 and line_txt[seg[0]:seg[1]] in {'大学', '中学', '小学', '学校', '省委', '市委', '区委', '县委'}:
                    rst[-1] = (pseg[0], seg[1], seg[2])  # 前后连接特定类型可合并: "东北|大学","北京|大学"
                    return True

                if pseg[1] - pseg[0] <= 2 and seg[1] - seg[0] <= 2 and pseg[2] & {types.NU} and seg[2] & {types.NB}:
                    rst[-1] = (pseg[0], seg[1], seg[2])
                    return True  # 前后连接特定类型可合并

            return False

        def rec_cut(pseg, seg):
            """记录前后两个分段的交叉切分"""

            def adj_typ_NO(b, e, typ_nhit):
                """根据给定的分段范围与默认类型,进行特定分段类型的校正"""
                w = line_txt[b:e]
                if w in {'矿', '店', '局'}:  # 需要进行NO/NS转换的单字
                    return types.tags_NO
                else:
                    if not matcher:
                        return nnd.nt_tail_datas.get(w, typ_nhit)
                    else:
                        if len(w) == 1 and line_txt[b - 1:e] in {'县城'}:
                            return types.tags_NS
                        mres = matcher.do_check(w, mode=mac.mode_t.max_match)
                        if not mres or mu.slen(mres[-1]) != len(w):
                            return typ_nhit
                        return mres[-1][2]

            if pseg[1] > seg[0] and types.NX not in seg[2]:
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

            # 在第三段到来的时候,尝试进行前两段的合并处理.
            if len(rst) >= 2 and rst[-2][1] == rst[-1][0]:
                p2seg = rst[-2]
                p1seg = rst[-1]
                if mu.slen(p2seg) > 1 and can_combi_NS(p2seg, p1seg, line_txt):  # 在前一轮北切分剩余单字后,再次尝试 合并'|南京|路|'
                    rst[-2] = (p2seg[0], p1seg[1], types.tags_NS)  # 转换分段类型为NS
                    rst.pop(-1)
                elif mu.slen(p1seg) == 1 and p1seg[1] == seg[0]:
                    if line_txt[p1seg[0]] not in {'和', '驻', '至'} and types.tags_NS.issubset(seg[2]):
                        rst[-1] = (p1seg[0], seg[1], seg[2])  # OC+NS合并为NS
                        return  # 不再重复记录当前分段

            if types.NX not in seg[2]:
                if seg[1] - seg[0] >= 2 and types.tags_NA.issubset(seg[2]) and line_txt[seg[1] - 2:seg[1]] in {'里店', '东店', '南店', '西店', '北店'}:
                    seg = (seg[0], seg[1], types.tags_NO)  # 校正特殊店铺尾缀
                rst.append(seg)  # 记录后段信息

        rst.append(segs[0])
        for idx in range(1, len(segs)):
            pseg = rst[-1]
            seg = segs[idx]
            if not rec_merge(pseg, seg, idx):  # 先尝试前后段合并
                rec_cut(pseg, seg)  # 再进行前后段切分

        lseg = rst[-1]
        rec_cut(lseg, (lseg[1], lseg[1], {types.NX}))  # 使用最后的模拟空段驱动前面的分段合并

        if not merge_seg:
            return rst, clst

        i = 1
        while i < len(rst):  # 合并相邻的 NN/NH/NA
            pseg = rst[i - 1]
            seg = rst[i]
            if pseg[1] != seg[0] or not seg[2] or not pseg[2]:
                i += 1  # 进行有效性检查
                continue

            # 进行分段类型修正,NH/NA变为NN
            if pseg[2] & {types.NA, types.NH}:
                pseg = rst[i - 1] = (pseg[0], pseg[1], types.tags_NN)
            if seg[2] & {types.NA, types.NH}:
                seg = rst[i] = (seg[0], seg[1], types.tags_NN)

            if (seg[1] - seg[0] == 1 or pseg[1] - pseg[0] == 1) and not pseg[2] & seg[2] & {types.NU}:
                i += 1  # 不主动合并单字
                continue

            # 前后相同类型分段进行合并
            if pseg[2] & seg[2] and not seg[2] & {types.NO, types.NB, types.NM}:
                rst[i - 1] = (pseg[0], seg[1], seg[2])
                rst.pop(i)  # 向前合并,丢弃当前段
            else:
                i += 1

        return rst, clst

    @staticmethod
    def _merge_nums(segs, nusegs, txt):
        """将nusegs中的分段信息合并到segs中"""
        if not nusegs:
            return

        def _find_pre(pos, seg):
            """在segs中查找pos之前与seg相交的NA/NU分段,返回值:前段索引,或None"""
            if not pos or not seg[2] & {types.NU, types.NA}:
                return None
            if txt[seg[0]] not in nnp.num_cn:
                return None

            pre = None
            for i in range(pos - 1, -1, -1):
                pseg = segs[i]
                if pseg[1] <= seg[0]:
                    break
                if pseg[2] & {types.NA, types.NU}:
                    pre = i
                else:
                    break
            return pre

        def _find_nxt(pos, seg):
            """在segs中查找pos之后与seg相交的NA/NU分段,返回值:后段索引,或None"""
            if not seg[2] & {types.NU, types.NA}:
                return None
            if txt[seg[1] - 1] not in nnp.num_cn:
                return None

            nxt = None
            for i in range(pos, len(segs)):
                nseg = segs[i]
                if nseg[0] >= seg[1] or nseg[1] <= seg[1]:
                    break
                if nseg[2] & {types.NA, types.NU}:
                    nxt = i
                else:
                    break
            return nxt

        def _equ(pos, nseg):
            """检查segs的pos处分段是否与nseg重合"""
            if pos >= len(segs):
                return False
            oseg = segs[pos]  # 不是追加新段,则需要判断是否与落脚点的分段重合
            return nseg[0] == oseg[0] and nseg[1] == oseg[1]

        def rec(pos, seg, append):
            """在segs的pos处插入新的序号分段seg"""
            if not append:
                # 不是追加新段,则需要判断是否与落脚点的分段重合
                if _equ(pos, seg):
                    oseg = segs[pos]
                    if not oseg[2] & seg[2] and oseg[2] & {types.NU, types.NA}:
                        segs[pos] = seg  # 分段重合但类别不同,则更新
                    return
            elif len(segs) and pos:
                if seg[1] - seg[0] == 1 and seg[1] < segs[pos - 1][1]:
                    return  # 追加的单字,处于前面分段的内部,放弃.

            pre = _find_pre(pos, seg)
            if pre is not None:
                pseg = segs[pre]
                if pseg[0] < seg[0] < pseg[1] < seg[1]:
                    mseg = (pseg[0], seg[1], seg[2])
                    if not _equ(pre + 1, mseg):
                        segs.insert(pre + 1, mseg)  # 待插入的seg序号段与前面的NA/NU分段有交叉,则生成一个新的合并段
                        pos += 1

            nxt = _find_nxt(pos, seg)
            if nxt is not None:
                nseg = segs[nxt]
                if seg[0] < nseg[0] < seg[1] < nseg[1]:
                    mseg = (seg[0], nseg[1], seg[2])
                    if not _equ(nxt, mseg):
                        segs.insert(nxt, mseg)  # 待插入的seg序号段与后面的NA/NU分段有交叉,则生成一个新的合并段

            if not _equ(pos, seg):
                segs.insert(pos, seg)

        nseg = nusegs[0]
        pos = mu.insert_pos(segs, nseg)
        rec(pos, nseg, pos == len(segs))
        for i in range(1, len(nusegs)):  # 对数字分段进行逐一处理
            nseg = nusegs[i]
            pos = mu.insert_pos(segs, nseg, max(0, pos - 1))
            rec(pos, nseg, pos == len(segs))

    def split(self, txt, mres=None, pres=None, fp_dbg=False, nres=None, drop_tail_O=False):
        '''在txt中拆分可能的组份段落
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            mres - 记录参与匹配的原始词汇列表
            pres - 记录匹配完成后并清理过的词汇列表
            返回值:分段列表nres [(b,e,{types})]
        '''

        def clean_drop(segs):
            """匹配后再分析并删除分段列表segs中被包含且无接续的无效分段"""

            rc = 0
            pos = 0
            while pos < len(segs) - 1:
                seg = segs[pos]
                nseg = segs[pos + 1]

                if nseg[0] == seg[0]:
                    # seg被nseg左贴包含,判断右侧是否有粘连
                    if seg[1] < nseg[1] and not nnp.find_right(segs, seg, pos + 2):
                        segs.pop(pos)
                        rc += 1
                        continue
                    if nseg[1] < seg[1] and not nnp.find_right(segs, nseg, pos + 2):
                        segs.pop(pos + 1)
                        rc += 1
                        continue

                if seg[1] == nseg[1]:
                    # seg被nseg右贴包含,判断左侧是否有粘连
                    if nseg[0] < seg[0]:
                        if (pos and not nnp.find_left(segs, seg, pos - 1)) or not pos:
                            segs.pop(pos)
                            rc += 1
                            continue
                    # nseg被seg右贴包含,判断左侧是否有粘连
                    if seg[0] < nseg[0]:
                        if pos and not nnp.find_left(segs, nseg, pos - 1) or not pos:
                            if not (mu.slen(seg) == 2 and seg[2] & types.tags_NA and mu.slen(nseg) == 1 and txt[nseg[0]] in {'店', '矿'}):
                                segs.pop(pos + 1)
                                rc += 1
                                continue

                if pos:
                    pseg = segs[pos - 1]
                    if pseg[1] == nseg[0] and pseg[0] < seg[0] and seg[1] < nseg[1] and not nseg[2] & {types.NU, types.NA}:  # seg被前后夹击覆盖
                        if not nnp.find_left(segs, seg, pos - 2) and not nnp.find_right(segs, seg, pos + 2):
                            segs.pop(pos)
                            rc += 1
                            continue

                pos += 1

            return rc

        def rec_ex(rst, pos, node, root):
            """保留分段匹配结果"""

            def can_drop(seg):
                rstlen = len(rst)
                if rstlen:
                    pseg = rst[-1]
                    plen = mu.slen(pseg)
                    slen = mu.slen(seg)
                    if seg[0] < pseg[0]:  # 新段起点早于旧段
                        if plen == 1 or not nnp.find_left(rst, pseg, rstlen - 2):  # 且旧段无左侧粘连
                            return True
                        if pseg[0] - seg[0] >= 2:
                            return True
                    if pseg[0] == seg[0]:  # 前后段起点相同
                        if slen - plen >= 2 and seg[2] & {types.NM, types.NO, types.NB}:
                            return True  # 发电|发电机厂,丢弃前段
                        if plen == 1 < slen and seg[2] & {types.NS}:
                            return True  # 北|北京,丢弃前段
                    if seg[0] < pseg[0] and pseg[1] < seg[1]:
                        if slen >= 6 and plen <= 4:
                            return True  # 长段包含短段,丢弃短段

                if rstlen >= 2:
                    fseg = rst[-2]
                    flen = fseg[1] - fseg[0]

                    if plen == 1:
                        if fseg[0] < pseg[0] and fseg[1] == pseg[1]:
                            if not nnp.find_left(rst, pseg, rstlen - 2):
                                return True  # 右贴被包含的单字,左侧无粘连则丢弃
                    if fseg[0] < pseg[0] and pseg[0] < fseg[1] < pseg[1] and fseg[2] & types.tags_NS and pseg[2] & types.tags_NS:
                        if rstlen >= 3:  # NS禁止交叉
                            if nnp.find_left(rst, pseg, rstlen - 3):
                                return False  # 除非前面存在接续分段
                        return True

                    if fseg[0] == pseg[0] == seg[0] and fseg[1] < pseg[1] < seg[1] and flen == 1:
                        rst.pop(-2)  # 东|东莞|东莞市,删除'东'
                        return False

                    if slen >= 3:
                        if fseg[0] < pseg[0] < seg[0] and pseg[1] > seg[0] and fseg[1] == seg[0] and flen > 1:
                            if seg[2] & {types.NM, types.NS} and not nnp.find_left(rst, pseg, rstlen - 2):
                                return True  # 以当前长段为基准,丢弃前面的交叉分段pseg
                        if fseg[0] == seg[0] and fseg[0] < pseg[0] < seg[1] and fseg[1] <= pseg[1] < seg[1]:
                            return True  # 中华|华人|中华人民共和国,丢弃中间分段
                        if fseg[1] - seg[0] >= 2 and fseg[1] - pseg[0] == 1 and pseg[1] < seg[1]:
                            return True  # 中小企业|业服|企业服务,丢弃中间分段

                    if flen >= 3 and fseg[2] & {types.NM, types.NZ} and not pseg[2] & {types.NM, types.NO}:
                        if fseg[0] < pseg[0] < fseg[1] and pseg[1] > fseg[1] and seg[0] == fseg[1] and not nnp.find_left(rst, pseg, rstlen - 2):
                            return True  # 以之前的长段为基准,丢弃后面的交叉分段pseg

                    if (slen - plen >= 2 and seg[2] & {types.NS, types.NZ, types.NM, types.NH}) and seg[0] < pseg[1] and not pseg[2] & {types.NM, types.NO, types.NB, types.NZ}:
                        pi = nnp.find_left(rst, seg, rstlen - 1)
                        if 1 <= pi <= rstlen:
                            oseg = rst[rstlen - pi]  # 重要分段前面连接着特征尾缀
                            if oseg[1] - oseg[0] >= 2 and oseg[2] & {types.NM, types.NO, types.NB, types.NZ, types.NS}:
                                return True  #

                if rstlen >= 3:
                    f3 = rst[-3]
                    f2 = rst[-2]
                    f1 = rst[-1]

                    if seg[1] - seg[0] == 1 and types.tags_NO.issubset(seg[2]):
                        if f3[1] == seg[0] and f3[0] == f2[0] and seg[1] == f2[1] == f1[1] and types.tags_NA.issubset(f2[2]) and not nnp.find_left(rst, seg, rstlen - 4):
                            rst.pop(-2)
                            return True  # S:东方|A:东方店|A:方店|O:店 不记录中间的A分段

                return False

            def can_rec(seg):
                city_tails = {'省', '市', '区', '县', '乡', '镇', '村', '州', '旗', '街', '路', '道'}
                rstlen = len(rst)
                if rstlen >= 3:
                    f3 = rst[-3]
                    f2 = rst[-2]
                    f1 = rst[-1]

                    if seg[1] - seg[0] == 1:
                        if f3[1] == seg[0] and f3[0] == f2[0] and seg[1] == f2[1] == f1[1] and not nnp.find_left(rst, seg, rstlen - 4):
                            return False  # Z:小吃|O:小吃店|O:吃店|O:店 不记录最后的单字

                        if f3[1] == f2[1] == f1[1] == seg[1] and not nnp.find_left(rst, seg, rstlen - 4):
                            return False  # O:发电机厂|O:电机厂|O:机厂|O:厂 不记录最后的单字

                if rstlen >= 2:
                    fseg = rst[-2]
                    pseg = rst[-1]
                    flen = mu.slen(fseg)
                    plen = mu.slen(pseg)
                    slen = mu.slen(seg)
                    if slen == 1:
                        if flen == 1 and seg[0] == fseg[1] and pseg[0] == fseg[0] and pseg[1] == seg[1] and fseg[2] & seg[2] & types.tags_NA:
                            rst.pop(-2)  # 西|西北|北 : 丢弃首段不记录尾段
                            return False
                        if fseg[1] == pseg[1] == seg[1] and not nnp.find_left(rst, seg, rstlen - 3):
                            return False  # O:电子厂|B:子厂|O:厂,不记录最后的单字
                        if fseg[0] == pseg[0] and fseg[1] == seg[0] and pseg[1] == seg[1] and types.tags_NO.issubset(seg[2]) and types.tags_NO.issubset(pseg[2]):
                            return False  # Z:卫生|O:卫生院|O:院,不记录最后的单字

                    if plen >= 3 and flen > 1:
                        if fseg[0] == pseg[0] and fseg[1] < pseg[1] and seg[1] == pseg[1]:
                            if seg[2] & {types.NO, types.NM, types.NB}:
                                return True  # 江门|江门市|门市,先记录后段
                            if fseg[1] == seg[0] and not nnp.find_left(rst, seg, rstlen - 3):
                                return False  # 资产|资产管理|管理 : 丢弃首段不记录尾段
                            if pseg[2] & {types.NS} and not nnp.find_left(rst, seg, rstlen - 3):
                                return False  # NS禁止交叉:天津|天津市|津市,不记录最后分段

                if rstlen:
                    pseg = rst[-1]
                    if mu.slen(pseg) >= 3:
                        if seg[1] == pseg[1] and seg[0] > pseg[0] and pseg[2] & {types.NO, types.NM, types.NB} and seg[2] & types.tags_NA:
                            return False  # 被NO/NM/NB右包含的NA不记录
                        if seg[1] == pseg[1] and mu.slen(seg) == 1 and pseg[2] & types.tags_NS and seg[2] & types.tags_NA and txt[seg[0]] in city_tails:
                            return False  # 上海|上海市|市,不记录最后的单字
                        if seg[0] - pseg[0] >= 2 and seg[1] <= pseg[1] and seg[2] & pseg[2] & {types.NM, types.NO}:
                            if not nnp.find_left(rst, seg, rstlen - 2):  # 有限责任公司|责任公司|公司,丢弃后两个,如果与前面无粘连
                                return False
                    if mu.slen(seg) == 1 and seg[1] == pseg[1]:
                        if pseg[2] & {types.NM, types.NO, types.NB} and txt[seg[0]] in {'市'}:
                            return False  # 不记录 '超市/门市' 末尾的单字
                        if pseg[2] & {types.NM, types.NO, types.NB} and seg[2] & {types.NO}:
                            if drop_tail_O or not nnp.find_left(rst, seg, rstlen - 2):
                                return False  # 不记录 '医院/院' 末尾的单字
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

        # 按词典进行完全匹配
        segs = self.matcher.do_check(txt, mode=rec_ex)
        clean_drop(segs)  # 进行无效匹配结果的丢弃
        if pres is not None and isinstance(pres, list):
            pres.extend(segs)  # 记录预处理后的结果

        # 进行未知分段的数字序号识别
        nums = self.rec_nums(segs, txt)
        if nums:
            self._merge_nums(segs, nums, txt)  # 对识别的数字序号分段进行合并
            clean_drop(segs)

        # 根据匹配结果查找最佳nt路径
        nres = nnp.find_nt_paths(txt, segs, fp_dbg, nres)
        self._merge_bracket(nres, txt)  # 合并附加括号
        return nres

    def parse(self, segs, txt, merge_seg=True, with_useg=False):
        '''在txt中解析可能的组份段落
            merge_seg - 告知是否合并同类分段
            nulst - 可给出外部数字模式匹配列表
            with_useg - 是否补全分段列表
            mres - 记录匹配过程中的原始词汇分段列表
            pres - 记录匹配完成后并清理过的词汇分段列表
            返回值:(分段列表[(b,e,{types})],分段关系列表[(pseg,rl,nseg,cr)])
        '''
        # segs = self.split(txt, mres=mres, fp_dbg=fp_dbg)  # 得到匹配分段列表
        if not txt:
            return [], []
        rlst, clst = self._tidy_segs(self.matcher, segs, merge_seg, txt)  # 进行合并整理
        if with_useg:
            rlst = mu.complete_segs(rlst, len(txt), True)[0]  # 补全中间的空洞分段

        return rlst, clst

    def verify(self, name, segs=None, merge_seg=False, rec_NL=False, mres=None, pres=None, nres=None, strict=False, fp_dbg=False):
        """对给定的name机构名称进行拆分并校验有效性(要求尾缀必须为有效机构特征),如附属机构/分支机构/工会.
            segs - 可记录组份分段数据的列表.
            merge_seg - 是否合并相同类型分段
            rec_NL - 是否独立记录后缀分段
            mres - 记录参与匹配的原始词汇分段列表(未处理过的)
            pres - 记录匹配完成后并清理过的词汇分段列表
            strict - 是否未严格模式,遇到未知分段则不记录
            返回值:分段列表[(bpos,epos,types)]
                  返回的types只有NM与NB两种组份模式
        """

        nres = self.split(name, mres=mres, pres=pres, fp_dbg=fp_dbg, nres=nres)  # 得到匹配分段列表
        cons, _ = self.parse(nres, name, merge_seg)
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
            if name[seg[0]] == '(' and name[seg[1] - 1] == ')':
                if name[seg[0] + 1] == '(' and name[seg[1] - 2] == ')':
                    return 2
                return 1
            return 0

        def chk_errs(i, seg):
            """检查当前段是否为错误切分.如'师范学院路'->师范学院/学院路->师范/学院路,此时的'师范'仍是NM,但明显是错误的."""
            if seg[1] - seg[0] >= 2 and {types.NU, types.NL}.isdisjoint(seg[2]) and types.equ(seg[2], types.tags_NM):
                brt = is_brackets(seg)
                if brt:
                    txt = name[seg[0] + brt:seg[1] - brt]
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

        def can_rec_o(islast, npos):
            if islast:
                return True
            if npos >= len(segs):
                return True
            nseg = segs[npos]
            if nseg[2] is None:
                return True
            if is_brackets(nseg) and nseg[2] & {types.NM, types.NL}:
                return True
            return False

        for i, seg in enumerate(segs):
            stype = seg[2]
            epos = seg[1]
            slen = seg[1] - seg[0]
            if slen == 0:
                print(name, segs)
            islast = (i == len(segs) - 1) or name[seg[1]] in {"'", '"'}
            if stype is None:
                if strict and name[seg[0]] not in {'(', ')'}:
                    break
                continue
            if stype & {types.NM, types.NL}:  # NT/NL/NTNL
                rec(i, seg, bpos, epos, types.NM)
                if rec_NL and types.tags_NL.issubset(stype):  # 在校验输出列表中,是否额外记录尾缀分段信息
                    outs.append((seg[0], seg[1], types.NL))
            elif types.NB in stype:
                rec(i, seg, bpos, epos, types.NB)  # 当前段是分支NT结尾
            elif types.NO in stype and can_rec_o(islast, i + 1):
                # 当前段是单字NO结尾,需要判断特例
                pseg = segs[i - 1]
                if slen == 1 and pseg[2] and pseg[2] & {types.NM, types.NO, types.NA}:
                    if name[pseg[1] - 1] != name[seg[0]] or name[seg[0]] in {'店', '站'}:
                        rec(i, seg, bpos, epos, types.NM)  # `NM|NO` 不可以为'图书馆馆'/'经销处处',可以是'马店店'/'哈站站',可以作为NT机构
                elif slen > 1 or pseg[2] is not None:
                    rec(i, seg, bpos, epos, types.NM)
        return outs

    def ends(self, txt, merge_seg=True, strict=True):
        '''查找txt中出现过的尾缀,merge_seg告知是否合并同类分段,strict指示是否严格尾部对齐.返回值:[(b,e,{types})]或[]'''
        mres = self.parse(txt, merge_seg)[0]
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
