# -*- coding: utf-8 -*-

import sqlite3 as s


class s3db:
    """sqlite3数据库功能封装"""

    def __init__(self, dbpath=None):
        """如果构造时给出了数据库路径,则直接打开"""
        self.conn = None
        if dbpath is not None:
            self.open(dbpath)

    def opened(self):
        """判断是否打开了数据库"""
        return self.conn is not None

    def open(self, dbpath):
        """打开指定的数据库,返回值:是否成功"""
        if self.conn is not None:
            return True

        try:
            self.conn = s.connect(dbpath, check_same_thread=False)
            return True
        except Exception as e:
            return False

    def opt_set(self, cmd, val):
        """设定sqlite3配置参数,返回值:是否成功"""
        if self.conn is None:
            return False

        try:
            if not isinstance(val, str):
                val = str(val)
            self.conn.execute("PRAGMA  %s = %s" % (cmd, val))
            return True
        except Exception as e:
            return False

    def opt_def(self):
        """设置默认优化参数"""
        self.opt_set('Synchronous', 'OFF')
        self.opt_set('Journal_Mode', 'WAL')
        self.opt_set('Cache_Size', '16384')

    def close(self):
        """关闭数据库连接"""
        if self.conn is None:
            return True
        self.conn.close()
        self.conn = None

    def exec(self, sql, data=None, commit=True):
        """执行sql语句(不返回结果集的增删改语句).
            data - sql的绑定参数
            commit - 告知是否立即提交.不是立即提交时需要外部执行commit()方法手动提交,提高性能.
            返回值: (是否成功,错误消息)
        """
        try:
            if data is None:
                self.conn.execute(sql)
            else:
                self.conn.execute(sql, data)
            if commit:
                self.conn.commit()
            return True, ''
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def commit(self):
        """手动提交执行结果.返回值(是否成功,错误消息)"""
        try:
            self.conn.commit()
            return True, ''
        except Exception as e:
            self.conn.rollback()
            return False, str(e)


'''
import db_sqlite as dbs
db=dbs.s3db('spd.sqlite3')
q=dbs.s3query(db)
rows,msg=q.query('select * from tbl_infos')
for row in rows:
    print(row[0],row[1])
'''


class s3query:
    """sqlite3数据查询功能封装"""

    def __init__(self, db):
        """构造时绑定数据库对象"""
        self.db = db
        if db.conn:
            self.open(db)

    # 初始化查询对象,可指定数据库对象
    def open(self, db=None):
        """创建查询游标对象."""
        if db is None:
            db = self.db
        self.conn = db.conn
        self.cur = db.conn.cursor()

    def exec(self, sql, param=None, cmt=True):
        """执行sql语句,不要求获取结果集.
            返回值:成功时 - (True,影响的行数)
                  失败时 - (False,错误信息)
        """
        try:
            if param is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, param)
            if cmt:
                self.conn.commit()
            return True, self.cur.rowcount
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def query(self, sql, param=None, fetchsize=None):
        """执行sql查询,得到结果集(默认是得到全部,也可以指定获取的数量)
            返回值:成功时 - (结果集,'')
                  失败时 - (None,错误信息)
        """
        try:
            if param is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, param)
            if fetchsize is None:
                return self.cur.fetchall(), ''
            else:
                return self.cur.fetchmany(size=fetchsize), ''
        except Exception as e:
            return None, str(e)

    def fetch(self, fetchsize):
        """在query使用了fetchsize分批获取之后,继续获取结果集的后续部分
            返回值:成功时 - (结果集,'')
                  失败时 - (None,错误信息)
        """
        try:
            return self.cur.fetchmany(size=fetchsize), ''
        except Exception as e:
            return None, str(e)

    def append(self, obj, cmt=True):
        """轻量级ORM插入实现,obj的类型为表名,obj内含属性为表中字段与对应的值
            返回值:成功时 - (True,影响的行数)
                  失败时 - (False,错误信息)
        """

        def _insert(obj, cmt):
            tbl = type(obj).__name__
            val = []
            fds = []
            dmy = []
            for f in obj.__dict__:
                fds.append(f)
                val.append(obj.__dict__[f])
                dmy.append('?')
            sql = 'insert into %s (%s) values(%s)' % (tbl, ','.join(fds), ','.join(dmy))
            return self.exec(sql, val, cmt)

        if isinstance(obj, list) or isinstance(obj, tuple):
            for o in obj:
                _insert(o, False)
            if cmt:
                return self.db.commit()
            else:
                return True, ''
        else:
            return _insert(obj, cmt)

    def extract(self, sql, filter_fun, param=None, fetchsize=100):
        """执行查询,给出sql和参数param,对结果行进行filter_fun过滤,可设定提取批尺寸fetchsize.
           返回值:成功时 - (结果数量,错误信息)
        """
        rc = 0
        rows, msg = self.query(sql, param, fetchsize)
        if msg: return rc, msg
        while len(rows):
            for row in rows:
                filter_fun(row)
                rc += 1
            rows, msg = self.fetch(fetchsize)
            if msg: return rc, msg
        return rc, msg

    def has(self, name, type='table'):
        """判断指定的库表对象table/index/view是否存在.
            返回值:None - 查询失败,结果未知
                  True/False - 告知是否存在
        """
        rows, msg = self.query("SELECT name FROM sqlite_master WHERE type=? and name=?", (type, name))
        if msg != '':
            return None
        return len(rows) > 0

    def close(self):
        """关闭数据查询对象"""
        if self.cur is not None:
            self.cur.close()
        self.cur = None
        self.conn = None
        self.db = None


# sqlite3简易table功能封装
class s3tbl(s3query):
    def __init__(self, db):
        super().__init__(db)
        self.sql_insert = None
        self.sql_update = None
        self.sql_select = None

    def set_insert(self, sql):
        """绑定insert语句"""
        self.sql_insert = sql

    def set_update(self, sql):
        """绑定update语句"""
        self.sql_update = sql

    def set_select(self, sql):
        """绑定select语句"""
        self.sql_select = sql

    def insert(self, vals, cmt=True):
        """插入记录vals
            返回值:成功时 - (True,影响的行数)
                  失败时 - (False,错误信息)
        """
        return super().exec(self.sql_insert, vals, cmt)

    def insertx(self, lst):
        """插入多条记录lst"""
        for t in lst:
            self.insert(t, False)
        self.conn.commit()

    def update(self, vals, where=None, cmt=True):
        """更新记录
            返回值:成功时 - (True,影响的行数)
                  失败时 - (False,错误信息)
        """
        if where is None:
            return super().exec(self.sql_update, vals, cmt)
        else:
            return super().exec(self.sql_update, vals + where, cmt)

    def query(self, param=None, sql=None):
        """查询结果
            返回值:成功时 - (结果集,'')
                  失败时 - (None,错误信息)
        """
        if sql is None:
            sql = self.sql_select
        return super().query(sql, param)

    def close(self):
        """关闭"""
        super().close()
        self.sql_insert = None
        self.sql_update = None
        self.sql_select = None
