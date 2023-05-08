# -*- coding: utf-8 -*-

class padding:
    def __init__(self, block_size, mode):
        self.block_size = block_size
        self.mode = mode

    def _zero_padding(self, s):
        """zero填充"""
        pad_len = self.block_size - len(s) % self.block_size
        return s + pad_len * b'\0'

    def _zero_unpadding(self, s):
        """zero去填充"""
        for i in range(len(s) - 1, -1, -1):
            if s[i] != 0:
                return s[0:i + 1]
        return s

    def _pkcs7_padding(self, s):
        """pkcs7填充"""
        pad_len = self.block_size - len(s) % self.block_size
        return s + pad_len * chr(pad_len).encode('latin-1')

    def _pkcs7_unpadding(self, s):
        """pkcs7去除填充"""
        n = s[-1]
        if n <= self.block_size:
            return s[0:-n]
        else:
            return s

    def pad(self, s):
        if self.mode == 'zero':
            return self._zero_padding(s)
        return self._pkcs7_padding(s)

    def unpad(self, s):
        if self.mode == 'zero':
            return self._zero_unpadding(s)
        return self._pkcs7_unpadding(s)
