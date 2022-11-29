# -*- coding: utf-8 -*-

from ttf_utils import *

import wx
from fontTools.pens.wxPen import WxPen
from io import *
import os
from tess_ocr import *
from PIL import Image

# 初始化ocr环境
tess_init_env()
G_OCR = tess_ocr()
G_OCR.open('chi_sim', OcrEngineMode.OEM_TESSERACT_ONLY)


def ocr_close():
    G_OCR.close()


# 封装一个简单的cor调用接口

def ocr(data):
    image = Image.open(BytesIO(data))
    r = G_OCR.rec_img(image, PageSegMode.SINGLE_WORD, 96)
    return r


# 字形图像导出功能类
class ttf_img:
    def __init__(self):
        # 绘图器需要的承载位图
        self.bitmap = wx.Bitmap(38, 38, 24)
        # 使用内存设备上下文
        self.dc = wx.MemoryDC(self.bitmap)
        self.dc.SetBackground(wx.Brush("white"))
        # 创建矢量绘图引擎
        self.gc = wx.GraphicsRenderer.GetDefaultRenderer().CreateContext(self.dc)
        self.gc.SetPen(wx.Pen("black", 1))
        self.gc.SetBrush(wx.Brush("black"))
        # 调整矢量字形的输出位置和大小
        self.gc.Translate(0, 32)
        self.gc.Scale(0.15, -0.15)

    # 绑定字形集合对象
    def bind_glyphs(self, glyphs):
        self.glyphs = glyphs

    # 导出指定字符的字形图像png数据
    def export_png(self, code):
        # 根据字符编码得到字形对象
        name = 'uni%x' % code
        glyph = self.glyphs[name]

        # 创建字形绘笔并绘制字形
        pen = WxPen(self.glyphs)
        glyph.draw(pen)

        # 将字形绘笔再次绘制到位图对象
        self.dc.Clear()
        self.gc.DrawPath(pen.path)

        # 位图对象中转为png图像并取出完整数据
        img = self.bitmap.ConvertToImage()
        out = BytesIO()
        img.SaveFile(out, wx.BITMAP_TYPE_PNG)
        out.seek(0)
        return out.read()

    # 导出指定字符的字形图像png文件
    def export_img(self, code, name, path='./glyph'):
        fname = '%s/%s.png' % (path, name)
        data2file(self.export_png(code), fname)

    def close(self):
        self.gc.Destroy()
        self.dc.Destroy()
        self.bitmap.Destroy()
        self.gc = None
        self.dc = None
        self.bitmap = None
        self.glyphs = None

# 定义字体字形管理器
class ttf_glyph_mgr:
    def __init__(self):
        # 字形字典,记录每个字形md5与对应的字形图像
        self.glyphs = {}
        self.app = wx.App()
        self.tp = ttf_img()
        self.last_edited = 0

    def save(self, fname='ttf_glyph.json', force=False):
        if self.last_edited == 0 and not force:
            return
        fp = open(fname, 'w',encoding='gb18030')
        json.dump(self.glyphs, fp, indent=4, ensure_ascii=False)
        fp.close()
        self.last_edited = 0

    def load(self, fname='ttf_glyph.json'):
        try:
            fp = open(fname, 'r',encoding='gb18030')
            self.glyphs = json.load(fp)
            fp.close()
            return True
        except Exception as e:
            return False

    def close(self):
        self.tp.close()
        self.app.Destroy()

    # 更新处理一个字体串,进行字库累积;使用字体中的字形md5作为字库中的key
    def update(self, fntStr, withocr=True):
        rc = 0
        try:
            # 字体工具
            tu = ttf_utils(fntStr)
            # 字体信息
            ti = ttf_infos(tu.export_xml())
            # 字形输出器绑定字形对象数组
            self.tp.bind_glyphs(tu.font.getGlyphSet())
            # 使用字形信息对象获取字符代码列表进行循环
            for c in ti.get_codes():
                # 根据字体代码得到字形md5作为唯一key
                key = ti.get_glyph_md5(c)
                if key in self.glyphs:
                    continue
                # 导出每个字符的字形图像数据
                data = self.tp.export_png(c)
                w = ocr(data) if withocr else ''
                if withocr:
                    print(w)
                # 字库累积,字形md5为key,记录识别结果w和对应的字形图像数据的base64串img
                self.glyphs[key] = {'n': len(self.glyphs) + 1, 'w': w, 'f': 0, 'img': base64_b2s(data)}
                self.last_edited += 1
                rc += 1
        except Exception as e:
            print(e)

        return rc

    # 使用OCR引擎重新识别图像文字,用于OCR参数调优之后
    def redo_ocr(self):
        for k in self.glyphs:
            g = self.glyphs[k]
            if g['f'] == 1:
                continue
            data = base64_s2b(g['img'])
            w = ocr(data)
            if g['w'] != w:
                print('redo ocr %s => %s' % (g['w'], w))
                g['w'] = w
                self.last_edited += 1

    # 得到指定key对应的字形图像数据
    def get_img(self, key):
        if key not in self.glyphs:
            return b''
        data = self.glyphs[key]['img']
        return base64_s2b(data)

    # 导出指定key对应的字形图像到文件
    def export_img(self, key, fname):
        data = self.get_img(key)
        if data == b'':
            return
        data2file(data, fname)

    # 识别指定key对应的字形图像得到文字
    def get_ocr_word(self, key):
        data = self.get_img(key)
        if data == '':
            return
        return ocr(data)

    # 导出小字库的字形图像为HTML文件,便于校对
    def export_html(self, fname='cnfont.html'):
        fp = open(fname, 'w',encoding='gb18030')
        rst = []
        cols = 20
        rst.append('<html><body>')
        rst.append('<table border="1">')
        remain = len(self.glyphs)
        line = []
        for k in self.glyphs:
            line.append(self.glyphs[k])
            remain -= 1
            if len(line) == cols or remain == 0:
                rst.append('<tr><td><hr style="height:1px;border:none;border-top:1px solid #555555;" /></td></tr>')
                # 输出序号行
                rst.append('<tr>')
                for g in line:
                    rst.append('<td align="center" >%d</td>' % (g['n']))
                rst.append('</tr>')

                # 输出图像行
                rst.append('<tr>')
                for g in line:
                    rst.append('<td align="center">')
                    rst.append('<img src="data:image/png;base64,%s"/>' % g['img'])
                    rst.append('</td>')
                rst.append('</tr>')

                # 输出对应文字行
                rst.append('<tr>')
                for g in line:
                    bgcolor = 'LightSkyBlue' if g['f'] != 0 else ''
                    rst.append('<td align="center" bgcolor="%s">%s</td>' % (bgcolor, g['w']))
                rst.append('</tr>')

                line = []

        rst.append('</table>')
        rst.append('</body></html>')
        fp.write('\n'.join(rst))
        fp.close()


if __name__ == '__main__':
    #潜 污 泵 采 购 真 空 充 电 氧 气 计
    fntStr = b'T1RUTwAJAIAAAwAQQ0ZGIFQqNmMAAAUEAAAUA09TLzJl2+DLAAABAAAAAGBjbWFwADIWRQAABAQAAADgaGVhZBSNva0AAACcAAAANmhoZWEA3wDTAAAA1AAAACRobXR4EAAAAAAAGQgAAAA0bWF4cAANUAAAAAD4AAAABm5hbWUKXYQxAAABYAAAAqNwb3N0AAMAAAAABOQAAAAgAAEAAAABAAAStir1Xw889QADAQAAAAAA2jw/gQAAAADaPD+BAAb/4QD4ANIAAAADAAIAAAAAAAAAAQAAAN3/xQAAAQAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAA0AAFAAAA0AAAADAQAB9AAFAAACigK7AAAAjAKKArsAAAHfADEBAgAAAAAAAAAAAAAAAIAAAAEAAAAAAAAAAAAAAABYWFhYAEAA2ADjAN3/xQAAANIAHwAAAAEAAAAAAG8A0gAAAAAAAAAAACIBngABAAAAAAAAAAEAQgABAAAAAAABAAwAAAABAAAAAAACAAYAJAABAAAAAAADABUAxgABAAAAAAAEABMANgABAAAAAAAFAAsApQABAAAAAAAGABIAbwABAAAAAAAHAAEAQgABAAAAAAAIAAEAQgABAAAAAAAJAAEAQgABAAAAAAAKAAEAQgABAAAAAAALAAEAQgABAAAAAAAMAAEAQgABAAAAAAANAAEAQgABAAAAAAAOAAEAQgABAAAAAAAQAAwAAAABAAAAAAARAAYAJAADAAEECQAAAAIAYQADAAEECQABABgADAADAAEECQACAAwAKgADAAEECQADACoA2wADAAEECQAEACYASQADAAEECQAFABYAsAADAAEECQAGACQAgQADAAEECQAHAAIAYQADAAEECQAIAAIAYQADAAEECQAJAAIAYQADAAEECQAKAAIAYQADAAEECQALAAIAYQADAAEECQAMAAIAYQADAAEECQANAAIAYQADAAEECQAOAAIAYQADAAEECQAQABgADAADAAEECQARAAwAKk9wZW5UeXBlU2FucwBPAHAAZQBuAFQAeQBwAGUAUwBhAG4Ac01lZGl1bQBNAGUAZABpAHUAbU9wZW5UeXBlU2FucyBNZWRpdW0ATwBwAGUAbgBUAHkAcABlAFMAYQBuAHMAIABNAGUAZABpAHUAbU9wZW5UeXBlU2Fuc01lZGl1bQBPAHAAZQBuAFQAeQBwAGUAUwBhAG4AcwBNAGUAZABpAHUAbVZlcnNpb24gMC4xAFYAZQByAHMAaQBvAG4AIAAwAC4AMSA6T3BlblR5cGVTYW5zIE1lZGl1bQAgADoATwBwAGUAbgBUAHkAcABlAFMAYQBuAHMAIABNAGUAZABpAHUAbQAAAAACAAMAAQAAABQAAwAKAAAANAAEACAAAAAEAAQAAQAAAAD//wAAAAD//wAAAAEAAAAAAAwAAAAAAKwAAAAAAAAADQAAAAAAAAAAAAAAAAABANgAAQDYAAAAAQABANkAAQDZAAAAAgABANoAAQDaAAAAAwABANsAAQDbAAAABAABANwAAQDcAAAABQABAN0AAQDdAAAABgABAN4AAQDeAAAABwABAN8AAQDfAAAACAABAOAAAQDgAAAACQABAOEAAQDhAAAACgABAOIAAQDiAAAACwABAOMAAQDjAAAADAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAEAQABAQETT3BlblR5cGVTYW5zTWVkaXVtAAEBAT/4GwD4HAL4HQP4HgSLbPdx95QFHQAAAQQPHQAAAR0Rix0AABQDEh4KADkGJf8eDx4PHgoAOQYl/x4PHg8MBwAQAQEMHysxOUFJUVlhaXF5gYmRVmVyc2lvbiAwLjFPcGVuVHlwZVNhbnMgTWVkaXVtT3BlblR5cGVTYW5zTWVkaXVtdW5pMTAwZDh1bmkxMDBkOXVuaTEwMGRhdW5pMTAwZGJ1bmkxMDBkY3VuaTEwMGRkdW5pMTAwZGV1bmkxMDBkZnVuaTEwMGUwdW5pMTAwZTF1bmkxMDBlMnVuaTEwMGUzAAAAAYsBjAGNAY4BjwGQAZEBkgGTAZQBlQGWAA0CAAEABALwBIYGBgejCeoLEwxtDeUO8BDjEbsSyPqUDveU7aoVi4sFi7sFoIEFzosFlZcFoH0FjIuLioqKCIuLBYODBYtuBYtyi3qMggiLiwWGh4SJgooIi4sFi54FQYsFi38FhoaFiYSLCIuLBYyUi5+Lqgj3CPIVlpoFn3kFiokFW4sFlXScfKODCIuLBYqHBYKLhYeIhAiLiwV4ln6fhKgIi4sFiIsFhnF4eGp+CIuLBYmOBaOcmZ2PnwiLiwWGiwWBiQWKjgWKiQVqiwWKiIqIiogIi4sFk4iSiJGHCIuLBY+IjYiLiAiLiwWKhIiGhokIi4sFiYuJjYmPCIuLBYiThpKFkgiLiwWEeXp7cH0Ii4sFiY4Fo5+Zn4+eCIuLBXuLBYGKBYiSBamLBY2UjJWLlgiLiwV8iwWBigWIkgWniwWMjouOi44Ii4sFi6gFooEFjIqLioqKCIuLBYSFBYuABYuIi4iLiAiLiwWQiwWUlgWbfAWKiQVuiwWLgIqBiYIIi4sFkYsFlJgFnXsFiY4Fn4sFjZSMlYuWCIuLBYGLBYKKBYiRBaKLBYuQi5CLkAiLiwWLpQWigQWLi4uLjIsIi4sFjIqLioqKCIuLBYSGBYuDBYuGi4aLhgiLiwWaiwWVmQWeegWKiQVfiwWLgIqBiYIIi4sFpIsF+0ZBFbHuBZCJBXAvBYiBiYOLhQiLiwWLhIyBjX4Ii4sFjYCMhIuHCIuLBYqEiYeHigiLiwWEjIWOhpAIi4sFi4uLi4uMCIuLBYqMi4yMjAiLiwWNmIyYi5gIi4sFjJSEknuPCIuLBYyOBZCLkIuRigiLiwWQi46NjZAIi4sF9y5qFUGLBYtsBdWLBYuqBYuRFYuoBUGLBYtuBdWLBfs59zkVjY0FmYaVhpGGCIuLBZGHjoeKhwiLiwWKgoiFhokIi4sFiIqJjYqQCIuLBYaWg5aAlwiLiwV4WRWNjgWYhpWFk4UIi4sFj4iNiIuHCIuLBYqCh4WFiAiLiwWIi4mNiZAIi4sFiJeEl4CWCIuLBQ73lPdn9xgVmJoFoXgFiogFLYsFfV0FxosFlpgFoXoFjIqLioqKCIuLBYCEBYh2iHiIegiLiwWJeH1/cYcIi4sFioqKi4uMCIuLBYyWgJR1kgiLiwWMjwWvhQWWiZGPjZYIi4sFkJ6On42gCIuLBU6LBYGBBXuYBYqMi4yMiwiLiwWSkQWWtAVziwV+igWIkwX3DYsF+zlDFbj3AwWQiQVrIgWGfomDjIgIi4sFjIGMgYyCCIuLBY2AjIOLhgiLiwWLhImIhosIi4sFg4yFjoeQCIuLBYqMi42LjQiLiwWNl4yYi5kIi4sFjJSDkXqOCIuLBYuOBZKMkYuRigiLiwWQio6OjJEIi4sF9yj3ExWYmgWieAWKiAX7AYsFf4oFiJMF5IsF+0tiFY2NBZaHloaWhQiLiwWQiI2Hi4YIi4sFioGHhYSJCIuLBYiLiY2JkAiLiwWGmIOXgJYIi4sFoMEVjI0FmYiWhpSFCIuLBZCIjYeLhgiLiwWKgoeFhYkIi4sFiYuJjYmPCIuLBYWYg5aAlQiLiwUO95T3XfdQFZeaBaJ4BYmJBfsEiwWCf4GBgIIIi4sFjIsF3IsFlZcFn34FjIqLioqLCIuLBYODBYuEBYt+i4CMgQiLiwWGh4WJg4oIi4sFi5kFM4sFi4EFhYeEiYSLCIuLBYyUi5qLoAiLiwV5f3iBdoIIi4sFiY8FsaKppKClCIuLBU2LBX2JBYiTBfdJiwVM+wAVizEFjIODhHqGCIuLBYmKioyKjQiLiwWLlYOSeo8Ii4sFjI8Fo4kFkomOjoqUCIuLBYvrBaaABYyKi4qKigiLiwWGhwWQf5GAkYIIi4sFnJabmJqZCIuLBZt3BYyJioqJiwiLiwWGjISJg4YIi4sFhoiBhnyECIuLBYmKiYqKigiLiwWZd6d8tYAIi4sFiocFfoyDhoiBCIuLBVycb6yCuwiLiwWyqxWLrAUziwWLagXjiwUsXhWVlgWeegWMi4uKiooIi4sFgYYFeGhtc2J+CIuLBYmOBayfpKWbqgiLiwVdiwWAiQWIkwXGiwUO95T3YuQVmZ0FpHYFiogFK4sFomSscreBCIuLBYqHBX6KgoaHggiLiwVknnCqfLYIi4sFh4sFi24Fi2mLcox7CIuLBYeIhImAigiLiwWLkouUjJcIi4sFjKSLnYuVCIuLBYuYBXBoZ29fdgiLiwWJjwWxpKurpbIIi4sFQIsFfYoFiJIF9IsFi6sFpYAFjIqMi4uLCIuLBYuLioqKigiLiwWEhgWLfgXQiwWH9wcVi4sFmngFjImLioqLCIuLBYSNg4uCiQiLiwVWhlaIVYoIi4sFio8FwJC6krSTCIuLBYyLjYuOjAiLiwWUjZONko4Igm0Vi4sFonoFjIqLiomLCIuLBYaKhoiHhgiLiwWCgH5+en0Ii4sFiI4FlZqTmZGYCIuLBY+TjpKNkQj7JHoVjY0FloWVhZOECIuLBZCHjYeLhgiLiwWJgoaFhIgIi4sFiYuJjomQCIuLBYiZhZiClwiLiwXJmBWNjQWWhJOEkYQIi4sFj4iNh4uGCIuLBYmBhoWEigiLiwWIi4mOi5AIi4sFiZmGmYSYCIuLBQ73lPdq9ykVi4sFRYsFgHJ/d358CIuLBYiNBZqplqiSpwiLiwWOlY2VjJQIi4sFpX8FjIqMioyKCIuLBYqKiouKiwiLiwWFiIaFiIIIi4sFiomKiImGCIuLBYqHioiKiAiLiwXKiwWUmgWhewWMiouKiooIi4sFgYMFi1eJYYhrCIuLBYt0f3xyhAiLiwWKioqLi4wIi4sFi5aAlHSSCIuLBYyPBamGBZqIk5KMnAiLiwWOqI22jMQI+xL7ARWL9x4FWosFi/seBYaGhYmEiwiLiwWMkouUi5YIi4sFi5SLnIukCIuLBYvgBaCABbSLBZSYBZ99BYyKi4qKigiLiwWChAWL+xIFhoeGiYWKCIuLBXruFYtnBYtuiXaIfgiLiwWcgpeCk4IIi4sFj4iNh4uGCIuLBYqDh4aEiAiLiwWIi4mNiY8Ii4sFhpqDmX+ZCIuLBYZ1eXdteAiLiwWJjwWenJeckJsIi4sFkZuOpYuuCIuLBYvABaKABY2Ki4qJigiLiwWEhQXoVBWNjgWafpV/kYAIi4sFjYiMh4uHCIuLBYqCh4aEiQiLiwWIi4mOipAIi4sFi4yLjYqOCIuLBYuNi42KjAiLiwWJioiKh4oIi4sFgomBiIGHCIuLBYWJhomHiAiLiwWKioqLiowIi4sFgJ0Fko2QkI+SCIuLBZObkpuQmwiLiwWOko2TjJMIi4sFo30FjIqLiomKCIuLBYaKh4eIhQiLiwWAdoB4gHsIi4sFk4yajaCOCIuLBYiWh5aGlgiLiwUO95T3Y6sVmZwFpHYFiokF+26LBX2JBYiTBcCLBYv3EgWhgAWmiwWNpAVBiwV9iQWIkwXmiwWNqwWlgAWMi4uKiooIi4sFgoQFin8Fz4sFmJsFoXcFiokFJYsFiXIFsIsFlZgFoXwFjIuLioqKCIuLBYKDBYskBZyLBWeiFTGLBYt0BeWLBYuiBYuoFTGLBYt0BeWLBYuiBYunFTGLBYt0BeWLBYuiBYuRFYuiBTGLBYt0BeWLBWsgFY2OBaaKpIaiggiLiwWSiY+HjIUIi4sFioKIhoaKCIuLBYiLiIyJjQiLiwV4mnSXb5QIi4sFX5MVi4sFoXkFjIqLiouKCIuLBYuKiouKiwiLiwWGjIWKhIgIi4sFb35wgnGGCIuLBYmPBbGappqbmggO95T3YIQVl5wFo3YFiYkF+2GLBX2JBYiTBfCLBYvOBVqLBX2JBYeTBfcRiwWYmwWhdwWKiQVEiwWLSAXNiwUr92oVjI0Fl4eUhpKGCIuLBZCIjoeLhwiLiwWKgoaFg4gIi4sF2YsFl5cFoHcFjIqLioqLCIuLBX+JBW51BYiNBZilBfs1iwWLdoWAf4oIi4sFhIyHjoqQCIuLBYuOjI2OjQiLiwWXkpKXjZwIi4sFjosFi4qLioyKCIuLBYyIi4eLhwiLiwXbiwWIi4mNipAIi4sFiJeGloOVCIuLBX5NFYuLBaB5BYyKi4qKigiLiwWLioqLiosIi4sFh4yGiYaHCIuLBXN2b3psfgiLiwWKjwWknKCcnJ0Ii4sFkpKQko6RCLqBFY2PBaeCooGegAiLiwWSh46Gi4UIi4sFioKIhoaJCIuLBYmLiYyIjgiLiwV6oHWdcJoIi4sFDveU9yr3HxWLiwWNjgWhg56Bmn8Ii4sFkoeOhouECIuLBYqBiIWFigiLiwWJi4mNiI8Ii4sFiY+Ij4iPCIuLBYGLgIqAigiLiwWLOgWKf5CGlowIi4sFrosFlIqQkIyVCIuLBZOvBY6LBYxoBYyEjoaQiQiLiwWGfoKFfowIi4sFV4sFeoqClIudCIuLBYviBWqIBYlkhHB+fQiLiwWAfHJ+ZIAIi4sFiY4Fw5+msYjDCIuLBYSKhIqFiwiLiwWKi4qLiYoIi4sFhYqHiYiJCIuLBYqKiouLjAiLiwWDnwWUjJKOkJAIi4sFnZqanJeeCIuLBT6LBX6JBYiTBfcHiwWJi4mNio4Ii4sFiJeFloKVCIuLBY2NBZWIlYaVhQiLiwWQiI2IiogIi4sFioKHhoSJCIuLBdeLBZibBaJ3BYqJBfsYiwWffAWMiouKiooIi4sFiIuGiYSHCIuLBXp8e398gQiLiwW2i7OMsI0Ii4sFgZd/l3yWCA73lPcH9zEVi74Fp38FjIqMi4uLCIuLBYuKioqKigiLiwWCgwWLbwXAiwWVmQWgewWMi4uKiooIi4sFgoMFi2AFi4aLgIx6CIuLBYt8i4KLhwiLiwWGh4WJg4sIi4sFi5kFUosFi2cFin6QhZeMCIuLBcKLBZaKkpCNlQiLiwWSsQWPigWNaAWLhI6GkYgIi4sFh36ChXyLCIuLBTqLBXuKg5SMngiLiwWLtgVTiwWLewWFhoSJhIsIi4sFjJiLpYuxCIuLBYvMBaB/BcGLBddTFVKLBYteBcSLBYu4BT+LFVOLBYteBcOLBYu4BdeSFYu2BVKLBYtgBcSLBT+2FVOLBYtgBcOLBYu2BQ73lMX3ChWNjQWTiJKHkYYIi4sFkIiNiIuHCIuLBYqFiIeFiAiLiwWmiwWSmJCXj5cIi4sFn34FjIqLioqKCIuLBYeLiImIiAiLiwWGhoaGhoYIi4sFposFlpkFoHoFiogFSosFi3MFpIsFlpkFn3oFiokFVIsFi4EFi3sFtosFl5oFoXkFiogFP4sFi36Lfox9CIuLBYeGhImCiwiLiwWLmoubjJsIi4sFUIsFf4oFiJIF1YsFi5cFi5kFaIsFf4kFiJIFvYsFi6MFXIsFf4oFiJIFu4sFiYyKjIqNCIuLBYmWh5SEkwiLiwX3IYwVi3UFi1uSbJl8CIuLBYyKjIqMiwiLiwWMjIyMjIwIi4sFl60FjooFiGcFiYKNg5GDCIuLBYmIiIqHiwiLiwV+jH+UgJwIi4sFgKGFrIu4CIuLBYukBfsOiwWAigWIkgX3GYsFlZcFn30FjIqLioqKCIuLBYKEBY7IFZiaBaF5BYmIBfs5iwV6cXl1d3kIi4sFiI4FnaKapJamCIuLBY2QjZGNkgiLiwWMjoyNjIwIi4sFo38FjIqLioqKCIuLBYuLiouKigiLiwWHioiIiIcIi4sFioqKiYqJCIuLBYqKi4qLigiLiwX3FYsFcnMVlpgFn3oFiYkF+xSLBYGKBYiSBfcEiwUO95T3SuEVi38FjGaYcaR9CIuLBY6KjYyMjgiLiwWWsQWOigWKaAWKgo6DkoUIi4sFiIiHiYaLCIuLBVyRcq6IywiLiwWLmQX7CosFgIoFiJMF9xSLBZWYBaJ8BYyKi4qKigiLiwWCgwWY3xWZnAWjdgWKiQX7NYsFfHB3dHN4CIuLBYiOBaClnKeYqgiLiwWQlo6TjJAIi4sFo30FjYqLioiLCIuLBYaJh4iJhgiLiwWJh4iHiIYIi4sF9w2LBXBnFZibBaF4BYqIBfsUiwWBigWIkgX2iwUO95T3LfcFFYvqBah+BYyKi4qKiQiLiwWChQWLQwWxiwWZnAWhdwWKiQVCiwWLgAWLgot7i3MIi4sFjGyLdIt8CIuLBYiIhImAigiLiwWMoou0i8cIi4sFi5cFWosFfokFiJIFzIsFNTMVsKsFjogFfHh9eX56CIuLBYmJiYiJhwiLiwWKiYqKiooIi4sFi4qLioqKCIuLBYuLiouKjAiLiwV8nQWRkI6Ri5MIi4sFi+UFc4sFgIkFiJMFrosFlZkFoXwFjIqLioqKCIuLBYGDBYs6BWv3RBWNjAWZhZeElYMIi4sFjomNh4uFCIuLBYqCh4WEiAiLiwWIi4mNio8Ii4sFiJiDmn6cCIuLBQ4ABAAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAA=='
    def test_make_glyphs_img():
        app = wx.App()
        # 字体工具
        tu = ttf_utils(fntStr)
        # 字体信息
        ti = ttf_infos(tu.export_xml())
        data2file(ti.xp.cnt_str,'qian_0x6f5c.xml')
        # 字体图像
        tp = ttf_img()

        # 获取指定字符代码对应的字形绘制动作文本
        print(ti.get_glyph_txt(0x100d8))
        # 获取指定字符代码对应的字形绘制动作文本对应的MD5值
        print(ti.get_glyph_md5(65753))
        # 字符代码列表
        print(ti.get_codes())

        # 创建字形图像输出目录
        if not os.path.exists('glyph'):
            os.mkdir('glyph')

        # 字形输出器绑定字形对象数组
        tp.bind_glyphs(tu.font.getGlyphSet())
        # 使用字形信息对象获取字符代码列表进行循环
        for c in ti.get_codes():
            # 导出每个字符的字形图像
            tp.export_img(c, ti.get_glyph_md5(c))
        # 必须要关闭字形输出器,否则会导致进程崩溃
        tp.close()

        app.Destroy()

    #print('0x%x'%ord('潜'))
    #test_make_glyphs_img()
    # ================================================================

    # 定义ttf字形管理器
    tm = ttf_glyph_mgr()
    # 装载已经积累的小字库
    tm.load()
    # 用新的字体小字体更新
    tm.update(fntStr)
    # 保存最新结果
    tm.save()
    # tm.export_img(ti.get_glyph_md5(65753), 'tst.png')
    # print(tm.get_ocr_word(ti.get_glyph_md5(65753)))
    # 重新进行ocr识别,更新非人工校准的文字
    # tm.redo_ocr()
    # tm.save()
    # 导出html页面,便于人工分析
    tm.export_html('qian_0x6f5c.html')
    # 关闭字形管理器
    tm.close()
    ocr_close()

    # 进行字体样本库的收缩
    # sl = fnt_str_lib()
    # sl.load()
    # sl.reduce()
    # sl.save()
