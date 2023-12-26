# AC自动机 用于多模式匹配的应用
from collections import deque
from typing import List
from enum import Enum, unique
from collections.abc import Iterable
from match_util import rep_rec_t
from copy import deepcopy


@unique
class mode_t(Enum):
    """匹配结果的记录模式"""

    @staticmethod
    def last(rst, pos, node, root):
        """后项最大匹配,记录最后出现的有效结果"""

        def rec(node):
            if node == root:
                return
            b, e, v = pos - node.words, pos, node.end
            while rst and b < rst[-1][1]:  # 新结果的起点小于已有结果的终点
                rst.pop(-1)  # 踢掉旧结果
            rst.append((b, e, v))

        rec(node.first)

    @staticmethod
    def all(rst, pos, node, root):
        """记录原文字符pos处匹配的节点node的全部可能值"""
        fails = node.get_fails()
        for fail in reversed(fails):
            if fail != root:
                rst.append((pos - fail.words, pos, fail.end))

    @staticmethod
    def cross(rst, pos, node, root):
        """交叉保留,丢弃重叠包含的匹配"""

        def rec(node):
            if node == root:
                return
            b, e, v = pos - node.words, pos, node.end
            while rst and b <= rst[-1][0]:  # 新结果的起点小于已有结果的起点
                rst.pop(-1)  # 踢掉旧结果
            rst.append((b, e, v))

        rec(node.first)

    max_match = last.__func__  # 后项最大化优先匹配(交叉碰触被丢弃,仅保留最后出现的最大匹配段)
    is_all = all.__func__  # 全匹配模式(不丢弃任何匹配,全部记录)
    keep_cross = cross.__func__  # 交叉保持模式(仅丢弃完全被包含的部分)


class ac_match_t:
    """AC自动机多模式匹配功能封装"""

    delimit = '\x00'

    class node_t:
        def __init__(self) -> None:
            self.char = None  # 当前节点字母
            self.childs = {}  # 当前节点的子节点分支 {char:node_t}
            self.words = None  # 当前节点前缀词的长度
            self.end = None  # 当前节点是否为一个有效端点(不为None,存在替换目标值,即为一个有效端点)
            self.fail = None  # 当前节点所指向的fail指针
            self.first = None  # 当前节点所指向的第一个端点fail指针
            self.parent = None  # 当前节点的父节点

        def pre_word(self):
            """获取指定节点node的前缀词"""
            rst = []
            node = self
            while node is not None and node.char is not None:
                rst.insert(0, node.char)
                node = node.parent
            return ''.join(rst)

        def get_fails(self):
            """获取指定节点node的有效fail跳转路径"""
            fails = []
            node = self
            if node.end is not None:
                fails.append(node)
            while node and node.fail:
                if node.fail.end is not None:
                    fails.insert(0, node.fail)
                node = node.fail
            return fails

        def __repr__(self):
            if self.parent is None and self.char is None:
                return f'root({len(self.childs)})'
            else:
                return f'"{self.pre_word()}"={self.end}/{list(self.childs.keys())}@<{self.fail}>'

    def __init__(self, fname=None):
        self.root = self.node_t()
        if fname:
            self.dict_load(fname)

    def dict_add(self, keyword, val=delimit, strip=True, force=False):
        """添加关键词条到词表
            keyword - 待匹配的关键词
            val - 匹配后对应的替换目标词
            strip - 是否对关键词进行净空处理(可能会导致空格被丢弃)
            force - 是否强制扩容替换匹配值
        返回值:
            None - 关键词已存在,不处理
            False - 关键词已存在,扩容替换
            True - 关键词不存在,正常添加
        """

        def add(keyword, val, strip, force):
            word = keyword if not strip else keyword.strip()
            node = pnode = self.root  # 从根进行节点树的遍历

            for i, char in enumerate(word):  # 遍历关键词的每个字符,构建子节点树
                if char not in node.childs:  # 如果当前层级的字符未出现在当前节点的下一级
                    node.childs[char] = self.node_t()  # 创建新的子节点
                    node = node.childs[char]  # 得到新的子节点
                    node.words = i + 1  # 当前节点前缀词的长度
                    node.char = char  # 记录节点对应的字符
                    node.parent = pnode  # 记录节点的父节点
                else:
                    node = node.childs[char]  # 得到当前层级对应的子节点
                pnode = node  # 准备进行下一级节点树的处理

            # 最后一级节点为端点,记录替换值,表示一个单词的正向匹配树构建完成

            if not force:
                # 不是强制替换,则保持旧值
                if node.end is not None:
                    return None  # 已存在不处理
                node.end = val
                return True  # 新值

            # 不可迭代,新值或替换
            if not isinstance(val, Iterable):
                ret = True if node.end is None else False  # 新值或替换
                node.end = val
                return ret

            # 新值或迭代扩容
            if node.end is None:
                node.end = val
                return True  # 新值
            else:
                node.end = deepcopy(node.end)
                node.end.update(val)
                return False  # 扩容值

        if isinstance(keyword, (tuple, list)):
            ret = True
            for word in keyword:
                ret = ret and add(word, val, strip, force)
            return ret
        else:
            return add(keyword, val, strip, force)

    def dict_end(self):
        """在添加词表结束后,构建完整的fail跳转路径.
            如果不进行fail路径的构建,则匹配行为就是简单的trie树(前项匹配)
        """
        root = self.root
        queue = deque()  # 待处理节点队列,FIFO
        for char in root.childs:  # 将根节点的全部子节点放入待处理队列
            queue.append(root.childs[char])

        def get_fail_end(node):
            """获取指定节点node的第一个有效fail指针"""
            if node.end is not None:
                return node
            while node and node.fail:
                if node.fail.end is not None:
                    return node.fail
                node = node.fail
            return None

        # 从第一层开始,对trie树进行广度优先逐层遍历,由浅入深为每个节点增加Fail指针
        while queue:
            for i in range(len(queue)):
                node = queue.popleft()  # 从待处理队列的前面取出当前待处理节点
                for char in node.childs:  # 当前节点的全部子节点放入待处理队列的后边,确保完整的层级处理顺序
                    queue.append(node.childs[char])

                # 取出父节点的fail指针
                pfail = node.parent.fail

                # 向上寻找含有当前节点分支的上级fail节点
                while pfail and node.char not in pfail.childs:
                    pfail = pfail.fail

                if pfail is None:  # 当前节点没有匹配的fail路径,直接指向根节点
                    node.fail = root
                else:  # 记录当前节点的匹配的fail指针(pfail的对应分支节点)
                    node.fail = pfail.childs[node.char]

                node.first = get_fail_end(node)  # 记录当前节点的首个端点fail指针

    def dict_load(self, fname, isend=True, defval='', sep='@', encoding='utf-8'):
        """从文本文件fname装载词条.此函数可多次调用, 最后一次确保isend为真即可.
            文件单行为一个词条配置,用sep分隔的左边值将被替换为右边值.没有sep分隔时,替换值为defval
            返回值:(词条数量,错误消息)
        """
        try:
            rc = 0
            with open(fname, 'r', encoding='utf8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rc += 1
                    dat = line.split(sep, 1)
                    if len(dat) == 1:
                        self.dict_add(dat[0], defval)
                    else:
                        self.dict_add(dat[0], dat[1])
            if isend:
                self.dict_end()
            return rc, ''
        except Exception as e:
            return None, str(e)

    def do_loop(self, cb, message, msg_len=None, offset=0):
        """底层方法:对给定长度为msg_len的消息文本message从offset处进行循环匹配,将匹配结果回调反馈给cb(pos,node).
            返回值:[(char,pos)],记录message中哪些字符被命中过
        """
        rc = []  # 记录一共命中过哪些字符
        pos = offset
        if msg_len is None:
            msg_len = len(message)

        node = self.root  # 尝试从根节点进行初始匹配
        while pos < msg_len:  # 在循环中,node就是状态机的当前状态
            char = message[pos]
            pos += 1
            # 如果当前字符与当前状态节点不匹配,则跳转至状态节点的fail节点
            while node and char not in node.childs:
                node = node.fail

            if node is None:  # 当前字符不存在匹配,则状态节点重新指向根节点,等待下一次初始匹配
                node = self.root
                continue

            node = node.childs[char]  # 得到当前字符匹配的子节点
            rc.append((char, pos - 1, node))  # 记录完整的匹配信息
            if node.first:
                # 如果当前节点fail路径是存在的,则可能需要处理匹配结果
                cb(pos, node)

        return rc

    def do_check(self, message, msg_len=None, offset=0, mode: mode_t = mode_t.is_all):
        """对给定的消息进行词条匹配测试,返回值:匹配结果[三元组(begin,end,val)]列表"""
        rst = []
        self.do_loop(lambda pos, node: mode(rst, pos, node, self.root), message, msg_len, offset)
        return rst

    @staticmethod
    def do_complete(matchs, message, msg_len=None):
        """将匹配结果进行补全,得到完整的分段列表.其中(b,e,None)为原始文本段,(b,e,val)为匹配目标段"""
        rst = []
        if msg_len is None:
            msg_len = len(message)
        if not matchs:
            return [(0, msg_len, None)]

        pos = 0
        for m in matchs:
            if pos < m[0]:
                rst.append((pos, m[0], None))
            pos = m[1]
            rst.append(m)

        last = rst[-1]
        if last[1] != msg_len:
            rst.append((last[1], msg_len, None))
        return rst

    def do_match(self, message, msg_len=None, mode=mode_t.is_all):
        """对给定的消息进行关键词匹配,得到补全过的结果链[(begin,end,val),(begin,end,val),...],val为None说明是原内容部分"""
        if msg_len is None:
            msg_len = len(message)

        rs = self.do_check(message, msg_len, 0, mode)
        if len(rs) == 0:
            return []
        return self.do_complete(rs, message, msg_len)

    def do_filter(self, message, repl="*", msg_len=None, offset=0, rep_rec=None):
        """对给定的消息进行匹配替换;没有替换词的时候使用repl代替;rep_rec可用来记录具体的替换过程.
            返回值:替换后的文本内容
        """
        if msg_len is None:
            msg_len = len(message)
        ck_rst = self.do_check(message, msg_len, offset, mode_t.max_match)
        if not ck_rst:
            return message
        cm_rst = self.do_complete(ck_rst, message, msg_len)

        rst = []

        def do_rep(begin, end, txt):
            """记录替换结果,并进行替换信息的扩展记录"""
            rst.append(txt)
            if not rep_rec or not rep_rec.rst:
                return
            if self.rep_rec.txt is None:
                self.rep_rec.txt = message
            self.rep_rec.make(begin, end, txt)

        for m in cm_rst:
            if m[2] is None:
                rst.append(message[m[0]:m[1]])
                continue

            if m[2] == self.delimit:
                do_rep(m[0], m[1], repl * (m[1] - m[0]))
                continue

            dst_len = len(m[2])  # 替换的目标长度
            mt_len = len(message[m[0]:m[1]])  # 匹配的内容长度
            old_val = message[m[0]:m[0] + dst_len]  # 目标长度对应的内容
            if dst_len > mt_len and old_val == m[2]:
                rst.append(message[m[0]:m[1]])  # 替换的目标与原有值相同,不重复替换
            else:
                do_rep(m[0], m[1], m[2])

        return ''.join(rst)


class spliter_t:
    """基于ac匹配树的多字符串列表分隔器.
        以绑定的关键词集合进行分段切分,如果关键词以'!'结尾则不进行切分.
    """

    def __init__(self, strs=None):
        self.matcher = ac_match_t()
        if strs:
            self.bind(strs)

    def bind(self, strs, isend=True):
        for i, line in enumerate(strs):
            if not line or line[0] == '#':
                continue
            if line[-1] in {'!'}:
                self.matcher.dict_add(line[:-1], line[-1])  # 特殊匹配模式
            else:
                self.matcher.dict_add(line, i + 1)  # 分段匹配模式
        if isend:
            self.matcher.dict_end()

    def load(self, fname, encode='utf-8'):
        with open(fname, 'r', encoding=encode) as f:
            self.bind(f.readlines())

    def match(self, txt):
        """用txt匹配内部词表.返回值:[(begin,end,val)],val is None对应未匹配部分"""
        segs = self.matcher.do_match(txt, mode=mode_t.max_match)
        return segs if segs else [(0, len(txt), None)]

    def split(self, txt):
        """用strs串列表拆分txt.返回值:[分段字符串]"""
        rst = []
        segs = self.match(txt)
        attach = False
        for seg in segs:
            if seg[2] == '!':  # 如果遇到特殊匹配
                line = rst.pop(-1) + txt[seg[0]:seg[1]]  # 则进行当前与前一段的拼装
                rst.append(line)
                attach = True  # 设置附加状态
            elif attach:  # 如果要求附加连接
                if seg[2] in {None, '!'}:  # 且当前不是分段匹配
                    line = rst.pop(-1) + txt[seg[0]:seg[1]]  # 则进行当前与前一段的拼装
                    rst.append(line)
                attach = seg[2] == '!'  # 更新附加状态,可能继续附加
            elif seg[2] is None:  # 当前就是普通分段
                rst.append(txt[seg[0]:seg[1]])

        return rst


def split_by_strs(txt, strs, outstrs=False):
    """用strs串列表拆分txt.
        outstrs 为 True:
            返回值:[(begin,end,val)],val is None对应未匹配部分
        outstrs 为 False:
            返回值:[分段字符串]
    """
    match = spliter_t(strs)
    if outstrs:
        return match.split(txt)
    else:
        return match.match(txt)
