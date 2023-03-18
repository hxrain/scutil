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
    max_match = 0  # 后项最大化优先匹配
    is_all = 1  # 全匹配模式


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

            # 最后一级的节点,记录替换值,表示一个单词的正向匹配树构建完成
            if force:
                if isinstance(val, Iterable):
                    if node.end is None:
                        node.end = deepcopy(val)
                        return True  # 新值
                    else:
                        node.end.update(val)
                        return False  # 扩容值
                else:
                    ret = True if node.end is None else False  # 新值或替换
                    node.end = val
                    return ret
            else:
                if node.end is not None:
                    return None  # 已存在不处理
                node.end = val
                return True  # 新值

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
        """底层方法:对给定长度为msg_len的消息文本message从offset处进行循环匹配,将匹配结果回调反馈给cb(pos,node)"""
        rc = 0  # 记录一共匹配了多少次
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
            if node.first:
                # 如果当前节点fail路径是存在的,则可能需要处理匹配结果
                cb(pos, node)
                rc += 1

        return rc

    def do_check(self, message, msg_len=None, offset=0, mode: mode_t = mode_t.is_all):
        """对给定的消息进行词条匹配测试,返回值:匹配结果[三元组(begin,end,val)]列表"""
        rst = []

        def cb_max(pos, node):
            """后项最大匹配,记录最后出现的有效结果"""
            node = node.first
            if node == self.root:
                return
            b, e, v = pos - node.words, pos, node.end
            while rst and b < rst[-1][1]:  # 新结果的起点小于已有结果的终点
                rst.pop(-1)  # 踢掉旧结果
            rst.append((b, e, v))

        def cb_all(pos, node):
            """记录原文字符pos处匹配的节点node的全部可能值"""
            fails = node.get_fails()
            for fail in reversed(fails):
                if fail != self.root:
                    rst.append((pos - fail.words, pos, fail.end))

        # 根据要求的匹配模式,选取对应的结果记录函数
        if mode == mode_t.max_match:
            cb = cb_max
        else:
            cb = cb_all

        # 执行匹配过程
        self.do_loop(cb, message, msg_len, offset)
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
            if dst_len > mt_len and max_match and old_val == m[2]:
                rst.append(message[m[0]:m[1]])  # 替换的目标与原有值相同,不重复替换
            else:
                do_rep(m[0], m[1], m[2])

        return ''.join(rst)
