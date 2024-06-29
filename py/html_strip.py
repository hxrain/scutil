import uni_blocks as ub
import match_ac as m
import re


class html_stripper_t:
    # 用于清理替换的规则
    rep_rule_0 = {
        "": ["&rdquo;", "&ldquo;", "rdquo;", "ldquo;", "&zwnj;", "&zwj;", "/**/", ],
        "\n": ["&#x000D;", "&#x000A;", ],
        " ": ["&thinsp;", "&#12288;", "&nbsp;", "&ensp;", "&emsp;", "&#160;", ],
        "\"": ["\\&quot;\"", "\"\\&quot;", "&quot;", "&#34;", ],
        "&": ["&amp;", "&#38;", ],
        "'": ["&apos;", "&#39;", ],
        "-": ["—", ],
        "<": ["&#60;", "&lt;", ],
        ">": ["&#62;", "&gt;", ],
        "£": ["&pound;", "&#163;", ],
        "¥": ["&#165;", "&yen;", ],
        "§": ["&sect;", "&#167;", ],
        "©": ["&copy;", "&#169;", ],
        "®": ["&#174;", "&reg;", ],
        "·": ["&middot;", ],
        "×": ["&times;", "&#215;", ],
        "÷": ["&divide;", "&#247;", ],
        "€": ["&#8364;", "&euro;", ],
        "™": ["&trade;", "&#8482;", ],
        "￠": ["&cent;", "&#162;", ],
    }

    # 内置的特殊替换处理re模式
    _ADJ_RE_PATTERNS = {
        r'\1': [r'[ ]*([/、,.，。\-_+*:;!?@\[\]{}()<>#$%^&`~\\=\n\r|【】『』《》﹙﹚〔〕«»〈〉—━∶：‘’＋“”″＆％！―〖〗]+)[ ]*', r'(:){2,}', r'\n([;])'],  # 移除标点符号两侧的空格
        r' ': [r'\t', r'[ ]{2,}', r'[!~,.，。、]{2,}'],  # 删除重复的空格,连续的无效符号
        r'\1\n': [r'([。！？!\?])', ],  # 强制断行处理
        r'\n': [r'[ \n\r]{2,}'],  # 删除重复空行
    }

    def __init__(self):
        self.rep_matcher = m.ac_match_t()
        for k in self.rep_rule_0:
            vs = self.rep_rule_0[k]
            for v in vs:
                self.rep_matcher.dict_add(v, k)
        self.rep_matcher.dict_end()

    def drop_blank(self, norm):
        """基于re匹配替换词典,移除无效的标点符号与空格,进行必要的内置替换"""
        for dst in self._ADJ_RE_PATTERNS:
            patterns = self._ADJ_RE_PATTERNS[dst]
            for pattern in patterns:
                norm = re.sub(pattern, dst, norm)
        return norm

    def entity_proc(self, txt):
        """进行html实体替换"""
        return self.rep_matcher.do_filter(txt)

    @staticmethod
    def clear_html(txt):
        """清理掉html中的URLData/style/script/tag等,降低文本字符数量."""
        txt = re.sub(r'data\s*:\s*image/[\d\w\+\/\=;,\n]*?(\)|")', r'\1 ', txt)
        txt = re.sub(r'(<\s*style|script\s*(.|\n)*?<\s*/\s*style|script\s*>)|(<\?xml[^/>]*?/>)', r' ', txt)
        txt = re.sub('<([^>/]*?)/>|<([^/][^>]*?)>|</([^>]*?)>', ' ', txt)  # 丢弃节点tag
        return txt

    def proc(self, txt, blank=True):
        """完整的进行html/text文本清理"""
        if not txt:
            return ''
        # 丢弃样式和代码
        norm = self.clear_html(txt)
        # HTML实体转换
        norm = self.entity_proc(norm)
        # 归一化空格,消除连续空白
        if blank:
            norm = self.drop_blank(norm)
        return norm
