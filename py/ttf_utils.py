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


# 保存数据到文件
def data2file(data, fname):
    f = open(fname, 'wb')
    f.write(data)
    f.close()


# 装载指定文件的内容
def loadfile(fname, mode='r'):
    f = open(fname, mode)
    rst = f.read()
    f.close()
    return rst


# 定义字体工具类
class ttf_utils:
    def __init__(self, fntStr):
        if fntStr is not None:
            # 将输入的base64编码的TTF数据,放入字节读取器
            infile = BytesIO(base64.decodebytes(fntStr))
            # 定义TTF字体解析器
            self.font = ttLib.TTFont(infile)

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


# 定义TTF字体信息提取功能类
class ttf_infos:
    def __init__(self, fntXml):
        self.xp = xpath(fntXml.encode('utf-8'))

    # 获取当前字体文件中的字符码列表
    def get_codes(self):
        names, err = self.xp.query('//GlyphOrder/GlyphID/@name')
        chars = []
        for n in names:
            if n.startswith('uni'):
                chars.append(int(n[3:], 16))
        return chars

    # 获取指定字符的绘图动作序列
    def get_glyph_txt(self, code, clean=False):
        name = 'uni%x' % code
        txt, err = self.xp.query('//CharStrings/CharString[@name="%s"]/text()' % name)
        if err != '':
            return ''

        if clean:
            return txt[0].replace('\n', '').replace(' ', '')
        else:
            return txt[0]

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


# 将字节数组val编码为base64串
def base64_b2s(val):
    ret = base64.encodebytes(val)
    return ret.decode('latin-1')


# 将base64字符串val解码得到原字节数组
def base64_s2b(val):
    ret = val.encode('latin-1')
    return base64.decodebytes(ret)


# 进行小字库字符串累计
class fnt_str_lib:
    def __init__(self):
        # 字形字典,记录每个字形md5与对应的字形图像
        self.libs = {}
        self.last_edited = 0

    def save(self, fname='ttf_libs.json', force=False):
        if self.last_edited == 0 and not force:
            return
        fp = open(fname, 'w', encoding='gb18030')
        json.dump(self.libs, fp, indent=4, ensure_ascii=False)
        fp.close()
        self.last_edited = 0

    def load(self, fname='ttf_libs.json'):
        try:
            fp = open(fname, 'r', encoding='gb18030')
            self.libs = json.load(fp)
            fp.close()
        except:
            pass

    def update(self, fntStr):
        key = hashlib.md5(fntStr).hexdigest()
        if key in self.libs:
            return
        self.libs[key] = fntStr.decode('latin-1')
        self.last_edited += 1

    def reduce(self):
        # 判断集合s中是否含有e中不包含的新元素
        def has_new(s, e):
            for i in s:
                if i not in e:
                    return True
            return False

        rem = []
        md5set = set()
        c = 0
        # 对字体库进行遍历
        for k in self.libs:
            c += 1
            # 得到字体信息
            ti = ttf_infos(base64ttf_to_xml(self.libs[k].encode('latin-1')))
            # 从字体信息中获取字形特征md5变为集合
            s = set(ti.get_glyphs_md5())
            # 当前字体集合与已有集合进行对比
            if has_new(s, md5set):
                # 含有新元素则进行合并
                md5set = md5set.union(s)
                print('has new - %d/%d' % (c, len(self.libs)))
            else:
                # 不含新元素则等待删除
                rem.append(k)
                print('repeat - %d/%d' % (c, len(self.libs)))

        for k in rem:
            del self.libs[k]
            self.last_edited += 1


# ttf字形查询管理器
class ttf_query_mgr:
    def __init__(self):
        # 字形字典,记录每个字形md5与对应的字形图像
        self.glyphs = {}

    def load(self, fname='ttf_glyph.json'):
        try:
            fp = open(fname, 'r', encoding='gb18030')
            self.glyphs = json.load(fp)
            fp.close()
            return True
        except Exception as e:
            return False

    # 追加字符串到文件
    def append_line(self,fname, dat):
        try:
            fp = open(fname, 'ab')
            fp.writelines([dat, b'\n'])
            fp.close()
            return True
        except Exception as e:
            return False

    # 给定字体串,查询里面含有的小字库字符集与标准字符集的对应关系
    def query(self, fntStr):
        if fntStr is None or fntStr == b'':
            return {}
        ti = ttf_infos(base64ttf_to_xml(fntStr))
        codes = ti.get_codes()
        rst = {}
        bads = 0
        for c in codes:
            k = ti.get_glyph_md5(c)
            c = '%x' % c
            if k in self.glyphs:
                rst[c] = self.glyphs[k]['w']
            else:
                rst[c] = '??'
                bads = bads + 1

        if bads != 0:
            self.append_line('bad_fnt_libs.txt', fntStr)
        return rst

    # 查询字体串,得到xml格式的对应关系
    def query_xml(self, fntStr):
        rst = self.query(fntStr)
        x = ['<root>']
        for k in rst:
            x.append('<code src="&amp;#x%s;" dst="%s"/>' % (k, rst[k]))
        x.append('</root>')
        return '\n'.join(x)


if __name__ == '__main__':
    fntStr = b'T1RUTwAJAIAAAwAQQ0ZGIFQqNmMAAAUEAAAUA09TLzJl2+DLAAABAAAAAGBjbWFwADIWRQAABAQAAADgaGVhZBSNva0AAACcAAAANmhoZWEA3wDTAAAA1AAAACRobXR4EAAAAAAAGQgAAAA0bWF4cAANUAAAAAD4AAAABm5hbWUKXYQxAAABYAAAAqNwb3N0AAMAAAAABOQAAAAgAAEAAAABAAAStir1Xw889QADAQAAAAAA2jw/gQAAAADaPD+BAAb/4QD4ANIAAAADAAIAAAAAAAAAAQAAAN3/xQAAAQAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAA0AAFAAAA0AAAADAQAB9AAFAAACigK7AAAAjAKKArsAAAHfADEBAgAAAAAAAAAAAAAAAIAAAAEAAAAAAAAAAAAAAABYWFhYAEAA2ADjAN3/xQAAANIAHwAAAAEAAAAAAG8A0gAAAAAAAAAAACIBngABAAAAAAAAAAEAQgABAAAAAAABAAwAAAABAAAAAAACAAYAJAABAAAAAAADABUAxgABAAAAAAAEABMANgABAAAAAAAFAAsApQABAAAAAAAGABIAbwABAAAAAAAHAAEAQgABAAAAAAAIAAEAQgABAAAAAAAJAAEAQgABAAAAAAAKAAEAQgABAAAAAAALAAEAQgABAAAAAAAMAAEAQgABAAAAAAANAAEAQgABAAAAAAAOAAEAQgABAAAAAAAQAAwAAAABAAAAAAARAAYAJAADAAEECQAAAAIAYQADAAEECQABABgADAADAAEECQACAAwAKgADAAEECQADACoA2wADAAEECQAEACYASQADAAEECQAFABYAsAADAAEECQAGACQAgQADAAEECQAHAAIAYQADAAEECQAIAAIAYQADAAEECQAJAAIAYQADAAEECQAKAAIAYQADAAEECQALAAIAYQADAAEECQAMAAIAYQADAAEECQANAAIAYQADAAEECQAOAAIAYQADAAEECQAQABgADAADAAEECQARAAwAKk9wZW5UeXBlU2FucwBPAHAAZQBuAFQAeQBwAGUAUwBhAG4Ac01lZGl1bQBNAGUAZABpAHUAbU9wZW5UeXBlU2FucyBNZWRpdW0ATwBwAGUAbgBUAHkAcABlAFMAYQBuAHMAIABNAGUAZABpAHUAbU9wZW5UeXBlU2Fuc01lZGl1bQBPAHAAZQBuAFQAeQBwAGUAUwBhAG4AcwBNAGUAZABpAHUAbVZlcnNpb24gMC4xAFYAZQByAHMAaQBvAG4AIAAwAC4AMSA6T3BlblR5cGVTYW5zIE1lZGl1bQAgADoATwBwAGUAbgBUAHkAcABlAFMAYQBuAHMAIABNAGUAZABpAHUAbQAAAAACAAMAAQAAABQAAwAKAAAANAAEACAAAAAEAAQAAQAAAAD//wAAAAD//wAAAAEAAAAAAAwAAAAAAKwAAAAAAAAADQAAAAAAAAAAAAAAAAABANgAAQDYAAAAAQABANkAAQDZAAAAAgABANoAAQDaAAAAAwABANsAAQDbAAAABAABANwAAQDcAAAABQABAN0AAQDdAAAABgABAN4AAQDeAAAABwABAN8AAQDfAAAACAABAOAAAQDgAAAACQABAOEAAQDhAAAACgABAOIAAQDiAAAACwABAOMAAQDjAAAADAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAEAQABAQETT3BlblR5cGVTYW5zTWVkaXVtAAEBAT/4GwD4HAL4HQP4HgSLbPdx95QFHQAAAQQPHQAAAR0Rix0AABQDEh4KADkGJf8eDx4PHgoAOQYl/x4PHg8MBwAQAQEMHysxOUFJUVlhaXF5gYmRVmVyc2lvbiAwLjFPcGVuVHlwZVNhbnMgTWVkaXVtT3BlblR5cGVTYW5zTWVkaXVtdW5pMTAwZDh1bmkxMDBkOXVuaTEwMGRhdW5pMTAwZGJ1bmkxMDBkY3VuaTEwMGRkdW5pMTAwZGV1bmkxMDBkZnVuaTEwMGUwdW5pMTAwZTF1bmkxMDBlMnVuaTEwMGUzAAAAAYsBjAGNAY4BjwGQAZEBkgGTAZQBlQGWAA0CAAEABALwBIYGBgejCeoLEwxtDeUO8BDjEbsSyPqUDveU7aoVi4sFi7sFoIEFzosFlZcFoH0FjIuLioqKCIuLBYODBYtuBYtyi3qMggiLiwWGh4SJgooIi4sFi54FQYsFi38FhoaFiYSLCIuLBYyUi5+Lqgj3CPIVlpoFn3kFiokFW4sFlXScfKODCIuLBYqHBYKLhYeIhAiLiwV4ln6fhKgIi4sFiIsFhnF4eGp+CIuLBYmOBaOcmZ2PnwiLiwWGiwWBiQWKjgWKiQVqiwWKiIqIiogIi4sFk4iSiJGHCIuLBY+IjYiLiAiLiwWKhIiGhokIi4sFiYuJjYmPCIuLBYiThpKFkgiLiwWEeXp7cH0Ii4sFiY4Fo5+Zn4+eCIuLBXuLBYGKBYiSBamLBY2UjJWLlgiLiwV8iwWBigWIkgWniwWMjouOi44Ii4sFi6gFooEFjIqLioqKCIuLBYSFBYuABYuIi4iLiAiLiwWQiwWUlgWbfAWKiQVuiwWLgIqBiYIIi4sFkYsFlJgFnXsFiY4Fn4sFjZSMlYuWCIuLBYGLBYKKBYiRBaKLBYuQi5CLkAiLiwWLpQWigQWLi4uLjIsIi4sFjIqLioqKCIuLBYSGBYuDBYuGi4aLhgiLiwWaiwWVmQWeegWKiQVfiwWLgIqBiYIIi4sFpIsF+0ZBFbHuBZCJBXAvBYiBiYOLhQiLiwWLhIyBjX4Ii4sFjYCMhIuHCIuLBYqEiYeHigiLiwWEjIWOhpAIi4sFi4uLi4uMCIuLBYqMi4yMjAiLiwWNmIyYi5gIi4sFjJSEknuPCIuLBYyOBZCLkIuRigiLiwWQi46NjZAIi4sF9y5qFUGLBYtsBdWLBYuqBYuRFYuoBUGLBYtuBdWLBfs59zkVjY0FmYaVhpGGCIuLBZGHjoeKhwiLiwWKgoiFhokIi4sFiIqJjYqQCIuLBYaWg5aAlwiLiwV4WRWNjgWYhpWFk4UIi4sFj4iNiIuHCIuLBYqCh4WFiAiLiwWIi4mNiZAIi4sFiJeEl4CWCIuLBQ73lPdn9xgVmJoFoXgFiogFLYsFfV0FxosFlpgFoXoFjIqLioqKCIuLBYCEBYh2iHiIegiLiwWJeH1/cYcIi4sFioqKi4uMCIuLBYyWgJR1kgiLiwWMjwWvhQWWiZGPjZYIi4sFkJ6On42gCIuLBU6LBYGBBXuYBYqMi4yMiwiLiwWSkQWWtAVziwV+igWIkwX3DYsF+zlDFbj3AwWQiQVrIgWGfomDjIgIi4sFjIGMgYyCCIuLBY2AjIOLhgiLiwWLhImIhosIi4sFg4yFjoeQCIuLBYqMi42LjQiLiwWNl4yYi5kIi4sFjJSDkXqOCIuLBYuOBZKMkYuRigiLiwWQio6OjJEIi4sF9yj3ExWYmgWieAWKiAX7AYsFf4oFiJMF5IsF+0tiFY2NBZaHloaWhQiLiwWQiI2Hi4YIi4sFioGHhYSJCIuLBYiLiY2JkAiLiwWGmIOXgJYIi4sFoMEVjI0FmYiWhpSFCIuLBZCIjYeLhgiLiwWKgoeFhYkIi4sFiYuJjYmPCIuLBYWYg5aAlQiLiwUO95T3XfdQFZeaBaJ4BYmJBfsEiwWCf4GBgIIIi4sFjIsF3IsFlZcFn34FjIqLioqLCIuLBYODBYuEBYt+i4CMgQiLiwWGh4WJg4oIi4sFi5kFM4sFi4EFhYeEiYSLCIuLBYyUi5qLoAiLiwV5f3iBdoIIi4sFiY8FsaKppKClCIuLBU2LBX2JBYiTBfdJiwVM+wAVizEFjIODhHqGCIuLBYmKioyKjQiLiwWLlYOSeo8Ii4sFjI8Fo4kFkomOjoqUCIuLBYvrBaaABYyKi4qKigiLiwWGhwWQf5GAkYIIi4sFnJabmJqZCIuLBZt3BYyJioqJiwiLiwWGjISJg4YIi4sFhoiBhnyECIuLBYmKiYqKigiLiwWZd6d8tYAIi4sFiocFfoyDhoiBCIuLBVycb6yCuwiLiwWyqxWLrAUziwWLagXjiwUsXhWVlgWeegWMi4uKiooIi4sFgYYFeGhtc2J+CIuLBYmOBayfpKWbqgiLiwVdiwWAiQWIkwXGiwUO95T3YuQVmZ0FpHYFiogFK4sFomSscreBCIuLBYqHBX6KgoaHggiLiwVknnCqfLYIi4sFh4sFi24Fi2mLcox7CIuLBYeIhImAigiLiwWLkouUjJcIi4sFjKSLnYuVCIuLBYuYBXBoZ29fdgiLiwWJjwWxpKurpbIIi4sFQIsFfYoFiJIF9IsFi6sFpYAFjIqMi4uLCIuLBYuLioqKigiLiwWEhgWLfgXQiwWH9wcVi4sFmngFjImLioqLCIuLBYSNg4uCiQiLiwVWhlaIVYoIi4sFio8FwJC6krSTCIuLBYyLjYuOjAiLiwWUjZONko4Igm0Vi4sFonoFjIqLiomLCIuLBYaKhoiHhgiLiwWCgH5+en0Ii4sFiI4FlZqTmZGYCIuLBY+TjpKNkQj7JHoVjY0FloWVhZOECIuLBZCHjYeLhgiLiwWJgoaFhIgIi4sFiYuJjomQCIuLBYiZhZiClwiLiwXJmBWNjQWWhJOEkYQIi4sFj4iNh4uGCIuLBYmBhoWEigiLiwWIi4mOi5AIi4sFiZmGmYSYCIuLBQ73lPdq9ykVi4sFRYsFgHJ/d358CIuLBYiNBZqplqiSpwiLiwWOlY2VjJQIi4sFpX8FjIqMioyKCIuLBYqKiouKiwiLiwWFiIaFiIIIi4sFiomKiImGCIuLBYqHioiKiAiLiwXKiwWUmgWhewWMiouKiooIi4sFgYMFi1eJYYhrCIuLBYt0f3xyhAiLiwWKioqLi4wIi4sFi5aAlHSSCIuLBYyPBamGBZqIk5KMnAiLiwWOqI22jMQI+xL7ARWL9x4FWosFi/seBYaGhYmEiwiLiwWMkouUi5YIi4sFi5SLnIukCIuLBYvgBaCABbSLBZSYBZ99BYyKi4qKigiLiwWChAWL+xIFhoeGiYWKCIuLBXruFYtnBYtuiXaIfgiLiwWcgpeCk4IIi4sFj4iNh4uGCIuLBYqDh4aEiAiLiwWIi4mNiY8Ii4sFhpqDmX+ZCIuLBYZ1eXdteAiLiwWJjwWenJeckJsIi4sFkZuOpYuuCIuLBYvABaKABY2Ki4qJigiLiwWEhQXoVBWNjgWafpV/kYAIi4sFjYiMh4uHCIuLBYqCh4aEiQiLiwWIi4mOipAIi4sFi4yLjYqOCIuLBYuNi42KjAiLiwWJioiKh4oIi4sFgomBiIGHCIuLBYWJhomHiAiLiwWKioqLiowIi4sFgJ0Fko2QkI+SCIuLBZObkpuQmwiLiwWOko2TjJMIi4sFo30FjIqLiomKCIuLBYaKh4eIhQiLiwWAdoB4gHsIi4sFk4yajaCOCIuLBYiWh5aGlgiLiwUO95T3Y6sVmZwFpHYFiokF+26LBX2JBYiTBcCLBYv3EgWhgAWmiwWNpAVBiwV9iQWIkwXmiwWNqwWlgAWMi4uKiooIi4sFgoQFin8Fz4sFmJsFoXcFiokFJYsFiXIFsIsFlZgFoXwFjIuLioqKCIuLBYKDBYskBZyLBWeiFTGLBYt0BeWLBYuiBYuoFTGLBYt0BeWLBYuiBYunFTGLBYt0BeWLBYuiBYuRFYuiBTGLBYt0BeWLBWsgFY2OBaaKpIaiggiLiwWSiY+HjIUIi4sFioKIhoaKCIuLBYiLiIyJjQiLiwV4mnSXb5QIi4sFX5MVi4sFoXkFjIqLiouKCIuLBYuKiouKiwiLiwWGjIWKhIgIi4sFb35wgnGGCIuLBYmPBbGappqbmggO95T3YIQVl5wFo3YFiYkF+2GLBX2JBYiTBfCLBYvOBVqLBX2JBYeTBfcRiwWYmwWhdwWKiQVEiwWLSAXNiwUr92oVjI0Fl4eUhpKGCIuLBZCIjoeLhwiLiwWKgoaFg4gIi4sF2YsFl5cFoHcFjIqLioqLCIuLBX+JBW51BYiNBZilBfs1iwWLdoWAf4oIi4sFhIyHjoqQCIuLBYuOjI2OjQiLiwWXkpKXjZwIi4sFjosFi4qLioyKCIuLBYyIi4eLhwiLiwXbiwWIi4mNipAIi4sFiJeGloOVCIuLBX5NFYuLBaB5BYyKi4qKigiLiwWLioqLiosIi4sFh4yGiYaHCIuLBXN2b3psfgiLiwWKjwWknKCcnJ0Ii4sFkpKQko6RCLqBFY2PBaeCooGegAiLiwWSh46Gi4UIi4sFioKIhoaJCIuLBYmLiYyIjgiLiwV6oHWdcJoIi4sFDveU9yr3HxWLiwWNjgWhg56Bmn8Ii4sFkoeOhouECIuLBYqBiIWFigiLiwWJi4mNiI8Ii4sFiY+Ij4iPCIuLBYGLgIqAigiLiwWLOgWKf5CGlowIi4sFrosFlIqQkIyVCIuLBZOvBY6LBYxoBYyEjoaQiQiLiwWGfoKFfowIi4sFV4sFeoqClIudCIuLBYviBWqIBYlkhHB+fQiLiwWAfHJ+ZIAIi4sFiY4Fw5+msYjDCIuLBYSKhIqFiwiLiwWKi4qLiYoIi4sFhYqHiYiJCIuLBYqKiouLjAiLiwWDnwWUjJKOkJAIi4sFnZqanJeeCIuLBT6LBX6JBYiTBfcHiwWJi4mNio4Ii4sFiJeFloKVCIuLBY2NBZWIlYaVhQiLiwWQiI2IiogIi4sFioKHhoSJCIuLBdeLBZibBaJ3BYqJBfsYiwWffAWMiouKiooIi4sFiIuGiYSHCIuLBXp8e398gQiLiwW2i7OMsI0Ii4sFgZd/l3yWCA73lPcH9zEVi74Fp38FjIqMi4uLCIuLBYuKioqKigiLiwWCgwWLbwXAiwWVmQWgewWMi4uKiooIi4sFgoMFi2AFi4aLgIx6CIuLBYt8i4KLhwiLiwWGh4WJg4sIi4sFi5kFUosFi2cFin6QhZeMCIuLBcKLBZaKkpCNlQiLiwWSsQWPigWNaAWLhI6GkYgIi4sFh36ChXyLCIuLBTqLBXuKg5SMngiLiwWLtgVTiwWLewWFhoSJhIsIi4sFjJiLpYuxCIuLBYvMBaB/BcGLBddTFVKLBYteBcSLBYu4BT+LFVOLBYteBcOLBYu4BdeSFYu2BVKLBYtgBcSLBT+2FVOLBYtgBcOLBYu2BQ73lMX3ChWNjQWTiJKHkYYIi4sFkIiNiIuHCIuLBYqFiIeFiAiLiwWmiwWSmJCXj5cIi4sFn34FjIqLioqKCIuLBYeLiImIiAiLiwWGhoaGhoYIi4sFposFlpkFoHoFiogFSosFi3MFpIsFlpkFn3oFiokFVIsFi4EFi3sFtosFl5oFoXkFiogFP4sFi36Lfox9CIuLBYeGhImCiwiLiwWLmoubjJsIi4sFUIsFf4oFiJIF1YsFi5cFi5kFaIsFf4kFiJIFvYsFi6MFXIsFf4oFiJIFu4sFiYyKjIqNCIuLBYmWh5SEkwiLiwX3IYwVi3UFi1uSbJl8CIuLBYyKjIqMiwiLiwWMjIyMjIwIi4sFl60FjooFiGcFiYKNg5GDCIuLBYmIiIqHiwiLiwV+jH+UgJwIi4sFgKGFrIu4CIuLBYukBfsOiwWAigWIkgX3GYsFlZcFn30FjIqLioqKCIuLBYKEBY7IFZiaBaF5BYmIBfs5iwV6cXl1d3kIi4sFiI4FnaKapJamCIuLBY2QjZGNkgiLiwWMjoyNjIwIi4sFo38FjIqLioqKCIuLBYuLiouKigiLiwWHioiIiIcIi4sFioqKiYqJCIuLBYqKi4qLigiLiwX3FYsFcnMVlpgFn3oFiYkF+xSLBYGKBYiSBfcEiwUO95T3SuEVi38FjGaYcaR9CIuLBY6KjYyMjgiLiwWWsQWOigWKaAWKgo6DkoUIi4sFiIiHiYaLCIuLBVyRcq6IywiLiwWLmQX7CosFgIoFiJMF9xSLBZWYBaJ8BYyKi4qKigiLiwWCgwWY3xWZnAWjdgWKiQX7NYsFfHB3dHN4CIuLBYiOBaClnKeYqgiLiwWQlo6TjJAIi4sFo30FjYqLioiLCIuLBYaJh4iJhgiLiwWJh4iHiIYIi4sF9w2LBXBnFZibBaF4BYqIBfsUiwWBigWIkgX2iwUO95T3LfcFFYvqBah+BYyKi4qKiQiLiwWChQWLQwWxiwWZnAWhdwWKiQVCiwWLgAWLgot7i3MIi4sFjGyLdIt8CIuLBYiIhImAigiLiwWMoou0i8cIi4sFi5cFWosFfokFiJIFzIsFNTMVsKsFjogFfHh9eX56CIuLBYmJiYiJhwiLiwWKiYqKiooIi4sFi4qLioqKCIuLBYuLiouKjAiLiwV8nQWRkI6Ri5MIi4sFi+UFc4sFgIkFiJMFrosFlZkFoXwFjIqLioqKCIuLBYGDBYs6BWv3RBWNjAWZhZeElYMIi4sFjomNh4uFCIuLBYqCh4WEiAiLiwWIi4mNio8Ii4sFiJiDmn6cCIuLBQ4ABAAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAA=='

    qm = ttf_query_mgr()
    qm.load()
    r = qm.query(fntStr)
    print(r)
