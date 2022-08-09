from util_base import *

'''

    def _cat_cond(self, info: info_t, cond):
        """ 拼装排重条件与值元组
            cond为['字段1','字段2']时,代表多个字段为and逻辑
            cond为[('字段1','字段2'),('字段3','字段4')]时,代表多个字段组为or逻辑,组内字段为and逻辑
        """
        vals = ()
        cons = ()

        # 统计分组的数量
        grps = 0
        for i in range(len(cond)):
            if isinstance(cond[i], tuple):
                grps += 1

        if grps:
            # 有分组,需要先对分组中的tuple进行检查修正
            for i in range(len(cond)):
                if not isinstance(cond[i], tuple):
                    cond[i] = (cond[i],)

            for fields in cond:
                # 对每个组进行处理,拼装and部分的逻辑串
                vals += tuple(info.__dict__[c] for c in fields)
                cons += ('(' + ' and '.join(tuple(c + '=?' for c in fields)) + ')',)
        else:
            # 无分组,直接拼装and部分的逻辑
            vals = tuple(info.__dict__[c] for c in cond)
            cons += (' and '.join(tuple(c + '=?' for c in cond)),)

        # 多个and条件,进行or连接
        cons = ' or '.join(tuple(c for c in cons))
        return vals, cons

    @guard(locker)
    def check_repeat(self, info: info_t, cond):
        """使用指定的信息对象,根据给定的cond条件(字段名列表),判断其是否重复.
            返回值:None不重复;其他为已有信息的ID
        """
        if len(cond) == 0:
            return None  # 没有给出判重条件,则认为不重复

        val, cnd = self._cat_cond(info, cond)
        rows, msg = self.dbq.query("select id from tbl_infos where %s limit 1" % cnd, val)

        if msg != '':
            _logger.error('info <%s> repeat QUERY fail. DB error <%s>', info.__dict__.__str__(), msg)
            return None

        if len(rows) == 0:
            return None

        return rows[0][0]

'''


# 查询指定的sql,返回元组列表,每个元组对应一行数据.
def query(q, sql, dat=None, ext=False):
    st, rst, cols = q.query(sql, dat, ext)
    if not st:
        q.open(force=True)
        st, rst, cols = q.query(sql, dat, ext)
    if ext:
        return rst, cols
    else:
        return rst


def exec(q, sql, dat=None, ext=False):
    """在指定的conn上执行sql语句,得到结果.
        返回值:(bool,result)
        对于select语句,result为结果集对象;否则为最后影响记录的rowid
    """

    def do(is_sel):
        if is_sel:
            st, res, cols = q.query(sql, dat, ext)
        else:
            st, res = q.exec(sql, dat)
        return st, res

    is_sel = sql.lower().strip().startswith('select')  # 判断是否为select语句
    st, res = do(is_sel)
    if not st:
        q.open()  # 查询或执行失败的时候,则尝试重新连接后再试一次.
        st, res = do(is_sel)

    return st, res


def norm_field_value(v):
    if isinstance(v, str) or isinstance(v, float) or isinstance(v, int):
        return v
    return str(v)


def make_kvs(q, sql, dct):
    """从数据库查询结果中构建key/value词典.返回值:(数量,消息),数量为-1时失败,消息告知错误原因"""
    rst = query(q, sql)
    if isinstance(rst, Exception):
        return -1, str(rst)
    for row in rst:
        dct[row[0]] = row[1].strip()
    return len(rst), ''


def make_objs(q, sql, objs, dat=None):
    """从数据库查询结果中构建obj列表.返回值:(数量,消息),数量为-1时失败,消息告知错误原因"""
    rst, cols = query(q, sql, dat, ext=True)
    if isinstance(rst, Exception):
        return -1, str(rst)

    class obj_t:
        def __init__(self):
            pass

        def __repr__(self):
            rst = []
            for k in self.__dict__:
                rst.append('%s:%s' % (k, self.__dict__[k]))
            return '{%s}' % (','.join(rst))

        def __getitem__(self, item):
            return self.__dict__[item.upper()]

    colcnt = len(cols)
    for row in rst:
        obj = obj_t()
        for i in range(colcnt):
            name = cols[i]['name']
            obj.__dict__[name] = norm_field_value(row[i])
        objs.append(obj)
    return len(rst), ''


def make_dcts(q, sql, dcts, keyidx=0, dat=None):
    """从数据库查询结果中构建obj词典.返回值:(数量,消息),数量为-1时失败,消息告知错误原因"""
    rst, cols = query(q, sql, dat, ext=True)
    if isinstance(rst, Exception):
        return -1, str(rst)
    colcnt = len(cols)

    if isinstance(keyidx, str):
        for i, c in enumerate(cols):
            if c['name'] == keyidx:
                keyidx = i
                break

    for row in rst:
        dct = {}
        for i in range(colcnt):
            dct[cols[i]['name']] = norm_field_value(row[i])
        dcts[row[keyidx]] = dct
    return len(rst), ''


class db_fetch_t:
    def __init__(self, fname, db, logger):
        self.db = db
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
            self.logger.warn('stub file load fail: %s' % (self.stub_file))
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
        st, res = self.on_exec(self.db, sql, param, exparam)
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

    def on_exec(self, db, sql, param, exparam):
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
            logger.error(ei(e))
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
