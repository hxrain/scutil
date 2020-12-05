# -*- coding: utf-8 -*-

from nlp_idf_dict import *


class BM25_Core:
    '可以基于词频词典的BM25计算核心'

    def __init__(self, idf_dict):
        # 词频效果系数
        self.K1 = 1.2
        # 文档长度效果系数
        self.B = 0.75
        # IDF-IDF计数器
        self.idf_dict = idf_dict
        # 相对缺失的字词默认词频
        self.missing_f = 0

    def _switch_check(self, w1, w2):
        """检查w1和w2的长度,按最长的在前面返回"""
        if len(w1) >= len(w2):
            return w1, w2
        else:
            return w2, w1

    def sim(self, query, df, dlen):
        '计算query查询词列表与给定的文档词频表df的相似度,dlen为df的原始文档词数'
        score = 0
        for word in query:

            if word not in df:
                if self.missing_f:
                    dfw = self.missing_f
                else:
                    continue
            else:
                dfw = df[word]

            idf = self.idf_dict.get_idf(word)
            A = idf * dfw * (self.K1 + 1)
            B = (1 - self.B + self.B * dlen / self.idf_dict.avg_docs_len)
            score += (A / (dfw + self.K1 * B))

        return score

    def sim2s(self, words1, words2):
        '计算words1与words2词列表在当前词频词典下的相似度比分'
        words1, words2 = self._switch_check(words1, words2)
        df2 = {}
        calc_tf(words2, df2)
        return self.sim(words1, df2, len(words2))

    def sim_self(self, words1):
        '计算在当前词频字典下,词列表words1与自身的相似度比分'
        df1 = {}
        calc_tf(words1, df1)
        return self.sim(words1, df1, len(words1))

    def sim2p(self, words1, words2):
        '计算words1与words2词列表在当前词频词典下的相似度百分比'
        words1, words2 = self._switch_check(words1, words2)
        score1 = math.fabs(self.sim_self(words1))
        score2 = math.fabs(self.sim2s(words1, words2))

        if score1 <= score2:
            return round(score1 / score2, 8)
        else:
            return round(score2 / score1, 8)


class BM25_Query(BM25_Core):
    '可以动态更新文档索引的简易BM25检索器'

    def __init__(self, idf_dict):
        BM25_Core.__init__(self, idf_dict)
        # 每个文档的词频计数列表
        self.doc_tf_list = []

    def append(self, doc, docid, upd_ti=True):
        '追加文档,并计算词频(可以在多次调用本方法后,最后调用update,相当于最后调用TDF_IDF.update)'
        doc_tf = {}
        calc_tf(doc, doc_tf)

        # 文档词频计算完毕后,放入内部文档列表
        self.doc_tf_list.append((doc_tf, len(doc), docid))

        # 根据最新的文档词频,更新整体词频
        if upd_ti:
            self.idf_dict.append(doc_tf)

    def update(self):
        # 每个文档内容的平均词数
        avg_docs_len = sum([dtf[1] for dtf in self.doc_tf_list]) / len(self.doc_tf_list)
        self.idf_dict.update(avg_docs_len)

    def query(self, doc, top_limit=15, score_limit=0.1):
        '在全部已有的文档列表中,逐一比对计算与给定文档的相似度,并记录结果'

        # 先计算在当前整体词频和IDF的基础上,给定查询doc自身的最大相关性评分.
        self_score = self.sim_self(doc)
        # print(self_score)

        scores = []
        for index in range(len(self.doc_tf_list)):
            # 获取待匹配文档词频
            dtf = self.doc_tf_list[index]

            # 计算查询与待匹配文档词频的相关度
            score = self.sim(doc, dtf[0], dtf[1])
            if score == 0:
                continue

            # 对相关度评分进行归一化
            if math.fabs(score) <= math.fabs(self_score):
                score = round(score / self_score, 4)
            else:
                score = round(self_score / score, 4)

            if score < score_limit:
                continue
            # 使用最终的评分进行TOP结果记录
            rec_top_result(scores, score, dtf[2], top_limit)
        return scores

class bm25_calc():
    """演示bm25相似度计算的集成用法"""
    def __init__(self, isquery=False, idf_dict_file='title_ss_rc'):
        self.tf_dct = TDF_IDF_Core()
        if tdf_idf_load(self.tf_dct, idf_dict_file)[0] is None:  # 先装载预先统计好的词频词典
            print('IDF DICT load fail: '+idf_dict_file)
            exit(-2)

        self.tf_dct.adjust_digital(1)

        if isquery:
            self.be = BM25_Query(self.tf_dct)
        else:
            self.be = BM25_Core(self.tf_dct)
        self.be.missing_f = -0.1
        self.be.B = 0.4

    def sim(self, title_a, title_b):
        return self.be.sim2p(title_a, title_b)