"""
    html/table布局分析模块,根据table中的rowspan/colspan将表格填充为完整归一化的格子.
"""
from util_base import *
from util_xml import *
import copy


def html_query_table(html, drop_multi=True):
    """尝试从html中提取table文本段列表"""
    tbls, msg = query_xpath_x(html, '//table', fixNode=None)  # 先查询所有表格
    if drop_multi:
        rst = []
        for t in tbls:
            r, msg = query_re(t, '<table.*<table')  # 判断并丢弃多级表格
            if len(r):
                continue
            rst.append(t)  # 记录单级表格
        return rst
    else:
        return tbls


def table_parse(html, node_filter=None):
    """将html/table串解析为元数据的二维矩阵.返回值(tr数量,td数量,元数据矩阵)"""

    def _get_td_val(cell):
        nodes = get_tag_child(cell, 'td|th')
        if len(nodes) == 0:
            return ''
        node = nodes[0]
        if node_filter is None:
            return node
        return node_filter(node)

    mates = []
    td_nodes = []
    nb_col = 0

    tr_list = query_xpath_x(html, '//tr', None)[0]  # 提取所有的tr行
    for i_tr, tr in enumerate(tr_list):  # 对每个tr行遍历
        mates.append([])  # 准备记录当前tr行的元信息
        td_th_list = query_xpath_x(tr, '//th|//td', None)[0]  # 提取当前tr行中的td或th节点
        td_nodes.append(td_th_list)  # 记录原始的tr/td行列文本串
        for i_td, cell in enumerate(td_th_list):  # 对当前行的每个节点遍历
            # Calculate rowspan and colspan
            colspan_val = query_re_num(cell, """colspan\s*=\s*["']\s*(\d+)\s*["']""", 1)  # 尝试提取节点的列跨度
            rowspan_val = query_re_num(cell, """rowspan\s*=\s*["']\s*(\d+)\s*["']""", 1)  # 尝试提取节点的行跨度
            cell_info = {'span': (rowspan_val, colspan_val), 'node': _get_td_val(cell), 'ref': (i_tr, i_td)}  # 构造节点的元信息
            mates[-1].append(cell_info)  # 记录当前tr行的每个节点元信息
        nb_col = max(nb_col, len(td_th_list))  # 累计记录最大列数

    return len(tr_list), nb_col, mates, td_nodes


def table_extract(nb_row, nb_col, table):
    """根据表格分析结果,继续重构抽取表格数据,得到规整的表格矩阵.
        入参:元数据矩阵对应的tr行数,最大的td列数,元数据表格;
        返回值:抽取的表格按最小单元格组成矩阵
    """

    def _make_cell(i_row, i_col, val, nb_row, nb_col):
        """生成指定行列处的格子,如果行列不满足则添加新的矩阵行列"""
        while len(table) <= i_row:  # 尝试添加新的矩阵行
            table.append([])
            nb_row += 1  # 记录新增的行数

        row = table[i_row]  # 获取指定的行列表

        while len(row) < i_col:
            row.append(None)  # 尝试添加新行的占位空列,保留一列不添加
        new = copy.deepcopy(val)
        new['fake'] = True  # 标记当前
        row.insert(i_col, new)  # 在指定行列的位置,记录指定的值

        nb_col = max(nb_col, len(row))  # 尝试记录最新的最大列数
        return nb_row, nb_col

    # 对元数据的行列格子进行遍历处理
    i_col = 0
    while i_col < nb_col:  # 对全部的列进行外循环,有可能会动态扩展列宽
        i_row = 0
        while i_row < nb_row:  # 对每行进行内循环,有可能会动态扩展行高
            row = table[i_row]
            while len(row) <= i_col:  # 先尝试扩张当前行到达当前的列数
                row.append(None)

            cell = row[i_col]  # 得到当前节点的元数据
            if type(cell) is not dict or 'fake' in cell:
                i_row += 1
                continue  # 当前遍历的行列位置不是元数据,或是填充节点,则跳过当前行

            span = cell['span']
            for i_colspan in range(i_col, i_col + span[1]):
                for i_rowspan in range(i_row, i_row + span[0]):
                    # 对当前节点的行列跨度范围进行组合遍历
                    if i_colspan == i_col and i_rowspan == i_row:
                        continue  # 边缘不处理
                    nb_row, nb_col = _make_cell(i_rowspan, i_colspan, cell, nb_row, nb_col)  # 在当前节点的跨度范围内进行值填充,并扩展行列范围

            i_row += 1
        i_col += 1

    return table


def table2matrix(html, node_filter=None):
    """提取html字符串中table对应的行列矩阵.
        返回值,规范的行列填充二维数组矩阵:([[{'span': (1, 2), 'node': 'r1c3', 'ref': (0, 2), 'fake': True},None]],行列内容矩阵)
            span是当前格子占用的行列跨度;
            node记录当前td的节点内容(被预处理过,只有内容有效值,不是原始节点内容);
            ref记录当前格子对于原始tr/td列表的索引;
            fake如果存在,告知当前格子是否为填充生成的.
            对于没有值可引用的行列位置,存在None节点.
    """
    nb_row, nb_col, table, td_nodes = table_parse(html, node_filter)
    return table_extract(nb_row, nb_col, table), td_nodes
