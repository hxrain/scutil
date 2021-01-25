import hashlib

# 计算字符串的sha256值
def sha(str):
    return hashlib.sha256(str.encode('utf-8')).hexdigest()

# 计算字符串的MD5值
def md5(str):
    return hashlib.md5(str.encode('utf-8')).hexdigest()


def calc_key(dat, keyIdx=None, sep=','):
    """对数据dat按指定的顺序keyIdx计算md5值.
        dat为str类型,尝试进行sep分隔处理.
        keyIdx为int类型,使用dat中的指定元素进行计算.
        keyIdx为(a,b)2元组,使用dat[a,b+1]分片进行计算.
        keyIdx为多元组或列表,使用元组或列表指定元素进行计算
    """
    if keyIdx is None:
        if type(dat).__name__ == 'str':
            return md5(dat)  # 将整行内容的md5作为唯一key
        else:
            return md5(''.join(dat))  # 将全部内容的md5作为唯一key
    elif isinstance(keyIdx, int):
        if type(dat).__name__ == 'str':
            dat = dat.split(sep)  # 用逗号分隔后的指定字段的md5作为唯一key
        return md5(dat[keyIdx])  # 用指定字段的md5作为唯一key
    elif isinstance(keyIdx, tuple) and len(keyIdx) == 2:
        if type(dat).__name__ == 'str':
            dat = dat.split(sep)
        return md5(''.join(dat[keyIdx[0]:keyIdx[1] + 1]))  # 用keyIdx元组的作为切片范围
    elif (isinstance(keyIdx, tuple) and len(keyIdx) > 2) or isinstance(keyIdx, list):
        if type(dat).__name__ == 'str':
            dat = dat.split(sep)
        return md5(''.join([dat[i] for i in keyIdx]))  # 用keyIdx元素的指定值


