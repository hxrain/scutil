class tiny_kryo_t:
    """超轻量级kryo解析器.写不会出错;读取出错表现为下标越界异常."""

    def __init__(self, datas=None):
        self.buffer = []
        self.position = 0
        if datas is not None:
            self.bindBuffer(datas)

    def bufferBytes(self):
        """获取写入的字节数组数据"""
        return bytes(self.buffer)

    def bindBuffer(self, bytesData, writeable=False):
        """绑定待读写的字节数据"""
        if writeable:
            self.buffer = []
            self.buffer.extend(bytesData)  # 可写模式需要将数据转换为字节列表
        else:
            self.buffer = bytesData

    def writeByte(self, value):
        """写入一个字节,返回值:占用的空间"""
        self.buffer.append(value & 0xff)
        return 1

    def writeInt(self, value):
        """写入原始整数"""
        self.buffer.append(value & 0xff)
        self.buffer.append((value >> 8) & 0xff)
        self.buffer.append((value >> 16) & 0xff)
        self.buffer.append((value >> 24) & 0xff)
        return 4

    def writeVarInt(self, value, optimizePositive=True):
        """写入可变整数"""
        if not optimizePositive:
            value = (value << 1) ^ (value >> 31)
        if value >> 7 == 0:
            self.buffer.append(value & 0xff)
            return 1

        if value >> 14 == 0:
            self.buffer.append(((value & 0x7F) | 0x80) & 0xff)
            self.buffer.append((value >> 7) & 0xff)
            return 2

        if value >> 21 == 0:
            self.buffer.append(((value & 0x7F) | 0x80) & 0xff)
            self.buffer.append((value >> 7 | 0x80) & 0xff)
            self.buffer.append((value >> 14) & 0xff)
            return 3

        if value >> 28 == 0:
            self.buffer.append(((value & 0x7F) | 0x80) & 0xff)
            self.buffer.append((value >> 7 | 0x80) & 0xff)
            self.buffer.append((value >> 14 | 0x80) & 0xff)
            self.buffer.append((value >> 21) & 0xff)
            return 4

        self.buffer.append(((value & 0x7F) | 0x80) & 0xff)
        self.buffer.append((value >> 7 | 0x80) & 0xff)
        self.buffer.append((value >> 14 | 0x80) & 0xff)
        self.buffer.append((value >> 21 | 0x80) & 0xff)
        self.buffer.append((value >> 28) & 0xff)
        return 5

    def writeVarIntFlag(self, flag, value, optimizePositive=True):
        """写入可变整数并带有额外bool标记返回值:占用字节数量"""
        if not optimizePositive:
            value = (value << 1) ^ (value >> 31)
        first = (value & 0x3F) | (0x80 if flag else 0)  # Mask first 6 bits, bit 8 is the flag.
        if value >> 6 == 0:
            self.buffer.append(first & 0xff)
            return 1

        if value >> 13 == 0:
            self.buffer.append((first | 0x40) & 0xff)  # Set bit 7.
            self.buffer.append((value >> 6) & 0xff)
            return 2

        if value >> 20 == 0:
            self.buffer.append((first | 0x40) & 0xff)  # Set bit 7.
            self.buffer.append(((value >> 6) | 0x80) & 0xff)  # Set bit 8.
            self.buffer.append((value >> 13) & 0xff)
            return 3

        if value >> 27 == 0:
            self.buffer.append((first | 0x40) & 0xff)  # Set bit 7.
            self.buffer.append(((value >> 6) | 0x80) & 0xff)  # Set bit 8.
            self.buffer.append(((value >> 13) | 0x80) & 0xff)  # Set bit 8.
            self.buffer.append((value >> 20) & 0xff)
            return 4

        self.buffer.append((first | 0x40) & 0xff)  # Set bit 7.
        self.buffer.append(((value >> 6) | 0x80) & 0xff)  # Set bit 8.
        self.buffer.append(((value >> 13) | 0x80) & 0xff)  # Set bit 8.
        self.buffer.append(((value >> 20) | 0x80) & 0xff)  # Set bit 8.
        self.buffer.append((value >> 27) & 0xff)
        return 5

    def writeString(self, value):
        """写入一个字符串"""
        if value is None:
            self.writeByte(0x80)  # 0 means null, bit 8 means UTF8.
            return 1

        charCount = len(value)
        if charCount == 0:
            self.writeByte(1 | 0x80)  # 1 means empty string, bit 8 means UTF8.
            return 1

        if self.is_ascii(value):
            if charCount == 1:
                self.writeByte(2 | 0x80)
                self.writeByte(ord(value[0]) & 0xff)
                return 2
            else:
                for i in range(charCount):
                    self.buffer.append(ord(value[i]) & 0xff)
                self.buffer[-1] |= 0x80  # 纯ascii字符串的最后一个字符需要给出标记位
                return charCount

        # 含有非ascii字符,需要明确告知字符数量(不是字节数量)
        self.writeVarIntFlag(True, charCount + 1, True)
        charIndex = 0
        while charIndex < charCount:
            c = ord(value[charIndex])
            if c > 127:
                break  # 优先尝试写入ascii字符
            self.buffer.append(c)
            charIndex += 1

        assert (charIndex <= charCount - 1)

        # 再写入剩下的字符
        remain = value[charIndex:].encode('utf-8')
        for b in remain:
            self.buffer.append(b)
        return charIndex + len(remain)

    @staticmethod
    def is_ascii(value):
        """Detect ASCII."""
        charCount = len(value)
        for i in range(charCount):
            if ord(value[i]) > 127:
                return False
        return True

    def readByte(self):
        """读取一个字节"""
        b = self.buffer[self.position]
        self.position += 1
        return b, 1

    def readInt(self):
        """读取原始整数"""
        p = self.position
        b0 = self.buffer[p]
        b1 = self.buffer[p + 1]
        b2 = self.buffer[p + 2]
        b3 = self.buffer[p + 3]
        self.position = p + 4
        return b0 & 0xFF | (b1 & 0xFF) << 8 | (b2 & 0xFF) << 16 | (b3 & 0xFF) << 24, 4

    def readVarInt(self, optimizePositive=True):
        """读取可变整数.返回值:(整数,消耗的字节数)"""
        b = self.buffer[self.position]
        pos = self.position
        self.position += 1
        result = b & 0x7F
        if b & 0x80 != 0:
            b = self.buffer[self.position]
            self.position += 1
            result |= (b & 0x7F) << 7
            if (b & 0x80) != 0:
                b = self.buffer[self.position]
                self.position += 1
                result |= (b & 0x7F) << 14
                if (b & 0x80) != 0:
                    b = self.buffer[self.position]
                    self.position += 1
                    result |= (b & 0x7F) << 21
                    if (b & 0x80) != 0:
                        b = self.buffer[self.position]
                        self.position += 1
                        result |= (b & 0x7F) << 28

        return result if optimizePositive else ((result >> 1) ^ -(result & 1)) & 0xffffffff, self.position - pos

    def readVarIntFlag(self, optimizePositive=True):
        """读取带有flag限定的可变整数"""
        b = self.buffer[self.position]
        pos = self.position
        self.position += 1
        result = b & 0x3F
        if (b & 0x40) != 0:
            b = self.buffer[self.position]
            self.position += 1
            result |= (b & 0x7F) << 6
            if (b & 0x80) != 0:
                b = self.buffer[self.position]
                self.position += 1
                result |= (b & 0x7F) << 13
                if (b & 0x80) != 0:
                    b = self.buffer[self.position]
                    self.position += 1
                    result |= (b & 0x7F) << 20
                    if (b & 0x80) != 0:
                        b = self.buffer[self.position]
                        self.position += 1
                        result |= (b & 0x7F) << 27
        return result if optimizePositive else ((result >> 1) ^ -(result & 1)) & 0xffffffff, self.position - pos

    def readString(self):
        """读取字符串"""
        rst = []
        pos = self.position
        b = self.buffer[self.position]
        if b & 0x80 == 0:  # 是ascii字符串
            while b & 0x80 == 0:
                rst.append(chr(b))
                self.position += 1
                b = self.buffer[self.position]
            rst.append(chr(b & 0x7f))
            self.position += 1
            return ''.join(rst), self.position - pos
        else:  # 是utf8串或特殊模式
            chars, _ = self.readVarIntFlag()
            if chars == 0:
                return None, 1
            elif chars == 1:
                return '', 1
            elif chars == 2:
                rst = self.buffer[self.position]
                self.position += 1
                return '%s' % chr(rst), self.position - pos
            else:
                for i in range(chars - 1):
                    b = self.buffer[self.position]
                    self.position += 1
                    h = b >> 4
                    if h <= 7:
                        rst.append(chr(b))
                    elif h <= 13:
                        b0 = (b & 0x1F) << 6
                        b1 = self.buffer[self.position] & 0x3F
                        self.position += 1
                        rst.append(chr(b0 | b1))
                    elif h == 14:
                        b0 = (b & 0x0F) << 12
                        b1 = (self.buffer[self.position] & 0x3F) << 6
                        self.position += 1
                        b2 = self.buffer[self.position] & 0x3F
                        self.position += 1
                        rst.append(chr(b0 | b1 | b2))
                return ''.join(rst), self.position - pos

    def writeTimestamp(self, val, type='java.sql.Timestamp', id=0):
        """写时间戳类型的值.返回值:占用字节空间数"""
        pos = len(self.buffer)
        self.writeByte(1)
        self.writeVarInt(id)
        self.writeString(type)
        self.writeInt(val)
        return len(self.buffer) - pos

    def readTimestamp(self):
        """读取指定类别时间戳.返回值:(int时间戳,占用字节数,类别名称)"""
        pos = self.position
        tag, _ = self.readByte()
        assert (tag == 1)
        id, _ = self.readVarInt()
        name, _ = self.readString()
        val, _ = self.readInt()
        return val, self.position - pos, name


def parse(rules, datas):
    """根据给定的规则列表rules解析给定的数据datas.返回值:([val],msg),msg为空正常
        规则就是读取顺序明确的,tiny_kryo_t的数据类型,如['VarInt','Byte','Int','VarIntFlag','String','Timestamp']
    """
    tk = tiny_kryo_t(datas)
    rst = []
    try:
        for r in rules:
            n = 'read%s' % r
            m = getattr(tk, n)
            rst.append(m()[0])
        return rst, ''
    except Exception as e:
        return rst, str(e)


def make(rules, infos):
    """按照规则rules,拼装数据infos,得到kryo报文结果"""
    tk = tiny_kryo_t()
    for i, r in enumerate(rules):
        n = 'write%s' % r
        m = getattr(tk, n)
        if r == 'VarIntFlag':
            m(True, infos[i])
        else:
            m(infos[i])
    return tk.bufferBytes()


if __name__ == '__main__':
    datas = b'\x817442c638-bb9f-11ec-aa4f-af6fb8e48d5\xe6\x00\xfd\x02\xe8\xa2\xab\xe6\x8e\x92\xe9\x87\x8d\xe5\xa4\x84\xe7\x90\x86![{"freshFlag":0,"repeatFlag":1,"repeatPosType":"LIST","sourceFieldNames":["SOURCE_URL"]},{"freshFlag":0,"repeatFlag":1,"repeatPosType":"LIST","sourceFieldNames":["TITLE","PUBDATE"]}]\x80T2018060413240218\xb57328a3cd-bb9f-11ec-aa4f-af6fb8e48d5\xe6\x01\x00java.sql.Timestam\xf0\xad\xa5\x9a\xb0\x820http://yinzhou.nbggzy.cn/gcjszbjggs/8874127.jhtm\xec\xa6\xe5\xae\x81\xe6\xb3\xa2\xe9\x84\x9e\xe5\xb7\x9e\xe5\x8c\xba\xe5\x86\x9c\xe6\x9d\x91\xe9\xa5\xae\xe7\x94\xa8\xe6\xb0\xb4\xe8\xbe\xbe\xe6\xa0\x87\xe5\xb7\xa5\xe7\xa8\x8b\xe5\xa1\x98\xe6\xba\xaa\xe9\x95\x87\xe5\x8d\x8e\xe5\xb1\xb1\xe6\x9d\x91\xe6\x9d\x91\xe7\xba\xa7\xe7\xae\xa1\xe7\xbd\x91\xe6\x94\xb9\xe9\x80\xa0\xe5\xb7\xa5\xe7\xa8\x8b\xe6\x96\xbd\xe5\xb7\xa5\xe7\x9a\x84\xe4\xb8\xad\xe6\xa0\x87\xe7\xbb\x93\xe6\x9e\x9c\xe5\x85\xac\xe5\x91\x8aDETAI\xcc'
    rules = ['VarIntFlag', 'String', 'VarInt', 'String', 'String', 'String','String', 'Timestamp', 'String', 'String', 'String', 'String']
    infos, msg = parse(rules, datas)
    assert (msg == '')
    datas2 = make(rules, infos)
    assert (datas2 == datas)
