# -*- coding: utf-8 -*-

import json
import math
import os


def load_dict(filename):
    '''load dict from json file'''
    with open(filename, "r", encoding='utf-8') as json_file:
        dic = json.load(json_file)
    return dic


def save_dict(filename, dic):
    '''save dict into json file'''
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(dic, json_file, ensure_ascii=False, indent=4)


def calc_tf(words, res):
    '计算指定words词列表的词频,结果放入res'
    for word in words:
        if not word in res:
            res[word] = 0
        res[word] += 1


def topK(nodes_rank, topK=None):
    '''对nodes_rank结果进行topK的排序计算
        - topK: 返回指定数量K的结果,如果为`None`则返回全部结果
    '''
    tags = sorted(nodes_rank.items(), key=lambda d: d[1], reverse=True)

    if topK:
        return tags[:topK]
    else:
        return tags


def ext_topK(nodes_rank, topK, idf_dict):
    '''对nodes_rank结果进行topK的排序计算
        - topK: 返回指定数量K的结果,如果为`None`则返回全部结果
    '''
    tags = sorted(nodes_rank.items(), key=lambda d: d[1], reverse=True)

    rst = []
    for k in tags:
        idf = idf_dict.get_idf(k[0])
        if idf < idf_dict.avg_idf / 3:
            continue
        rst.append(k)

        if topK and len(rst) >= topK:
            return rst

    return rst


def rec_top_result(rst, score, docid, top_limit=10):
    '按score的高低顺序将score和docid放入rst,rst超过limit数量后淘汰最后的值'
    if math.fabs(score) < 0.00001:
        return

    loc = -1
    for i in range(len(rst)):
        r = rst[i]
        if score >= r[0]:
            rst.insert(i, (score, docid))
            loc = i
            break

    if loc == -1:
        rst.append((score, docid))

    if len(rst) > top_limit:
        rst.pop(-1)

    return


'''
    TF(词频,单文档词频 : 如果某个单词在一篇文章中出现的频率TF高，并且在其他文章中很少出现，则认为此词或者短语具有很好的类别区分能力，适合用来分类): 
        TF = (文档中关键词T出现的次数)/(文档总词数)
    D(文档数量):
        D = 样本空间或参与计算的文档的总数
    TDF(DF,含有关键词T的文档频率):
        TDF = (含有关键词T的文档数量)/(文档数量D) 
    IDF(逆文档频率 : 如果包含词条t的文档越少IDF越大,则说明词条具有很好的类别区分能力):
        IDF = log(文档数量D/(含有关键词T的文档数量+1))
    TF-IDF(权重 : 某一特定文件内的高词语频率，以及该词语在整个文档集合中的低文档频率，可以产生出高权重的TF-IDF):
        TF-IDF(t) = TF(t) * IDF(t) 
'''


class TDF_IDF_Core:
    'TDF_IDF词典核心'

    def __init__(self):
        # 每个词的文档频率统计表
        self.tdf_dict = {}
        # 全部文档的IDF(逆文档词频)
        self.idf_dict = {}
        # IDF负值校正系数(0.25)
        self.EPSILON = 0
        # 数字符号tdf的权重系数,用于提高数字的敏感性(平均tdf的倍率)
        self.digital_dtf_rate = 30
        # 参与计算IDF的文档总数
        self.D = 0
        # 平均文档长度
        self.avg_docs_len = 0
        # 关键词的平均idf值
        self.avg_idf = 0
        # 关键词的平均文档频率
        self.avg_tdf = 0

    def get_idf(self, word):
        '获取指定单词的全库逆文档频率IDF'
        if word not in self.idf_dict:
            return self.avg_idf

        if self.EPSILON:
            return self.idf_dict[word] if self.idf_dict[word] >= 0 else self.EPSILON * self.avg_idf
        else:
            return self.idf_dict[word]

    def get_tdf(self, word):
        '获取指定单词的全库文档频率tdf(出现过word的文档数/文档总数)'
        if word not in self.tdf_dict:
            return self.avg_tdf
        return self.tdf_dict[word] / self.D

    def adjust_digital(self, rate):
        # 基于平均idf的倍数校正数字的idf
        if not rate or rate <= 0:
            return
        adj_tdf = self.avg_tdf * rate

        for i, k in enumerate(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']):
            if k not in self.idf_dict:
                continue
            self.idf_dict[k] = adj_tdf + 0.0001 * i

    def adjust_alpha(self, rate):
        # 基于平均idf的倍数校正数字的idf
        if not rate or rate <= 0:
            return
        adj_tdf = self.avg_tdf * rate

        for k in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
            if k not in self.idf_dict:
                continue
            self.idf_dict[k] = adj_tdf


def tdf_idf_save(dst: TDF_IDF_Core, filename):
    '保存TDF_IDF词典到文件'
    save_dict(filename + '.tdf', dst.tdf_dict)
    save_dict(filename + '.idf', dst.idf_dict)
    cfg = {'D': dst.D,
           'digital_dtf_rate': dst.digital_dtf_rate,
           'avg_docs_len': dst.avg_docs_len,
           'avg_idf': dst.avg_idf,
           'avg_tdf': dst.avg_tdf,
           'EPSILON': dst.EPSILON,
           }
    save_dict(filename + '.cfg', cfg)


def tdf_idf_load(dst: TDF_IDF_Core, filename):
    '装载TDF_IDF词典,返回tdf与idf词典的数量2元组'
    fn = filename + '.cfg'
    if not os.path.exists(fn):
        return (None, None)

    cfg = load_dict(fn)
    dst.tdf_dict = load_dict(filename + '.tdf')
    dst.idf_dict = load_dict(filename + '.idf')

    dst.D = cfg['D']
    dst.digital_dtf_rate = cfg['digital_dtf_rate']
    dst.avg_docs_len = cfg['avg_docs_len']
    dst.avg_idf = cfg['avg_idf']
    dst.avg_tdf = cfg['avg_tdf']
    dst.EPSILON = cfg['EPSILON']
    return (len(dst.tdf_dict), len(dst.idf_dict))


class TDF_IDF_Maker(TDF_IDF_Core):
    'TDF_IDF词典生成器'

    def __init__(self):
        TDF_IDF_Core.__init__(self)

    def append(self, doc_tf):
        # 根据最新的文档词频,更新整体词文档词频
        for k, v in doc_tf.items():
            if k not in self.tdf_dict:
                self.tdf_dict[k] = 0
            self.tdf_dict[k] += 1
        self.D += 1

    def update(self, avg_docs_len=None):
        'append之后,更新计算整体文档的IDF'
        if avg_docs_len is not None:
            self.avg_docs_len = avg_docs_len
        # 重新计算IDF
        self.idf_dict.clear()
        total_tdf = 0
        for k, v in self.tdf_dict.items():
            self.idf_dict[k] = math.log(self.D - v + 0.5) - math.log(v + 0.5)
            total_tdf += v
        # 计算得到平均tdf
        self.avg_tdf = (total_tdf / self.D)

        # 尝试校正数字的idf
        self.adj_number_idf(self.digital_dtf_rate)

        # 最后计算平均IDF的时候,排除文档频率为1的词,避免干扰得到较大的平均值.
        total_idf = sum(map(lambda k: float(self.idf_dict[k]) if self.tdf_dict[k] != 1 else 0, self.idf_dict.keys()))
        self.avg_idf = total_idf / len(self.idf_dict.keys())
        # print(self.idf_dict)


def idf_keywords(tf_dict, idf_dict):
    '根据IDF词典计算给定tf词典中的关键词权重,返回值为每个关键词的权重词典'
    rst = {}
    for t, f in tf_dict.items():
        rst[t] = f / len(tf_dict.items()) * idf_dict.get_idf(t)
    return rst
