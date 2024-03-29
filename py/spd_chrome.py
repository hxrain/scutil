# -*- coding: utf-8 -*-

import functools
import json
import logging
import os
import time
import requests

try:
    import websocket._core as websocket
except:
    import websocket

import base64
import spd_base
import socket
import traceback
import py_util
import util_curve
import urllib.parse as up


# 代码来自 https://github.com/fate0/pychrome 进行了调整.
# chrome.exe --disk-cache-dir=.\tmp --user-data-dir=.\tmp --cache-path=.\tmp --remote-debugging-port=9222 --disable-web-security --disable-features=IsolateOrigins,site-per-process --disable-gpu --disable-software-rasterize

class PyChromeException(Exception):
    pass


class CallMethodException(PyChromeException):
    pass


class RuntimeException(PyChromeException):
    pass


logger = logging.getLogger(__name__)
debug_out = os.getenv("SPD_CHROME_DEBUG", False)  # 是否显示收发内容


# if debug_out:
#     filehandler = logging.handlers.RotatingFileHandler('./dbg_cdp.txt', encoding='utf-8', maxBytes=1024 * 1024 * 32, backupCount=8)
#     filehandler.setLevel(logging.DEBUG)
#     filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
#     logger.addHandler(filehandler)
#     logger.setLevel(logging.DEBUG)


# 协议方法伪装
class GenericAttr(object):
    def __init__(self, domain, tab):
        """记录方法所属的功能域名称与关联的tab对象"""
        self.__dict__['domain'] = domain
        self.__dict__['tab'] = tab

    def __getattr__(self, item):
        method_name = "%s.%s" % (self.domain, item)
        event_listener = self.tab.get_listener(method_name)

        if event_listener:
            return event_listener

        return functools.partial(self.tab.call_method, method_name)

    def __setattr__(self, item, value):
        self.tab.set_listener("%s.%s" % (self.domain, item), value)


class cycle_t:
    '周期计时器'

    def __init__(self, interval_ms):
        self.last_time = 0
        self.interval = interval_ms / 1000
        self.hit()

    def hit(self):
        '检查周期事件是否发生'
        now = time.time()
        if now - self.last_time > self.interval:
            self.last_time = now
            return True
        return False


# 默认chrome缓存的回应内容比较小,进行内容提取的时候会反馈错误"evicted from inspector cache",需要给出较大的缓存空间
_maxResourceBufferSize = 1024 * 1024 * 256  # 单个资源的缓存尺寸
_maxTotalBufferSize = int(1024 * 1024 * 1024 * 1.8)  # 总共资源的缓存尺寸,需要小于2G


# chrome浏览器Tab页操控功能
class Tab(object):
    def __init__(self, **kwargs):
        """根据chrome的tab对象信息创建tab操纵类,需要browser对象配合获取"""
        self.id = kwargs.get("id")  # tab的唯一id
        self.type = kwargs.get("type")
        self.last_url = kwargs.get("url")
        self.last_title = kwargs.get("title")
        self.last_act = None
        self.last_err = None
        self._websocket_url = kwargs.get("webSocketDebuggerUrl")  # 操纵tab的websocket地址
        self._cur_id = 1000  # 交互消息的初始流水序号
        self.downpath = None  # 控制浏览器的下载路径
        self.timeout = 3  # 默认的交互超时时间
        self._brwId = kwargs.get("brwId")  # 绑定在指定的浏览器上下文id
        self.disable_alert_url_re = None  # 需要关闭alert对话框的页面url配置
        self._srcid = kwargs.get("srcid", '')  # 控制当前tab页的客户端来源标识

        if debug_out:
            logger.info(f'{self._srctag()} => {self._websocket_url}')

        # 根据环境变量的设定进行功能开关的处理
        if os.getenv("SPD_CHROME_REOPEN", False):
            self.cycle = cycle_t(1000 * 60 * 5)  # 是否自动重连websocket
        else:
            self.cycle = None

        self._websocket = None  # websocket功能对象
        self.event_handlers = {}  # 记录tab事件处理器
        self._wait_result = -1  # 用于记录当前等待的结果id与结果dict

        self._data_requestWillBeSent = {}  # 记录请求内容,以url为key,value为[请求内容对象]列表
        self._data_requestIDs = {}  # 记录请求ID对应的请求信息
        self.req_event_filter_re = None  # 过滤请求信息使用的url匹配re规则
        self._last_act(kwargs.get("act", False))

        # 绑定监听器,记录必要的请求与应答信息
        self.set_listener('Network.requestWillBeSent', self._on_requestWillBeSent)
        self.set_listener('Network.responseReceived', self._on_responseReceived)
        self.set_listener('Network.loadingFinished', self._on_loadingFinished)
        self.set_listener('Page.javascriptDialogOpening', self._on_Page_javascriptDialogOpening)
        self.set_listener('Inspector.detached', self._on_Inspector_detached)
        self.set_listener('Inspector.targetCrashed', self._on_Inspector_targetCrashed)

    def _on_Inspector_detached(self, reason):
        """接收调试器通知:调试分离"""
        logger.warning(f"{self._srctag()} callback <Inspector.detached> {reason}")
        self.type = 'BAD'

    def _on_Inspector_targetCrashed(self):
        """接收调试器通知:目标崩溃"""
        logger.warning(f"{self._srctag()} callback <Inspector.targetCrashed>")
        self.type = 'BAD'

    def _srctag(self, pre='tab'):
        """获取当前tab的标识串"""
        return f'{pre}<{self._srcid}|{self.id}|{self.last_url}>'

    def _last_act(self, using):
        """记录该tab是否处于使用中,便于外部跟踪状态"""
        self.last_act = (using, time.time())

    def __getattr__(self, item):
        """拦截未定义操作,转换为对应的协议方法伪装"""
        attr = GenericAttr(item, self)
        setattr(self, item, attr)
        return attr

    def _is_bad(self):
        """判断当前tab对象是否已经崩坏或关闭"""
        return self.type in {'CLOSE', 'BAD'}

    def _recv(self, timeout=0.01):
        """尝试进行一次接收处理.
           返回值:(结果数,事件数,错误消息)
                    (0,0,'')超时;
                    (None,None,err)通信错误
        """
        if not self._websocket:
            return (None, None, 'not websocket connection.')

        try:
            self._websocket.settimeout(timeout)
            message_json = self._websocket.recv()
            message = json.loads(message_json)  # 接收到json消息后就转换为对象
        except websocket.WebSocketTimeoutException:
            return (0, 0, '')  # 超时了,什么都没有收到
        except websocket.WebSocketException as e:
            return (None, None, spd_base.es(e))  # websocket错误
        except Exception as e:
            return (None, None, spd_base.es(e))  # 其他错误

        if debug_out:  # 如果开启了调试输出,则打印接收到的消息
            logger.debug(f'<RECV {self._srctag()}\n{message_json}')

        if "method" in message:
            # 接收到事件报文,尝试进行回调处理
            method = message['method']
            if method in self.event_handlers:
                try:
                    self.event_handlers[method](**message['params'])
                except Exception as e:
                    logger.warning(f"{self._srctag()} callback <{method}> exception {py_util.get_trace_stack()}")
            return (0, 1, '')
        elif "id" in message:
            # 接收到结果报文
            if self._wait_result == message["id"]:
                self._wait_result = message  # 得到了等待的对应结果,则记录下来
                return (1, 0, '')
        else:
            logger.warning(f"{self._srctag()} unknown CDP message\n{message}")
            return (None, None, 'unknown CDP message.')
        return (0, 0, '')

    def recv_try(self, clear_his=False):
        """尝试0等待持续接收可能存在的报文;
           返回值:(结果数,事件数,错误消息)
        """
        _rcnt = 0
        _ecnt = 0
        err = ''
        while True:  # 真正按照总的最大超时时间进行循环
            if self._is_bad():
                break
            rcnt, ecnt, err = self._recv(0.001)  # 尝试进行一次接收处理
            if err:
                break
            if rcnt + ecnt == 0:
                break
            _rcnt += rcnt
            _ecnt += ecnt
        if clear_his:
            self.clear_request_historys()  # 顺手清理事件回调记录的数据
        return _rcnt, _ecnt, err

    def recv_loop(self, wait_result=False, timeout=1, step=0.05):
        """在指定的时间范围内进行接收处理.可告知是否必须等到结果或超时才结束;
           返回值:(结果或事件数,错误消息)
                    (None,错误消息) - 通信错误;
                    (0,'') - 超时;
        """
        wait = spd_base.waited_t(timeout)
        while True:  # 真正按照总的最大超时时间进行循环
            if self._is_bad():
                break
            rcnt, ecnt, err = self._recv(step)  # 尝试进行一次接收处理
            if rcnt is None:
                return (None, err)
            if wait_result:  # 如果要求必须等待回应结果
                if rcnt:  # 判断结果数
                    return (rcnt, '')
            else:
                rcnt += ecnt
                if rcnt:  # 判断结果数或事件数
                    return (rcnt, '')
            if wait.timeout():
                break
        return (0, '')

    def _call(self, message, timeout=5):
        """发送tab操纵请求对象.
           返回值:(结果对象,错误消息)
                (None,'') - 超时;
                (None,错误消息) - 错误;
                (结果对象,'') - 正常返回
        """
        if 'id' not in message:
            self._cur_id += 1
            message['id'] = self._cur_id
        msg_id = message['id']  # 得到本次请求的消息id
        msg_json = json.dumps(message)  # 生成本次请求的消息json串
        self._wait_result = msg_id  # 提前登记待接收结果对应的消息id

        if debug_out:  # pragma: no cover
            logger.debug(f">SEND {self._srctag()}\n{msg_json}")

        reconn = False
        try:
            self._websocket.settimeout(timeout)
            self._websocket.send(msg_json)  # 发送请求
        except Exception as e:
            reconn = True  # 发送失败则标记,准备重试

        try:
            if reconn:  # 需要重试ws连接,并重新发送
                self._close_websock()
                self._open_websock()
                self._websocket.send(msg_json)  # 重新发送请求

            cnt, err = self.recv_loop(True, timeout)  # 循环接收,要求必须尝试等待结果
            if err:
                return None, err  # 出错了
            if cnt:
                return self._wait_result, ''  # 正常返回
            else:
                return None, ''  # 等待超时,需要继续尝试接收
        except Exception as e:
            return None, spd_base.es(e)

    def _on_Page_javascriptDialogOpening(self, url, message, type, hasBrowserHandler, *args, **kwargs):
        """拦截页面对话框"""

        def _handle_js_dialog(enable=False, proto_timeout=10):
            """在对话框事件回调中进行调用,禁用或启用页面上的js对话框"""
            try:
                rst = self.call_method('Page.handleJavaScriptDialog', accept=enable, _timeout=proto_timeout)
                return True, ''
            except Exception as e:
                return False, spd_base.es(e)

        if type == 'alert' and self.disable_alert_url_re and spd_base.query_re_str(url, self.disable_alert_url_re):
            _handle_js_dialog(False)

    def call_method(self, _method, *args, **kwargs):
        """调用协议方法,核心功能.具体请求交互细节可参考协议描述. https://chromedevtools.github.io/devtools-protocol/
           返回值:None超时;其他为回应结果"""
        self.last_err = None
        if self._is_bad():
            return None
        if not self._websocket or (self.cycle and self.cycle.hit()):
            self.reopen()  # 进行ws的重连

        # 不允许使用普通参数传递,必须为key/value型参数
        timeout = kwargs.pop("_timeout", self.timeout)  # 额外摘取超时控制参数

        result, err = self._call({"method": _method, "params": kwargs}, timeout=timeout)  # 发起调用请求
        if err:
            self.last_err = f'call_method<{_method}> fail: {err}'

        if result is None:
            return None

        if 'result' not in result and 'error' in result:
            # logger.warning("%s error: %s" % (_method, result['error']['message']))
            msg = result.get('error', {}).get('message', 'unknown')
            raise CallMethodException(f"{self._srctag()} calling method <{_method}> error\n{msg}")

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

    def getDocument(self, timeout=None):
        '''获取文档主体节点树(字典)'''
        if timeout is None:
            timeout = self.timeout
        res = self.call_method('DOM.getDocument', _timeout=timeout)
        return res["root"]

    def querySelector(self, selector, parentid=None, timeout=None):
        '''在指定的parentid节点上执行选择器,获取对应的节点'''
        if timeout is None:
            timeout = self.timeout
        if parentid is None:
            parentid = self.getDocument(timeout)["nodeId"]
        res = self.call_method('DOM.querySelector', nodeId=parentid, selector=selector, _timeout=timeout)
        return res["nodeId"] if res["nodeId"] > 0 else None

    def querySelectorAll(self, selector, parentid=None, timeout=None):
        '''在指定的parentid节点上执行选择器,获取对应的全部节点'''
        if timeout is None:
            timeout = self.timeout
        if parentid is None:
            parentid = self.call_method('DOM.getDocument', _timeout=timeout)
            parentid = parentid["root"]["nodeId"]
        res = self.call_method('DOM.querySelectorAll', nodeId=parentid, selector=selector, _timeout=timeout)
        return res["nodeIds"]

    def queryNodeBox(self, sel, parentid=None, timeout=None):
        """在指定的parentid节点上执行选择器sel,获取对应的节点box模型数据
            矩形表达为8个浮点数的数组,分别为[左,上,右,上,右,下,左,下]
            返回值:{'content':内容矩形,'padding':填充矩形,'border':边框矩形,'margin':外边界矩形,'width':整体宽度,'height':整体高度},nodeid
        """
        if timeout is None:
            timeout = self.timeout
        if isinstance(sel, str):
            nid = self.querySelector(sel, parentid, timeout)
        else:
            nid = sel

        if nid is None:
            return None, None
        res = self.call_method('DOM.getBoxModel', nodeId=nid, _timeout=timeout)
        return res['model'], nid

    def getViewport(self):
        """获取页面布局视口信息.返回值:(布局信息对象,msg),msg为空正常,否则信息对象为None
        {'offsetX': 0 相对于布局视窗的水平偏移量,
         'offsetY': 0 相对于布局视窗的垂直偏移量,
         'pageX': 视口左侧的内容坐标, 'pageY': 视口顶部的内容坐标,
         'clientWidth': 视口宽度, 'clientHeight': 视口高度,
         'scale': 1 视口缩放比例,
         'zoom': 1 页面缩放因子,
         'width': 内容宽度,
         'height': 内容高度}
        """
        try:
            res = self.call_method('Page.getLayoutMetrics')
            if res is None:
                return None, 'Page.getLayoutMetrics fail.'

            # 查询视口尺寸
            Viewport = None
            if 'cssVisualViewport' in res:
                Viewport = res['cssVisualViewport']
            elif 'visualViewport' in res:
                Viewport = res['visualViewport']
            else:
                return None, 'visualViewport not found.'

            # 查询内容尺寸
            Box = None
            if 'cssContentSize' in res:
                Box = res['cssContentSize']
            elif 'contentSize' in res:
                Box = res['contentSize']
            else:
                return None, 'contentSize not found.'

            # 记录内存尺寸
            Viewport['contentWidth'] = Box['width']
            Viewport['contentHeight'] = Box['height']
            return Viewport, ''
        except Exception as e:
            return None, e.__repr__()

    def setEmuScreen(self, width, height, timeout=20, scale=1, mobile=False):
        """设置模拟屏幕的尺寸,校正旧版本chrome全尺寸截图失效的情况"""
        try:
            if timeout is None:
                timeout = self.timeout
            if width and height:
                res = self.call_method('Emulation.setDeviceMetricsOverride', width=width, height=height, deviceScaleFactor=scale, mobile=mobile, _timeout=timeout)
            else:
                res = self.call_method('Emulation.clearDeviceMetricsOverride', _timeout=timeout)
            if res is None:
                return 'Emulation.setDeviceMetricsOverride fail.'
            return ''
        except Exception as e:
            return None, e.__repr__()

    def getScreenshot(self, tobin=True, timeout=20, isfull=True, scale=1, quality=None):
        """获取页面图像快照
            tobin - 是否返回二进制而不是base64串
            timeout - 等待超时时间
            isfull - 指定抓取视口范围或完整内容范围.
            scale - 拉伸缩放比例
            quality - jpeg压缩品质系数,1~100
            返回值:(base64图像数据,msg),msg为空正常
        """
        box, msg = self.getViewport()
        if msg:
            return None, msg

        args = {}
        if timeout is None:
            timeout = self.timeout

        # 等待超时
        args['_timeout'] = timeout

        # 图像格式
        if quality:
            args['format'] = 'jpeg'
            args['quality'] = quality
        else:
            args['format'] = 'png'

        # 截图范围
        if isfull:
            args['clip'] = {'x': 0, 'y': 0, 'width': box['contentWidth'], 'height': box['contentHeight'], 'scale': scale}
            args['captureBeyondViewport'] = True
            self.setEmuScreen(args['clip']['width'], args['clip']['height'])  # 修正chrome86不能正确全尺寸截图的问题
        else:
            args['clip'] = {'x': 0, 'y': 0, 'width': box['clientWidth'], 'height': box['clientHeight'], 'scale': scale}

        try:
            img = self.call_method('Page.captureScreenshot', **args)
            if isfull:
                self.setEmuScreen(None, None, timeout=timeout)
            if img is None or 'data' not in img:
                return None, 'Page.captureScreenshot fail.'
            if tobin:
                return base64.decodebytes(img['data'].encode('ascii')), ''
            else:
                return img['data'], ''
        except Exception as e:
            return None, e.__repr__()

    def sendKey(self, keyCode=0x0D, eventType='keyDown', modifiers=0, timeout=10):
        """给tab页发送键盘事件.返回值:错误消息
            keyCode参考:
                https://msdn.microsoft.com/en-us/library/dd375731(VS.85).aspx
                https://docs.microsoft.com/zh-cn/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
            eventType - 事件类型:keyDown, keyUp
            modifiers - 修饰类型:Alt=1, Ctrl=2, Meta/Command=4, Shift=8
        """
        try:
            r = self.call_method('Input.dispatchKeyEvent', type=eventType, windowsVirtualKeyCode=keyCode, nativeVirtualKeyCode=keyCode, modifiers=modifiers,
                                 _timeout=timeout)
            return '' if r is not None else 'sendMouse fail.'
        except Exception as e:
            return spd_base.es(e)

    def sendMouseEvent(self, x, y, eventType='mousePressed', button=None, modifiers=0, timeout=10):
        """给tab页发送鼠标事件.返回值:错误消息
            x,y - 鼠标位置
            eventType - 事件类型: mousePressed, mouseReleased, mouseMoved, mouseWheel
            button - 按钮类型: none, left, middle, right, back, forward
            modifiers - 修饰类型:Alt=1, Ctrl=2, Meta/Command=4, Shift=8
        """
        try:
            args = {}
            if button:
                args['button'] = button
                args['clickCount'] = 1
            if modifiers:
                args['modifiers'] = modifiers
            r = self.call_method('Input.dispatchMouseEvent', type=eventType, x=x, y=y, **args, _timeout=timeout)
            return '' if r is not None else 'sendMouse fail.'
        except Exception as e:
            return spd_base.es(e)

    def take_pos(self, sel, rand=True):
        """获取指定CSS选取器sel对应的元素位置点,可进行随机偏移.
            返回值:(x,y),'' 或 None,errmsg
        """
        try:
            model, nodeid = self.queryNodeBox(sel, None, self.timeout)
            if model is None:
                return None, ''  # 目标不存在
            border = model['border']
            pt = util_curve.make_rect_center((border[0], border[1]), (border[4], border[5]), rand)
            return pt, ''
        except Exception as e:
            return None, py_util.get_trace_stack()

    def mouse_move(self, path, button='left'):
        """在指定的tab页上,控制鼠标按指定的路径path进行移动.如果指定了按钮button,则是拖拽动作."""
        sz = len(path)
        for i in range(sz):
            pt = path[i]
            msg = self.sendMouseEvent(pt[0], pt[1], 'mouseMoved')

            if msg:
                return msg

            if not button:
                continue

            if i == 0:
                msg = self.sendMouseEvent(pt[0], pt[1], 'mousePressed', button)
                if msg:
                    return msg
            elif i == sz - 1:
                msg = self.sendMouseEvent(pt[0], pt[1], 'mouseReleased', button)
                if msg:
                    return msg

        return ''

    def mouse_click(self, dst, button='left'):
        """在指定的tab页面对指定点位置或CSS选取器dst目标发起鼠标按钮button点击"""
        try:
            if isinstance(dst, str):
                pt, msg = self.take_pos(dst)
                if msg:
                    return msg
            else:
                pt = dst
            msg = self.sendMouseEvent(pt[0], pt[1], 'mousePressed', button, timeout=self.timeout)
            if msg:
                return msg
            msg = self.sendMouseEvent(pt[0], pt[1], 'mouseReleased', button, timeout=self.timeout)
            if msg:
                return msg
            return ''
        except Exception as e:
            return py_util.get_trace_stack()

    def _on_requestWillBeSent(self, requestId, loaderId, documentURL, request, timestamp, wallTime, initiator, **param):
        """记录发送的请求信息"""
        url = request['url']
        if self.req_event_filter_re and not spd_base.query_re_str(url, self.req_event_filter_re):
            return  # 如果明确指定了re规则进行匹配,则不匹配时直接退出
        if url not in self._data_requestWillBeSent:
            self._data_requestWillBeSent[url] = []  # 创建url对应的发送请求信息列表
        if len(self._data_requestWillBeSent[url]) > 100:
            self._data_requestWillBeSent[url].pop(0)  # 如果信息列表过长则清空最初的旧数据
        self._data_requestWillBeSent[url].append((request, requestId))  # 记录请求信息和请求id
        self._data_requestIDs[requestId] = [request]  # 记录requestid对应的请求信息,回应阶段1

    def _on_responseReceived(self, requestId, loaderId, timestamp, type, response, **args):
        """记录请求对应的应答信息"""
        if requestId not in self._data_requestIDs:
            return

        r = self._data_requestIDs[requestId]
        r.append(response)  # 记录当前请求的应答头,回应阶段2

    def _on_loadingFinished(self, requestId, timestamp, encodedDataLength, *arg, **args):
        """记录请求对应的完成信息"""
        if requestId not in self._data_requestIDs:
            return

        r = self._data_requestIDs[requestId]
        r.append(encodedDataLength)  # 记录当前请求的完整应答内容长度,回应阶段3

    def get_request_urls(self, hold_url, url_is_re=True):
        """获取记录过的请求url列表"""

        def _get():
            if hold_url is None:  # 没有明确告知拦截url的模式,则返回全部记录的请求url
                return list(self._data_requestWillBeSent.keys())

            rst = []
            if url_is_re:
                for url in self._data_requestWillBeSent.keys():
                    if spd_base.query_re_str(url, hold_url):  # 否则记录匹配的请求url
                        rst.append(url)
            else:
                if self.get_request_info(hold_url):
                    rst.append(hold_url)

            return rst

        rst = _get()
        if len(rst) == 0:
            self.recv_loop()
            rst = _get()
        return rst

    def get_request_info(self, url=None):
        """获取已经发送的请求信息;如果给定了明确的url,则返回该url对应的最新请求列表;否则返回全部记录的请求字典."""

        def _get():
            if url:
                if url in self._data_requestWillBeSent:
                    return self._data_requestWillBeSent[url]
                else:
                    return None
            else:
                return self._data_requestWillBeSent

        rst = _get()
        if not rst or len(rst) == 0:
            self.recv_loop()
            rst = _get()
        return rst

    def get_request_infos(self, url, url_is_re=False):
        """获取指定url的请求信息
            工作流程:1 打开tab页的时候,就需要告知url的匹配模式;2 等待页面装载完成,内部记录发送的请求信息; 3根据url查找发送的请求内容.
            返回值: [(request,requestId)],msg
                    msg为''则正常;request为请求内容;requestId为请求ID,可据此获取更多数据.
        """
        try:
            if url_is_re:
                urls = self.get_request_urls(url, url_is_re)
                if len(urls) == 0:
                    return None, ''
                rst = []
                for u in urls:
                    rst.extend(self.get_request_info(u))
                return rst, ''
            else:
                return self.get_request_info(url), ''

        except Exception as e:
            return None, spd_base.es(e)

    def get_response_info(self, reqid, stat=3):
        """根据请求id获取对应的回应信息,要求回应阶段满足stat的数量要求,返回值:None回应不存在;其他为回应对象."""

        def _get():
            r = self._data_requestIDs.get(reqid)
            if not r or len(r) != stat:
                return None
            return r

        rst = _get()
        if rst:
            return rst
        self.recv_loop()  # 重试接收一次
        return _get()

    def wait_response_info(self, reqid, timeout, stat=3):
        """最多等待timeout回应完成.返回值:None超时;否则为回应信息"""
        wait = spd_base.waited_t(timeout)
        while True:
            r = self.get_response_info(reqid, stat)
            if r:
                return r
            if wait.timeout():
                break
        return None

    def get_response_body(self, reqid, proto_timeout=10):
        """根据请求id获取回应body内容.需要先确保回应已经完成,否则出错.
            返回值:(body,err) err为空则正常
        """
        try:
            rst = self.call_method('Network.getResponseBody', requestId=reqid, _timeout=proto_timeout)
            if rst is None:
                return None, 'Network.getResponseBody call fail: %s' % self.last_err
            body = rst['body']
            en = rst['base64Encoded']
            if en:
                body = base64.decodebytes(body.encode('latin-1'))
            return body, ''
        except Exception as e:
            return None, spd_base.es(e)

    def clear_request_historys(self):
        """清理全部历史的请求信息"""
        self._data_requestWillBeSent.clear()
        self._data_requestIDs.clear()

    def _open_websock(self):
        if self._websocket:
            return
        opt = [(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 64)]
        try:
            self._websocket = websocket.create_connection(self._websocket_url, enable_multithread=True, sockopt=opt, skip_utf8_validation=True)
        except Exception as e:
            raise e

    def _close_websock(self):
        if self._websocket:
            self._websocket.close()
            self._websocket = None

    def init(self, req_event_filter=None, downpath=None):
        """启动tab交互象,建立websocket连接"""
        if self._websocket:
            return True
        self.downpath = downpath
        self.req_event_filter_re = req_event_filter
        return self.reopen()

    def reopen(self):
        """对tab的websocket连接进行强制重连处理"""
        try:
            self._close_websock()
            self._open_websock()
            if self._is_bad():
                return False
            if self.type != 'browser':
                self.call_method('Page.enable', _timeout=10)
                self.call_method('Network.enable', maxResourceBufferSize=_maxResourceBufferSize, maxTotalBufferSize=_maxTotalBufferSize, _timeout=30)
            if self.downpath:
                self.call_method('Browser.setDownloadBehavior', behavior='allow', downloadPath=self.downpath, _timeout=30)
            return True
        except websocket.WebSocketBadStatusException as e:
            logger.warning(f'{self._srctag()} reopen fail => {self._websocket_url}')
            return False
        except Exception as e:
            logger.warning(f'{self._srctag()} reopen error {self._websocket_url} => {py_util.get_trace_stack()}')
            return False

    def close(self):
        """停止tab交互,关闭websocket连接"""
        self._close_websock()
        self.clear_request_historys()
        self._wait_result = -1
        self.type = 'CLOSE'
        return True

    def goto(self, url, proto_timeout=10):
        """控制tab页浏览指定的url.返回值({'frameId': 主框架id, 'loaderId': 装载器id}, 错误消息)"""
        try:
            self.clear_request_historys()  # 每次发起新导航的时候,都清空之前记录的请求信息
            self.last_url = url
            rst = self.call_method('Page.navigate', url=url, _timeout=proto_timeout)
            return rst, ''
        except Exception as e:
            return None, spd_base.es(e)

    def exec(self, js, proto_timeout=10):
        """在tab页中运行js代码.返回值(运行结果,错误消息)"""
        try:
            rst = self.call_method('Runtime.evaluate', expression=js, returnByValue=True, _timeout=proto_timeout)
            if rst is None:
                return '', ''
            ret = rst['result']
            if 'value' in ret:
                return ret['value'], ''  # 正常有返回值
            elif 'description' in ret:
                return '', ret['description']  # 出现错误了
            elif 'type' in ret and ret['type'] == 'undefined':
                return '', ''  # 正常无返回值
            else:
                return '', ret  # 其他错误
        except Exception as e:
            return '', py_util.get_trace_stack()

    def stop(self, proto_timeout=10):
        """控制指定的tab页停止浏览.返回值:错误消息,空正常"""
        try:
            rst = self.call_method('Page.stopLoading', _timeout=proto_timeout)
            return ''
        except Exception as e:
            return None, spd_base.es(e)


class MouseAct:
    """多个鼠标动作的组合执行器.
        1 必须先调用enter进入到视口的目标位置
        2 整体多个动作可链式调用,简化编码: enter(dst1).move(dst2).sleep().click()
        3 过程中出现的首个错误记录在err中,并且后续动作被放弃.
        可用于判断整体动作是否成功完成.
    """

    def __init__(self, tab):
        self.last = None  # 上一次动作最后停留的点位
        self.tab = tab  # 操纵的tab页对象
        self.err = None  # 记录过程中出现的首个错误(idx,type,msg),
        self.acts = None  # 动作执行的数量

    def enter(self, dst=None, btn=None):
        """鼠标从上方进入tab视口,到达CSS选取器dst对应的元素或目标点.
            返回值:self
        """
        self.last = None
        self.acts = 0

        if isinstance(dst, str):
            dst, msg = self.tab.take_pos(dst)  # 获取目标位置
            if msg:
                self.err = (self.acts, 'enter', msg)
                return self

        if not dst:
            dst = (100, 100)  # dst无效的时候,给出默认值

        src = (round(50 + util_curve.random.random() * 200), 0)  # 视口上边缘的随机位置
        path = util_curve.make_beizer2_path3(src, dst)
        self.last = path[-1]  # 记录最后的位置

        msg = self.tab.mouse_move(path, btn)  # 移动鼠标
        if msg:
            self.err = (self.acts, 'enter', msg)
        return self

    def click(self, dst=None, btn='left'):
        """在目标CSS选取器或点位dst上点击鼠标按钮btn.如果没有dst则在最后的点位处点击.
            返回值:self
        """
        self.acts += 1
        if self.err:
            return self

        if isinstance(dst, str):
            dst, msg = self.tab.take_pos(dst)  # 获取目标位置
            if msg:
                self.err = (self.acts, 'click', msg)
                return self

        if dst:
            self.last = dst  # 记录目标位置

        msg = self.tab.mouse_click(self.last, btn)  # 执行点击
        if msg:
            self.err = (self.acts, 'click', msg)
        return self

    def move(self, dst, btn=None):
        """从当前点位移动到CSS选取器目标或点位dst,如果给定了按钮btn则进行拖放.
            返回值:self
        """
        if self.last is None:
            return self.enter(dst, btn)  # 没有上一次的点位,那么就认为是首次进入

        self.acts += 1
        if self.err:
            return self

        if isinstance(dst, str):
            dst, msg = self.tab.take_pos(dst)  # 获取目标位置
            if msg:
                self.err = (self.acts, 'move', msg)
                return self

        path = util_curve.make_beizer2_path3(self.last, dst)
        self.last = path[-1]  # 记录最后的位置

        msg = self.tab.mouse_move(path, btn)  # 移动鼠标
        if msg:
            self.err = (self.acts, 'move', msg)

        return self

    def moveto(self, dst):
        return self.move(dst)

    def lineto(self, dst):
        return self.move(dst, 'left')

    def sleep(self, delay=0.5, range=0.5):
        """休眠动作,用于更好的模拟人工动作.休眠时间为delay+随机range.
            返回值:self
        """
        self.acts += 1
        if self.err:
            return self

        t = round(delay + range * util_curve.random.random(), 2)
        time.sleep(t)
        return self


def _load_json(rp: requests.Response) -> dict:
    return json.loads(rp.text)


def chrome_list_tab(chrome_addr, session=None, excludes={}, timeout=None):
    """查询chrome_addr浏览器所有打开的tab页列表.
        session - 多次调用时使用的http会话管理器
        timeout - 超时时间
        excludes - 需要排除的tabid集合
        返回值:[{'id': tabid, 'title': '', 'url': ''}],''
            或 None,error
    """
    if session is None:
        session = requests

    try:
        dst_url = f"http://{chrome_addr}/json"
        rst_tabs = []
        rp = session.get(dst_url, timeout=timeout, proxies={'http': None, 'https': None})

        tab_jsons = _load_json(rp)
        for tab_json in tab_jsons:
            if tab_json['type'] != 'page':  # pragma: no cover
                continue  # 只保留page页面tab,其他后台进程不记录

            id = tab_json['id']
            if id in excludes:
                continue

            # 构造基本的tab信息对象
            tinfo = {'id': id, 'title': tab_json['title'], 'url': tab_json['url'], 'webSocketDebuggerUrl': tab_json['webSocketDebuggerUrl']}
            rst_tabs.append(tinfo)
        return rst_tabs, ''
    except Exception as e:
        return None, spd_base.es(e)


def chrome_makeup_tabs(infos, tabs, backinit=True, req_event_filter=None, excludes={}):
    """根据给定的tab信息列表infos,在已有的tab对象字典tabs中补充新的tab对象,并可进行初始化
        返回值:新增补充的tab数量
    """
    rc = 0
    for tinfo in infos:
        id = tinfo['id']
        if id not in tabs:
            if id in excludes:  # 明确被排除的tab,不处理.
                continue
            # 补充新的tab信息对应的tab对象
            rc += 1
            tabs[id] = Tab(**tinfo)
            if backinit:
                tabs[id].init(req_event_filter)
        else:
            # 更新已有tab对象的相关属性
            tabs[id].last_url = tinfo['url']
            tabs[id].last_title = tinfo['title']
    return rc


def chrome_open_tab(chrome_addr, dsturl, session=None, timeout=None):
    """在指定的chrome_addr上打开新tab并浏览目标dsturl
        返回值:tabinfo,''
            或 None,error
    """
    if session is None:
        session = requests
    try:
        rp = session.get(f"http://{chrome_addr}/json/new?{dsturl}", timeout=timeout, proxies={'http': None, 'https': None})
        rst = _load_json(rp)
        return rst, ''
    except Exception as e:
        return None, spd_base.es(e)


def chrome_activate_tab(chrome_addr, tab_id, session=None, timeout=None):
    """激活指定的tab页.返回值:空正常,否则为错误."""
    if session is None:
        session = requests
    try:
        rp = session.get(f"http://{chrome_addr}/json/activate/{tab_id}", timeout=timeout, proxies={'http': None, 'https': None})
        return ''
    except Exception as e:
        return spd_base.es(e)


def chrome_close_tab(chrome_addr, tab_id, session=None, timeout=None):
    """关闭指定的tab页,返回值:空正常,否则为错误."""
    if session is None:
        session = requests
    try:
        rp = session.get(f"http://{chrome_addr}/json/close/{tab_id}", timeout=timeout, proxies={'http': None, 'https': None})
        return ''
    except Exception as e:
        return spd_base.es(e)


def chrome_version(chrome_addr, session=None, timeout=None):
    """查询浏览器的版本信息,返回值:(ver,'')或(None,error)"""
    if session is None:
        session = requests
    try:
        rp = session.get(f"http://{chrome_addr}/json/version", timeout=timeout, proxies={'http': None, 'https': None})
        rst = _load_json(rp)
        return rst, ''
    except Exception as e:
        return None, spd_base.es(e)


# Chrome浏览器管理对象
class Browser(object):

    def __init__(self, url="http://127.0.0.1:9222"):
        self.hostport = up.urlparse(url)[1]
        self._tabs = {}  # 记录被管理的tab页
        self._session = requests.Session()  # http会话对象
        ver, _ = chrome_version(self.hostport, self._session)
        sp = '\\'
        if ver:
            if ver['User-Agent'].find('Linux') != -1:
                basedir = '/home/'
                sp = '/'
            elif self.hostport.startswith('127.'):
                basedir = os.getcwd() + '\\'
            else:
                basedir = 'c:\\'
        else:
            basedir = os.getcwd() + '\\'
        self.downpath = basedir + 'tmpdown' + spd_base.query_re_str(url, r'://.*:(\d+)', '9222') + sp

        self._brw = None
        self._brws = {}  # 代理关联的浏览器id映射表 {'代理地址':'浏览器上下文id'}

    def brw_conn(self):
        """连接目标浏览器主体端点"""
        ver, _ = chrome_version(self.hostport, self._session)
        if ver is None:
            return f'query browser version fail: {self.hostport}'
        url = ver['webSocketDebuggerUrl']
        dst = {'id': url.split('/')[-1], 'type': 'browser', 'url': url, 'title': 'browser', 'webSocketDebuggerUrl': url}
        self._brw = Tab(**dst)
        self._brw.clear_listeners()
        if not self._brw.init():
            return f'conn browser fail: {url}'
        return ''

    def brw_take(self, proxy, url=None):
        """使用指定的代理线路打开一个新的tab.
            proxy - 代理服务器地址,如 '172.17.200.2:3039'
           返回值:tab信息字典,或None
        """
        if self._brw is None and self.brw_conn():
            return None
        url = url or ''

        def get_brw(proxy):
            brwId = self._brws.get(proxy)
            if brwId is None:
                rst = self._brw.call_method('Target.createBrowserContext', disposeOnDetach=True, proxyServer=proxy, _timeout=20)
                if rst is None:
                    return None
                brwId = rst['browserContextId']
                self._brws[proxy] = brwId
            return brwId

        for i in range(2):
            brwId = get_brw(proxy)
            if brwId is None:
                return None  # 上下文获取/创建失败,直接返回

            try:
                rst = self._brw.call_method('Target.createTarget', url=url, browserContextId=brwId, _timeout=20)
                tid = rst['targetId']
                return {'id': tid, 'type': 'page', 'brwId': brwId, 'webSocketDebuggerUrl': f'ws://{self.hostport}/devtools/page/{tid}'}
            except Exception as e:
                self.brw_close(proxy)  # 交互失败,放弃当前浏览器上下文,准备重试

        return None

    def brw_close(self, proxy):
        """关闭指定代理线路对应的浏览器上下文核心"""
        brwId = self._brws.get(proxy)
        if brwId is None:
            return None

        try:
            del self.brws[proxy]
            self._brw.call_method('Target.disposeBrowserContext', browserContextId=brwId, _timeout=20)
            return True
        except Exception as e:
            return False

    def new_tab(self, url=None, timeout=None, start=True, req_event_filter=None, proxy=None, srcid=''):
        """打开新tab页,并浏览指定的网址"""
        url = url or ''
        if proxy is None:
            rp, err = chrome_open_tab(self.hostport, url, self._session, timeout)
            if err:
                raise PyChromeException(f'open_tab fail: {url}')
            tab = Tab(**rp, srcid=srcid)
        else:
            # 使用指定的代理线路打开tab页
            tinfo = self.brw_take(proxy, url)
            if tinfo is None:
                raise PyChromeException(f'new_tab with proxy fail: {url}')
            tab = Tab(**tinfo, srcid=srcid)

        self._tabs[tab.id] = tab
        if start:
            tab.init(req_event_filter, downpath=self.downpath)
        return tab

    def list_tab(self, timeout=None, backinit=True, req_event_filter=None, excludes={}):
        """列出浏览器所有打开的tab页,可控制是否反向补全外部打开的tab进行操控.
            返回值:[{'id': tabid, 'title': '', 'url': ''}]
        """
        _tabs_list, err = chrome_list_tab(self.hostport, self._session, excludes, timeout)
        if err:
            raise PyChromeException(f'list_tab fail: {self.hostport}')

        self.makeup_tab(_tabs_list, backinit, req_event_filter, excludes)
        return _tabs_list

    def makeup_tab(self, tabs, backinit=True, req_event_filter=None, excludes={}):
        """使用tabs信息列表,反向补全外部打开的tab页.
            返回值:补充的tab对象数量
        """
        return chrome_makeup_tabs(tabs, self._tabs, backinit, req_event_filter, excludes)

    def tab_infos(self):
        """根据已有tab对象生成tab信息列表"""
        _tabs_list = []
        for id in self._tabs:
            t = self._tabs[id]
            tinfo = {'id': id, 'title': t.last_title, 'url': t.last_url}
            _tabs_list.append(tinfo)
        return _tabs_list

    def tabs(self):
        """获取已知tab的数量"""
        return len(self._tabs)

    def activate_tab(self, tab_id, timeout=None):
        """激活指定的tab页"""
        if isinstance(tab_id, Tab):
            tab_id = tab_id.id
        if chrome_activate_tab(self.hostport, tab_id, self._session, timeout):
            raise PyChromeException(f'activate_tab fail: {tab_id}')

    def close_tab(self, tab_id, timeout=None):
        """关闭指定的tab页"""
        if isinstance(tab_id, Tab):
            tab_id = tab_id.id

        if chrome_close_tab(self.hostport, tab_id, self._session, timeout):
            raise PyChromeException(f'close_tab fail: {tab_id}')

        tab = self._tabs.pop(tab_id, None)
        tab.close()
        tab = None


dom100 = '''
//DOM选取功能封装:el为选择表达式或已选取的对象;parent为选取的父节点范围作用域,也可以为父节点的选取表达式
var _$_ = function(exp, parent) {
	var api = { el: null } //最终返回的API对象,初始的时候其持有的el元素对象为null
	var qs = function(selector, parent) { //内部使用的CSS选择器单节点查询函数
		parent = parent || document;
		return parent.querySelector(selector);
	};
	var qsa = function(selector, parent) { //内部使用的CSS选择器多节点查询函数
		parent = parent || document;
		return parent.querySelectorAll(selector);
	};
	var qx=function(xpath,parent) { //内部使用的xpath多节点查询函数
		parent = parent || document;
	    var xresult = document.evaluate(xpath, parent, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
	    switch(xresult.snapshotLength)
		{
		    case 0:return null;
		    case 1:return xresult.snapshotItem(0);
		    default:
			    var xnodes = [];
			    for(var i=0;i<xresult.snapshotLength;++i)
				    xnodes.push(xresult.snapshotItem(i));
			    return xnodes;
		}
	};

	//对外提供val值操作函数,获取或设置
	api.val = function(value) {
		if(!this.el) return null;
		//判断是取值还是赋值
		var set = !!value;
		//简单处理原生value值的工具
		var useValueProperty = function(value) {
			//赋值时返回封装对象或取值时返回值本身
			if(set) { this.el.value = value; return api; }
			else { return this.el.value; }
		}
		//根据节点的tag类型进行分类处理
		switch(this.el.nodeName.toLowerCase()) {
			case 'input':
				//是input元素,需要再判断UI类型
				var type = this.el.getAttribute('type');
				if(type != 'radio' && type != 'checkbox') 
					return useValueProperty.apply(this, [value]); //其他UI类型则直接简单处理
				//如果是radio组或checkBox组,需要进行部分元素的选择与其他元素的反选处理
				var els = qsa('[name="' + this.el.getAttribute('name') + '"]', parent);
				var values = [];
				for(var i=0; i<els.length; i++) {
					if(set && els[i].checked && els[i].value !== value) { els[i].removeAttribute('checked'); } 
					else if(set && els[i].value === value) {
						els[i].setAttribute('checked', 'checked');
						els[i].checked = 'checked';
					} else if(els[i].checked) { values.push(els[i].value); }
				}
				if(!set) { return type == 'radio' ? values[0] : values; }
				break;
			case 'textarea': //文本框的值处理
				return useValueProperty.apply(this, [value]); 
			case 'select':
				//下拉列表框的值处理
				if(!set) return this.el.value;
				var options = qsa('option', this.el);
				for(var i=0; i<options.length; i++) 
					if(options[i].getAttribute('value') === value) {this.el.selectedIndex = i;}
					else {options[i].removeAttribute('selected');}
				break;
			default: 
				//其他类型的元素,处理innerHTML或textContent
				if(set) {this.el.innerHTML = value;}
				else {
					if (typeof this.el.textContent != 'undefined') { return this.el.textContent; } 
					else if(typeof this.el.innerText != 'undefined') {return typeof this.el.innerText;} 
					else {return this.el.innerHTML;}
				}
				break;
		}
		return set ? api : null;	//返回值,可继续链式调用;取值动作在上面处理,这里返回null
	}
	//对外提供的触发事件功能,默认为点击事件,0ms延迟后异步执行
	api.hit=function (evtType,delayMs,key,mode){//evtType:"click/dbclick/mouseenter/mouseleave/blur/focus"
		evtType = evtType||"click";
		delayMs = delayMs || 0;
		el=this.el;
		setTimeout(function(){
		    var EventMode=key?'Event':'MouseEvent';
		    if (mode) EventMode=mode;
			var myEvent = document.createEvent(EventMode) //创建事件对象
			myEvent.initEvent(evtType, true, true);//初始化事件类型
			if (key)
			    myEvent.keyCode=key;
			el.dispatchEvent(myEvent);	//触发事件
		},delayMs);
	}
	api.click=function(){api.hit('click');} //对目标元素触发点击动作(是hit函数的语法糖,与jquery保持兼容.)
	api.frm=function(){ //查询获取iframe节点
		if (this.el==null || this.el.nodeName!='IFRAME')
			return null;
		return this.el.contentWindow;
	}
	api.frm_html=function(){ //获取iframe的整体内容.
	    cw=api.frm()
	    if (cw!=null && cw.document!=null && cw.document.documentElement!=null)
	        return cw.document.documentElement.outerHTML;
	    return "";
	}
	//根据输入的选择表达式的类型进行选取操作
	switch(typeof exp) {
		case 'string':
			//选取表达式为串,先处理得到正确的父节点
			parent = parent && typeof parent === 'string' ? qs(parent) : parent;
			if (exp.charAt(0)=='/'||(exp.charAt(0)=='.'&&exp.charAt(1)=='/')) api.el = qx(exp, parent);
			else api.el = qs(exp, parent);
			break;
		case 'object':
			//选取表达式为对象,如果对象是一个原生的DOM节点,则直接记录下来
			if(typeof exp.nodeName != 'undefined') api.el = exp;
			break;
	}
	return api; //对于选取操作,返回的就是封装后的对象
}
'''

# 用来进行ajax调用的功能函数
http_ajax = """
function _$_hashcode(str){
     var hashCode=1
     for(var i=0;i<str.length;i++)
        hashCode=37* hashCode + str.charCodeAt(i)
     return hashCode 
}
function _$_make_node(tag,val)
{
    var uid="#"+_$_hashcode(tag) //用show关键词的哈希码构造唯一标识
    var it=document.getElementById(uid);
    if (it==null)
    {
        it=document.createElement("textarea");
        it.id=uid;
        document.body.appendChild(it);
    }
    if (val=="")
        it.setAttribute("show","!");
    else
        it.setAttribute("show",tag);//只有成功的时候,指定的show关键词才会出现.
    it.innerHTML=val;
}

function http_ajax(url,method="GET",data=null,contentType="application/x-www-form-urlencoded",show="root")
{
    if (show=="root")
        document.documentElement.innerHTML="";
    else
        _$_make_node(show,"");
	var xmlhttp=new XMLHttpRequest();
	xmlhttp.onreadystatechange=function()
	{
		if (xmlhttp.readyState==4){
		    if (show=="root")
		        document.documentElement.innerHTML=xmlhttp.responseText;
		    else
		        _$_make_node(show,xmlhttp.responseText)
		}
	}
	xmlhttp.open(method,url);
	xmlhttp.setRequestHeader("Content-Type",contentType)
	
	if (data)
	    xmlhttp.send(data);
	else
	    xmlhttp.send();
	return "";
}
"""

# 简单的演示spd_chrome的常规功能goto/post/wait/dhtml的使用
demo = """
import spd_chrome as sc
c=sc.spd_chrome()
tid=0
c.goto(tid,'http://credit.chuzhou.gov.cn/publicity/doublePublicity/getXZCFPageInfo.do')
c.wait_re(tid,'msg')

print(c.post(tid,'http://credit.chuzhou.gov.cn/publicity/doublePublicity/getXZCFPageInfo.do?currentPageNo=3&pageSize=10',"dfbm=&bmbh=&keyword="))
c.wait_re(tid,'msg')

print(c.dhtml(tid,True)[0])
"""


def parse_cond(cond):
    """解析判断表达式,如果是以!!开头,则意味着是反向判断"""
    if cond.startswith('!!'):
        return True, cond[2:]
    return False, cond


def check_cond(isnot, rst):
    """判断条件的结果,根据是否反向逻辑决定结果是否完成.返回值:是否完成"""
    if isnot:
        return len(rst) == 0
    else:
        return len(rst) > 0


def make_cookie_str(cks):
    """根据cookie字典列表生成提交时使用的cookie串"""
    rst = []
    for c in cks:
        rst.append('%s=%s' % (c['name'], c['value']))
    return '; '.join(rst)


def make_cookie_dct(cks):
    """根据cookie字典列表生成提交时使用的cookie字典"""
    rst = {}
    for c in cks:
        rst[c['name']] = c['value']
    return rst


# 定义常见爬虫功能类
class spd_chrome:
    def __init__(self, proto_url="http://127.0.0.1:9222", enable_wait_evt=False):
        self.browser = Browser(proto_url)
        self.proto_timeout = 30
        self.on_waiting = None if not enable_wait_evt else self.on_cb_waiting  # 等待事件回调

    def on_cb_waiting(self, tab, page, loops, remain):
        """默认等待事件回调函数,可进行外部idle驱动,或其他判定处理.
            tab - 当前的tab对象
            page - 本次获取的页面内容
            loops - 目前已经循环等待过的次数
            remain - 剩余等待时间,秒float
            返回值:是否停止等待.
        """
        if loops:
            if not tab.last_title:
                # 在没有得到有效title的时候,尝试从html页面获取
                tab.last_title = spd_base.query_re_str(page, '<title>(.*?)</title>', '')
                if not tab.last_title:
                    # 页面获取失败则尝试动态从tab中获取
                    title, msg = tab.exec('document.title')
                    if title != tab.last_url:
                        tab.last_title = title  # 得到有效的title了,记录下来
            else:
                js = """document.title='等待<%d>次 剩余<%.02f>秒'""" % (loops, remain)
                tab.exec(js)  # 等待中,修改title显示进度
        elif tab.last_title:
            js = """document.title='%s'""" % tab.last_title  # 等待完成,恢复原有title
            tab.exec(js)

        return False

    def open(self, url='', req_event_filter=None, proxy=None, srcid=''):
        """打开tab页,并浏览指定的url;返回值:(tab页标识id,错误消息)"""
        try:
            tab = self.browser.new_tab(url, self.proto_timeout, req_event_filter=req_event_filter, proxy=proxy, srcid=srcid)
            return tab.id, ''
        except Exception as e:
            return '', py_util.get_trace_stack()

    def new(self, url='', req_event_filter=None, proxy=None, srcid=''):
        """打开tab页,并浏览指定的url;返回值:(tab页对象,错误消息)"""
        try:
            tab = self.browser.new_tab(url, self.proto_timeout, req_event_filter=req_event_filter, proxy=proxy, srcid=srcid)
            return tab, ''
        except Exception as e:
            return None, py_util.get_trace_stack()

    def list(self, backinit=True, excludes={}):
        """列出现有打开的tab页,backinit可告知是否反向补全外部打开的tab进行操控;返回值:([{tab}],错误消息)
            按最后的活动顺序排列,元素0总是当前激活的tab页
        """
        try:
            rst = self.browser.list_tab(self.proto_timeout, backinit, excludes=excludes)
            return rst, ''
        except requests.exceptions.ConnectionError:
            return '', 'connect fail: %s' % self.browser.hostport
        except Exception as e:
            return '', py_util.get_trace_stack()

    def wait_request_infos(self, tab, url, timeout=60, url_is_re=True):
        """尝试等待请求信息中出现指定的url.返回值:([请求信息列表],msg),msg为空正常."""
        try:
            t = self._tab(tab)
            wait = spd_base.waited_t(timeout)
            while True:
                dst, msg = t.get_request_infos(url, url_is_re)
                if dst and len(dst):
                    return dst, ''
                if wait.timeout():
                    break
            return [], ''
        except Exception as e:
            return None, py_util.get_trace_stack()

    def clear_request(self, tab, url=None):
        """清空记录的请求内容"""
        try:
            t = self._tab(tab)
            req_lst = t.get_request_info(url)
            req_lst.clear()
            return ''
        except Exception as e:
            return py_util.get_trace_stack()

    def wait_response_body(self, tab, url, url_is_re=False, timeout=30, mode=None):
        """获取指定url的回应内容
            工作流程:1 等待页面装载完成,内部记录发送的请求信息; 2 根据url查找发送的请求id; 3 使用请求id获取对应的回应内容.
            mode = None or 'body' - 提取对应的回应内容; 'req' - 请求头; 'rsp' - 回应头
            返回值: (body,msg)
                    msg为''则正常;body为回应内容
        """
        t = self._tab(tab)
        if not mode:
            mode = 'body'

        def get_downtmp(rrinfo, downpath):
            """在回应获取失败的时候,尝试查找下载文件"""
            if len(rrinfo) != 3:
                return None
            rsp_heads = rrinfo[1].get('headers', None)
            if rsp_heads is None:
                return None
            Content_disposition = rsp_heads.get('Content-disposition', None)
            if Content_disposition is None:
                return None
            # attachment; filename="五河县农村供水保障项目双忠庙供水区群众喝上更好水工程施工补遗说明BB2022WHGCZ004.pdf"
            filename = spd_base.query_re_str(Content_disposition, r'filename\s*=\s*"?([^"]*)[";]?', None)
            if filename is None:
                return None
            filepath = downpath + filename
            filedata = spd_base.load_from_file(filepath, None, 'rb')
            if filedata:
                os.remove(filepath)  # 下载并读取成功了,则删除当前的文件
            return filedata

        # 先等待请求信息被发出
        req_lst, msg = self.wait_request_infos(tab, url, timeout, url_is_re)
        if msg:
            return None, msg
        if not req_lst:
            return None, 'requestWaiting.'
        if mode == 'req':
            rr = req_lst[-1][0]
            rst = {'url': rr['url'], 'method': rr['method'], 'headers': rr['headers'], }
            return spd_base.dict2json(rst)

        # 再等待请求的回应内容到达
        _, reqid = req_lst[-1]
        rrinfo = t.wait_response_info(reqid, timeout)
        if not rrinfo:
            return None, 'responseWaiting.'
        if mode == 'rsp':
            rr = rrinfo[1]
            rst = {'url': rr['url'], 'status': rr['status'], 'statusText': rr['statusText'], 'headers': rr['headers'], }
            return spd_base.dict2json(rst)

        # 不要求回应body的时候,等待回应完成就直接返回
        if mode != 'body':
            return None, ''

        # 之后再提取回应body
        rst, msg = t.get_response_body(reqid, self.proto_timeout)
        if rst is None or msg and t.downpath:
            # 回应提取不成功的时候,还需要尝试判断是否有下载文件
            rst = get_downtmp(rrinfo, t.downpath)
            if rst is not None:
                msg = ''
        return rst, msg

    def clear_cookies(self, tab):
        """删除浏览器全部的cookie值;
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            rst = t.call_method('Network.clearBrowserCookies', _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def clear_cache(self, tab):
        """删除浏览器全部的cache内容;
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            rst = t.call_method('Network.clearBrowserCache', _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def page_reload(self, tab, nocache=False):
        """重新装载页面.nocache告知是否强制重装(不使用缓存)
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            rst = t.call_method('Page.reload', ignoreCache=nocache, _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def clear_storage(self, tab, url=None, types='all'):
        """删除浏览器指定域名下的storage数据;types可以为以下值逗号分隔串:
            appcache, cookies, file_systems, indexeddb, local_storage, shader_cache, websql, service_workers, cache_storage, interest_groups, all, other
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            if url is None:
                url = t.last_url
            origin = spd_base.query_re_str(url, '^.*?://.*?/')
            if origin is None:
                origin = url
            t.call_method('Storage.clearDataForOrigin', origin=origin, storageTypes=types, _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def miss_cache(self, tab, is_disable=True):
        """是否屏蔽缓存内容的使用;
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            rst = t.call_method('Network.setCacheDisabled', cacheDisabled=is_disable, _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def set_cookie(self, tab, name, val, domain, expires=None, path='/', secure=False):
        """设置cookie,需要给出必要的参数;
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            if expires is None:
                expires = int(time.time()) + 3600 * 24 * 365
            rst = t.call_method('Network.setCookie', name=name, value=val, domain=domain, expires=expires, path=path, secure=secure, _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def remove_cookies(self, tab, url, names=None):
        """删除匹配url与names的cookie值;返回值:(bool,msg),msg=''为正常,否则为错误信息"""
        try:
            coks, msg = self.query_cookies(tab, url)  # 先根据url查询匹配的cookies
            if msg:
                return False, msg

            if isinstance(names, str):  # 如果指定了具体的cookie名字串,则将其转换为名字集合
                names = {names}
            elif names is None:  # 如果没有指定具体的cookie名字,则记录全部cookie名字.
                names = {c['name'] for c in coks}

            t = self._tab(tab)
            for c in coks:  # 对全部cookie进行遍历
                name = c['name']
                if name in names:  # 如果名字匹配则进行删除.
                    t.call_method('Network.deleteCookies', name=name, domain=c['domain'], path=c['path'], _timeout=self.proto_timeout)  # 删除时除了名字,还需要指定必要的限定信息
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def modify_cookies(self, tab, url, name, value):
        """修改匹配url与name的cookie值;返回值:(bool,msg),msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            t.call_method('Network.setCookie', name=name, value=value, url=url, _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, py_util.get_trace_stack()

    def query_cookies(self, tab, urls=None):
        """查询指定url对应的cookie.如果urls列表没有指定,则获取当前tab页下的全部cookie信息.返回值:([{cookie}],msg)
            urls可以进行域名路径限定,如'http://xysy.sanya.gov.cn/CreditHnExtranetWeb'
        """

        def remove_key(r, key):
            if key in r:
                del r[key]

        try:
            t = self._tab(tab)
            if isinstance(urls, str):
                urls = [urls]
            if isinstance(urls, list):
                rst = t.call_method('Network.getCookies', urls=urls, _timeout=self.proto_timeout)
            else:
                rst = t.call_method('Network.getCookies', _timeout=self.proto_timeout)
            if rst is None:
                return None, 'Network.getCookies Error.'
            # 丢弃结果中的不关注内容
            ret = rst['cookies']
            for r in ret:
                remove_key(r, 'size')
                remove_key(r, 'httpOnly')
                remove_key(r, 'session')
                remove_key(r, 'priority')
                remove_key(r, 'sameParty')
                remove_key(r, 'sourceScheme')
            return ret, ''
        except Exception as e:
            return None, py_util.get_trace_stack()

    def _tab(self, tab):
        """根据tab标识或序号获取tab对象.返回值:tab对象"""
        if isinstance(tab, int):
            # tab参数为序号的时候,需要进行列表查询并动态获取id
            lst = self.browser.list_tab(self.proto_timeout, False)
            id = lst[tab]['id']
        elif isinstance(tab, Tab):
            return tab
        elif tab is None:
            return None
        else:
            id = tab
        return self.browser._tabs[id]

    def tab(self, tab):
        """根据tab标识或序号获取tab对象.返回值(tab对象,错误消息)"""
        if tab is None:
            return None, 'tab not exists.'
        try:
            return self._tab(tab), ''
        except Exception as e:
            return None, py_util.get_trace_stack()

    def close(self, tab):
        """关闭指定的tab页.tab可以是id也可以是序号.返回值:(tab页id,错误消息)"""
        try:
            t = self._tab(tab)
            self.browser.close_tab(t.id, self.proto_timeout)
            return t.id, ''
        except Exception as e:
            return '', py_util.get_trace_stack()

    def active(self, tab):
        """激活指定的tab页,返回值:(tab页id,错误消息)"""
        try:
            t = self._tab(tab)
            self.browser.activate_tab(t.id, self.proto_timeout)
            return t.id, ''
        except Exception as e:
            return '', py_util.get_trace_stack()

    def stop(self, tab, clean=False):
        """控制指定的tab页停止浏览.返回值:错误消息,空正常"""
        t = self._tab(tab)
        if clean:
            self.clean(t)
        return t.stop(self.proto_timeout)

    def goto(self, tab, url, retry=3):
        """控制指定的tab页浏览指定的url.返回值(是否完成,{'frameId': 主框架id, 'loaderId': 装载器id}, 错误消息)"""
        ok = False  # 是否完成
        r = None  # tab信息
        m = ''  # 返回的消息
        t = self._tab(tab)
        for i in range(retry):
            r, m = t.goto(url, self.proto_timeout)
            if r and 'errorText' not in r:
                ok = True
                break
            time.sleep(1)

        return ok, r, m

    def dhtml(self, tab, body_only=False, frmSel=None):
        """获取指定tab页当前的动态渲染后的html内容(给定iframe选择器时,是获取iframe的内容).返回值(内容串,错误消息)"""
        if frmSel is None:
            rst, msg = self.exec(tab, 'document&&document.documentElement?document.documentElement.outerHTML:""')
        else:
            rst, msg = self.run(tab, """_$_('%s').frm_html()""" % (frmSel))
        if not body_only or msg:
            return rst, msg

        bpos = rst.find('><head></head><body>')
        if bpos != -1:
            bpos = bpos + 20 if bpos != -1 else 0
            return rst[bpos:-14], msg
        return rst, msg

    def dom_document(self, tab):
        """获取当前tab页的DOM根节点"""
        try:
            t = self._tab(tab)
            return t.getDocument(self.proto_timeout), ''
        except Exception as e:
            return '', py_util.get_trace_stack()

    def dom_node(self, tab, sel, parentNodeId=None):
        """使用css选择表达式,或xpath表达式,在父节点id之下,查询对应的节点id"""
        try:
            t = self._tab(tab)
            return t.querySelector(sel, parentNodeId, self.proto_timeout), ''
        except Exception as e:
            return '', py_util.get_trace_stack()

    def dom_dhtml(self, tab, sel, parentNodeId=None):
        """获取dom对象的html文本,但对于iframe无效"""
        nid, err = self.dom_query_node(tab, sel, parentNodeId)
        if err:
            return '', err
        try:
            t = self._tab(tab)
            rst = t.call_method('DOM.getOuterHTML', nodeId=nid, _timeout=self.proto_timeout)
            if rst is None:
                return '', ''
            if 'outerHTML' in rst:
                return rst['outerHTML'], ''
            else:
                return '', rst
        except Exception as e:
            return '', py_util.get_trace_stack()

    def clean(self, tab, retry=1):
        """清空当前tab页的内容,返回值:错误信息.空串正常."""
        txt, msg = self.exec(tab, "document.documentElement.innerHTML='';")
        if msg and retry:
            time.sleep(retry)
            txt, msg = self.exec(tab, "document.documentElement.innerHTML='';")
        return msg

    def exec(self, tab, js):
        """在指定的tab页中运行js代码.返回值(内容串,错误消息)"""
        try:
            t = self._tab(tab)
            return t.exec(js, self.proto_timeout)
        except Exception as e:
            return '', py_util.get_trace_stack()

    def run(self, tab, js):
        '''基于dom100运行js代码'''
        jss = '{%s%s}' % (dom100, js)
        return self.exec(tab, jss)

    def post(self, tab, url, data="", contentType="application/x-www-form-urlencoded", show="root"):
        """在指定的tab页上,利用js的ajax技术,发起post请求.返回值:正常为('','')
           由于浏览器对于跨域请求的限制,所以在执行ajax/post之前,需要先使用goto让页面处于正确的域状态下.
        """
        if isinstance(data, str):
            data = data.replace('\n', '\\n').replace('"', r'\"')
        jss = [http_ajax]
        jss.append('_tmp_ajaxPostData_="%s";' % data)
        jss.append('http_ajax("%s","POST",_tmp_ajaxPostData_,"%s","%s");' % (url, contentType, show))
        return self.exec(tab, '\n'.join(jss))

    def get(self, tab, url, show="root"):
        """在指定的tab页上,利用js的ajax技术,发起get请求.返回值:正常为('','')
           由于浏览器对于跨域请求的限制,所以在执行ajax/get之前,需要先使用goto让页面处于正确的域状态下.
        """
        jss = http_ajax + 'http_ajax("%s","GET","","","%s");' % (url, show)
        return self.exec(tab, jss)

    def wait(self, tab, cond, is_xpath=False, max_sec=60, body_only=False, frmSel=None):
        """在指定的tab页上,等待符合条件的结果出现,最大等待max_sec秒.返回值:(内容串,错误消息)"""
        isnot, cond = parse_cond(cond)

        # 获取tab标识
        t, msg = self.tab(tab)
        if msg != '':
            return None, msg

        wait = spd_base.waited_t(max_sec)
        xhtml = ''
        loops = 0
        msg = 'waiting'
        err = ''
        # 进行循环等待
        while True:
            loops += 1
            if t.id not in self.browser._tabs:
                msg = 'TNE'
                break

            html, msg = self.dhtml(t, body_only, frmSel)
            if msg != '' or html == '':  # html内容导出错误
                if msg:
                    err = f'{t._srctag()} wait ({cond}) take error <{msg}>\n{html[:400]}'
                else:
                    msg = 'waiting'
            else:  # html内容导出完成,需要检查完成条件
                if is_xpath:
                    xhtml = spd_base.format_xhtml(html)  # 执行xpath之前先进行xhtml格式化
                    r, msg = spd_base.query_xpath_x(xhtml, cond)
                else:
                    xhtml = html
                    r, msg = spd_base.query_re(html, cond)
                    if msg:
                        # 针对re条件中包含未转义元字符导致re查询失败的情况,尝试进行退化的串包含匹配
                        r = spd_base.query_str(html, cond)
                        if len(r):
                            msg = ''  # 如果有串包含的结果,也认为匹配成功了.

                if msg != '':
                    err = f'{t._srctag()} wait ({cond}) query error <{msg}>\n{html[:400]}'
                elif check_cond(isnot, r):
                    if self.on_waiting:
                        self.on_waiting(t, html, 0, wait.remain())  # 给出完成通知
                    break  # 如果条件满足,则停止循环
                else:
                    if self.on_waiting and self.on_waiting(t, html, loops, wait.remain()):  # 给出外部回调事件
                        break
                    msg = 'waiting'

            if wait.timeout():
                break
            time.sleep(0.45)
        if msg and err:
            logger.warning(err)
        return xhtml, msg

    def wait_re(self, tab, regexp, max_sec=60, body_only=False, frmSel=None):
        """在指定的tab页上,等待regexp表达式的结果出现,最大等待max_sec秒.返回值:(页面的html内容串,错误消息)"""
        return self.wait(tab, regexp, False, max_sec, body_only, frmSel)

    def wait_xp(self, tab, xpath, max_sec=60, body_only=False, frmSel=None):
        """在指定的tab页上,等待xpath表达式的结果出现,最大等待max_sec秒.返回值:(被xhtml格式化的内容串,错误消息)"""
        return self.wait(tab, xpath, True, max_sec, body_only, frmSel)
