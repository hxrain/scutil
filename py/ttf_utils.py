# -*- coding: utf-8 -*-

import base64
import hashlib
import json
from io import *

import fontTools.ttLib as ttLib
from lxml import etree


# 可进行多次xpath查询的功能对象
class xpath:
    def __init__(self, cntstr):
        self.rootNode = etree.XML(cntstr)
        self.cnt_str = cntstr

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


# 定义字体工具类
class ttf_utils:
    def __init__(self, fntBase64=None):
        if fntBase64 is not None:
            self.parse(base64.decodebytes(fntBase64))

    def parse(self, fntdata):
        """解析字体数据内容"""
        self.font = ttLib.TTFont(BytesIO(fntdata))

    def open(self, fname):
        self.font = ttLib.TTFont(fname)

    def export_xml(self):
        # 定义输出字符串缓冲区
        out = StringIO()
        # 将解析后的TTF内容转为XML格式并输出到缓冲区
        self.font.saveXML(out)
        # 得到解析后的结果
        out.seek(0)
        return out.read()


# 解析base64编码的ttf数据并得到xml格式串
def base64ttf_to_xml(fnt):
    f = ttf_utils(fnt)
    return f.export_xml()


# 解析ttf文件并导出xml格式串
def filettf_to_xml(fname):
    f = ttf_utils(None)
    f.open(fname)
    return f.export_xml()


# 解析base64编码的ttf数据并得到xml格式串
def datattf_to_xml(fntData):
    f = ttf_utils()
    f.parse(fntData)
    return f.export_xml()


class ttf_infos:
    """定义TTF字体信息提取功能类"""

    def __init__(self, fntXml):
        self.xp = xpath(fntXml.encode('utf-8'))

    # 获取当前字体文件中的字符码列表
    def get_codes(self):
        names, err = self.xp.query('//GlyphOrder/GlyphID/@name')
        chars = []
        for n in names:
            if n.startswith('uni'):
                chars.append(int(n[3:], 16))
            else:
                chars.append(str(n))
        return chars

    # 获取指定字符的绘图动作序列
    def get_glyph_txt(self, code, clean=False):
        if isinstance(code, int):
            name = f'uni%x' % code
        else:
            name = code
        txt, err = self.xp.query('//CharStrings/CharString[@name="%s"]/text()' % name)
        if err != '':
            return ''

        if clean:
            return txt[0].replace('\n', '').replace(' ', '')
        else:
            return txt[0]

    def get_related_chars(self, code):
        """获取code字符编码的别名编码"""
        els, err = self.xp.query('//cmap/cmap_format_12/map[@name="uni%x"]' % code)
        if err != '':
            return []
        codes = []
        for e in els:
            codes.append(int(e.attrib['code'], 16))
        return codes

    # 获取指定字符的图像动作序列的md5值
    def get_glyph_md5(self, code):
        txt = self.get_glyph_txt(code, True)
        if txt == '':
            return ''
        return hashlib.md5(txt.encode('utf-8')).hexdigest()

    # 获取全部字形的md5特征码
    def get_glyphs_md5(self):
        rst = []
        for c in self.get_codes():
            rst.append(self.get_glyph_md5(c))
        return rst


class woff_infos(ttf_infos):
    """定义WOFF字体信息提取功能类"""

    def __init__(self, fntXml):
        super().__init__(fntXml)

    def get_related_chars(self, code):
        """获取code字符编码的别名编码"""
        els, err = self.xp.query('//cmap/cmap_format_4/map[@name="uni%X"]' % code)
        if err != '':
            return []
        codes = []
        for e in els:
            codes.append(int(e.attrib['code'], 16))
        return codes

    # 获取指定字符的绘图动作序列
    def get_glyph_txt(self, code, clean=False):
        if isinstance(code, int):
            name = f'uni%X' % code
        else:
            name = code
        els, err = self.xp.query('//glyf/TTGlyph[@name="%s"]/contour' % name)
        if err != '':
            return ''

        txts = []
        for e in els:
            txts.append(etree.tostring(e, encoding='unicode'))

        if clean:
            return ''.join(txts).replace('\n', '').replace(' ', '')
        else:
            return ''.join(txts)


def make_sample_lib(infos, libName):
    """根据给定的字体库,生成对应的映射样本库"""
    codes = infos.get_codes()
    out = {}
    for n, c in enumerate(codes):
        md5 = infos.get_glyph_md5(c)
        out[md5] = {'n': n + 1, 'w': hex(c) if isinstance(c, int) else c}
    with open(libName, "w") as filedata:
        json.dump(out, filedata, ensure_ascii=False, indent=4)
