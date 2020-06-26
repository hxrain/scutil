#! /usr/bin/env python
# -*- coding: utf-8 -*-

# 代码来自 https://github.com/fate0/pychrome 进行了调整.

import functools
import json
import logging
import os
import queue
import threading
import warnings

import websocket


class PyChromeException(Exception):
    pass


class TabConnectionException(PyChromeException):
    pass


class CallMethodException(PyChromeException):
    pass


class RuntimeException(PyChromeException):
    pass


logger = logging.getLogger(__name__)


# 协议方法伪装
class GenericAttr(object):
    def __init__(self, name, tab):
        """记录方法所属的功能域名字与关联的tab对象"""
        self.__dict__['name'] = name
        self.__dict__['tab'] = tab

    def __getattr__(self, item):
        method_name = "%s.%s" % (self.name, item)
        event_listener = self.tab.get_listener(method_name)

        if event_listener:
            return event_listener

        return functools.partial(self.tab.call_method, method_name)

    def __setattr__(self, key, value):
        self.tab.set_listener("%s.%s" % (self.name, key), value)


# chrome浏览器Tab页操控功能
class Tab(object):
    status_initial = 'initial'
    status_started = 'started'
    status_stopped = 'stopped'

    def __init__(self, **kwargs):
        """根据chrome的tab对象信息创建tab操纵类,需要browser对象配合获取"""
        self.id = kwargs.get("id")  # tab的唯一id
        self.type = kwargs.get("type")
        self.debug = os.getenv("DEBUG", False)

        self._websocket_url = kwargs.get("webSocketDebuggerUrl")  # 操纵tab的websocket地址
        self._kwargs = kwargs

        self._cur_id = 1000  # 交互消息的初始流水序号

        self._ws = None  # websocket功能对象

        self._started = False  # 记录tab操纵对象是否启动了
        self.status = self.status_initial

        self.event_handlers = {}  # 记录tab事件处理器
        self.method_results = {}  # 记录请求对应的回应结果

    def _call(self, message, timeout=5):
        """发送tab操纵请求对象.
           返回值:None超时;其他为结果对象"""
        if 'id' not in message:
            self._cur_id += 1
            message['id'] = self._cur_id
        msg_id = message['id']  # 得到本次请求的消息id
        assert (msg_id not in self.method_results)
        msg_json = json.dumps(message)  # 生成本次请求的消息json串
        self.method_results[msg_id] = None

        if self.debug:  # pragma: no cover
            print("SEND > %s" % msg_json)

        try:
            # just raise the exception to user
            self._ws.send(msg_json)  # 发送请求
            rst = self._recv_loop(True, timeout)  # 循环接收,要求必须尝试等待结果
            if rst[0]:
                return self.method_results[msg_id]
            else:
                return None

        finally:
            del self.method_results[msg_id]

    def _recv(self, timeout=0.01):
        """尝试进行一次接收处理.
           返回值:(None,None)通信错误;(0,0)超时;其他为(结果数,事件数)"""
        try:
            self._ws.settimeout(timeout)
            message_json = self._ws.recv()
            message = json.loads(message_json)  # 接收到json消息后就转换为对象
        except websocket.WebSocketTimeoutException:
            return (0, 0)  # 超时了,什么都没有收到
        except (websocket.WebSocketException, OSError):
            if self._started:
                logger.error("websocket exception", exc_info=True)
                self._started = False
            return (None, None)  # websocket错误了

        if self.debug:  # pragma: no cover
            print('< RECV %s' % message_json)

        if "method" in message:
            # 接收到事件了,尝试进行处理
            method = message['method']
            if method in self.event_handlers:
                try:
                    self.event_handlers[method](**message['params'])
                except Exception as e:
                    logger.error("callback %s exception" % method, exc_info=True)
            return (0, 1)
        elif "id" in message:
            # 接收到结果了,记录下来
            msg_id = message["id"]
            if msg_id in self.method_results:
                self.method_results[msg_id] = message
            return (1, 0)
        else:  # pragma: no cover
            warnings.warn("unknown message: %s" % message)
            return (0, 0)

    def _recv_loop(self, wait_result=False, timeout=1):
        """在指定的时间范围内进行接收处理.可告知是否必须等到结果或超时才结束;
           返回值:(None,None)通信错误;(0,0)超时;其他为(结果数,事件数)"""
        one_timeout = 0.01
        loop = int(timeout // one_timeout)
        for i in range(loop):
            if not self._started:
                break  # 如果要求停止,则结束循环
            rst = self._recv(one_timeout)  # 尝试进行一次接收处理
            if wait_result:
                if rst[0]:  # 如果要求必须等待回应结果,则强制判断结果数
                    return rst
            else:
                if rst[0] or rst[1]:  # 否则判断结果数或事件数
                    return rst
            if rst[0] is None:
                return rst
        return (0, 0)

    def __getattr__(self, item):
        """拦截未定义操作,转换为对应的协议方法伪装"""
        attr = GenericAttr(item, self)
        setattr(self, item, attr)
        return attr

    def call_method(self, _method, *args, **kwargs):
        """调用协议方法,核心功能.具体请求交互细节可参考协议描述. https://chromedevtools.github.io/devtools-protocol/
           返回值:None超时;其他为回应结果"""
        if not self._started:
            raise RuntimeException("Cannot call method before it is started")

        if args:  # 不允许使用普通参数传递,必须为key/value型参数
            raise CallMethodException("the params should be key=value format")

        timeout = kwargs.pop("_timeout", None)  # 额外摘取超时控制参数

        result = self._call({"method": _method, "params": kwargs}, timeout=timeout)  # 发起调用请求
        if result is None:
            return None

        if 'result' not in result and 'error' in result:
            warnings.warn("%s error: %s" % (_method, result['error']['message']))
            raise CallMethodException("calling method: %s error: %s" % (_method, result['error']['message']))

        return result['result']

    def set_listener(self, event, callback):
        """绑定事件监听器/解除指定的监听器"""
        if not callback:
            return self.event_handlers.pop(event, None)

        if not callable(callback):
            raise RuntimeException("callback should be callable")

        self.event_handlers[event] = callback
        return True

    def get_listener(self, event):
        """获取指定的事件监听器"""
        return self.event_handlers.get(event, None)

    def clear_listeners(self):
        """清理全部事件监听器"""
        self.event_handlers = {}
        return True

    def start(self):
        """启动tab交互象,建立websocket连接"""
        if self._started:
            return False

        if not self._websocket_url:
            raise RuntimeException("Already has another client connect to this tab")

        self._started = True
        self.status = self.status_started
        self._ws = websocket.create_connection(self._websocket_url, enable_multithread=True)
        return True

    def stop(self):
        """停止tab交互,关闭websocket连接"""
        if not self._started:
            return False

        self.status = self.status_stopped
        self._started = False
        if self._ws:
            self._ws.close()
        return True
