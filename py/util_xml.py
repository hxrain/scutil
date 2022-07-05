from xml.dom import minidom
from lxml import etree
from lxml import html
from lxml.html.clean import Cleaner
import re


def get_tag_child(html, tag, with_tag=False):
    """在html内容中,提取tag标签的内容,返回子节点内容列表"""
    rst = []
    res = re.finditer("""<\s*(%s)\s*[^<>]*?>\s*(.*?)\s*<\s*/(%s)\s*>""" % (tag, tag), html, re.DOTALL)
    for m in res:
        if with_tag:
            rst.append(m.group(0))
        else:
            rst.append(m.group(2))
    return rst


def get_tag_nest(html, tag='\w+', with_tag=False):
    """在html内容中,提取tag标签嵌套的内容,返回子节点内容列表
        单级嵌套和多级嵌套的返回值都是单一的.但多个并行嵌套的返回值是多个.
    """
    rst = []
    exp = r"""(<\s*%s\s*[^<>]*?>[\n\s]*)+(.*?)([\n\s]*<\s*/%s\s*>)+""" % (tag, tag)
    res = re.finditer(exp, html, re.DOTALL)
    for m in res:
        if with_tag:
            rst.append(m.group(0))
        else:
            rst.append(m.group(2))
    return rst


def html_drop_tag(txt, tag='', dst='', is_begin=None):
    """替换指定类型的html标签,或全部标签为指定的目标值"""
    if tag == '':
        tag = '\w+'
    if is_begin is None:
        r = r'<\s*%s\s*/\s*>|</\s*%s\s*>|<\s*%s\s[^>]*?>|<\s*%s>' % (tag, tag, tag, tag)
    elif is_begin:
        r = r'<\s*%s\s*/\s*>|<\s*%s\s[^>]*?>|<\s*%s>' % (tag, tag, tag)
    else:
        r = r'<\s*%s\s*/\s*>|</\s*%s\s*>' % (tag, tag)
    return re.sub(r, dst, txt)


def html_get_tags(txt, tag='', is_begin=None):
    """获取txt文本中的指定或全部tag标签"""
    if tag == '':
        tag = '\w+'
    if is_begin is None:
        r = r'</\s*%s\s*>|<\s*%s\s[^>]*?>|<\s*%s>' % (tag, tag, tag)
    elif is_begin:
        r = r'<\s*%s\s[^>]*?>|<\s*%s>' % (tag, tag)
    else:
        r = r'</\s*%s\s*>' % tag
    return re.findall(r, txt)


def html_drop_attr(txt):
    """删除tag内全部属性"""
    r = '<\s*([^\s>]*)\s*[^>]*?>'
    return re.sub(r, '<\\1>', txt)


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
                r = re.sub(r'[\r\n\t ]+', '', node.text)
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

        return etree.tostring(xp.rootNode, encoding='unicode', method=xp.mode), ''
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