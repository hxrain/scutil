import sqlite3 as s
import hashlib


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
            self.conn = s.connect(dbpath)

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
        self.opt_set('Synchronous', 'OFF')
        self.opt_set('Journal_Mode', 'WAL')
        self.opt_set('Cache Size', '5000')

    def close(self):
        if self.conn is None:
            return True
        self.conn.close()
        self.conn = None


class s3tbl:
    def __init__(self, db):
        self.cur = db.conn.cursor()
        self.conn = db.conn
        self.sql_insert = None
        self.sql_update = None
        self.sql_select = None

    def set_insert(self, sql):
        self.sql_insert = sql

    def set_update(self, sql):
        self.sql_update = sql

    def set_select(self, sql):
        self.sql_select = sql

    def insert(self, t, cmt=True):
        self.cur.execute(self.sql_insert, t)
        if cmt:
            self.conn.commit()

    def insertx(self, lst):
        for t in lst:
            self.insert(t, False)
        self.conn.commit()

    def update(self, t, w, cmt=True):
        self.cur.execute(self.sql_update, t + w)
        if cmt:
            self.conn.commit()

    def query(self, w=None, sql=None):
        if sql is None:
            sql = self.sql_select
        if w is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, w)
        return self.cur.fetchall()

    def close(self):
        if self.cur is not None:
            self.cur.close()
        self.cur = None
        self.conn = None
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

    def md5(self, str):
        return hashlib.md5(str.encode('utf-8')).hexdigest()

    def _calc_key(self, line):
        # 计算字符串的MD5值
        if type(self.keyIdx).__name__ == 'int':
            return self.md5(line[self.keyIdx])
        else:
            ks = ''.join(line[self.keyIdx[0]:self.keyIdx[1] + 1])
            return self.md5(ks)

    def open(self, select_keys, sql_insert=None):
        if self.keys is not None:
            return True

        if sql_insert is not None:
            self.tbl.set_insert(sql_insert)
        try:
            self.keys = set()
            for fields in self.tbl.query(None, select_keys):
                ks = ''.join(fields)
                self.keys.add(self.md5(ks))  # 记录当前行数据的唯一key,便于排重

            return True
        except Exception as e:
            return False

    def append(self, line, cmt=True):
        """追加行内容到数据表.返回值:-1 DB未打开;-2其他错误;1内容重复;2正常完成."""
        if self.keys is None:
            return -1, ''

        key = self._calc_key(line)
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
