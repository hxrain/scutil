import mimetypes
import magic

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
