import match_ac as mac
import uni_blocks as ub
import html_strip as hs

"""
    轻量级停用词处理引擎,可基于停用词规则列表进行文本短句的切分,便于进行NER识别或校验.
"""

# 名字分隔符归一化
SEP_NAMES = {'·': '.', '°': '.', '—': '.', '━': '.', '．': '.', '－': '.', '•': '.', '-': '.', '・': '.', '_': '.', '▪': '.', '▁': '.', '/': '.', '／': '.',
             '\\': '.', '"': "'", '●': '.', '[': '(', ']': ')', '{': '(', '}': ')', '―': '.', '─': '.'}


def ner_text_clean(txt, with_sbc=True):
    """对文本进行必要的处理转换,但不应改变文本长度和位置"""
    if with_sbc:
        txt = ub.sbccase_to_ascii_str2(txt, True, True)
    txt = ub.char_replace(txt, SEP_NAMES).upper()
    return txt


# 用于NER分句的符号,不应含有"#、&"
SEP_CHARS = {'\n', '！', '？', '￥', '%', '，', '。', '|', '!', '?', '$', '%', ',', '\\', '`', '~', ':', '丶', ' ', '：', ';', '；', '*', '\u200b', '\uf0d8', '\ufeff'}
SEP_CHARSTR = '[' + ''.join(SEP_CHARS) + ']'


def ner_text_split(txt):
    """对txt进行简单分行处理,返回值:[line]"""
    return re.split(SEP_CHARSTR, txt)


def wild_parse(line, tostr=None):
    """解析分段规则,返回用于匹配器使用的结果.
        组合拼接,解析'{A|B@C|D@E|F}',返回:['ACE', 'ACF', 'ADE', 'ADF', 'BCE', 'BCF', 'BDE', 'BDF']
        组合跨越,解析'{A|B*C|D}',返回:[('A','C'),('A','D'),('B','C'),('B','D')]
        格式不符返回:None
        当组合拼接的最后有叹号的时候'{..@..}!',会给每个组合结果都带上最后的叹号.
        tostr is None 默认模式,只有@分组才会返回字符串;
        tostr is True 强制模式,两类规则均会返回字符串.
        tostr is False禁止转换,两类规则均会返回原始tuple组合结果列表
    """
    if not line or len(line) < 5:
        return None
    if line[0] != '{' or (line[-1] != '}' and line[-2:] != '}!'):
        return None

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
                if with_space:
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
        return match.split(txt, '')[1]
    else:
        return match.match(txt)


class wild_spliter_t:
    """基于ac匹配树的规则列表分隔器.
        以绑定的组合规则进行分段切分.
    """

    def __init__(self):
        self.matcher = mac.ac_match_t()
        self.groups = {}

    def dict_add(self, segs):
        grpno = len(self.groups)  # 组号
        self.groups[grpno] = segs  # 绑定组号与对应词列表
        for s in segs:  # 装载词汇并绑定对应组号集合
            self.matcher.dict_add(s, {grpno})

    def dict_end(self):
        self.matcher.dict_end()

    def match(self, txt):
        """对txt进行内部词表的匹配.返回值:[(begin,end,val)],val is None对应未匹配部分"""
        segs = self.matcher.do_match(txt, mode=mac.mode_t.max_match)

        grps = {}
        for seg in segs:  # 先统计各分组匹配情况
            if seg[2] is None:
                continue
            for gn in seg[2]:
                if gn not in grps:
                    grps[gn] = []
                grps[gn].append(txt[seg[0]:seg[1]])  # 记录每个匹配的对应值顺序到组号列表中
        if not grps:
            return [(0, len(txt), None)]

        def equ(l1, l2):
            if len(l1) != len(l2):
                return False
            for i, v in enumerate(l1):
                if v != l2[i]:
                    return False
            return True

        # 判断各匹配是否完全符合之前的分组词汇列表
        for gn in grps:
            if not equ(self.groups[gn], grps[gn]):
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
            elif with_space:
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
        for segs in wild_parse(s):
            match.dict_add(segs)
    match.dict_end()

    if outstrs:
        return match.split(txt, '')[1]
    else:
        return match.match(txt)


class text_spliter_t:
    """文本复合分割器."""

    def __init__(self):
        self.wild_spliter = wild_spliter_t()
        self.word_spliter = word_spliter_t()

    def load(self, fname, isend=True, encoding='utf-8'):
        """装载规则文件.返回值:''正常,其他为错误信息."""
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
                        words = wild_parse(txt)  # 特殊规则格式,进行解析后再添加
                        if words is None:
                            print(f'spliter RULE is bad: {txt}')
                            continue
                        if isinstance(words[0], str):
                            for word in words:
                                chk(word, txt, i)
                                self.word_spliter.dict_add(word)
                        else:
                            for segs in words:
                                chk('/'.join(segs), txt, i)
                                self.wild_spliter.dict_add(segs)
                    else:  # 普通格式,直接添加
                        chk(txt, txt, i)
                        self.word_spliter.dict_add(txt)
        except Exception as e:
            return str(e)

        if isend:
            self.wild_spliter.dict_end()
            self.word_spliter.dict_end()
        return ''

    def split(self, txt, with_space=''):
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


class html_spliter_t:
    """HTML文本清理分割器"""

    def __init__(self):
        self._html_cleaner = hs.html_stripper_t()
        self._text_spliter = text_spliter_t()
        for c in SEP_CHARS:  # 默认先装载分局所需的标点符号
            self._text_spliter.word_spliter.dict_add(c, )
        self._text_spliter.word_spliter.dict_end()

    def load(self, rule_file):
        """装载拆分规则.返回值:空串正常,否则为错误信息."""
        return self._text_spliter.load(rule_file)

    def split(self, txt):
        rt = self._html_cleaner.proc(txt)
        st = ub.sbccase_to_ascii_str2(rt, True, True)
        segs, strs = self._text_spliter.split(st, ' ')
        return rt, segs


if __name__ == "__main__":
    assert split_by_strs('0123456789', ['1', '34', '345!', '78'], True) == ['0', '23456', '9']
    assert split_by_wild('0123456789', ['{1*78}'], True) == ['0', '23456', '9']
