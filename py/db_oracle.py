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
        print('oracle instant client init fail.\n\t' + str(e))
        return str(e)


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

    def query(self, sql, dat=None, ext=False):

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

            return True, s.fetchall(), _make_cols_info(s.description)
        except Exception as e:
            return False, e, None

    def exec(self, sql, dat=None, prepare=True, commit=True):
        try:
            if prepare:
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
