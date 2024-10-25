# -*- coding: utf-8 -*-

import base64
import re
import select
import socket
import time

from mutex_lock import *

"""
    这里实现一个简单的多线程代理转发功能核心,用于进行代理的代理转发.
"""


class tiny_tcp_svr_sock:
    '超简单的tcp服务器sock'

    def __init__(self):
        self.svr_sock = None

    def init(self, port, max_backlog=200):
        '对服务器进行初始化,绑定监听端口,设置并发数量'
        if self.svr_sock is not None:
            return False
        try:
            self.svr_sock = socket.socket()
            self.svr_sock.bind(('', port))
            self.svr_sock.listen(max_backlog)
        except OSError as e:
            print(e)
            return False

        return True

    def take(self, wait_time=0.1):
        '服务器进行周期性调取,尝试获取可用客户端连接'
        rlist, wlist, elist = select.select([self.svr_sock], [], [], wait_time)
        if self.svr_sock not in rlist:
            return None  # 超时了,没有连接到达
        clt_sock, addr = self.svr_sock.accept()  # 获取新的客户端连接
        return clt_sock

    def uninit(self):
        if self.svr_sock is None:
            return False
        self.svr_sock.close()


def parse_http_head(data, is_req=True):
    '解析请求,得到分解后的字典'
    lines = data.decode('ascii').split('\r\n')
    if is_req:
        # 解析首行
        m = re.search(r'([A-Z]+) (.+) HTTP/', lines[0])
        if m is None:
            return None
        # 得到首行的方法与url路径
        head = {}
        head['method'] = m.group(1)
        head['url'] = m.group(2)
    else:
        # 解析首行
        m = re.search(r'HTTP/\d\.\d (\d{3}) (.*$)', lines[0])
        if m is None:
            return None
        # 得到首行的方法与url路径
        head = {}
        head['status'] = int(m.group(1))
        head['reason'] = m.group(2)

    # 清除首行后,进行后续行的遍历
    lines.remove(lines[0])
    for l in lines:
        # 将http头内容进行拆分放入字典
        if l == '':
            break

        m = re.search(r'\s*(.*?)\s*:\s*(.*)', l)
        if m is not None:
            head[m.group(1)] = m.group(2)
    return head


def make_tcp_conn(host, port, time_out=5):
    """生成socket,并连接指定的目标主机端口"""
    s = None
    try:
        s = socket.socket()
        s.settimeout(time_out)
        s.connect((host, int(port)))
        s.settimeout(None)
        return s
    except Exception as e:
        if s:
            s.close()
            s = None
        return None


def make_http_head(old_head, pauth, method=None):
    """基于原有的请求头,构造新的请求头"""
    if not method:
        method = old_head['method']

    rst = []
    rst.append('%s %s HTTP/1.1' % (method, old_head.get('url')))
    if pauth:
        rst.append('Proxy-Authorization: %s' % pauth)

    for k in old_head:  # 复制旧头,但需要排除几个字段
        if k in {'url', 'method', 'Proxy-Authorization'}:
            continue
        rst.append('%s: %s' % (k, old_head[k]))

    return '\r\n'.join(rst) + '\r\n\r\n'


# -----------------------------------------------------------------------------
class tiny_proxy_sock:
    '便于进行服务端proxy读写解析的功能类'

    def __init__(self, s):
        self.sock = s
        self.data = b""
        self.head = None

    def read_data(self, wait_time=10, MAXSIZE=1024 * 8):
        # 等待数据到达
        rlist, wlist, elist = select.select([self.sock], [], [], wait_time)
        if self.sock not in rlist:
            return None, 0  # 超时了,返回

        try:
            chunk = self.sock.recv(MAXSIZE)
            if not chunk:
                return None, -1  # 没有数据了,说明对方连接断开了,返回
        except OSError as e:
            return None, -2  # 出现错误了,返回

        return chunk, len(chunk)

    def is_CONNECT(self):
        '判断接收的是否为CONNECT方法'
        return self.head.get('method') == 'CONNECT'

    def get_TARGET(self):
        """获取本次请求要连接的目标"""
        if self.is_CONNECT():
            return self.head.get('url')
        else:
            return self.head.get('Host')

    def wait_head(self, wait_time=120, wait_one=5, is_req=True):
        '在给定的时间范围内接收请求,返回值告知是否成功,请求内容可以在head和data中获取'
        self.head = None
        self.data = b""
        self.raw = b''
        self.rawrc = 0

        for i in range(int(wait_time / wait_one) + 1):
            # 进行分时循环接收
            self.raw, self.rawrc = self.read_data(wait_one)
            if self.rawrc < 0:  # 连接断开或接收错误
                break
            if self.rawrc == 0:
                continue

            self.data += self.raw  # 所有接收过的数据,都先放在这里,等待可能的转发使用

            if self.head is None:
                hb = self.data.find(b'\r\n\r\n')  # 查找http请求的head和body的分隔符
                if hb == -1: continue  # 没有分隔符,继续接收
                self.head = parse_http_head(self.data[0:hb + 2], is_req)  # 解析请求头
                if self.head is None:
                    return False  # 头格式错误
                # 需要截取保存body数据
                hb += 4
                self.data = self.data[hb:] if len(self.raw) > hb else None
                break
        return self.head is not None

    def send_data(self, data):
        '发送回应,返回值告知是否成功'
        try:
            self.sock.sendall(data)
        except OSError as e:
            print(e)
            return False
        return True

    def close(self):
        if self.sock is None:
            return
        self.sock.close()
        self.sock = None
        self.data = None


def get_sock_addr(sock, islocal=False):
    if islocal:
        sa = sock.getsockname()
    else:
        sa = sock.getpeername()
    return sa


def get_sock_info(sock):
    """获取sock对应的本端和对端地址信息"""
    p = sock.getpeername()
    l = sock.getsockname()
    return '<laddr=(%s:%d)raddr=(%s:%d)>' % (l[0], l[1], p[0], p[1])


class tiny_proxy_session:
    '便于进行服务端proxy会话操作的功能类'

    def __init__(self, src_sock, log_out, enable_log=False):
        self.src_sock = tiny_proxy_sock(src_sock)
        self.dst_sock = None
        self.proxy_info = None
        self._log_out = log_out
        self._enable_log_ = enable_log

    def proxy(self):
        return '<proxy=(%s:%d)>' % (self.proxy_info[0], self.proxy_info[1]) if self.proxy_info else ''

    def warn(self, *args):
        if self._log_out:
            self._log_out('WARN:', get_sock_info(self.src_sock.sock), self.proxy(), *args)

    def log(self, *args):
        if self._log_out and self._enable_log_:
            self._log_out('INFO:', get_sock_info(self.src_sock.sock), self.proxy(), *args)


# CONNECT method response OK.
RSP_CONNOK = (
    b"HTTP/1.0 200 Connection established\r\n"
    b"Content-Length: 0\r\n\r\n"
)


class tick_meter:
    '毫秒间隔计时器'

    def __init__(self, interval_ms, first_hit=True):
        self.last_time = 0 if first_hit else int(time.time() * 1000)
        self.interval = interval_ms

    def hit(self):
        '判断当前时间是否超过了最后触发时间一定的间隔'
        cur_time = int(time.time() * 1000)
        if cur_time - self.last_time > self.interval:
            self.last_time = cur_time
            return True
        return False


# 代理服务器回调处理器句柄
class tiny_proxy_handler:
    def __init__(self):
        self.meter_idle = tick_meter(5 * 1000, False)
        pass

    def on_idle(self):
        '通知内部目前处于空闲状态,返回值告知proxy循环是否停止'
        return False

    def on_error(self, type, data):
        '通知内部发生的错误'
        pass

    def on_get_dst(self, session):
        """根据session中的信息,查找对应的目标代理地址"""
        return ('127.0.0.1', 8899, 'usr', 'pwd')

    def on_log(self, *args):
        out_list = []
        for a in args:
            if type(a).__name__ == 'str':
                out_list.append(a)
            elif hasattr(a, '__str__'):
                out_list.append(str(a))
            else:
                out_list.append(a.__class__)
        out_str = ''.join(out_list)
        self.do_log(out_str)

    def do_log(self, out_str):
        print(out_str)


# -----------------------------------------------------------------------------
def tiny_proxy_svr(port, handler, maxconn=200):
    'http代理服务器主体循环功能函数'

    # -----------------------------------------------------
    def on_req(session, handler):
        '代理请求处理入口,在多线程中被运行'
        try:
            if not _do_req(session, handler):
                session.warn('TinyProxyFor Fail.')
        except Exception as e:
            print(e)
            pass
        session.src_sock.close()
        if session.dst_sock:
            session.dst_sock.close()

    def _do_req(session, handler):
        '真正的代理请求处理函数,在多线程中被运行'
        if not session.src_sock.wait_head():
            session.warn('recv src head fail')
            return False

        # 根据当前请求的会话信息,获取目标代理地址
        session.proxy_info = handler.on_get_dst(session)

        # 连接目标代理地址
        dst_sck = make_tcp_conn(session.proxy_info[0], session.proxy_info[1])
        if dst_sck is None:
            session.warn('conn DST<%s:%d> proxy timeout.' % (session.proxy_info[0], session.proxy_info[1]))
            handler.on_error('cto', (session.proxy_info[0], session.proxy_info[1]))  # 通知外部,连接超时
            return False

        # 初始化目标连接会话
        session.dst_sock = tiny_proxy_sock(dst_sck)

        # 生成目标代理需要的认证信息
        if session.proxy_info[2]:
            pauth = base64.b64encode(('%s:%s' % (session.proxy_info[2], session.proxy_info[3])).encode('utf-8'))
        else:
            pauth = None

        if session.src_sock.is_CONNECT():
            # 明确给出CONNECT方法了,需要对目标代理也发起连接请求
            head = make_http_head(session.src_sock.head, pauth, 'CONNECT')
            if not session.dst_sock.send_data(head.encode('ascii')):
                session.warn('send head CONNECT error.')
                return False

            # 等待目标端回应
            if not session.dst_sock.wait_head(is_req=False) or session.dst_sock.head.get('status') != 200:
                session.warn('recv resp CONNECT error.')
                return False

            # 给源端应答
            if not session.src_sock.send_data(RSP_CONNOK):
                session.warn('send resp CONNECT error.')
                return False
        else:
            # 初始的就是普通请求,重构http请求头后转发
            head = make_http_head(session.src_sock.head, pauth)
            if not session.dst_sock.send_data(head.encode('ascii')):
                session.warn('send head init error.')
                return False

            if session.src_sock.data and not session.dst_sock.send_data(session.src_sock.data):
                session.warn('send data init error.')
                return False

        # 进入完整的交互循环过程,两个链接任意连接中断就算结束.
        while True:
            # 尝试读取目标端数据
            data, rc1 = session.dst_sock.read_data(0)
            if rc1 < 0:
                break

            # 目标端数据转发给源端
            if rc1 > 0:
                if not session.src_sock.send_data(data):
                    session.warn('send dst data to src error.')
                    return False

            # 尝试读取源端数据
            data, rc2 = session.src_sock.read_data(0)
            if rc2 < 0:
                break

            # 源端数据转发给目标端
            if rc2 > 0:
                if not session.dst_sock.send_data(data):
                    session.warn('send src data to dst error.')
                    return False

            if rc1 + rc2 == 0:
                time.sleep(0.001)

        session.log(' End.')
        return True

    # -----------------------------------------------------
    # 先进行一次空闲事件处理,更新初始的目标代理列表
    handler.on_idle()
    # 生成server对象
    svr = tiny_tcp_svr_sock()
    # 初始化并绑定端口
    if not svr.init(port, maxconn):
        return

    # 进行收发循环
    loop = 1
    while loop:
        # 获取新连接
        clt_sock = svr.take()
        if clt_sock is None:
            if handler.meter_idle.hit():
                loop = 0 if handler.on_idle() else 1  # 如果外部事件要求停止,则循环结束
            continue

        # 构造proxy服务端会话对象
        session = tiny_proxy_session(clt_sock, handler.on_log)
        session.log(' Begin.')

        # 调用回调函数,进行proxy请求的处理,启动新的连接处理过程
        start_thread(on_req, session, handler)

    svr.uninit()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    handler = tiny_proxy_handler()
    print('TinyProxyFor Start.')
    tiny_proxy_svr(7878, handler)
