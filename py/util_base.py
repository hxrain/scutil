import logging
import logging.handlers
import datetime
import os
import json
import re
import time
from xml.dom import minidom


# -----------------------------------------------------------------------------
# 生成指定路径的日志记录器
def make_logger(pspath, lvl=logging.DEBUG, max_baks=None):
    basedir = os.path.dirname(pspath)
    try:
        os.mkdir(basedir)
    except:
        pass

        # 调整日志输出的级别名称.
    logging._levelToName[logging.ERROR] = 'ERR!'
    logging._levelToName[logging.WARNING] = 'WRN!'
    logging._levelToName[logging.DEBUG] = 'DBG.'

    # 生成日志记录器
    ps_logger = logging.getLogger()
    ps_logger.setLevel(logging.DEBUG)

    # 生成文件处理器
    if max_baks:
        filehandler = logging.handlers.RotatingFileHandler(pspath, encoding='utf-8', maxBytes=1024 * 1024, backupCount=max_baks)
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


def clean_blank_line(txt):
    """删除文本中的空白行(只由空白和回车符构成的行)"""
    return re.sub(r'\n[\s\t]*\r?\n', '\n', txt)


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
