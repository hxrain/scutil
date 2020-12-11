from functools import wraps
from threading import Lock
from threading import RLock
from threading import Thread

"""
locker = lock_t()  # 定义互斥锁封装对象

@guard(locker)  # 使用指定的锁对目标函数进行锁保护装饰
def tst():
    print(tst.__name__)

tst()
"""


# 定义互斥锁功能封装
class lock_t:
    def __init__(self, use=False, is_rlock=True):
        self.locker = None
        if use:
            self.init(is_rlock)

    def init(self, is_rlock=True):
        if self.inited():
            return
        if is_rlock:
            self.locker = RLock()
        else:
            self.locker = Lock()

    def lock(self):
        if not self.inited():
            return
        self.locker.acquire()

    def unlock(self):
        if not self.inited():
            return
        self.locker.release()

    def inited(self):
        return self.locker is not None


# 给指定函数绑定锁保护的装饰器函数
def guard(locker):  # 顶层装饰函数,用来接收用户参数,返回外层装饰函数
    def outside(fun):  # 外层装饰函数,用来接收真实的目标函数
        @wraps(fun)
        def wrap(*args, **kwargs):  # 包装函数对真实函数进行锁保护的调用
            locker.lock()
            ret = fun(*args, **kwargs)
            locker.unlock()
            return ret

        return wrap

    return outside


# 创建并启动一个线程
def start_thread(fun, *args, run=True):
    thd = Thread(target=fun, args=args)
    if run:
        thd.start()
    return thd


def wait_thread(thd, timeout=None):
    """等待线程结束.返回值:1成功;0超时;-1错误"""
    try:
        thd.join(timeout)
        if thd.isAlive():
            return 0
        return 1
    except Exception as e:
        print(e)
        return -1


def wait_threads(thds, timeout=None):
    """逐一判断,等待线程列表中的线程结束.返回值:从thds中被移除的线程对象"""
    rst = []
    for t in thds:
        if wait_thread(t, timeout) > 0:
            rst.append(t)
    for t in rst:
        thds.remove(t)
    return rst
