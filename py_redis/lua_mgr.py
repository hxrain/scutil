#!/usr/bin/python
# coding:utf-8

# 可以使用redis集群客户端
# import rediscluster
# G_red=rediscluster.StrictRedisCluster(startup_nodes=[{"host": redis_host_addr, "port": redis_host_port}],
#                                     decode_responses=True,socket_timeout=conn_timeout)

# 使用redis主从客户端
import redis
import os
import time
import json
import sys
import socket
import struct
from itertools import chain
import logging
import logging.handlers
import glob

# ---------------------------------------------------------
# 配置参数.连接超时
conn_timeout = 6
# 配置参数.输出日志的json格式化缩进(None不格式化)
log_json_indent = None

# 本地主节点地址
addr_local_master = '127.0.0.1:8000'


# ---------------------------------------------------------
# 生成指定进程名字对应的日志记录器
def make_ps_logger(psname, path='./log/'):
    if not os.path.exists(path):
        os.mkdir(path)

    # 生成文件写入器
    filehandler = logging.handlers.RotatingFileHandler(path + psname, maxBytes=1024 * 1024 * 16, backupCount=64)
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    # 生成日志记录器,并绑定文件写入器
    ps_logger = logging.getLogger()
    ps_logger.setLevel(logging.DEBUG)
    ps_logger.addHandler(filehandler)

    # 写入初始启动标识串
    ps_logger.info("")
    ps_logger.info("CHKREDIS.START")
    return ps_logger


# ---------------------------------------------------------
# 生成日志记录器
G_log = make_ps_logger("chkredis.log")


# ---------------------------------------------------------
# 结束当前脚本,记录结束标识串并退出.
def end(code):
    if code == 0:
        G_log.info("CHKREDIS.END_OK")
    else:
        G_log.info("CHKREDIS.END_BAD")
    exit(code)


# ---------------------------------------------------------
# 生成redis客户端对象
def make_redis_client(dst_host, dst_port=None):
    if dst_host is None and dst_port is None:
        return None

    if dst_port is None and ':' in dst_host:
        # 使用'ip:port'格式,需要转换
        dst_addr = dst_host
        tmp = dst_host.split(':')
        dst_host = tmp[0]
        dst_port = int(tmp[1])
    else:
        dst_addr = dst_host + ':' + str(dst_port)

    try:
        # 生成连接池,给定连接参数
        pool = redis.ConnectionPool(host=dst_host, port=dst_port, decode_responses=True,
                                    socket_timeout=conn_timeout)
        # 生成客户端并绑定连接池
        return redis.StrictRedis(connection_pool=pool)
    except redis.RedisError as e:
        G_log.error("make_redis_client:%s:%s", dst_addr, e)
        return None
    except Exception as e:
        G_log.error("make_redis_client:%s:%s", dst_addr, e)
        return None


# ---------------------------------------------------------
# 根据redis客户端对象,获取其连接的目标地址
def get_red_addr(red):
    red_host = red.connection_pool.connection_kwargs['host']
    red_port = red.connection_pool.connection_kwargs['port']
    red_addr = red_host + ':' + str(red_port)
    return red_addr


# ---------------------------------------------------------
# 强制关闭连接池,避免产生TIME_WAIT状态
def red_close(red):
    all_conns = chain(red.connection_pool._available_connections,
                      red.connection_pool._in_use_connections)
    for connection in all_conns:
        if connection._sock is None:
            continue
        # 调整socket为强制关闭,不要进入TIME_WAIT状态
        connection._sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        # 直接调用close不要经过shutdown阶段
        connection._sock.close()
    # 再关闭连接内部其他资源
    red.connection_pool.disconnect()


# ---------------------------------------------------------
# 装载脚本串s;返回值:成功时为sha字符串;失败时为None.
def redis_lua_load(red, s):
    try:
        return red.script_load(s)
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
# 装载脚本文件file;返回值:成功时为sha字符串;失败时为None.
def redis_lua_loadfile(red, file):
    try:
        f = open(file, 'r')
        s = f.read()
        f.close()
        return red.script_load(s)
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red),
                    file, e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red),
                    file, e)
        return None


# ---------------------------------------------------------
# 装载脚本文件file;返回值:装载的文件数量;失败时为None.
def redis_lua_loaddir(red, out_file='out.ini', dir=None):
    try:
        out = open(out_file, 'w')
        out.write('[funcs]\n')
        list = glob.glob('Lua_*.lua') if dir is None else glob.glob(dir)
        rc = 0
        for f in list:
            sha = redis_lua_loadfile(red, f)
            if sha is None:
                continue
            out.write(f.split('.')[0] + '=' + sha + '\n')
            rc = rc + 1
        out.close()
        return rc
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
# 判断指定sha对应的脚本是否存在;返回值:1存在;0不存在;None出错了.
def redis_lua_exist(red, sha):
    try:
        return 1 if True in red.script_exists(sha) else 0
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
# 清空全部lua脚本缓存,必须重新装载;返回值:1存在;0不存在;None出错了.
def redis_lua_flush(red):
    try:
        return 1 if red.script_flush() is True else 0
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
# 调用sha对应的脚本,args为脚本的键与参数列表;key_count告知列表中key的数量,默认认为全部都是key.
# 返回值:None出错了;否则为脚本返回内容
def redis_lua_call(red, sha, args=None, key_count=None):
    try:
        if key_count is None:
            key_count = 0 if args is None else len(args)
        return red.evalsha(sha, key_count, args)
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
# 调用s对应的脚本,args为脚本的键与参数列表;key_count告知列表中key的数量,默认认为全部都是key.
# 返回值:None出错了;否则为脚本返回内容(没有内容时为'')
def redis_lua_exec(red, s, args=None, key_count=None):
    try:
        if key_count is None:
            key_count = 0 if args is None else len(args)
        rc = red.eval(s, key_count, args)
        return '' if rc is None else rc
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
# 终止lua脚本的运行;返回值:1完成;0没有阻塞;None出错了.
def redis_lua_kill(red):
    try:
        return 1 if red.script_kill() is True else 0
    except redis.RedisError as e:
        if 'NOTBUSY' in e.message:
            return 0
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# =========================================================

G_red = make_redis_client('20.0.2.156:8000')

G_log.info(redis_lua_load(G_red, 'return 12'))
G_log.info(redis_lua_exist(G_red, 'bc1911793137c7c871ce1616c22ce4461d9186f7'))
G_log.info(redis_lua_call(G_red, 'bc1911793137c7c871ce1616c22ce4461d9186f7'))
G_log.info(redis_lua_exec(G_red, 'local var={}'))
G_log.info(redis_lua_flush(G_red))
G_log.info(redis_lua_kill(G_red))
G_log.info(redis_lua_loaddir(G_red))

# 标记脚本最终执行完毕
end(0)
