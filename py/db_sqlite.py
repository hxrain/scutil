import sqlite3 as s

from hash_util import *


class s3db:
    def __init__(self, dbpath=None):
        self.conn = None
        if dbpath is not None:
            self.open(dbpath)

    def opened(self):
        return self.conn is not None

    def open(self, dbpath):
        if self.conn is not None:
            return True

        try:
            self.conn = s.connect(dbpath, check_same_thread=False)
            return True
        except Exception as e:
            return False

    def opt_set(self, cmd, val):
        if self.conn is None:
            return False

        try:
            if type(val).__name__ != 'str':
                val = str(val)
            self.conn.execute("PRAGMA  %s = %s" % (cmd, val))
            return True
        except Exception as e:
            return False

    def opt_def(self):
        """设置默认优化参数"""
        self.opt_set('Synchronous', 'OFF')
        self.opt_set('Journal_Mode', 'WAL')
        self.opt_set('Cache Size', '5000')

    def close(self):
        if self.conn is None:
            return True
        self.conn.close()
        self.conn = None

    def exec(self, sql, w=None):
        try:
            if w is None:
                self.conn.execute(sql)
            else:
                self.conn.execute(sql, w)
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
    def __init__(self, db):
        self.db = db
        if db.conn:
            self.open(db)

    # 初始化查询对象,可指定数据库对象
    def open(self, db=None):
        if db is None:
            db = self.db
        self.conn = db.conn
        self.cur = db.conn.cursor()

    def exec(self, sql, param=None, cmt=True):
        try:
            if param is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, param)
            if cmt:
                self.conn.commit()
            return True, ''
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def query(self, sql, param=None):
        try:
            if param is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, param)
            return self.cur.fetchall(), ''
        except Exception as e:
            return None, str(e)

    def has(self, name, type='table'):
        """判断指定的库表对象table/index/view是否存在.返回值:None查询失败,结果未知;True/False告知是否存在"""
        rows, msg = self.query("SELECT name FROM sqlite_master WHERE type=? and name=?", (type, name))
        if msg != '':
            return None
        return len(rows) > 0

    def close(self):
        if self.cur is not None:
            self.cur.close()
        self.cur = None
        self.conn = None
        self.db = None


class s3tbl(s3query):
    def __init__(self, db):
        super().__init__(db)
        self.sql_insert = None
        self.sql_update = None
        self.sql_select = None

    def set_insert(self, sql):
        self.sql_insert = sql

    def set_update(self, sql):
        self.sql_update = sql

    def set_select(self, sql):
        self.sql_select = sql

    def insert(self, vals, cmt=True):
        return super().exec(self.sql_insert, vals, cmt)

    def insertx(self, lst):
        for t in lst:
            self.insert(t, False)
        self.conn.commit()

    def update(self, vals, where=None, cmt=True):
        if where is None:
            return super().exec(self.sql_update, vals, cmt)
        else:
            return super().exec(self.sql_update, vals + where, cmt)

    def query(self, param=None, sql=None):
        if sql is None:
            sql = self.sql_select
        return super().query(sql, param)

    def close(self):
        super().close()
        self.sql_insert = None
        self.sql_update = None
        self.sql_select = None


'''
db=s3db("dat.s3db")
db.opt_def()
sw=s3_writer(db,(0,1))
sw.open('select name,url from cops',"insert into cops(name,url) values(?,?)")
sw.append(('n1','u1'))
sw.append(('n2','u2'))
'''


class s3_writer:
    def __init__(self, db, keyIdx=0):
        self.tbl = s3tbl(db)
        self.keys = None
        self.keyIdx = keyIdx

    def open(self, select_keys, sql_insert=None):
        if self.keys is not None:
            return True

        if sql_insert is not None:
            self.tbl.set_insert(sql_insert)
        try:
            self.keys = set()
            for fields in self.tbl.query(None, select_keys):
                ks = ''.join(fields)
                self.keys.add(calc_key(ks))  # 记录当前行数据的唯一key,便于排重

            return True
        except Exception as e:
            return False

    def append(self, line, cmt=True):
        """追加行内容到数据表.返回值:-1 DB未打开;-2其他错误;1内容重复;2正常完成."""
        if self.keys is None:
            return -1, ''

        key = calc_key(line, self.keyIdx)
        if key in self.keys:
            return 1, ''
        try:
            self.tbl.insert(line, cmt)
            self.keys.add(key)
            return 2, ''
        except Exception as e:
            return -2, 'ERR: ' + str(e) + ' append' + str(line)

    def appendx(self, lst):
        """追加元组列表到文件"""
        if self.keys is None:
            return -1
        for l in lst:
            r, m = self.append(l, False)
            if r < 0:
                print(m)
        self.tbl.conn.commit()
        return 2

    def save(self):
        if self.fp is None:
            return False
        self.fp.flush()
        return True

    def close(self):
        if self.fp is None:
            return False
        self.fp.close()
        self.fp = None
        self.keys = None
        return True
