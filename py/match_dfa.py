#!/usr/bin/python
# -*- coding: utf-8 -*-
from match_util import *

# DFA前向最大匹配算法
class dfa_match_t():
    def __init__(self, value_is_list=False, rep_rec=None):
        self.keyword_chains = {}
        self.delimit = '\x00'  # 结束
        self.value_is_list = value_is_list  # 是否使用list记录匹配的多值列表
        self.keyword_lower = False
        self.rep_rec = rep_rec  # 替换记录器

    def dict_add(self, keyword, val='\x00', strip=True):
        """添加关键词条到词表
            keyword - 待匹配的关键词
            val - 匹配后对应的替换目标词
            strip - 是否对关键词进行净空处理(可能会导致空格被丢弃)
        """
        if strip:
            keyword = keyword.strip()  # 关键词丢弃首尾空白
        if self.keyword_lower:
            keyword = keyword.lower()  # 关键词变小写

        if not keyword or val is None:
            return False

        key_len = len(keyword)
        # 得到当前词链的层级(入口)
        level = self.keyword_chains
        i = 0
        # 对关键词进行逐一遍历处理
        for i in range(key_len):
            char = keyword[i]
            if char in level:
                # 如果当前字符在当前层,则沿着该字符的分支进入下一层(获得dict的对应value)
                level = level[char]
                if i == key_len - 1:
                    if self.value_is_list:
                        # 记录值列表
                        if self.delimit in level:
                            level[self.delimit].append(val)
                        else:
                            level[self.delimit] = [val]
                    else:
                        # 如果全部层级都处理完毕,则最后要标记关键词结束,或者是用新值替代旧值
                        if self.delimit not in level or level[self.delimit] != val:
                            level[self.delimit] = val
            else:
                # 当前字符对应当前层级新分支
                if not isinstance(level, dict):
                    break
                # 假设当前层就是最后一层
                last_level = level
                for j in range(i, key_len):
                    # 对剩余的关键词字符进行循环
                    char = keyword[j]
                    # 记录最后一层
                    last_level = level
                    # 创建当前层当前字符的新分支
                    level[char] = {}
                    # 当前层级向下递进
                    level = level[char]
                # 最后字符对应着结束标记
                if self.value_is_list:
                    last_level[char] = {self.delimit: [val]}
                else:
                    last_level[char] = {self.delimit: val}
                break
        return True

    # 从文件装载关键词
    def dict_load(self, path, defval=''):
        with open(path, 'r', encoding='utf8') as f:
            for line in f:
                dat = line.strip().split('@', 1)
                if len(dat) == 1:
                    self.dict_add(dat[0], defval)
                else:
                    self.dict_add(dat[0], dat[1])

    def do_filter(self, message, repl="*", max_match=True, isall=False):
        """对给定的消息进行关键词匹配过滤,替换为字典中的对应值,或指定的字符"""
        msg_len = len(message)
        rs = self.do_match(message, msg_len, max_match=max_match, isall=isall)
        if len(rs) == 0:
            return message

        ms = self.do_complete(rs, message, msg_len)
        rst = []

        def do_rep(begin, end, txt):
            """记录替换结果,并进行替换信息的扩展记录"""
            rst.append(txt)
            if self.rep_rec and self.rep_rec.rst is not None:
                if self.rep_rec.txt is None:
                    self.rep_rec.txt = message
                self.rep_rec.make(begin, end, txt)

        for m in ms:
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

    # 对给定的消息进行关键词匹配,得到补全过的结果链[(begin,end,val),(begin,end,val),...],val为None说明是原内容部分
    def do_match(self, message, msg_len=None, max_match=True, isall=True):
        """max_match:告知是否进行最长匹配
           isall:告知是否记录全部匹配结果(最长匹配时,也包含匹配的短串)
        """
        if self.keyword_lower:
            message = message.lower()  # 待处理消息串进行小写转换,消除干扰
        if msg_len is None:
            msg_len = len(message)

        rs = self.do_check(message, msg_len, 0, max_match, isall)
        if len(rs) == 0:
            return []
        return self.do_complete(rs, message, msg_len)

    # 根据do_match匹配结果,补全未匹配的部分
    def do_complete(self, matchs, message, msg_len=None):
        def _find_max_seg(begin, matchs, matchs_len):
            """在matchs的begin开始处,查找其最长的匹配段索引"""
            if begin >= matchs_len:
                return begin

            bi = matchs[begin][0]
            ri = begin
            for i in range(begin + 1, matchs_len):
                if matchs[i][0] != bi:
                    break
                ri = i
            return ri

        if self.keyword_lower:
            message = message.lower()  # 待处理消息串进行小写转换,消除干扰
        if msg_len is None:
            msg_len = len(message)
        rst = []
        matchs_len = len(matchs)
        pos = _find_max_seg(0, matchs, matchs_len)
        while pos < matchs_len:
            rc = matchs[pos]
            if len(rst) == 0:
                if rc[0] != 0:
                    rst.append((0, rc[0], None))  # 记录首部未匹配的原始内容
                rst.append(rc)  # 记录当前匹配项
            elif rc[0] >= rst[-1][1]:
                if rc[0] != rst[-1][1]:
                    rst.append((rst[-1][1], rc[0], None))  # 记录前面未匹配的原始内容
                rst.append(rc)  # 记录当前匹配项
            pos = _find_max_seg(pos + 1, matchs, matchs_len)  # 查找后项

        if rst[-1][1] != msg_len:
            rst.append((rst[-1][1], msg_len, None))  # 补充最后剩余的部分
        return rst

    def do_check(self, message, msg_len=None, offset=0, max_match=True, isall=True, skip_match=False):
        """对给定的消息进行关键词匹配测试,返回值:匹配结果[三元组(begin,end,val)]列表"""
        rst = []

        def cb(b, e, v):
            rst.append((b, e, v))

        self.do_loop(cb, message, msg_len, offset, max_match, isall, skip_match)
        return rst

    def do_loop(self, cb, message, msg_len=None, offset=0, max_match=True, isall=True, skip_match=False):
        """基础方法,对给定的消息进行关键词匹配循环
            cb - 结果回调函数
            message - 待匹配的原文消息
            msg_len - 待匹配的原文消息字符长度
            offset - 从原文的指定偏移量进行匹配
            max_match - 是否进行关键词最大化优先匹配
            isall - 是否在最大化优先匹配的情况下记录同词根的短词匹配结果
            skip_match - 是否直接跳过已匹配的短语长度(提高速度,但可能丢弃中间短语)
            返回值:匹配次数"""
        if msg_len is None:
            msg_len = len(message)
        start = offset  # 记录当前正处理的字符位置
        rc = 0
        # 对消息进行逐一字符的过滤处理
        while start < msg_len:
            # 得到词链树的根
            level = self.keyword_chains
            step_ins = 0
            # 对当前剩余消息进行逐一过滤,进行本轮匹配
            for char in message[start:]:
                if char not in level:
                    break  # 没有匹配的字符,结束当前匹配循环
                step_ins += 1
                if self.delimit not in level[char]:
                    # 如果当前词链没有结束,则尝试向下深入,不记录结果
                    level = level[char]
                else:
                    if max_match and start + step_ins < msg_len:  # 要进行最大化匹配的尝试
                        nchar = message[start + step_ins]
                        if nchar in level[char] or start + step_ins + 1 == msg_len:
                            if isall:  # 记录匹配的全部中间结果
                                cb(start, start + step_ins, level[char][self.delimit])
                                rc += 1
                            level = level[char]
                            continue

                    # 如果当前词链标记结束了,说明从start开始到现在的消息内容,是一个完整匹配
                    cb(start, start + step_ins, level[char][self.delimit])
                    rc += 1
                    break
            # 跳过当前消息字符,开始下一轮匹配
            if skip_match:
                start += max(1, step_ins)
            else:
                start += 1
        return rc


def do_filter(dfa, message, reps=None, repl="*", max_match=True, isall=False, lr_len=3):
    """便捷函数:调用dfa对message进行替换过滤,将过程信息放入reps.返回值:(替换后的文本,reps)"""
    if reps is None:
        reps = []
    rep_rec = rep_rec_t(message, reps, lr_len)
    dfa.rep_rec = rep_rec
    return dfa.do_filter(message, repl, max_match, isall), reps



if __name__ == '__main__':
    match = dfa_match_t()
    match.dict_add('abcde', '12345')
    match.dict_add('abc', '123')
    match.dict_add('cde', '345')
    match.dict_add('bcd', '234')
    txt = "hello!abcde!abc!"
    result = match.do_match(txt)
    print(result)
    result2 = match.do_filter(txt, isall=True)
    print(result2)
