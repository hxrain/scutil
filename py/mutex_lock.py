# -*- coding: utf-8 -*-

from functools import wraps
from threading import Lock
from threading import RLock
from threading import Thread
from threading import Semaphore
from threading import currentThread
import time
import traceback
import copy
import os

"""
locker = lock_t()  # 定义互斥锁封装对象

@guard(locker)  # 使用指定的锁对目标函数进行锁保护装饰
def tst():
    print(tst.__name__)

tst()
"""


def get_thread_id():
    """获取线程标识"""
    t = currentThread()
    return (t.ident, t.name)


# 定义互斥锁功能封装
class lock_t:
    def __init__(self, use=False, is_rlock=True):
        """use - 是否开启同步锁功能;is_rlock - 是否为递归锁"""
        self.locker = None
        if use:
            self.init(is_rlock)

    def __del__(self):
        self.uninit()

    def init(self, is_rlock=True):
        if self.inited():
            return
        if is_rlock:
            self.locker = RLock()
        else:
            self.locker = Lock()

    def uninit(self):
        del self.locker
        self.locker = None

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

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()


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
def guard_ext(locker, timeout=2):  # 顶层装饰函数,用来接收用户参数,返回外层装饰函数
    if 'ownfunc' not in locker.__dict__:
        locker.__dict__['waitimes'] = {}
        locker.__dict__['ownfunc'] = ''

    def outside(fun):  # 外层装饰函数,用来接收真实的目标函数
        @wraps(fun)  # 使用内置包装器保留fun的原属性(下面的fun已经是闭包中的一个变量了)
        def wrap(*args, **kwargs):  # 包装函数对真实函数进行锁保护的调用
            tm_begin = time.time()  # 得到锁之前先记录开始时间和可能的拥有者
            own = locker.__dict__['ownfunc']
            locker.lock()  # 得到锁
            tm_wait = int(time.time() - tm_begin)  # 计算等待时间
            cur = f'{fun.__module__}.{fun.__name__}'
            if tm_wait > timeout and own:  # 如果等待时间超过限定值,则进行上一个拥有者的记录
                waits = locker.__dict__['waitimes']
                key = f'{cur}@{own}'  # 记录当前调用者与上一个拥有者,以及阻塞等待时间
                if key not in waits:
                    waits[key] = set()
                owns = waits[key]
                owns.add(tm_wait)
                if len(owns) > 20:
                    owns.remove(min(owns))

            locker.__dict__['ownfunc'] = f'{fun.__module__}.{fun.__name__}'
            try:
                ret = fun(*args, **kwargs)
            except Exception as e:
                ret = e
                print(f"{e.__class__.__name__}:{str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
                pass
            locker.__dict__['ownfunc'] = ''
            locker.unlock()  # 释放锁

            return ret

        return wrap

    return outside


def guard_owns(locker, isclean=False):
    """查询获取指定锁对象记录的拥有者超时数据"""
    ret = None
    with locker:
        if 'ownfunc' not in locker.__dict__:
            return None
        if isclean:
            ret = copy.deepcopy(locker.__dict__['waitimes'])
            locker.__dict__['waitimes'] = {}
        else:
            ret = locker.__dict__['waitimes']
    return ret


# 给指定函数绑定锁保护的装饰器函数
def guard_std(locker):  # 顶层装饰函数,用来接收用户参数,返回外层装饰函数
    def outside(fun):  # 外层装饰函数,用来接收真实的目标函数
        @wraps(fun)  # 使用内置包装器保留fun的原属性(下面的fun已经是闭包中的一个变量了)
        def wrap(*args, **kwargs):  # 包装函数对真实函数进行锁保护的调用
            locker.lock()
            try:
                ret = fun(*args, **kwargs)
            except Exception as e:
                ret = e
                print('%s:\n%s' % (e.__class__.__name__, ''.join(traceback.format_tb(e.__traceback__))))
                pass
            locker.unlock()
            return ret

        return wrap

    return outside


# 默认使用标准guard模式,不记录锁等待信息.
guard = guard_std


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
        if thd.is_alive():
            return 0
        return 1
    except Exception as e:
        print(e)
        return -1


def stop_thread(thd, exc=InterruptedError):
    """强制线程停止"""

    def _async_raise(tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    _async_raise(thd.ident, exc)


def wait_threads(thds, timeout=None, idle_cb=None):
    """逐一判断,等待线程列表中的线程结束.返回值:(已结束线程[],是否要求停止)"""
    rst = []
    stop = False
    for t in thds:
        if wait_thread(t, timeout) > 0:
            rst.append(t)
        if idle_cb:
            stop = idle_cb()
            if stop:
                break
    for t in rst:
        thds.remove(t)
    return rst, stop


def wait_threads_count(thds, max_thds, timeout=0.1, idle_cb=None):
    """等待thds的线程数量小于max,返回值:外部idle回调是否要求停止"""
    if max_thds <= 0:
        max_thds = 1
    while len(thds) >= max_thds:
        ends, stop = wait_threads(thds, timeout, idle_cb)
        if stop:
            return True
    return False


def with_threads(datas, task_cb, threads=32, stat_cb=None):
    """并发threads线程处理datas字典,字典的每个元素都传递给task_cb(key,val)在独立的线程中运行.
        如果给出了状态回调,则周期性调用stat_cb(remain,total)便于进行计数或进度更新.
    """
    workers = []
    ids = list(datas.keys())
    total = len(ids)
    while ids:
        if stat_cb:
            stat_cb(len(ids), total)
        cnt = min(threads - len(workers), len(ids))
        for i in range(cnt):
            id = ids.pop(0)
            workers.append(start_thread(task_cb, id, datas[id]))
        wait_threads(workers, 1)


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


class fixed_pool_t:
    """固定缓存池功能封装"""

    def __init__(self, obj_type=None, size=0, on_free=None, *datas, **args):
        self.objs = []
        self.pool = obj_cache_t()
        self.on_free = on_free
        if size and obj_type:
            self.init(obj_type, size, *datas, **args)

    def init(self, obj_type, size, *datas, **args):
        """进行指定类型的对象池初始化"""
        for i in range(size):
            self.objs.append(obj_type(*datas, **args))
        self.pool.init(self.objs)

    def call(self, func, *args):
        """运行指定的功能函数func(obj,*args),在obj不能获取时进行等待
           返回值:(func的返回值,err)
           err正常为空,否则为异常对象
        """
        err = ''
        idx = self.pool.get()
        try:
            ret, err = func(self.objs[idx], *args)
        except Exception as e:
            ret = None
            err = e

        if self.on_free:
            self.on_free(self.objs[idx])
        self.pool.put(idx)
        return ret, err


class lines_exporter:
    """带有线程锁保护的文本输出器"""

    def __init__(self, fname=None, with_lock=True, mode='a+'):
        self._fp = None
        self._fname = None
        self._locker = lock_t(with_lock)
        if fname:
            self.open(fname, mode=mode)

    def __del__(self):
        self.close()
        del self._locker
        self._locker = None

    def open(self, fname, encoding='utf-8', mode='a+'):
        """打开指定路径下的文件,路径不存在则创建"""
        try:
            path = os.path.dirname(fname)
            os.mkdir(path)
        except Exception as e:
            pass

        with self._locker:
            if self._fp is not None:
                return True
            self._fname = fname
            try:
                self._fp = open(fname, mode, encoding=encoding)
                self._fp.writelines()
                return True
            except Exception as e:
                return False

    # 真正的单行输出方法,不进行锁保护,便于复用
    def __put(self, line, with_lf):
        try:
            if with_lf and line[-1] != '\n':
                self._fp.writelines((line, '\n'))
            else:
                self._fp.write(line)
            return ''
        except Exception as e:
            return e

    def put(self, line, with_lf=True):
        """追加行内容到文件.返回值:None-文本为空;''-正常完成;其他-异常错误"""
        if line is None:
            return None
        with self._locker:
            return self.__put(line, with_lf)

    def puts(self, lst, with_lf=True):
        """追加列表到文件"""
        with self._locker:
            if isinstance(lst, str):
                return self.__put(lst, with_lf)
            for line in lst:
                e = self.__put(line, with_lf)
                if e:
                    return e
            return ''

    def save(self):
        """立即存盘,刷新缓存到文件."""
        with self._locker:
            if self._fp is None:
                return None
            try:
                self._fp.flush()
                return True
            except Exception as e:
                return False

    def close(self):
        with self._locker:
            if self._fp is None:
                return None
            try:
                self._fp.close()
                self._fp = None
                return True
            except Exception as e:
                return False
