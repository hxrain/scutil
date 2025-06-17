//"""skeeto哈希函数族"""
unsigned long long hash_skeeto3x(unsigned long long x,unsigned long long f0,unsigned long long f1,unsigned long long f2,unsigned long long f3,unsigned long long f4,unsigned long long f5,unsigned long long f6)
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
unsigned long long hash_skeeto__0(unsigned long long x){x ^= x >> 17; x = (x * 0xed5ad4bb); x ^= x >> 11; x = (x * 0xac4c1b51); x ^= x >> 15; x = (x * 0x31848bab); x ^= x >> 14; return x;}
unsigned long long hash_skeeto__1(unsigned long long x){x ^= x >> 16; x = (x * 0xaeccedab); x ^= x >> 14; x = (x * 0xac613e37); x ^= x >> 16; x = (x * 0x19c89935); x ^= x >> 17; return x;}
unsigned long long hash_skeeto__2(unsigned long long x){x ^= x >> 16; x = (x * 0x236f7153); x ^= x >> 12; x = (x * 0x33cd8663); x ^= x >> 15; x = (x * 0x3e06b66b); x ^= x >> 16; return x;}
unsigned long long hash_skeeto__3(unsigned long long x){x ^= x >> 18; x = (x * 0x4260bb47); x ^= x >> 13; x = (x * 0x27e8e1ed); x ^= x >> 15; x = (x * 0x9d48a33b); x ^= x >> 15; return x;}
unsigned long long hash_skeeto__4(unsigned long long x){x ^= x >> 17; x = (x * 0x3f6cde45); x ^= x >> 12; x = (x * 0x51d608ef); x ^= x >> 16; x = (x * 0x6e93639d); x ^= x >> 17; return x;}
unsigned long long hash_skeeto__5(unsigned long long x){x ^= x >> 15; x = (x * 0x5dfa224b); x ^= x >> 14; x = (x * 0x4bee7e4b); x ^= x >> 17; x = (x * 0x930ee371); x ^= x >> 15; return x;}
unsigned long long hash_skeeto__6(unsigned long long x){x ^= x >> 17; x = (x * 0x3964f363); x ^= x >> 14; x = (x * 0x9ac3751d); x ^= x >> 16; x = (x * 0x4e8772cb); x ^= x >> 17; return x;}
unsigned long long hash_skeeto__7(unsigned long long x){x ^= x >> 16; x = (x * 0x66046c65); x ^= x >> 14; x = (x * 0xd3f0865b); x ^= x >> 16; x = (x * 0xf9999193); x ^= x >> 16; return x;}
unsigned long long hash_skeeto__8(unsigned long long x){x ^= x >> 16; x = (x * 0xb1a89b33); x ^= x >> 14; x = (x * 0x09136aaf); x ^= x >> 16; x = (x * 0x5f2a44a7); x ^= x >> 15; return x;}
unsigned long long hash_skeeto__9(unsigned long long x){x ^= x >> 16; x = (x * 0x24767aad); x ^= x >> 12; x = (x * 0xdaa18229); x ^= x >> 16; x = (x * 0xe9e53beb); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_10(unsigned long long x){x ^= x >> 15; x = (x * 0x42f91d8d); x ^= x >> 14; x = (x * 0x61355a85); x ^= x >> 15; x = (x * 0xdcf2a949); x ^= x >> 14; return x;}
unsigned long long hash_skeeto_11(unsigned long long x){x ^= x >> 15; x = (x * 0x4df8395b); x ^= x >> 15; x = (x * 0x466b428b); x ^= x >> 16; x = (x * 0xb4b2868b); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_12(unsigned long long x){x ^= x >> 16; x = (x * 0x2bbed51b); x ^= x >> 14; x = (x * 0xcd09896b); x ^= x >> 16; x = (x * 0x38d4c587); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_13(unsigned long long x){x ^= x >> 16; x = (x * 0x0ab694cd); x ^= x >> 14; x = (x * 0x4c139e47); x ^= x >> 16; x = (x * 0x11a42c3b); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_14(unsigned long long x){x ^= x >> 17; x = (x * 0x7f1e072b); x ^= x >> 12; x = (x * 0x8750a507); x ^= x >> 16; x = (x * 0xecbb5b5f); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_15(unsigned long long x){x ^= x >> 16; x = (x * 0xf1be7bad); x ^= x >> 14; x = (x * 0x73a54099); x ^= x >> 15; x = (x * 0x3b85b963); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_16(unsigned long long x){x ^= x >> 16; x = (x * 0x66e756d5); x ^= x >> 14; x = (x * 0xb5f5a9cd); x ^= x >> 16; x = (x * 0x84e56b11); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_17(unsigned long long x){x ^= x >> 15; x = (x * 0x233354bb); x ^= x >> 15; x = (x * 0xce1247bd); x ^= x >> 16; x = (x * 0x855089bb); x ^= x >> 17; return x;}
unsigned long long hash_skeeto_18(unsigned long long x){x ^= x >> 16; x = (x * 0xeb6805ab); x ^= x >> 15; x = (x * 0xd2c7b7a7); x ^= x >> 16; x = (x * 0x7645a32b); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_19(unsigned long long x){x ^= x >> 16; x = (x * 0x8288ab57); x ^= x >> 14; x = (x * 0x0d1bfe57); x ^= x >> 16; x = (x * 0x131631e5); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_20(unsigned long long x){x ^= x >> 16; x = (x * 0x45109e55); x ^= x >> 14; x = (x * 0x3b94759d); x ^= x >> 16; x = (x * 0xadf31ea5); x ^= x >> 17; return x;}
unsigned long long hash_skeeto_21(unsigned long long x){x ^= x >> 15; x = (x * 0x26cd1933); x ^= x >> 14; x = (x * 0xe3da1d59); x ^= x >> 16; x = (x * 0x5a17445d); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_22(unsigned long long x){x ^= x >> 16; x = (x * 0x7001e6eb); x ^= x >> 14; x = (x * 0xbb8e7313); x ^= x >> 16; x = (x * 0x3aa8c523); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_23(unsigned long long x){x ^= x >> 16; x = (x * 0x49ed0a13); x ^= x >> 14; x = (x * 0x83588f29); x ^= x >> 15; x = (x * 0x658f258d); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_24(unsigned long long x){x ^= x >> 16; x = (x * 0x6cdb9705); x ^= x >> 14; x = (x * 0x4d58d2ed); x ^= x >> 14; x = (x * 0xc8642b37); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_25(unsigned long long x){x ^= x >> 16; x = (x * 0xa986846b); x ^= x >> 14; x = (x * 0xbdd5372d); x ^= x >> 15; x = (x * 0xad44de6b); x ^= x >> 17; return x;}
unsigned long long hash_skeeto_26(unsigned long long x){x ^= x >> 16; x = (x * 0xc9575725); x ^= x >> 15; x = (x * 0x9448f4c5); x ^= x >> 16; x = (x * 0x3b7a5443); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_27(unsigned long long x){x ^= x >> 15; x = (x * 0xfc54c453); x ^= x >> 13; x = (x * 0x08213789); x ^= x >> 15; x = (x * 0x669f96eb); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_28(unsigned long long x){x ^= x >> 16; x = (x * 0xd47ef17b); x ^= x >> 14; x = (x * 0x642fa58f); x ^= x >> 16; x = (x * 0xa8b65b9b); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_29(unsigned long long x){x ^= x >> 16; x = (x * 0x953a55e9); x ^= x >> 15; x = (x * 0x8523822b); x ^= x >> 17; x = (x * 0x56e7aa63); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_30(unsigned long long x){x ^= x >> 16; x = (x * 0xa3d7345b); x ^= x >> 15; x = (x * 0x7f41c9c7); x ^= x >> 16; x = (x * 0x308bd62d); x ^= x >> 17; return x;}
unsigned long long hash_skeeto_31(unsigned long long x){x ^= x >> 16; x = (x * 0x195565c7); x ^= x >> 14; x = (x * 0x16064d6f); x ^= x >> 16; x = (x * 0x0f9ec575); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_32(unsigned long long x){x ^= x >> 16; x = (x * 0x13566dbb); x ^= x >> 14; x = (x * 0x59369a03); x ^= x >> 15; x = (x * 0x990f9d1b); x ^= x >> 16; return x;}
unsigned long long hash_skeeto_33(unsigned long long x){x ^= x >> 16; x = (x * 0x8430cc4b); x ^= x >> 15; x = (x * 0xa7831cbd); x ^= x >> 15; x = (x * 0xc6ccbd33); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_34(unsigned long long x){x ^= x >> 16; x = (x * 0x699f272b); x ^= x >> 14; x = (x * 0x09c01023); x ^= x >> 16; x = (x * 0x39bd48c3); x ^= x >> 15; return x;}
unsigned long long hash_skeeto_35(unsigned long long x){x ^= x >> 15; x = (x * 0x336536c3); x ^= x >> 13; x = (x * 0x4f0e38b1); x ^= x >> 16; x = (x * 0x15d229f7); x ^= x >> 16; return x;}

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

