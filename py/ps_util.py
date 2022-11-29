# -*- coding: utf-8 -*-

import psutil
import time

def take_mem_used():
    """获取内存使用信息"""
    mem = psutil.virtual_memory()
    return {'total': mem.total // 1024 // 1024, 'used': mem.used // 1024 // 1024,
            'free': mem.available // 1024 // 1024, 'percent': mem.percent}


def take_swap_used():
    """获取交换分区使用信息"""
    mem = psutil.swap_memory()
    return {'total': mem.total // 1024 // 1024, 'used': mem.used // 1024 // 1024,
            'free': mem.free // 1024 // 1024, 'percent': mem.percent, }


def take_cpu_used(interval=0.5):
    """返回每个cpu核心的使用率.返回值:[每个核心的使用率]"""
    return psutil.cpu_percent(interval=interval, percpu=True)


def take_diskio_used(interval=1):
    """获取磁盘io读写情况,
        返回值:{'persec_read_bytes': 0, 'persec_write_bytes': 921547, 'persec_read_count': 0, 'persec_write_count': 0}
    """
    bt = time.time()
    d1 = psutil.disk_io_counters()
    time.sleep(interval)
    d2 = psutil.disk_io_counters()
    et = time.time()
    interval = (et - bt)

    rst = {}

    def delta(key, unit=1):
        dv = getattr(d2, key) - getattr(d1, key)
        rst['persec_' + key] = int(dv // unit // interval)

    delta('read_bytes')
    delta('write_bytes')
    delta('read_count')
    delta('write_count')
    return rst
