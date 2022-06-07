import pymysql
import pymysql.constants.FIELD_TYPE as field_types
from warnings import filterwarnings

filterwarnings("ignore", category=pymysql.Warning)

# 字段类型对应的类型名称
field_type_names = {field_types.TIME: 'TIEM', field_types.DOUBLE: 'DOUBLE', field_types.STRING: 'STRING', field_types.DECIMAL: 'DECIMAL', field_types.NEWDATE: 'NEWDATE',
                    field_types.BIT: 'BIT', field_types.BLOB: 'BLOB', field_types.CHAR: 'CHAR', field_types.DATE: 'DATE', field_types.DATETIME: 'DATETIME',
                    field_types.JSON: 'JSON', field_types.LONG: 'LONG', field_types.LONGLONG: 'LONGLONG', field_types.LONG_BLOB: 'LONG_BLOB',
                    field_types.MEDIUM_BLOB: 'MEDIUM_BLOB', field_types.ENUM: 'ENUM', field_types.FLOAT: 'FLOAT', field_types.GEOMETRY: 'GEOMETRY', field_types.INT24: 'INT24',
                    field_types.NEWDECIMAL: 'NEWDECIMAL', field_types.TIMESTAMP: 'TIMESTAMP',
                    field_types.SHORT: 'SHORT', field_types.YEAR: 'YEAR', field_types.VARCHAR: 'VARCHAR', field_types.TINY_BLOB: 'TINY_BLOB',
                    field_types.VAR_STRING: 'VAR_STRING', field_types.SET: 'SET', field_types.NULL: 'NULL'}

text_field_types = {
    field_types.BIT,
    field_types.BLOB,
    field_types.LONG_BLOB,
    field_types.MEDIUM_BLOB,
    field_types.STRING,
    field_types.TINY_BLOB,
    field_types.VAR_STRING,
    field_types.VARCHAR,
    field_types.GEOMETRY,
}


def is_text_type(type):
    """判断字段类型是否为文本类型"""
    return type in text_field_types


class mysql_conn_t:
    def __init__(self, host=None, db=None, user=None, pwd=None, port=3306):
        self.handle = None
        self.host = None
        self.port = 3306
        self.user = None
        self.pwd = None
        self.db = None
        self.init(host, db, user, pwd, port)

    def open(self, autocommit=False):
        """打开或重新打开数据库连接.返回值:msg,告知错误信息,空串为正常"""
        self.close()
        try:
            self.handle = pymysql.connect(host=self.host, port=self.port,
                                          user=self.user, password=self.pwd,
                                          database=self.db, autocommit=autocommit)
            return ''
        except Exception as e:
            return str(e)

    def init(self, host, db, user, pwd, port=3306):
        self.host = host
        self.db = db
        self.user = user
        self.pwd = pwd
        self.port = port

    def close(self):
        if self.handle is None:
            return
        try:
            self.handle.close()
        except:
            pass
        self.handle = None


# 打开mysql的连接
def make_conn(ip, db, user, pwd, port=3306):
    conn = mysql_conn_t(ip, db, user, pwd, port)
    msg = conn.open()
    if msg:
        print('mysql db connect error:%s' % (msg))
    return conn


class query_t:
    """基于连接对象管理游标对象"""

    def __init__(self, conn):
        self.cur = None
        self.conn = conn
        self.open()

    def open(self, conn=None, force=False):
        self.close()
        if conn is None:
            conn = self.conn

        if conn.handle is None or force:
            msg = conn.open()
            if msg: return msg
        try:
            self.cur = conn.handle.cursor()
        except Exception as e:
            return str(e)
        return ''

    def close(self):
        if self.cur is None:
            return
        try:
            self.cur.close()
        except:
            pass
        self.cur = None

    def query(self, sql, dat=None, ext=False):

        def _make_cols_info(desc):
            if desc is None or not ext:
                return None

            rst = []
            for c in desc:
                rst.append({'name': c[0], 'type': field_type_names.get(c[1], 'OTHER'), 'size': c[3]})
            return rst

        try:
            if dat:
                s = self.cur.execute(sql, dat)
            else:
                s = self.cur.execute(sql)
            if not self.conn.handle.get_autocommit():
                self.cur.connection.commit()  # 在非自动提交模式下,查询也需要提交才能得到其他连接上的最新结果
            return True, self.cur.fetchall(), _make_cols_info(self.cur.description)
        except Exception as e:
            return False, e, None

    def exec(self, sql, dat=None, commit=True):
        try:
            if isinstance(dat, list):
                r = self.cur.executemany(sql, dat)
            else:
                r = self.cur.execute(sql, dat)
            if commit:
                self.cur.connection.commit()
            return True, self.cur.lastrowid or r
        except Exception as e:
            self.cur.connection.rollback()
            return False, e
