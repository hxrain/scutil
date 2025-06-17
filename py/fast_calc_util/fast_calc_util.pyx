# -*- coding: utf-8 -*-

cpdef ARGB2RGBA(bytes src, bytearray dst, int len):
    '进行像素格式转换,从src中的ARGB格式，转换到dst中为RGBA格式，A分量固定为0xFF'
    cdef int i = 0
    cdef int lc = 0
    cdef unsigned char b = 0
    while i < len:
        lc = i * 4
        b = src[lc + 1]
        dst[lc] = b

        b = src[lc + 2]
        dst[lc + 1] = b

        b = src[lc + 3]
        dst[lc + 2] = b

        dst[lc + 3] = 0xff
        i += 1
    return

cpdef ARGB2RGBA2(bytes src, bytearray dst, int len):
    '进行像素格式转换,从src中的ARGB格式，转换到dst中为RGBA格式'
    cdef int i = 0
    cdef int lc = 0
    cdef unsigned char b = 0
    while i < len:
        lc = i * 4
        b = src[lc + 1]
        dst[lc] = b

        b = src[lc + 2]
        dst[lc + 1] = b

        b = src[lc + 3]
        dst[lc + 2] = b

        b = src[lc]
        dst[lc + 3] = b
        i += 1
    return

# skeeto三绕哈希函数配置参数(36个)
cdef list skeeto_3f = [
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

#引入外部的c函数
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto3x(unsigned long long x, unsigned long long f0, unsigned long long f1, unsigned long long f2,
                                     unsigned long long f3, unsigned long long f4, unsigned long long f5, unsigned long long f6)

cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__0(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__1(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__2(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__3(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__4(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__5(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__6(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__7(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__8(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto__9(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_10(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_11(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_12(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_13(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_14(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_15(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_16(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_17(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_18(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_19(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_20(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_21(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_22(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_23(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_24(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_25(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_26(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_27(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_28(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_29(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_30(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_31(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_32(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_33(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_34(unsigned long long x)
cdef extern from "fast_hash.c":
    unsigned long long hash_skeeto_35(unsigned long long x)

#36个skeeto哈希函数族指针列表
cdef hash_skeeto_funcs = [
    hash_skeeto__0, hash_skeeto__1, hash_skeeto__2, hash_skeeto__3, hash_skeeto__4, hash_skeeto__5, hash_skeeto__6, hash_skeeto__7, hash_skeeto__8,
    hash_skeeto__9, hash_skeeto_10, hash_skeeto_11, hash_skeeto_12, hash_skeeto_13, hash_skeeto_14, hash_skeeto_15, hash_skeeto_16, hash_skeeto_17,
    hash_skeeto_18, hash_skeeto_19, hash_skeeto_20, hash_skeeto_21, hash_skeeto_22, hash_skeeto_23, hash_skeeto_24, hash_skeeto_25, hash_skeeto_26,
    hash_skeeto_27, hash_skeeto_28, hash_skeeto_29, hash_skeeto_30, hash_skeeto_31, hash_skeeto_32, hash_skeeto_33, hash_skeeto_34, hash_skeeto_35,
]

##------------------------------------------------------------------------------
cpdef rx_hash_skeeto30(unsigned long long x):
    """skeeto哈希函数族"""
    return hash_skeeto__0(x)

cpdef list[unsigned long long] rx_hash_skeeto3l(unsigned long long x, int b, int e):
    """根据[b,e]序列索引范围,生成x的哈希函数族值列表"""
    cdef list[unsigned long long] rst = []
    for fi in range(b, e + 1):
        func = hash_skeeto_funcs[fi]
        rst.append(func(x))
    return rst

cpdef list[unsigned long long] rx_hash_skeeto3m(unsigned long long x, int b, int e, unsigned long long m):
    """根据[b,e]序列索引范围以及比特数组长度,生成x的哈希函数族比特位置列表"""
    cdef list[unsigned long long] rst = []
    for fi in range(b, e + 1):
        func = hash_skeeto_funcs[fi]
        rst.append(func(x) % m)
    return rst

cpdef rx_hash_skeeto3x(unsigned long long x, int fi):
    """skeeto哈希函数族"""
    func = hash_skeeto_funcs[fi]
    return func(x)

##------------------------------------------------------------------------------
cpdef rx_dek_hash(str v, reverse=False):
    """字符串DEK Hash函数,可配置字符的哈希方式"""
    if not v:
        return 0
    if reverse:
        itr = reversed(v)
        char = v[-1]
    else:
        itr = iter(v)
        char = v[0]

    cdef unsigned long long c = ord(char)
    cdef unsigned long long code = c * 378551
    for char in itr:
        c = ord(char)
        code = ((code << 5) ^ (code >> 27)) ^ hash_skeeto__0(c)
    return code

cpdef rx_dek_update(unsigned long long c, unsigned long long code=0):
    """对数字c基于code进行迭代计算"""
    if code == 0:
        code = c * 378551
    code = ((code << 5) ^ (code >> 27)) ^ hash_skeeto__0(c)
    return code

##------------------------------------------------------------------------------
"""判断两个simhash的结果是否相同"""
cdef extern from "fast_hash.c":
    unsigned long long simhash_equx(unsigned long long hash1, unsigned long long hash2, unsigned long long limit)

def simhash_equ(unsigned long long hash1, unsigned long long hash2, unsigned long long limit=3):
    return simhash_equx(hash1, hash2, limit)

"""计算hamming距离,两个simhash值的差异度"""
cdef extern from "fast_hash.c":
    unsigned long long simhash_distance(unsigned long long hash1, unsigned long long hash2)

cpdef uint16_split(unsigned long long hash, unsigned long long bits=64):
    """将给定的整数进行16比特拆分,得到多个分量的短整数列表"""
    cdef unsigned long long lc = bits // 16
    cdef unsigned long long mask = 0xffffffffffffffff
    cdef list rst = []
    for i in range(lc):
        sh = (lc - i - 1) * 16
        rst.append((hash & mask) >> sh)
        mask = mask >> 16
    return rst

cpdef string_hash(str v, hashfunc=rx_hash_skeeto30, unsigned long long bitsmask=0xffffffffffffffff):
    """基于数字hash函数的字符串DEK Hash函数"""
    if not v:
        return 0
    cdef unsigned long long x = len(v) * 378551
    for c in v:
        x = ((x << 5) ^ (x >> 27)) ^ hashfunc(ord(c))
    return x & bitsmask

cdef class simhash():
    """simhash相关功能封装"""
    cdef public unsigned long long hashbits
    cdef public unsigned long long bitsmask
    cdef public hashfunc
    cdef public whtfunc
    def __init__(self, unsigned long long bits=64, hashfunc=rx_hash_skeeto30, whtfunc=None):
        self.hashbits = bits  # 最终结果bit位数
        self.bitsmask = 0xffffffffffffffff if bits == 64 else 0xffffffff  # 最终结果bit位数对应的二进制掩码
        self.hashfunc = hashfunc  # 整数哈希函数
        self.whtfunc = whtfunc  # 权重计算方法

    cpdef hash(self, list tokens, use_weight=True):
        cdef list v = [0] * int(self.hashbits)
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
                fingerprint += (1 << i)
        return fingerprint

    cpdef _weight_func(self, v, use_weight):
        """获取v的权重"""
        cdef double  w = 0
        if self.whtfunc and use_weight:
            w = self.whtfunc(v)
        else:
            for c in v:
                w += 1
        return w

    cpdef distance(self, unsigned long long hash1, unsigned long long hash2):
        """计算hamming距离,两个simhash值的差异度"""
        cdef unsigned long long x = (hash1 ^ hash2) & self.bitsmask
        cdef unsigned long long tot = 0
        while x:
            tot += 1
            x &= (x - 1)
        return tot

    cpdef similarity(self, unsigned long long hash1, unsigned long long hash2, base=None):
        """计算两个simhash的相似度"""
        cdef unsigned long long dst = self.distance(hash1, hash2)
        if not base: base = self.hashbits
        if dst >= base: return 0
        return (base - dst) / base

cpdef jacard_sim(s1, s2, is_union=True):
    """对于集合或链表s1和s2,计算杰卡德相似度;返回值:(相同元素数,元素总数)"""
    if not s1 or not s2 or len(s1) == 0 or len(s2) == 0:
        return 0, 0

    if not isinstance(s1, set):
        s1 = set(s1)
    if not isinstance(s2, set):
        s2 = set(s2)

    cdef set i = s1.intersection(s2)
    cdef set u = s1.union(s2) if is_union else set()
    return len(i), len(u)

cdef class super_shingle:
    """基于k-shingle的supershingle哈希计算器"""
    cdef public unsigned long long k
    cdef public unsigned long long m
    cdef public unsigned long long s
    cdef public unsigned long long hashbits
    cdef public unsigned long long bitsmask
    cdef public hashfunc

    def __init__(self, unsigned long long k=8, unsigned long long s=4, unsigned long long m=6, unsigned long long hashbits=32):
        """k为子片文字长度;s为子片跳跃步长;m为子片哈希二次投影结果数"""
        self.k = k
        self.m = m
        self.s = s
        self.hashbits = hashbits  # 最终结果bit位数
        self.bitsmask = 0xffffffffffffffff if hashbits == 64 else 0xffffffff  # 最终结果bit位数对应的二进制掩码

    cpdef hash(self, str s):
        """计算字符串s的supershingle哈希,得到长度为m的{int}集合"""
        if not s: return None
        cdef list shingles = []
        slen = len(s)
        cdef unsigned long long loop = 1 if slen < self.k else (slen - self.k + 1)  # n-gram循环数量做最小限定
        for i in range(0, loop, self.s):
            shingles.append(string_hash(s[i:i + self.k], rx_hash_skeeto30, self.bitsmask))  # 循环得到全部子片的哈希值

        cdef set rst = set()
        cdef unsigned long long minval
        for j in range(self.m):  # 对m个二级哈希函数进行遍历
            minval = self._shingle_min(shingles, j)  # 计算当前二级哈希函数下,全部子片哈希值再哈希后的最小哈希
            if minval in rst:
                minval = self._shingle_min(shingles, j + self.m)  # 做一个冲突预防,使用后面的hash算法重新生成
            rst.add(minval)  # 用再次降维后的最小哈希值作为当前二级哈希处理后的结果
        return rst

    cpdef _shingle_min(self, list shingles, unsigned long long hashfunc_idx):
        """内置功能,对shingles列表按哈希族函数hashfunc_idx计算,并得到最小的结果"""
        if len(shingles) == 0:
            return None
        cdef list mins = []
        hashfunc = hash_skeeto_funcs[hashfunc_idx + 1]
        for s in shingles:
            mins.append(hashfunc(s) & self.bitsmask)
        return min(mins)

    cpdef distance(self, unsigned long long hash1, unsigned long long hash2):
        """计算两个super_shingle集合的差异度"""
        si, su = jacard_sim(hash1, hash2)
        return self.m - si

    cpdef similarity(self, unsigned long long hash1, unsigned long long hash2):
        """计算两个super_shingle集合的(相似度,相似量)"""
        si, su = jacard_sim(hash1, hash2)
        return si / self.m, si

cpdef super_shingle_equ(set s1, set s2, unsigned long long limit=2):
    """判断两个super_shingle哈希结果是否相同"""
    si, su = jacard_sim(s1, s2)
    return si >= limit
