# -*- coding: utf-8 -*-

import bisect
import re

# unicode字符分块范围与名称
_UNICODE_BLOCKS = [
    (0x0000, None),
    (0x0020, 'SPACE'),
    (0x0021, 'BASIC_PUNCTUATION_A'),
    (0x0030, 'DIGIT'),
    (0x003A, 'BASIC_PUNCTUATION_B'),
    (0x0041, 'BASIC_LATIN_A'),
    (0x005B, 'BASIC_PUNCTUATION_C'),
    (0x0061, 'BASIC_LATIN_B'),
    (0x007B, 'BASIC_PUNCTUATION_D'),
    (0x007f, None),
    (0x00A0, 'LATIN_1_SUPPLEMENT'),
    (0x00C0, 'LATIN_EXTENDED_LETTER'),
    (0x0100, 'LATIN_EXTENDED_A'),
    (0x0180, 'LATIN_EXTENDED_B'),
    (0x0250, 'IPA_EXTENSIONS'),
    (0x02B0, 'SPACING_MODIFIER_LETTERS'),
    (0x0300, 'COMBINING_DIACRITICAL_MARKS'),
    (0x0370, 'GREEK'),
    (0x0400, 'CYRILLIC'),
    (0x0500, 'CYRILLIC_SUPPLEMENTARY'),
    (0x0530, 'ARMENIAN'),
    (0x0590, 'HEBREW'),
    (0x0600, 'ARABIC'),
    (0x0700, 'SYRIAC'),
    (0x0750, 'ARABIC_SUPPLEMENT'),
    (0x0780, 'THAANA'),
    (0x07C0, 'NKO'),
    (0x0800, 'SAMARITAN'),
    (0x0840, 'MANDAIC'),
    (0x0860, None),
    (0x0900, 'DEVANAGARI'),
    (0x0980, 'BENGALI'),
    (0x0A00, 'GURMUKHI'),
    (0x0A80, 'GUJARATI'),
    (0x0B00, 'ORIYA'),
    (0x0B80, 'TAMIL'),
    (0x0C00, 'TELUGU'),
    (0x0C80, 'KANNADA'),
    (0x0D00, 'MALAYALAM'),
    (0x0D80, 'SINHALA'),
    (0x0E00, 'THAI'),
    (0x0E80, 'LAO'),
    (0x0F00, 'TIBETAN'),
    (0x1000, 'MYANMAR'),
    (0x10A0, 'GEORGIAN'),
    (0x1100, 'HANGUL_JAMO'),
    (0x1200, 'ETHIOPIC'),
    (0x1380, 'ETHIOPIC_SUPPLEMENT'),
    (0x13A0, 'CHEROKEE'),
    (0x1400, 'UNIFIED_CANADIAN_ABORIGINAL_SYLLABICS'),
    (0x1680, 'OGHAM'),
    (0x16A0, 'RUNIC'),
    (0x1700, 'TAGALOG'),
    (0x1720, 'HANUNOO'),
    (0x1740, 'BUHID'),
    (0x1760, 'TAGBANWA'),
    (0x1780, 'KHMER'),
    (0x1800, 'MONGOLIAN'),
    (0x18B0, 'UNIFIED_CANADIAN_ABORIGINAL_SYLLABICS_EXTENDED'),
    (0x1900, 'LIMBU'),
    (0x1950, 'TAI_LE'),
    (0x1980, 'NEW_TAI_LUE'),
    (0x19E0, 'KHMER_SYMBOLS'),
    (0x1A00, 'BUGINESE'),
    (0x1A20, 'TAI_THAM'),
    (0x1AB0, None),
    (0x1B00, 'BALINESE'),
    (0x1B80, 'SUNDANESE'),
    (0x1BC0, 'BATAK'),
    (0x1C00, 'LEPCHA'),
    (0x1C50, 'OL_CHIKI'),
    (0x1C80, None),
    (0x1CD0, 'VEDIC_EXTENSIONS'),
    (0x1D00, 'PHONETIC_EXTENSIONS'),
    (0x1D80, 'PHONETIC_EXTENSIONS_SUPPLEMENT'),
    (0x1DC0, 'COMBINING_DIACRITICAL_MARKS_SUPPLEMENT'),
    (0x1E00, 'LATIN_EXTENDED_ADDITIONAL'),
    (0x1F00, 'GREEK_EXTENDED'),
    (0x2000, 'GENERAL_PUNCTUATION'),
    (0x2070, 'SUPERSCRIPTS_AND_SUBSCRIPTS'),
    (0x20A0, 'CURRENCY_SYMBOLS'),
    (0x20D0, 'COMBINING_MARKS_FOR_SYMBOLS'),
    (0x2100, 'LETTERLIKE_SYMBOLS'),
    (0x2150, 'NUMBER_FORMS'),
    (0x2190, 'ARROWS'),
    (0x2200, 'MATHEMATICAL_OPERATORS'),
    (0x2300, 'MISCELLANEOUS_TECHNICAL'),
    (0x2400, 'CONTROL_PICTURES'),
    (0x2440, 'OPTICAL_CHARACTER_RECOGNITION'),
    (0x2460, 'ENCLOSED_ALPHANUMERICS'),
    (0x2500, 'BOX_DRAWING'),
    (0x2580, 'BLOCK_ELEMENTS'),
    (0x25A0, 'GEOMETRIC_SHAPES'),
    (0x2600, 'MISCELLANEOUS_SYMBOLS'),
    (0x2700, 'DINGBATS'),
    (0x27C0, 'MISCELLANEOUS_MATHEMATICAL_SYMBOLS_A'),
    (0x27F0, 'SUPPLEMENTAL_ARROWS_A'),
    (0x2800, 'BRAILLE_PATTERNS'),
    (0x2900, 'SUPPLEMENTAL_ARROWS_B'),
    (0x2980, 'MISCELLANEOUS_MATHEMATICAL_SYMBOLS_B'),
    (0x2A00, 'SUPPLEMENTAL_MATHEMATICAL_OPERATORS'),
    (0x2B00, 'MISCELLANEOUS_SYMBOLS_AND_ARROWS'),
    (0x2C00, 'GLAGOLITIC'),
    (0x2C60, 'LATIN_EXTENDED_C'),
    (0x2C80, 'COPTIC'),
    (0x2D00, 'GEORGIAN_SUPPLEMENT'),
    (0x2D30, 'TIFINAGH'),
    (0x2D80, 'ETHIOPIC_EXTENDED_A'),
    (0x2DE0, 'CYRILLIC_EXTENDED_A'),
    (0x2E00, 'SUPPLEMENTAL_PUNCTUATION'),
    (0x2E80, 'CJK_RADICALS_SUPPLEMENT'),  # 部首扩展
    (0x2F00, 'KANGXI_RADICALS'),  # 康熙部首
    (0x2FE0, None),
    (0x2FF0, 'IDEOGRAPHIC_DESCRIPTION_CHARACTERS'),
    (0x3000, 'CJK_SYMBOLS_AND_PUNCTUATION_A'),
    (0x3041, 'HIRAGANA'),
    (0x3097, 'CJK_SYMBOLS_AND_PUNCTUATION_B'),
    (0x30A1, 'KATAKANA_A'),
    (0x30FB, 'CJK_SYMBOLS_AND_PUNCTUATION_C'),
    (0x30FC, 'KATAKANA_B'),
    (0x3100, 'BOPOMOFO'),
    (0x3130, 'HANGUL_COMPATIBILITY_JAMO'),
    (0x3190, 'KANBUN'),
    (0x31A0, 'BOPOMOFO_EXTENDED'),  # 注音扩展
    (0x31C0, 'CJK_STROKES'),  # 汉字笔画
    (0x31F0, 'KATAKANA_PHONETIC_EXTENSIONS'),
    (0x3200, 'ENCLOSED_CJK_LETTERS_AND_MONTHS'),
    (0x3300, 'CJK_COMPATIBILITY'),
    (0x3400, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_A'),  # 汉字扩展A
    (0x4DC0, 'YIJING_HEXAGRAM_SYMBOLS'),
    (0x4E00, 'CJK_UNIFIED_IDEOGRAPHS'),  # 基本汉字与补充
    (0xA000, 'YI_SYLLABLES'),
    (0xA490, 'YI_RADICALS'),
    (0xA4D0, 'LISU'),
    (0xA500, 'VAI'),
    (0xA640, 'CYRILLIC_EXTENDED_B'),
    (0xA6A0, 'BAMUM'),
    (0xA700, 'MODIFIER_TONE_LETTERS'),
    (0xA720, 'LATIN_EXTENDED_D'),
    (0xA800, 'SYLOTI_NAGRI'),
    (0xA830, 'COMMON_INDIC_NUMBER_FORMS'),
    (0xA840, 'PHAGS_PA'),
    (0xA880, 'SAURASHTRA'),
    (0xA8E0, 'DEVANAGARI_EXTENDED'),
    (0xA900, 'KAYAH_LI'),
    (0xA930, 'REJANG'),
    (0xA960, 'HANGUL_JAMO_EXTENDED_A'),
    (0xA980, 'JAVANESE'),
    (0xA9E0, None),
    (0xAA00, 'CHAM'),
    (0xAA60, 'MYANMAR_EXTENDED_A'),
    (0xAA80, 'TAI_VIET'),
    (0xAAE0, None),
    (0xAB00, 'ETHIOPIC_EXTENDED_A'),
    (0xAB30, None),
    (0xABC0, 'MEETEI_MAYEK'),
    (0xAC00, 'HANGUL_SYLLABLES'),
    (0xD7B0, 'HANGUL_JAMO_EXTENDED_B'),
    (0xD800, 'HIGH_SURROGATES'),
    (0xDB80, 'HIGH_PRIVATE_USE_SURROGATES'),
    (0xDC00, 'LOW_SURROGATES'),
    (0xE000, 'PRIVATE_USE_AREA'),
    (0xF900, 'CJK_COMPATIBILITY_IDEOGRAPHS'),  # 兼容汉字
    (0xFB00, 'ALPHABETIC_PRESENTATION_FORMS'),
    (0xFB50, 'ARABIC_PRESENTATION_FORMS_A'),
    (0xFE00, 'VARIATION_SELECTORS'),
    (0xFE10, 'VERTICAL_FORMS'),
    (0xFE20, 'COMBINING_HALF_MARKS'),
    (0xFE30, 'CJK_COMPATIBILITY_FORMS'),
    (0xFE50, 'SMALL_FORM_VARIANTS'),
    (0xFE70, 'ARABIC_PRESENTATION_FORMS_B'),
    (0xFF00, 'HALFWIDTH_AND_FULLWIDTH_FORMS_A'),
    (0xFF10, 'FULLWIDTH_DIGIT'),
    (0xFF1A, 'HALFWIDTH_AND_FULLWIDTH_FORMS_B'),
    (0xFF21, 'FULLWIDTH_LATIN_A'),
    (0xFF3B, 'HALFWIDTH_AND_FULLWIDTH_FORMS_C'),
    (0xFF41, 'FULLWIDTH_LATIN_B'),
    (0xFF5B, 'HALFWIDTH_AND_FULLWIDTH_FORMS_D'),
    (0xFFF0, 'SPECIALS'),
    (0x10000, 'LINEAR_B_SYLLABARY'),
    (0x10080, 'LINEAR_B_IDEOGRAMS'),
    (0x10100, 'AEGEAN_NUMBERS'),
    (0x10140, 'ANCIENT_GREEK_NUMBERS'),
    (0x10190, 'ANCIENT_SYMBOLS'),
    (0x101D0, 'PHAISTOS_DISC'),
    (0x10200, None),
    (0x10280, 'LYCIAN'),
    (0x102A0, 'CARIAN'),
    (0x102E0, None),
    (0x10300, 'OLD_ITALIC'),
    (0x10330, 'GOTHIC'),
    (0x10350, None),
    (0x10380, 'UGARITIC'),
    (0x103A0, 'OLD_PERSIAN'),
    (0x103E0, None),
    (0x10400, 'DESERET'),
    (0x10450, 'SHAVIAN'),
    (0x10480, 'OSMANYA'),
    (0x104B0, None),
    (0x10800, 'CYPRIOT_SYLLABARY'),
    (0x10840, 'IMPERIAL_ARAMAIC'),
    (0x10860, None),
    (0x10900, 'PHOENICIAN'),
    (0x10920, 'LYDIAN'),
    (0x10940, None),
    (0x10A00, 'KHAROSHTHI'),
    (0x10A60, 'OLD_SOUTH_ARABIAN'),
    (0x10A80, None),
    (0x10B00, 'AVESTAN'),
    (0x10B40, 'INSCRIPTIONAL_PARTHIAN'),
    (0x10B60, 'INSCRIPTIONAL_PAHLAVI'),
    (0x10B80, None),
    (0x10C00, 'OLD_TURKIC'),
    (0x10C50, None),
    (0x10E60, 'RUMI_NUMERAL_SYMBOLS'),
    (0x10E80, None),
    (0x11000, 'BRAHMI'),
    (0x11080, 'KAITHI'),
    (0x110D0, None),
    (0x12000, 'CUNEIFORM'),
    (0x12400, 'CUNEIFORM_NUMBERS_AND_PUNCTUATION'),
    (0x12480, None),
    (0x13000, 'EGYPTIAN_HIEROGLYPHS'),
    (0x13430, None),
    (0x16800, 'BAMUM_SUPPLEMENT'),
    (0x16A40, None),
    (0x1B000, 'KANA_SUPPLEMENT'),
    (0x1B100, None),
    (0x1D000, 'BYZANTINE_MUSICAL_SYMBOLS'),
    (0x1D100, 'MUSICAL_SYMBOLS'),
    (0x1D200, 'ANCIENT_GREEK_MUSICAL_NOTATION'),
    (0x1D250, None),
    (0x1D300, 'TAI_XUAN_JING_SYMBOLS'),
    (0x1D360, 'COUNTING_ROD_NUMERALS'),
    (0x1D380, None),
    (0x1D400, 'MATHEMATICAL_ALPHANUMERIC_SYMBOLS'),
    (0x1D800, None),
    (0x1F000, 'MAHJONG_TILES'),
    (0x1F030, 'DOMINO_TILES'),
    (0x1F0A0, 'PLAYING_CARDS'),
    (0x1F100, 'ENCLOSED_ALPHANUMERIC_SUPPLEMENT'),
    (0x1F200, 'ENCLOSED_IDEOGRAPHIC_SUPPLEMENT'),
    (0x1F300, 'MISCELLANEOUS_SYMBOLS_AND_PICTOGRAPHS'),
    (0x1F600, 'EMOTICONS'),
    (0x1F650, None),
    (0x1F680, 'TRANSPORT_AND_MAP_SYMBOLS'),
    (0x1F700, 'ALCHEMICAL_SYMBOLS'),
    (0x1F780, None),
    (0x20000, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_B'),  # 汉字扩展B
    (0x2A6E0, None),
    (0x2A700, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_C'),  # 汉字扩展C
    (0x2B740, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_D'),  # 汉字扩展D
    (0x2B820, None),
    (0x2F800, 'CJK_COMPATIBILITY_IDEOGRAPHS_SUPPLEMENT'),  # 兼容扩展
    (0x2FA20, None),
    (0xE0000, 'TAGS'),
    (0xE0080, None),
    (0xE0100, 'VARIATION_SELECTORS_SUPPLEMENT'),
    (0xE01F0, None),
    (0xF0000, 'SUPPLEMENTARY_PRIVATE_USE_AREA_A'),
    (0x100000, 'SUPPLEMENTARY_PRIVATE_USE_AREA_B'),
    (0x10FFFF, None),
]

_UNICODE_BLOCK_STARTS = [i[0] for i in _UNICODE_BLOCKS]
_UNICODE_BLOCK_NAMES = [i[1] for i in _UNICODE_BLOCKS]

# 定义空白字符
_WHITESPACE = {
    0x9, 0xA, 0xB, 0xC, 0xD, 0x20, 0x85, 0xA0, 0x1680, 0x180E, 0x2000,
    0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009,
    0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000
}

# 全角符号范围,包含部分与ascii兼容的全角标点/大小字母/小写字母.
_SBC_CASE_SIGN_LOW = ord(u'！')
_SBC_CASE_SIGN_HIGH = ord(u'～')
_SBC_CASE_LOWER_DIFF = _SBC_CASE_SIGN_LOW - ord('!')

# 完整的汉字符号范围,[(左闭,右开)]
_FULL_CHINISE_CHARS = [(0x2E80, 0x2FE0), (0x31A0, 0x31F0), (0x3400, 0x4DC0), (0x4E00, 0xA000), (0xF900, 0xFB00),
                       (0x20000, 0x2A6E0), (0x2A700, 0x2B820), (0x2F800, 0x2FA20)]


# 全角字符转换为ascii字符,可选是否保留回车换行
def sbccase_to_ascii(ch, retain_CRFL=False):
    code = ord(ch)
    if _SBC_CASE_SIGN_LOW <= code <= _SBC_CASE_SIGN_HIGH:
        return chr(code - _SBC_CASE_LOWER_DIFF)
    if code in _WHITESPACE:
        if retain_CRFL and code in {0xA, 0xD}:
            return ch
        return ' '
    return ch


# 进行字符串的全角转ascii处理
def sbccase_to_ascii_str(u, retain_CRFL=False):
    return ''.join([sbccase_to_ascii(ch, retain_CRFL) for ch in u])




# 强制进行中文符号到英文符号的映射
_SBC_CHR_CONV_TBL = {'【': '[', '】': ']', '『': '<', '』': '>', '《': '<', '》': '>', '﹙': '(', '﹚': ')', '〔': '[', '〕': ']', '«': '<', '»': '>', '〈': '<', '〉': '>', '：': ':',
                     '—': '-', '━': '-', '∶': ':', '〇': '0', '‘': "'", '’': "'", '＋': '+', '“': '"', '”': '"', '″': '"', '＆': '&', '％': '%', '！': '!', '―': '-', '〖': '<', '〗': '>'}


def char_replace(src, dct=_SBC_CHR_CONV_TBL):
    """进行字符串特定符号转换"""
    lst = []
    for ch in src:
        if ch in _SBC_CHR_CONV_TBL:
            ch = _SBC_CHR_CONV_TBL[ch]
        lst.append(ch)
    return ''.join(lst)


def sbccase_to_ascii_str2(u, force=True, retain_CRFL=False):
    """进行额外的常见中文符号转为英文符号"""
    lst = []
    for ch in u:
        if force and ch in _SBC_CHR_CONV_TBL:
            ch = _SBC_CHR_CONV_TBL[ch]
        ch = sbccase_to_ascii(ch, retain_CRFL)
        lst.append(ch)
    return ''.join(lst)


# 根据给定的unicode字符码查询其对应的块名字
def unicode_block_of(code):
    return _UNICODE_BLOCK_NAMES[bisect.bisect_right(_UNICODE_BLOCK_STARTS, code) - 1]


# 根据给定的unicode字符查询其对应的块名字
def unichar_block_of(uchar):
    return unicode_block_of(ord(uchar))


# 筛选unicode字符集范围内,与特定字符集enc的交集字符
def make_charset_list(enc='gbk', limit=0x10000, show=False):
    rst = []
    tol = len(_UNICODE_BLOCKS)
    for i in range(tol):
        u = _UNICODE_BLOCKS[i]
        n = _UNICODE_BLOCKS[i + 1]
        if u[0] >= limit: break
        if u[1] is None: continue
        for j in range(u[0], n[0]):
            c = chr(j)
            try:
                c.encode(enc)
                rst.append(c)
                if show: print(c)
            except:
                pass
    return rst


def is_chinese_char(char):
    """判断是否为中文字符或汉字"""
    for range in _FULL_CHINISE_CHARS:
        if char >= range[0] and char < range[1]:
            return True
    return False


def is_number_char(char):
    """判断字符是否为十进制数字字符"""
    return char >= '0' and char <= '9'


def is_number_str(chars):
    """判断字符串是否为十进制数字字符"""
    for char in chars:
        if not is_number_char(char):
            return False
    return True


def is_english_lc(char):
    """判断是否为英文小写字符"""
    return char >= 'a' and char <= 'z'


def is_english_cl(char):
    """判断是否为英文大写字符"""
    return char >= 'A' and char <= 'Z'


def is_alpha_num(char):
    """判断是否为数字与英文字母"""
    return is_number_char(char) or is_english_lc(char) or is_english_cl(char)


def is_ascii_char(char):
    """判断是否为ascii字符"""
    return ord(char) <= 255


def is_ascii_str(s):
    """判断是否为ascii字符串"""
    for c in s:
        if not is_ascii_char(c):
            return False
    return True


def ascii_chars(s):
    """查询s中ascii字符的数量"""
    r = 0
    for c in s:
        if is_ascii_char(c):
            r += 1
    return r


def with_numalp(s):
    """查找字符串s前后两端的数字与字母的数量"""
    sl = len(s)
    hc = 0
    tc = 0
    for i in range(sl):
        if is_alpha_num(s[i]):
            hc += 1
        else:
            break

    for i in range(sl):
        if is_alpha_num(s[sl - i - 1]):
            tc += 1
        else:
            break
    return hc, tc


def rreplace(self, old, new, max=None):
    """从字符串的右边进行替换"""
    count = len(self) if not max else max
    tmp = self.rsplit(old, count)
    return new.join(tmp)


def re_replace(patt, rep, src):
    """进行反向引用的时候仍能替换全部匹配内容的re功能封装"""
    rst = re.sub(patt, rep, src)
    while rst != src:
        src = rst
        rst = re.sub(patt, rep, src)
    return rst


def split_ex(src, chr='|', lvls='()'):
    """对src进行chr分隔,但保持lvls[0]和lvls[1]的平滑对称.返回值:[分段子串],没有任何分隔符的时候子串为自身"""
    if not src:
        return ['']
    deep = pos = bpos = 0
    rlen = len(src)
    rst = []
    while pos < rlen:
        c = src[pos]
        if c == lvls[0]:
            deep += 1
        elif c == lvls[1]:
            deep -= 1
        elif c == chr and deep == 0:
            rst.append(src[bpos:pos])
            bpos = pos + 1
        pos += 1
    if pos != bpos:
        rst.append(src[bpos:pos])
    return rst


def eat_rep_substr(txt, sublen_zh=3, sublen_en=8, one_zh=True):
    """从txt中消除重复的子串内容;one_zh告知对于汉字串,是否使用单字判断模式"""

    def find_max_repstr(tlen, txt, bp, sublen=3):
        """从txt的bp处开始向后查找最长的重复子串,返回值:-1未找到;其他为从bp开始的子串结束点"""
        ep = bp + sublen
        while ep <= tlen:
            if txt[ep:].find(txt[bp:ep]) != -1:
                ep += 1
            else:
                break
        return ep - 1 if ep > bp + sublen else -1

    def chk_sub_zh(tlen, txt, bp):
        """判断从当前位置向后,是否应该使用汉字短串判断"""
        if one_zh:
            return not is_alpha_num(txt[bp])
        else:
            ep = min(bp + sublen_zh, tlen)
            while bp < ep:
                if is_alpha_num(txt[bp]):
                    return False
                bp += 1
            return True

    eats = []
    tlen = len(txt)
    bp = 0
    while bp < tlen:  # 逐一遍历找到最大重复子串的位置
        if chk_sub_zh(tlen, txt, bp):
            ep = find_max_repstr(tlen, txt, bp, sublen_zh)
        else:
            ep = find_max_repstr(tlen, txt, bp, sublen_en)
        if ep != -1:
            eats.append((bp, ep))
            bp = ep
        else:
            bp += 1

    if len(eats) == 0:
        return txt

    # 将重复子串范围内的序号全部列出为集合
    pnt = set()
    for e in eats:
        for p in range(e[0], e[1]):
            pnt.add(p)

    # 跳过重复子串的位置,生成最终结果串
    rst = []
    for i in range(tlen):
        if i in pnt:
            continue
        rst.append(txt[i])
    return ''.join(rst)


def chinese_to_arabic(value):
    """
    中文金额转阿拉伯金额，最大支持到千亿位
    :param value:
    :return: 转换后的数字
    """
    CHINESE_DIGITS = {'零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
                      '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    CHINESE_UNITS = {'分': 0.01, '角': 0.1, '毛': 0.1, '拾': 10, '十': 10, '佰': 100, '仟': 1000, '万': 10000, '亿': 100_000_000}

    # 删除整、正
    value = value.replace('整', '').replace('正', '')

    if value.find('毛') != -1 or value.find('角') != -1:
        if value[-1] in CHINESE_DIGITS:
            value += '分'  # 校正'三块四毛五'这样的情况
    elif value.find('块') != -1 or value.find('元') != -1:
        if value[-1] in CHINESE_DIGITS:
            value += '角'  # 校正'三块四'这样的情况

    separator = None
    # 拆分整数和小数部分
    if '元' in value:
        separator = '元'
    elif '圆' in value:
        separator = '圆'
    elif '块' in value:
        separator = '块'
    elif '点' in value:
        separator = '点'

    if separator:
        values = value.split(separator)
        integer = values[0]
        decimal = values[1]
    else:
        integer = ''
        decimal = value

    # 小数部分
    decimal_part = 0
    unit = 1
    for char in reversed(decimal):
        if char in CHINESE_DIGITS:
            if separator != '点':
                decimal_part += CHINESE_DIGITS[char] * unit
                unit = 1
            else:
                decimal_part += CHINESE_DIGITS[char] * unit
                unit *= 10
        elif char in CHINESE_UNITS:
            unit = CHINESE_UNITS[char]

    if separator == '点':
        decimal_part /= unit

    # 整数部分
    integer_part = 0
    unit = 1
    if len(integer) > 0:
        ratio = 1
        for char in reversed(integer):
            if char in CHINESE_DIGITS:
                integer_part += CHINESE_DIGITS[char] * unit * ratio

                unit = 1
            elif char in CHINESE_UNITS:
                unit = CHINESE_UNITS[char]

                if unit == 10000:
                    ratio = 10000
                    unit = 1
                elif unit == 100_000_000:
                    ratio = 100_000_000
                    unit = 1

        # 处理最前端为'拾',且之前再无数词的情况
        if integer[0] in CHINESE_UNITS and CHINESE_UNITS[integer[0]] == 10:
            integer_part += 10 * ratio

    return round(integer_part + decimal_part, 2)


assert (chinese_to_arabic('十五点三五') == 15.35)
assert (chinese_to_arabic('十元') == 10)
assert (chinese_to_arabic('十二元') == 12)
assert (chinese_to_arabic('二十元') == 20)
assert (chinese_to_arabic('二十二元') == 22)
assert (chinese_to_arabic('叁块四') == 3.4)
assert (chinese_to_arabic('叁块四毛') == 3.4)
assert (chinese_to_arabic('叁块四毛五') == 3.45)
assert (chinese_to_arabic('壹佰贰拾叁元四角五分') == 123.45)
assert (chinese_to_arabic('拾贰亿叁仟肆佰伍拾陆万柒仟捌佰玖拾元') == 1234567890)
assert (chinese_to_arabic('拾贰亿叁仟肆佰伍拾陆万柒仟捌佰玖拾圆四角五分') == 1234567890.45)


def find(txt, dst, pre, begin=0):
    """查找txt中的目标字符dst,但不能有前缀pre;返回值:符合条件的dst的位置,-1未找到"""
    pos = txt.find(dst, begin)
    while pos != -1:
        if pos != 0 and txt[pos - 1] != pre:
            return pos
        pos = txt.find(dst, pos + 1)
    return -1


def find_bracket_begin(restr, chr, bpos, epos, esp='\\'):
    """在rs的指定范围[bpos:epos]内搜索没有转义前导符esp的chr字符的位置.不存在则返回-1"""
    pos = bpos
    while pos < epos:
        c = restr[pos]
        if c != chr:
            pos += 1
            continue
        if pos == bpos:
            return pos
        elif restr[pos - 1] != esp:
            return pos
    return -1


def find_bracket_end(restr, bpos, echr, epos=-1, esp='\\'):
    """查找restr中指定范围[bpos:epos]内同级适配的字符echr.返回值:(匹配点,最大深度),匹配点-1未找到"""
    if epos == -1:
        epos = len(restr)
    if bpos >= epos or bpos < 0:
        return -1, 0

    bchr = restr[bpos]
    i = bpos + 1
    deep = 0
    max_deep = 0

    def next():
        if i + 1 >= epos:
            return None
        return restr[i + 1]

    while i < epos:
        c = restr[i]
        if c == esp:
            nc = next()  # 遇到转义字符了,尝试获取下一个字符
            if nc is None:
                return -1, max_deep  # 没有下一个字符了,查找结束
            elif nc in {bchr, echr}:
                i += 1  # 如果下一个字符是匹配符号则多跳一步
        elif c == echr:
            if deep == 0:
                return i, max_deep  # 遇到匹配结束符号了,如果深度持平则作为结果返回
            deep -= 1  # 否则减少深度等待后续字符
        elif c == bchr:
            deep += 1  # 遇到匹配开始符号了,增加深度记录
            max_deep = max(deep, max_deep)
        i += 1  # 正常跳过当前字符
    return -1, max_deep


def find_brackets(restr, chrs, bpos=0, epos=-1):
    """在restr的指定范围[bpos:epos]内,查找chrs[0]和同级配对的chrs[1]的位置.返回值:(b,e,最大深度),或者(None,None,None)"""
    if epos == -1:
        epos = len(restr)
    b = find_bracket_begin(restr, chrs[0], bpos, epos)
    if b < 0:
        return (None, None, None)
    e, d = find_bracket_end(restr, b, chrs[1], epos)
    if e < 0:
        return (None, None, None)
    return (b, e, d)


# 可进行配对包裹的字符关系对
_G_brackets_map = {'<': '>', '(': ')', '[': ']', '"': '"', "'": "'", '{': '}'}
_G_brackets_rmap = {_G_brackets_map[k]: k for k in _G_brackets_map}


def find_brackets_list(txt, result):
    """在txt中查找可按深度配对(_G_brackets_map)的字符匹配元组,将配对结果放入result列表[(起点,终点)].
        返回值:None无错误;否则返回匹配的深度剩余栈列表[(位置,字符)]
    """
    stack = []

    def _is_left_char(char):
        """判断当前左括号是否可以push积累"""
        if char not in _G_brackets_map:
            return False  # 不是左括号
        rchar = _G_brackets_map[char]
        if char == rchar and stack:  # 左右括号是同一种字符的时候
            if stack[-1][1] == char:
                return False  # 如果stack的最后已经存在当前字符,则不能push累积
        return True

    for pos in range(len(txt)):
        char = txt[pos]  # 对文本串进行逐一遍历
        if _is_left_char(char):
            stack.append((pos, char))  # 遇到了左括号则记录到stack中
        elif char in _G_brackets_rmap:
            pchar = _G_brackets_rmap[char]  # 遇到了右括号
            if stack and stack[-1][1] == pchar:  # 如果真的与stack中最后的配对相吻合
                result.append((stack[-1][0], pos))  # 则记录最内侧(最深的)的括号范围
                stack.pop(-1)  # 并剔除stack中已经用过的待配对信息
            else:
                break  # 出现错层现象了,放弃当前配对分析

    if stack:  # 括号配对失败
        return stack  # 返回待配对层级信息list
    return None


_G_NUMMAP_ZH = {'零': '0', '一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9'}


def zhnum_to_arabic(N):
    """单个中文数字转换为单个阿拉伯数字字符"""
    if N in _G_NUMMAP_ZH:
        return _G_NUMMAP_ZH[N]
    else:
        return N


def zhnum_to_arabics(NS):
    """中文数字串转换为阿拉伯数字串"""
    rst = []
    if '十' in NS:
        return '%d' % chinese_to_arabic(NS + '元')  # 借用中文金额转换函数做复杂中文数字的转换
    else:
        for N in NS:
            rst.append(zhnum_to_arabic(N))
    return ''.join(rst)


def norm_date_str(txt):
    """日期串txt进行归一化"""
    patt = r'([零一二三四五六七八九\d]{2,4})\s*[年\-\./]?\s*([零一二三四五六七八九十\d]{1,2})?\s*[月\-\./]?\s*([零一二三四五六七八九十\d]{1,2})?\s*[日号]?'
    m = re.search(patt, txt)
    if not m:
        return txt

    rst = []
    for i in range(3):
        ns = m.group(i + 1)
        if ns:
            ns = zhnum_to_arabics(ns)
            try:
                ns = '%02d' % int(ns)
            except:
                pass
            rst.append(ns)
    return '-'.join(rst)


assert (norm_date_str('2015.12.20') == '2015-12-20')
assert (norm_date_str('2015年') == '2015')
assert (norm_date_str('二零一五 年 十二 月 二十 日') == '2015-12-20')
assert (norm_date_str('二零一五年二月二十日') == '2015-02-20')
assert (norm_date_str('2015年12月20日') == '2015-12-20')
assert (norm_date_str('2015年02月20日') == '2015-02-20')
assert (norm_date_str('2015年2月20日') == '2015-02-20')
assert (norm_date_str('2015年12-20日') == '2015-12-20')
assert (norm_date_str('2015年02-20日') == '2015-02-20')
assert (norm_date_str('2015年2月20') == '2015-02-20')
assert (norm_date_str('2015 年 12 - 20 日') == '2015-12-20')
assert (norm_date_str('2015年 02-20日') == '2015-02-20')
assert (norm_date_str('2015 年2月 20') == '2015-02-20')
assert (norm_date_str('2015-2-20日') == '2015-02-20')
assert (norm_date_str('2015-2-20日下午12:00:00') == '2015-02-20')


def norm_date_str2(txt, to_upper=True):
    """对英式美式日期串txt(要求外部大写转换)进行归一化"""
    if to_upper:
        txt = txt.upper()
    mons = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8, 'SEPT': 9, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
    ms = re.search(r'(\d{1,2})(ST|ND|RD|TH)?[ ,]{1,2}(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEPT|SEP|OCT|NOV|DEC)[ .,]{1,3}(\d{4})', txt)
    ymd = None
    if ms:
        mr = ms.groups()
        if mr and len(mr) == 4:
            ymd = (mr[3], mons.get(mr[2]), int(mr[0]))

    if ymd is None:
        ms = re.search(r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEPT|SEP|OCT|NOV|DEC)[ .,]{1,3}(\d{1,2})(ST|ND|RD|TH)?[ ,]{1,2}(\d{4})', txt)
        if ms:
            mr = ms.groups()
            if mr and len(mr) == 4:
                ymd = (mr[3], mons.get(mr[0]), int(mr[1]))

    if ymd is None:
        return txt
    return '%s-%02d-%02d' % ymd


assert (norm_date_str2('11 APR,2022') == '2022-04-11')
assert (norm_date_str2('11,APR,2022') == '2022-04-11')
assert (norm_date_str2('11 APR. 2022') == '2022-04-11')
assert (norm_date_str2('11TH APR. 2022') == '2022-04-11')
assert (norm_date_str2('11TH,APR.,2022') == '2022-04-11')
assert (norm_date_str2('11TH,APR. ,2022') == '2022-04-11')
assert (norm_date_str2('11TH,APR ,2022') == '2022-04-11')
assert (norm_date_str2('11TH,APR,2022') == '2022-04-11')


def norm_time_str(txt):
    pat = '(上午|中午|下午)?([\d一二三四五六七八九十]{1,2})[时点\:]([\d一二三四五六七八九十]{1,3})?[分\:]?(\d{1,2})?[秒|时|点|整]?'
    ms = re.search(pat, txt)
    if not ms:
        return txt

    def time_num(s, dev=''):
        try:
            n = zhnum_to_arabics(s) if s is not None else dev
            if n:
                return '%02d' % int(n)
            return n
        except:
            return dev

    rst = ''
    mi = ms.groups()
    ap = mi[0]  # 上午|中午|下午
    h = time_num(mi[1])  # 小时
    if ap in {'中午', '下午'} and int(h) < 12:
        h = str(int(h) + 12)
    rst += h
    m = time_num(mi[2], '00')  # 分钟
    if m:
        rst += ':' + m
    s = time_num(mi[3])  # 秒
    if s:
        rst += ':' + s

    return rst


def norm_time_str2(txt, to_upper=True):
    """将美式英式时间格式串txt(要求外部大写转换)进行归一化"""
    if to_upper:
        txt = txt.upper()
    ms = re.search(r'(AM|PM)?[ ]?(\d{1,2})[:：](\d{1,2})([:：]\d{1,2})?[ ]?(AM|PM)?', txt)
    if not ms:
        return txt

    mr = ms.groups()
    if not mr or len(mr) != 5:
        return txt

    APM = mr[0]
    if not APM:
        APM = mr[4]

    h = int(mr[1])
    if h < 12 and APM == 'PM':
        h += 12

    m = int(mr[2])
    if mr[3] is not None:
        s = int(mr[3][1:])
    else:
        s = 0
    return '%02d:%02d:%02d' % (h, m, s)


assert (norm_time_str2('9:2:03 PM') == '21:02:03')
assert (norm_time_str2('PM9:2:03') == '21:02:03')
assert (norm_time_str2('PM 9:2:03') == '21:02:03')

assert (norm_time_str('09:08:7') == '09:08:07')
assert (norm_time_str('上午9点00分') == '09:00')
assert (norm_time_str('上午8:00') == '08:00')
assert (norm_time_str('12:00') == '12:00')
assert (norm_time_str('下午12:00') == '12:00')
assert (norm_time_str('下午1点') == '13:00')
assert (norm_time_str('下午5点') == '17:00')
assert (norm_time_str('中午12:00') == '12:00')
assert (norm_time_str('17:30') == '17:30')
assert (norm_time_str('上午9:00') == '09:00')
assert (norm_time_str('下午13:00') == '13:00')
assert (norm_time_str('17:00') == '17:00')
assert (norm_time_str('上午九点三十分') == '09:30')
assert (norm_time_str('上午九点三十五分') == '09:35')

# 标点符号与停用词
PUNCTUATIONS = {'“', '”', '、', '！', '!', '|', '：', '，', '；', '。', ':', ',', ' ', '\\', '#', '&', '/', '<', '>', '+',
                '°', ';', '·', '×', '—', '‘', '’', '…', '《', '》', '『', '』', '【', '】', '（', '）', '(', ')', '[', ']', '{',
                '}', '？', '`', '~', '～', '@', '#', '\n', '\r', '\t', '\'', '=', '「', '」', '・', '_', '.', '●', '«', '»',
                'Φ', '㎡', '﹙', '﹚', '．', '"', '／', '?', '＋', '－', '•', '%', '〔', '〕', '＃', '^', '*', '$', '-', '\u200b',
                '\u200c', '\u200d', '\xa0', '％', '\u3000', '＆', '丶', '\ufeff', '\x7f', '\ue772', '\ue618', '▪',
                '\ufffd', '\ue5ca', '\xed', 'π', 'Ф', '℃', '①', '″', 'Ω', '▁', '±', 'μ'}


def split_text(txt, drop_crlf=True, drop_punc=True, puns=PUNCTUATIONS):
    '对给定字符串进行预处理,返回分词过滤后的词列表(简化的单字切分)'
    ret = []
    for c in txt:
        if c in {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                 'u', 'v', 'w', 'x', 'y', 'z'}:
            # 小写字母变大写
            c = c.upper()
        elif c in {'\n', '\r'}:
            if drop_crlf:
                continue
            else:
                c = '\n'
        elif c in puns:
            # 标点符号都丢弃
            if drop_punc:
                continue
            else:
                c = ' '

        if len(ret) > 0 and ret[-1] == ' ' and c == ' ':
            continue
        ret.append(c)
    return ret


def filter_segs(txt, segs, dst='*'):
    """替换文本串txt的指定分段列表segs对应的内容为目标字符dst"""
    if not segs:
        return txt
    begin = 0
    rst = []
    for i in range(len(segs)):
        seg = segs[i]
        assert (seg[0] >= begin)
        rst.append(txt[begin:seg[0]])
        rst.append(dst * (seg[1] - seg[0]))
        begin = seg[1]

    if begin != len(txt):
        rst.append(txt[begin:])
    return ''.join(rst)


assert filter_segs('1234567890', [(0, 3), (5, 7)]) == '***45**890'
assert filter_segs('1234567890', [(1, 3), (5, 7)]) == '1**45**890'
assert filter_segs('1234567890', [(2, 3), (5, 10)]) == '12*45*****'

