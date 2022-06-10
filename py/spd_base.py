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
import magic
import base64
import requests
import mimetypes
import urllib.parse as up
from xml.dom import minidom
from hash_calc import *
from util_base import *

from lxml import etree
from lxml import html
from lxml.html.clean import Cleaner

# 调整requests模块的默认日志级别,避免无用调试信息的输出
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def enable_cros(req, rsp):
    """尝试根据req中的cros请求开启rsp中的cros回应"""
    Origin = req.headers.get('Origin', '*')
    rsp.headers['Access-Control-Allow-Origin'] = Origin
    rsp.headers['Access-Control-Allow-Credentials'] = 'true'


# 补充MIME
_G_EXT_MIME_NAMES = {'application/x-rar': '.rar',
                     'image/vnd.dwg': '.dwg',
                     'application/x-7z-compressed': '.7z',
                     'text/rtf': '.rtf',
                     'application/CDFV2': '.doc',
                     'application/CDF': '.doc'}


def magic_mime(data, to_extname=False):
    """按data内容猜测对应的mime类型;to_extname告知是否转换为文件扩展名."""
    t = magic.from_buffer(data, mime=True)
    if not t:
        t = 'text/plain'
    if to_extname:
        r = mimetypes.guess_extension(t)
        if r:
            return r
        return _G_EXT_MIME_NAMES.get(t)
    else:
        return t


def guess_mime(data, to_extname=False):
    """按data内容扩展分析猜测对应的mime类型;to_extname告知是否转换为文件扩展名.
       返回值:结果MIME类型串或文件扩展名;失败为None
    """
    # 调用magic库猜测数据的格式
    if isinstance(data, str):
        dat = data.encode('utf-8')
    else:
        dat = data[:8192]
    rt = magic_mime(dat, to_extname)
    if rt in {'.txt', 'text/plain'}:
        # 文本类型,进行后续增强判断
        try:
            json.loads(data)  # 先尝试装载json格式
            return '.json' if to_extname else 'application/json'
        except:
            pass

        try:
            minidom.parseString(data)  # 尝试进行xml格式分析
            return '.xml' if to_extname else 'application/xml'
        except:
            pass

        try:
            etree.HTML(data)  # 再尝试装载html格式
            return '.html' if to_extname else 'text/html'
        except:
            pass

    if rt in {'.zip', 'application/zip'}:
        # 对误识别的zip文件进行额外的特征校正
        if dat.startswith(b'\x50\x4B\x03\x04\x0A\x00\x00\x00\x00\x00\x87\x4E\xE2\x40'):
            if dat.find(b'word/document.xml') != -1:  # .docx
                return '.docx' if to_extname else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif dat.find(b'xl/worksheets') != -1:  # .xlsx
                return '.xlsx' if to_extname else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif dat.startswith(b'ppt/presentation.xml'):  # .pptx
                return '.pptx' if to_extname else 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            else:
                return '.docx' if to_extname else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return rt


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
        cleaner = Cleaner(style=True, scripts=True, page_structure=False, safe_attrs_only=False, forms=False)
        rst = cleaner.clean_html(html_str)
        return clean_blank_line(rst)
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
    if dst is not None:
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





# 可进行多次xpath查询的功能对象
class xpath:
    def __init__(self, cntstr=None, try_format=True, fixNode='-'):
        self.cnt_str = None
        self.rootNode = None
        self.mode = None
        if cntstr:
            self.parse(cntstr, try_format, fixNode)

    def is_valid(self):
        return self.rootNode and self.mode

    def parse(self, cntstr, try_format=True, fixNode='-'):
        cnt_str = fix_xml_node(cntstr, fixNode)
        self.cnt_str = None
        self.rootNode = None
        self.mode = None
        errs = []

        try:
            if cnt_str.startswith('<?xml'):
                cnt_str = re.sub(r'<\?xml\s+version\s*=\s*"\d+.\d+"\s+encoding\s*=\s*".*?"\s*\?\??>', '', cnt_str)  # 剔除xml描述信息,避免字符集编码造成的干扰
                parser = etree.XMLParser(strip_cdata=False)  # 需要保留CDATA节点
                self.rootNode = etree.XML(cnt_str, parser)
                self.mode = 'xml'
            else:
                self.rootNode = etree.HTML(cnt_str)
                self.mode = 'html'
            self.cnt_str = cnt_str
            return True, ''
        except Exception as e:
            errs.append(es(e))

        if not try_format:
            return False, ';'.join(errs)  # 不要求进行格式化尝试,则直接返回

        if self.cnt_str is None:
            # 尝试进行xhtml格式化后再解析
            try:
                self.cnt_str = format_xhtml(cnt_str)
                if self.cnt_str:
                    self.rootNode = etree.HTML(self.cnt_str)
                    self.mode = 'html'
                    return True, ''
            except Exception as e:
                errs.append(es(e))

        if self.cnt_str is None:
            # 尝试进行html转换为xhtml后再解析
            try:
                self.cnt_str = html_to_xhtml(cnt_str)
                if self.cnt_str:
                    self.rootNode = etree.HTML(self.cnt_str)
                    self.mode = 'html'
                    return True, ''
            except Exception as e:
                errs.append(es(e))
                self.cnt_str = None
                pass

        return False, ';'.join(errs)

    def query(self, cc_xpath, base=None):
        """查询cc_xpath表达式对应的结果(串或元素).可明确指定查询的基础节点base
            返回值:([文本或元素列表],'错误说明')
            如果'错误说明'不为空则代表发生了错误
        """
        try:
            if base is None:
                base = self.rootNode
            return base.xpath(cc_xpath), ''
        except etree.XPathEvalError as e:
            return [], es(e)
        except Exception as e:
            return [], es(e)

    def take(self, cc_xpath, idx=None, rstmode='xml'):
        """查询cc_xpath表达式对应的结果串或串列表,错误串为空则正常.
            idx=None,获取全部结果
                返回值:([结果串],'错误')
            idx=数字,得到指定的idx结果
                返回值:(结果串,'错误')
        """
        rst, msg = self.query(cc_xpath)
        if msg or len(rst) == 0:
            if idx is None:
                return [], msg
            else:
                return '', msg

        if idx is None:
            lst = []
            for n in rst:
                if isinstance(n, etree._Element):
                    lst.append(etree.tostring(n, encoding='unicode', method=rstmode))
                else:
                    lst.append(n)
            return lst, msg
        else:
            if isinstance(rst[idx], etree._Element):
                return etree.tostring(rst[idx], encoding='unicode', method=rstmode), ''
            else:
                return rst[idx], ''

    @staticmethod
    def xmlnode(nodes, rstmode='xml'):
        """将节点对象转为对应的xml节点文本"""
        lst = []
        for n in nodes:
            if isinstance(n, etree._Element):
                lst.append(etree.tostring(n, encoding='unicode', method=rstmode))
            else:
                lst.append(n)
        return lst


# -----------------------------------------------------------------------------
# 对xstr进行xpath查询,查询表达式为cc_xpath
# 返回值为([文本或元素列表],'错误说明'),如果错误说明串不为空则代表发生了错误
# 元素可以进行etree高级访问
def query_xpath(xstr, cc_xpath, fixNode=' '):
    xp = xpath()
    r, msg = xp.parse(xstr, True, fixNode)
    if not r or msg:
        return [], msg
    return xp.query(cc_xpath)


def remove_xpath(xstr, cc_xpaths, fixNode=' '):
    """根据xpath列表删除xml内容中的相应节点.返回值:(删除后的结果,错误说明)"""
    xp = xpath()
    r, msg = xp.parse(xstr, True, fixNode)
    if not r or msg:
        return xstr, 'xml parse error.'

    if isinstance(cc_xpaths, str):
        cc_xpaths = [cc_xpaths]

    try:
        for cc_xpath in cc_xpaths:  # 循环进行xpath的查找
            nodes = xp.rootNode.xpath(cc_xpath)
            for node in nodes:  # 对查找结果进行逐一遍历
                pn = node.getparent()
                if pn is None:
                    pn = xp.rootNode
                pn.remove(node)  # 调用目标节点的父节点,将目标节点删除
        return etree.tostring(xp.rootNode, encoding='unicode', method=xp.mode), ''
    except Exception as e:
        return xstr, str(e)


def remove_empty(xstr, cc_xpath, fixNode=' '):
    """尝试删除xstr中cc_xpath对应节点,当其下所有子节点的text()都无效的时候.
        返回值:(修正后的内容结果,错误消息) 正常时错误消息为空.
    """
    xp = xpath()
    r, msg = xp.parse(xstr, True, fixNode)
    if not r or msg:
        return xstr, 'xml parse error.'

    try:
        def rec(node):
            if node.text is not None:
                r = re.sub(r'[\r\n\t ]', '', node.text)
                if r:
                    return True  # 存在有效数据,直接返回.
            childs = list(node)
            for cnode in childs:
                if rec(cnode):
                    return True  # 遇到有效数据,直接返回.
            return False  # 不存在有效数据.

        nodes = xp.rootNode.xpath(cc_xpath)
        for node in nodes:  # 对查找结果进行逐一遍历
            if rec(node):
                continue  # 当前节点存在有效数据,跳过
            # 没有有效数据的节点,删除
            pn = node.getparent()
            if pn is None:
                pn = xp.rootNode
            pn.remove(node)  # 调用目标节点的父节点,将目标节点删除

        return etree.tostring(xp.rootNode, encoding='unicode', method=mode), ''
    except Exception as e:
        return xstr, str(e)


# 对cnt_str进行xpath查询,查询表达式为cc_xpath;可以删除removeTags元组列表指出的标签(保留元素内容)
# 返回值为([文本],'错误说明'),如果错误说明串不为空则代表发生了错误
def query_xpath_x(cnt_str, cc_xpath, removeTags=None, removeAtts=None, fixNode=' ', rstmode='html'):
    rs, msg = query_xpath(cnt_str, cc_xpath, fixNode)
    if msg or len(rs) == 0:
        return rs, msg

    for i in range(len(rs)):
        if isinstance(rs[i], etree._Element):
            if removeTags:
                etree.strip_tags(rs[i], removeTags)
            if removeAtts:
                etree.strip_attributes(rs[i], removeAtts)
            rs[i] = etree.tostring(rs[i], encoding='unicode', method=rstmode)

    return rs, msg


# 使用xpath查询指定节点的内容并转为数字.不成功时返回默认值
def query_xpath_num(cnt_str, cc_xpath, defval=1, fixNode=' '):
    rs, msg = query_xpath_x(cnt_str, cc_xpath, fixNode=fixNode)
    if len(rs) != 0:
        return int(rs[0])
    return defval


# 使用xpath查询指定节点的内容串.不成功时返回默认值
def query_xpath_str(cnt_str, cc_xpath, defval=None, fixNode=' '):
    rs, msg = query_xpath_x(cnt_str, cc_xpath, fixNode=fixNode)
    if len(rs) != 0:
        return rs[0].strip()
    return defval


def xml_filter(xstr, xp_node, xp_field, fixNode=' '):
    """对xstr记录的xml进行xpath过滤检查,如果xp_node指出的节点中没有xp_field,则删除该节点"""
    xnodes = query_xpath_x(xstr, xp_node, fixNode=fixNode)[0]
    ret = xstr
    for n in xnodes:
        f = query_xpath_x('<?xml version="1.0" ?>\n' + n, xp_field, fixNode=fixNode)[0]
        if len(f) == 0:
            ret = ret.replace(n, '')
    return ret


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
    last_err = []
    try:
        xp = xpath(xml)
        rows = 99999999999
        # 先根据给定的规则,查询得到各个分量的结果
        for p in xpaths:
            qr[p], err = xp.query(p)
            if err:
                last_err.append(err)
            siz = len(qr[p])
            rows = min(rows, siz)  # 获取最少的结果数量

        for p in xpaths:
            siz = len(qr[p])
            if siz > rows:
                return [], 'xpath查询结果数量不等 <%s> (%d > %d)' % (p, siz, rows)

        if rows == 0:
            msg = ''
            if len(last_err):
                msg = '; '.join(last_err)
            return [], msg  # 没有匹配的结果

        rst = []
        for i in range(rows):
            t = ()
            for p in xpaths:
                x = qr[p][i]
                if isinstance(x, etree._Element):
                    if removeTags:
                        etree.strip_tags(x, removeTags)
                    x = '<?xml version="1.0"?>\n' + etree.tostring(x, encoding='unicode')
                t = t + (x.strip(),)
            rst.append(t)
        return rst, ''

    except Exception as e:
        return [], es(e)


def pair_extract2(xml, xpbase, xpaths, dv=None, removeTags=None):
    """根据xpbase基础表达式和xpaths子节点相对表达式列表,从xml中抽取结果,拼装为元组列表.返回值:[(子节点)],errmsg
        如:pair_extract2(tst, '//item', ['key/data/text()|key/text()', 'val/text()']),子节点的表达式不应有前缀根路径/或相对路径//
        子查询过程中进行了容错处理,查询失败或为空时仍会继续进行,但记录错误消息.
    """

    if len(xpaths) == 0 or not xpbase:
        return [], ''
    try:
        xp = xpath(xml)
        rst = []
        xbase, err = xp.query(xpbase)  # 先进行基础表达式的查询
        if err:
            return [], err

        err = []
        for node in xbase:  # 进行基础查询结果的遍历
            row = []
            for subpath in xpaths:  # 再进行当前基础节点的子查询
                x, e = xp.query(subpath, node)
                # 查询为空或出错时记录默认值和错误
                if len(x) == 0:
                    err.append(f"{etree.tostring(node, encoding='unicode')} sub query empty: {subpath}")
                    row.append(dv)
                    continue
                if e:
                    err.append(f"{etree.tostring(node, encoding='unicode')} sub query error: {e}")
                    row.append(dv)
                    continue
                # 如果子查询结果为节点,则进行文本转换
                x = x[0]
                if isinstance(x, etree._Element):
                    if removeTags:
                        etree.strip_tags(x, removeTags)  # 移除特定tag但保留文本节点内容
                    x = '<?xml version="1.0"?>\n' + etree.tostring(x, encoding='unicode')
                # 记录当前节点的子查询结果
                row.append(x.strip())
            # 记录当前节点的全部子查询结果
            rst.append(tuple(row))
        return rst, ';'.join(err)
    except Exception as e:
        return [], es(e)


# 将xpath规则结果对列表转换为字典
def make_pairs_dict(lst, xml2txt=False):
    dct = {}
    if xml2txt:
        for d in lst:
            k = extract_xml_text(d[0])
            v = extract_xml_text(d[1])
            dct[k] = v
    else:
        for d in lst:
            dct[d[0]] = d[1]
    return dct


def pair_extract_dict(xml, xpaths, removeTags=None, xml2txt=False):
    """将xml内容按xpaths对抽取拼装为dict"""
    rst, err = pair_extract(xml, xpaths, removeTags)
    if err:
        return {}, err
    return make_pairs_dict(rst, xml2txt), ''


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
                self.logger.warn('page table xpath query error <%s>:\n%s', msg, page)
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
        req['COOKIE']={}        可告知http请求的cookie信息
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
        try:
            return cnt.decode(chs, errors='ignore')
        except Exception as e:
            print('STR DECODE WARN :: %s :: %s :: %s' % (rsp.headers, es(e), rsp_cnt))

        try:
            chs2 = 'utf-8'
            return cnt.decode(chs2, errors='ignore')
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

    # 获取会话回应cookie字典
    def get_COOKIE(self):
        return self.rst.get('COOKIE', {})

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
