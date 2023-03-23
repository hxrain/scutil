'''
    基于HMM进行完整NER/NT功能实现,并提供一些相关工具.
    1 定义NT行业类型
    2 定义常见NT尾缀,并标注行业类型/常见扩展/排除词表
    3 提供NT名称校验功能,用于剔除无效名称
    4 提供NT组分处理功能,用于NER识别
    5 提供最终的NER/NT识别工具
'''
import re

import nlp_ner_hmm as nnh
import match_ac as mac
import match_util as mu
import china_area_id as ca
from inspect import isfunction
from nlp_ner_data import types, nt_tails
from copy import deepcopy
from collections.abc import Iterable


class nt_parser_t:
    '''NT特征解析器.
        与分词器类似,基于字典进行匹配;
        分词器需要给出尽量准确的分词结果,而本解析器则尽可能的对目标串进行组合覆盖,给出覆盖后的分段列表.
    '''
    tags_NM = {types.NM}  # 组织机构/后缀
    tags_NZ = {types.NZ}  # 专业名词
    tags_NN = {types.NN}  # 名称字号
    tags_ND = {types.ND}  # 用来规避NO单字匹配的词
    tags_NU = {types.NU}  # 数字序号
    tags_NO = {types.NO}  # 单独尾字
    tags_NS = {types.NS}  # 地域名称
    tags_NB = {types.NB}  # 分支机构
    tags_NS1 = {types.NS, types.NS1}
    tags_NS2 = {types.NS, types.NS2}
    tags_NS3 = {types.NS, types.NS3}
    tags_NS4 = {types.NS, types.NS4}
    tags_NS5 = {types.NS, types.NS5}
    tags_NS6 = {types.NS, types.NS6}
    tags_NS7 = {types.NS, types.NS7}

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
        (r'第?([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)([分号]*[小中厂店部亭号组校院馆台处师村团局园队所站区会厅库])(?![件河乡镇])', 1, __nu_nm.__func__),
        (r'([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)(分公司|公司)', 1, __nu_nm.__func__),
        (r'[第东南西北]*([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)(马路|路|弄|街|里|亩)', 1, __nu_ns.__func__),
        (r'第([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]+)', 1, __nu.__func__),
        (r'([O\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千仟]{2,})', 1, __nu.__func__),
    ]

    @staticmethod
    def nums(txt):
        """查找文本txt中出现的数字部分.返回值:[(b,e)]"""
        rst = []
        for pat in nt_parser_t.num_norm:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            for m in mres:
                span = m.span(pat[1])
                if span not in rst:
                    rst.append(span)
        return sorted(rst, key=lambda x: x)

    @staticmethod
    def query_nu(txt):
        """查询txt中的数字相关特征模式,返回值:[b,e,{types}]"""
        rst = []
        for pat in nt_parser_t.num_norm:
            mres = list(re.finditer(pat[0], txt))
            if not mres:
                continue
            pat[2](rst, mres)
        ret = sorted(rst, key=lambda x: x[0])
        return nt_parser_t.__merge_segs(ret)

    def __init__(self, inited=True):
        self._load_check_cb = None  # 检查词典回调输出函数
        self.matcher = mac.ac_match_t()  # 定义ac匹配树

        if inited:
            self.load_nt(isend=False)
            self.load_ns(isend=True)

    def __load(self, fname, tags, encode='utf-8', vals_cb=None):
        """装载词典文件fname并绑定数据标记tags,返回值:''正常,否则为错误信息."""
        try:
            row = -1
            with open(fname, 'r', encoding=encode) as fp:
                for line in fp:
                    row += 1
                    if not line:
                        continue
                    tag = tags(line) if isfunction(tags) else tags
                    txt = line[:-1] if line[-1] == '\n' else line
                    if vals_cb:
                        txt = vals_cb(txt)
                    ret = self.matcher.dict_add(txt, tag, force=True)
                    if self._load_check_cb is not None and ret is False:
                        b, e, ctag = self.matcher.do_check(txt)[0]
                        self._load_check_cb(fname, row, txt, tag, ctag.difference(tag))
            return ''
        except Exception as e:
            return e

    def load_nt(self, fname=None, encode='utf-8', isend=True, chk=False):
        """装载NT尾缀词典,返回值:''正常,否则为错误信息."""
        # 初始化构建匹配词表
        for k in nt_tails:
            data = nt_tails[k]
            assert '.' in data and '+' in data and '-' in data, data
            tags = data['.']
            exts = data['+']
            nobs = data['-']
            self.matcher.dict_add(k, tags, force=True)
            for e in exts:
                r = self.matcher.dict_add(e, tags, force=True)
                if chk and not r:
                    print(f'nt_parser_t.nt_tails+: {k}/{e} is repeat!')
            for b in nobs:
                r = self.matcher.dict_add(b, self.tags_ND, force=True)
                if chk and not r:
                    print(f'nt_parser_t.nt_tails-: {k}/{b} is repeat!')

        ret = self.__load(fname, self.tags_NM, encode) if fname else ''
        if isend:
            self.matcher.dict_end()
        return ret

    def load_ns(self, fname=None, encode='utf-8', isend=True, worlds=True):
        """装载NS尾缀词典,worlds告知是否开启全球主要地区.返回值:''正常,否则为错误信息."""
        lvls = {0: self.tags_NS, 1: self.tags_NS1, 2: self.tags_NS2, 3: self.tags_NS3, 4: self.tags_NS4, 5: self.tags_NS5, 6: self.tags_NS6}
        for id in ca.map_id_areas:  # 装入内置的行政区划名称
            alst = ca.map_id_areas[id]
            lvl = ca.query_aera_level(alst[0])  # 根据正式地名得到行政区划级别
            tags = lvls[lvl]
            for name in alst:
                self.matcher.dict_add(name, tags, force=True)
                aname = ca.drop_area_tail(name, {'省', '市', '区', '县', '州', '盟', '旗'})
                if name != aname:
                    self.matcher.dict_add(aname, tags, force=True)  # 特定尾缀地区名称,放入简称

        if worlds:
            for state in ca.map_worlds:  # 装入内置的世界主要国家与首都
                city = ca.map_worlds[state]
                self.matcher.dict_add(state, self.tags_NS, force=True)
                self.matcher.dict_add(city, self.tags_NS1, force=True)

            stats = ['亚太', '东北亚', '东亚', '北美', '环太平洋', '欧洲', '亚洲', '美洲', '非洲', '印度洋', '太平洋', '大西洋', '北欧', '东欧', '西欧', '中亚', '南亚','东南亚']
            for state in stats:
                self.matcher.dict_add(state, self.tags_NS, force=True)

        def ns_tags(line):
            """根据地名进行行政级别查询,返回对应的标记"""
            lvl = ca.query_aera_level(line)
            return lvls[lvl]

        ret = self.__load(fname, ns_tags, encode) if fname else ''
        if isend:
            self.matcher.dict_end()
        return ret

    def load_nz(self, fname, encode='utf-8', isend=True):
        """装载NZ尾缀词典,返回值:''正常,否则为错误信息."""
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
    def __merge_bracket(segs, txt):
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
    def __drop_nesting(segs, txt):
        """丢弃segs段落列表中被完全包含嵌套的部分,返回值:结果列表"""
        rst = []

        def chk(rst, seg):
            """检查并处理当前段在已记录结果中的重叠情况.返回值:是否记录当前段"""
            if types.equ(seg[2], types.ND):
                while rst:
                    r = mu.related_segs(rst[-1], seg)[0]
                    if r[1] in {'&', '@'} and types.equ(rst[-1][2], types.NO):
                        rst.pop(-1)  # 被坏词碰到的单尾字需要丢弃
                    else:
                        break
            else:
                while rst:
                    r = mu.related_segs(rst[-1], seg)[0]
                    if r in {'A@B', 'A=B'}:
                        return False  # 当前段被包含,不记录
                    elif r == 'B@A':
                        rst.pop(-1)  # 前一个段落被包含,丢弃
                    else:
                        break
            return True  # 默认情况,记录当前段

        for seg in segs:  # 对待记录的段落逐一进行检查
            if chk(rst, seg):
                rst.append(seg)  # 记录合法的段落
        return rst

    @staticmethod
    def __drop_crossing(segs):
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
    def __merge_segs(segs):
        '''合并segs段落列表中连续出现的相同组份,返回值:结果列表'''
        rst = []

        for seg in segs:
            if not rst:
                rst.append(seg)
                continue
            pseg = rst[-1]
            rl = mu.related_segs(pseg, seg)[0]
            if types.equ(pseg[2], seg[2]):  # 前后段落组份类型相同
                if rl in {'A+B', 'A@B', 'A&B'}:
                    pseg[2].update(seg[2])
                    rst.pop(-1)
                    rst.append((pseg[0], seg[1], pseg[2]))
                else:
                    rst.append(seg)
            else:
                if rl == 'A&B':  # 前后两段类型不同,但相交,按重要度进行保留
                    pt = types.type(pseg[2])
                    t = types.type(seg[2])
                    if pt < t:
                        rst[-1] = (pseg[0], seg[0], pseg[2])
                    else:
                        seg = (pseg[1], seg[1], seg[2])

                rst.append(seg)

        return rst

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

    def query(self, txt, merge=True):
        '''在txt中查找可能的组份段落,merge告知是否合并结果.返回值:[(b,e,{types})]或[]'''
        segs = self.matcher.do_check(txt)  # 按词典进行完全匹配
        mres = self.__merge_bracket(segs, txt)  # 合并附加括号
        if not mu.is_full_segs(mres, len(txt)):
            nums = self.query_nu(txt)  # 进行数字序号匹配
            if nums:
                self.__merge_nums(mres, nums)
        mres = self.__drop_nesting(mres, txt)  # 删除重叠嵌套
        self.__drop_crossing(mres)  # 删除交叉叠加的部分
        return self.__merge_segs(mres) if merge else mres

    def ends(self, txt, strict=True):
        '''查找txt中出现过的尾缀,strict指示是否严格尾部对齐.返回值:[(b,e,{types})]或[]'''
        mres = self.query(txt)
        if strict:
            while mres and mres[0][1] != len(txt):
                mres.pop(0)
        return mres

    def match(self, txt):
        '''判断给定的txt是否为完全匹配的已知尾缀.返回值:(b,e,{types})或None'''
        mres = self.query(txt)
        if not mres or mu.slen(mres[0]) != len(txt):
            return None
        return mres[0]
