# -*- coding: utf-8 -*-
"""
    CDP(Chrome DevTools Protocol)驱动模块
    进行底层WebSocket和协议Json数据的交互处理(发送报文/接收报文/响应事件),是操控单一tab的基础.
"""

try:
    import websocket._core as websocket
except:
    import websocket

import base64
from cdp.cdp_jsonable import jsonable

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


class driver_t:
    """CDP驱动交互功能类"""

    def __init__(self):
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

    def call(self, ReturnType, Command, **args):
        pass
