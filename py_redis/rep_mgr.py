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
import socket
import struct
from itertools import chain
import logging
import logging.handlers

# ---------------------------------------------------------
# 配置参数.连接超时
conn_timeout = 6
# 配置参数.输出日志的json格式化缩进(None不格式化)
log_json_indent = None

# 远程主节点地址
addr_remote_master = '127.0.0.1:8002'
# 本地主节点地址
addr_local_master = '127.0.0.1:8000'
# 本地全部节点地址
addr_local_list = ['127.0.0.1:8000', '127.0.0.1:8001']


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
# 从redis中查询必要信息
def query_redis_info(red):
    dst_host = red.connection_pool.connection_kwargs['host']
    dst_port = red.connection_pool.connection_kwargs['port']
    dst_addr = dst_host + ':' + str(dst_port)
    try:
        info = red.info()

        rc = {}
        # 状态.上线时间sec
        rc['svr.uptime'] = info['uptime_in_seconds']
        rc['svr.addr'] = dst_addr
        # 网络
        rc['net.cmds'] = info['total_commands_processed']
        rc['net.bytes_in'] = info['total_net_input_bytes']
        rc['net.bytes_out'] = info['total_net_output_bytes']
        rc['net.bytes_out'] = info['total_net_output_bytes']
        # 状态.内存用量bytes
        rc['mem.total'] = info['used_memory']
        # 状态.内存峰值bytes
        rc['mem.peak'] = info['used_memory_peak']

        # rdb 快照是否开启
        rc['rdb.enabled'] = 1 if info['rdb_last_save_time'] != -1 else 0
        if rc['rdb.enabled'] != 0:
            # rdb 是否在存盘过程中
            rc['rdb.saving'] = 1 if info['rdb_bgsave_in_progress'] != 0 else 0
            # rdb 最后的存盘状态
            rc['rdb.last_state'] = info['rdb_last_bgsave_status']
            # rdb 最后的存盘用时
            rc['rdb.last_usetime'] = info['rdb_last_bgsave_time_sec']
            # rdb 待存盘条目数
            rc['rdb.remain'] = info['rdb_changes_since_last_save']

        # aof 追加是否开启
        rc['aof.enabled'] = info['aof_enabled']
        if rc['aof.enabled'] != 0:
            # aof 是否在重建存盘中
            rc['aof.saving'] = info['aof_rewrite_in_progress']
            # aof 最后的重建存盘状态
            rc['aof.last_state'] = info['aof_last_bgrewrite_status']
            # aof 最后的重建存盘用时
            rc['rdb.last_usetime'] = info['aof_last_rewrite_time_sec']
            # aof 最后的实时写盘状态
            rc['aof.real_state'] = info['aof_last_write_status']

        # 复制状态.节点模式:0从节点/1主节点/2级联主节点
        rc['rep.mode'] = 1 if info['role'] == 'master' else 0

        # 如果是从节点,则记录主节点信息
        if info['role'] == 'slave':
            # 从节点.主节点地址
            rc['rep.master.addr'] = info['master_host'] + ':' + str(info['master_port'])
            # 从节点.主节点是否在线:1/0
            rc['rep.master.link'] = 1 if info['master_link_status'] == 'up' else 0
            # 从节点.是否与主节点同步了:1/0
            rc['rep.master.sync'] = 1 if info['master_repl_offset'] == info['slave_repl_offset'] else 0

        # 拥有的从节点数量
        slaves = int(info['connected_slaves'])
        rc['rep.slaves'] = slaves
        if slaves != 0:
            # 拥有从节点的从节点,变为级联节点
            if rc['rep.mode'] == 0:
                rc['rep.mode'] = 2
            # 拥有的从节点状态
            for i in range(0, rc['rep.slaves']):
                # 生成从节点key名字
                slave_key = 'rep.slave' + str(i)
                # 获取从节点信息
                si = info['slave' + str(i)]
                # 生成从节点地址:'ip:port'
                rc[slave_key + '.addr'] = si['ip'] + ':' + str(si['port'])
                # 生成从节点在线状态:1/0
                rc[slave_key + '.link'] = 1 if si['state'] == 'online' else 0
                # 生成从节点同步状态(是否与主节点同步了):1/0
                rc[slave_key + '.sync'] = 1 if si['offset'] == info['master_repl_offset'] else 0

        # 集群状态:1/0
        rc['clt.enabled'] = info['cluster_enabled']
        if rc['clt.enabled'] != 0:
            # 动态获取集群信息
            info = red.cluster('info')
            # 获取集群状态:ok/...
            rc['clt.state'] = info['cluster_state']
            # 获取集群节点数量
            rc['clt.nodes'] = info['cluster_known_nodes']
            # 获取集群节点信息
            info = red.cluster('nodes')
            nc = 0
            for nip in info:
                # 拼装集群节点标识
                nid = 'clt.nodes' + str(nc)
                # 节点地址
                rc[nid + '.addr'] = nip
                # 节点在线状态
                rc[nid + '.link'] = 1 if info[nip]['connected'] is True else 0
                # 节点主从模式:1/0
                rc[nid + '.mode'] = 1 if 'master' in info[nip]['flags'] else 0
                nc = nc + 1

        return rc
    except redis.RedisError as e:
        G_log.error("query_redis_info:%s:%s", dst_addr, e)
        return None
    except Exception as e:
        G_log.error("query_redis_info:%s:%s", dst_addr, e)
        return None


# ---------------------------------------------------------
# redis 复制集群管理器功能封装
class redis_rep_mgr:
    # -----------------------------------------------------
    def __init__(self, addr_list):
        self.reds = {}
        self.addr_list = addr_list
        for addr in addr_list:
            self.reds[addr] = make_redis_client(addr)

    # -----------------------------------------------------
    # 内部动作,让指定的red节点变为dst的从节点;dst为None则让red变为主节点
    def __slaveof__(self, red, dst, check_loopback=False):
        red_addr = get_red_addr(red)

        try:
            if dst is None:
                red.slaveof('no', 'one')
            else:
                if check_loopback:
                    # 当前red在指向dst之前,需要校验dst是否又指向了red,避免出现环路.
                    dst_conn = make_redis_client(dst)
                    dst_stat = query_redis_info(dst_conn)
                    red_close(dst_conn)
                    if dst_stat is None:
                        G_log.error("__slaveof__:%s=>%s:%s", red_addr, dst, 'dst not connect.')
                        return False

                    if 'rep.master.addr' in dst_stat and dst_stat['rep.master.addr'] == red_addr:
                        G_log.warn("__slaveof__:%s=>%s:%s", red_addr, dst, 'dst is self''s slave. please retry.')
                        return False

                tmp = dst.split(':')
                red.slaveof(tmp[0], int(tmp[1]))
            return True
        except redis.RedisError as e:
            G_log.error("__slaveof__:%s=>%s:%s", red_addr, dst, e)
            return False
        except Exception as e:
            G_log.error("__slaveof__:%s=>%s:%s", red_addr, dst, e)
            return False

    # -----------------------------------------------------
    # 根据给定的状态信息,判断是否同步进行中
    def __is_syncing__(self, stat):
        if 'rep.master.sync' in stat:
            if stat['rep.master.sync'] == 0:
                return True
        for i in range(0, stat['rep.slaves']):
            if stat['rep.slave' + str(i) + '.sync'] == 0:
                return True
        return False

    # -----------------------------------------------------
    # 等待red完成同步,time为等待的时间.
    # 返回值:是否同步等待完成
    def __wait_sync__(self, red, wait):
        if time is None or time == 0:
            return True
        self.last_stat = query_redis_info(red)
        if self.last_stat is None:
            return False

        host_addr = get_red_addr(red)

        for i in range(0, wait):
            if not self.__is_syncing__(self.last_stat):
                return True
            G_log.info("__wait_sync__(%s,%d):%d", host_addr, wait, i)
            time.sleep(1)
            self.last_stat = query_redis_info(red)
            if self.last_stat is None:
                return False

        G_log.warn("__wait_sync__(%s,%d) timeout.", host_addr, wait)
        return False

    # -----------------------------------------------------
    # 等待red变成指定的mode
    def __wait_mode__(self, red, mode, wait):
        if time is None or time == 0:
            return True
        self.last_stat = query_redis_info(red)
        if self.last_stat is None:
            return False

        host_addr = get_red_addr(red)

        for i in range(0, wait):
            if self.last_stat['rep.mode'] == mode:
                return True

            G_log.info("__wait_mode__(%s,%d,%d):%d", host_addr, mode, wait, i)
            time.sleep(1)

            self.last_stat = query_redis_info(red)
            if self.last_stat is None:
                return False

        G_log.warn("__wait_mode__(%s,%d,%d) timeout.", host_addr, mode, wait)
        return False

    # -----------------------------------------------------
    # 查询指定redis节点的状态
    def query(self, addr):
        if addr not in self.addr_list:
            return None
        self.last_stat = query_redis_info(self.reds[addr])
        return self.last_stat

    # -----------------------------------------------------
    # 输出本地redis复制集的状态
    def status(self):
        for addr in self.reds:
            info = query_redis_info(self.reds[addr])
            G_log.info(json.dumps(info, sort_keys=True, indent=log_json_indent))

    # -----------------------------------------------------
    # 遍历当前redis列表中的全部节点,让loc_master成为新的主节点;如果当前节点正在sync中则wait指示需要等待的时间
    # 如果给定了远程主节点rmt_master,则loc_master节点就会变为中继节点
    # 返回值:是否成功True/False
    def follow(self, loc_master, rmt_master=None, wait=0):
        # 对全部red连接进行遍历
        for curr_node in self.reds:
            # 取出一个连接
            red = self.reds[curr_node]
            # 尝试等待此连接完成同步状态
            self.__wait_sync__(red, wait)

            # 获取当前连接的最新状态
            if self.last_stat is None:
                self.last_stat = query_redis_info(red)

            if self.last_stat is None:
                continue

            if loc_master == curr_node:
                # 如果当前连接应该变为本地新主
                if rmt_master is not None:
                    if 'rep.master.addr' in self.last_stat and self.last_stat['rep.master.addr'] == rmt_master:
                        continue
                    # 如果当前节点还需要挂载到远程节点
                    self.__slaveof__(red, rmt_master, True)
                else:
                    # 不用挂载到远程,则当前节点变为主节点
                    if self.last_stat['rep.mode'] == 1:
                        continue
                    self.__slaveof__(red, None)
            else:
                # 当前连接不是目标节点,则尝试进行主从切换
                if 'rep.master.addr' in self.last_stat and self.last_stat['rep.master.addr'] == loc_master:
                    continue
                if self.__slaveof__(red, loc_master):
                    self.__wait_mode__(red, 0, wait)

        # 遍历完成后,尝试等待节点状态的转换
        if rmt_master is not None:
            self.__wait_mode__(self.reds[loc_master], 2, wait)
        else:
            self.__wait_mode__(self.reds[loc_master], 1, wait)

    # -----------------------------------------------------
    # 关闭全部的redis客户端连接,不产生TIME_WAIT状态
    def close(self):
        for curr_node in self.reds:
            red_close(self.reds[curr_node])


# ---------------------------------------------------------
# 校验初始参数
if addr_local_master not in addr_local_list:
    G_log.error('local_master(%s) not in local_list(%s).', addr_local_master, addr_local_list)
    end(-1)

# 定义复制集管理器
G_redis_rep_master = redis_rep_mgr(addr_local_list)

# 让指定的节点成为本地复制集的主节点
G_redis_rep_master.follow(addr_local_master, addr_remote_master, 5)
# 再次尝试
G_redis_rep_master.follow(addr_local_master, addr_remote_master, 5)

# 输出最终状态
G_redis_rep_master.status()
# 关闭连接
G_redis_rep_master.close()
# =========================================================

# 标记脚本最终执行完毕
end(0)
