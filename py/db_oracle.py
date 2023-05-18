# -*- coding: utf-8 -*-

import cx_Oracle as co
import platform


def ora_client_init(path=None):
    """用指定的路径对OCI客户端进行初始化;返回值:msg错误消息,空串正常."""
    if path is None:
        if platform.system() == 'Windows':
            path = 'd:/soft/instantclient_11_2/'  # 告知默认oci立即客户端的位置
        else:
            path = '/usr/lib/oracle/11.2/client64/lib/'

    try:
        co.init_oracle_client(path)
        return ''
    except Exception as e:
        msg=str(e)
        if msg!='Oracle Client library has already been initialized':
            print('oracle instant client init fail.\n\t' + str(e))
            return str(e)
        return ''


# 进行oracle客户端的默认初始化.首次初始化失败时可以再次尝试
oci_client_inited_msg = ora_client_init()


class ora_conn_t:
    def __init__(self):
        self.handle = None
        self.ip = None
        self.port = 1521
        self.user = None
        self.pwd = None
        self.db = None
        self.sys_as_dba = True
        self.schema = None

    def open(self):
        """打开或重新打开数据库连接.返回值:msg,告知错误信息,空串为正常"""
        self.close()
        try:
            dsn = co.makedsn(self.ip, self.port, self.db)
            if self.user == 'sys':
                if self.sys_as_dba:
                    self.handle = co.connect(self.user, self.pwd, dsn, encoding="UTF-8", mode=co.SYSDBA)
                else:
                    self.handle = co.connect(self.user, self.pwd, dsn, encoding="UTF-8", mode=co.SYSOPER)
            else:
                self.handle = co.connect(self.user, self.pwd, dsn, encoding="UTF-8")

            if self.schema:
                self.handle.current_schema = self.schema
            return ''
        except Exception as e:
            return str(e)

    def init(self, ip, db, user, pwd, port=1521, sys_as_dba=True):
        self.ip = ip
        self.db = db
        self.user = user
        self.pwd = pwd
        self.port = port
        self.sys_as_dba = sys_as_dba

    def close(self):
        if self.handle is None:
            return
        try:
            self.handle.close()
        except:
            pass
        self.handle = None


# 打开oracle的连接
def make_conn(ip, db, user, pwd, port=1521, sys_as_dba=True):
    conn = ora_conn_t()
    conn.init(ip, db, user, pwd, port, sys_as_dba)
    msg = conn.open()
    if msg:
        print('oracle db connect error:%s' % (msg))
    return conn


# 切换当前默认模式(用户/库)
def switch_schema(conn, name):
    if conn.handle:
        conn.handle.current_schema = name
    conn.schema = name


class query_t:
    """基于连接对象管理游标对象"""

    def __init__(self, conn):
        self.cur = None
        self.conn = conn
        self.open()

    def open(self, conn=None):
        self.close()
        if conn is None:
            conn = self.conn

        if conn.handle is None:
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

    def query(self, sql, dat=None, ext=False, fetchall=True):

        def _make_cols_info(desc):
            if desc is None or not ext:
                return None
            rst = []
            for c in desc:
                rst.append({'name': c[0], 'type': c[1].name[8:], 'size': c[2]})
            return rst

        try:
            if dat:
                s = self.cur.execute(sql, dat)
            else:
                s = self.cur.execute(sql)

            if fetchall:
                return True, s.fetchall(), _make_cols_info(s.description)
            else:
                return True, s, _make_cols_info(s.description)
        except Exception as e:
            return False, e, None

    def prepare(self, sql):
        try:
            self.cur.prepare(sql)
            return ''
        except Exception as e:
            return str(e)

    def exec(self, sql, dat=None, prepare=True, commit=True):
        try:
            if prepare and sql:
                self.cur.prepare(sql)
            if isinstance(dat, list):
                self.cur.executemany(None, dat)
            else:
                self.cur.execute(None, dat)
            if commit:
                self.cur.connection.commit()
            return True, self.cur.lastrowid
        except Exception as e:
            self.cur.connection.rollback()
            return False, e

    def fetch(self, res, count=100):
        try:
            return res.fetchmany(count), ''
        except Exception as e:
            return None, str(e)


# 查询指定的sql,返回元组列表,每个元组对应一行数据.
def query(conn, sql, dat=None, ext=False):
    q = query_t(conn)
    st, rst, cols = q.query(sql, dat, ext)
    if not st:
        conn.open()
        q.open(conn)
        st, rst, cols = q.query(sql, dat, ext)
    q.close()
    if ext:
        return rst, cols
    else:
        return rst


def exec(conn, sql, dat=None, ext=False):
    """在指定的conn上执行sql语句,得到结果.
        返回值:(bool,result)
        对于select语句,result为结果集对象;否则为最后影响记录的rowid
    """

    def do(is_sel):
        q = query_t(conn)
        if is_sel:
            st, res, cols = q.query(sql, dat, ext)
        else:
            st, res = q.exec(sql, dat)
        q.close()
        return st, res

    is_sel = sql.lower().strip().startswith('select')  # 判断是否为select语句
    st, res = do(is_sel)
    if not st:
        conn.open()  # 查询或执行失败的时候,则尝试重新连接后再试一次.
        st, res = do(is_sel)

    return st, res


def norm_field_value(v):
    """尝试将入参v进行基本数据类型转换."""
    if v is None:
        return None
    if isinstance(v, str) or isinstance(v, float) or isinstance(v, int):
        return v
    return str(v)


def make_kvs(conn, sql, dct):
    """从数据库查询结果中构建key/value词典.返回值:(数量,消息),数量为-1时失败,消息告知错误原因"""
    rst = query(conn, sql)
    if isinstance(rst, Exception):
        return -1, str(rst)
    for row in rst:
        dct[row[0]] = row[1].strip()
    return len(rst), ''


def make_objs(conn, sql, objs, dat=None):
    """从数据库查询结果中构建obj列表.返回值:(数量,消息),数量为-1时失败,消息告知错误原因"""
    rst, cols = query(conn, sql, dat, ext=True)
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


def make_dcts(conn, sql, dcts, keyidx=0, dat=None):
    """从数据库查询结果中构建obj词典.返回值:(数量,消息),数量为-1时失败,消息告知错误原因"""
    rst, cols = query(conn, sql, dat, ext=True)
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
