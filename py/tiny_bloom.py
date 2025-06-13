import hash_util
import array
import math
import ctypes

"""
布隆过滤器,误判率 P ≈ (1 - e^(-k*n/m))^k
    m=位数组大小,越大误判率越低
    k=哈希函数数量,最优值k=(m/n)*ln2
    n=最大元素数量,增加会提高误判率

"""


def calc_bits_size(n, p):
    """根据预计的最大元素数量n以及允许的错误率p,估算需要的位数组长度m"""
    m = -(n * math.log(p)) / (math.log(2) ** 2)
    return int(m)


def calc_hash_count(m, n):
    """根据位数组大小m与最大元素数量n,估算需要的哈希次数k"""
    k = (m / n) * math.log(2)
    return int(k)


class bitarray_t:
    """基于长整数数组构建一个比特数组"""
    effs = 2 ** 32 - 1

    def init(self, num_bits, array_=None):
        """初始化指定位数的比特数组"""
        self.num_bits = num_bits
        self.num_words = (self.num_bits + 31) // 32  # 计算需要的4字节长整数的数量
        if array_ is None:
            self.array_ = array.array('L', [0]) * self.num_words
        else:
            self.array_ = array_

    def isset(self, bitno):
        """判断指定的位序号bitno是否被置位"""
        wordno, bitidx = divmod(bitno, 32)
        mask = 1 << bitidx
        return self.array_[wordno] & mask

    def set(self, bitno):
        """对指定的位序号bitno进行置位操作.返回值:该位置的原值"""
        wordno, bitidx = divmod(bitno, 32)
        mask = 1 << bitidx
        old = self.array_[wordno] & mask
        self.array_[wordno] |= mask
        return old

    def unset(self, bitno):
        """clear bit number bitno - set it to false"""
        wordno, bitidx = divmod(bitno, 32)
        mask = bitarray_t.effs - (1 << bitidx)
        self.array_[wordno] &= mask


class bloom_filter_t:
    """基于内存数组的布隆过滤器"""

    def __init__(self, max_items=0, error_rate=0.000001, array_=None):
        if max_items:
            self.init(max_items, error_rate, array_)

    def init(self, max_items, error_rate, array_=None):
        self.bitarray = bitarray_t()
        self.bitarray.init(calc_bits_size(max_items, error_rate), array_)

    def add(self, codes: []):
        """添加指定的哈希码序列,返回值:告知当前序列是否已经存在"""
        olds = 0
        for code in codes:
            bitno = code % self.bitarray.num_bits
            if self.bitarray.set(bitno):
                olds += 1
        return olds == len(codes)

    def has(self, codes: []):
        """判断指定序列是否存在"""
        olds = 0
        for code in codes:
            bitno = code % self.bitarray.num_bits
            if self.bitarray.isset(bitno):
                olds += 1
        return olds == len(codes)


class hash_skeeto3_64t:
    def __init__(self):
        # self.x = array.array('Q', [0])
        self.mask = 0xffffffffffffffff
        self.x = ctypes.c_uint64(0)

    # def calc(self, v, f=hash_util._skeeto_3f[0]):
    #     """对数字v进行哈希计算"""
    #     self.x[0] = v
    #     self.x[0] ^= self.x[0] >> f[0]
    #     self.x[0] = (self.x[0] * f[1]) & self.mask
    #     self.x[0] ^= self.x[0] >> f[2]
    #     self.x[0] = (self.x[0] * f[3]) & self.mask
    #     self.x[0] ^= self.x[0] >> f[4]
    #     self.x[0] = (self.x[0] * f[5]) & self.mask
    #     self.x[0] ^= self.x[0] >> f[6]
    #     return self.x[0]

    # def calc(self, x, f=hash_util._skeeto_3f[0]):
    #     """对数字v进行哈希计算"""
    #     x ^= x >> f[0]
    #     x = (x * f[1]) & self.mask
    #     x ^= x >> f[2]
    #     x = (x * f[3]) & self.mask
    #     x ^= x >> f[4]
    #     x = (x * f[5]) & self.mask
    #     x ^= x >> f[6]
    #     return x

    def calc(self, v, f=hash_util._skeeto_3f[0]):
        """对数字v进行哈希计算"""
        self.x.value = v
        self.x.value ^= self.x.value >> f[0]
        self.x.value *= f[1]
        self.x.value ^= self.x.value >> f[2]
        self.x.value *= f[3]
        self.x.value ^= self.x.value >> f[4]
        self.x.value *= f[5]
        self.x.value ^= self.x.value >> f[6]
        return self.x.value

    # def calc(self, x, f=hash_util._skeeto_3f[0]):
    #     """对数字v进行哈希计算"""
    #     x ^= x >> f[0]
    #     x *= f[1]
    #     x ^= x >> f[2]
    #     x *= f[3]
    #     x ^= x >> f[4]
    #     x *= f[5]
    #     x ^= x >> f[6]
    #     return x & self.mask

    def extend(self, code, fops: []):
        """根据给定的功能参数表fops,对code进行扩展哈希码的生成.返回值:[code,code1,code2,...]"""
        rst = [code]
        for fi in fops:
            rst.append(self.calc(code, hash_util._skeeto_3f[f]))
        return rst

    def make(self, v, fops: []):
        rst = []
        for fi in fops:
            rst.append(self.calc(v, hash_util._skeeto_3f[fi]))
        return rst


hasher = hash_skeeto3_64t()


def mk(v):
    return hasher.make(v, [0, 1, 2, 3, 4, 5, 6, 7])


rs = bloom_filter_t(200000000)
print(rs.add(mk(0xff191A1B1C1D1E1F)))
print(rs.add(mk(0xff191A1B1C1D1E1F)))
print(rs.has(mk(0xff191A1B1C1D1E1F)))
print(rs.has(mk(0xff191A1B1C1D1E1E)))

import time

olds = 0
bt = time.time()
for i in range(200000000):
    if rs.add(mk(i)):
        olds += 1
    if i % 1000000 == 0:
        print(i, olds, time.time() - bt)
print(time.time() - bt)
