import bisect

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
    (0x2E80, 'CJK_RADICALS_SUPPLEMENT'),
    (0x2F00, 'KANGXI_RADICALS'),
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
    (0x31A0, 'BOPOMOFO_EXTENDED'),
    (0x31C0, 'CJK_STROKES'),
    (0x31F0, 'KATAKANA_PHONETIC_EXTENSIONS'),
    (0x3200, 'ENCLOSED_CJK_LETTERS_AND_MONTHS'),
    (0x3300, 'CJK_COMPATIBILITY'),
    (0x3400, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_A'),
    (0x4DC0, 'YIJING_HEXAGRAM_SYMBOLS'),
    (0x4E00, 'CJK_UNIFIED_IDEOGRAPHS'),
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
    (0xF900, 'CJK_COMPATIBILITY_IDEOGRAPHS'),
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
    (0x20000, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_B'),
    (0x2A6E0, None),
    (0x2A700, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_C'),
    (0x2B740, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_D'),
    (0x2B820, None),
    (0x2F800, 'CJK_COMPATIBILITY_IDEOGRAPHS_SUPPLEMENT'),
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


# 全角字符转换为ascii字符
def sbccase_to_ascii(ch):
    code = ord(ch)
    if _SBC_CASE_SIGN_LOW <= code <= _SBC_CASE_SIGN_HIGH:
        return chr(code - _SBC_CASE_LOWER_DIFF)
    if code in _WHITESPACE:
        return ' '
    return ch


# 进行字符串的全角转ascii处理
def sbccase_to_ascii_str(u):
    return ''.join([sbccase_to_ascii(ch) for ch in u])


# 强制进行中文符号到英文符号的映射
_SBC_CHR_CONV_TBL = {'【': '[', '】': ']', '『': '<', '』': '>', '《': '<', '》': '>', '﹙': '(', '﹚': ')', '〔': '[', '〕': ']'}


def sbccase_to_ascii_str2(u, force=True):
    """进行额外的常见中文符号转为英文符号"""
    lst = []
    for ch in u:
        if force and ch in _SBC_CHR_CONV_TBL:
            ch = _SBC_CHR_CONV_TBL[ch]
        ch = sbccase_to_ascii(ch)
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


def is_number_char(char):
    """判断是否为数字字符"""
    return char >= '0' and char <= '9'


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


def eat_rep_substr(txt, sublen_zh=3, sublen_en=8):
    """从txt中消除重复的子串内容"""

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
