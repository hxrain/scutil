import os
from io import *

'''
这里提供了两种调用tesseract OCR功能的方法:
1 ocr_tess
    创建exe进程,使用磁盘文件做输入输出.性能较低且会干扰磁盘,但ocr进程崩溃不会导致主进程异常.
2 ocr_capi
    调用dll接口,在内存中传递参数做输入输出.性能较好不会干扰磁盘,但ocr进程崩溃会导致主进程异常.
对外提供了统一的调用接口
    ocr(img, oneword=False)
默认使用进程模式,若想使用api模式,则需要调用方法:
    enable_ocr_capi
'''
# ------------------------------------------------------------------------------
import pytesseract as tess
from PIL import Image

# 设置pytesseract需要的环境变量，告知tess库的位置
tess.pytesseract.tesseract_cmd = 'd:/Tesseract-OCR/tesseract.exe'
# 设置tess库需要的环境变量，控制并发线程数量
os.putenv('OMP_THREAD_LIMIT', '8')
os.putenv('OMP_NUM_THREADS', '8')


# 调用ocr识别文字,img为图像文件的字节数据
def ocr_tess(img, oneword=False):
    image = Image.open(BytesIO(img))
    cfg = ''
    if oneword:
        cfg = '--psm 8 --oem 0'
    return tess.image_to_string(image, lang='chi_sim', config=cfg)


# ------------------------------------------------------------------------------
import pyocr
import pyocr.builders

# 设置pyocr需要的环境变量，告知tess库的位置
os.putenv('TESSDATA_PREFIX', r"D:\Tesseract-OCR\tessdata")
os.putenv('TESSBIN_PREFIX', r"D:\Tesseract-OCR\libtesseract-5.dll")
# 定义pyocr库需要的全局变量，准备进行pyocr的初始化
pyocr_tool = None
pyocr_lang = None


# 开启capi模式的ocr调用接口
def enable_ocr_capi():
    global pyocr_tool
    global pyocr_lang
    tools = pyocr.get_available_tools()
    pyocr_tool = tools[1]
    langs = pyocr_tool.get_available_languages()
    pyocr_lang = langs[0]


# 调用ocr识别文字,img为图像文件的字节数据
def ocr_capi(img, oneword=False):
    image = Image.open(BytesIO(img))
    if oneword:
        bp = pyocr.builders.TextBuilder(tesseract_layout=8)
    else:
        bp = pyocr.builders.TextBuilder()

    return pyocr_tool.image_to_string(image, lang=pyocr_lang, builder=bp)


# ------------------------------------------------------------------------------
# 进行图像ocr调用的功能封装,img为图像文件的字节数据
def ocr(img, oneword=False):
    if pyocr_lang is None:
        return ocr_tess(img, oneword)
    else:
        return ocr_capi(img, oneword)


# 进行图像ocr调用的功能封装,fname为图像文件的路径
def ocr_img(fname, oneword=False):
    fp = open(fname, 'rb')
    img = fp.read()
    fp.close()
    if pyocr_lang is None:
        return ocr_tess(img, oneword)
    else:
        return ocr_capi(img, oneword)

