#! /usr/bin/env python
# coding=utf-8
import psutil
import datetime
import time
import os
import logging  
import logging.handlers
import xml.etree.ElementTree as ET

'''
    进程监控脚本的设计目标：
    1 待监控的进程通过命令行特征进行区分，避免命令路径无法区分多重性。
    2 配置信息使用简单的xml格式描述，可增加命令启动后的跟随处理事件（执行另外的命令行）。
    3 监控脚本启动时，不破坏已有环境，无缝接管待监控环境。
    4 监控脚本同时输出系统静态信息与动态信息，并输出监控目标进程的动态信息。
    5 配置信息错误或不存在时，反复尝试直到读取解析成功，降低部署调整时的工作量。
    6 监控目标的状态检查周期为500毫秒
    7 日志输出文件按大小进行控制，总数量进行控制，避免占满磁盘空间.
    8 监控日志输出内容简要说明：
        A) 2018-12-21 10:41:19,512 ::           时间格式为（带有逗号分隔的毫秒） 
        B) 'BOOT::.....'                        监控脚本启动时输出 
        C) 'OS::'                               间隔10秒输出系统动态信息
        D) 'START::'                            监控目标首次启动时输出 
        E) 'RESTART::'                          监控目标被重复拉起时立刻输出
        F) 'OKAY::'                             监控目标状态正常时间隔10秒输出 
        G) 'BADCLI::'                           目标命令行启动失败时输出 
        H) 'BADCFG::'                           配置信息读取解析失败时输出 

    TODO:
        A) 进行linux环境配置，完成自启动与安装(或等待安装部署脚本处理)
        B) 进行伴生进程模式的扩展，用一份脚本完成对自身的进程监控。
'''

#-----------------------------------------------------------
#休眠指定的毫秒
def sleep(ms):
    time.sleep(ms/1000.0)

#-----------------------------------------------------------
#生成指定进程名字对应的日志记录器
def make_ps_logger(psname,path='./log/'):
    if not os.path.exists(path):
        os.mkdir(path)
    
    ps_logger = logging.getLogger()
    ps_logger.setLevel(logging.DEBUG)

    filehandler = logging.handlers.RotatingFileHandler(path+psname, maxBytes=1024 * 1024 * 16, backupCount=64)
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(message)s'))
    ps_logger.addHandler(filehandler)
    return ps_logger

#-----------------------------------------------------------
log=None

#-----------------------------------------------------------
#生成系统初始状态信息
def make_static_sysinfo():
    try:
        rc={}
        rc['psutil_version']=psutil.version_info
        rc['boot_time']=datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")#启动时间
        rc['cpu_count']=psutil.cpu_count(logical=False)     #物理CPU核数
        rc['cpu_cores']=psutil.cpu_count()                  #逻辑CPU核数
        rc['disk_partitions']=psutil.disk_partitions()      #磁盘分区信息
        rc['net_if_stats']=psutil.net_if_stats()            #网卡接口状态
        rc['net_if_addrs']=psutil.net_if_addrs()            #所有网卡的地址信息
        return rc
    except:
        return None
#-----------------------------------------------------------
#生成系统动态状态信息
def make_realtime_sysinfo():
    try:
        rc={}
        rc['cpu_percent']=psutil.cpu_percent(percpu=True)   #CPU的使用率

        mi=psutil.virtual_memory()                          #内存使用
        rc['memory.free(G)']=round(mi.free / (1024.0 * 1024.0 * 1024.0), 4)
        rc['memory.total(G)']=round(mi.total / (1024.0 * 1024.0 * 1024.0), 4)

        si=psutil.swap_memory()                             #swap使用
        rc['swap.free(G)']=round(si.free / (1024.0 * 1024.0 * 1024.0), 4)
        rc['swap.total(G)']=round(si.total / (1024.0 * 1024.0 * 1024.0), 4)

        di=psutil.disk_usage('/')                           #磁盘使用
        rc['disk.free(G)']=round(di.free / (1024.0 * 1024.0 * 1024.0), 4)
        rc['disk.total(G)']=round(di.total / (1024.0 * 1024.0 * 1024.0), 4)

        ii=psutil.disk_io_counters()                        #磁盘IO情况
        rc['disk.read_bytes(M)']=round(ii.read_bytes / (1024.0 * 1024.0), 4)
        rc['disk.write_bytes(M)']=round(ii.write_bytes / (1024.0 * 1024.0), 4)
        rc['disk.read_time(s)']=round(ii.read_time / (1000.0), 3)
        rc['disk.write_time(s)']=round(ii.write_time / (1000.0), 3)
        return rc
    except:
        return None
#-----------------------------------------------------------
#获取指定pid进程的信息
def make_realtime_psinfo(pid):
    try:
        pi=psutil.Process(pid)
        rc={}
        rc['name']=pi.name();                               #进程文件名
        rc['path']=pi.exe();                                #进程文件路径
        rc['cmdline']=' '.join(pi.cmdline());                #进程命令行
        rc['create_time']=datetime.datetime.fromtimestamp(pi.create_time()).strftime("%Y-%m-%d %H:%M:%S")
        rc['thread_count']=pi.num_threads()                 #进程内部线程数量

        ti=pi.cpu_times()                                   #进程cpu用时情况
        rc['cpu_times.user(s)']=round(ti.user / (1000.0), 3)
        rc['cpu_times.sys(s)']=round(ti.system / (1000.0), 3)
        rc['cpu_times.children(s)']=round((ti.children_user+ti.children_system)/ (1000.0), 3)

        mi=pi.memory_info()                                 #内存使用
        rc['memory.rss(M)']=round(mi.rss / (1024.0 * 1024.0), 4)
        rc['memory.vms(M)']=round(mi.vms / (1024.0 * 1024.0), 4)

        ii=pi.io_counters()                                 #进程使用的io情况
        rc['disk.read_bytes(M)']=round(ii.read_bytes / (1024.0 * 1024.0), 4)
        rc['disk.write_bytes(M)']=round(ii.write_bytes / (1024.0 * 1024.0), 4)
        rc['disk.other_bytes(M)']=round(ii.other_bytes / (1024.0 * 1024.0), 4)
        return rc
    except:
        return None

#-----------------------------------------------------------
#尝试根据命令行字符串查找对应的pid
def find_pid_by_cmdline(cmdline):
    for pid in psutil.pids():
        pi=make_realtime_psinfo(pid)
        if pi!=None and pi['cmdline']==cmdline:
            return pid
    return 0

#-----------------------------------------------------------
#启动指定的命令行,可进行重复性检查;返回值：进程pid,0错误
def start_cmdline(cli,repeat_check=False):
    try:
        if repeat_check and find_pid_by_cmdline(cli)!=0:
            return 0
            
        sp= psutil.Popen(cli,close_fds=True)
        return sp.pid
    except:
        log.error("BADCLI::%s",cli)
        return 0

#-----------------------------------------------------------
#待监控进程条目信息.返回值:0正常;1新建;2重建
class mon_item_t:
    #-------------------------------------------------------
    def __init__(self,cmdline,onstart):
        self.pid=find_pid_by_cmdline(cmdline)               #初始启动，要判断目标项是否已经存在
        self.cmdline=cmdline
        self.onstart=onstart
    #-------------------------------------------------------
    #执行监控项的检查
    def check(self,log_on_ok):
        if self.pid==0:                                     #目标初始就不存在
            self.pid=start_cmdline(self.cmdline)
            if self.pid!=0:                                 #启动命令行与附带的事件
                log.info("START::%s",make_realtime_psinfo(self.pid))
                if self.onstart:
                    start_cmdline(self.onstart,True)        #需要对附加事件命令进行重复性判断，避免无限创建
            return 1
        else:                                               #目标存在需检查有效性
            pi=make_realtime_psinfo(self.pid)
            if pi==None or pi['cmdline']!=self.cmdline:     #目标无效，需要启动命令行与附带的事件
                self.pid=start_cmdline(self.cmdline)
                if self.pid!=0:
                    log.info("RESTART::%s",make_realtime_psinfo(self.pid))
                    if self.onstart:
                        start_cmdline(self.onstart,True)    #需要对附加事件命令进行重复性判断，避免无限创建
                return 2
            else:                                           #目标确实有效，根据标记给出日志
                if log_on_ok!=0:
                    log.info("OKAY::%s",pi)
                return 0

#-----------------------------------------------------------
#从配置文件之后获取待监控的程序列表
def get_monitor_lists(cfgname):
    try:
        root = ET.parse(cfgname).getroot()
        items=root.find('items')
        rc=[]
        for i in items.findall('cmdline'):
            onstart=''
            if 'onstart' in i.attrib:
                onstart=i.attrib['onstart']
            rc.append(mon_item_t(i.text,onstart))
        return rc
    except:
        log.error("BADCFG::%s",cfgname)
        return None

#-----------------------------------------------------------
#对监控列表进行检查，进行必要的进程创建动作
def check_monitor_lists(items,log_on_ok=0):
    for i in items:
        i.check(log_on_ok)


#***********************************************************
#主函数启动
#***********************************************************

#生成日志记录器
log=make_ps_logger("monitor.log")

#输出系统静态信息
log.info("")
log.info("BOOT::%s",make_static_sysinfo())
log.info("")

#输出系统动态信息
log.info("OS::%s",make_realtime_sysinfo())

#读取监控配置列表,读取失败则反复尝试
mon_items=None
while mon_items==None:
    mon_items=get_monitor_lists('monitor.xml')
    sleep(1000)

#先立即进行一次进程启动检查
check_monitor_lists(mon_items)

#进程状态周期检查,同时周期性输出系统状态
scount=1
while 1:
    check_monitor_lists(mon_items,scount%10==0)
    scount=scount+1
    if scount % 20 == 0:
        log.info("OS::%s",make_realtime_sysinfo())
    sleep(500)
