import hashlib

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
def rx_hash_gold(x, factor=17711):
    return x * factor


# 对x计算n个gold哈希函数的结果
def rx_hash_gold_f(x, n):
    return [rx_hash_gold(x, _fibonacci_seqs[i]) for i in range(n)]


# 通过配置参数产生一系列哈希函数族
def rx_hash_skeeto3(x, f=_skeeto_3f[0]):
    x ^= x >> f[0]
    x *= f[1]
    x ^= x >> f[2]
    x *= f[3]
    x ^= x >> f[4]
    x *= f[5]
    x ^= x >> f[6]
    return x


# 对x计算n个哈希函数的结果
def rx_hash_skeeto3_f(x, n):
    return [rx_hash_skeeto3(x, _skeeto_3f[i]) for i in range(n)]


# 对数字列表中的每个元素取模
def rx_int_list_mod(ints, bits=64):
    return [i % bits for i in ints]


# 根据数组序列,叠加rst生成64bit整数的布隆投影哈希值
def mk_bloom_code(ints, rst=0, xormode=False):
    if xormode:
        for i in ints:
            flag = (1 << i)
            if rst & flag:
                rst = rst & ~flag
            else:
                rst |= flag
    else:
        for i in ints:
            rst |= (1 << i)
    return rst


# 生成指定字符串的整体布隆投影哈希,hashdeep告知每个字符的样本深度,xormode控制是否进行影子的异或翻转
def rx_bloom_hash(str, hashdeep=4, xormode=True):
    hc = 0
    for c in str:
        x = ord(c)
        hashs = rx_hash_skeeto3_f(x, hashdeep)
        # 对N个哈希值进行比特数组的回绕处理
        ints = rx_int_list_mod(hashs)
        # 根据投影位置数组生成最终的布隆值
        hc = mk_bloom_code(ints, hc, xormode)
    return hc
