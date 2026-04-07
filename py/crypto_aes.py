# -*- coding: utf-8 -*-

import base64

from Crypto.Cipher import AES
from crypto_comm import padding


class AESCrypt:
    """AES加解密功能封装"""

    def __init__(self, key_bytes, mode='cbc', padmode='zero', iv=None):
        self.CRType = AES  # 记录加密器类型

        if mode == 'ecb':
            self.emode = AES.MODE_ECB
        elif mode == 'cbc':
            self.emode = AES.MODE_CBC
        else:
            self.emode = AES.MODE_CBC
        self.iv = iv
        self.key_bytes = key_bytes
        # 根据块尺寸构造对应的填充器
        self._padding = padding(self.cryptor.block_size, padmode)

    def encrypt(self, bytes):
        """加密指定的字节数据"""
        pln = self._padding.pad(bytes)
        cryptor = self.CRType.new(self.key_bytes, self.emode, self.iv)
        return cryptor.encrypt(pln)

    def decrypt(self, bytes):
        """解密指定的字节数据"""
        cryptor = self.CRType.new(self.key_bytes, self.emode, self.iv)
        pln = cryptor.decrypt(bytes)
        return self._padding.unpad(pln)


def aes_base64_decode(dat, key, iv=None, pad='zero', mode='cbc'):
    try:
        key = key.encode('latin-1')
        if iv:
            iv = iv.encode('latin-1')
        aes = AESCrypt(key, mode=mode, padmode=pad, iv=iv)
        chp = base64.b64decode(dat)
        edat = aes.decrypt(chp)
        return edat.decode('utf-8'), ''
    except Exception as e:
        return '', str(e)
