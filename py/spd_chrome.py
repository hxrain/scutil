import functools
import json
import logging
import os
import time
import requests
import websocket
import base64
import spd_base


# 代码来自 https://github.com/fate0/pychrome 进行了调整.
# chrome.exe --disk-cache-dir=.\tmp --user-data-dir=.\tmp --cache-path=.\tmp --remote-debugging-port=9222 --disable-web-security --disable-features=IsolateOrigins,site-per-process --disable-gpu --disable-software-rasterize

class PyChromeException(Exception):
    pass


class CallMethodException(PyChromeException):
    pass


class RuntimeException(PyChromeException):
    pass


logger = logging.getLogger(__name__)


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


# chrome浏览器Tab页操控功能
class Tab(object):
    def __init__(self, **kwargs):
        """根据chrome的tab对象信息创建tab操纵类,需要browser对象配合获取"""
        self.id = kwargs.get("id")  # tab的唯一id
        self.type = kwargs.get("type")
        self.last_url = kwargs.get("url")
        self.last_title = kwargs.get("title")
        self.last_act = None
        self._websocket_url = kwargs.get("webSocketDebuggerUrl")  # 操纵tab的websocket地址
        self._cur_id = 1000  # 交互消息的初始流水序号

        # 根据环境变量的设定进行功能开关的处理
        self.debug = os.getenv("SPD_CHROME_DEBUG", False)  # 是否显示收发内容
        if os.getenv("SPD_CHROME_REOPEN", False):
            self.cycle = cycle_t(1000 * 60 * 5)  # 是否自动重连websocket
        else:
            self.cycle = None

        self._websocket = None  # websocket功能对象
        self.event_handlers = {}  # 记录tab事件处理器
        self.method_results = {}  # 记录请求对应的回应结果

        self._data_requestWillBeSent = {}  # 记录请求内容,以url为key,value为[请求内容对象]列表
        self.req_event_filter_re = None  # 过滤请求信息使用的url匹配re规则
        self._last_act(False)

    def _last_act(self, using):
        """记录该tab是否处于使用中,便于外部跟踪状态"""
        self.last_act = (using, time.time())

    def _call(self, message, timeout=5):
        """发送tab操纵请求对象.
           返回值:None超时;其他为结果对象"""
        if 'id' not in message:
            self._cur_id += 1
            message['id'] = self._cur_id
        msg_id = message['id']  # 得到本次请求的消息id
        assert (msg_id not in self.method_results)
        msg_json = json.dumps(message)  # 生成本次请求的消息json串
        self.method_results[msg_id] = None  # 提前登记待接收结果对应的消息id

        if self.debug:  # pragma: no cover
            print("SEND > %s" % msg_json)

        try:
            self._websocket.send(msg_json)  # 发送请求
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
        if not self._websocket:
            return (None, None)

        try:
            self._websocket.settimeout(timeout)
            message_json = self._websocket.recv()
            message = json.loads(message_json)  # 接收到json消息后就转换为对象
        except websocket.WebSocketTimeoutException:
            return (0, 0)  # 超时了,什么都没有收到
        except (websocket.WebSocketException, OSError):
            # logger.error("websocket exception", exc_info=True)
            return (None, None)  # websocket错误了
        except Exception as e:
            logger.error("exception", exc_info=True)
            return (None, None)  # 其他错误

        if self.debug:  # pragma: no cover
            print('< RECV %s' % message_json)

        if "method" in message:
            # 接收到事件了,尝试进行处理
            method = message['method']
            if method in self.event_handlers:
                try:
                    self.event_handlers[method](**message['params'])
                except Exception as e:
                    logger.error("callback %s exception %s" % (method, spd_base.es(e)), exc_info=True)
            return (0, 1)
        elif "id" in message:
            # 接收到结果了,记录下来
            msg_id = message["id"]
            if msg_id in self.method_results:
                self.method_results[msg_id] = message
                return (1, 0)

        # logger.warn("unknown message: %s" % message)
        message = None
        return (0, 0)

    def _recv_loop(self, wait_result=False, timeout=1):
        """在指定的时间范围内进行接收处理.可告知是否必须等到结果或超时才结束;
           返回值:(None,None)通信错误;(0,0)超时;其他为(结果数,事件数)"""
        one_timeout = 0.01
        loop = int(timeout // one_timeout)
        for i in range(loop):
            rst = self._recv(one_timeout)  # 尝试进行一次接收处理
            if rst[0] is None:
                break
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
        if not self._websocket:
            return None

        if self.cycle and self.cycle.hit():
            self.reopen()  # 尝试周期性进行ws连接的重连

        # 不允许使用普通参数传递,必须为key/value型参数
        timeout = kwargs.pop("_timeout", None)  # 额外摘取超时控制参数

        result = self._call({"method": _method, "params": kwargs}, timeout=timeout)  # 发起调用请求
        if result is None:
            return None

        if 'result' not in result and 'error' in result:
            logger.warn("%s error: %s" % (_method, result['error']['message']))
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

    def querySelector(self, selector, nodeid=None):
        '''执行选择器,获取对应的节点'''
        if not nodeid:
            nodeid = self.DOM.getDocument()
            nodeid = nodeid["root"]["nodeId"]
        res = self.DOM.querySelector(nodeId=nodeid, selector=selector)
        return res["nodeId"] if res["nodeId"] > 0 else None

    def querySelectorAll(self, selector, nodeid=None):
        '''执行选择器,获取对应的全部节点'''
        if not nodeid:
            nodeid = self.DOM.getDocument()
            nodeid = nodeid["root"]["nodeId"]
        res = self.DOM.querySelectorAll(nodeId=nodeid, selector=selector)
        return res["nodeIds"]

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

    def recv_loop(self, loops=50):
        for i in range(loops):
            rc, mc = self._recv_loop(timeout=0.2)
            if rc is None:
                break
            if rc + mc == 0:
                break

    def get_requests(self, url=None):
        """获取已经发送的请求信息;如果给定了明确的url,则返回该url对应的最新请求列表;否则返回全部记录的请求字典."""
        self.recv_loop()
        if url:
            if url in self._data_requestWillBeSent:
                return self._data_requestWillBeSent[url]
            else:
                return None
        else:
            return self._data_requestWillBeSent

    def clear_requests(self):
        """清理全部记录的请求信息"""
        self._data_requestWillBeSent.clear()

    def get_request_urls(self, hold_url=None):
        """获取记录过的请求信息的url列表"""
        self.recv_loop()
        if hold_url is None:  # 没有明确告知拦截url的模式,则返回全部记录的请求url
            return list(self._data_requestWillBeSent.keys())

        rst = []
        for url in self._data_requestWillBeSent.keys():
            if spd_base.query_re_str(url, hold_url):  # 否则记录匹配的请求url
                rst.append(url)
        return rst

    def init(self, req_event_filter=None):
        """启动tab交互象,建立websocket连接"""
        if self._websocket:
            return True

        self.req_event_filter_re = req_event_filter
        self._websocket = websocket.create_connection(self._websocket_url, enable_multithread=True)
        self.set_listener('Network.requestWillBeSent', self._on_requestWillBeSent)
        self.call_method('Network.enable', _timeout=1)
        return True

    def reopen(self):
        """与tab的websocket连接进行重连处理"""
        if self._websocket:
            self._websocket.close()
            self._websocket = None

        self._websocket = websocket.create_connection(self._websocket_url, enable_multithread=True)
        self.set_listener('Network.requestWillBeSent', self._on_requestWillBeSent)
        self.call_method('Network.enable', _timeout=1)

    def close(self):
        """停止tab交互,关闭websocket连接"""
        if self._websocket:
            self._websocket.close()
            self._websocket = None
        self._data_requestWillBeSent.clear()
        return True


# Chrome浏览器管理对象
class Browser(object):

    def __init__(self, url="http://127.0.0.1:9222"):
        self.dev_url = url
        self._tabs = {}  # 记录被管理的tab页

    def new_tab(self, url=None, timeout=None, start=True, req_event_filter=None):
        """打开新tab页,并浏览指定的网址"""
        url = url or ''
        rp = requests.get("%s/json/new?%s" % (self.dev_url, url), json=True, timeout=timeout)
        tab = Tab(**rp.json())
        self._tabs[tab.id] = tab
        if start:
            tab.init(req_event_filter)
        return tab

    def list_tab(self, timeout=None, backinit=True, req_event_filter=None):
        """列出浏览器所有打开的tab页,可控制是否反向补全外部打开的tab进行操控"""
        rp = requests.get("%s/json" % self.dev_url, json=True, timeout=timeout)
        tabs_map = {}
        _tabs_list = []

        for tab_json in rp.json():
            if tab_json['type'] != 'page':  # pragma: no cover
                continue  # 只保留page页面tab,其他后台进程不记录

            id = tab_json['id']
            tinfo = {'id': id, 'title': tab_json['title'], 'url': tab_json['url']}
            _tabs_list.append(tinfo)
            if id in self._tabs:
                tabs_map[id] = self._tabs[id]
            else:
                tabs_map[id] = Tab(**tab_json)
                if backinit:
                    tabs_map[id].init(req_event_filter)

            tabs_map[id].last_url = tinfo['url']
            tabs_map[id].last_title = tinfo['title']

        self._tabs = tabs_map
        return _tabs_list

    def activate_tab(self, tab_id, timeout=None):
        """激活指定的tab页"""
        if isinstance(tab_id, Tab):
            tab_id = tab_id.id

        rp = requests.get("%s/json/activate/%s" % (self.dev_url, tab_id), timeout=timeout)
        return rp.text

    def close_tab(self, tab_id, timeout=None):
        """关闭指定的tab页"""
        if isinstance(tab_id, Tab):
            tab_id = tab_id.id

        rp = requests.get("%s/json/close/%s" % (self.dev_url, tab_id), timeout=timeout)

        tab = self._tabs.pop(tab_id, None)
        tab.close()
        tab = None

        return rp.text

    def version(self, timeout=None):
        """查询浏览器的版本信息"""
        rp = requests.get("%s/json/version" % self.dev_url, json=True, timeout=timeout)
        return rp.json()


dom100 = '''
//DOM选取功能封装:el为选择表达式或已选取的对象;parent为选取的父节点范围作用域,也可以为父节点的选取表达式
var _$_ = function(el, parent) {
	//最终返回的API对象,初始的时候其持有的el元素对象为null
	var api = { el: null }
	//内部使用的CSS选择器单节点查询函数
	var qs = function(selector, parent) {
		parent = parent || document;
		return parent.querySelector(selector);
	};
	//内部使用的CSS选择器多节点查询函数
	var qsa = function(selector, parent) {
		parent = parent || document;
		return parent.querySelectorAll(selector);
	};
	//内部使用的xpath多节点查询函数
	var qx=function(xpath,parent) {
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
		return set ? api : null;	//最终的返回值,对于赋值动作可以链式继续处理;取值动作应该在上面处理了,这里就返回未处理的null
	}
	//对外提供的触发事件功能,默认为点击事件,0ms延迟后异步执行
	api.hit=function (evtType,delayMs,key){//evtType:"click/dbclick/mouseenter/mouseleave/blur/focus"
		evtType = evtType||"click";
		delayMs = delayMs || 0;
		el=this.el;
		setTimeout(function(){
			var myEvent = document.createEvent('Events') //创建事件对象
			myEvent.initEvent(evtType, true, true);//初始化事件类型
			if (key)
			    myEvent.keyCode=key;
			el.dispatchEvent(myEvent);	//触发事件
		},delayMs);
	}
	//查询获取iframe节点
	api.frm=function(){
		if (this.el==null || this.el.nodeName!='IFRAME')
			return null;
		return this.el.contentWindow;
	}
	//获取iframe的整体内容.
	api.frm_html=function(){
	    cw=api.frm()
	    if (cw!=null)
	        return cw.document.documentElement.outerHTML;
	    return "";
	}

	//根据输入的选择表达式的类型进行选取操作
	switch(typeof el) {
		case 'string':
			//选取表达式为串,先处理得到正确的父节点
			parent = parent && typeof parent === 'string' ? qs(parent) : parent;
			if (el.charAt(0)=='/'||(el.charAt(0)=='.'&&el.charAt(1)=='/')) api.el = qx(el, parent);
			else api.el = qs(el, parent);
			break;
		case 'object':
			//选取表达式为对象,如果对象是一个原生的DOM节点,则直接记录下来
			if(typeof el.nodeName != 'undefined') api.el = el;
			break;
	}

	return api; //对于选取操作,返回的就是封装后的对象
}
'''

# 用来进行ajax调用的功能函数
http_ajax = """
function http_ajax(url,method="GET",data=null,contentType="application/x-www-form-urlencoded")
{
    document.documentElement.innerHTML="";
	var xmlhttp=new XMLHttpRequest();
	xmlhttp.onreadystatechange=function()
	{
		if (xmlhttp.readyState==4){
		    document.documentElement.innerHTML=xmlhttp.responseText;
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


def parse_cond(xpath):
    """解析判断表达式,如果是以!!开头,则意味着是反向判断"""
    if xpath.startswith('!!'):
        return True, xpath[2:]
    return False, xpath


def check_cond(isnot, rst):
    """判断条件的结果,根据是否反向逻辑决定结果是否完成.返回值:是否完成"""
    if isnot:
        return len(rst) == 0
    else:
        return len(rst) > 0


# 定义常见爬虫功能类
class spd_chrome:
    def __init__(self, proto_url="http://127.0.0.1:9222"):
        self.browser = Browser(proto_url)
        self.proto_timeout = 10

    def open(self, url='', req_event_filter=None):
        """打开tab页,并浏览指定的url;返回值:(tab页标识id,错误消息)"""
        try:
            tab = self.browser.new_tab(url, self.proto_timeout, req_event_filter=req_event_filter)
            return tab.id, ''
        except Exception as e:
            return '', spd_base.es(e)

    def new(self, url='', req_event_filter=None):
        """打开tab页,并浏览指定的url;返回值:(tab页对象,错误消息)"""
        try:
            tab = self.browser.new_tab(url, self.proto_timeout, req_event_filter=req_event_filter)
            return tab, ''
        except Exception as e:
            return None, spd_base.es(e)

    def list(self, backinit=True):
        """列出现有打开的tab页,backinit可告知是否反向补全外部打开的tab进行操控;返回值:([{tab}],错误消息)
            按最后的活动顺序排列,元素0总是当前激活的tab页
        """
        try:
            rst = self.browser.list_tab(self.proto_timeout, backinit)
            return rst, ''
        except Exception as e:
            return '', spd_base.es(e)

    def get_request_urls(self, tab, hold_url=None):
        """获取指定tab记录的请求信息,与hold_url匹配的url列表,或全部url列表;返回值:([urls],msg)"""
        try:
            t = self._tab(tab)
            return t.get_request_urls(hold_url), ''
        except Exception as e:
            return None, spd_base.es(e)

    def wait_request_urls(self, tab, hold_url, timeout=60):
        """尝试等待请求信息中出现指定的url"""
        loop = timeout * 2
        try:
            t = self._tab(tab)
            wait = spd_base.waited_t(timeout)
            for i in range(loop):
                dst = t.get_request_urls(hold_url)
                if len(dst):
                    return dst, ''
                if wait.timeout():
                    break
                time.sleep(0.45)
            return [], ''
        except Exception as e:
            return None, spd_base.es(e)

    def get_request_info(self, tab, url):
        """获取指定url的请求信息
            工作流程:1 打开tab页的时候,就需要告知url的匹配模式;2 等待页面装载完成,内部记录发送的请求信息; 3根据url查找发送的请求内容.
            返回值: [(request,requestId)],msg
                    msg为''则正常;request为请求内容;requestId为请求ID,可据此获取更多数据.
        """
        try:
            t = self._tab(tab)
            return t.get_requests(url), ''
        except Exception as e:
            return None, spd_base.es(e)

    def clear_request(self, tab, url=None):
        """清空记录的请求内容"""
        try:
            req_lst, msg = self.get_request(tab, url)
            if msg:
                return msg
            if len(req_lst) == 0:
                return ''
            req_lst.clear()
            return ''
        except Exception as e:
            return spd_base.es(e)

    def get_response_body(self, tab, url):
        """获取指定url的回应内容
            工作流程:1 打开tab页的时候,就需要告知url的匹配模式;2 等待页面装载完成,内部记录发送的请求信息; 3根据url查找发送的请求id; 4 使用请求id获取对应的回应内容.
            返回值: (body,msg)
                    msg为''则正常;body为回应内容
        """
        try:
            req_lst, msg = self.get_request_info(tab, url)
            if msg:
                return None, msg
            if req_lst is None or len(req_lst) == 0:
                return None, ''

            req, reqid = req_lst[-1]

            t = self._tab(tab)
            rst = t.call_method('Network.getResponseBody', requestId=reqid, _timeout=self.proto_timeout)
            body = rst['body']
            en = rst['base64Encoded']
            if en:
                body = base64.decodebytes(body.encode('latin-1'))
            return body, ''
        except Exception as e:
            return None, spd_base.es(e)

    def clear_cookies(self, tab):
        """删除浏览器全部的cookie值;
            返回值: (bool,msg)
                    msg=''为正常,否则为错误信息"""
        try:
            t = self._tab(tab)
            rst = t.call_method('Network.clearBrowserCookies', _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, spd_base.es(e)

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
            return False, spd_base.es(e)

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
            return False, spd_base.es(e)

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
            return None, spd_base.es(e)

    def _tab(self, tab):
        """根据tab标识或序号获取tab对象.返回值:tab对象"""
        if isinstance(tab, int):
            # tab参数为序号的时候,需要进行列表查询并动态获取id
            lst = self.browser.list_tab(self.proto_timeout)
            id = lst[tab]['id']
        elif isinstance(tab, Tab):
            return tab
        else:
            id = tab
        return self.browser._tabs[id]

    def tab(self, tab):
        """根据tab标识或序号获取tab对象.返回值(tab对象,错误消息)"""
        try:
            return self._tab(tab), ''
        except Exception as e:
            return None, spd_base.es(e)

    def close(self, tab):
        """关闭指定的tab页.tab可以是id也可以是序号.返回值:(tab页id,错误消息)"""
        try:
            t = self._tab(tab)
            self.browser.close_tab(t.id, self.proto_timeout)
            return t.id, ''
        except Exception as e:
            return '', spd_base.es(e)

    def active(self, tab):
        """激活指定的tab页,返回值:(tab页id,错误消息)"""
        try:
            t = self._tab(tab)
            self.browser.activate_tab(t.id, self.proto_timeout)
            return t.id, ''
        except Exception as e:
            return '', spd_base.es(e)

    def _goto(self, tab, url):
        """控制指定的tab页浏览指定的url.返回值({'frameId': 主框架id, 'loaderId': 装载器id}, 错误消息)"""
        try:
            t = self._tab(tab)
            t.clear_requests()  # 每次发起新导航的时候,都清空之前记录的请求信息
            rst = t.call_method('Page.navigate', url=url, _timeout=self.proto_timeout)
            return rst, ''
        except Exception as e:
            return None, spd_base.es(e)

    def goto(self, tab, url, retry=3):
        """控制指定的tab页浏览指定的url.返回值(是否完成,{'frameId': 主框架id, 'loaderId': 装载器id}, 错误消息)"""
        ok = False  # 是否完成
        r = None  # tab信息
        m = ''  # 返回的消息
        for i in range(retry):
            r, m = self._goto(tab, url)
            if r and 'errorText' not in r:
                ok = True
                break
            time.sleep(1)

        return ok, r, m

    def dhtml_clear(self, tab):
        """清空指定tab页当前的动态渲染后的html内容.返回值:错误消息,空为正常."""
        rst, msg = self.exec(tab, "document.documentElement.innerHTML='';")
        return msg

    def dhtml(self, tab, body_only=False, frmSel=None):
        """获取指定tab页当前的动态渲染后的html内容(给定iframe选择器时,是获取iframe的内容).返回值(内容串,错误消息)"""
        if frmSel is None:
            rst, msg = self.exec(tab, 'document.documentElement.outerHTML')
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
            rst = t.call_method('DOM.getDocument', _timeout=self.proto_timeout)
            if rst is None:
                return '', ''
            if 'root' in rst:
                return rst['root'], ''
            else:
                return '', ret
        except Exception as e:
            return '', spd_base.es(e)

    def dom_node(self, tab, sel, parentNodeId=1):
        """使用css选择表达式,或xpath表达式,在父节点id之下,查询对应的节点id"""
        try:
            t = self._tab(tab)
            rst = t.call_method('DOM.querySelector', nodeId=parentNodeId, selector=sel, _timeout=self.proto_timeout)
            if rst is None:
                return '', ''
            if 'nodeId' in rst:
                return rst['nodeId'], ''
            else:
                return '', ret
        except Exception as e:
            return '', spd_base.es(e)

    def dom_dhtml(self, tab, sel, parentNodeId=1):
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
                return '', ret
        except Exception as e:
            return '', spd_base.es(e)

    def exec(self, tab, js):
        """在指定的tab页中运行js代码.返回值(内容串,错误消息)"""
        try:
            t = self._tab(tab)
            rst = t.call_method('Runtime.evaluate', expression=js, returnByValue=True, _timeout=self.proto_timeout)
            if rst is None:
                return '', ''
            ret = rst['result']
            if 'value' in ret:
                return ret['value'], ''
            elif 'description' in ret:
                return '', ret['description']
            elif 'type' in ret and ret['type'] == 'undefined':
                return '', ''
            else:
                return '', ret
        except Exception as e:
            return '', spd_base.es(e)

    def run(self, tab, js):
        '''基于dom100运行js代码'''
        jss = '{%s%s}' % (dom100, js)
        return self.exec(tab, jss)

    def post(self, tab, url, data="", contentType="application/x-www-form-urlencoded"):
        """在指定的tab页上,利用js的ajax技术,发起post请求.返回值:正常为('','')
           由于浏览器对于跨域请求的限制,所以在执行ajax/post之前,需要先使用goto让页面处于正确的域状态下.
        """
        if isinstance(data, str):
            data = data.replace('\n', '\\n')
        jss = http_ajax + 'http_ajax("%s","POST","%s","%s");' % (url, data, contentType)
        return self.exec(tab, jss)

    def get(self, tab, url):
        """在指定的tab页上,利用js的ajax技术,发起get请求.返回值:正常为('','')
           由于浏览器对于跨域请求的限制,所以在执行ajax/get之前,需要先使用goto让页面处于正确的域状态下.
        """
        jss = http_ajax + 'http_ajax("%s","GET","","");' % (url)
        return self.exec(tab, jss)

    def sendkey(self, tab, keyCode=0x0D, eventType='keyDown'):
        """给指定的tab页发送键盘事件.返回值(True,错误消息).事件代码参考
            https://msdn.microsoft.com/en-us/library/dd375731(VS.85).aspx
            https://docs.microsoft.com/zh-cn/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
        """
        try:
            t = self._tab(tab)
            t.call_method('Input.dispatchKeyEvent', type=eventType, windowsVirtualKeyCode=keyCode, nativeVirtualKeyCode=keyCode,
                          _timeout=self.proto_timeout)
            return True, ''
        except Exception as e:
            return False, spd_base.es(e)

    def wait_xp(self, tab, xpath, max_sec=60, body_only=False, frmSel=None):
        """在指定的tab页上,等待xpath表达式的结果出现,最大等待max_sec秒.返回值:(被xhtml格式化的内容串,错误消息)"""
        loops = max_sec * 2 if max_sec > 0 else 1  # 间隔0.5秒进行循环判定
        xhtml = ''

        isnot, xpath = parse_cond(xpath)

        # 获取tab标识
        t, msg = self.tab(tab)
        if msg != '':
            return None, msg

        wait = spd_base.waited_t(max_sec)
        # 进行循环等待
        for i in range(loops):
            html, msg = self.dhtml(t, body_only, frmSel)
            if msg != '':
                if wait.timeout():
                    break
                time.sleep(0.45)
                continue

            xhtml = spd_base.format_xhtml(html)  # 执行xpath之前先进行xhtml格式化
            r, msg = spd_base.query_xpath_x(xhtml, xpath)
            if msg != '':
                return None, msg
            if check_cond(isnot, r):
                break  # 如果条件满足,则停止循环
            if wait.timeout():
                break
            time.sleep(0.45)
            msg = 'waiting'
        return xhtml, msg

    def wait_re(self, tab, regexp, max_sec=60, body_only=False, frmSel=None):
        """在指定的tab页上,等待regexp表达式的结果出现,最大等待max_sec秒.返回值:(页面的html内容串,错误消息)"""
        loops = max_sec * 2 if max_sec > 0 else 1  # 间隔0.5秒进行循环判定
        html = ''
        isnot, regexp = parse_cond(regexp)

        # 获取tab标识
        t, msg = self.tab(tab)
        if msg != '':
            return None, msg

        wait = spd_base.waited_t(max_sec)
        # 进行循环等待
        for i in range(loops):
            html, msg = self.dhtml(t, body_only, frmSel)
            if msg != '':
                if wait.timeout():
                    break
                time.sleep(0.45)
                continue

            r, msg = spd_base.query_re(html, regexp)
            if msg != '':
                return None, msg
            if check_cond(isnot, r):
                break  # 如果条件满足,则停止循环
            if wait.timeout():
                break
            time.sleep(0.45)
            msg = 'waiting'
        return html, msg


class tiny_chrome:
    """简单使用的chrome客户端"""

    def __init__(self, cond='html', tab=None, proto_url="http://127.0.0.1:9222"):
        self.sc = spd_chrome(proto_url)
        self.tab = tab if tab else self.sc.new()[0]
        self.chrome_timeout = 600
        self.cond(cond)
        self.resp_body_only = False  # 渲染结果是否仅保留body内容(json回应时有意义)

    def cond(self, cond, cond_is_re=True):
        """设置完成条件"""
        self.cond = cond
        self.cond_is_re = cond_is_re

    def wait(self, max_sec=None):
        """阻塞等待页面渲染,完成条件是cond正则表达式/xpath表达式匹配到了结果;返回值:是否成功,页面内容,状态码,错误信息"""
        if max_sec is None:
            max_sec = self.chrome_timeout

        if self.cond_is_re:
            rsp, msg = self.sc.wait_re(self.tab, self.cond, max_sec, self.resp_body_only)  # 等待页面装载完成
        else:
            rsp, msg = self.sc.wait_xp(self.tab, self.cond, max_sec, self.resp_body_only)  # 等待页面装载完成

        if msg != '':
            return False, '', 999, msg
        else:
            return True, rsp, 200, ''

    def exec(self, js):
        """运行js代码.返回值(运行结果,错误消息)"""
        return self.sc.run(self.tab, js)

    def take(self, url, max_sec=None):
        """导航并抓取指定的url页面,完成条件是cond_re;返回值:是否成功,页面内容,状态码,错误信息"""
        r = self.sc.goto(self.tab, url)  # 控制浏览器访问入口url
        if not r[0]:
            return False, '', 998, 'chrome open fail.'
        return self.wait(max_sec)

    def post(self, url, data, max_sec=None):
        """使用chrome控制器,发起ajax/post请求url页面,完成条件是cond_re"""
        r = self.sc.post(self.tab, url, data)  # 控制浏览器访问入口url
        if r[1]:
            return False, '', 997, r[1]
        return self.wait(max_sec)

    def get(self, url, max_sec=None):
        """使用chrome控制器,发起ajax/get请求url页面,完成条件是cond_re"""
        r = self.sc.get(self.tab, url)  # 控制浏览器访问入口url
        if r[1]:
            return False, '', 996, r[1]
        return self.wait(max_sec)
