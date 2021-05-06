import inspect
import re
import sys
import tracemalloc

def get_curr_func_name(is_parent=False):
    """调用者获取当前自己所在函数或父函数的名字"""
    if is_parent:
        return sys._getframe(2).f_code.co_name
    else:
        return sys._getframe(1).f_code.co_name


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
        self.snap1 = None
        self.snap2 = None
        self.min_size = min_size

        self.filters = [
            tracemalloc.Filter(False, '<frozen importlib._bootstrap_external>'),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
            tracemalloc.Filter(False, '<string>'),
            tracemalloc.Filter(False, '*tracemalloc.*'),
            tracemalloc.Filter(False, '*pycharm*'),
        ]
        if exclude_std:
            self.filters.append(tracemalloc.Filter(False, '*python*'))

        self.init(frames)

    def init(self, frames=1):
        tracemalloc.start(frames)
        self.capture(1)

    def capture(self, idx=1):
        self.__dict__['snap%d' % idx] = tracemalloc.take_snapshot().filter_traces(self.filters)

    def comp(self, i1, i2):
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
