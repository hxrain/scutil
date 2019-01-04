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
import getopt

# ---------------------------------------------------------
# 配置参数.连接超时
conn_timeout = 6
# 配置参数.输出日志的json格式化缩进(None不格式化)
log_json_indent = None
# redis服务器默认地址
redis_addr = '20.0.2.156:8000'

# 进行命令参数的解析
opts, args = getopt.getopt(sys.argv[1:], '', ['dst=', 'timeout='])

# 进行参数值处理
for name, val in opts:
    if name == '--dst':
        redis_addr = val
    if name == '--timeout':
        conn_timeout = int(val)


# ---------------------------------------------------------
def make_ps_logger(psname, path='./'):
    '生成指定进程名字对应的日志记录器'
    if not os.path.exists(path):
        os.mkdir(path)

    # 生成文件写入器
    filehandler = logging.handlers.RotatingFileHandler(path + psname, maxBytes=0, mode='w', backupCount=0)
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    # 生成日志记录器,并绑定文件写入器
    ps_logger = logging.getLogger()
    ps_logger.setLevel(logging.DEBUG)
    ps_logger.addHandler(filehandler)

    # 写入初始启动标识串
    ps_logger.info("")
    ps_logger.info("lua_mgr.START")
    return ps_logger


# ---------------------------------------------------------
# 生成日志记录器
G_log = make_ps_logger("lua_mgr.log")


# ---------------------------------------------------------
def end(code):
    '结束当前脚本,记录结束标识串并退出.'
    if code == 0:
        G_log.info("lua_mgr.END_OK")
    else:
        G_log.info("lua_mgr.END_BAD")
    exit(code)


# ---------------------------------------------------------
def make_redis_client(dst_host, dst_port=None):
    '生成redis客户端对象'
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
def get_red_addr(red):
    '根据redis客户端对象,获取其连接的目标地址'
    red_host = red.connection_pool.connection_kwargs['host']
    red_port = red.connection_pool.connection_kwargs['port']
    red_addr = red_host + ':' + str(red_port)
    return red_addr


# ---------------------------------------------------------
def red_close(red):
    '强制关闭连接池,避免产生TIME_WAIT状态'
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
def redis_lua_load(red, s):
    '装载脚本串s;返回值:成功时为sha字符串;失败时为None.'
    try:
        return red.script_load(s)
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
def load_from_file(src_file):
    '装载指定的文件内容;返回值:None错误;其他为内容'
    try:
        f = open(src_file, 'r')
        s = f.read()
        f.close()
        return s
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, src_file, e)
        return None


# ---------------------------------------------------------
def save_to_file(dst_file, s):
    '保存s到指定的文件dst_file;返回值:None错误;其他为内容长度'
    try:
        f = open(dst_file, 'w')
        f.write(s)
        f.close()
        return len(s)
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, dst_file, e)
        return None


# ---------------------------------------------------------
def redis_lua_loadfile(red, file):
    '装载脚本文件file;返回值:成功时为sha字符串;失败时为None.'
    try:
        s = load_from_file(file)
        return None if s is None else red.script_load(s)
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red),
                    file, e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red),
                    file, e)
        return None


# ---------------------------------------------------------
def redis_lua_loaddir(red, out_file='lua_func.ini', wildcard='Lua_*.lua'):
    '''
        根据通配符wildcard装载脚本文件到red对应的服务器,并将sha结果与脚本文件名的对应关系输出到out_file;
        返回值:装载的文件数量;失败时为None.
    '''

    try:
        out = open(out_file, 'w')
        out.write('[funcs]\n')
        list = glob.glob(wildcard)
        rc = 0
        for f in list:
            sha = redis_lua_loadfile(red, f)
            if sha is None:
                continue
            out.write(os.path.splitext(os.path.basename(f))[0] + '=' + sha + '\n')
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
def redis_lua_exist(red, sha):
    '判断指定sha对应的脚本是否存在;返回值:1存在;0不存在;None出错了.'
    try:
        return 1 if True in red.script_exists(sha) else 0
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
def redis_lua_flush(red):
    '清空全部lua脚本缓存,必须重新装载;返回值:1存在;0不存在;None出错了.'
    try:
        return 1 if red.script_flush() is True else 0
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# ---------------------------------------------------------
def redis_lua_call(red, sha, args=None, key_count=None):
    '''
        调用sha对应的脚本,args为脚本的键与参数列表;key_count告知列表中key的数量,默认认为全部都是key.
        返回值:None出错了;否则为脚本返回内容
    '''
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
def redis_lua_exec(red, s, args=None, key_count=None):
    '''
        调用s对应的脚本,args为脚本的键与参数列表;key_count告知列表中key的数量,默认认为全部都是key.
        返回值:None出错了;否则为脚本返回内容(没有内容时为'')
    '''
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
def redis_lua_kill(red):
    '终止lua脚本的运行;返回值:1完成;0没有阻塞;None出错了.'
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


# ---------------------------------------------------------
def lua_script_preproc(src_file, out_dir='./out/'):
    '''
        对指定的lua脚本进行预处理,进行dofile文件的引入替换,输出到指定路径
        返回值:None出错;>=0为新文件长度
    '''

    def query_lua_dofile(s):
        '在指定的串s中查找lua语句dofile("xxx.lua");返回值:None错误;tuple元组(完整字符串,文件名)'
        try:
            bp = s.find('dofile("')
            if bp == -1:
                return '', ''
            ep = s.find('")', bp + 8)
            if ep == -1:
                return '', ''
            return s[bp:ep + 2], s[bp + 8:ep]
        except Exception as e:
            G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, src_file, e)
            return None

    try:
        # 检查目标目录是否存在
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        # 装载源文件内容
        s = load_from_file(src_file)
        if s is None:
            return None

        basedir = os.path.dirname(src_file)

        # 对源文件内容进行循环检查
        fs, ss = query_lua_dofile(s)
        while fs != '' and ss != '':
            # 装载目标文件内容
            fc = load_from_file(basedir + '/' + ss)
            if fc is None:
                return None
            # 将源文件中的'dofile("xxx.lua")'字符串替换为xxx.lua中的内容
            s = s.replace(fs, fc)
            # 继续查找源文件内容
            fs, ss = query_lua_dofile(s)
        # 最终将处理过的内容输出到目标目录
        return save_to_file(out_dir + os.path.basename(src_file), s)

    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, src_file, e)
        return None


# ---------------------------------------------------------
def lua_dir_preproc(wildcard='Lua_*.lua', out_dir='./out/'):
    '根据通配符预处理脚本文件目录;返回值:装载的文件数量;失败时为None.'
    try:
        list = glob.glob(wildcard)
        rc = 0
        for f in list:
            if lua_script_preproc(f, out_dir) is None:
                return None
            rc = rc + 1
        return rc
    except redis.RedisError as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None
    except Exception as e:
        G_log.error("%s:%d::%s:%s", sys._getframe().f_code.co_name, sys._getframe().f_lineno, get_red_addr(red), e)
        return None


# =========================================================
# redis/lua脚本预处理
filecount = lua_dir_preproc(wildcard='./lua/Lua_*.lua')
if filecount is None:
    end(-1)
else:
    G_log.info("lua_dir_preproc file count is (%d)", filecount)

# 生成redis客户端
G_red = make_redis_client(redis_addr)
if G_red is None:
    end(-2)

# 将预处理后的脚本装载到服务器并记录sha列表
filecount = redis_lua_loaddir(G_red, out_file='./out/lua_func.ini', wildcard='./out/Lua_*.lua')
if filecount is None:
    end(-3)
else:
    G_log.info("redis_lua_loaddir file count is (%d)", filecount)

# =========================================================
# 标记脚本最终执行完毕
end(0)
