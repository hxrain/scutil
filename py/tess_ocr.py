import ctypes

# 默认图像的DPI,70是最小值
DPI_DEFAULT = 70


# OEM识别引擎的模式
class OcrEngineMode(object):
    OEM_TESSERACT_ONLY = 0
    OEM_LSTM_ONLY = 1
    OEM_TESSERACT_LSTM_COMBINED = 2
    OEM_DEFAULT = 3


# PSM页面分段模式,3默认,8单字
class PageSegMode(object):
    OSD_ONLY = 0
    AUTO_OSD = 1
    AUTO_ONLY = 2
    AUTO = 3
    SINGLE_COLUMN = 4
    SINGLE_BLOCK_VERT_TEXT = 5
    SINGLE_BLOCK = 6
    SINGLE_LINE = 7
    SINGLE_WORD = 8
    CIRCLE_WORD = 9
    SINGLE_CHAR = 10
    SPARSE_TEXT = 11
    SPARSE_TEXT_OSD = 12
    PSM_RAW_LINE = 13
    COUNT = 14


# TESS库的模型数据文件所在路径
TESSDATA_PREFIX = r"D:\Tesseract-OCR\tessdata"
# TESS库的DLL文件路径
TESSCAPI_DLL = r'D:\Tesseract-OCR\libtesseract-5.dll'
DLL = None


# 装载DLL,初始化配置API调用模式
def tess_init_env(libname=TESSCAPI_DLL):
    try:
        global DLL
        if DLL is not None:
            return ''

        DLL = ctypes.cdll.LoadLibrary(libname)

        DLL.TessVersion.argtypes = []
        DLL.TessVersion.restype = ctypes.c_char_p

        DLL.TessBaseAPICreate.argtypes = []
        DLL.TessBaseAPICreate.restype = ctypes.c_void_p  # TessBaseAPI*
        DLL.TessBaseAPIDelete.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
        ]
        DLL.TessBaseAPIDelete.argtypes = None

        DLL.TessBaseAPIInit1.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.c_char_p,  # datapath
            ctypes.c_char_p,  # language
            ctypes.c_int,  # TessOcrEngineMode
            ctypes.POINTER(ctypes.c_char_p),  # configs
            ctypes.c_int,  # configs_size
        ]
        DLL.TessBaseAPIInit1.restype = ctypes.c_int

        DLL.TessBaseAPISetSourceResolution.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.c_int,  # PPI
        ]

        DLL.TessBaseAPISetSourceResolution.restype = None

        DLL.TessBaseAPISetVariable.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.c_char_p,  # name
            ctypes.c_char_p,  # value
        ]
        DLL.TessBaseAPISetVariable.restype = ctypes.c_bool

        DLL.TessBaseAPISetPageSegMode.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.c_int,  # See PageSegMode
        ]
        DLL.TessBaseAPISetPageSegMode.restype = None

        DLL.TessBaseAPISetImage.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.POINTER(ctypes.c_char),  # imagedata
            ctypes.c_int,  # width
            ctypes.c_int,  # height
            ctypes.c_int,  # bytes_per_pixel
            ctypes.c_int,  # bytes_per_line
        ]
        DLL.TessBaseAPISetImage.restype = None

        DLL.TessBaseAPIRecognize.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.c_void_p,  # ETEXT_DESC*
        ]
        DLL.TessBaseAPIRecognize.restype = ctypes.c_int

        DLL.TessBaseAPIGetUTF8Text.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
        ]
        DLL.TessBaseAPIGetUTF8Text.restype = ctypes.c_void_p

        DLL.TessDeleteText.argtypes = [
            ctypes.c_void_p
        ]
        DLL.TessDeleteText.restype = None

        return ''
    except OSError as ex:  # pragma: no cover
        if hasattr(ex, 'message'):
            # python 2
            return ex.message
        else:
            # python 3
            return str(ex)


# 初始化tess识别器,得到句柄.之后所有的调用都基于此句柄
def tess_init(lang, OEM=OcrEngineMode.OEM_DEFAULT, datapath=TESSDATA_PREFIX):
    assert (DLL)

    handle = DLL.TessBaseAPICreate()
    try:
        lang = lang.encode("utf-8")
        prefix = datapath.encode("utf-8")
        DLL.TessBaseAPIInit1(
            ctypes.c_void_p(handle),
            ctypes.c_char_p(prefix),
            ctypes.c_char_p(lang),
            ctypes.c_int(OEM),  # TessOcrEngineMode 使用基础引擎
            ctypes.c_char_p(0),  # configs** 串指针数组
            ctypes.c_int(0)  # configs_size 数组长度
        )
        DLL.TessBaseAPISetVariable(
            ctypes.c_void_p(handle),
            b"tessedit_zero_rejection",
            b"F"
        )
    except:  # noqa: E722
        DLL.TessBaseAPIDelete(ctypes.c_void_p(handle))
        raise
    return handle


# 释放tess识别器
def tess_uninit(handle):
    assert (DLL)
    DLL.TessBaseAPIDelete(ctypes.c_void_p(handle))


def get_version():
    assert (DLL)
    return DLL.TessVersion().decode("utf-8")


# 设置可识别字符白名单
def set_char_whitelist(handle, wl=None):
    assert (DLL)

    if wl is None:
        wl = b"0123456789."

    DLL.TessBaseAPISetVariable(
        ctypes.c_void_p(handle),
        b"tessedit_char_whitelist",
        wl
    )


# 设置tess的页面模式
def set_page_seg_mode(handle, mode):
    assert (DLL)

    DLL.TessBaseAPISetPageSegMode(
        ctypes.c_void_p(handle), ctypes.c_int(mode)
    )


# 绑定待识别的图像数据
def bind_image(handle, image, default_dpi=DPI_DEFAULT):
    assert (DLL)

    image = image.convert("RGB")
    image.load()
    imgdata = image.tobytes("raw", "RGB")

    DLL.TessBaseAPISetImage(
        ctypes.c_void_p(handle),
        imgdata,
        ctypes.c_int(image.width),
        ctypes.c_int(image.height),
        ctypes.c_int(3),  # RGB = 3 * 8
        ctypes.c_int(image.width * 3)
    )

    dpi = image.info.get("dpi", [default_dpi])[0]
    DLL.TessBaseAPISetSourceResolution(ctypes.c_void_p(handle), dpi)


# 发起识别动作
def recognize(handle):
    assert (DLL)

    return DLL.TessBaseAPIRecognize(
        ctypes.c_void_p(handle), ctypes.c_void_p(None)
    )


# 获取识别结果,内部需要释放返回值指针
def get_utf8_text(handle):
    assert (DLL)
    ptr = DLL.TessBaseAPIGetUTF8Text(ctypes.c_void_p(handle))
    val = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
    DLL.TessDeleteText(ptr)
    return val


# 封装ocr识别器
class tess_ocr:
    def __init__(self):
        self.handle = None

    # 初始化ocr识别器,告知待识别语言库/识别引擎/模型数据路径
    def open(self, lang='chi_sim', OEM=OcrEngineMode.OEM_DEFAULT, datapath=TESSDATA_PREFIX):
        self.handle = tess_init(lang, OEM, datapath)

    # 识别给定的PIL图像对象,告知页面模式/图像DPI
    def rec_img(self, image, PSM=PageSegMode.AUTO, default_dpi=DPI_DEFAULT):
        bind_image(self.handle, image, default_dpi)
        set_page_seg_mode(self.handle, PSM)
        recognize(self.handle)
        rst = get_utf8_text(self.handle)

        if len(rst) > 0 and rst[-1] == '\n':
            rst = rst.strip('\r\n\t ')

        return rst

    # 关闭ocr识别器
    def close(self):
        if self.handle:
            tess_uninit(self.handle)
            self.handle = None


if __name__ == '__main__':
    from PIL import Image

    image = Image.open('index.png')

    # 初始化DLL环境
    tess_init_env()
    # 构造ocr对象
    ocr = tess_ocr()
    # 初始化ocr引擎
    ocr.open('chi_sim', OcrEngineMode.OEM_LSTM_ONLY)
    # 识别图像得到结果
    r = ocr.rec_img(image, PageSegMode.SINGLE_WORD, 100)
    print(r)
    # 关闭ocr引擎
    ocr.close()
