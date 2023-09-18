from enum import Enum, unique
import tqdm
import os
import re
import uni_blocks as ub
import util_hmm as uh

# 用于分句的符号
SEP_CHARS = {'\n', '！', '？', '#', '￥', '%', '，', '。', '、', '|', '!', '?', '#', '$', '%', ',', '\\', '`', '~', ':', '丶', '、', ' ', '：', ';', '；', '*', '\u200b', '\uf0d8', '\ufeff'}
SEP_CHARSTR = '[' + ''.join(SEP_CHARS) + ']'

# 名字分隔符归一化
SEP_NAMES = {'·': '.', '°': '.', '—': '.', '．': '.', '－': '.', '•': '.', '-': '.', '・': '.', '_': '.', '▪': '.', '▁': '.', '/': '.', '／': '.',
             '\\': '.', '"': "'", '●': '.', '[': '(', ']': ')', '{': '(', '}': ')', '&': '.'}


def ner_text_clean(txt):
    """对文本进行必要的处理转换,但不应改变文本长度和位置"""
    txt = ub.sbccase_to_ascii_str2(txt, True, True)
    txt = ub.char_replace(txt, SEP_NAMES).upper()
    return txt


def ner_text_split(txt):
    """对txt进行简单分行处理,返回值:[line]"""
    return re.split(SEP_CHARSTR, txt)


@unique
class tags(Enum):
    O = 0  # NER其他状态
    B = 1  # NER开始状态
    I = 2  # NER中间状态
    E = 3  # NER结束状态


class ner_hmm_bio_t:
    """基于简单BIO标注的NER识别器.要求:O-0;B-1;I-2"""

    def __init__(self, model_dir=None, model_tag='bio', status_N=3):
        self.hmm = uh.std_hmm_t(status_N)
        if model_dir:
            self.load(model_dir, model_tag)

    def load(self, model_dir, model_tag):
        return self.hmm.model_load(model_dir, model_tag)

    def on_check(self, r):
        """检查r识别结果(begin,end,[status])是否可以使用,返回值:可用的结果,或None"""
        return r if r[2][0] == tags.B.value and r[2][-1] == tags.I.value else None  # 要求NER结尾状态为2(I)

    def on_split_lines(self, txt):
        """对txt进行分行处理"""
        return ner_text_split(txt)  # 对文本简单分行

    def on_conv_seqs(self, line):
        """将字符转换为观测序列"""
        obs = [min(ord(c), 65535) for c in line]
        obs.append(ord('\n'))  # 末尾补位,提高区分度
        return obs

    def predict_text(self, txt, sep_status=tags.O.value):
        """对给定的txt文本进行ner预测.返回值:[(begin,end,[status])]"""
        rst = []
        lines = self.on_split_lines(txt)  # 分行
        self.txt = txt
        offset = 0

        for line in lines:  # 逐行进行预测处理
            linelen = len(line)
            if linelen <= 2:
                offset += linelen + 1
                continue  # 跳过短行

            # 将字符转换为观测序列
            obs = self.on_conv_seqs(line)
            # 预测得到状态序列
            self.predict_seqs(obs, rst, offset, sep_status)
            offset += linelen + 1
        return rst

    def predict_seqs(self, obs, rsts, offset=0, sep_status=tags.O.value):
        """预测指定的观察序列obs,得到状态序列并放入rsts,offset告知观察序列在整体样本中的偏移位置.返回值:有效结果序列的数量"""
        stlst, rglst = self.hmm.predict(obs, sep_status)
        rc = 0
        for rg in rglst:
            # 构造结果记录
            r = (offset + rg[0], offset + rg[1], stlst[rg[0]:rg[1]])
            r = self.on_check(r)  # 进行校正检查
            if r:  # 记录有效结果
                rsts.append(r)
                rc += 1
        return rc


class ner_hmm_bioe_t(ner_hmm_bio_t):
    """基于简单BIOE标注的NER识别器.要求:O-0;B-1;I-2;E-3"""

    def __init__(self, model_dir=None, model_tag='bioe'):
        super().__init__(model_dir, model_tag, 4)

    def on_check(self, r):
        """检查识别结果是否可以使用,返回值:可用的结果,或None"""
        ss = r[2]
        if ss[0] != tags.B.value or ss[-1] != tags.E.value:
            return None
        if self.txt[r[1] - 1] in SEP_CHARSTR:
            return None
        return r
