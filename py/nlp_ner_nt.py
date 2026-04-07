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
from match_util import find_none
from nlp_ner_data import types


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需给出尽量准确的分词结果,而本解析器则尝试进行组合覆盖,给出覆盖后的分段特征结果.
    '''

    # 附加单字填充占位模式
    att_chars = {'省', '市', '区', '县', '乡', '镇', '村', '屯', '州', '盟', '旗', '办', '与', '及', '和', '的', '暨', '新', '老', '原', '东', '南', '西', '北', '路', '街', '道', '驻', '至', '段', }  # '女', '港',

    # 为了更好的利用地名组份信息,更好的区分主干部分的类型,引入了"!尾缀"标注模式,规则如下:
    # 1 未标注!的行,整体地名(S)进行使用,并在移除尾缀词后,主干部分作为名称(N)使用,等同于标注了!N
    # 2 标注!的且没有字母的,不拆分,将整体作为:地名(S)
    # 3 标注!后有其他字母的,主干部分按标注类型使用: A-弱化名称/S-地名/M-实体/U-序号/N-名称/Z-专业名词/H-特殊词/B-分支
    tag_labels = {'A': types.tags_NA, 'S': types.tags_NS, 'M': types.tags_NM, 'U': types.tags_NU, 'O': types.tags_NO, 'N': types.tags_NN, 'Z': types.tags_NZ, 'H': types.tags_NH, 'B': types.tags_NB}

    def __init__(self, light=False):
        self.matcher = mac.ac_match_t()  # 定义ac匹配树
        self.nsa_type_maps = {}  # 临时使用,地名简称类型转换映射表
        self.listen_cb_wordadd = None  # 监听词汇添加动作的回调方法
        if light:
            self.load_nt(isend=False)
            self.load_ns(isend=True)

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

    def add_word(self, word, tags, force=True):
        """给内部匹配器添加词汇.
        返回值: None,None 被放弃
               True,None 正常添加
               False,old 合并添加
        """
        if self.listen_cb_wordadd and self.listen_cb_wordadd(word, tags):
            return None, None  # 如果要求放弃该词,则直接返回

        word = word.replace('-', '.')
        ret, old = self.matcher.dict_add(word, tags)
        if ret:
            return True, None
        else:
            if force and not old & tags:
                self.matcher.dict_add(word, tags.union(old))
            return False, old

    def add_words(self, words, tags, isend=True):
        """添加指定的词汇列表到匹配树中"""
        for word in words:
            self.add_word(word, tags)
        if isend:
            self.matcher.dict_end()

    def _chk_dict_words(self, fname, row, txt, word, tag):
        """默认的检查词典冲突的输出回调事件处理器"""
        fn = fname if isinstance(fname, str) else f'dict@{fname[0]}'
        if tag is None:
            return
        if txt == word:
            print(f'<{fn}|{row + 1:>8},{len(txt):>2}>:{txt} repeat!<{tag}>')
        else:
            print(f'<{fn}|{row + 1:>8},{len(txt):>2}>:{txt} repeat {word}<{tag}>')

    def load_num_combs(self):
        """装载动态组合构造的词表,用于代替re正则匹配过程."""

        def make(tag, *cols):
            def cb(path, tag):
                self.add_word(''.join(path), tag)

            if len(cols) > 1:
                uni.make_str_combs(cb, tag, *cols)
            else:
                for v in cols[0]:
                    self.add_word(v, tag)

        def mix(*cols):
            rst = []
            for lst in cols:
                for v in lst:
                    if v not in rst:
                        rst.append(v)
            return rst

        nums_mix = list('0123456789零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾')
        nums_1_20lxs = uni.make_num2hz(1, 20, uni.NUM_MAP_HZL, False, True)
        nums_11_30lxs = uni.make_num2hz(11, 30, uni.NUM_MAP_HZL, False, True)
        nums_1_20us = uni.make_num2hz(1, 20, uni.NUM_MAP_HZL, True, True)
        nums_1_250lxs = uni.make_num2hz(1, 250, uni.NUM_MAP_HZL, False, True)
        nums_11_200ls = uni.make_num2hz(11, 200, uni.NUM_MAP_HZL, True, True)
        nums_11_200us = uni.make_num2hz(11, 200, uni.NUM_MAP_HZU, True, True)
        nums_11_100ls = uni.make_num2hz(11, 100, uni.NUM_MAP_HZL, True, True)
        nums_11_100us = uni.make_num2hz(11, 100, uni.NUM_MAP_HZU, True, True)
        nums_1_250 = [str(i) for i in range(250 + 1)]
        nums_100_800 = [str(i) for i in range(100, 800)]
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

        make(types.tags_NU, list('第笫苐'), mix(nums_mix, nums_1_20lxs, nums_1_250lxs))
        make(types.tags_NU, list('第笫苐') + [''], mix(nums_11_200ls, nums_11_200us, nums_1_250))
        make(types.tags_NA, list('新老大小东西南北钢附'), nums_mix)
        make(types.tags_NS, alphabet, list('0123456789') + [''], ['区', '块', '栋', '幢', '座', '楼', '小区', '社区'])
        make(types.tags_NU, alphabet, [''])
        make(types.tags_NS, list('GSXYC'), nums_100_800, ['线', ''])
        make(types.tags_NU, mix(nums_mix, nums_11_200ls, nums_11_200us, nums_1_250), list('#号號户轮块度角毛分秒吨届座级期船元克天年℃°'))
        make(types.tags_NS, ['第', ''], mix(nums_mix, nums_11_30lxs, nums_11_100ls, nums_11_100us, nums_1_250), list('#大支') + [''],
             '公里|经路|纬路|经街|纬街|马路|路段|矿区|社区|组村|队组|组组|职高|职中|层楼|门面|单元|号楼|号渠|号院子|院子|号铺子|铺子|组团|号井|街区'.split('|') + list(
                 '职委米道路弄街口里亩线层楼栋幢段桥井闸渠河沟江坝村区片门台田居营连排'))
        make(types.tags_NB, mix(nums_mix, nums_11_100ls, nums_11_100us, nums_1_250), ['', '号', '號'], list('团校院馆局矿场社所部处店园摊厂铺站园亭厅仓库队组'))
        make(types.tags_NB, mix(nums_mix, nums_11_100ls, nums_11_100us), ['', '号', '號'], '营部|包房|仓库|站台|库区|库房|校区|摊挡|摊点|摊位|店铺'.split('|'))
        make(types.tags_NB, mix(nums_mix, nums_11_100ls, nums_11_100us), '号坊'.split('|'))
        make(types.tags_NS, list('第笫苐农兵') + [''], nums_1_20lxs + nums_1_20us, ['师'], mix(nums_1_250lxs, nums_11_200ls, nums_1_250), ['团'])
        make(types.tags_NS, list('第笫苐农兵') + [''], nums_1_20lxs + nums_1_20us, ['师'])

    def load_nt(self, fname=None, encode='utf-16', isend=True, with_NO=True, keys=None, debars=None):
        """装载NT尾缀词典,返回值:''正常,否则为错误信息."""

        # 初始化构建匹配词表
        if len(self.matcher.do_loop(None, '有限公司')) != 4:
            self.load_num_combs()
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

        return self.__load(isend, fname, types.tags_NM, encode, chk_cb=self._chk_dict_words) if fname else ''

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

        def ns_tags(line, ismain=False):
            """根据地名进行行政级别查询,返回对应的类型标记"""
            tags = self.nsa_type_maps.get(line)
            if tags is not None:
                return tags
            if line[-2:] in {'林场', '农场', '牧场', '渔场'}:
                return types.tags_NM
            if line[-2:] in {'水库', '灌区'}:
                return {types.NS, types.NM}
            if not ismain and line[-3:] in {'管理区'}:
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
                    self.add_word(name, ns_tags(name, True))  # 进行动态类型计算
                    self.add_word(f'({name})', tags)  # 增加括号地名模式
                    if len(name) <= 10:
                        self.add_word(f'驻{name}', tags)  # 增加驻地名称模式
                    aname = cai.drop_area_tail(name)
                    if name != aname and aname not in nnd.nt_tail_datas:
                        tags = self.nsa_type_maps.get(aname, tags)  # 对内置地名的简称进行类型调整
                        _, old = self.add_word(f"({aname})", tags)  # 简化名称带着括号,放入简称和初始类型
                        _, old = self.add_word(aname, tags)  # 简化地区名称,放入简称和初始类型
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
                r, ot = self.add_word(f"({state})", tags)
                r, ot = self.add_word(state, tags)
                if not r:
                    print(f"nlp_ner_nt.load_ns state is repeat: {state} {ot}")

                city = cai.map_worlds[state]
                if city:
                    tags = self.nsa_type_maps.get(city, types.tags_NS1)  # 对city首都地名进行类型调整
                    r, ot = self.add_word(f"({city})", tags)
                    r, ot = self.add_word(city, tags)
                    if not r:
                        print(f"nlp_ner_nt.load_ns city is repeat: {city} {ot}")

            areas = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚', '东南亚']
            for area in areas:
                r, ot = self.add_word(f'({area})', types.tags_NS)
                r, ot = self.add_word(area, types.tags_NS)
                if not r:
                    print(f"nlp_ner_nt.load_ns area is repeat: {area} {ot}")

        # 地名的构成很复杂.最简单的模式为'名字+省/市/区/县/乡',还有'主干+街道/社区/村/镇/屯',此时的主干组份的模式就很多,如'xx街/xx路/xx站/xx厂'等.

        def nn_tags(aname):
            """获取指定地名主干的类别"""
            pc = aname[0]
            ch = aname[-1]
            if len(aname) == 2:
                if pc in cai.base_ns_tails or pc in nnp.num_cn or pc in nnp.num_zh:
                    return types.tags_NN  # 特定字符开头

                if ch in nnp.num_cn:
                    return types.tags_NA  # 数字结尾

            if ch in cai.ns_tails:
                return ns_tags(aname)  # 如果主干部分的尾字符合地名尾缀特征,则按地名标注

            if len(aname) == 2:
                if ch in cai.ext_ns_tails:
                    return types.tags_NN
                return types.tags_NH
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
                tag = nn_tags(aname)  # 根据主干部分决定类型

            rst = [(name, ns_typ), (aname, tag)]
            if len(name) > 4 and name[-3:] in {'嘎查村', '苏木乡'}:
                rst.append((name[:-1], ns_typ))  # 增加特殊简化名称
            return rst

        return self.__load(isend, fname, types.tags_NS, encode, vals_cb, self._chk_dict_words) if fname else ''

    def load_nz(self, fname, encode='utf-16', isend=True):
        """装载NZ组份词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NZ, encode, chk_cb=self._chk_dict_words)

    def load_nn(self, fname, encode='utf-16', isend=True):
        """装载NN尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NN, encode, chk_cb=self._chk_dict_words)

    def load_nh(self, fname, encode='utf-16', isend=True):
        """装载NH尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NH, encode, chk_cb=self._chk_dict_words)

    def load_na(self, fname, encode='utf-16', isend=True):
        """装载NA尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NA, encode, chk_cb=self._chk_dict_words)

    def load_nu(self, fname, encode='utf-16', isend=True):
        """装载NU尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NU, encode, chk_cb=self._chk_dict_words)

    def load_no(self, fname, encode='utf-16', isend=True):
        """装载NO尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, types.tags_NO, encode, chk_cb=self._chk_dict_words)

    def load_x(self, fname, encode='utf-16', isend=False, tags=None):
        """装载指定尾缀词典,返回值:''正常,否则为错误信息."""
        return self.__load(isend, fname, tags, encode, chk_cb=self._chk_dict_words)

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
                if pseg[2] & {types.NM, types.NO, types.NB}:
                    return bi, ei, False  # 包含了MOB分段
                seg = segs[i]
                if seg[2] & {types.NM, types.NO, types.NB}:
                    return bi, ei, False  # 包含了MOB分段
                if pseg[1] < seg[0]:
                    return bi, ei, False  # 前后分段位置相离

            if segs[ei][1] - segs[bi][0] >= 12:
                return bi, ei, False  # 括号范围内容过长
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

        # 地域行政区划尾字
        std_ns_tails = {'省', '市', '区', '县', '州', '乡', '镇', '村', '屯'}
        ext_ns_tails = std_ns_tails.union({'路', '街', '道'})

        def can_combi_NS(pseg, seg, txt, nseg=None):
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

            if ct in {'路', '街', '道', '巷', '里', '弄', '线', '东路', '西路', '南路', '北路', '中路', '东街', '南街', '西街', '北街', '中街', '大街'}:
                if len(pt) >= 3 and pt[-1] in {'省', '市', '区', '县'}:
                    return False  # 较长地名后面出现道路特征,不合并
                if pseg[2] & {types.NS, types.NN, types.NA, types.NZ, types.NH}:
                    return True  # 常规词性后出现道路特征,可合并

            if ct in {'区', '县', '乡', '镇', '村', '屯', '居', '办', '组', '港', '港区', '湾区', '地区', '苏木', '嘎查', '小区', '街道', '社区', '行政村', '自然村'}:
                if len(pt) >= 3 and pt[-1] in std_ns_tails:
                    return False  # 较长地名后面出现村镇特征,不合并
                if pt[-1] in ext_ns_tails and nseg and nseg[2] & {types.NO, types.NM, types.NB}:
                    return False  # 前段是区划特征字,后面是实体尾缀,不合并
                if pseg[2] & {types.NS, types.NN, types.NA, types.NZ, types.NU}:
                    return True  # 常规词性后出现村镇特征,可合并

            if ct in {'东', '西', '南', '北', }:
                if pseg[2] & {types.NS, types.NM} or (len(pt) >= 3 and pt[-1] in std_ns_tails):
                    return True  # 较长地名后面出现方向特征,合并
                if pseg[2] & {types.NN, types.NA, types.NZ}:
                    return False  # 常规词性后出现方位特征,不合并

            if ct in {'前', '后', '旁', '外', '内', '门前'}:
                if len(pt) >= 3 and pt[-1] in std_ns_tails:
                    return False  # 较长地名后面出现方位特征,不合并
                if pseg[2] & {types.NS, types.NM, types.NO}:
                    return True  # 组织词性后出现方位特征,合并

            return False  # 默认不允许合并

        area0_chars = {'县', '乡', '镇', '村', '屯', '路', '街', '道', '港'}  # 区以下地域特征尾缀
        areas_chars = {'新', '老', '小', '省', '市', '区', '州', '盟', '县', '乡', '镇', '村', }  # 地域特征字
        area1_chars = {'新', '老', '大', '小', '上', '下', '前', '后', '东', '西', '南', '北'}  # 乡村名称前置特征字

        def _is_tag(b, e, tag):
            """判断给定范围的文本是否为指定的词性类型"""
            word = line_txt[b:e]
            mres = matcher.do_check(word, mode=mac.mode_t.max_match)
            if not mres:
                return False
            return mres[-1][2] & tag

        def rec_merge(pseg, seg, idx, nseg):
            """基于当前分段索引idx和分段信息seg,以及前段信息pseg,尝试进行分段合并(相交合并与紧邻合并)"""
            pchar = line_txt[pseg[0]]
            if pseg[1] > seg[0]:
                # 前后两段相交
                if pseg[1] - seg[0] == 1:  # 前后单字交叉
                    if seg[2] & {types.NO, types.NM}:
                        # 前段剩余单字且为前缀单字, 后段为特定尾缀, 合并: "市人|人民医院" 或 "芒市|市委"
                        if (seg[0] - pseg[0] == 1 and pchar in areas_chars) or line_txt[seg[0]] in areas_chars:
                            rst[-1] = (pseg[0], seg[1], seg[2])
                            return True

                    if pseg[2] & {types.NO, types.NM, types.NB}:
                        return False  # 编辑室|室室,相交时,进行切分

                    if pseg[2] & types.tags_NU and seg[2] & types.tags_NS and line_txt[seg[0]] in nnp.num_chars:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                        return True

                    if seg[0] - pseg[0] == 1:
                        if line_txt[seg[1] - 1] in area0_chars and not seg[2] & {types.NO, types.NM, types.NB}:
                            # 根据后缀,能构成典型地点名称的前后段,合并: "长江|江路"
                            rst[-1] = (pseg[0], seg[1], types.tags_NS)
                            return True

                        if pchar in area1_chars and pseg[2] & {types.NA, types.NN, types.NS} and types.NS in seg[2]:
                            # 根据前缀,能构成典型地点名称的前后段,合并: "老坊|坊子"
                            rst[-1] = (pseg[0], seg[1], types.tags_NS)
                            return True

                score = nnp.tree_paths_t.score(pseg, seg, line_txt)
                if score[1] == 0:
                    typ = seg[2] if not seg[2] & types.tags_NU else pseg[2]
                    rst[-1] = (pseg[0], seg[1], typ)  # 与路径分析保持一致,前后交叉且不扣分,则合并
                    return True

                if pseg[2] & {types.NN, types.NA} and seg[2] & {types.NN, types.NA}:
                    if line_txt[seg[1] - 1] in area0_chars:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)
                    else:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                    return True  # 前后交叉,且为特定类型,合并: "百家|家幸"

                if pseg[2] & {types.NS, types.NZ, types.NH} and seg[2] & {types.NS, types.NN, types.NA}:
                    if line_txt[seg[1] - 1] in area0_chars and line_txt[seg[1] - 2] not in area0_chars:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 特定模式,合并"凉山|山村",但不合并"李沟村|村村"
                        return True

                if pseg[2] & {types.NS} and seg[2] & {types.NS, types.NN, types.NA}:
                    if line_txt[seg[0]] in area0_chars and line_txt[seg[0]:seg[1]] in {'镇中', '镇内'}:
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 特定模式,"太平镇|镇中"合并
                        return True

                if pseg[2] & {types.NU, types.NA} and seg[2] & {types.NU, types.NA}:
                    typ = seg[2] if not seg[2] & types.tags_NU else pseg[2]
                    rst[-1] = (pseg[0], seg[1], typ)
                    return True  # 前后交叉,且为特定序号类型,合并

                if not seg[2] & {types.NM, types.NO, types.NB}:
                    tseg = (pseg[1], seg[1], seg[2])  # 尝试基于交叉的剩余分段进行地名合并分析
                    if can_combi_NS(pseg, tseg, line_txt, nseg):
                        rst[-1] = (pseg[0], seg[1], types.tags_NS)
                        return True

            elif pseg[1] == seg[0]:  # 前后两段紧邻
                if {types.NB, types.NO, types.NM}.isdisjoint(pseg[2]) and seg[2].issuperset(types.tags_NL):
                    seg = segs[idx] = (seg[0], seg[1], {types.NM, types.NL})  # 孤立出现的尾缀NL要当作NM,如:深圳市投控东海一期基金(有限合伙)
                    rst.append(seg)
                    return True

                if can_combi_NS(pseg, seg, line_txt, nseg):
                    rst[-1] = (pseg[0], seg[1], types.tags_NS)  # 进行NS地名合并
                    return True

                if pseg[2] & types.tags_NU and seg[2] & {types.NS, types.NB} and line_txt[seg[0]] in nnp.num_chars and _is_tag(seg[0] - 1, seg[0] + 1, types.tags_NU):
                    rst[-1] = (pseg[0], seg[1], seg[2])
                    return True

                if pseg[1] - pseg[0] == 1 and pchar in area1_chars and pseg[2] & {types.NA, types.NN, } and types.NS in seg[2]:
                    # 根据前缀,能构成典型地点名称的前后段,合并: "老|坊子"
                    rst[-1] = (pseg[0], seg[1], types.tags_NS)
                    return True

                if pseg[2] & seg[2] & types.tags_NU:
                    rst[-1] = (pseg[0], seg[1], types.tags_NU)  # 相邻的NU直接合并
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

                if pseg[1] - pseg[0] == 1 and pchar in areas_chars and seg[2] & {types.NB, types.NO, types.NM, types.NS}:
                    rst[-1] = (pseg[0], seg[1], seg[2])
                    return True  # 特定前置单字连接特征尾缀,合并:村|卫生室

                if not merge_seg:
                    return False  # 不要求类型合并,则后面的合并分析不执行

                if pseg[1] - pseg[0] == 1:
                    if seg[1] - seg[0] == 2 and seg[2] & {types.NO, types.NM} and pchar in {'东', '南', '西', '北'}:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                        return True  # 扩大前后相连的特定单字前缀范围,合并:东|卫生室

                    if seg[2] & {types.NN, types.NA} and pchar in {'新'}:
                        rst[-1] = (pseg[0], seg[1], seg[2])
                        return True  # 前后相连的特定单字前缀

                if pseg[1] - pseg[0] <= 2 and seg[1] - seg[0] <= 2 and pseg[2] & {types.NU} and seg[2] & {types.NB}:
                    rst[-1] = (pseg[0], seg[1], seg[2])
                    return True  # 前后连接特定类型可合并

            return False

        def rec_cut(pseg, seg):
            """记录前后两个分段的交叉切分"""

            def adj_typ_NO(b, e, typ_nhit):
                """根据给定的分段范围与默认类型,进行特定分段类型的校正"""
                w = line_txt[b:e]
                if w in nnd.nt_tail_chars:  # {'矿', '店', '局'}:  # 需要进行NO/NS转换的单字
                    return types.tags_NO
                if w in nnp.num_chars:
                    return types.tags_NU

                if not matcher:
                    return nnd.nt_tail_datas.get(w, typ_nhit)

                mres = matcher.do_check(w, mode=mac.mode_t.max_match)
                if not mres or mu.slen(mres[-1]) != len(w):
                    return typ_nhit
                return mres[-1][2]

            if pseg[1] > seg[0]:
                if types.cmp(pseg[2], seg[2]) <= 0 or (pseg[2] & {types.NN, types.NH, types.NO, types.NU} and mu.slen(seg) > 2 and seg[2] & {types.NO}):
                    if pseg[1] - seg[0] >= 2 and seg[0] - pseg[0] == 1 and seg[1] - pseg[1] > 1 and {types.NM, types.NB, types.NO}.isdisjoint(seg[2]):
                        seg = (pseg[1], seg[1], seg[2])  # 前后相交大于两个字且前段切分后剩余单字,则调整后段
                    else:
                        typ = adj_typ_NO(pseg[0], seg[0], pseg[2])
                        if pseg[1] - seg[0] >= 2 and seg[0] - pseg[0] == 1 and seg[2] & {types.NO, types.NM} and pseg[2] & {types.NO} and mu.slen(pseg) >= 3 and mu.slen(seg) >= 3:
                            print(f"{line_txt[pseg[0]:pseg[1]]}@{line_txt[:pseg[0]]}|{line_txt[pseg[0]:seg[0]]}|{line_txt[seg[0]:seg[1]]}")
                        rst[-1] = (pseg[0], seg[0], typ)  # 后段重要,调整前段范围
                else:
                    if pseg[1] - seg[0] >= 2 and seg[1] - pseg[1] == 1 and seg[0] - pseg[0] > 1 and {types.NM, types.NB, types.NO}.isdisjoint(pseg[2]):
                        rst[-1] = (pseg[0], seg[0], pseg[2])  # 前后相交大于两个字且后段切分后剩余单字,则调整前段
                    else:
                        typ = adj_typ_NO(pseg[1], seg[1], seg[2])
                        seg = (pseg[1], seg[1], typ)  # 前段重要,调整后段范围

            # 在进行分段切割后,尝试进行最后两段的合并.
            if len(rst) >= 2 and rst[-2][1] == rst[-1][0]:
                p2seg = rst[-2]
                p1seg = rst[-1]
                p2len = p2seg[1] - p2seg[0]
                if p2len > 1 and can_combi_NS(p2seg, p1seg, line_txt):  # 在前一轮北切分剩余单字后,再次尝试 合并'|南京|路|'
                    rst[-2] = (p2seg[0], p1seg[1], types.tags_NS)  # 合并前面分段类型为NS
                    rst.pop(-1)
                elif p2len == 1 and types.NO in p1seg[2] and seg[2] & {types.NM, types.NB, types.NO}:
                    rst[-2] = (p2seg[0], p1seg[1], types.tags_NN)  # 合并前面分段类型为NN
                    rst.pop(-1)

            if seg[1] - seg[0] >= 2 and types.tags_NA.issubset(seg[2]) and line_txt[seg[1] - 2:seg[1]] in {'中店', '新店', '村店', '里店', '家店', '东店', '南店', '西店', '北店'}:
                seg = (seg[0], seg[1], types.tags_NO)  # 校正特殊店铺尾缀
            rst.append(seg)  # 记录后段信息

        # 对NER解析得到的分段进行交叉合并分析,得到最终结果
        segs_len = len(segs)
        rst.append(segs[0])
        for idx in range(1, segs_len):
            pseg = rst[-1]  # 输出的最后段
            seg = segs[idx]  # 待传输的当前段
            nseg = segs[idx + 1] if idx + 1 < segs_len else None  # 带输出的后段
            if not rec_merge(pseg, seg, idx, nseg):  # 先尝试前后段合并
                rec_cut(pseg, seg)  # 再进行前后段拼接或切分

        def _conv_H2S(segs, idx):
            """将NH类别的地名进行NS类别转化"""
            seg = segs[idx]
            if types.NH in seg[2]:
                name = line_txt[seg[0]:seg[1]]
                if name[-1] in {'区', '县', '乡', '镇', '村', '屯'}:
                    if len(name) == 3 and name[-2:] in {'社区', '园区', '景区', '街区', '禁区'}:
                        return seg
                    aname = cai.drop_area_tail(name)
                    if aname != name:
                        seg = segs[idx] = (seg[0], seg[1], types.tags_NS)
            return seg

        for i in range(len(rst)):
            _conv_H2S(rst, i)

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
                if pseg[1] - pseg[0] == 1 and line_txt[pseg[0]:pseg[1]] in nnp.num_cn:
                    pseg = rst[i - 1] = (pseg[0], pseg[1], types.tags_NU)
                else:
                    pseg = rst[i - 1] = (pseg[0], pseg[1], types.tags_NN)

            if seg[2] & {types.NA, types.NH}:
                if seg[1] - seg[0] == 1 and line_txt[seg[0]:seg[1]] in nnp.num_cn:
                    seg = rst[i] = (seg[0], seg[1], types.tags_NU)
                else:
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
    def _clean_drop(segs, txt):
        """匹配后再分析并删除分段列表segs中被包含且无接续的无效分段"""

        rc = 0
        pos = 0
        if segs and segs[0][0] == 1 and txt[0] in nnp.tree_paths_t.std_ns_tails:
            segs.insert(0, (0, 1, types.tags_NA))  # 填充开头空缺的区划特征字

        while pos < len(segs) - 1:
            pseg = None if pos == 0 else segs[pos - 1]
            seg = segs[pos]
            nseg = segs[pos + 1]

            if nseg[0] - seg[1] >= 1:  # 出现了分段的空白间隔
                xt = txt[seg[1]:nseg[0]]
                if xt[0] in nt_parser_t.att_chars:  # 在分段间隔处存在特定字符,则补充其分段
                    pos += 1
                    segs.insert(pos, (seg[1], nseg[0], types.tags_NA))
                    rc += 1
                    continue

                if len(xt) == 2 and xt[0] in {'(', "'"} and xt[1] in nt_parser_t.att_chars:  # 在分段间隔处存在特定字符,则补充其分段
                    pos += 1
                    segs.insert(pos, (seg[1] + 1, nseg[0], types.tags_NA))
                    rc += 1
                    continue

                if xt[0] in nnp.num_chars:  # 在分段间隔处存在数字字符,则补充其分段
                    pos += 1
                    segs.insert(pos, (seg[1], nseg[0], types.tags_NU))
                    rc += 1
                    continue

            if pseg and nseg[0] - pseg[1] == 1 and pseg[2] & {types.NM, types.NB, types.NO, types.NZ, types.NH, types.NS}:
                # 前中后三个分段,前后间隔是特殊字,则补充其单字分段
                if txt[pseg[1]] in nt_parser_t.att_chars and seg[1] - seg[0] == 2 and seg[2] & {types.NA, types.NN, }:
                    segs.insert(pos + 1, (pseg[1], nseg[0], types.tags_NA))
                    rc += 1
                    pos += 1
                    continue

            if pos == 0 and txt[seg[0]] in nnp.tree_paths_t.std_ns_tails:  # 特殊区划特征字开头,补充其单字分段
                segs.insert(pos, (seg[0], seg[0] + 1, types.tags_NA))
                rc += 1
                pos += 1
                continue

            if nseg[0] == seg[0]:
                # seg被nseg左贴包含,判断右侧是否有粘连
                if seg[1] < nseg[1] and types.NA not in nseg[2] and not nnp.find_right(segs, seg, pos + 2):
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

            if pseg and pseg[0] == seg[0] and seg[2] & {types.NM, types.NO, types.NB}:
                # 发电|发电厂|厂,判断前后两个词是否可以被丢弃
                drop_pseg = drop_nseg = False
                if pseg[1] == nseg[0] and nseg[1] == seg[1]:  # pseg+nseg=seg
                    if not nnp.find_left(segs, nseg, pos - 2):
                        drop_nseg = True  # 如果nseg在前面没有被碰触,则丢弃
                    if not nnp.find_right(segs, pseg, pos + 2):
                        drop_pseg = True  # 如果pseg在后面没有被碰触,则丢弃

                    if drop_nseg:
                        segs.pop(pos + 1)
                        rc += 1
                    if drop_pseg:
                        segs.pop(pos - 1)
                        rc += 1

                    if drop_nseg and drop_pseg:
                        pos -= 1
                        continue
                    if drop_nseg or drop_pseg:
                        continue

            if seg[1] >= nseg[0] and seg[2] & nseg[2] & {types.NU}:
                # 合并相邻或交叉的前后两个NU分段
                if pseg is None or pseg[2] & types.tags_NU or pseg[1] <= seg[0]:
                    segs.insert(pos + 1, (seg[0], nseg[1], types.tags_NU))
                    pos += 2
                    rc += 1
                    continue

            if pos:
                if pseg[1] == nseg[0] and pseg[0] < seg[0] and seg[1] < nseg[1] and not nseg[2] & {types.NU, types.NA}:  # seg被前后夹击覆盖
                    if not nnp.find_left(segs, seg, pos - 2) and not nnp.find_right(segs, seg, pos + 2):
                        segs.pop(pos)
                        rc += 1
                        continue

                if seg[1] == nseg[0] + 1 and txt[nseg[0]] == '门' and txt[nseg[0] - 1] in nnp.num_chars and nseg[2] & {types.NM, types.NO, types.NB} and seg[2] & {types.NS}:
                    # 尝试修正: "分社|一门|门市",变为:"分社|一|一门|门市"
                    if nnp.find_left(segs, seg, pos - 1, 4, tags={types.NM, types.NO, types.NB, types.NZ, types.NH, types.NS}):
                        segs.insert(pos, (seg[0], seg[0] + 1, types.tags_NU))
                        rc += 1
                        pos += 2
                        continue

            pos += 1

        return rc

    @staticmethod
    def _can_drop(txt, rst, seg):
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
                if seg[1] >= pseg[1] and seg[2] & pseg[2] & {types.NU}:
                    return True  # 新的NU包含之前的NU,丢弃前段

            if pseg[0] == seg[0]:  # 前后段起点相同
                if slen - plen >= 3 and seg[2] & {types.NM, types.NO, types.NB}:
                    return True  # 发电|发电机厂,丢弃前段
                if slen >= 5 and slen - plen >= 2 and seg[2] & {types.NZ, types.NS, types.NH}:
                    return True  # 特定长词,丢弃覆盖的前段
                if plen == 1 < slen and seg[2] & {types.NS} and txt[pseg[0]] not in nnp.num_chars:
                    return True  # 北|北京,丢弃前段
                if rstlen == 1 and plen == 1 and pseg[2] & {types.NO}:
                    return True  # 所|所苏,丢弃前段
                if slen > plen and seg[2] & pseg[2] & {types.NU} and txt[seg[1] - 1] in nnp.num_chars and nnp.find_left(rst, pseg, rstlen - 2, can_cross=True, tags={types.NU}):
                    return True  # 新的NU包含之前的NU,丢弃前段
                if slen >= 4 and plen == 3 and pseg[2] & {types.NM, types.NO, types.NB} and seg[2] & {types.NZ, types.NH} and txt[pseg[1] - 1] in {'科'}:
                    return True  # 管理科|管理科技,丢弃前段

            if seg[0] < pseg[0] and pseg[1] < seg[1]:
                if slen >= 6 and plen <= 4:
                    return True  # 长段包含短段,丢弃短段

            if seg[0] == pseg[1] - 1 and types.NZ in seg[2] and types.NB in pseg[2] and txt[pseg[0]] in nnp.num_chars and txt[seg[0]:seg[1]] in {'部队'}:
                return True  # 五部|部队,丢弃前分段

        if rstlen >= 2:
            fseg = rst[-2]
            flen = fseg[1] - fseg[0]

            if plen == 1:
                if fseg[0] < pseg[0] and fseg[1] == pseg[1]:
                    if not nnp.find_left(rst, pseg, rstlen - 2):
                        return True  # 右贴被包含的单字,左侧无粘连则丢弃
                    if types.NB in fseg[2] and types.NO in pseg[2] and seg[2] & {types.NZ} and txt[fseg[0]] in nnp.num_chars:
                        return True  # 9部|部|部队,丢弃中间的单字

            def _has_nu_ns_cross(seg):
                """判断seg是否与rst中的数字地名分段交叉"""
                if not seg[0] < pseg[1] < seg[1]:
                    return False
                if not nnp.is_num_str(txt[pseg[0]:pseg[1] - 1]) or not pseg[2] & {types.NS}:
                    return False
                if not seg[2] & {types.NS, types.NZ, types.NM, types.NO, types.NB}:
                    return False
                if plen >= 3:
                    return True
                elif plen == 2 and flen >= 3 and fseg[1] == pseg[1] and fseg[2] & {types.NS}:
                    return True
                return False

            def _find_lefts(segs, nidx, rngs, tags, steps=5):
                """在segs分段列表中从nidx向前查找rngs位置集是否存在tags类型分段"""
                if not segs:
                    return None
                end = max(-1, -1 if nidx == steps else nidx - steps)
                for i in range(nidx, end, -1):
                    seg = segs[i]
                    if (seg[0], seg[1]) in rngs and seg[2] & tags:
                        return i
                return None

            if _has_nu_ns_cross(seg):
                if _find_lefts(rst, rstlen - 2, {(pseg[1] - 4, pseg[1] - 1), (pseg[1] - 5, pseg[1] - 1), (pseg[1] - 6, pseg[1] - 1), (pseg[1] - 7, pseg[1] - 1)}, types.tags_NU) is not None:
                    return True  # 第二百三十一|第二百三十一连|连锁,丢弃中间段

            if fseg[0] == pseg[0] == seg[0] and fseg[1] < pseg[1] < seg[1] and flen == 1:
                rst.pop(-2)  # 东|东莞|东莞市,删除'东'
                return False

            if slen >= 3:
                if fseg[0] < pseg[0] < seg[0] and pseg[1] > seg[0] and fseg[1] == seg[0] and flen > 1:
                    if seg[2] & {types.NM, types.NS} and not nnp.find_left(rst, pseg, rstlen - 2) and plen <= slen:
                        return True  # 以当前长段为基准,丢弃前面的交叉分段pseg
                if flen >= 3 and fseg[1] - seg[0] >= 2 and fseg[1] - pseg[0] == 1 and pseg[1] < seg[1]:
                    return True  # 中小企业|业服|企业服务,丢弃中间分段
            if slen >= 5:
                if fseg[0] == seg[0] and fseg[0] < pseg[0] < seg[1] and fseg[1] <= pseg[1] < seg[1] and pseg[0] - seg[0] >= 2:
                    return True  # 中华|华人|中华人民共和国,丢弃中间分段

            if flen >= 3 and fseg[2] & {types.NM, types.NZ} and not pseg[2] & {types.NM, types.NO}:
                if fseg[0] < pseg[0] < fseg[1] and pseg[1] > fseg[1] and seg[0] == fseg[1] and not nnp.find_left(rst, pseg, rstlen - 2):
                    return True  # 以之前的长段为基准,丢弃后面的交叉分段pseg

            if (slen - plen >= 2 and seg[2] & {types.NS, types.NZ, types.NM, types.NH}) and seg[0] < pseg[1] and not pseg[2] & {types.NM, types.NO, types.NB, types.NZ}:
                pi = nnp.find_left(rst, seg, rstlen - 1)
                if 1 <= pi <= rstlen:
                    oseg = rst[rstlen - pi]  # 重要分段前面连接着特征尾缀
                    if oseg[1] - oseg[0] >= 2 and oseg[2] & {types.NM, types.NO, types.NB, types.NZ, types.NS} and not pseg[2] & {types.NZ, types.NH}:
                        return True  #
            if fseg[0] == seg[0] and slen - flen >= 2 and seg[2] & {types.NZ, types.NS} and txt[fseg[0]:fseg[1]] in {'中心'}:
                rst.pop(-2)  # 中心|中心城区,丢弃前段
                return False

            if slen >= 4 and seg[2] & {types.NS, types.NZ, types.NM, types.NO, types.NB}:
                def _drop(nidx, end, seg):
                    rc = 0
                    for i in range(nidx, end, -1):
                        tseg = rst[i]
                        tlen = tseg[1] - tseg[0]
                        if tseg[0] == seg[0]:
                            if tseg[1] == seg[1] - 1:
                                continue
                            if tseg[2] & {types.NN, types.NH, types.NA, types.NU}:
                                rst.pop(i)
                                rc += 1
                                continue
                        if tseg[0] < seg[0] and tseg[1] >= seg[0] + 2:
                            continue
                        if tseg[2] & {types.NN, types.NH, types.NA, types.NU}:
                            rst.pop(i)
                            rc += 1
                    return rc

                bpos = _find_lefts(rst, rstlen - 1, {(seg[0] - 4, seg[0]), (seg[0] - 5, seg[0]), (seg[0] - 6, seg[0])}, {types.NS, types.NZ, types.NM, types.NO, types.NB})
                if bpos is not None and _drop(rstlen - 1, bpos, seg):
                    return False  # '人民政府|城乡建设|总规划师',长段相邻时,丢弃中间的小段.

        if rstlen >= 3:
            f3 = rst[-3]
            f2 = rst[-2]
            f1 = rst[-1]

            if seg[1] - seg[0] == 1 and types.tags_NO.issubset(seg[2]):
                if f3[1] == seg[0] and f3[0] == f2[0] and seg[1] == f2[1] == f1[1] and types.tags_NA.issubset(f2[2]) and not nnp.find_left(rst, seg, rstlen - 4):
                    rst.pop(-2)
                    return False  # S:东方|A:东方店|A:方店|O:店 不记录中间的A分段

        return False

    @staticmethod
    def _can_rec(txt, rst, seg):
        city_tails = {'省', '市', '区', '县', '乡', '镇', '村', '州', '旗', '街', '路', '道'}
        rstlen = len(rst)
        slen = seg[1] - seg[0]
        if rstlen >= 3:
            f3 = rst[-3]
            f2 = rst[-2]
            f1 = rst[-1]

            if slen == 1:
                if f3[1] == seg[0] and f3[0] == f2[0] and seg[1] == f2[1] == f1[1] and not nnp.find_left(rst, seg, rstlen - 4):
                    return False  # Z:小吃|O:小吃店|O:吃店|O:店 不记录最后的单字

                if f3[1] == f2[1] == f1[1] == seg[1] and not nnp.find_left(rst, seg, rstlen - 4):
                    return False  # O:发电机厂|O:电机厂|O:机厂|O:厂 不记录最后的单字

        if rstlen >= 2:
            fseg = rst[-2]
            pseg = rst[-1]
            flen = fseg[1] - fseg[0]
            plen = pseg[1] - pseg[0]
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

            if fseg[1] - 1 == seg[0] and flen >= 3 and fseg[2] & {types.NO, types.NM, types.NB} and seg[2] & types.tags_NA and txt[seg[1] - 1] in {'和'}:
                return False  # MOB与NA又相交,丢弃NA

        if rstlen:
            pseg = rst[-1]
            plen = pseg[1] - pseg[0]
            if plen >= 3:
                if seg[1] == pseg[1] and seg[0] > pseg[0] and pseg[2] & {types.NO, types.NM, types.NB} and seg[2] & types.tags_NA:
                    return False  # 被NO/NM/NB右包含的NA不记录
                if seg[1] == pseg[1] and slen == 1 and pseg[2] & types.tags_NS and seg[2] & types.tags_NA and txt[seg[0]] in city_tails:
                    return False  # 上海|上海市|市,不记录最后的单字
                if seg[0] - pseg[0] >= 2 and seg[1] <= pseg[1] and seg[2] & pseg[2] & {types.NM, types.NO}:
                    if not nnp.find_left(rst, seg, rstlen - 2):  # 有限责任公司|责任公司|公司,丢弃后两个,如果与前面无粘连
                        return False

            if seg[0] == pseg[1] - 1 and slen == 2 and plen > 1 and seg[2] & {types.NA, types.NN} and txt[seg[1] - 1] in nnp.num_chars:
                if pseg[2] & {types.NO, types.NM, types.NB, types.NZ}:
                    rst.append(seg)
                    rst.append((seg[1] - 1, seg[1], types.tags_NU))  # 与NO/NM/NB左相交的双字特定NA/NN,额外记录单独的数字部分
                    return False

            if seg[0] >= pseg[0] and seg[1] <= pseg[1] and seg[2] & pseg[2] & {types.NU}:
                return False  # 当前段被前段包含,且均为NU,则当前段不记录
            if pseg[0] < seg[0] and pseg[1] - seg[0] >= 2 and types.NU in pseg[2] and seg[2] & {types.NA, types.NS}:
                rst.append((pseg[0], seg[1], seg[2]))  # 有交叉的NU&(NA,NS),则合并生成新段
                return True
            if pseg[0] < seg[0] == pseg[1] - 1 and pseg[2] & {types.NN, types.NA} and types.NU in seg[2] and txt[seg[0]] in nnp.num_chars:
                rst.append((pseg[0], seg[1], types.tags_NA))  # 有交叉的(NA,NN)&NU,则合并生成新段
                return True

            if slen == 1 and seg[1] == pseg[1]:
                if pseg[2] & {types.NM, types.NO, types.NB} and txt[seg[0]] in {'市'}:
                    return False  # 不记录 '超市/门市' 末尾的单字
                if pseg[2] & {types.NM, types.NO, types.NB} and seg[2] & {types.NO}:
                    if not nnp.find_left(rst, seg, rstlen - 2):
                        return False  # 不记录 '医院/院' 末尾的单字
        return True

    def split(self, txt, mres=None, pres=None, fp_dbg=None, nres=None):
        '''在txt中拆分可能的组份段落
            mres - 记录参与匹配的原始词汇列表
            pres - 记录预处理后的词汇列表
            nres - 记录最佳路径结果词汇列表
            返回值:分段列表nres,含有待处理的交叉分段
                [(b,e,{types})]
        '''

        def rec_ex(rst, pos, node, root):
            """保留分段匹配结果"""

            def rec_node_seg(node):
                """记录当前节点对应的匹配分段到结果列表"""
                if node is root:
                    return
                # 当前待记录的新匹配分段
                seg = pos - node.words, pos, node.end
                if mres is not None:
                    mres.append(seg)
                if seg[2] == types.tags_NP:
                    return  # 占位记号不参与后续匹配
                while rst and self._can_drop(txt, rst, seg):
                    rst.pop(-1)  # 回溯,逐一踢掉旧结果
                if self._can_rec(txt, rst, seg):
                    rst.append(seg)

            # 逐一记录所有可能的匹配节点
            vnodes = node.get_fails()
            for node in reversed(vnodes):
                rec_node_seg(node.first)

        # 按词典进行完全匹配
        segs = self.matcher.do_check(txt, mode=rec_ex)
        self._clean_drop(segs, txt)  # 进行无效匹配结果的丢弃
        if pres is not None and isinstance(pres, list):
            pres.extend(segs)  # 记录预处理后的结果

        # 根据匹配结果查找最佳nt路径
        nres = nnp.find_nt_paths(txt, segs, fp_dbg, nres)
        self._merge_bracket(nres, txt)  # 合并附加括号
        return nres

    def parse(self, txt, nres=None, merge_seg=True, rst=None):
        '''根据split拆分结果nres和txt,解析最终的分段结果.
            merge_seg - 告知是否合并同类分段
            rst - 补全空洞后的完整分段列表
            返回值:(分段列表[(b,e,{types})],分段关系列表[(pseg,rl,nseg,cr)])
        '''
        if not txt:
            return [], []
        if nres is None:
            nres = self.split(txt)

        rlst, clst = self._tidy_segs(self.matcher, nres, merge_seg, txt)  # 进行合并整理
        if rst is None:
            rst = rlst
        else:
            mu.complete_segs(rlst, len(txt), True, rst)  # 补全中间的空洞分段

        return rst, clst
