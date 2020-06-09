#!/usr/bin/python
# -*- coding: utf-8 -*-

import json


def showdict(msg, dic):
    print(msg, json.dumps(dic))


# DFA前向最大匹配算法
class dfa_match_t():
    def __init__(self):
        self.keyword_chains = {}
        self.delimit = '\x00'  # 结束

    def dict_add(self, keyword, val='\x00'):
        keyword = keyword.lower().strip()  # 关键词变小写并丢弃首尾空白
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

    def do_filter(self, message, repl="*", max_match=True):
        """对给定的消息进行关键词匹配过滤,替换为字典中的对应值,或指定的字符"""
        ms = self.do_match(message, max_match=max_match)
        rst = []
        for m in ms:
            if m[2] is None:
                rst.append(message[m[0]:m[1]])
            else:
                if m[2] == self.delimit:
                    rst.append(repl * (m[1] - m[0]))
                else:
                    rst.append(m[2])
        return ''.join(rst)

    # 对给定的消息进行关键词匹配,得到结果链[(begin,end,val),(begin,end,val),...],val为None说明是原内容部分
    def do_match(self, message, msg_len=None, isall=True, max_match=True):
        message = message.lower()  # 待处理消息串进行小写转换,消除干扰
        if msg_len is None:
            msg_len = len(message)
        offset = 0
        rst = []
        while offset < msg_len:
            rc = self.do_check(message, msg_len, offset, max_match)
            if rc[0] is None:  # 没有找到匹配结果
                if isall:
                    if offset == 0:
                        rst.append((0, msg_len, None))  # 记录首次匹配不成功的全部原始内容
                    elif rst[-1][1] != msg_len:
                        rst.append((rst[-1][1], msg_len, None))  # 补充最后剩余的部分
                break
            if isall and rc[0] != offset:
                rst.append((offset, rc[0], None))  # 记录当前段不匹配的部分
            rst.append(rc)  # 记录当前段匹配的结果
            offset = rc[1]  # 从当前匹配的结束位置继续后面的尝试
        return rst

    def do_check(self, message, msg_len=None, offset=0, max_match=True):
        """对给定的消息进行关键词匹配测试,返回值:首个匹配的结果,三元组(begin,end,val)"""
        if msg_len is None:
            msg_len = len(message)
        start = offset  # 记录当前正处理的字符位置
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
                        if nchar in level[char]:
                            level = level[char]
                            continue
                    # 如果当前词链标记结束了,说明从start开始到现在的消息内容,是一个完整匹配
                    return (start, start + step_ins, level[char][self.delimit])
            # 跳过当前消息字符,开始下一轮匹配
            start += 1
        return (None, None, None)
