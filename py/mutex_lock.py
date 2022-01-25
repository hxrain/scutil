from functools import wraps
from threading import Lock
from threading import RLock
from threading import Thread
from threading import Semaphore
import time

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

    def lock(self, timeout=-1):
        if not self.inited():
            return False
        return self.locker.acquire(timeout=timeout)

    def unlock(self):
        if not self.inited():
            return False
        self.locker.release()
        return True

    def inited(self):
        return self.locker is not None


class sem_t:
    """信号量功能封装"""

    def __init__(self, maxval=None):
        self.sem = None
        if maxval:
            self.init(maxval)

    def init(self, maxval):
        assert (self.sem is None)
        self.sem = Semaphore(maxval)

    def inited(self):
        return self.sem is not None

    def lock(self, timeout=-1):
        if not self.inited():
            return False
        return self.sem.acquire(timeout=timeout)

    def unlock(self):
        if not self.inited():
            return False
        self.sem.release()
        return True


# 给指定函数绑定锁保护的装饰器函数
def guard(locker):  # 顶层装饰函数,用来接收用户参数,返回外层装饰函数
    def outside(fun):  # 外层装饰函数,用来接收真实的目标函数
        @wraps(fun)  # 使用内置包装器保留fun的原属性(下面的fun已经是闭包中的一个变量了)
        def wrap(*args, **kwargs):  # 包装函数对真实函数进行锁保护的调用
            locker.lock()
            try:
                ret = fun(*args, **kwargs)
            except Exception as e:
                ret = e
                pass
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


# 创建并启动一个间隔定时器函数线程,周期运行
def start_timer(fun, interval, *args):
    def proc():
        while not thd.stop:
            fun(*args)
            time.sleep(interval)

    thd = Thread(target=proc)
    thd.stop = False  # 外面可以设置此变量为True,逻辑停止工作函数.
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


def wait_threads_less(thds, less):
    """等待thds的线程数量小于less"""
    while len(thds) >= less:
        wait_threads(thds, 1)


class obj_pool_t:
    """简单的对象池,线程安全"""

    def __init__(self, obj_type):
        self.obj_type = obj_type
        self.locker = lock_t(True)
        self.objs = []

    def get(self, frmpos=0):
        """获取对象.返回值:None失败;其他为指定类型的对象"""
        obj = None
        self.locker.lock()
        try:
            if len(self.objs):
                obj = self.objs.pop(frmpos)
            else:
                obj = self.obj_type()
        except Exception as e:
            print('obj_pool memory overflow for get: %s' % self.obj_type.__name__)

        self.locker.unlock()
        return obj

    def put(self, obj):
        """归还对象.返回值:是否成功"""
        ret = False
        if obj is None:
            return ret

        self.locker.lock()
        try:
            self.objs.append(obj)
            ret = True
        except Exception as e:
            print('obj_pool memory overflow for put: %s' % self.obj_type.__name__)
        self.locker.unlock()
        return ret


class obj_cache_t:
    """阻塞的对象缓存管理器"""

    def __init__(self, vals=None, is_ref=True):
        self.objs = []
        self.id_pool = None
        self.sem = None
        self.frmpos = 0
        if vals:
            self.init(vals, is_ref)

    def init(self, vals, is_ref=True):
        """初始化,告知可用对象列表"""
        assert (self.id_pool is None)
        if is_ref:
            self.objs = vals
        else:
            self.objs.extend(vals)
        self.sem = sem_t(len(vals))
        self.id_pool = obj_pool_t(int)
        for i in range(len(vals)):
            self.id_pool.put(i)

    def inited(self):
        return self.id_pool is not None

    def get(self, timeout=None):
        """获取对象索引,若全部对象都已被分配则进行阻塞等待;返回None失败"""
        if not self.sem.lock(timeout):
            return None
        return self.id_pool.get(self.frmpos)

    def put(self, idx):
        """归还对象索引"""
        self.id_pool.put(idx)
        self.sem.unlock()

    def __getitem__(self, item):
        """根据索引获取对象的值"""
        return self.objs[item]
