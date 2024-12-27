import match_ac as mac
import uni_blocks as ub
import html_strip as hs
import match_util as mu
import re

"""
    轻量级停用词处理引擎,可基于停用词规则列表进行文本短句的切分,便于进行NER识别或校验.
"""

# 名字分隔符归一化
SEP_NAMES = {'·': '.', '°': '.', '—': '.', '━': '.', '．': '.', '－': '.', '•': '.', '-': '.', '・': '.', '_': '.', '▪': '.', '▁': '.', '/': '.', '／': '.', '‧': '.',
             '\\': '.', '"': "'", '●': '.', '[': '(', ']': ')', '{': '(', '}': ')', '―': '.', '─': '.', '､': '、', '￮': '0', '﹢': '+', '﹒': '.', 'ˉ': '.'}


def ner_chars_clean(txt, with_sbc=True):
    """对文本中特定字符进行必要的处理转换,但不应改变文本长度和位置"""
    if with_sbc:
        txt = ub.sbccase_to_ascii_str2(txt, True, True)
    txt = ub.char_replace(txt, SEP_NAMES).upper()
    return txt


# 用于NER分句的符号,不应含有"#&.@";
SEP_CHARS = {'\n', '！', '？', '￥', '%', '，', '。', '|', '!', '?', '$', '%', ',', '\\', '`', '~', ':', '丶', '：', ';', '；', '*', '\u200b', '\uf0d8', '\ufeff'}
SEP_CHARS.add('、')  # '、'顿号也偶尔出现在NT名称中,但更频繁出现在原文中,所以暂时先放弃名字中的作用,也用于分句.


def tiny_text_split(txt, skip_front=True):
    """对txt进行简单分行处理,返回值:[(b,e,tag)],[line]"""
    segs = []
    strs = []
    pos = 0
    for i, c in enumerate(txt):
        if c in SEP_CHARS:
            if pos != i:
                segs.append((pos, i, None))
                strs.append(txt[pos:i])

            segs.append((i, i + 1, c))
            strs.append(c)
            pos = i + 1

    if pos != len(txt):
        segs.append((pos, len(txt), None))
        strs.append(txt[pos:])

    if skip_front:  # 跳过每行首部的章节号
        i = 0
        while i < len(segs):
            seg = segs[i]
            line = strs[i]
            if len(line) <= 3:
                i += 1
                continue
            sk = ub.skip_front(line)
            if not sk:
                i += 1
                continue
            strs[i] = line[:sk]
            segs[i] = (seg[0], seg[0] + sk, strs[i])
            strs.insert(i + 1, line[sk:])
            segs.insert(i + 1, (seg[0] + sk, seg[1], seg[2]))
            i += 1

    return segs, strs


def wild_parse(line, tostr=None):
    """解析分段规则,返回用于匹配器使用的结果.
        组合拼接,解析'{A|B@C|D@E|F}',返回:['ACE', 'ACF', 'ADE', 'ADF', 'BCE', 'BCF', 'BDE', 'BDF']
        组合跨越,解析'{A|B*C|D}',返回:[('A','C'),('A','D'),('B','C'),('B','D')]
        扩展跨越,解析'{A|B`正则表达式`C|D}',返回:[('A','C'),('A','D'),('B','C'),('B','D')],正则表达式
        格式不符返回:None
        当组合拼接的最后有叹号的时候'{..@..}!',会给每个组合结果都带上最后的叹号.
        tostr is None 默认模式,只有@分组才会返回字符串;
        tostr is True 强制模式,返回字符串列表.
        tostr is False禁止转换,返回tuple组合列表
    """
    if not line or len(line) < 5:
        return None
    if line[0] != '{' or (line[-1] != '}' and line[-2:] != '}!'):
        return None

    # 先进行扩展跨越的预处理,得到校验所需的正则表达式,并将其降级为组合跨越模式
    exts = re.findall(r'`(.+?)`', line)
    if exts:
        line = re.sub(r'`.+?`', '*', line)

    exclmark = None
    if line[-2:] == '}!':
        exclmark = '!'
        line = line[:-1]

    mpos = line.find('@')
    if mpos == -1:
        mpos = line.find('*')
        if exclmark and mpos > 0:
            return None  # 星号规则不允许有叹号尾缀
    if mpos == -1:
        return None

    sep = line[mpos]  # 得到分组的分隔符
    grps = line[1:-1].split(sep)  # 根据分隔符@或*进行分组拆分
    for i in range(len(grps)):
        grps[i] = grps[i].split('|')  # 对每个分组进行组合拆分

    rst = []

    # 进行多级排列组合,得到返回结果
    def loop(res, node):
        res.append(node)  # 利用当前组合结果list当作stack,其长度代表递归深度.
        deep = len(res)  # 得到递归深度
        if deep >= len(grps):
            comb = tuple(res) if exclmark is None else tuple(res + ['!'])
            rst.append(comb)  # 当前是最深层了,记录本轮组合结果
            res.pop(-1)
            return
        # 继续深度递归下一层
        for n in grps[deep]:
            loop(res, n)
        res.pop(-1)

    for node in grps[0]:
        res = []
        loop(res, node)  # 从首层开始深度递归,构造全部的组合结果

    # 进行后处理得到返回结果
    if (tostr is None and sep == '@') or tostr:
        for i in range(len(rst)):
            rst[i] = ''.join(rst[i])

    if exts:
        return rst, exts[0]
    else:
        return rst


class word_spliter_t:
    """基于ac匹配树的文本分隔器.
        以绑定的关键词集合进行分段切分,如果关键词以'!'结尾则进行修复连接或不切分.
    """

    def __init__(self):
        self.matcher = mac.ac_match_t()

    def dict_add(self, line):
        if not line or line[0] == '#':
            return None, None
        if len(line) > 1 and line[-1] == '!':
            return self.matcher.dict_add(line[:-1], line[-1], strip=False)  # 特殊匹配模式
        else:
            return self.matcher.dict_add(line, strip=False)  # 分段匹配模式

    def dict_end(self):
        self.matcher.dict_end()

    def clear(self):
        self.matcher.clear()

    def match(self, txt):
        """对txt进行内部词表的匹配.返回值:[(begin,end,val)],val is None对应未匹配部分"""
        segs = self.matcher.do_match(txt, mode=mac.mode_t.merge_cross)
        return segs if segs else [(0, len(txt), None)]

    def split(self, txt, with_space=' '):
        """基于绑定的词表对txt进行分段.
            返回值:分段列表[b,e,tag],结果串列表[子串]
        """
        rst = []
        mres = self.match(txt)

        segs = []

        def rec_merge(seg):
            if rst:
                segs.append((segs.pop(-1)[0], seg[1], None))
                t = rst.pop(-1) + txt[seg[0]:seg[1]]
                rst.append(t)
            else:
                segs.append(seg)
                rst.append(txt[seg[0]:seg[1]])

        attach = False
        for seg in mres:
            if seg[2] == '!':  # 如果遇到特殊匹配
                rec_merge(seg)  # 合并记录当前与前一段的拼装
                attach = True  # 设置附加状态
            elif attach:  # 如果要求附加连接
                if seg[2] in {None, '!'}:  # 且当前不是分段匹配
                    rec_merge(seg)  # 合并记录当前与前一段的拼装
                attach = seg[2] == '!'  # 更新附加状态,可能继续附加
            elif seg[2] is None:  # 当前就是普通分段
                rst.append(txt[seg[0]:seg[1]])
                segs.append(seg)
            else:
                if with_space is not None:
                    rst.append(with_space * (seg[1] - seg[0]))  # 占位的无用分段.
                segs.append(seg)
        return segs, rst


def split_by_strs(txt, strs, outstrs=False):
    """用strs串列表拆分txt.
        outstrs 为 True:
            返回值:[分段字符串]
        outstrs 为 False:
            返回值:[(begin,end,val)],val is None对应未匹配部分
    """
    match = word_spliter_t()
    for s in strs:
        match.dict_add(s)
    match.dict_end()

    if outstrs:
        return match.split(txt, None)[1]
    else:
        return match.match(txt)


class wild_spliter_t:
    """基于ac匹配树的规则列表分隔器.
        以绑定的组合规则进行分段切分.
    """

    def __init__(self):
        self.matcher = mac.ac_match_t()
        self.pairs = {}  # 记录所有的双词组合,映射到组号

    def dict_add(self, strs, exres=None):
        """添加双词列表strs和对应的扩展re表达式."""
        assert (len(strs) == 2)
        grpno = len(self.pairs)  # 用当前已有数量作为新的组号
        self.pairs[grpno] = (strs, exres)  # 绑定组号与对应词列表
        for s in strs:  # 装载词汇并绑定对应组号集合
            self.matcher.dict_add(s, {grpno}, force=True)

    def rule_add(self, rule):
        """直接添加匹配规则"""
        wp = wild_parse(rule)
        if wp is None:
            return False
        if isinstance(wp, tuple):
            for pair in wp[0]:
                self.dict_add(pair, wp[1])
        else:
            for pair in wp:
                self.dict_add(pair)
        return True

    def dict_end(self):
        self.matcher.dict_end()

    def clear(self):
        self.matcher.clear()
        self.pairs.clear()

    def match(self, txt):
        """对txt进行内部词表的匹配.返回值:[(begin,end,val)],val is None对应未匹配部分"""
        rsegs = self.matcher.do_match(txt, mode=mac.mode_t.max_match)
        segs = []
        grps = {}
        for seg in rsegs:  # 先统计各分组匹配情况,同时进行原始匹配结果的克隆,避免污染元数据
            segs.append((seg[0], seg[1], set(seg[2]) if seg[2] else None))
            if seg[2] is None:
                continue
            for gn in seg[2]:
                if gn not in grps:
                    grps[gn] = []
                grps[gn].append((seg[0], seg[1], txt[seg[0]:seg[1]]))  # 记录每个匹配的对应值顺序到组号列表中
        if not grps:
            return [(0, len(txt), None)]

        def equ(pairs, grp):
            """比较预先配置的双词和动态匹配的分组是否相同"""
            l1 = pairs[0]
            if len(l1) != len(grp):
                return False
            for i, v in enumerate(l1):
                if v != grp[i][2]:
                    return False
            if pairs[1] and not re.fullmatch(pairs[1], txt[grp[0][1]:grp[1][0]]):
                return False  # 要求进行双词中间部分的正则匹配

            return True

        # 判断匹配结果是否符合预先登记的分组词汇列表
        for gn in grps:
            if not equ(self.pairs[gn], grps[gn]):
                grps[gn].append(None)  # 不是完全匹配的分组则标记不使用

        for i in range(len(segs)):
            seg = segs[i]
            if seg[2] is None:
                continue
            for gn in list(seg[2]):  # 逐一回溯处理,剔除匹配不成功的分段标记
                if grps[gn][-1] is None:
                    seg[2].remove(gn)
            if not seg[2]:
                segs[i] = (seg[0], seg[1], None)  # 校正匹配结果

        # 需要重新合并之前部分匹配后又被撤销的分段.
        i = 1
        while i < len(segs):
            if segs[i - 1][2] is None and segs[i][2] is None:
                segs[i - 1] = (segs[i - 1][0], segs[i][1], None)
                segs.pop(i)
            else:
                i += 1
        return segs

    def split(self, txt, with_space=' '):
        """基于绑定的词表对txt进行分段.返回值:[分段字符串,...]"""
        rst = []
        segs = self.match(txt)
        for seg in segs:
            if seg[2] is None:
                rst.append(txt[seg[0]:seg[1]])
            elif with_space is not None:
                rst.append(with_space * (seg[1] - seg[0]))
        return segs, rst


def split_by_wild(txt, strs, outstrs=False):
    """用wild串列表拆分txt.
        outstrs 为 True:
            返回值:[分段字符串]
        outstrs 为 False:
            返回值:[(begin,end,val)],val is None对应未匹配部分
    """
    match = wild_spliter_t()
    for s in strs:
        match.rule_add(s)
    match.dict_end()

    if outstrs:
        return match.split(txt, None)[1]
    else:
        return match.match(txt)


class text_spliter_t:
    """文本复合分割器."""

    def __init__(self):
        self.wild_spliter = wild_spliter_t()
        self.word_spliter = word_spliter_t()

    def load(self, fname, isend=True, encoding='utf-8'):
        """装载规则文件.返回值:''正常,其他为错误信息."""
        self.wild_spliter.clear()
        self.word_spliter.clear()
        try:
            rules = {}  # 进行重复性检查,记录所有装载过的规则

            def chk(word, line, lineno):
                if word not in rules:
                    rules[word] = line
                else:
                    print(f'<{fname}|{lineno:>8},{len(line):>2}>: spliter RULE is repeat: {word} at "{line}" and {rules[word]}')

            with open(fname, 'r', encoding=encoding) as f:
                for i, line in enumerate(f.readlines()):
                    txt = line.strip()
                    if not txt or txt[0] == '#':
                        continue

                    if txt[0] == '{':
                        wprules = wild_parse(txt)  # 特殊规则格式,进行解析后再添加
                        if wprules is None or not isinstance(wprules, (tuple, list)):
                            print(f'spliter RULE is bad: {txt}')
                            continue

                        if isinstance(wprules, tuple):  # 扩展跨越
                            for segs in wprules[0]:
                                chk('/'.join(segs), txt, i)
                                self.wild_spliter.dict_add(segs, wprules[1])
                        elif isinstance(wprules[0], tuple):  # 组合跨越
                            for segs in wprules:
                                chk('/'.join(segs), txt, i)
                                self.wild_spliter.dict_add(segs)
                        elif isinstance(wprules[0], str):  # 组合拼接
                            for word in wprules:
                                chk(word, txt, i)
                                self.word_spliter.dict_add(word)

                    else:  # 普通格式,直接添加
                        chk(txt, txt, i)
                        self.word_spliter.dict_add(txt)
        except Exception as e:
            return str(e)

        if isend:
            self.wild_spliter.dict_end()
            self.word_spliter.dict_end()
        return ''

    def split0(self, txt, with_space=''):
        """对txt进行分段.返回值:[分段字符串,...]"""
        rst_strs = []
        rst_segs = []
        segs1, strs1 = self.word_spliter.split(txt, with_space)
        for seg in segs1:
            if seg[2] is None:
                s = txt[seg[0]:seg[1]]
                segs2, strs2 = self.wild_spliter.split(s, with_space)
                rst_strs.extend(strs2)
                for seg2 in segs2:
                    rst_segs.append((seg[0] + seg2[0], seg[0] + seg2[1], seg2[2]))
            else:
                rst_segs.append(seg)
        return rst_segs, rst_strs

    def split(self, txt, with_space=' '):
        """对txt进行分段.返回值:[分段字符串,...]"""
        rst_segs = []  # 最终返回的分割段列表
        rst_strs = []  # 分割段对应的字符串列表

        def adj_debar_match(segs, txt, strs):
            """尝试调整切割分段列表中出现的跨段且需保护的部分,比如'{关于*的}'不能破坏'关于它的!'"""

            def find_next(b, ids):
                """从segs的b开始,查找含有相同ids的分段,返回其下标"""
                for i in range(b, len(segs)):
                    if segs[i][2] and segs[i][2] & ids:
                        return i
                return None

            mods = 0

            pos = 0
            while pos < len(segs):
                cseg = segs[pos]
                if cseg[2] is None:
                    pos += 1
                    continue
                next = find_next(pos + 1, cseg[2])  # 遇到跨段匹配的分段了,则尝试查找对应的下一段
                if next is None:
                    return  # 找不到就结束了
                nseg = segs[next]
                # 对找到的跨段内容进行排除测试
                st = txt[cseg[0]:nseg[1]]
                mres = self.word_spliter.matcher.do_check(st, mode=mac.mode_t.max_match)
                if not mres or mres[-1][2] != '!':  # 无命中则继续检查后续段
                    pos += 1
                    continue
                # 命中排除分段了,则将对应分段删除并合并
                for i in range(next - pos):
                    segs.pop(pos)
                segs[pos] = (cseg[0], nseg[1], None)
                pos += 1
                mods += 1

            if not mods:
                return  # 未修改过,直接返回

            strs.clear()
            # 需要检查排除处理后是否存在需要重新合并的未匹配分段
            pos = 0
            while pos < len(segs) - 1:
                cseg = segs[pos]
                if cseg[2] is not None:
                    pos += 1
                    strs.append(with_space * (cseg[1] - cseg[0]))  # 重构被丢弃的文本串为对应长度的空白串
                    continue

                nseg = segs[pos + 1]
                if nseg[2] is not None:
                    pos += 1
                    strs.append(txt[cseg[0]:cseg[1]])  # 记录上一个有效分段字符串
                    continue

                # 更新或记录新的合并字符串
                if not strs:
                    strs.append(txt[cseg[0]:nseg[1]])
                else:
                    strs[pos] = txt[cseg[0]:nseg[1]]

                segs[pos] = (cseg[0], nseg[1], None)
                segs.pop(pos + 1)

        segs0, strs0 = tiny_text_split(txt)  # 按标点分割
        for i0, seg0 in enumerate(segs0):
            if seg0[2] is None and mu.slen(seg0) >= 3:  # 非标点分段
                # 进行跨段分割
                segs1, strs1 = self.wild_spliter.split(strs0[i0], with_space)
                adj_debar_match(segs1, strs0[i0], strs1)  # 进行规避校正

                for i1, seg1 in enumerate(segs1):
                    if seg1[2] is None and mu.slen(seg0) >= 3:  # 当前是跨段需保留的部分
                        # 进行停用词分割
                        segs2, strs2 = self.word_spliter.split(strs1[i1], with_space)
                        rst_strs.extend(strs2)
                        for i2, seg2 in enumerate(segs2):
                            rst_segs.append(mu.tran_seg(seg2, seg1[0] + seg0[0]))
                    else:
                        rst_segs.append(mu.tran_seg(seg1, seg0[0]))
                        rst_strs.append(strs1[i1])
            else:
                rst_segs.append(seg0)
                rst_strs.append(strs0[i0])

        return rst_segs, rst_strs


class html_spliter_t:
    """HTML文本清理分割器"""

    def __init__(self):
        self._html_cleaner = hs.html_stripper_t()  # HTML文本清理器
        self._text_spliter = text_spliter_t()  # 文本停用词拆分器
        self._pre_ac = mac.ac_match_t()  # 前处理替换器

    def load(self, rule_file, pre_file, encoding='utf-16'):
        """装载规则文件.
            rule_file - 停用词拆分规则
            pre_file - 前处理替换规则
            返回值:空串正常,否则为错误信息.
        """
        err = self._text_spliter.load(rule_file, encoding=encoding)
        if err:
            return f'html_spliter_t._text_spliter.load() fail: {rule_file}'
        self._pre_ac.clear()
        _, err = self._pre_ac.dict_load(pre_file, encoding=encoding)
        if err:
            return f'html_spliter_t._pre_ac.load() fail: {pre_file}'
        return ''

    def split(self, txt):
        """对文本进行完整的预处理并进行停用词分段处理"""
        rt = self._html_cleaner.proc(txt)  # 初步预处理后丢弃HTML标签的文本内容
        st = ub.sbccase_to_ascii_str2(rt, True, True)  # 进行半角归一化,得到临时断句使用的文本内容
        st1 = self._pre_ac.do_filter(st)  # 进行额外的前置替换,规避含有断句字符的有效内容(在前处理规则文件中统一使用半角归一化字符即可)
        segs, strs = self._text_spliter.split(st1, ' ')  # 进行断句拆分(在停用词规则文件中统一使用半角归一化字符即可)
        return rt, segs


class tails_checker_t:
    """尾缀检查器"""

    def __init__(self):
        self._ac = mac.ac_match_t()

    def load(self, rule_file, encoding='utf-16'):
        """装载匹配规则,返回值:错误信息"""
        _, err = self._ac.dict_load(rule_file, defval='.', sep='!', encoding=encoding)  # val is '.' 为尾缀匹配;val is '' 为完整匹配
        return err

    def match(self, name):
        """判断nt名称name是否匹配了无效尾缀,返回值:0-未命中;1-完整命中;2-尾缀命中"""
        mres = self._ac.do_check(name, mode=mac.mode_t.max_match)
        if not mres:
            return 0
        m = mres[-1]
        if m[2] == '.':
            return 2
        if mu.slen(m) == len(name):
            return 1
        return 0


if __name__ == "__main__":
    assert split_by_strs('0123456789', ['1', '34', '345!', '78'], True) == ['0', '23456', '9']
    assert split_by_wild('0123456789', ['{1*78}'], True) == ['0', '23456', '9']
    assert split_by_wild('0123456789', ['{1`\d+`78}'], True) == ['0', '23456', '9']
    assert split_by_wild('0123456789', ['{1`\d{1,4}`78}'], True) == ['0123456789']
