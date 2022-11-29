# -*- coding: utf-8 -*-

from uni_blocks import *
from nlp_idf_dict import *
from nlp_text_rank import *

'''
多模短语提取方式,可变量:
1 topk的数量,建议为[4,8,12]
2 是否删除停用词               :是
3 使用IDF/TR/IDF+TR算法       :IDF+TR
4 是否使用文档词序输出          :是
5 文档前部分段(前7段或不少于100字)
'''

_STOPS = {'或者', '意见反馈', '需求', '满意', '社会公众', '提出', '客观', '公示', '处理意见', '遵循', '质疑', '具体情况', '论证', '意见',
          '得到', '代理', '财政部门', '对本', '秒', '项目管理', '异议', '同级', '公正', '处理', '建议', '未', '详见', '预算', '概况', '起', '原则', '潜在',
          '联系方式', '内', '止', '机构', '向', '附件', '书面', '予以', '请于', '投诉', '标的', '期间', '监督', '工作日内', '就', '问题', '可以', '期限',
          '应当', '不', '规定', '自', '天', '分', '室', '可', '满', '政府采购', '接受', '有关', '于', '发布', '通过', '无', '前', '供应商', '至', '请',
          '情况', '本', '并', '时', '对', '在', '地址', '管理', '将', '个', '文件', '工程', '万元', '方式', '为', '日', '联系人', '人', '号', '时间',
          '及', '单位', '有限公司', '采购', '年', '的', '项目', '公示期', 'RAR', 'ZIP', '7Z', 'TXT', 'XML', 'WORD', 'XLSX', 'BMP',
          'JPG', 'JPEG', 'PNG'}


# 移除分词列表中的停用词
def cut_stops_terms(txts, stops):
    terms = []
    for n in txts:
        if n in stops:
            continue
        terms.append(n)
    return terms


# 计算tf-idf关键词
def calc_idf_keywords(txts, idf_dict, topk):
    tf_dict = {}
    calc_tf(txts, tf_dict)
    ks = idf_keywords(tf_dict, idf_dict)
    return topK(ks, topk)


# 计算TextRank关键词
def calc_tr_keywords(txts, idf_dict, topk):
    tr = TextRank.rank(txts)
    return ext_topK(tr, topk, idf_dict)


# 按文字顺序txts输出关键词集合keys的结果
def txt_order_by(txts, keys, topk):
    rst = []
    for t in txts:
        if t in keys:
            rst.append(t)
            keys.remove(t)
            if len(keys) == 0:
                break
            if topk and len(rst) >= topk:
                break
    return rst


# 计算复合算法下的关键词短语列表
def calc_keywords(txts, idf_dict, topk=12, TR=True, word_order=True, stops=_STOPS):
    if stops:
        txts = cut_stops_terms(txts, stops)

    kw1 = calc_idf_keywords(txts, idf_dict, topk)
    keys = set([k[0] for k in kw1])

    if TR:
        kw2 = calc_tr_keywords(txts, idf_dict, topk)
        skw2 = set([k[0] for k in kw2])

        keys = skw2.union(keys)

    if not word_order:
        if topk and len(keys) > topk:
            return list(keys)[:topk]
        return list(keys)

    # 按文字顺序输出结果
    return txt_order_by(txts, keys, topk)
