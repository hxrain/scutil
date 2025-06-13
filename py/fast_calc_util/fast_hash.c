//"""skeeto哈希函数族"""
unsigned long long rx_hash_skeeto3x(unsigned long long x,unsigned long long f0,unsigned long long f1,unsigned long long f2,unsigned long long f3,unsigned long long f4,unsigned long long f5,unsigned long long f6)
{
    x ^= x >> f0;
    x = (x * f1);
    x ^= x >> f2;
    x = (x * f3);
    x ^= x >> f4;
    x = (x * f5);
    x ^= x >> f6;
    return x;
}

//"""skeeto哈希函数,首个参数的固化版"""
unsigned long long rx_hash_skeeto30(unsigned long long x)
{
    x ^= x >> 17;
    x = (x * 0xed5ad4bb);
    x ^= x >> 11;
    x = (x * 0xac4c1b51);
    x ^= x >> 15;
    x = (x * 0x31848bab);
    x ^= x >> 14;
    return x;
}

//"""判断两个simhash的结果是否相同"""
unsigned long long simhash_equx(unsigned long long hash1, unsigned long long hash2, unsigned long long limit)
{
    unsigned long long x = (hash1 ^ hash2);
    unsigned long long tot = 0;
    unsigned long long n = limit;
    while (x && n >= 0){
        tot += 1;
        x &= x - 1;
        n -= 1;
	}
    return tot <= limit;
}

//"""计算hamming距离,两个simhash值的差异度"""
unsigned long long simhash_distance(unsigned long long hash1, unsigned long long hash2)
{
    unsigned long long x = (hash1 ^ hash2);
    unsigned long long tot = 0;
    while (x){
        tot += 1;
        x &= x - 1;
	}
    return tot;
}

