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
import urllib.parse as up
import zipfile
from xml.dom import minidom
from hash_calc import *

import requests
from lxml import etree
from lxml import html
from lxml.html.clean import Cleaner

# 调整requests模块的默认日志级别,避免无用调试信息的输出
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# -----------------------------------------------------------------------------
# 从json文件装载字典
def dict_load(fname, encoding=None):
    try:
        fp = open(fname, 'r', encoding=encoding)
        ret = json.load(fp)
        fp.close()
        return ret
    except Exception as e:
        return None


# 保存词典到文件
def dict_save(fname, dct, encoding=None):
    try:
        fp = open(fname, 'w', encoding=encoding)
        json.dump(dct, fp, indent=4, ensure_ascii=False)
        fp.close()
        return True
    except Exception as e:
        return False


# 追加字符串到文件
def append_line(fname, dat, encoding=None):
    try:
        fp = open(fname, 'a', encoding=encoding)
        fp.writelines([dat, '\n'])
        fp.close()
        return True
    except Exception as e:
        return False


# 追加字符串到文件
def append_lines(fname, dats, encoding=None):
    try:
        fp = open(fname, 'a', encoding=encoding)
        for l in dats:
            fp.write(','.join(l) + '\n')
        fp.close()
        return True
    except Exception as e:
        return False

class waited_t:
    """简单的超时等待计时器"""

    def __init__(self, timeout):
        """从构造的时候就开始计时,告知等待超时秒数"""
        self._timeout = timeout
        self.reset()

    def reset(self):
        """复位结束时间点,准备重新计时"""
        self.end = time.time() + self._timeout

    def timeout(self):
        """用当前时间判断,是否超时了"""
        return time.time() >= self.end

# 文件行输出器
class append_line_t:
    def __init__(self, fname, encoding='utf-8'):
        try:
            self.fp = open(fname, 'a', encoding=encoding)
        except Exception as e:
            print('ERROR: %s' % (es(e)))

    def append(self, line=''):
        if isinstance(line, list):
            for l in line:
                self.fp.writelines([l, '\n'])
        else:
            self.fp.writelines([line, '\n'])

    def flush(self):
        if self.fp:
            self.fp.flush()

    def close(self):
        if self.fp:
            self.fp.close()
            self.fp = None

    def __del__(self):
        self.close()


# 文件行读取器
class read_lines_t:
    def __init__(self, fname, encoding='utf-8'):
        try:
            self.fp = open(fname, 'r', encoding=encoding)
        except Exception as e:
            self.fp = None
            print('ERROR: %s' % (es(e)))

    def skip(self, lines=100):
        if not self.fp:
            return False

        for i in range(lines):
            l = self.fp.readline()
            if l is '': break
        return True

    def fetch(self, lines=100):
        if not self.fp:
            return []
        ret = []
        for i in range(lines):
            l = self.fp.readline()
            if l is '': break
            ret.append(l.rstrip())
        return ret

    def loop(self, looper):
        if not self.fp:
            return 0
        rc = 0
        while True:
            l = self.fp.readline()
            if l is '': break
            rc += 1
            looper(l, rc)

        return rc

    def close(self):
        if self.fp:
            self.fp.close()
            self.fp = None

    def __del__(self):
        self.close()


# 将infile分隔为多个ofile_prx文件,每个文件最多lines行
def split_lines_file(infile, ofile_prx, lines):
    fi = spd_base.read_lines_t(infile)
    fn = 1
    ls = []
    while True:
        fo = spd_base.append_line_t(ofile_prx % fn)
        for p in range(lines // 100):
            ls = fi.fetch()
            if len(ls) == 0:
                break
            fo.append(ls)
        fo.close()
        fn += 1

        if len(ls) == 0:
            break


'''
lw = lines_writer(0)
lw.open('tst.txt')
lw.append('1')
lw.append('2')
lw.append('3')
lw.appendt(('4',))
lw.appendx([('5',), ('6',)])
'''


class lines_writer:
    def __init__(self, keyIdx=None, sep=','):
        self.fp = None
        self.keys = set()
        self.keyIdx = keyIdx
        self.sep = sep

    def open(self, fname, encoding='utf-8'):
        if self.fp is not None:
            return True
        try:
            self.fp = open(fname, 'a+', encoding=encoding)
            self.fp.seek(0, 0)
            for line in self.fp.readlines():
                line = line.strip()
                if line == '': continue
                self.keys.add(calc_key(line, self.keyIdx, self.sep))  # 记录当前行数据的唯一key,便于排重

            self.fp.seek(0, 2)
            return True
        except Exception as e:
            return False

    def append(self, line):
        """追加行内容到文件.返回值:-1文件未打开;-2其他错误;0内容为空;1内容重复;2正常完成."""
        line = line.strip()
        if line == '': return 0

        t = line.split(self.sep)
        return self.appendt(t)

    def appendt(self, t):
        """追加()元组内容到文件.返回值:-1文件未打开;-2其他错误;0内容为空;1内容重复;2正常完成."""
        if self.fp is None:
            return -1

        key = calc_key(t, self.keyIdx)
        if key in self.keys:
            return 1
        try:
            self.fp.write(self.sep.join(t) + '\n')
            self.keys.add(key)
            return 2
        except Exception as e:
            return -2

    def appendx(self, lst):
        """追加元组列表到文件"""
        if self.fp is None:
            return -1
        for l in lst:
            r = self.appendt(l)
            if r < 0:
                return r
        return 2

    def save(self):
        if self.fp is None:
            return False
        self.fp.flush()
        return True

    def close(self):
        if self.fp is None:
            return False
        self.fp.close()
        self.fp = None
        return True


# 装载指定文件的内容
def load_from_file(fname, encode='utf-8', mode='r'):
    try:
        f = open(fname, mode, encoding=encode)
        rst = f.read()
        f.close()
        return rst
    except Exception as e:
        return None


# 保存指定内容到文件
def save_to_file(fname, strdata, encode='utf-8', mode='w'):
    try:
        f = open(fname, mode, encoding=encode)
        f.write(strdata)
        f.close()
        return True
    except Exception as e:
        return False


# 保存指定内容到文件,同时创建不存在的层级目录
def save_to_file2(path, fname, strdata, encode='utf-8', mode='w'):
    try:
        os.makedirs(path.rstrip("\\").rstrip('/'))
    except Exception as e:
        pass
    return save_to_file(path + fname, strdata, encode, mode)


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


# -----------------------------------------------------------------------------
# 生成指定路径的日志记录器
def make_logger(pspath, lvl=logging.DEBUG, max_baks=None):
    # 调整日志输出的级别名称.
    logging._levelToName[logging.ERROR] = 'ERR!'
    logging._levelToName[logging.WARNING] = 'WRN!'
    logging._levelToName[logging.DEBUG] = 'DBG.'

    # 生成日志记录器
    ps_logger = logging.getLogger()
    ps_logger.setLevel(logging.DEBUG)

    # 生成文件处理器
    if max_baks:
        filehandler = logging.handlers.RotatingFileHandler(pspath, encoding='utf-8', maxBytes=1024 * 1024 * 4, backupCount=max_baks)
    else:
        filehandler = logging.handlers.WatchedFileHandler(pspath, encoding='utf-8')
    filehandler.setLevel(lvl)
    filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    # 日志记录器绑定文件处理器
    ps_logger.addHandler(filehandler)
    return ps_logger


def bind_logger_console(lg, lvl=logging.ERROR):
    stm = logging.StreamHandler()
    stm.setLevel(lvl)
    stm.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
    lg.addHandler(stm)


# -----------------------------------------------------------------------------
# 将数据保存到fn对应的文件中
def save_file(fn, data, encoding='utf-8'):
    if type(data).__name__ == 'str':
        data = data.encode(encoding)
    f = open(fn, "wb+")
    f.write(data)
    f.close()


# 十六进制串转换为对应的字符
import binascii


def hexstr_to_chr(hex_str):
    hex = hex_str.encode('utf-8')
    str_bin = binascii.unhexlify(hex)
    return str_bin.decode('utf-8')


# 挑选出指定串中的\xHH转义序列，并转换为标准串
def hex_decode(s):
    m = re.findall(r'(\\x[0-9a-fA-F]{2})', s)
    ms = set(m)
    for i in ms:
        c = hexstr_to_chr(i[2:])
        s = s.replace(i, c)
    return s


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
                keyElement.appendChild(document.createTextNode(value.strip()))
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
        return '', 'XML CONV : ' + es(e)


# -----------------------------------------------------------------------------
# 将json串转换为xml格式串,可控制是否直接返回utf-8串
# 返回值:('结果串','错误说明'),如果错误说明为''则代表没有错误
def json2xml(jstr, indent=True, utf8=False):
    try:
        dic = json.loads(jstr)
        if isinstance(dic, str):
            dic = json.loads(dic)
        return dict2xml(dic, indent, utf8)
    except Exception as e:
        return '', 'JSON ERR : ' + es(e)


def json2dict(jstr, indent=True, utf8=False):
    try:
        dic = json.loads(jstr)
        return dic, ''
    except Exception as e:
        return [], 'JSON ERR : ' + es(e)


# -----------------------------------------------------------------------------
# 进行html代码修正格式化,得到可解析易读的类似xhtml文本串
def format_html(html_soup):
    try:
        root = etree.HTML(html_soup)
        return etree.tostring(root, encoding='unicode', pretty_print=True, method='html')
    except Exception as e:
        return html_soup


# -----------------------------------------------------------------------------
# 进行html代码修正格式化,得到可解析易读的类似xhtml文本串
def format_xhtml(html_soup):
    try:
        root = html.fromstring(html_soup)
        return html.tostring(root, encoding='unicode', pretty_print=True, method='xml')
    except Exception as e:
        return html_soup


# -----------------------------------------------------------------------------
# 清理html页面内容,移除style样式定义与script脚本段
def clean_html(html_str):
    try:
        cleaner = Cleaner(style=True, scripts=True, page_structure=False, safe_attrs_only=False)
        return cleaner.clean_html(html_str)
    except Exception as e:
        return html_str


# -----------------------------------------------------------------------------
def html_to_xhtml(html_str):
    """将html_str严格的转换为xhtml格式,带着完整的命名空间限定"""
    try:
        root = etree.HTML(html_str)
        html.html_to_xhtml(root)
        return html.tostring(root, encoding='utf-8', pretty_print=True, method='xml').decode('utf-8')
    except Exception as e:
        return html_str


# -----------------------------------------------------------------------------
# 进行xml代码修正格式化
def format_xml(html_soup, desc, chs='utf-8'):
    try:
        root = etree.fromstring(html_soup.encode(chs))
        return desc + '\n' + etree.tostring(root, encoding=chs, pretty_print=True, method='xml').decode(chs)
    except Exception as e:
        return html_soup


# 修正xml串xstr中的自闭合节点与空内容节点值为dst
def fix_xml_node(xstr, dst='-'):
    if xstr is None: return None
    ret = xstr.strip()  # 字符串两端净空
    ret = re.sub('<([^>/\s]+)(\s*[^>/]*)/>', '<\\1\\2>%s</\\1>' % dst, ret)  # 修正自闭合节点
    ret = re.sub('<([^/][^>]*?)></([^>]*?)>', '<\\1>%s</\\2>' % dst, ret)  # 替换空节点
    ret = re.sub(r'[\u001f\u000b\u001e]', '', ret)  # 替换无效字符干扰
    ret = ret.replace('&#13;', '\n')  # 修正结果串
    return ret


# 提取xml串中的节点文本,丢弃全部标签格式
def extract_xml_text(xstr):
    if xstr is None: return None
    ret = xstr.strip()  # 字符串两端净空
    ret = re.sub('<([^>/]*?)/>', '', ret)  # 丢弃自闭合节点
    ret = re.sub('<([^/][^>]*?)>', '', ret)  # 替换开始标签
    ret = re.sub('</([^>]*?)>', '', ret)  # 替换结束标签

    ret = ret.replace('&#13;', '\n')  # 修正结果串
    ret = ret.strip()
    return ret


def replace_re(cnt_str, cc_re, cc_dst):
    """将cnt_str中符合cc_re正则表达式的部分替换为cc_dst"""
    try:
        rst = re.sub(cc_re, cc_dst, cnt_str, flags=re.DOTALL)
        return rst, ''
    except Exception as e:
        return cnt_str, es(e)


def zip_file(srcdir, outfile):
    """把原目录srcdir中的文件全部打包放在outfile压缩文件中.返回值:空正常;否则为错误信息"""
    try:
        ls = os.listdir(srcdir)
        zf = zipfile.ZipFile(outfile, 'w')
        for f in ls:
            zf.write(srcdir + '/' + f, f)
        zf.close()
        return ''
    except Exception as e:
        return es(e)


# -----------------------------------------------------------------------------
# 获取时间串,默认为当前时间
def get_datetime(dt=None, fmt='%Y-%m-%d %H:%M:%S'):
    if dt is None:
        dt = time.localtime()
    return time.strftime(fmt, dt)


def get_curr_date(fmt='%Y-%m-%d', now=None):
    """得到当前日期,ISO串;可以取得微秒时间的格式为 '%Y-%m-%d %H:%M:%S.%f'"""
    if now is None:
        now = datetime.datetime.now()
    return now.strftime(fmt)


def adj_date_day(datestr, day):
    """对给定的日期串datestr进行天数day增减运算,得到新的日期,ISO串"""
    date = datetime.datetime.strptime(datestr, '%Y-%m-%d')
    date += datetime.timedelta(days=day)
    return date.strftime('%Y-%m-%d')


def date_to_utc(datestr):
    """将日期串转换为UTC时间秒"""
    return int(datetime.datetime.strptime(datestr, '%Y-%m-%d').timestamp())


def datetime_to_utc(datestr):
    """将日期串转换为UTC时间秒"""
    return int(datetime.datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S').timestamp())


def utc_to_datetime(sec):
    """把UTC秒转换为ISO标准时间串"""
    date = datetime.datetime.fromtimestamp(sec)
    return date.strftime('%Y-%m-%d %H:%M:%S')


def utc_to_date(sec):
    """把UTC秒转换为ISO标准日期串"""
    date = datetime.datetime.fromtimestamp(sec)
    return date.strftime('%Y-%m-%d')


def printf(fmt, *arg):
    """带有当前时间格式的打印输出"""
    fmt = '[%s] ' + fmt
    dt = get_datetime()
    print(fmt % (dt, *arg))


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


def es(e: Exception):
    return '%s:%s' % (e.__class__.__name__, e)


# -----------------------------------------------------------------------------
# 对xstr进行xpath查询,查询表达式为cc_xpath
# 返回值为([文本或元素列表],'错误说明'),如果错误说明串不为空则代表发生了错误
# 元素可以进行etree高级访问
def query_xpath(xstr, cc_xpath, fixNode='-'):
    try:
        if fixNode is not None:
            xstr = fix_xml_node(xstr, fixNode)
        if xstr.startswith('<?xml'):
            HTMLRoot = etree.XML(xstr)
        else:
            HTMLRoot = etree.HTML(xstr)
        if HTMLRoot is None:
            return [], 'xml/html xpath parse fail.'
        r = HTMLRoot.xpath(cc_xpath)
        return r, ''
    except etree.XPathEvalError as e:
        return [], es(e)
    except Exception as e:
        return [], es(e)


# 对cnt_str进行xpath查询,查询表达式为cc_xpath;可以删除removeTags元组列表指出的标签(保留元素内容)
# 返回值为([文本],'错误说明'),如果错误说明串不为空则代表发生了错误
def query_xpath_x(cnt_str, cc_xpath, removeTags=None):
    rs, msg = query_xpath(cnt_str, cc_xpath)
    if msg != '':
        return rs, msg

    for i in range(len(rs)):
        if isinstance(rs[i], etree._Element):
            if removeTags:
                etree.strip_tags(rs[i], removeTags)
            rs[i] = etree.tostring(rs[i], encoding='unicode', method='html')

    return rs, msg


# 使用xpath查询指定节点的内容并转为数字.不成功时返回默认值
def query_xpath_num(cnt_str, cc_xpath, defval=1):
    rs, msg = query_xpath(cnt_str, cc_xpath)
    if len(rs) != 0:
        return int(rs[0])
    return defval


# 使用xpath查询指定节点的内容串.不成功时返回默认值
def query_xpath_str(cnt_str, cc_xpath, defval=None):
    rs, msg = query_xpath(cnt_str, cc_xpath)
    if len(rs) != 0:
        return rs[0].strip()
    return defval


def xml_filter(xstr, xp_node, xp_field):
    """对xstr记录的xml进行xpath过滤检查,如果xp_node指出的节点中没有xp_field,则删除该节点"""
    xnodes = query_xpath_x(xstr, xp_node)[0]
    ret = xstr
    for n in xnodes:
        f = query_xpath_x('<?xml version="1.0" ?>\n' + n, xp_field)[0]
        if len(f) == 0:
            ret = ret.replace(n, '')
    return ret


# 可进行多次xpath查询的功能对象
class xpath:
    def __init__(self, cntstr, is_xml=False):
        cnt_str = fix_xml_node(cntstr)
        self.cnt_str = None
        self.last_err = []
        try:
            if cnt_str.startswith('<?xml') or is_xml:
                self.rootNode = etree.XML(cnt_str)
            else:
                self.rootNode = etree.HTML(cnt_str)
            self.cnt_str = cnt_str
        except Exception as e:
            self.last_err.append(es(e))

        if self.cnt_str is None:
            try:
                self.cnt_str = format_xhtml(cnt_str)
                if self.cnt_str:
                    self.rootNode = etree.HTML(self.cnt_str)
            except Exception as e:
                self.last_err.append(es(e))

        if self.cnt_str is None:
            try:
                self.cnt_str = html_to_xhtml(cnt_str)
                if self.cnt_str:
                    self.rootNode = etree.HTML(self.cnt_str)
            except Exception as e:
                self.last_err.append(es(e))
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
            return [], es(e)
        except Exception as e:
            return [], es(e)


# -----------------------------------------------------------------------------
# 将xml串str抽取重构为rules指定的格式条目{'条目名称':'xpath表达式'}
def xml_extract(str, rules, rootName='条目', removeTags=None):
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
                x = qr[tag][i]
                if isinstance(x, etree._Element):
                    if removeTags:
                        etree.strip_tags(x, removeTags)
                    x = etree.tostring(x, encoding='unicode', method='xml')

                n = document.createElement(tag)  # 条目节点
                n.appendChild(document.createTextNode(x))  # 条目内容
                node.appendChild(n)  # 条目节点挂载到序号节点
            root.appendChild(node)  # 序号节点挂载到根节点
        document.appendChild(root)  # 根节点挂载到文档对象

        return rows, document.toprettyxml(indent='\t')  # 输出最终结果
    except Exception as e:
        return None, es(e)


def pair_extract(xml, xpaths, removeTags=None):
    """根据xpaths列表,从xml中抽取结果,拼装为元组列表.
        返回值:[()],errmsg
    """
    qr = {}
    if len(xpaths) == 0:
        return [], ''
    try:
        xp = xpath(xml)
        rows = 99999999999
        # 先根据给定的规则,查询得到各个分量的结果
        for p in xpaths:
            qr[p] = xp.query(p)[0]
            siz = len(qr[p])
            rows = min(rows, siz)  # 获取最少的结果数量

        for p in xpaths:
            siz = len(qr[p])
            if siz > rows:
                return [], 'xpath查询结果数量不等 <%s> (%d > %d)' % (p, siz, rows)

        if rows == 0:
            msg = ''
            if len(xp.last_err):
                msg = '; '.join(xp.last_err)
            return [], msg  # 没有匹配的结果

        rst = []
        for i in range(rows):
            t = ()
            for p in xpaths:
                x = qr[p][i]
                if isinstance(x, etree._Element):
                    if removeTags:
                        etree.strip_tags(x, removeTags)
                    x = etree.tostring(x, encoding='unicode')
                    x = '<?xml version="1.0"?>\n' + x
                t = t + (x.strip(),)
            rst.append(t)
        return rst, ''

    except Exception as e:
        return [], es(e)


# 将xpath规则结果对列表转换为字典
def make_pairs_dict(lst, trsxml=False):
    dct = {}
    if trsxml:
        for d in lst:
            k = extract_xml_text(d[0])
            v = extract_xml_text(d[1])
            dct[k] = v
    else:
        for d in lst:
            dct[d[0]] = d[1]
    return dct


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


# -----------------------------------------------------------------------------
# 对html/table信息列进行提取的功能封装
class table_xpath:
    def __init__(self, page, rule_key, rule_val, logger=None, trsxml=False):
        '''构造函数传入含有table的page内容串,以及table中的key列与val列的xpath表达式'''
        self.logger = logger
        self.trsxml = trsxml  # 是否转换xml为txt
        self.parse(page, rule_key, rule_val)

    def parse(self, page, rule_key, rule_val):
        """使用规则提取page中的对应内容"""
        self.dct = None
        self.page = page

        rst, msg = pair_extract(page, [rule_key, rule_val])
        if msg != '':
            if self.logger:
                self.logger.warn('page table xpath parse error <%s>:\n%s', msg, page)
            return

        self.dct = make_pairs_dict(rst, self.trsxml)

    def __getitem__(self, item):
        '''使用['key']的方式访问对应的值'''
        return self.value(item)

    def value(self, item, defval=None):
        '''访问对应的值'''
        v = get_dict_value(self.dct, item, defval)
        if v is None:
            if self.logger:
                self.logger.warn('page table xpath dict error <%s>:\n%s', item, self.page)
            return None
        return extract_xml_text(v)

    def cloneTo(self, dct, filter=None):
        """将当前字典克隆合并到目标字典中,同时可进行键值过滤处理"""
        if self.dct is None:
            return

        for k in self.dct:
            if filter:
                k1, v1 = filter(k, self.dct[k])
            else:
                k1 = k
                v1 = self.dct[k]
            dct[k1] = v1


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
        return [], es(e)
    except Exception as e:
        return [], es(e)


# 查询指定捕获组的内容并转为数字.不成功时返回默认值
def query_re_num(cnt_str, cc_re, defval=1):
    rs, msg = query_re(cnt_str, cc_re)
    if len(rs) != 0 and rs[0] != '':
        return int(rs[0])
    return defval


# 查询指定捕获组的内容串.不成功时返回默认值
def query_re_str(cnt_str, cc_re, defval=None):
    rs, msg = query_re(cnt_str, cc_re)
    if len(rs) != 0:
        return rs[0]
    return defval


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
        'Accept': 'text/html,application/xhtml+xml,application/json,application/xml;q=0.9,*/*;q=0.8',
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
    SSL_VERIFY = req['SSL_VERIFY'] if req and 'SSL_VERIFY' in req else None
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

    # 记录最终的结果
    if chs != '':
        rst['BODY'] = rsp_cnt.decode(chs, errors='ignore')
    else:
        rst['BODY'] = rsp_cnt

    return True


# 快速抓取目标url的get请求函数
def http_get(url, req=None, timeout=15, allow_redirects=True, session=None, cookieMgr=None):
    rst = {}
    http_req(url, rst, req, timeout, allow_redirects, session, cookieMgr)
    return rst['BODY'], rst['status_code'], rst['error']


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
        if line is '': continue
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


# -----------------------------------------------------------------------------
class spd_base:
    '''进行简单功能封装的cookie持久化长连接HTTP爬虫'''

    def __init__(self, filename='./cookie_storage.dat'):
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

    def _rst_val(self, key, defval):
        return self.rst[key] if key in self.rst else defval

    # 抓取指定的url,通过req可以传递灵活的控制参数
    def take(self, url, req=None, proxy_files='./proxy_host.json'):

        def match_proxy(url):  # 匹配域名对应的代理服务器
            if isinstance(proxy_files, str):
                proxy_table = dict_load(proxy_files, 'utf-8')
            else:
                proxy_table = proxy_files

            if proxy_table is None:
                return None

            for m in proxy_table:
                if url.find(m) != -1:
                    return proxy_table[m]
            return None

        if req is None or 'PROXY' not in req:
            prx = match_proxy(url)  # 尝试使用配置文件进行代理服务器的修正
            if prx:
                if not req:
                    req = {}
                req['PROXY'] = prx

        self.rst = {}
        return http_req(url, self.rst, req, self.timeout, self.allow_redirects, self.session, self.cookieMgr)

    # 保存cookie到文件
    def cookies_save(self):
        save_cookie_storage(self.cookieMgr, self.ckm_filename)

    # 获取过程中出现的错误
    def get_error(self):
        return self._rst_val('error', '')

    # 获取回应状态码
    def get_status_code(self):
        return self._rst_val('status_code', 0)

    # 获取回应状态简述
    def get_status_reason(self):
        return self._rst_val('status_reason', '')

    # 获取回应头,字典
    def get_HEAD(self):
        return self._rst_val('HEAD', {})

    # 获取会话回应cookie字典
    def get_COOKIE(self):
        return self._rst_val('COOKIE', {})

    # 获取回应内容,解压缩转码后的内容
    def get_BODY(self):
        return self._rst_val('BODY', None)



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
