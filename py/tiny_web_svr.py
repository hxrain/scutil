#!/usr/bin/env python

import socket
import select
import re

# Unresolved/HTTPS domain
RSP_404 = (
    b"HTTP/1.1 404 Not Found\r\n"
    b"Content-Length: 0\r\n"
    b"Connection: Close\r\n\r\n"
)

RSP_456 = (
    b"HTTP/1.1 456 PPCEF fail\r\n"
    b"Content-Length: 0\r\n"
    b"Connection: Close\r\n\r\n"
)

RSP_FMT_CHS = (
    b"HTTP/1.1 %d %s\r\n"
    b"Content-Type: %s\r\n"
    b"Content-Length: %d\r\n\r\n"
)


# -----------------------------------------------------------------------------
def make_rsp_chs(code, data, chs, status=b'OK'):
    '用于拼装通用http回应'
    return RSP_FMT_CHS % (code, status, chs, len(data)) + data


# -----------------------------------------------------------------------------
class tiny_tcp_svr_sock:
    '超简单的tcp服务器'

    def __init__(self):
        self.svr_sock = None

    def init(self, port, max_backlog=1):
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

    def take(self, wait_time=0.01):
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


# -----------------------------------------------------------------------------
class tiny_http_svr_sock:
    '便于进行服务端http读写解析的功能类'

    def __init__(self, s):
        self.sock = s

    def _recv(self, wait_time, MAXSIZE=1024 * 8):
        # 等待数据到达
        rlist, wlist, elist = select.select([self.sock], [], [], wait_time)
        if self.sock not in rlist:
            return 0  # 超时了,返回

        try:
            chunk = self.sock.recv(MAXSIZE)
            if not chunk:
                return -1  # 没有数据了,说明对方连接断开了,返回
        except OSError as e:
            return -2  # 出现错误了,返回

        # 得到数据了,累积
        self.data += chunk
        return len(self.data)

    def _parse_head(self, data):
        '解析请求,得到分解后的字典'
        lines = data.decode('ascii').split('\r\n')
        # 解析首行
        m = re.search(r'([A-Z]+) (.*) ', lines[0])
        if m is None:
            return None
        # 得到首行的方法与url
        head = {}
        head['method'] = m.group(1)
        head['url'] = m.group(2)
        # 清除首行后,进行后续行的遍历
        lines.remove(lines[0])
        for l in lines:
            # 将http头内容进行拆分放入字典
            m = re.search(r'\s*(.*?)\s*:\s*(.*)', l)
            if m is not None:
                head[m.group(1).lower()] = m.group(2)
        return head

    def _is_recv_ok(self):
        '判断接收是否完成(头与体都完成)'
        if self.head is None:
            return False
        if self.head['method'] == 'POST':
            # post方法,需要根据头中的内容长度与实际长度判断是否接收完成
            return int(self.head['content-length']) == len(self.data)
        else:
            # 不是post方法,有head就认为接收成功了
            return True

    def recv_req(self, wait_time=60):
        '在给定的时间范围内接收请求,返回值告知是否成功,请求内容可以在head和data中获取'
        self.head = None
        self.data = b""
        wait_one = 0.5
        for i in range(int(wait_time / wait_one) + 1):
            # 进行分时循环接收
            rc = self._recv(wait_one)
            if rc <= 0:  # 对方断开或超时
                # print(rc)
                break

            if self.head is None:
                hb = self.data.find(b'\r\n\r\n')  # 查找http请求的head和body的分隔符
                if hb == -1: continue  # 没有分隔符,继续接收
                self.head = self._parse_head(self.data[0:hb + 2])  # 解析请求头
                if self.head is None:
                    return False  # 头格式错误
                self.data = self.data[hb + 4:]  # 截取body数据

            if self._is_recv_ok():
                return True

        return self._is_recv_ok()

    def send_rsp(self, data):
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


# -----------------------------------------------------------------------------
# 代理服务器回调处理器句柄
class tiny_svr_handler:
    def on_idle(self):
        '返回值告知proxy循环是否停止'
        return False

    def on_req(self, sock, head, body):
        '代理请求处理函数'
        return RSP_404

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

    def do_log(self,out_str):
        print(out_str)


# -----------------------------------------------------------------------------
def tiny_http_svr(port, handler):
    '单线程长连接http代理服务器主体循环功能函数'

    # 生成server对象
    svr = tiny_tcp_svr_sock()
    # 初始化并绑定端口
    if not svr.init(port, 1):
        return

    # 进行收发循环
    loop = 1
    while loop:
        # 获取新连接
        clt_sock = svr.take()
        if clt_sock is None:
            loop = 0 if handler.on_idle() else 1
            continue

        # 构造http服务端会话对象
        session = tiny_http_svr_sock(clt_sock)
        handler.on_log('TinyHttpSvr Accept: ', clt_sock)

        # 对会话进行收发交互,长连接循环多次请求模式
        while session.recv_req():
            handler.on_log('TinyHttpSvr Request: ', session.head)
            # 调用外部函数,进行http请求的处理
            rsp = handler.on_req(clt_sock, session.head, session.data)
            # 发送回应给客户端
            if not session.send_rsp(rsp):
                break  # 发送失败也停止

        handler.on_log('TinyHttpSvr Disconn: ', clt_sock)
        # 当前会话处理完成
        session.close()

    svr.uninit()

def find_chs_by_head(heads,defchs=''):
    '根据http头中的内容类型,分析查找可能存在的字符集类型'
    if 'Content-Type' not in heads:
        return defchs
    CT = heads['Content-Type'].lower()

    m = re.search('charset\s*?[=:]\s*?(.*?)[; "]+', CT)
    if m is not None:
        return m.group(1)

    return defchs

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    handler = tiny_svr_handler()
    tiny_http_svr(8888, handler)
