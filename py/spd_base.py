# -*- coding: utf-8 -*-

import datetime
import html as hp
import http.cookiejar as cookiejar
import json
import hashlib
import logging
import logging.handlers
import os
import re
import time
import base64
import requests
import socket
import urllib.parse as up
from util_xml import *
from hash_calc import *
from util_base import *

# 调整requests模块的默认日志级别,避免无用调试信息的输出
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def enable_cros(req, rsp):
    """尝试根据req中的cros请求开启rsp中的cros回应"""
    Origin = req.headers.get('Origin', '*')
    rsp.headers['Access-Control-Allow-Origin'] = Origin
    rsp.headers['Access-Control-Allow-Credentials'] = 'true'


# 挑选出指定串中的unicode转义序列，并转换为标准串
def uniseq2str(s):
    m = re.findall(r'(\\u[0-9a-fA-F]{4})', s)
    ms = set(m)
    for i in ms:
        c = i.encode('latin-1').decode('unicode_escape')
        s = s.replace(i, c)
    return s


# 对指定的内容进行URLData编码转换
def URLData(content, type='text/html'):
    if isinstance(content, str):
        content = content.encode('utf-8')
    encoded_body = base64.b64encode(content)
    return "data:%s;base64,%s" % (type, encoded_body.decode())


# -----------------------------------------------------------------------------
# URL编码
def encodeURIComponent(url, encode='utf-8'):
    url = hp.unescape(url)
    url = up.quote_plus(url, safe='', encoding=encode)
    return url


# URI解码
def decodeURIComponent(url):
    url = up.unquote_plus(url)
    url = uniseq2str(url)
    return url


# 基于url_base补全url_path,得到新路径
def full_url(url_path, url_base):
    return up.urljoin(url_base, url_path)


# -----------------------------------------------------------------------------
def url_ext_match(url, exts):
    '判断url对应的文件是否与给定的扩展名匹配'
    ext = up.urlparse(url)
    if ext.path == '' or ext.path == '/':
        return False

    ext = os.path.splitext(ext.path)[1].strip().lower()
    if ext in exts:
        return True

    return False


# -----------------------------------------------------------------------------
# 判断两个url是否相同(包含了URI编码后的情况)
def url_equ(a, b):
    if a == b:
        return True

    if a.startswith('file:///'):
        a = a[8:].replace(':///', ':/')
        a = a.replace('://', ':/')
    if b.startswith('file:///'):
        b = b[8:].replace(':///', ':/')
        b = b.replace('://', ':/')

    if up.unquote(a) == b:
        return True

    if up.unquote(b) == a:
        return True

    return False


def localip_by_dest(dstip='202.97.224.68'):
    """基于udp目标socket,获取对应的本地ip.
        返回值:正常为访问dstip时使用的(本机ip串,本机端口)
              错误为(None,异常对象).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
        s.connect((dstip, 53))  # udp/socket的connect方法,会根据目标地址查询本机路由表,绑定本机ip
        return s.getsockname()  # 得到访问目标地址使用的本机ip与本机端口
    except Exception as e:
        return None, e


# 获取字典dct中的指定key对应的值,不存在时返回默认值
def get_dict_value(dct, key, defval=None):
    if key in dct:
        return dct[key]
    else:
        return defval


def get_slice(lst, seg, segs):
    """获取列表lst的指定分段的切片,seg为第几段(从1开始),segs为总段数"""
    tol = len(lst)  # 元素总量
    slen = (tol + segs // 2) // segs  # 每段元素数量
    e = seg * slen if seg != segs else tol  # 最后一段涵盖尾部
    return lst[(seg - 1) * slen: e]


def union_dict(dst, src):
    """合并src词典的内容到dst,跳过src的空值"""
    for k in src:
        v = src[k]
        if k not in dst:
            dst[k] = v
        else:
            if v == '' or v is None:
                continue
            dst[k] = v


def is_base64_content(body):
    """判断给定的字符串或字节数组是否为有效的base64编码内容
        返回值:(True,decoded)或(False,body)
    """
    try:
        if isinstance(body, str):
            sb_bytes = bytes(body, 'ascii')
        elif isinstance(body, bytes):
            sb_bytes = body
        else:
            return False, body
        decoded = base64.decodebytes(sb_bytes)  # 得到解码后内容
        encoded = base64.encodebytes(decoded).replace(b'\n', b'')  # 对解码后内容再编码
        r = encoded == sb_bytes.replace(b'\n', b'')  # 对再编码的内容和原始内容进行比较,如果一样则说明原始内容是base64编码的
        return (True, decoded) if r else (False, body)
    except Exception:
        return False, body


# -----------------------------------------------------------------------------
def find_chs_by_head(heads):
    '根据http头中的内容类型,分析查找可能存在的字符集类型'
    if 'Content-Type' not in heads:
        return ''
    CT = heads['Content-Type'].lower()

    m = re.search('charset\s*?[=:]\s*?(.*)[; "]?', CT)
    if m is not None:
        return m.group(1)

    return ''


# -----------------------------------------------------------------------------
def find_chs_by_cnt(cnt):
    rp = '<meta[^<>]+charset\s*?=\s*?"?(.*?)[; ">]+'
    if type(cnt).__name__ == 'bytes':
        rp = rp.encode('utf-8')
    ret = ''
    m = re.search(rp, cnt)
    if m:
        if type(cnt).__name__ == 'bytes':
            ret = m.group(1).decode('utf-8')
        else:
            ret = m.group(1)
    if len(ret) <= 2:
        return ''
    return ret


# -----------------------------------------------------------------------------
def find_cnt_type(cnt_type):
    '提取内容类型中的确定值'
    m = re.search(r'\s*([0-9a-zA-Z/*\-_.+]*)([; "]?)', cnt_type)
    if m:
        return m.group(1)
    return cnt_type


# -----------------------------------------------------------------------------
def is_br_content(heads):
    if 'content-encoding' in heads and heads['content-encoding'] in {'br'}:
        return True
    return False


# -----------------------------------------------------------------------------
def is_text_content(heads):
    if 'Content-Type' not in heads:
        return False

    CT = heads['Content-Type'].lower()
    if find_cnt_type(CT) in {'text/html', 'text/xml', 'text/plain', 'application/json',
                             'application/x-www-form-urlencoded'}:
        return True
    return False


# -----------------------------------------------------------------------------
# 生成HTTP默认头
def default_headers(url, Head, body=None):
    ur = up.urlparse(url)
    host = ur[1]

    def make(key, val):
        if key not in Head:
            Head[key] = val

    make('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0')
    make('Accept', 'text/html,application/xhtml+xml,application/json,application/xml;q=0.9,*/*;q=0.8')
    make('Host', host)
    make('Connection', 'keep-alive')

    if body is None or 'Content-Type' in Head:
        return

    # 根据body内容猜测head中的Content-Type
    if isinstance(body, dict):
        # key=val值为URL编码格式
        Head['Content-Type'] = 'application/x-www-form-urlencoded'
        return

    if isinstance(body, str):
        body = body.strip()
    if len(body) == 0:
        return

    if isinstance(body, bytes):
        Head['Content-Type'] = 'application/octet-stream'  # 内容是二进制数据
        return

    if body[0] in {'{', '['}:
        Head['Content-Type'] = 'application/json; charset=utf-8'  # 内容是json
    elif body[0] == '<':
        Head['Content-Type'] = 'text/xml; charset=utf-8'  # 内容是xml
    else:
        m = re.search(r'^[0-9a-zA-Z_\-.*]{1,64}\s*?=\s*?.*', body)
        if m is None:
            # 内容不是key=val那就当作文本了
            Head['Content-Type'] = 'text/plain; charset=utf-8'
        else:
            # key=val值为URL编码格式
            Head['Content-Type'] = 'application/x-www-form-urlencoded'


# -----------------------------------------------------------------------------
def http_req(url, rst, req=None, timeout=15, allow_redirects=True, session=None, cookieMgr=None):
    '''根据给定的req内容进行http请求,得到rst回应.返回值告知是否有错误出现.
        req['METHOD']='get'     可告知http请求的方法类型,get/post/put/...
        req['PROXY']=None       可告知请求使用的代理服务器,如'http://ip:port'
        req['HEAD']={}          可告知http请求头域信息
        req['BODY']={}          可告知http请求的body信息,注意需要同时给出正确的Content-Type
        req['COOKIE']={}        可告知http请求的cookie信息,并进入cookie管理器进行多连接复用.(HEAD中的cookie仅单次请求有效)
        req['SSL_VERIFY']=False 可明确关闭SSL的证书校验

        rst['error']            记录过程中出现的错误
        rst['status_code']      告知回应状态码
        rst['status_reason']    告知回应状态简述
        rst['HEAD']             告知回应头
        rst['COOKIE']           记录回应的cookie内容
        rst['BODY']             记录回应内容,解压缩转码后的内容
    '''
    # 准备请求参数
    if req is None:
        req = {}
    method = req.get('METHOD', 'get').lower()
    SSL_VERIFY = req.get('SSL_VERIFY')
    proxy = req.get('PROXY')
    HEAD = req.get('HEAD', {})
    BODY = req.get('BODY')

    if proxy is not None:
        proxy = {'http': proxy, 'https': proxy}

    COOKIE = req.get('COOKIE')
    # 进行cookie管理与合并
    if cookieMgr is None:
        # 没有cookie管理器对象,直接使用给定的cookie字典
        CKM = COOKIE
    else:
        CKM = cookieMgr
        # 如果COOKIE字典存在且cookie管理器也存在,则进行值合并,后续会清理
        if COOKIE is not None:
            CKM.update(COOKIE)

    rst['error'] = ''

    # 执行请求
    try:
        if session is None:
            session = requests.sessions.Session()
        # 尝试给出默认头域
        default_headers(url, HEAD, BODY)

        # 发起请求
        rsp = session.request(method, url, proxies=proxy, headers=HEAD, data=BODY, cookies=CKM,
                              timeout=timeout, allow_redirects=allow_redirects, verify=SSL_VERIFY)
    except Exception as e:
        rst['error'] = es(e)
        rst['status_code'] = 999
        return False
    finally:
        # 清理掉临时附着的cookie
        if COOKIE is not None and cookieMgr is not None:
            for n in COOKIE:
                cookieMgr.clear('', '/', n)

    # 拼装回应状态
    rst['status_code'] = rsp.status_code
    rst['status_reason'] = rsp.reason

    # 拼装回应头信息
    r = rst['HEAD'] = {}
    for k in rsp.headers:
        r[k] = rsp.headers[k]

    if cookieMgr is not None:
        # 将本次会话得到的cookie进行持久化保存
        cookieMgr.update(session.cookies)

    # 拼装本次得到的cookie信息
    r = rst['COOKIE'] = {}
    for k in session.cookies:
        r[k.name] = k.value

    # 判断是否需要进行额外的br解压缩处理
    rsp_cnt = ''
    if is_br_content(rsp.headers):
        import brotli
        rsp_cnt = brotli.decompress(rsp.content)
    else:
        rsp_cnt = rsp.content

    # 判断是否需要进行字符集解码处理
    chs = find_chs_by_cnt(rsp_cnt)
    if chs == '' and is_text_content(rsp.headers):
        chs = find_chs_by_head(rsp.headers)
        if chs == '':
            chs = 'utf-8'

    def dc(cnt, chs):
        ret = cnt
        try:
            ret = cnt.decode(chs, errors='ignore')
            return ret
        except Exception as e:
            print('STR DECODE WARN :: %s :: %s :: %s' % (rsp.headers, es(e), rsp_cnt))

        try:
            chs2 = 'utf-8'
            ret = cnt.decode(chs2, errors='ignore')
            return ret
        except Exception as e:
            print('STR DECODE ERR :: %s :: %s :: %s :: %s' % (chs, chs2, es(e), rsp_cnt))

        return cnt

    # 记录最终的结果
    if chs != '':
        rst['BODY'] = dc(rsp_cnt, chs)
    else:
        rst['BODY'] = rsp_cnt

    return True


# 快速抓取目标url的get请求函数
def http_get(url, req=None, timeout=15, allow_redirects=True, session=None, cookieMgr=None):
    rst = {}
    http_req(url, rst, req, timeout, allow_redirects, session, cookieMgr)
    return rst.get('BODY', None), rst['status_code'], rst['error']


def make_head(req_dict, head_str):
    ''' 将如下的http头域字符串转换为key/value字典,并放入请求头域
    User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0
    Accept: application/json, text/javascript, */*; q=0.01
    Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
    Accept-Encoding: gzip, deflate
    Content-Type: application/x-www-form-urlencoded; charset=UTF-8
    X-Requested-With: XMLHttpRequest
    Origin: http://credit.fgw.panjin.gov.cn
    Connection: keep-alive
    Referer: http://credit.fgw.panjin.gov.cn/doublePublicity/doublePublicityPage?type=4&columnCode=top_xygs
    '''
    lines = head_str.split('\n')
    if 'HEAD' not in req_dict:
        req_dict['HEAD'] = {}

    for line in lines:
        line = line.strip()
        if line == '': continue
        kv = line.split(':', 1)
        req_dict['HEAD'][kv[0].strip()] = kv[1].strip()


def make_post(req_dict, body=None, content_type='application/x-www-form-urlencoded'):
    """构造请求参数字典,设定为post请求"""
    req_dict['METHOD'] = 'post'
    if body:
        if 'HEAD' not in req_dict:
            req_dict['HEAD'] = {}
        req_dict['HEAD']['Content-Type'] = content_type
        req_dict['BODY'] = body


# -----------------------------------------------------------------------------
def load_cookie_storage(filename):
    '从文件中装载cookie内容,返回RequestsCookieJar对象'
    CJ = cookiejar.LWPCookieJar(filename)
    try:
        CJ.load()
    except FileNotFoundError as e:
        pass
    except Exception as e:
        return -1

    CM = requests.cookies.RequestsCookieJar()
    CM.update(CJ)
    return CM


# -----------------------------------------------------------------------------
def save_cookie_storage(CM, filename):
    '''保存CookieManager对象到filename文件'''
    CJ = cookiejar.LWPCookieJar(filename)
    requests.cookies.merge_cookies(CJ, CM)
    CJ.save()


# 匹配域名对应的代理服务器
def match_proxy(url, proxy_files='./proxy_host.json'):
    if isinstance(proxy_files, str):
        if os.path.exists(proxy_files):
            proxy_table = dict_load(proxy_files, 'utf-8')
        else:
            proxy_table = None
    else:
        proxy_table = proxy_files

    if proxy_table is None:
        return None

    for m in proxy_table:
        if url.find(m) != -1:
            return proxy_table[m]
    return None


# -----------------------------------------------------------------------------
class spd_base:
    '''进行简单功能封装的cookie持久化长连接HTTP爬虫'''

    def __init__(self, filename='./cookie_storage.dat', sessionMgr=None):
        # 初始记录cookie存盘文件名
        self.ckm_filename = filename
        # 装载可能已经存在的cookie值
        self.cookieMgr = load_cookie_storage(filename)
        # 设置默认超时时间
        self.timeout = 15
        # 默认允许自动进行302跳转
        self.allow_redirects = True
        # 生成长连接会话对象
        self.sessionMgr = requests.sessions.Session() if sessionMgr is None else sessionMgr
        # 定义结果对象
        self.rst = {}
        # 最后请求的url
        self.last_url = None

    # 抓取指定的url,通过req可以传递灵活的控制参数
    def take(self, url, req=None, proxy_files='./proxy_host.json'):
        if req is None or 'PROXY' not in req:
            prx = match_proxy(url, proxy_files)  # 尝试使用配置文件进行代理服务器的修正
            if prx:
                if not req:
                    req = {}
                req['PROXY'] = prx

        self.last_url = url
        self.rst = {}
        return http_req(url, self.rst, req, self.timeout, self.allow_redirects, self.sessionMgr, self.cookieMgr)

    def take2(self, url, req=None, proxy_files='./proxy_host.json'):
        """对http动作结果做状态码判断,非200回应也算错误"""
        r = self.take(url, req, proxy_files)
        if not r:
            return r
        if self.get_status_code() != 200:
            self.rst['error'] = '%s :: %s :: %d' % (self.get_error(), self.get_status_reason(), self.get_status_code())
            return False
        return True

    # 保存cookie到文件
    def cookies_save(self):
        save_cookie_storage(self.cookieMgr, self.ckm_filename)

    # 清理持有的cookies
    def cookies_clear(self):
        self.cookieMgr.clear()
        self.sessionMgr.cookies.clear()

    # 获取过程中出现的错误
    def get_error(self):
        return self.rst.get('error', '')

    # 获取回应状态码
    def get_status_code(self):
        return self.rst.get('status_code', 0)

    # 获取回应状态简述
    def get_status_reason(self):
        return self.rst.get('status_reason', '')

    # 获取回应头,字典
    def get_HEAD(self):
        return self.rst.get('HEAD', {})

    # 获取会话回应cookie字典,如果给出了名字则返回对应的值
    def get_COOKIE(self, name=None):
        cookies = self.rst.get('COOKIE', {})
        if name is None:
            return cookies
        return cookies.get(name)

    # 获取回应内容,解压缩转码后的内容
    def get_BODY(self, dv=None):
        rst = self.rst.get('BODY', dv)
        if rst is None:
            return None
        if len(rst) == 0:
            return dv
        return rst


"""
#多项列表排列组合应用样例,先访问,再调整
ic = items_comb()
ic.append(['A', 'B', 'C'])
ic.append(['x', 'y', 'z'])
ic.append(['1', '2', '3'])
print(ic.total())

for i in range(ic.total()):
    print(ic.item(), ic.next())

while True:
    print(ic.item())
    if ic.next():
        break
"""


class items_comb():
    """多列表项排列组合管理器"""

    def __init__(self):
        self.lists = []
        self.lists_pos = []

    def append(self, items):
        """追加一个列表项"""
        self.lists.append(items)
        self.lists_pos.append(0)

    def total(self):
        """计算现有列表项排列组合总数"""
        lists_size = len(self.lists)
        if lists_size == 0:
            return 0
        ret = 1
        for l in range(lists_size):
            ret *= len(self.lists[l])
        return ret

    def plan(self, lvl=0):
        """查询指定层级的当前进度,返回值:(位置1~n,总量n)"""
        if len(self.lists) == 0:
            return None, None
        return self.lists_pos[lvl] + 1, len(self.lists[lvl])

    def next(self):
        """调整当前组合序列索引,便于调用item时得到下一种组合结果.返回值:是否已经归零"""
        levels = len(self.lists)
        for l in range(levels - 1, -1, -1):  # 从后向前遍历
            idx = self.lists_pos[l]  # 取出当前级链表元素索引
            if idx < len(self.lists[l]) - 1:
                self.lists_pos[l] += 1  # 索引没有超出链表范围,则增加后结束
                return False
            self.lists_pos[l] = 0  # 索引超出链表范围时,归零,准备处理上一级链表元素索引
        return True  # 全部级别都处理完毕,这是一轮遍历结束了.

    def item(self):
        """获取当前组合"""
        rst = []
        for i in range(len(self.lists_pos)):
            rst.append(self.lists[i][self.lists_pos[i]])
        return rst
