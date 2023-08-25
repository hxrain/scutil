from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
import hashlib
import random
import time
import uuid


def sha(str):
    """计算字符串的sha256值"""
    return hashlib.sha256(str.encode('utf-8')).hexdigest()


def md5(str):
    """计算字符串的MD5值"""
    return hashlib.md5(str.encode('utf-8')).hexdigest()


def timestamp():
    """获取当前时间utc纳秒时间戳"""
    return time.time_ns()


def base64_encode(data):
    """对数据data进行base64编码,得到结果字符串"""
    return base64.b64encode(data).decode('latin-1')


def padding_pkcs7(data, block_size):
    """pkcs7填充"""
    pad_len = block_size - len(data) % block_size
    return data + pad_len * chr(pad_len).encode('latin-1')


def unpadding_pkcs7(data, block_size):
    """pkcs7解填充"""
    n = data[-1]
    return data[0:-n] if n <= block_size else data


def padding_pkcs5(data, block_size=None):
    """pkcs5填充"""
    return padding_pkcs7(data, 8)


def unpadding_pkcs5(data, block_size=None):
    """pkcs5解填充"""
    return unpadding_pkcs7(data, 8)


# 填充模式映射表
PADDINGS = {'pkcs5pad': padding_pkcs5, 'pkcs5unpad': unpadding_pkcs5,
            'pkcs7pad': padding_pkcs7, 'pkcs7unpad': unpadding_pkcs7}


class rand_t:
    """随机序列生成器"""

    def __init__(self):
        """使用当前时间初始化种子"""
        self._r = random.Random(timestamp())
        self._q = 0  # 记录递增序号

    def groupi(self, count=8, sep='-', seq=True):
        """生成count组最大值为0xFFFF的随机数分组串,使用sep进行分隔,seq告知是否附加递增序号"""
        rst = []
        count = max(count, 4)
        if seq:
            for i in range(count - 1):
                rst.append('%04x' % (self._r.randint(0, 0xFFFF)))
            rst.append('%04x' % self._q)
        else:
            for i in range(count):
                rst.append('%04x' % (self._r.randint(0, 0xFFFF)))
        self._q += 1  # 随机数的最后一组,是调用递增序号
        return sep.join(rst)

    def groups(self, count=16, sep='', templ=None):
        """生成count个随机字母数字串"""
        rst = []
        tbl = templ or '0123456789abcdefABCDEFghijklGHIJKLmnopqrsMNOPQRStuvwxyzTUVWXYZ~!@#$%^&*(){}[]:'
        for i in range(count):
            idx = self._r.randint(0, 0xFFFF) % len(tbl)
            rst.append(tbl[idx])
        return sep.join(rst)

    def exts(self, count=8, sep='@'):
        """生成增强的唯一序列"""
        return f'{self.groupi(count)}{sep}{uuid.uuid1()}'


class aes_crypto_t:
    """AES加解密工具"""

    @staticmethod
    def make_aes(key_bytes, emode=AES.MODE_ECB):
        """使用指定的key和工作模式emode,生成AES加解密器"""
        if isinstance(key_bytes, str):
            key_bytes = key_bytes.encode('latin-1')
        return AES.new(key_bytes, emode)

    @staticmethod
    def encrypt(cryptor, data, padding='pkcs7pad'):
        """加密指定的字节数据"""
        pln = PADDINGS[padding](data, cryptor.block_size)
        return cryptor.encrypt(pln)

    @staticmethod
    def decrypt(cryptor, data, unpadding='pkcs7unpad'):
        """解密指定的字节数据"""
        pln = cryptor.decrypt(data)
        return PADDINGS[unpadding](pln, cryptor.block_size)

    def __init__(self, key_bytes, emode=AES.MODE_ECB):
        self.aes = self.make_aes(key_bytes, emode)

    def encode(self, data, padding='pkcs7pad'):
        """加密,返回二进制密文"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.encrypt(self.aes, data, padding)

    def decode(self, data, tostr=True, unpadding='pkcs7unpad'):
        """解密,data为字符串则进行base64解码,根据tostr决定是否转换为字符串."""
        if isinstance(data, str):
            data = base64.decodebytes(data.encode('latin-1'))
        rst = self.decrypt(self.aes, data, unpadding)
        return rst.decode('utf-8') if tostr else rst


class rsa_crypto_t:
    """RSA加解密工具"""

    @staticmethod
    def make_key(bits=1024, mode=0):
        """随机生成rsa算法的密钥:
            mode=0 原始密钥对象
            mode=1 完整x509/PEM文本(带有BEGIN/END描述)
            mode=2 简化x509/PEM文本(只有BASE64数据部分)
            返回值:(私钥,公钥)
        """
        key = RSA.generate(bits)
        pub = key.public_key()
        if mode == 0:
            return key, pub  # 返回RsaKey对象

        ikey = key.export_key().decode('latin-1')
        pkey = pub.export_key().decode('latin-1')
        if mode == 1:
            return ikey, pkey  # 返回PEM标准Key字符串

        return ikey[32:-30], pkey[27:-25]  # 返回精简Key字符串

    @staticmethod
    def make_rsa(key):
        """根据给定的公钥或私钥生成RSA加解密器.key可以是RsaKey对象,也可以是base64编码后的x509/PEM密钥串"""
        if isinstance(key, str):
            key = base64.decodebytes(key.encode('latin-1'))
        if isinstance(key, bytes):
            key = RSA.import_key(key)
        return PKCS1_v1_5.new(key)  # PKCS1填充模式

    @staticmethod
    def encrypt(cryptor, data):
        """对给定的数据进行加密"""
        pos = 0
        blksize = cryptor._key.size_in_bytes() - 11  # PKCS1填充模式要求,明文块尺寸<=密钥模长-11字节
        rst = []
        while pos < len(data):
            et = cryptor.encrypt(data[pos:pos + blksize])
            rst.append(et)
            pos += blksize
        return b''.join(rst)

    @staticmethod
    def decrypt(cryptor, data):
        """对给定的密文进行解密"""
        pos = 0
        blksize = cryptor._key.size_in_bytes()
        rst = []
        while pos < len(data):
            ot = cryptor.decrypt(data[pos:pos + blksize], None)
            if ot is None:
                return None  # error
            rst.append(ot)
            pos += blksize
        return b''.join(rst)

    def __init__(self, key):
        """使用指定的密钥(公钥或私钥)进行初始化"""
        self.rsa = self.make_rsa(key)

    def encode(self, data):
        """加密"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.encrypt(self.rsa, data)

    def decode(self, data, tostr=True):
        """解密,data为字符串则进行base64解码,根据tostr决定是否转换为字符串."""
        if isinstance(data, str):
            data = base64.decodebytes(data.encode('latin-1'))
        rst = self.decrypt(self.rsa, data)
        return rst.decode('utf-8') if tostr else rst


if __name__ == '__main__':
    """临时测试代码"""
    # RSA加密器测试
    vkey, pkey = rsa_crypto_t.make_key(mode=2)  # 生成密钥对(简化x509格式串)
    prsa = rsa_crypto_t(pkey)  # 使用公钥生成加密器
    vrsa = rsa_crypto_t(vkey)  # 使用私钥生成加密器

    et = prsa.encode('abc')  # 使用公钥加密器进行加密
    print(et)
    assert (vrsa.decode(et) == 'abc')  # 使用私钥加密器进行解密

    # AES加密器测试
    aes = aes_crypto_t(b'0123456789ABCDEF')  # 使用密钥生成加密器
    et = aes.encode('abc')  # 加密操作
    print(et)
    assert (aes.decode(et) == 'abc')  # 解密操作
