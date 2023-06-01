# -*- coding: utf-8 -*-
"""
    CDP(Chrome DevTools Protocol)驱动模块
    进行底层WebSocket和协议Json数据的交互处理(发送报文/接收报文/响应事件),是操控单一tab的基础.
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

# 是否开启调试日志输出,显示收发内容
debug_out = os.getenv("SPD_CHROME_DEBUG", False)
if debug_out:
    logger = logging.getLogger(__name__)
    _filehandler = logging.handlers.RotatingFileHandler('./cdp_dbg_log.txt', encoding='utf-8', maxBytes=1024 * 1024 * 32, backupCount=8)
    _filehandler.setLevel(logging.DEBUG)
    _filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
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


class driver_t:
    """CDP驱动交互功能类"""

    def __init__(self):
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

        # 内部通信使用的上下文
        self.__event_handlers = {}
        self.__websocket = None
        self.__ws_url = None
        self.__session_seq = 0  # 会话交互的递增序号
        self.__session_http = None  # 访问http的客户端会话对象
        self.__session_ids = {}  # 'flat'模式使用的sessionId标识与targetId对照表
        self.__session_sid = None  # 'flat'模式使用的当前会话sessionId

        self.timeout = 10  # 默认交互超时上限
        self.idle_cb = None  # loop接收,空闲回调函数

    @trying
    def ver(self, url='http://127.0.0.1:9222/') -> VersionT:
        """查询浏览器版本信息,获得访问端点.
            url - 浏览器调试地址,page端点/http端点/browser端点均可.
            返回值:VersionT或error_t
        """
        hostport = up.urlparse(url)[1]
        url = f'http://{hostport}/json/version'
        rsp = self.__http_take(url)
        if is_error(rsp):
            return rsp
        return jsonable.decode(VersionT, rsp.content.decode('utf-8'))

    def endpoint(self, uuid, port=None, host=None, type='page'):
        """使用指定的地址参数,构造访问端点url"""
        if port is not None or host is not None:  # 给定了任一地址参数
            port = port or 9222
            host = host or '127.0.0.1'
            return f'ws://{host}:{port}/devtools/{type}/{uuid}'
        elif not self.__ws_url:  # 没给定地址参数,且不存在已知会话地址,完全使用默认值
            port = 9222
            host = '127.0.0.1'
            return f'ws://{host}:{port}/devtools/{type}/{uuid}'
        else:  # 没给定地址参数,但存在已知会话地址,提取后进行构造
            hostport = up.urlparse(self.__ws_url)[1]
            return f'ws://{hostport}/devtools/{type}/{uuid}'

    def conn(self, ws_url=None, toBrwser=False, timeout=None):
        """连接ws_url指定的chrome/chromium端点
            ws_url - 目标端点 ws:// 或 http:// 或 uuid
            brwend - 是否强制连接为Browser端点
            timeout - 可指定连接超时上限
            返回值:None成功,errot_t错误.
        """
        ws_url = ws_url or self.__ws_url
        if not ws_url:  # 默认就连接本地9222浏览器主体
            ws_url = 'http://127.0.0.1:9222/'
            toBrwser = True

        if ws_url.find('://') == -1:
            ws_url = self.endpoint(ws_url)

        if toBrwser:
            # 强制连接Browser端点,则获取端点地址
            v = self.ver(ws_url)
            if is_error(v):
                return v
            ws_url = v.webSocketDebuggerUrl

        self.close()
        self.__ws_url = ws_url

        timeout = timeout or self.timeout
        opt = [(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 64)]
        try:
            self.__websocket = websocket.create_connection(ws_url, timeout, enable_multithread=False, sockopt=opt, skip_utf8_validation=True)
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

    def listen(self, Event: EventT, callback, add=True):
        """绑定/解除指定的Event事件类监听器callback.
            Event - 事件类class
            callback - 事件触发的回调函数,原型为
                def cb_event(drv:driver_t, evt:EventT, sid,tid):
                    pass
            add - 告知是删除还是增加
            返回值:error_t错误,其他为回调索引号
        """
        if not issubclass(Event, EventT):
            return error_t("event class should extend by EventT.", -13)

        if not callable(callback):
            return error_t("event callback should be callable", -14)

        key = Event.event
        if not add:  # 移除事件回调
            if key not in self.__event_handlers:
                return error_t(f'Event <{key}> not exists.', -11)
            handlers = self.__event_handlers[key][1]
            idx = handlers.find(callback)
            if idx == -1:
                return error_t(f'Event <{key}> Callback not exists.', -12)
            handlers.pop(idx)
            return idx
        else:  # 绑定事件回调
            if key not in self.__event_handlers:
                self.__event_handlers[key] = (EventT, [])  # {'功能域.事件名称':(事件class类型,[回调函数列表])}
            handlers = self.__event_handlers[key][1]
            idx = handlers.find(callback)
            if idx == -1:
                idx = len(handlers)
                handlers.append(callback)
            return idx

    @trying
    def call(self, ReturnType, Command, **args):
        """核心方法,发起CDP协议请求,接收得到回应结果.
            返回值:error_t错误; 其他为回应结果,ReturnType/ErrorT/None
                error_t.tag = 0 超时
        """
        if not self.__websocket:
            return error_t('not websocket connection.', -4)

        # 会话序号递增
        self.__session_seq += 1
        # 尝试摘取额外参数
        timeout = args.pop("_timeout", self.timeout)
        idle_cb = args.pop("_idle_cb", self.idle_cb)

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
        # 发送请求
        snd = self.__ws_send(req_json)
        if is_error(snd):
            return snd

        # 等待明确指定的回应
        rsp = self.wait(timeout, self.__session_seq, idle_cb)
        if rsp is None:
            return error_t(f'call({Command}) is timeout.', 0)
        elif is_error(rsp):
            return rsp  # 客户端错误

        # 解析回应结果
        if 'error' in rsp:
            return jsonable.decode(ErrorT, rsp['error'])  # Chrome内部错误

        if ReturnType is None:
            return None
        return jsonable.decode(ReturnType, rsp['result'])  # 正常交互结果

    @trying
    def wait(self, timeout=None, seq=None, idle_cb=None):
        """在当前的ws连接上,等待CDP事件或之前交互序列seq对应的结果.
            timeout - 时间等待上限
            seq - 等待的交互序列号,None不进行强制等待.
            返回值:None超时未等到seq结果; error_t错误; 其他为seq回应报文dict
        """
        if not self.__websocket:
            return error_t('not websocket connection.', -4)

        if timeout is None:
            timeout = self.timeout
        if idle_cb is None:
            idle_cb = self.idle_cb

        waited = waited_t(timeout)  # 使用逻辑计时器,进行更灵活的接收逻辑处理
        ret = None
        while not waited.timeouted():  # 小步快跑,尝试进行多次短时接收等待,给出处理空闲回调的机会.
            rcv = self.__ws_recv(0.01)  # 进行很短时间的接收等待,避免阻塞在接收动作上,且释放cpu.
            if is_error(rcv):
                return rcv  # 接收错误,直接返回
            elif rcv is None:
                if not seq:
                    return ret  # 非强制等待,且接收超时,则直接返回避免浪费等待时间
                else:
                    if idle_cb:
                        idle_cb(self, timeout, waited.remain())  # 尝试处理外部空闲事件
                    continue  # 强制等待结果,继续尝试

            if "method" in rcv:
                # 接收到事件报文
                try:
                    self.__evt_proc(rcv['method'], rcv.get('params', []), rcv.get('sessionId'))
                except Exception as e:
                    return error_e(e, -5)
            elif "id" in rcv:
                # 接收到结果报文
                if rcv.get('id') == seq:
                    ret = rcv
                    seq = None  # 不要立即返回,尝试继续循环处理一些后续可能出现的事件消息
            else:
                return error_t(f"unknown CDP message: {rcv}", -6)
        return ret  # 返回None或对应seq的结果

    def __http_take(self, url):
        """进行http请求,返回值:error_t错误,其他为回应对象"""
        try:
            if self.__session_http is None:
                self.__session_http = requests.Session()
            return self.__session_http.get(url)
        except Exception as e:
            return error_e(e, -10)

    def __evt_proc(self, event, message_json, sid):
        """内部使用,处理接收到的事件.返回值:None非绑定关注的事件;EventT对象为关注的事件"""
        if event not in self.__event_handlers:
            return None  # 未绑定的事件不处理

        cls, handlers = self.__event_handlers[event]  # 得到绑定的事件处理器
        obj = jsonable.decode(cls, message_json)  # 反序列化事件类别对象
        if sid in self.__session_ids:
            tid = self.__session_ids[sid]
        else:
            sid = None
            tid = None

        for handle in handlers:
            handle(self, obj, sid, tid)  # 循环调用事件处理器
        return obj

    def __ws_send(self, message_json, retry=2):
        """在当前的websocket上发送CDP报文.返回值:None成功;error_t错误."""
        err = None
        for i in range(retry):
            try:
                self.__websocket.settimeout(self.timeout)
                self.__websocket.send(message_json)  # 发送请求
                log("SEND > %s" % message_json)
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
            log(f"RECV < {message_json}")
            return json.loads(message_json)
        except websocket.WebSocketTimeoutException:
            return None  # 超时
        except websocket.WebSocketException as e:
            return error_e(e, -8)  # websocket错误
        except Exception as e:
            return error_e(e, -9)  # 其他错误
