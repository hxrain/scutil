# -*- coding: utf-8 -*-

import logging
import logging.handlers
import datetime
import os
import json
import re
import time
from xml.dom import minidom
import zipfile
from hash_calc import calc_key
import traceback


# -----------------------------------------------------------------------------
def es(e: Exception):
    """格式化简短异常信息"""
    return '%s:%s' % (e.__class__.__name__, e)


def ei(e: Exception):
    """格式化完整异常信息"""
    es = ''.join(traceback.format_tb(e.__traceback__))
    return '%s:\n%s' % (e.__class__.__name__, es)


def is_normal_attr(obj, key):
    """判断对象obj的key对应的属性,是否为简单属性(不是property/不是函数/不是私有属性)"""
    is_prop = isinstance(getattr(type(obj), key, None), property)
    is_func_attr = callable(getattr(obj, key))
    is_private_attr = key.startswith('__')
    return not (is_func_attr or is_prop or is_private_attr)


def is_basic_type(value):
    """判断指定的值类型,是否为内置的基本类型"""
    if value is None:
        return True
    if type(value) is not type:
        value = type(value)
    return value in {int, float, str, bool}


def bind_closure(func, usrdat):
    """绑定func与usrdat,返回对应的闭包函数"""

    def closure_func(*args, **kwargs):
        return func(usrdat, *args, **kwargs)

    return closure_func


def find_zh_chars(s, is_zh=True):
    """查询字符串s中的字符.
        is_zh 控制是否为中文,或英文字符范围
        返回值:['中','文','字','符']
    """
    if is_zh:
        return re.findall('[\u4e00-\u9fa5]', s)
    else:
        return re.findall('[!-~]', s)


# -----------------------------------------------------------------------------
# 生成指定路径的日志记录器
def make_logger(pspath, lvl=logging.DEBUG, max_baks=None, tag=None):
    """根据给定的日志输出文件路径,生成日志记录器;
        lvl:告知允许输出的日志级别
        max_baks:告知是否允许生成循环备份的日志文件
            None:使用单日志文件模式
            isinstance(max_baks,int):告知备份文件数量
            isinstance(max_baks, tuple):告知(备份文件数量,以及文件最大尺寸)
        tag为不同日志记录器的标识名字
    """

    basedir = os.path.dirname(pspath)
    try:
        os.mkdir(basedir)
    except:
        pass

    # 调整日志输出的级别名称.
    logging._levelToName[logging.ERROR] = 'ERR!'
    logging._levelToName[logging.WARNING] = 'WRN!'
    logging._levelToName[logging.DEBUG] = 'DBG.'

    # 生成指定名字标识的日志记录器
    ps_logger = logging.getLogger(tag)
    ps_logger.setLevel(logging.DEBUG)

    # 生成文件处理器
    if max_baks is not None:
        if isinstance(max_baks, int):
            max_bytes = 16 * 1024 * 1024
        elif isinstance(max_baks, tuple):
            max_bytes = max_baks[1] * 1024 * 1024
            max_baks = max_baks[0]
        filehandler = logging.handlers.RotatingFileHandler(pspath, encoding='utf-8', maxBytes=max_bytes,
                                                           backupCount=max_baks)
    else:
        filehandler = logging.handlers.WatchedFileHandler(pspath, encoding='utf-8')
    filehandler.setLevel(lvl)
    filehandler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    # 日志记录器绑定文件处理器
    ps_logger.addHandler(filehandler)
    return ps_logger


def make_logger2(outer, lvl=logging.DEBUG, tag=None):
    """根据给定的日志输出器,生成日志记录器;
        lvl:告知允许输出的日志级别
        tag为不同日志记录器的标识名字
    """

    # 调整日志输出的级别名称.
    logging._levelToName[logging.ERROR] = 'ERR!'
    logging._levelToName[logging.WARNING] = 'WRN!'
    logging._levelToName[logging.DEBUG] = 'DBG.'

    # 生成指定名字标识的日志记录器
    ps_logger = logging.getLogger(tag)
    ps_logger.setLevel(logging.DEBUG)

    # 给记录器绑定输出器
    outer.setLevel(lvl)
    outer.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
    ps_logger.addHandler(outer)
    return ps_logger


def bind_logger_console(lg, lvl=logging.ERROR):
    stm = logging.StreamHandler()
    stm.setLevel(lvl)
    stm.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
    lg.addHandler(stm)


def make_logger_console(lvl=logging.DEBUG):
    """生成控制台日志输出器;lvl:告知允许输出的日志级别"""
    # 调整日志输出的级别名称.
    logging._levelToName[logging.ERROR] = 'ERR!'
    logging._levelToName[logging.WARNING] = 'WRN!'
    logging._levelToName[logging.DEBUG] = 'DBG.'

    # 生成日志记录器
    ps_logger = logging.getLogger()
    ps_logger.setLevel(lvl)

    # 生成控制台输出器
    stm = logging.StreamHandler()
    stm.setLevel(lvl)
    stm.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))

    # 日志记录器绑定输出器
    ps_logger.addHandler(stm)
    return ps_logger


def adj_logger_stream(lg, lvl, stream_name='StreamHandler'):
    """调整日志记录器中指定输出流的输出级"""
    rc = 0
    for handler in lg.handlers:
        if type(handler).__name__ == stream_name:
            handler.setLevel(lvl)
            rc += 1
    return rc


def calc_paging(pages, cur, part=5):
    """计算翻页列表页号范围,总页数pages,当前页cur,当前页号两侧列表数part
        返回值:(begin,end)页号范围
    """
    pg_begin = max(1, cur - part)
    pg_end = min(pages, cur + part)
    if cur <= part:
        pg_end = min(pages, part * 2 + 1)
    if cur > pages - part:
        pg_begin = max(1, pages - part * 2)
    return pg_begin, pg_end


def json_default(obj):
    """自定义对象导出json时使用的default转换函数"""
    dst = {}
    dst.update(obj.__dict__)  # 将对象的内部词典导入到dst词典中,将对象的输出转换为对象内部数据的输出.

    keys = []
    keys.extend(dst.keys())  # 备份dst词典的全部key,避免下面被删除时无法访问

    for key in keys:  # 过滤dst的key,做有效性判断,无效结果不输出
        ov = dst[key]
        drop = False
        if ov is None:
            drop = True
        elif isinstance(ov, list) and len(ov) == 0:
            drop = True
        elif isinstance(ov, dict) and len(ov) == 0:
            drop = True

        if drop:
            del dst[key]  # 遍历dst,发现空值则删除对应的key

    return dst  # 返回处理后的结果


# -----------------------------------------------------------------------------
# 从json文件装载字典
def dict_load(fname, encoding=None, defval=None):
    try:
        fp = open(fname, 'r', encoding=encoding)
        ret = json.load(fp)
        fp.close()
        return ret
    except Exception as e:
        print(e)
        return defval


def dict_load2(fname, encoding=None, defval=None):
    try:
        fp = open(fname, 'r', encoding=encoding)
        ret = json.load(fp)
        fp.close()
        return ret, ''
    except Exception as e:
        return defval, str(e)


# 保存词典到文件
def dict_save(fname, dct, encoding=None):
    try:
        fp = open(fname, 'w', encoding=encoding)
        json.dump(dct, fp, indent=4, ensure_ascii=False)
        fp.close()
        return True
    except Exception as e:
        return False


def load_as_set(fname, encoding='utf-8', rst=None):
    """装载文件内容,每行作为一个元素,得到全部元素的集合.返回值:(set(),'')或(None,err)"""
    try:
        if rst is None:
            rst = set()
        fp = open(fname, 'r', encoding=encoding)
        for line in fp:
            rst.add(line[:-1] if line[-1] == '\n' else line)
        fp.close()
        return rst, ''
    except Exception as e:
        return None, e


def load_as_dict(fname, encoding='utf-8', rst=None, row_as_key=False):
    """装载文件内容,每行内容作为key,行号作为val.返回值:({},'')或(None,err)"""
    try:
        if rst is None:
            rst = {}
        fp = open(fname, 'r', encoding=encoding)
        row = 0
        for line in fp:
            row += 1
            txt = line[:-1] if line[-1] == '\n' else line
            if row_as_key:
                rst[row] = txt
            else:
                rst[txt] = row
        fp.close()
        return rst, ''
    except Exception as e:
        return None, e


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


def clean_blank_line(txt, dst='\n'):
    """删除文本中的空白行(只由空白和回车符构成的行)"""
    return re.sub(r'\n[\s\t]*\r?\n', dst, txt)


def clean_blank_str(txt):
    """删除文本中的空白内容(由空白和回车符构成的片段)"""
    return re.sub(r'[\r\n\s\t]+', '', txt)


def clean_xml_tags(xstr, tags=['em']):
    """清理删除指定的xml标签,tags为空,则清理全部标签."""
    ret = xstr.strip()  # 字符串两端净空
    if not tags:
        tags = ['[^<>]+']
    for tag in tags:
        exp = f'<{tag}(\s+[^>]*)?/>|<{tag}(\s+[^>]*)?>|</{tag}>'
        ret = re.sub(exp, '', ret)
    return ret


def remove_xml_tags(xstr, tags=['style', 'script']):
    """删除指定的xml标签与其内容"""
    ret = xstr.strip()  # 字符串两端净空
    ret = re.sub('<!--(.+)?-->', '', ret)  # 移除注释
    for tag in tags:
        exp = f'<{tag}(\s+[^>]*)?>.*?</{tag}>'
        ret = re.sub(exp, '', ret, flags=re.DOTALL)
    return ret


def cmp_file_extname(aname, bname, like=True):
    """比较两个文件的扩展名是否相同"""
    if aname is None:
        aname = ''
    if bname is None:
        bname = ''

    aes = aname.split('.')
    if '' in aes:
        aes.remove('')
    bes = bname.split('.')
    if '' in bes:
        bes.remove('')

    if len(aes) == 0 and len(bes) == 0:
        return False
    if len(aes) == 0 or len(bes) == 0:
        return False

    ae = aes[-1]
    be = bes[-1]
    if ae == be:
        return True  # 扩展名完全相同

    if not like:
        return False  # 不要求近似判断,则告知不相同

    def chk(a, b, exts):
        return a in exts and b in exts

    # 进行扩展名的近似判断
    if chk(ae, be, {'doc', 'docx'}):
        return True
    if chk(ae, be, {'xls', 'xlsx'}):
        return True
    if chk(ae, be, {'ppt', 'pptx'}):
        return True
    if chk(ae, be, {'jpg', 'jpeg'}):
        return True

    return False  # 近似判断未通过,则告知不相同


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

    def remain(self):
        """获知剩余等待秒数"""
        r = self.end - time.time()
        return 0 if r <= 0 else r


# 文件行输出器
class append_line_t:
    def __init__(self, fname=None, encoding='utf-8', append=True):
        if fname:
            self.open(fname, encoding, append)

    def open(self, fname, encoding='utf-8', append=True):
        try:
            mode = 'a' if append else 'w'
            self.fp = open(fname, mode, encoding=encoding)
            return ''
        except Exception as e:
            self.fp = None
            return es(e)

    def append(self, line=''):
        if isinstance(line, list):
            for l in line:
                if l.endswith('\n'):
                    self.fp.write(l)  # 不要输出额外的空行
                else:
                    self.fp.writelines([l, '\n'])  # 确保正确分行
            return len(line)
        else:
            self.fp.writelines([line, '\n'])
            return 1

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
    def __init__(self, fname=None, encoding='utf-8'):
        if fname:
            self.open(fname, encoding)

    def open(self, fname, encoding='utf-8'):
        try:
            self.fp = open(fname, 'r', encoding=encoding)
            self.fname = fname
            return ''
        except Exception as e:
            self.fp = None
            return es(e)

    def skip(self, lines=100):
        """跳过指定行数"""
        if not self.fp:
            return False

        for i in range(lines):
            l = self.fp.readline()
            if l == '': break
        return True

    def fetch(self, lines=100):
        """获取一批行数据"""
        if not self.fp:
            return []
        ret = []
        for i in range(lines):
            l = self.fp.readline()
            if l == '': break
            ret.append(l.rstrip())
        return ret

    def fetch_all(self):
        """获取全部行数据"""
        rst = []
        while True:
            lines = self.fetch(100)
            rst.extend(lines)
            if len(lines) < 100:
                break
        return rst

    def loop(self, cb, goto_head=False):
        """对全部行数据进行遍历调用"""
        if not self.fp:
            return 0
        if goto_head:
            self.fp.seek(0, 0)
        rc = 0
        while True:
            l = self.fp.readline()
            if l == '': break
            rc += 1
            if cb(l, rc):
                break

        return rc

    def close(self):
        """关闭"""
        if self.fp:
            self.fp.close()
            self.fp = None

    def __del__(self):
        self.close()


def conv_file_lines(infile, outfile, cbfunc, cbargs=None):
    """逐行读取infile内容,使用cbfunc处理后,再输出到outfile中.
        回调函数原型: cbfunc(line, idx, oldlines, *cbargs) -> newlines
        返回值:(oldlines,newlines)或errormsg
    """
    oldlines = 0
    newlines = 0

    # 打开读取器
    if isinstance(infile, read_lines_t):
        reader = infile
    else:
        reader = read_lines_t()
        msg = reader.open(infile)
        if msg:
            return msg

    # 打开输出器
    if isinstance(outfile, append_line_t):
        writer = outfile
    else:
        writer = append_line_t()
        msg = writer.open(outfile)
        if msg:
            return msg

    # 进行读取处理循环
    inlines = reader.fetch()
    while inlines:
        oldlines += len(inlines)
        for idx, line in enumerate(inlines):
            outlines = cbfunc(line, idx, oldlines, *cbargs)
            if outlines:
                newlines += writer.append(outlines)
        inlines = reader.fetch()

    writer.close()
    reader.close()
    return (oldlines, newlines)


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
    def __init__(self, keyIdx=None, sep=',', fname=None, mode='a+'):
        self.fp = None
        self.keys = set()
        self.keyIdx = keyIdx
        self.sep = sep
        self.name = None
        if fname:
            self.open(fname, mode=mode)

    def open(self, fname, encoding='utf-8', mode='a+'):
        if self.fp is not None:
            return True
        self.name = fname
        try:
            self.fp = open(fname, mode, encoding=encoding)
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
        if line is None:
            return -2
        line = line.strip()
        if line == '': return 0

        if self.sep:
            t = line.split(self.sep)
            return self.appendt(t)
        else:
            return self.appendt(line)

    def appendt(self, t):
        """追加(元组或字符串)内容到文件.返回值:-1文件未打开;-2其他错误;0内容为空;1内容重复;2正常完成."""
        if self.fp is None:
            return -1

        key = calc_key(t, self.keyIdx)
        if key in self.keys:
            return 1
        try:
            if isinstance(t, tuple):
                self.fp.write(self.sep.join(t) + '\n')
            else:
                if t[-1] != '\n':
                    self.fp.write(t + '\n')
                else:
                    self.fp.write(t)
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
        print(es(e))
        return False


def make_paths(filepath, last_is_file=True):
    """生成filepath路径依赖的所有父路径.
        last_is_file - 告知filepath最后一段是否为文件名(不用创建最后一段)
        返回值:'' - 正常;其他为错误信息
    """
    paths = re.split(r'[/\\]', filepath)
    if last_is_file:
        paths.pop(-1)
    try:
        os.makedirs(os.path.sep.join(paths), exist_ok=True)
        return ''
    except Exception as e:
        return ei(e)


# 保存指定内容到文件,同时创建不存在的层级目录
def save_to_file2(path, fname, strdata, encode='utf-8', mode='w'):
    try:
        os.makedirs(path.rstrip("\\").rstrip('/'))
    except Exception as e:
        pass
    return save_to_file(path + fname, strdata, encode, mode)


# -----------------------------------------------------------------------------
# 将数据保存到fn对应的文件中
def save_file(fn, data, encoding='utf-8'):
    try:
        if type(data).__name__ == 'str' and encoding:
            data = data.encode(encoding)
        f = open(fn, "wb+")
        f.write(data)
        f.close()
        return ''
    except Exception as e:
        return es(e)


def save_objs_csv(fn, objs, encoding='utf-8'):
    """保存对象列表到csv文件fn.返回值:错误消息,空串正常."""
    try:
        out = open(fn, 'w+', encoding=encoding)
        if len(objs):
            out.write(','.join(objs[0].keys()) + '\n')
            for d in objs:
                out.write(','.join(d.values()) + "\n")
        out.close()
        return ''
    except Exception as e:
        return es(e)


# 十六进制串转换为对应的字符
import binascii


def hexstr_to_chr(hex_str):
    """将hex字节数组或字符串转换为对应的文本串"""
    if isinstance(hex_str, str):
        hex = hex_str.encode('utf-8')
    else:
        hex = hex_str
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


def json2dict(jstr):
    try:
        dic = json.loads(jstr)
        return dic, ''
    except Exception as e:
        return None, 'json2dict: ' + es(e)


def dict2json(obj, indent=True, conv=json_default):
    try:
        jstr = json.dumps(obj, ensure_ascii=False, indent=4 if indent else None, default=conv)
        return jstr, ''
    except Exception as e:
        return None, 'dict2json: ' + es(e)


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
def get_datetime(dt=None, fmt='%Y-%m-%d %H:%M:%S'):
    """按指定格式,获取当前本地时间."""
    if dt is None:
        dt = time.localtime()
    return time.strftime(fmt, dt)


def get_curr_date(fmt='%Y-%m-%d', now=None):
    """按照指定格式得到当前本地日期(默认为ISO格式);可以取得微秒时间的格式为 '%Y-%m-%d %H:%M:%S.%f'"""
    if now is None:
        now = datetime.datetime.now()
    return now.strftime(fmt)


def adj_date_day(datestr, day, outfmt='%Y-%m-%d'):
    """对给定的本地日期串datestr进行天数day增减运算,得到新的日期,ISO串"""
    if not datestr:
        datestr = get_curr_date()
    date = datetime.datetime.strptime(datestr, '%Y-%m-%d')
    date += datetime.timedelta(days=day)
    return date.strftime(outfmt)


def date_to_utc(datestr):
    """将本地日期串转换为UTC时间秒"""
    return int(datetime.datetime.strptime(datestr, '%Y-%m-%d').timestamp())


def datetime_to_utc(datestr):
    """将本地日期串转换为UTC时间秒"""
    return int(datetime.datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S').timestamp())


def utc_to_datetime(sec):
    """把UTC秒转换为ISO标准本地时间串"""
    date = datetime.datetime.fromtimestamp(sec)
    return date.strftime('%Y-%m-%d %H:%M:%S')


def utc_to_date(sec):
    """把UTC秒转换为ISO标准本地日期串"""
    date = datetime.datetime.fromtimestamp(sec)
    return date.strftime('%Y-%m-%d')


def printf(fmt, *arg):
    """带有当前时间格式的打印输出"""
    print(f"[{get_datetime()}]", fmt % (*arg,))


def find_dcts(lst, value, key='name'):
    """在字典列表lst中查找指定key匹配value的条目索引"""
    for i in range(len(lst)):
        if lst[i][key] == value:
            return i
    return -1


def make_datedir(root='./files', make=True, fmt='%Y%m%d%H'):
    """用当前日期时间创建目录.返回值:完成时为路径串,错误时为None"""
    dt = ub.get_curr_date(fmt)
    path = f'{root}/{dt}'
    try:
        if make:
            os.makedirs(path)
        return path
    except FileExistsError:
        return path


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


class time_meter:
    """简单的间隔时间计量器"""

    def __init__(self):
        self._begin = time.time()

    def reset(self):
        self._begin = time.time()

    def use(self):
        end = time.time()
        ut = end - self._begin
        self._begin = end
        return ut

    def hit(self, timeout, msg=None):
        """判断use用时是否超过了timeout"""
        ut = self.use()
        self.reset()
        if ut > timeout and msg:
            printf(f"USE<{ut}>:{msg}")
            return True


def sleep(sec, delay=0.5, idle_cb=None, *cb_arg):
    """多次短时休眠,直到指定的时间结束.中间醒来时可以进行回调处理."""
    beg = time.time()
    while time.time() - beg < sec:
        time.sleep(delay)
        if idle_cb:
            idle_cb(*cb_arg)


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


def query_str(cnt_str, cc_str):
    """在cnt_str中查找cc_str出现的位置数组"""
    rst = []
    pos = cnt_str.find(cc_str)
    while pos != -1:
        rst.append(pos)
        begin = pos + len(cc_str)
        pos = cnt_str.find(cc_str, begin)
    return rst


# 查询指定捕获组的内容并转为数字.不成功时返回默认值
def query_re_num(cnt_str, cc_re, defval=1, numtype=int):
    rs, msg = query_re(cnt_str, cc_re)
    if len(rs) != 0 and rs[0] != '':
        return numtype(rs[0])
    return defval


# 查询指定捕获组的内容串.不成功时返回默认值
def query_re_str(cnt_str, cc_re, defval=None):
    rs, msg = query_re(cnt_str, cc_re)
    if len(rs) != 0:
        return rs[0]
    return defval


def adj_xml_desc(txt):
    """调整丢弃XML文本中描述节点的字符集编码声明"""
    txt = txt.replace("""<?xml version="1.0" encoding="utf-8"?>""", """<?xml version="1.0"?>""")
    txt = txt.replace("""<?xml version="1.0" encoding="UTF-8"?>""", """<?xml version="1.0"?>""")
    return txt


# -----------------------------------------------------------------------------
def is_html(txt):
    """判断给定的文本串是否可能为html文本"""
    tags = txt.count('</td')
    tags += txt.count('</tr')
    tags += txt.count('</div')
    tags += txt.count('</span')
    tags += txt.count('</table')
    tags += txt.count('<br')
    tags += txt.count('</p')
    tags += txt.count('</a')
    tags += txt.count('</li')
    if tags >= 2:
        return True
    if txt.count('<') >= 20:
        return True
    if txt.count('</') >= 10:
        return True
    return False


def save_top(rst, score, docid, top_limit=10):
    '按score的高低顺序将(score,docid)放入rst,rst超过limit数量后淘汰最后的值'
    loc = -1
    for i in range(len(rst)):
        r = rst[i]
        if score >= r[0]:
            rst.insert(i, (score, docid))
            loc = i
            break

    if loc == -1:
        rst.append((score, docid))
        loc = len(rst)

    if len(rst) > top_limit:
        rst.pop(-1)

    return loc != -1


def make_usage_html(title, txt, ver):
    """生成简单的使用说明的html页面"""

    def conv(s):
        return s.replace('<', '&lt;').replace(' ', '&ensp;').replace('\n', '<br>\n')

    tit = conv(title)
    usage = '''<html><title>%s</title><body>
&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;<b>%s(%s)</b>
    %s
    </body></html>''' % (tit, tit, conv(ver), conv(txt))
    return usage


def hash_number(x):
    """对数字x进行哈希计算"""
    x ^= x >> 17
    x *= 0xed5ad4bb
    x ^= x >> 11
    x *= 0xac4c1b51
    x ^= x >> 15
    x *= 0x31848bab
    x ^= x >> 14
    return x


def hash_string(v, bitsmask=(1 << 64) - 1):
    """基于字符集编码的字符串DEK Hash函数"""
    if not v:
        return 0
    x = len(v) * 378551
    for c in v:
        x = ((x << 5) ^ (x >> 27)) ^ ord(c)
    return x & bitsmask


def hash_string2(v, hashfunc=hash_number, bitsmask=(1 << 64) - 1):
    """字符串DEK Hash函数,可配置字符的哈希方式"""
    if not v:
        return 0
    x = len(v) * 378551
    for c in v:
        x = ((x << 5) ^ (x >> 27)) ^ hashfunc(ord(c))
    return x & bitsmask


def hash_route(v, dsts):
    """根据v的哈希值与目标dsts的数量,进行定向路由选取"""
    code = hash_string(v)
    return dsts[code % len(dsts)]


def kvcopy(src, dst):
    """将源对象src中的指定key的内容复制到目标dst中.可指定目标key为dstkey,否则与源key相同"""

    def cpy(key, dstkey=None):
        if dstkey is None:
            dstkey = key
        if key not in src:
            dst[dstkey] = ''
            return cpy
        dst[dstkey] = src[key]
        return cpy

    return cpy


def dict_path(dct, path, dv=None):
    """根据/k1[i1]/k2这样的简单路径提取dct中对应的值"""
    if not isinstance(dct, dict):
        raise Exception('dict_path param dct need dict object.')

    segs = path.split('/')
    if segs[-1] == '':
        segs.pop(-1)
    if segs[0] == '':
        segs.pop(0)

    for i, seg in enumerate(segs):
        if dct is None:
            return dv
        if seg[-1] == ']':
            rlst, msg = query_re(seg, '(.*?)\[(\d+)\]')
            if len(rlst) == 0:
                rlst, msg = query_re(seg, '(.*?)\[(.*?)\]')
                if len(rlst) == 0:
                    return dv
                rs = rlst[0]
            else:
                rs = rlst[0]
                rs = (rs[0], 0 if int(rs[1]) < 1 else int(rs[1]) - 1)

            try:
                if i == len(segs) - 1:
                    return dct[rs[0]][rs[1]]
                else:
                    dct = dct[rs[0]][rs[1]]
            except:
                return dv
        else:
            if i == len(segs) - 1:
                if isinstance(dct, dict):
                    return dct.get(seg, dv)
                else:
                    return dv
            else:
                dct = dct.get(seg, None)
    return dv


def jacard_sim(s1, s2):
    """对于集合或链表s1和s2,计算杰卡德相似度;返回值:(相同元素数,元素总数)"""
    s1 = set(s1)
    s2 = set(s2)
    il = len(s1.intersection(s2))
    ul = len(s1.union(s2))
    return il, ul


def jacard_ratio(s1, s2):
    """计算两个链表或集合的杰卡德相似度:0~1"""
    sc, tc = jacard_sim(s1, s2)
    if tc == 0:
        return 0
    return sc / tc


def take_file_size(fp):
    """获取指定文件对象的尺寸.返回值:size:int或Exception对象"""
    try:
        now = fp.tell()
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(now, 0)
        return size
    except Exception as e:
        return e


class eat_file_size:
    """文件数据读取增量记录器,与TQDM配合使用"""

    def __init__(self, fp):
        self.fp = fp
        self.reset()

    def reset(self, use_tell=False):
        """读取点记录归零"""
        self.pos = self.fp.tell() if use_tell else 0

    def total(self):
        return take_file_size(self.fp)

    def eat(self):
        """获取自上次调用以来,文件被读取的尺寸增量"""
        now = self.fp.tell()
        ret = now - self.pos
        self.pos = now
        return ret


def dict_reduce(main, data):
    """将data中的计数结果累积到main中"""
    for k in data:
        main[k] = main.get(k, 0) + data[k]


def text_file_sort(fname, mode=1, encoding='utf-8'):
    """对fname文件的内容排序,输出覆盖原文件.
        排序模式mode:
            1 - 字符串/升序
            2 - 字符串/降序
            3 - 字符串反读/升序
            4 - 字符串反读/降序
            5 - (长度,字符串)/升序
            6 - (长度,字符串)/降序
            7 - (长度,字符串反读)/升序
            8 - (长度,字符串反读)/降序
            mode为tuple的时候:(自定义key方法,是否逆序)
        返回值:''正常;其他为错误信息.
    """
    kf_str_f = lambda x: x
    kf_str_r = lambda x: x[::-1]
    kf_str_nf = lambda x: (len(x), x)
    kf_str_nr = lambda x: (len(x), x[::-1])
    func_keys = {1: (kf_str_f, False), 2: (kf_str_f, True),
                 3: (kf_str_r, False), 4: (kf_str_r, True),
                 5: (kf_str_nf, False), 6: (kf_str_nf, True),
                 7: (kf_str_nr, False), 8: (kf_str_nr, True)}
    try:
        if isinstance(mode, int):
            kf = func_keys[mode]
        else:
            kf = mode
        fp = open(fname, 'r', encoding=encoding)
        lines = fp.readlines()
        fp.close()
        if lines and lines[-1][-1] != '\n':
            lines[-1] = lines[-1] + '\n'
        res = sorted(lines, key=kf[0], reverse=kf[1])
        fp = open(fname, 'w', encoding=encoding)
        fp.writelines(res)
        fp.close()
        return ''
    except Exception as e:
        return ei(e)


def text_file_unrepeat(fname, encoding='utf-8', oname=None, cb=None):
    """对指定的文本文件按行进行排重处理"""
    try:
        fp = open(fname, 'r', encoding=encoding)
        lines = fp.readlines()
        fp.close()
        out = lines_writer(sep=None)
        if oname is None:
            oname = fname + '.out'
        if not out.open(oname, encoding, mode='w+'):
            return 'file open fail.'
        if cb is None:
            out.appendx(lines)
        else:
            for line in lines:
                txt = cb(line.strip())
                out.append(txt)
        return ''
    except Exception as e:
        return ei(e)


def text_file_loop(fname, encoding='utf-8', oname=None, cb=None):
    """对指定的文本文件fname按行调用cb进行处理后写入新文件oname
            def cb(line,rowno) 返回值为None时放弃当前行的输出
        返回值:空串正常.否则为错误信息.
    """
    try:
        fp = open(fname, 'r', encoding=encoding)
        lines = fp.readlines()
        fp.close()

        if oname is None:
            oname = fname + '.out'
        out = open(oname, 'w+', encoding=encoding)

        if cb is None:
            out.writelines(lines)
        else:
            for rowno, line in enumerate(lines):
                txt = cb(line.strip(), rowno)
                if txt is not None:
                    if not txt or txt[-1] != '\n':
                        out.write(txt + '\n')
                    else:
                        out.write(txt)
        return ''
    except Exception as e:
        return ei(e)


def inc(dct, key, cnt=1):
    """对指定字典key进行值累加.返回值:累加之前的旧值"""
    old = dct.get(key, 0)
    dct[key] = old + cnt
    return old


def text_file_drops(fname, xname, encoding='utf-8', oname=None):
    """删除fname文件中与xname文件内容相同的行.返回值:''正常,否则为错误信息"""
    try:
        exs, err = load_as_set(xname, encoding)
        if err:
            return err

        def cb(line):
            if line in exs:
                return ''
            return line

        return text_file_unrepeat(fname, encoding, oname, cb)
    except Exception as e:
        return ei(e)


def str_ins(txt, val, pos=None):
    """在txt串的pos位置前插入新值val.
        pos is None 则在末尾追加
        返回值:结果串
    """
    if pos is None:
        pos = len(txt)
    return f'{txt[:pos]}{val}{txt[pos:]}'


def str_add(txt, val, pos=None):
    """在txt串的pos位置后插入新值val.
        pos is None 则在头部追加
        返回值:结果串
    """
    if pos is None:
        return f'{val}{txt}'
    else:
        return f'{txt[:pos + 1]}{val}{txt[pos + 1:]}'


def take_dirs(path, dironly=False, toponly=False):
    """递归遍历path,查找文件或目录.
        dironly - 是否只记录目录名
        toponly - 是否只遍历顶级路径
        返回值:[(目录path,True),(文件path,False)]
    """
    rst = []

    for root, dirs, files in os.walk(path, topdown=True):
        for name in dirs:
            rst.append((os.path.join(root, name), True))
        if not dironly:
            for name in files:
                rst.append((os.path.join(root, name), False))
        if toponly:
            break
    return rst


def make_out_log(sfname, txt, row, col=0):
    """生成外部编辑器日志行结果"""
    return f'<{sfname}|{row:>8},{col:>2}>:{txt}'


def slen(seg):
    """计算seg段的长度"""
    return seg[1] - seg[0]
