import inspect
import re
import sys


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
