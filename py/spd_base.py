import html as hp
import http.cookiejar as cookiejar
import json
import logging
import logging.handlers
import os
import re
import time
import urllib.parse as up
from xml.dom import minidom

import requests
from lxml import etree
from lxml import html
from lxml.html.clean import Cleaner

# 调整requests模块的默认日志级别,避免无用调试信息的输出
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# -----------------------------------------------------------------------------
# 从json文件装载字典
def dict_load(fname,encoding=None):
    try:
        fp = open(fname, 'r', encoding=encoding)
        ret = json.load(fp)
        fp.close()
        return ret
    except:
        return None


# 保存词典到文件
def dict_save(fname, dct,encoding=None):
    try:
        fp = open(fname, 'w', encoding=encoding)
        json.dump(dct, fp, indent=4, ensure_ascii=False)
        fp.close()
        return True
    except:
        return False


# 追加字符串到文件
def append_line(fname, dat, encoding=None):
    try:
        fp = open(fname, 'a', encoding=encoding)
        fp.writelines([dat, '\n'])
        fp.close()
        return True
    except:
        return False

# 装载指定文件的内容
def load_from_file(fname, encode='utf-8',mode='r'):
    try:
        f = open(fname, mode, encoding=encode)
        rst = f.read()
        f.close()
        return rst
    except e as Exception:
        return None
        
#保存指定内容到文件
def save_to_file(fname,strdata,encode='utf-8',mode='w'):
    try:
        f = open(fname, mode, encoding=encode)
        f.write(strdata)
        f.close()
        return True
    except:
        return False

# -----------------------------------------------------------------------------
# 进行URL编码
def encodeURIComponent(url):
    url = hp.unescape(url)
    url = up.quote_plus(url, safe='', encoding='utf-8')
    return url


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


# -----------------------------------------------------------------------------
# 生成指定路径的日志记录器
def make_logger(pspath, lvl=logging.DEBUG):
    # 生成日志记录器
    ps_logger = logging.getLogger()
    ps_logger.setLevel(lvl)

    # 生成文件处理器
    filehandler = logging.handlers.WatchedFileHandler(pspath, encoding='utf-8')
    filehandler.setLevel(lvl)
    filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    # 日志记录器绑定文件处理器
    ps_logger.addHandler(filehandler)
    return ps_logger


def bind_logger_console(lg, lvl=logging.ERROR):
    stm = logging.StreamHandler()
    stm.setLevel(lvl)
    lg.addHandler(stm)


# -----------------------------------------------------------------------------
# 将数据保存到fn对应的文件中
def save_file(fn, data, encoding='utf-8'):
    if type(data).__name__ == 'str':
        data = data.encode(encoding)
    f = open(fn, "wb+")
    f.write(data)
    f.close()


# -----------------------------------------------------------------------------
# 自定义实现一个轻量级原汁原味的ini解析器(标准库ini解析器会将key转为小写,干扰参数名字的传递)
class ini_reader:
    def __init__(self):
        self.dct = {}

    # 解析ini字符串
    def read_string(self, cnt):
        lines = cnt.split('\n')
        sec = ''
        for l in lines:
            l = l.strip()
            if l == '': continue
            if l[0] == ';': continue
            if l[0] == '[' and l[-1] == ']':
                sec = l[1:-1]
                self.dct[sec] = []
                continue
            m = re.search(r'(.*?)\s*[=:]\s*(.*)', l)
            if m is None:
                continue
            self.dct[sec].append((m.group(1), m.group(2)))

    # 判断是否含有指定的节
    def has_section(self, sec):
        return sec in self.dct

    # 获取指定节下全部条目的元组列表
    def items(self, sec):
        if not self.has_section(sec):
            return None
        return self.dct[sec]


# -----------------------------------------------------------------------------
# 将py字典对象转换为xml格式串
# 返回值:('结果串','错误说明'),如果错误说明为''则代表没有错误
def dict2xml(dic, indent=True, utf8=False):
    class dict2xml_util:
        '''将python的dict对象转换为xml文本串的工具类'''

        def __init__(self):
            self.DATATYPE_ROOT_DICT = 0
            self.DATATYPE_KEY = 1
            self.DATATYPE_ATTR = 2
            self.DATATYPE_ATTRS = 3

        def _check_errors(self, value, data_type):
            if data_type == self.DATATYPE_ROOT_DICT:
                if isinstance(value, dict):
                    values = value.values()
                    if len(values) != 1:
                        raise Exception('Must have exactly one root element in the dictionary.')
                    elif isinstance(list(values)[0], list):
                        raise Exception('The root element of the dictionary cannot have a list as value.')
                else:
                    raise Exception('Must pass a dictionary as an argument.')

            elif data_type == self.DATATYPE_KEY:
                if not isinstance(value, str):
                    raise Exception('A key must be a string.')

            elif data_type == self.DATATYPE_ATTR:
                (attr, attrValue) = value
                if not isinstance(attr, str):
                    raise Exception('An attribute\'s key must be a string.')
                if not isinstance(attrValue, str):
                    raise Exception('An attribute\'s value must be a string.')

            elif data_type == self.DATATYPE_ATTRS:
                if not isinstance(value, dict):
                    raise Exception('The first element of a tuple must be a dictionary '
                                    'with a set of attributes for the main element.')

        # Recursive core function
        def _buildXMLTree(self, rootXMLElement, key, value, document):
            # 检查节点类型
            self._check_errors(key, self.DATATYPE_KEY)
            # 创建当前节点
            keyElement = document.createElement(key)

            if isinstance(value, str):
                # 如果当前值是简单文本,则在当前节点中直接创建文本节点
                keyElement.appendChild(document.createTextNode('%s' % value))
                # 在本级根节点插入当前节点
                rootXMLElement.appendChild(keyElement)

            elif isinstance(value, dict):
                # 如果当前值是字典,则需要遍历递归处理
                for (k, cont) in value.items():
                    # 用当前节点作为父节点,递归处理字典值的所有子项
                    self._buildXMLTree(keyElement, k, cont, document)
                # 最终将当前节点插入本级根
                rootXMLElement.appendChild(keyElement)

            elif isinstance(value, list):
                # 值为列表项,则遍历处理
                for subcontent in value:
                    # 当前根作为列表值的父节点,用当前key作为元素值的key
                    self._buildXMLTree(rootXMLElement, key, subcontent, document)

            elif isinstance(value, int):
                keyElement.appendChild(document.createTextNode('%d' % value))
                rootXMLElement.appendChild(keyElement)

            elif isinstance(value, float):
                keyElement.appendChild(document.createTextNode('%f' % value))
                rootXMLElement.appendChild(keyElement)

            elif isinstance(value, bool):
                keyElement.appendChild(document.createTextNode('%s' % ('True' if value else 'False')))
                rootXMLElement.appendChild(keyElement)

            elif value is None:
                keyElement.appendChild(document.createTextNode(''))
                rootXMLElement.appendChild(keyElement)

            else:
                raise Exception('Invalid value.')

        def tostring(self, dat, indent=True, utf8=False):
            document = minidom.Document()

            # 先在输出xml中创建一个根节点,标记为root
            root = document.createElement('root')
            if isinstance(dat, dict):
                # 如果数据对象是字典
                for (key, content) in dat.items():
                    self._buildXMLTree(root, key, content, document)
            elif isinstance(dat, list):
                # 如果数据对象是列表
                for content in dat:
                    self._buildXMLTree(root, 'array', content, document)
            else:
                raise Exception('Invalid Data object <%s>' % type(dat))
            if len(root.childNodes) == 0:
                # 如果树是空的,那么要给出一个空的文本节点,避免产生<root/>形式的输出
                root.appendChild(document.createTextNode(''))
            document.appendChild(root)

            encoding = utf8 and 'utf-8' or None

            if indent:
                return document.toprettyxml(indent='\t', encoding=encoding)
            else:
                return document.toxml(encoding=encoding)

    dx = dict2xml_util()
    try:
        return dx.tostring(dic, indent, utf8), ''
    except Exception as e:
        return '', 'XML CONV : ' + str(e)


# -----------------------------------------------------------------------------
# 将json串转换为xml格式串
# 返回值:('结果串','错误说明'),如果错误说明为''则代表没有错误
def json2xml(jstr, indent=True, utf8=False):
    try:
        dic = json.loads(jstr)
        return dict2xml(dic, indent, utf8)
    except Exception as e:
        return '', 'JSON ERR : ' + str(e)


# -----------------------------------------------------------------------------
# 将xml串str抽取重构为rules指定的格式条目{'条目名称':'xpath表达式'}
def xml_extract(str, rules, rootName='条目'):
    qr = {}
    try:
        xp = xpath(str)
        rows = 99999999999
        # 先根据给定的规则,查询得到各个分量的结果
        for tag, p in rules.items():
            qr[tag] = xp.query(p)[0]
            rows = min(rows, len(qr[tag]))  # 获取最少的结果数量

        for tag, p in rules.items():
            if len(qr[tag]) > rows:
                return None, 'xpath查询结果数量不等 <%s> :: %s' % (tag, p)

        if rows == 0:
            return 0, ''  # 没有匹配的结果

        # 创建输出xml文档与根节点
        document = minidom.Document()
        root = document.createElement(rootName)

        # 行循环,逐一输出各个节点中的条目列
        for i in range(rows):
            node = document.createElement('%d' % (i + 1))  # 序号节点
            for tag in rules:
                n = document.createElement(tag)  # 条目节点
                n.appendChild(document.createTextNode(qr[tag][i]))  # 条目内容
                node.appendChild(n)  # 条目节点挂载到序号节点
            root.appendChild(node)  # 序号节点挂载到根节点
        document.appendChild(root)  # 根节点挂载到文档对象

        return rows, document.toprettyxml(indent='\t')  # 输出最终结果
    except Exception as e:
        return None, str(e)


# -----------------------------------------------------------------------------
# 进行html代码修正格式化,得到可解析易读的类似xhtml文本串
def format_html(html_soup):
    try:
        root = etree.HTML(html_soup)
        return etree.tostring(root, encoding='unicode', pretty_print=True, method='html')
    except:
        return html_soup


# -----------------------------------------------------------------------------
# 进行html代码修正格式化,得到可解析易读的类似xhtml文本串
def format_html2(html_soup):
    try:
        root = html.fromstring(html_soup)
        return html.tostring(root, encoding='unicode', pretty_print=True, method='html')
    except:
        return html_soup


# -----------------------------------------------------------------------------
# 清理html页面内容,移除style样式定义与script脚本段
def clean_html(html_str):
    try:
        cleaner = Cleaner(style=True, scripts=True, page_structure=False, safe_attrs_only=False)
        return cleaner.clean_html(html_str)
    except:
        return html_str


# -----------------------------------------------------------------------------
def html2xhtml(html_str):
    try:
        return html.html_to_xhtml(html_str)
    except:
        return html_str


# -----------------------------------------------------------------------------
# 进行xml代码修正格式化
def format_xml(html_soup, desc, chs='utf-8'):
    try:
        root = etree.fromstring(html_soup.encode(chs))
        return desc + '\n' + etree.tostring(root, encoding=chs, pretty_print=True, method='xml').decode(chs)
    except:
        return html_soup


# -----------------------------------------------------------------------------
# 进行xml代码修正格式化
def format_xml2(html_soup):
    try:
        root = html.fromstring(html_soup)
        return html.tostring(root, encoding='utf-8', pretty_print=True, method='xml').decode('utf-8')
    except:
        return html_soup


# 修正xml串xstr中的自闭合节点与空内容节点值为dst
def fix_xml_node(xstr, dst='-'):
    ret = re.sub('<([^>/]*?)/>', '<\\1>%s</\\1>' % dst, xstr)
    return re.sub('<([^>/]*?)></([^>]*?)>', '<\\1>%s</\\2>' % dst, ret)


# -----------------------------------------------------------------------------
# 获取时间串,默认为当前时间
def get_datetime(dt=None, fmt='%Y-%m-%d %H:%M:%S'):
    if dt is None:
        dt = time.localtime()
    return time.strftime(fmt, dt)


# -----------------------------------------------------------------------------
# 对cnt_str进行xpath查询,查询表达式为cc_xpath
# 返回值为([文本或元素列表],'错误说明'),如果错误说明串不为空则代表发生了错误
# 元素可以访问text与attrib字典
def query_xpath(cnt_str, cc_xpath):
    try:
        HTMLRoot = etree.HTML(fix_xml_node(cnt_str))
        r = HTMLRoot.xpath(cc_xpath)
        return r, ''

    except etree.XPathEvalError as e:
        return [], str(e)
    except Exception as e:
        return [], str(e)


# 可进行多次xpath查询的功能对象
class xpath:
    def __init__(self, cntstr):
        cnt_str = fix_xml_node(cntstr)
        self.cnt_str = None
        try:
            self.rootNode = etree.HTML(cnt_str)
            self.cnt_str = cnt_str
        except:
            pass

        if self.cnt_str is None:
            try:
                self.cnt_str = html.html_to_xhtml(cnt_str)
                self.rootNode = etree.HTML(self.cnt_str)
            except:
                self.cnt_str = None
                pass

        if self.cnt_str is None:
            self.cnt_str = format_html2(cnt_str)
            try:
                self.rootNode = etree.HTML(self.cnt_str)
            except:
                self.cnt_str = None
                pass

        if self.cnt_str is None:
            self.cnt_str = "ERROR"

    # 进行xpath查询,查询表达式为cc_xpath
    # 返回值为([文本或元素列表],'错误说明'),如果错误说明串不为空则代表发生了错误
    # 元素可以访问text与attrib字典
    def query(self, cc_xpath):
        try:
            r = self.rootNode.xpath(cc_xpath)
            return r, ''
        except etree.XPathEvalError as e:
            return [], str(e)
        except Exception as e:
            return [], str(e)


# -----------------------------------------------------------------------------
# 对cnt_str进行re查询,re表达式为cc_re,提取的结果序号为idx,(默认为全部匹配结果)
# 返回值为([结果列表],'错误说明'),如果错误说明串不为空则代表发生了错误
def query_re(cnt_str, cc_re, idx=None):
    try:
        m = re.findall(cc_re, cnt_str, re.DOTALL)
        if m is None:
            return '', ''
        if idx is not None:
            return [m[idx]], ''
        return m, ''
    except re.error as e:
        return [], str(e)
    except Exception as e:
        return [], str(e)


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
    rp = '<meta[^<>]+charset\s*?=\s*?(.*?)([; ">]+)'
    if type(cnt).__name__ == 'bytes':
        rp = rp.encode('utf-8')
    m = re.search(rp, cnt)
    if m:
        if type(cnt).__name__ == 'bytes':
            return m.group(1).decode('utf-8')
        else:
            return m.group(1)

    return ''


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
def default_headers(url):
    ur = up.urlparse(url)
    host = ur[1]
    return requests.structures.CaseInsensitiveDict({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Host': host,
        'Connection': 'keep-alive',
    })


# -----------------------------------------------------------------------------
def http_req(url, rst, req=None, timeout=15, allow_redirects=True, session=None, cookieMgr=None):
    '''根据给定的req内容进行http请求,得到rst回应.返回值告知是否有错误出现.
        req['METHOD']='get'     可告知http请求的方法类型,get/post/put/...
        req['PROXY']=''         可告知请求使用的代理服务器,如'http://ip:port'
        req['HEAD']={}          可告知http请求头域信息
        req['BODY']={}          可告知http请求的body信息,注意需要同时给出正确的Content-Type
        req['COOKIE']={}        可告知http请求的cookie信息

        rst['error']            记录过程中出现的错误
        rst['status_code']      告知回应状态码
        rst['status_reason']    告知回应状态简述
        rst['HEAD']             告知回应头
        rst['COOKIE']           记录回应的cookie内容
        rst['BODY']             记录回应内容,解压缩转码后的内容
    '''
    # 准备请求参数
    method = req['METHOD'] if req and 'METHOD' in req else 'get'
    proxy = req['PROXY'] if req and 'PROXY' in req else None
    HEAD = req['HEAD'] if req and 'HEAD' in req else None
    BODY = req['BODY'] if req and 'BODY' in req else None

    if proxy is not None:
        proxy = {'http': proxy, 'https': proxy}

    COOKIE = req['COOKIE'] if req and 'COOKIE' in req else None
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
        # 校正会话对象内部的http默认头
        session.headers = default_headers(url)

        rsp = session.request(method, url, proxies=proxy, headers=HEAD, data=BODY, cookies=CKM,
                              timeout=timeout, allow_redirects=allow_redirects)
    except Exception as e:
        rst['error'] = e
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

    # 记录最终的结果
    if chs != '':
        rst['BODY'] = rsp_cnt.decode(chs, errors='replace')
    else:
        rst['BODY'] = rsp_cnt

    return True


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


# -----------------------------------------------------------------------------
class spd_base:
    '''进行简单功能封装的cookie持久化长连接HTTP爬虫'''

    def __init__(self, filename='./cookiee_storage.dat'):
        # 初始记录cookie存盘文件名
        self.ckm_filename = filename
        # 装载可能已经存在的cookie值
        self.cookieMgr = load_cookie_storage(filename)
        # 设置默认超时时间
        self.timeout = 15
        # 默认允许自动进行302跳转
        self.allow_redirects = True
        # 生成长连接会话对象
        self.session = requests.sessions.Session()
        # 定义结果对象
        self.rst = {}

    # 抓取指定的url,通过req可以传递灵活的控制参数
    def take(self, url, req=None):
        self.rst = {}
        return http_req(url, self.rst, req, self.timeout, self.allow_redirects, self.session, self.cookieMgr)

    # 保存cookie到文件
    def cookies_save(self):
        save_cookie_storage(self.cookieMgr, self.ckm_filename)

    # 获取过程中出现的错误
    def get_error(self):
        return self.rst['error']

    # 获取回应状态码
    def get_status_code(self):
        return self.rst['status_code']

    # 获取回应状态简述
    def get_status_reason(self):
        return self.rst['status_reason']

    # 获取回应头,字典
    def get_HEAD(self):
        return self.rst['HEAD']

    # 获取会话回应cookie字典
    def get_COOKIE(self):
        return self.rst['COOKIE']

    # 获取回应内容,解压缩转码后的内容
    def get_BODY(self):
        return self.rst['BODY']
