"""
    这里封装一套简单的多进程单生产者多消费者模型
"""
import multiprocessing


def take_rst(que, maxsize=None):
    """尝试从que队列中获取一批数据,最大不超过maxsize"""
    rst = []
    if maxsize and maxsize > 0:
        while not que.empty() and len(rst) < maxsize:
            v = que.get()  # 得到一批处理结果
            rst.append(v)
    else:
        while not que.empty():
            v = que.get()  # 得到一批处理结果
            rst.append(v)
    return rst


def data_put(datas, que):
    """尝试将datas列表中的数据放入que队列"""
    rc = 0
    while not que.full() and len(datas):
        que.put(datas.pop(-1))
        rc += 1
    return rc


def cb_main(arg_main, que_tasks: multiprocessing.Queue, que_results: multiprocessing.Queue):
    """生产者任务函数样例
        arg_main: 用户自己传入的业务参数
        que_tasks: 任务队列,应该放入待处理的数据
        que_results: 结果队列,应该取出结果数据
    """
    tasks = 100000
    rc = 0
    datas = list(range(tasks))
    try:
        while datas:
            data_put(datas, que_tasks)  # 尝试放入待处理数据
            for r in take_rst(que_results):
                rc += 1
                print(r)  # 尝试获取并处理结果

        while rc < tasks:  # 尝试获取并处理最后一批结果
            for r in take_rst(que_results):
                rc += 1
                print(r)

        for i in range(4):
            que_tasks.put(None)  # 推送结束标记
    except Exception as e:
        print(e)


def cb_worker(widx, que_tasks: multiprocessing.Queue, que_results: multiprocessing.Queue):
    """消费者任务函数样例
        widx: 该任务创建的顺序号
        que_tasks: 任务队列,应该取出待处理的数据
        que_results: 结果队列,应该放入结果数据
    """
    try:
        while True:
            d = que_tasks.get()  # 得到任务数据
            if d is None:
                break  # 是结束标记
            # 否则处理任务,放入结果
            que_results.put((widx, d + 10))
    except Exception as e:
        print(e)


class manager_t:
    """任务管理器"""

    def __init__(self, cb_main, cb_worker, arg_main=None, workers=4, maxque=0):
        """初始化,提供必要的工作环境
            cb_main: 生产者工作函数
            cb_worker: 消费者工作函数
            arg_main: 生产者初始参数
            workers: 消费者进程并发数量,默认为4
            maxque: 队列最大尺寸,避免过量占用内存.(但需要注意put的时候需要确保队列能被消耗)
        """
        self._queue_tasks = multiprocessing.Queue(maxque)
        self._queue_results = multiprocessing.Queue(maxque)
        self._workers = []
        self._main = multiprocessing.Process(target=cb_main, args=(arg_main, self._queue_tasks, self._queue_results))
        for i in range(workers):
            w = multiprocessing.Process(target=cb_worker, args=(i, self._queue_tasks, self._queue_results))
            self._workers.append(w)

    def start(self):
        """启动全部的任务进程"""
        for w in self._workers:
            w.start()
        self._main.start()
        return self

    def end(self, force=False):
        """等待任务进程全部结束"""
        rets = []  # 记录进程返回值,供参考
        if force:
            if self._main.is_alive():
                self._main.terminate()
            for w in self._workers:
                if w.is_alive():
                    w.terminate()
        else:
            for i, w in enumerate(self._workers):
                w.join()
                rets.append((i, w.exitcode))
            self._main.join()
            rets.append((None, self._main.exitcode))

        self._main.close()
        self._main = None
        for w in self._workers:
            w.close()
        self._workers.clear()

        self._queue_results.close()
        self._queue_tasks.close()
        return rets


if __name__ == "__main__":
    # cb_main和cb_worker必须是全局函数,不能在这里局部定义,否则出错
    m = manager_t(cb_main, cb_worker,maxque=1000)
    m.start().end()
