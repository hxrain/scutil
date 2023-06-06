# -*- coding: utf-8 -*-
"""
    CDP(Chrome DevTools Protocol)协议会话模块
    进行底层WebSocket和协议Json数据的交互处理(发送报文/接收报文/响应事件),是操控Chrome/Chromium的基础.
"""

try:
    import websocket._core as websocket
except:
    import websocket

import socket
import base64
import traceback
import json
import os
import time
import requests
import urllib.parse as up

from cdp.cdp_jsonable import jsonable
from cdp.cdp_comm import *

# 记录所有的事件类映射表
EVENTS = {}

# 是否开启调试日志输出,显示收发内容
debug_out = os.getenv("CDP_DEBUG_LOGGING", False)
if debug_out:
    import logging
    import logging.handlers

    _filehandler = logging.handlers.RotatingFileHandler('./cdp_dbg_log.txt', encoding='utf-8', maxBytes=1024 * 1024 * 32, backupCount=8)
    _filehandler.setLevel(logging.DEBUG)
    _filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    logger = logging.getLogger(__name__)
    logger.addHandler(_filehandler)
    logger.setLevel(logging.DEBUG)


# 记录调试日志的内部方法
def log(msg):
    if not debug_out:
        return
    logger.debug(msg)


class error_t(Exception):
    """记录交互错误的对象"""

    def __init__(self, message, tag=None, source=None, stack=None):
        self.message = message  # 错误消息
        self.tag = tag  # 错误相关标识
        self.source = source  # 发生错误的调用来源
        self.stack = stack  # 发生错误的完整调用栈

    def __str__(self):
        return self.message if self.tag is None else f'{self.tag}/{self.message}'

    def info(self, msg=None):
        if msg:
            msg = f'{msg}/{self.message}'
        else:
            msg = self.message
        rst = [f'MSG = {msg}']
        if self.tag is not None:
            rst.append(f'TAG = {self.tag}')
        if self.source:
            rst.append(f'SRC = {self.source}')
        if self.stack:
            rst.append('DEP:')
            rst.append(''.join(self.stack))
        return '\n'.join(rst)


def error_e(e: Exception, tag, source=None, pop_tb0=False):
    """使用给定的异常对象e,构造对应的错误对象.返回值:error_t对象"""
    # 发生错误时的上层调用来源
    stacks = traceback.extract_stack(e.__traceback__.tb_frame)
    stack = stacks[-2]
    fname = stack.filename.replace("\\", "/")

    # 发生错误时的调用栈
    backs = traceback.format_tb(e.__traceback__)
    if pop_tb0:
        backs.pop(0)
    backs.append(f'  File "{fname}", line {stack.lineno}, in {stack.name}\n    {stack.line}')

    # 返回错误信息对象
    return error_t(str(e), tag, source, backs)


def is_error(obj):
    """判断给定的对象是否为错误"""
    return isinstance(obj, (error_t, ErrorT))


def trying(func):
    """统一的异常捕捉装饰器"""

    def inner(*args, **kwargs):
        try:
            # 正常情况返回原始函数结果
            return func(*args, **kwargs)
        except Exception as e:
            return error_e(e, getattr(e, 'tag', None), getattr(e, 'source', None), True)

    return inner


@trying
def tryout(func, *args, **argv):
    """对func进行try包装,返回值:错误时为error_t对象,其他为func的返回值."""
    return func(*args, **argv)


class waited_t:
    """简单的超时等待计时器"""

    def __init__(self, timeout):
        """从构造的时候就开始计时,告知等待超时秒数"""
        self._timeout = timeout
        self.reset()

    def reset(self):
        """复位结束时间点,准备重新计时"""
        self.end = time.time() + self._timeout

    def timeouted(self):
        """用当前时间判断,是否超时了"""
        return time.time() >= self.end

    def remain(self):
        """获知剩余等待秒数"""
        r = self.end - time.time()
        return 0 if r <= 0 else r


class session_t:
    """CDP交互会话功能类"""

    def __init__(self):
        # 内部通信使用的上下文
        self.__event_handlers = {}  # 事件绑定表 {'功能域.事件名称':[(回调函数,用户数据)]}
        self.__websocket: websocket.WebSocket = None
        self.__ws_url = None
        self.__session_seq = 0  # 会话交互的递增序号
        self.__session_http = None  # 访问http的客户端会话对象
        self.__session_ids = {}  # 'flat'模式使用的sessionId标识与targetId对照表
        self.__session_sid = None  # 'flat'模式使用的当前会话sessionId

        self.timeout = 60  # 默认交互超时上限
        self.cb_idle = None  # wait接收过程,空闲回调函数
        self.cb_events = None  # 全部事件的过滤回调,原型为 def cb_event(drv:driver_t, evt:EventT, sid, tid)

    @trying
    def ver(self, url='http://127.0.0.1:9222/') -> VersionT:
        """查询浏览器版本信息,获得访问端点.
            url - 浏览器调试地址,page端点/http端点/browser端点均可.
            返回值:VersionT或error_t
        """
        hostport = up.urlparse(url)[1]
        url = f'http://{hostport}/json/version'
        rsp = self.http_take(url)
        if is_error(rsp):
            return rsp
        return jsonable.decode(VersionT, rsp.content.decode('utf-8'))

    def endpoint(self, uuid, port=None, host=None, type='page'):
        """使用指定的地址参数,构造访问端点url"""
        if port is not None or host is not None:  # 给定了任一地址参数
            port = port or 9222
            host = host or '127.0.0.1'
            return f'ws://{host}:{port}/devtools/{type}/{uuid}'
        elif not self.__ws_url:  # 没给定地址参数,且不存在已知地址,使用默认地址
            port = 9222
            host = '127.0.0.1'
            return f'ws://{host}:{port}/devtools/{type}/{uuid}'
        else:  # 没给定地址参数,但存在已知会话地址,提取后进行构造
            hostport = up.urlparse(self.__ws_url)[1]
            return f'ws://{hostport}/devtools/{type}/{uuid}'

    def conn(self, dst=None, toBrwser=False, timeout=None):
        """连接ws_url指定的chrome/chromium端点
            dst - 目标端点 ws:// 或 http:// 或 targetId
            brwend - 是否强制连接为Browser端点
            timeout - 可指定连接超时上限
            返回值:None成功,errot_t错误.
        """
        self.close()

        timeout = timeout or self.timeout
        ws_url = dst or self.__ws_url
        if not ws_url:  # 没有已知地址,则连接本地9222浏览器主体
            ws_url = 'http://127.0.0.1:9222/'
            toBrwser = True

        if ws_url.find('://') == -1:  # 传入的是targetId
            ws_url = self.endpoint(ws_url)

        if toBrwser:
            # 强制连接Browser端点,则获取端点地址
            v = self.ver(ws_url)
            if is_error(v):
                return v
            ws_url = v.webSocketDebuggerUrl
            self.__session_ids[0] = None
        else:
            self.__session_ids[0] = ws_url.split('/')[-1]  # 使用ws连接地址中的端点id作为默认tid

        self.__ws_url = ws_url

        opt = [(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 256)]
        try:
            self.__websocket: websocket.WebSocket = websocket.create_connection(ws_url, timeout, enable_multithread=False, sockopt=opt, skip_utf8_validation=True)
        except websocket.WebSocketBadStatusException as e:
            return error_t(f'tab ws open fail: {ws_url} {str(e)}', -2)  # 连接失败
        except Exception as e:
            return error_t(f'tab ws open fail: {ws_url}. {str(e)}', -3)  # 连接失败

    def close(self):
        """关闭websocket"""
        if self.__websocket:
            self.__websocket.close()
            self.__websocket = None

        if self.__session_http:
            self.__session_http.close()
            self.__session_http = None

        self.__session_seq = 0
        self.__session_ids = {}
        self.__session_sid = None

    def listen(self, evtcls: EventT, callback, usrdat=None, add=True):
        """绑定/解除指定的evtcls事件类监听器callback.
            evtcls - 事件类class
            callback - 事件触发的回调函数,原型为
                def cb_event(drv:driver_t, evt:EventT, sid, tid, usrdat):
                    '''事件回调函数返回True,则结束当前轮wait函数的持续等待.'''
                    pass
            usrdat - callback外部绑定的用户关联数据
            add - 告知是删除还是增加
            返回值:error_t错误,其他为回调索引号
        """
        if not issubclass(evtcls, EventT):
            return error_t("event class should extend by EventT.", -13)

        if not callable(callback):
            return error_t("event callback should be callable", -14)

        def find(cb, handlers):
            """在事件绑定元组列表中查找指定的回调序号"""
            for i, hd in enumerate(handlers):
                if cb == hd[0]:
                    return i
            return -1

        evtname = evtcls.event
        if not add:  # 移除事件回调
            if evtname not in self.__event_handlers:
                return error_t(f'Event <{evtname}> not exists.', -11)

            if callback is None:
                # 删除当前事件的全部回调绑定
                rc = len(self.__event_handlers[evtname])
                del self.__event_handlers[evtname]
                return rc
            else:
                # 删除当前事件的指定回调绑定
                handlers = self.__event_handlers[evtname]
                idx = find(callback, handlers)
                if idx == -1:
                    return error_t(f'Event <{evtname}> Callback not exists.', -12)
                else:
                    handlers.pop(idx)
                    return idx
        else:  # 绑定事件回调
            if evtname not in self.__event_handlers:
                self.__event_handlers[evtname] = []
            handlers = self.__event_handlers[evtname]
            idx = find(callback, handlers)
            if idx == -1:
                idx = len(handlers)
                handlers.append((callback, usrdat))
            return idx

    @trying
    def call(self, ReturnType, Command, **args):
        """核心方法,发起CDP协议请求,接收得到回应结果.
            返回值: 正常时为回应结果,ReturnType/ErrorT/rsp['result']
                交互错误时为error_t,且 error_t.tag = 0 为接收超时
        """
        if not self.__websocket:
            return error_t('not websocket connection.', -4)

        # 会话序号递增
        self.__session_seq += 1

        # 尝试摘取额外参数
        timeout = args.pop("_timeout", self.timeout)
        cb_idle = args.pop("_cb_idle", self.cb_idle)

        # 剔除值为None的可选参数
        keys = list(args.keys())
        for key in keys:
            if args.get(key, None) is None:
                args.pop(key)

        # 构造请求报文
        req = {"id": self.__session_seq, "method": Command, "params": args}
        if self.__session_sid:
            req['sessionId'] = self.__session_sid  # 如果绑定了tab会话id,则需要在请求报文中附带
        req_json = json.dumps(req)

        # 发送请求报文
        snd = self.__ws_send(req_json)
        if is_error(snd):
            return snd

        # 等待回应报文
        rsp = self.wait(timeout, self.__session_seq, cb_idle)  # 明确指定的seq序号
        if rsp is None:  # 等待超时
            return error_t(f'call({Command}) is timeout.', 0)
        elif is_error(rsp):
            return rsp  # 通信错误

        # call调用的时候,wait方法不应返回事件对象
        assert not isinstance(rsp, EventT)

        if 'error' in rsp:  # Chrome交互错误
            return jsonable.decode(ErrorT, rsp['error'])

        if ReturnType is None:  # 未指定返回值类别,则告知回应报文的结果部分
            return rsp['result']

        # 正常交互完成,返回明确指定的返回值类对象
        return jsonable.decode(ReturnType, rsp['result'])

    @trying
    def wait(self, timeout=None, seq=None, cb_idle=None):
        """在当前的ws连接上,等待CDP事件或之前交互序列seq对应的结果.
            timeout: 时间等待上限
            seq: None - 不进行强制等待,单次接收超时即返回.
                  <0 - 等待特定的EventT(对应的事件回调函数返回True)
                  =0 - 循环接收等待完整的timeout结束
                  >0 - 等待指定交互序号的回应结果
            cb_idle: 空闲时的回调函数
            返回值:None超时未等到seq结果; error_t错误; 其他为seq回应报文dict,或指定等待的事件EventT对象实例
        """
        if not self.__websocket:
            return error_t('not websocket connection.', -4)

        timeout = timeout or self.timeout
        cb_idle = cb_idle or self.cb_idle

        ret = None
        waited = waited_t(timeout)  # 使用逻辑计时器,进行更灵活的接收逻辑处理
        while not waited.timeouted():  # 小步快跑,尝试进行多次短时接收等待,给出处理空闲回调的机会.
            rcv = self.__ws_recv(0.01)  # 进行很短时间的接收等待,避免阻塞在接收动作上,且释放cpu.
            if is_error(rcv):
                return rcv  # 接收错误,直接返回
            if rcv is None:
                if seq is None:
                    return ret  # 非强制等待,且接收超时,则直接返回避免浪费等待时间
                else:
                    if cb_idle:
                        cb_idle(self, timeout, waited.remain())  # 尝试处理外部空闲事件
                    continue  # 强制等待结果,继续尝试

            if "method" in rcv:
                # 接收到事件报文
                try:
                    evt = self.__evt_proc(rcv['method'], rcv.get('params', []), rcv.get('sessionId'))
                    if evt is not None and (isinstance(seq, int) and seq < 0):
                        return evt  # 定向等待的事件发生了,立即返回
                except Exception as e:
                    return error_e(e, -5)
            elif "id" in rcv:
                # 接收到回应报文
                if rcv.get('id') == seq:  # 需要等待回应报文的时候,就是在CALL方法中
                    ret = rcv
                    seq = None  # 不要立即返回,尝试继续循环处理一些后续可能出现的事件消息
            else:
                return error_t(f"unknown CDP message: {rcv}", -6)
        return ret  # 返回None或对应seq的结果

    def http_take(self, url):
        """进行http请求,返回值:error_t错误,其他为回应对象"""
        try:
            if self.__session_http is None:
                self.__session_http = requests.Session()
            return self.__session_http.get(url)
        except Exception as e:
            return error_e(e, -10)

    def __evt_proc(self, evtname, dat, sid):
        """内部使用,处理接收到的事件.返回值:非None为事件对象,结束当前轮wait的循环等待"""
        handlers = self.__event_handlers.get(evtname, None)  # 得到绑定的事件处理器
        evtcls = EVENTS.get(evtname)  # 查看已知事件映射表得到事件类
        if evtcls is None:
            return None  # 未知事件,不处理
        if self.cb_events is None and not handlers:
            return None  # 无回调函数,不处理

        obj = jsonable.decode(evtcls, dat)  # 反序列化事件类别对象
        tid = self.__session_ids.get(sid, self.__session_ids[0])  # 尝试获取会话id绑定的tab标识

        if self.cb_events:
            self.cb_events(self, obj, sid, tid)  # 全部事件处理回调

        if handlers:
            ret = None
            for cb, usrdat in handlers:
                ret = ret or cb(self, obj, sid, tid, usrdat)  # 循环调用事件处理回调函数
            return obj if ret else None
        return None

    def __ws_send(self, message_json, retry=2):
        """在当前的websocket上发送CDP报文.返回值:None成功;error_t错误."""
        err = None
        for i in range(retry):
            try:
                self.__websocket.settimeout(self.timeout)
                self.__websocket.send(message_json)  # 发送请求
                log("WS_SEND > %s" % message_json)
                return None  # 成功返回
            except Exception as e:
                err = error_e(e, -7)  # 记录最后出现的错误
                self.open()
        return err  # 返回最后的错误

    def __ws_recv(self, timeout=0.01):
        """在当前的websocket上进行一次接收.返回值:None超时;error_t错误;其他为CDP回应报文dict"""
        try:
            self.__websocket.settimeout(timeout)
            message_json = self.__websocket.recv()
            log(f"WS_RECV < {message_json}")
            return json.loads(message_json)
        except websocket.WebSocketTimeoutException:
            return None  # 超时
        except websocket.WebSocketException as e:
            return error_e(e, -8)  # websocket错误
        except Exception as e:
            return error_e(e, -9)  # 其他错误
