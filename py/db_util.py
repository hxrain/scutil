from util_base import *


class db_fetch_t:
    def __init__(self, fname, conn, logger):
        self.conn = conn
        self.logger = logger

        # 装载保存过的信息存根
        self.stub_file = fname
        self.last_time = None
        self.last_id = None
        self._load_stub()
        if self.last_time is None:
            self.last_time = get_curr_date('%Y-%m-%d %H:%M:%S.%f')

    def _load_stub(self):
        """从存根文件中获取最后的时间和id"""
        dct = dict_load(self.stub_file, 'utf-8')
        if dct is None:
            return False
        assert ('last_time' in dct)
        assert ('last_id' in dct)
        self.last_time = dct['last_time']
        self.last_id = dct['last_id']
        return True

    def put_stub(self, last_time, uuid=None):
        """强制更新存根信息(在外面推送失败的时候)"""
        self.last_time = last_time  # 信息查询的开始时间点
        self.last_id = uuid  # 最后提交失败时的id,此信息需要重试,且从它之后再发送

    def upd_stub(self, info):
        """使用给定的info对象强制更新存根信息(在外面推送失败的时候)"""
        self.last_time = self.on_get_lasttime(info, None)
        self.last_id = self.on_make_unique(info, None)

    def save_stub(self):
        """存根信息落盘"""
        stub = {'last_time': self.last_time, 'last_id': self.last_id}
        rst = dict_save(self.stub_file, stub)
        if not rst:
            self.logger.warn('stub save fail: %s' % (stub))
        else:
            self.logger.info('stub save ok: %s' % (stub))
        return rst

    def query(self, exparam=None, auto_skip=False):
        """执行预设查询,得到期待的结果信息列表.返回值:(信息列表,原始数据列表)"""
        sql, param = self.on_make_sql(exparam)
        st, res = self.on_exec(self.conn, sql, param, exparam)
        if not st:
            self.logger.warn('db query error: %s' % (res))
            return None, None

        rst = []
        info = None
        for r in res:  # 对查询结果进行遍历
            info = self.on_make_info(r, exparam)
            if self.last_id:
                if self.on_make_unique(info, exparam) != self.last_id:
                    continue
                self.last_id = None  # 如果指定了接续记录且遇到了该记录,则可进行后续的正常处理了
            if not self.on_filter(info, exparam):
                rst.append(info)  # 记录需要的输出信息

        if len(rst):  # 存在有效记录,则使用最后的有效记录更新时间点
            self.last_time = self.on_get_lasttime(rst[-1], exparam)
        elif info:  # 不存在有效记录,则尝试使用最后的记录更新时间点
            self.last_time = self.on_get_lasttime(info, exparam)
        elif auto_skip:  # 使用当前时间作为最后的时间点
            self.last_time = get_curr_date('%Y-%m-%d %H:%M:%S.%f')
        return rst, res

    def on_make_sql(self, exparam):
        """构造查询sql,以及对应的查询参数"""

    def on_exec(self, conn, sql, param, exparam):
        """基于conn执行sql查询,param是查询参数,exparam是外部给出的扩展参数.返回值:(bool状态,结果集)"""

    def on_make_unique(self, info, exparam):
        """从查询结果中构造代表此记录的唯一值"""

    def on_filter(self, info, exparam):
        """对给定的信息进行过滤.返回值:是否需要丢弃"""

    def on_get_lasttime(self, info, exparam):
        """获取信息中的增量时间"""

    def on_make_info(self, row, exparam):
        """从查询结果中构造需要的信息字典"""


def proc_fetch(anz_fun, fetcher, pusher=None, logger=None):
    """进行查询/分析/推送的集成处理;返回值:是否完全执行成功,提取数量,推送数量"""
    try:
        # 查询最新信息
        logs, raws = fetcher.query()
        # 如果查询失败或没有信息则返回
        if logs is None:
            return False, 0, 0

        if len(logs) == 0:
            fetcher.save_stub()
            # 原始数据存在但有效数据不存在,说明当前数据需要被忽略,继续下一批
            return len(raws) != 0, len(raws), 0

        # 执行分析处理动作,得到待发送数据
        infos = anz_fun(logs)
        # 分析处理失败,直接返回
        if infos is None:
            return False, len(raws), 0
        if len(infos) == 0:
            return False, len(raws), 0
    except Exception as e:
        if logger:
            logger.error(str(e))
        return False, 0, 0

    # 将分析结果推送给mq
    fail = None
    idx = 0
    if pusher:
        fail, idx = pusher.put2(infos)
        # 如果推送失败则记录失败点,等待重试
        if fail is not None:
            fetcher.upd_stub(logs[idx])
        else:
            idx = len(infos)

    # 执行点存根信息落盘
    fetcher.save_stub()
    return fail is None, len(raws), idx