import base64

from Crypto.Cipher import DES


class DESCrypt:
    """DES/DES3加解密功能封装"""

    def __init__(self, key_bytes, mode=DES.MODE_ECB, CR=DES, iv=None):
        self.CR = CR  # 记录加密器类型
        if CR == DES:  # 如果是DES,则要求密钥长度必须为8
            key_bytes = key_bytes[:8]

        if iv is None:  # 根据是否有初始化向量决定如何构造加密器对象
            self.cryptor = self.CR.new(key_bytes, mode)
        else:
            self.cryptor = self.CR.new(key_bytes, mode, iv)

    def _pad(self, s):
        """填充"""
        pad_len = self.CR.block_size - len(s) % self.CR.block_size
        return s + pad_len * chr(pad_len).encode('latin-1')

    def _unpad(self, s):
        """去除填充字符"""
        return s[0:-s[-1]]

    def encrypt(self, bytes):
        """加密指定的字节数据"""
        pln = self._pad(bytes)
        return self.cryptor.encrypt(pln)

    def decrypt(self, bytes):
        """解密指定的字节数据"""
        pln = self.cryptor.decrypt(bytes)
        if int(pln[-1]) <= self.CR.block_size:
            return self._unpad(pln)
        else:
            return pln


def des_base64_decode(dat, key):
    try:
        des = DESCrypt(key.encode('latin-1'))
        chp = base64.b64decode(dat)
        edat = des.decrypt(chp)
        return edat.decode('utf-8'), ''
    except Exception as e:
        return '', str(e)
