# -*- coding: utf-8 -*-
"""
    CDP(Chrome DevTools Protocol)驱动模块,整合cdp协议交互与具体可用的功能域.
    功能域分类:
        Browser     浏览器整体行为,下载路径/权限
        DOM         页面dom模型操纵
        DOMDebugger 页面dom/event断点操纵
        Emulation   设备与环境模拟
        IO          对象数据流读取
        Input       键盘/鼠标/触摸等输入功能
        Log         接收控制台日志
        Network     页面网络交互与操纵
        Page        页面内容交互与操纵
        Performance 浏览器性能事件报告
        Security    浏览器/HTTPS安全性与认证功能
        Target      Tab功能操纵
        Debugger    JavaScript调试器交互
        Profiler    浏览器性能分析器操纵
        Runtime     JavaScript引擎交互
"""

# 全部已知功能域模块
from cdp import Browser
from cdp import DOM
from cdp import DOMDebugger
from cdp import Emulation
from cdp import IO
from cdp import Input
from cdp import Log
from cdp import Network
from cdp import Page
from cdp import Performance
from cdp import Security
from cdp import Target
from cdp import Debugger
from cdp import Profiler
from cdp import Runtime

DOMAINS = [Browser, DOM, DOMDebugger, Emulation, IO, Input, Log, Network, Page, Performance, Security, Target, Debugger, Profiler, Runtime]

from cdp.cdp_session import *


def list_events(domains):
    """列出所有event类映射,返回值:{'事件名字':事件类}"""
    rst = {}
    for dm in domains:
        for dmk in dir(dm):
            if dmk.startswith('_'):
                continue
            T = getattr(dm, dmk)
            if type(T) is not type or T is EventT:
                continue
            if issubclass(T, EventT):
                rst[T.event] = T
    return rst


# 全部已知的事件名称与类别登记表
EVENTS = list_events(DOMAINS)


class driver_t(session_t):
    """CDP完整功能域驱动类,基础功能继承自session_t会话类."""

    def __init__(self):
        super().__init__()
        # 稳定可用的功能域API对象
        self.Browser = Browser.Browser(self)
        self.DOM = DOM.DOM(self)
        self.DOMDebugger = DOMDebugger.DOMDebugger(self)
        self.Emulation = Emulation.Emulation(self)
        self.IO = IO.IO(self)
        self.Input = Input.Input(self)
        self.Log = Log.Log(self)
        self.Network = Network.Network(self)
        self.Page = Page.Page(self)
        self.Performance = Performance.Performance(self)
        self.Security = Security.Security(self)
        self.Target = Target.Target(self)
        self.Debugger = Debugger.Debugger(self)
        self.Profiler = Profiler.Profiler(self)
        self.Runtime = Runtime.Runtime(self)

    @trying
    def attach(self, targetId=None) -> Target.SessionID:
        """在flat模式下,单一ws操纵多个tab之前,需要先附着到目标target.
            targetId - is not None,为目标tab的标识
                     - None则为附着到Browser,等同于连接到Browser端点.
            返回值:error_t错误; 其他为当前附着的sessionId
        """
        tkey = f'tid_{targetId}'
        if tkey in self.__session_ids:  # 如果targetId缓存有效,则直接使用
            self.__session_sid = self.__session_ids[tkey]
            return self.__session_sid

        if targetId:  # 附着到指定tab或browser主体
            sr = self.Target.attachToTarget(targetId, True)
        else:
            sr = self.Target.attachToBrowserTarget()

        if is_error(sr):
            return sr

        self.__session_sid = sr.sessionId
        self.__session_ids[sr.sessionId] = targetId
        self.__session_ids[tkey] = sr.sessionId
        return sr.sessionId

    @trying
    def detach(self, sessionId):
        """释放附着的会话资源,不再操作对应的tab
           返回值:error_t或ErrorT,有错误;None完成.
        """
        if sessionId not in self.__session_ids:
            return None
        targetId = self.__session_ids[sessionId]  # 得到会话id对应的tab标识
        del self.__session_ids[sessionId]  # 清理缓存的会话id
        tkey = f'tid_{targetId}'
        del self.__session_ids[tkey]  # 清理缓存的tab标识
        if self.__session_sid == sessionId:
            self.__session_sid = None  # 清理缓存的当前会话id

        return self.Target.detachFromTarget(sessionId)  # 进行真正的交互动作,解除会话id对应的tab附着关系.
