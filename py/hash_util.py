import hashlib
from numba import jit

# skeeto三绕哈希函数配置参数(36个)
_skeeto_3f = [
    (17, 0xed5ad4bb, 11, 0xac4c1b51, 15, 0x31848bab, 14),
    (16, 0xaeccedab, 14, 0xac613e37, 16, 0x19c89935, 17),
    (16, 0x236f7153, 12, 0x33cd8663, 15, 0x3e06b66b, 16),
    (18, 0x4260bb47, 13, 0x27e8e1ed, 15, 0x9d48a33b, 15),
    (17, 0x3f6cde45, 12, 0x51d608ef, 16, 0x6e93639d, 17),
    (15, 0x5dfa224b, 14, 0x4bee7e4b, 17, 0x930ee371, 15),
    (17, 0x3964f363, 14, 0x9ac3751d, 16, 0x4e8772cb, 17),
    (16, 0x66046c65, 14, 0xd3f0865b, 16, 0xf9999193, 16),
    (16, 0xb1a89b33, 14, 0x09136aaf, 16, 0x5f2a44a7, 15),
    (16, 0x24767aad, 12, 0xdaa18229, 16, 0xe9e53beb, 16),
    (15, 0x42f91d8d, 14, 0x61355a85, 15, 0xdcf2a949, 14),
    (15, 0x4df8395b, 15, 0x466b428b, 16, 0xb4b2868b, 16),
    (16, 0x2bbed51b, 14, 0xcd09896b, 16, 0x38d4c587, 15),
    (16, 0x0ab694cd, 14, 0x4c139e47, 16, 0x11a42c3b, 16),
    (17, 0x7f1e072b, 12, 0x8750a507, 16, 0xecbb5b5f, 16),
    (16, 0xf1be7bad, 14, 0x73a54099, 15, 0x3b85b963, 15),
    (16, 0x66e756d5, 14, 0xb5f5a9cd, 16, 0x84e56b11, 16),
    (15, 0x233354bb, 15, 0xce1247bd, 16, 0x855089bb, 17),
    (16, 0xeb6805ab, 15, 0xd2c7b7a7, 16, 0x7645a32b, 16),
    (16, 0x8288ab57, 14, 0x0d1bfe57, 16, 0x131631e5, 16),
    (16, 0x45109e55, 14, 0x3b94759d, 16, 0xadf31ea5, 17),
    (15, 0x26cd1933, 14, 0xe3da1d59, 16, 0x5a17445d, 16),
    (16, 0x7001e6eb, 14, 0xbb8e7313, 16, 0x3aa8c523, 15),
    (16, 0x49ed0a13, 14, 0x83588f29, 15, 0x658f258d, 15),
    (16, 0x6cdb9705, 14, 0x4d58d2ed, 14, 0xc8642b37, 16),
    (16, 0xa986846b, 14, 0xbdd5372d, 15, 0xad44de6b, 17),
    (16, 0xc9575725, 15, 0x9448f4c5, 16, 0x3b7a5443, 16),
    (15, 0xfc54c453, 13, 0x08213789, 15, 0x669f96eb, 16),
    (16, 0xd47ef17b, 14, 0x642fa58f, 16, 0xa8b65b9b, 16),
    (16, 0x953a55e9, 15, 0x8523822b, 17, 0x56e7aa63, 15),
    (16, 0xa3d7345b, 15, 0x7f41c9c7, 16, 0x308bd62d, 17),
    (16, 0x195565c7, 14, 0x16064d6f, 16, 0x0f9ec575, 15),
    (16, 0x13566dbb, 14, 0x59369a03, 15, 0x990f9d1b, 16),
    (16, 0x8430cc4b, 15, 0xa7831cbd, 15, 0xc6ccbd33, 15),
    (16, 0x699f272b, 14, 0x09c01023, 16, 0x39bd48c3, 15),
    (15, 0x336536c3, 13, 0x4f0e38b1, 16, 0x15d229f7, 16),
]

# 斐波那契序数(36个)
_fibonacci_seqs = [3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657,
                   46368, 75025, 121393, 196418, 317811, 514229, 832040, 1346269, 2178309, 3524578, 5702887, 9227465,
                   14930352, 24157817, 39088169, 63245986]


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


# 计算字符串的sha256值
def sha(str):
    return hashlib.sha256(str.encode('utf-8')).hexdigest()


# 因子选斐波那契序数,给定不同的因子可造就一系列的哈希函数族
def rx_hash_gold(x, factor=_fibonacci_seqs[18]):
    return x * factor


# 对x计算n个gold哈希函数的结果
def rx_hash_gold_f(x, n):
    return [rx_hash_gold(x, _fibonacci_seqs[i]) for i in range(n)]


# 通过配置参数产生一系列哈希函数族
@jit
def rx_hash_skeeto3(x, f=_skeeto_3f[0]):
    x ^= x >> f[0]
    x *= f[1]
    x ^= x >> f[2]
    x *= f[3]
    x ^= x >> f[4]
    x *= f[5]
    x ^= x >> f[6]
    return x


# 对x计算n个skeeto3哈希函数的结果
def rx_hash_skeeto3_f(x, n):
    return [rx_hash_skeeto3(x, _skeeto_3f[i]) for i in range(n)]


def string_hash(v, hashfunc=rx_hash_skeeto3, bitsmask=(1 << 64) - 1):
    """基于数字hash函数的字符串hash函数"""
    if not v:
        return 0
    x = 0
    for c in v:
        x = x + x ^ hashfunc(ord(c))
    return x & bitsmask


class simhash():
    """simhash相关功能封装"""

    def __init__(self, hashbits=64, hashfunc=rx_hash_skeeto3, whtfunc=None):
        self.hashbits = hashbits  # 最终结果bit位数
        self.bitsmask = (1 << self.hashbits) - 1  # 最终结果bit位数对应的二进制掩码
        self.hashfunc = hashfunc  # 整数哈希函数
        self.whtfunc = whtfunc  # 权重计算方法

    def hash(self, tokens, use_weight=True):
        v = [0] * self.hashbits
        for x in tokens:
            t = string_hash(x, self.hashfunc, self.bitsmask)
            w = self._weight_func(x, use_weight)
            for i in range(self.hashbits):
                if t & (1 << i):
                    v[i] += w
                else:
                    v[i] -= w
        fingerprint = 0
        for i in range(self.hashbits):
            if v[i] >= 0:
                fingerprint += 1 << i
        return fingerprint

    def _weight_func(self, v, use_weight):
        """获取v的权重"""
        w = 0
        if self.whtfunc and use_weight:
            w = self.whtfunc(v)
        else:
            for c in v:
                w += 1
        return w

    def distance(self, hash1, hash2):
        """计算hamming距离,两个simhash值的差异度"""
        x = (hash1 ^ hash2) & self.bitsmask
        tot = 0
        while x:
            tot += 1
            x &= x - 1
        return tot

    def similarity(self, hash1, hash2, base=None):
        """计算两个simhash的相似度"""
        dst = self.distance(hash1, hash2)
        if not base: base = self.hashbits
        if dst >= base: return 0
        return (base - dst) / base


@jit
def simhash_equ(hash1, hash2, limit=3):
    """判断两个simhash的结果是否相同"""
    x = (hash1 ^ hash2)
    tot = 0
    n = limit
    while x and n >= 0:
        tot += 1
        x &= x - 1
        n -= 1
    return tot <= limit


@jit
def simhash_distance(hash1, hash2):
    """计算hamming距离,两个simhash值的差异度"""
    x = (hash1 ^ hash2)
    tot = 0
    while x:
        tot += 1
        x &= x - 1
    return tot


@jit
def uint16_split(hash, bits=64):
    """将给定的整数进行16比特拆分,得到多个分量的短整数列表"""
    lc = bits // 16
    mask = 0xffffffffffffffff
    rst = []
    for i in range(lc):
        sh = (lc - i - 1) * 16
        rst.append((hash & mask) >> sh)
        mask = mask >> 16
    return rst



def jacard_sim(s1, s2, is_union=True):
    """对于集合或链表s1和s2,计算杰卡德相似度;返回值:(相同元素数,元素总数)"""
    if not s1 or not s2 or len(s1) == 0 or len(s2) == 0:
        return 0, 0

    if not isinstance(s1, set):
        s1 = set(s1)
    if not isinstance(s2, set):
        s2 = set(s2)

    i = s1.intersection(s2)
    u = s1.union(s2) if is_union else []
    return len(i), len(u)


class super_shingle:
    """基于k-shingle的supershingle哈希计算器"""

    def __init__(self, k=8, s=4, m=6, hashbits=32):
        """k为子片文字长度;s为子片跳跃步长;m为子片哈希二次投影结果数"""
        self.k = k
        assert (m <= len(_skeeto_3f) / 2)
        self.m = m
        self.s = s
        self.hashbits = hashbits  # 最终结果bit位数
        self.bitsmask = (1 << self.hashbits) - 1  # 最终结果bit位数对应的二进制掩码
        self.hashfunc = rx_hash_skeeto3

    def hash(self, s):
        """计算字符串s的supershingle哈希,得到长度为m的{int}集合"""
        if not s: return None
        shingles = []
        loop = max(1, len(s) - self.k + 1)  # n-gram循环数量做最小限定
        for i in range(0, loop, self.s):
            shingles.append(string_hash(s[i:i + self.k], self.hashfunc, self.bitsmask))  # 循环得到全部子片的哈希值

        rst = set()
        for j in range(self.m):  # 对m个二级哈希函数进行遍历
            minval = self._shingle_min(shingles, j)  # 计算当前二级哈希函数下,全部子片哈希值再哈希后的最小哈希
            if minval in rst:
                minval = self._shingle_min(shingles, j + self.m)  # 做一个冲突预防,使用后面的hash算法重新生成
            rst.add(minval)  # 用再次降维后的最小哈希值作为当前二级哈希处理后的结果
        return rst

    def _shingle_min(self, shingles, hashfunc_idx):
        """内置功能,对shingles列表按哈希族函数hashfunc_idx计算,并得到最小的结果"""
        if len(shingles) == 0:
            return None
        mins = []
        for s in shingles:
            mins.append(self.hashfunc(s, _skeeto_3f[hashfunc_idx + 1]) & self.bitsmask)
        return min(mins)

    def distance(self, hash1, hash2):
        """计算两个super_shingle集合的差异度"""
        si, su = jacard_sim(hash1, hash2)
        return self.m - si

    def similarity(self, hash1, hash2):
        """计算两个super_shingle集合的(相似度,相似量)"""
        si, su = jacard_sim(hash1, hash2)
        return si / self.m, si


def super_shingle_equ(s1, s2, limit=2):
    """判断两个super_shingle哈希结果是否相同"""
    si, su = jacard_sim(s1, s2)
    return si >= limit
