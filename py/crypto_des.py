# -*- coding: utf-8 -*-

import base64

from Crypto.Cipher import DES
from crypto_comm import padding


class DESCrypt:
    """DES/DES3加解密功能封装"""

    def __init__(self, key_bytes, mode='cbc', padmode='zero', iv=None):
        self.CRType = DES  # 记录加密器类型
        if mode == 'ecb':
            emode = DES.MODE_ECB
        elif mode == 'cbc':
            emode = DES.MODE_CBC
        else:
            emode = DES.MODE_CBC

        # DES要求密钥长度必须为8
        key_bytes = key_bytes[:8]

        if iv is None:  # 根据是否有初始化向量决定如何构造加密器对象
            self.cryptor = self.CRType.new(key_bytes, emode)
        else:
            self.cryptor = self.CRType.new(key_bytes, emode, iv)

        self.padding = padding(self.CRType.block_size, padmode)

    def encrypt(self, bytes):
        """加密指定的字节数据"""
        pln = self.padding.pad(bytes)
        return self.cryptor.encrypt(pln)

    def decrypt(self, bytes):
        """解密指定的字节数据"""
        pln = self.cryptor.decrypt(bytes)
        return self.padding.unpad(pln)


def des_base64_decode(dat, key, iv=None, pad='pkcs7', mode='ecb'):
    try:
        key = key.encode('latin-1')
        if iv:
            iv = iv.encode('latin-1')

        des = DESCrypt(key, mode=mode, padmode=pad, iv=iv)
        chp = base64.b64decode(dat)
        edat = des.decrypt(chp)
        return edat.decode('utf-8'), ''
    except Exception as e:
        return '', str(e)
