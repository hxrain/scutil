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
        """强制更新存根信息,在外面推送失败的时候"""
        self.last_time = last_time  # 信息查询的开始时间点
        self.last_id = uuid  # 最后提交失败时的id,此信息需要重试,且从它之后再发送

    def save_stub(self):
        """存根信息落盘"""
        stub = {'last_time': self.last_time, 'last_id': self.last_id}
        rst = dict_save(self.stub_file, stub)
        if not rst:
            self.logger.warn('stub save fail: %s' % (stub))
        else:
            self.logger.info('stub save ok: %s' % (stub))
        return rst

    def query(self, exparam=None):
        sql, param = self.on_make_sql(exparam)
        st, res = self.on_exec(self.conn, sql, param, exparam)
        if not st:
            self.logger.warn('db query error: %s' % (res))
            return None

        rst = []
        for r in res:  # 对查询结果进行遍历
            if self.last_id:
                if self.on_make_onlyval(r, exparam) != self.last_id:
                    continue
                self.last_id = None  # 如果指定了接续记录且遇到了该记录,则可进行后续的正常处理了

            info = self.on_make_info(r, exparam)
            if not self.on_filter(info, exparam):
                rst.append(info)  # 记录需要的输出信息

        if len(rst):
            self.last_time = self.on_get_lasttime(rst[-1], exparam)  # 更新最后的更新时间

        return rst

    def on_make_sql(self, exparam):
        """构造查询sql,以及对应的查询参数"""

    def on_exec(self, conn, sql, param, exparam):
        """基于conn执行sql查询,param是查询参数,exparam是外部给出的扩展参数.返回值:(bool状态,结果集)"""

    def on_make_onlyval(self, row, exparam):
        """从查询结果中构造代表此记录的唯一值"""

    def on_filter(self, info, exparam):
        """对给定的信息进行过滤.返回值:是否需要丢弃"""

    def on_get_lasttime(self, info, exparam):
        """获取信息中的增量时间"""

    def on_make_info(self, row, exparam):
        """从查询结果中构造需要的信息字典"""
