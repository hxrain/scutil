# -*- coding: utf-8 -*-
"""
     CDP(Chrome DevTools Protocol) 功能基类
"""

from typing import List


class BaseT:
    """基础类"""

    def __init__(self):
        pass

    # def __str__(self):
    #     return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)


class TypingT(BaseT):
    """数据类"""


class EventT(BaseT):
    """事件类"""


class ReturnT(BaseT):
    """返回值类"""


class DomainT(BaseT):
    """功能域类"""


class ErrorT(BaseT):
    """CDP错误消息类"""

    def __init__(self):
        self.code: int = int
        self.message: str = str

    def info(self, msg=None):
        if not msg:
            msg = ErrorT
        return f'ErrorT/{self.code}/{self.message}'


class VersionT(BaseT):
    """浏览器版本信息"""
    underline = '-'  # 下划线需要转义为横线

    def __init__(self):
        self.Protocol_Version: str = str
        self.Browser: str = str
        self.WebKit_Version: str = str
        self.User_Agent: str = str
        self.V8_Version: str = str
        self.webSocketDebuggerUrl: str = str  # Browser endpoint URL
