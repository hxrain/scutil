import array
import math

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


def calc_bits_hash(n, p):
    """根据预计的最大元素数量n以及允许的错误率p,估算需要的哈希次数k.返回值:(位数组尺寸m,哈希次数k)"""
    m = calc_bits_size(n, p)
    return m, calc_hash_count(m, n)


class bitarray_t:
    """基于长整数数组构建一个比特数组"""
    effs = 2 ** 32 - 1

    def init(self, num_bits, array_=None):
        """初始化指定位数的比特数组"""
        self.num_bits = num_bits
        self.num_words = (self.num_bits + 31) // 32  # 计算需要的4字节长整数的数量
        if array_ is None:
            self._array = array.array('L', [0]) * self.num_words
        else:
            self._array = array_

    def isset(self, bitno):
        """判断指定的位序号bitno是否被置位"""
        wordno, bitidx = divmod(bitno, 32)
        mask = 1 << bitidx
        return self._array[wordno] & mask

    def set(self, bitno):
        """对指定的位序号bitno进行置位操作.返回值:该位置的原值"""
        wordno, bitidx = divmod(bitno, 32)
        mask = 1 << bitidx
        old = self._array[wordno] & mask
        self._array[wordno] |= mask
        return old

    def unset(self, bitno):
        """clear bit number bitno - set it to false"""
        wordno, bitidx = divmod(bitno, 32)
        mask = bitarray_t.effs - (1 << bitidx)
        self._array[wordno] &= mask


class bloom_filter_t:
    """基于内存数组的布隆过滤器"""
    masks = tuple(1 << i for i in range(32))

    def __init__(self, max_items=0, error_rate=0.00000001, array_=None):
        if max_items:
            self.init(max_items, error_rate, array_)

    def init(self, max_items, error_rate, array_=None):
        self.num_bits = calc_bits_size(max_items, error_rate)
        self.num_words = (self.num_bits + 31) // 32  # 计算需要的4字节长整数的数量
        if array_ is None:
            self._array = array.array('L', [0]) * self.num_words
        else:
            self._array = array_

    def set(self, bitpos: []):
        """添加指定的比特位序列,返回值:告知当前序列是否已经存在"""
        olds = 0
        for bitno in bitpos:
            wordno = bitno >> 5
            mask = self.masks[bitno & 0x1f]
            if self._array[wordno] & mask:
                olds += 1
                continue
            self._array[wordno] |= mask
        return olds == len(bitpos)

    def tst(self, bitpos: []):
        """判断指定比特位序列是否存在"""
        for bitno in bitpos:
            wordno = bitno >> 5
            mask = self.masks[bitno & 0x1f]
            if not self._array[wordno] & mask:
                return False
        return True

    def add(self, codes: []):
        """添加指定的哈希码序列,返回值:告知当前序列是否已经存在"""
        olds = 0
        for code in codes:
            bitno = code % self.num_bits
            wordno = bitno >> 5
            mask = self.masks[bitno & 0x1f]
            if self._array[wordno] & mask:
                olds += 1
                continue
            self._array[wordno] |= mask
        return olds == len(codes)

    def has(self, codes: []):
        """判断指定序列是否存在"""
        for code in codes:
            bitno = code % self.num_bits
            wordno = bitno >> 5
            mask = self.masks[bitno & 0x1f]
            if not self._array[wordno] & mask:
                return False
        return True
