# -*- coding: utf-8 -*-

import inspect
import re
import sys
import tracemalloc
import traceback


def get_curr_func_name(is_parent=False):
    """调用者获取当前自己所在函数或父函数的名字"""
    if is_parent:
        return sys._getframe(2).f_code.co_name
    else:
        return sys._getframe(1).f_code.co_name


def get_stackup(start=0):
    """调用者获取上级调用栈信息"""
    rst = []
    d = start
    while True:
        d += 1
        try:
            frm = sys._getframe(d)
            rst.insert(0, '  File "%s", line %d, in %s' % (frm.f_code.co_filename, frm.f_lineno, frm.f_code.co_name))
            if frm.f_code.co_name == '<module>':
                break
        except:
            break
    rst.insert(0, 'Traceback (call stack parent)')
    return '\n'.join(rst)


def get_trace_stack():
    """获取当前调用栈信息,包括之上的父调用与之下的异常抛出点"""
    up = get_stackup(2)
    dn = traceback.format_exc()
    return up, dn


def get_curr_func_params(drop_self=True):
    """调用者获取当前自己被调用时传递的实参名称"""
    funcname = get_curr_func_name(True)
    rst = []
    for l in inspect.getframeinfo(sys._getframe(1).f_back).code_context:
        m = re.search(r'%s\s*\(\s*(.*)\s*\)' % funcname, l)
        if m:
            for p in m.group(1).split(','):
                p = p.strip()
                if drop_self:
                    p = p.replace('self.', '')
                rst.append(p)
    return rst


class tramem_mgr:
    """内存快照分析管理器,便于对比两次快照中的内存增量,快速发现内存泄露"""

    def __init__(self, exclude_std=True, min_size=1024, frames=1):
        self.snap1 = None  # 快照槽位1
        self.snap2 = None  # 快照槽位2
        self.min_size = min_size

        self.filters = []  # 定义过滤器,可丢弃不关注的信息
        if exclude_std:
            self.filters.append(tracemalloc.Filter(False, '*python*'))
            self.filters.append(tracemalloc.Filter(False, '<frozen importlib._bootstrap_external>'))
            self.filters.append(tracemalloc.Filter(False, "<frozen importlib._bootstrap>"))
            self.filters.append(tracemalloc.Filter(False, "<unknown>"))
            self.filters.append(tracemalloc.Filter(False, '<string>'))
            self.filters.append(tracemalloc.Filter(False, '*tracemalloc.*'))
            self.filters.append(tracemalloc.Filter(False, '*pycharm*'))

        self.init(frames)

    def init(self, frames=1):
        """初始化快照管理器,并捕捉最初的状态"""
        tracemalloc.start(frames)
        self.capture(1)

    def capture(self, idx=1):
        """捕捉最新的快照到指定的槽位"""
        self.__dict__['snap%d' % idx] = tracemalloc.take_snapshot().filter_traces(self.filters)

    def comp(self, i1, i2):
        """比较给定的两个槽位的快照,得到比较的结果"""
        s1 = self.__dict__['snap%d' % i1]
        s2 = self.__dict__['snap%d' % i2]
        if s2 is None or s1 is None:
            return 'next'
        top_stats = s2.compare_to(s1, 'lineno')
        rst = []
        for l in top_stats:
            if l.size < self.min_size and l.size_diff < self.min_size:
                continue
            rst.append(str(l))

        return '\n'.join(rst)

    def take(self, idx):
        """快捷方法,抓取指定的快照,并进行前后槽位的快照比较,得到差异结果"""
        idx = int(idx)
        if idx in {1, 2}:
            self.capture(idx)
        else:
            return 'bad snap idx. only 1 or 2.'
        if idx == 2:
            stats = self.comp(idx - 1, idx)
        else:
            stats = 'wait take snap 2'

        return stats


def loop_globals(limit=4000):
    """递归遍历全局变量,查看子元素过大的变量"""
    old_mods = set()
    result = []

    def can(obj):
        if obj is None:
            return []
        typename = type(obj).__name__
        if typename in {'int', 'str', 'float', 'type'}:
            return []

        if id(obj) in old_mods:
            return []
        old_mods.add(id(obj))

        if typename in {'module'}:
            return dir(obj)
        try:
            return list(obj.keys())
        except:
            return []

    def siz(obj):
        try:
            if isinstance(obj, str):
                return 0
            return len(obj)
        except:
            return 0

    def tak(obj, name):
        try:
            return obj[name]
        except:
            pass

        try:
            return getattr(obj, name)
        except:
            return None

    def loop(root, path):
        """对当前根进行全遍历递归"""
        keys = can(root)
        if not keys:
            return
        for name in keys:
            obj = tak(root, name)
            if obj is None:
                continue
            if not isinstance(name, str):
                name = str(name)
            path.append(name)
            s = siz(obj)
            if s >= limit:
                result.append((s, '/'.join(path), str(type(obj))))
            loop(obj, path)
            path.pop(-1)

    loop(globals(), ['globals'])
    return result
