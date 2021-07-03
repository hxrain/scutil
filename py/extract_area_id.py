import china_area_id as cai
import dfa_match as dm


class addr_analyse_t:
    """基于给定的文本,分析可能的行政区划地点"""

    def __init__(self):
        self.dfa = dm.dfa_match_t()  # 用DFA引擎装载省市区县名称与对应的区划代码
        for name in cai.map_area_ids:
            ids = cai.map_area_ids[name]
            self.dfa.dict_add(name, ids)

    def extract(self, txt):
        """根据给定的文本,尝试分析其中出现过最基层(区县或市或省)的行政代码.返回值:[区划代码]或None"""
        mrs = self.dfa.do_check(txt, max_match=True, isall=True, skip_match=True)
        mrs_len = len(mrs)
        if mrs_len == 0:
            return None

        rst = []  # 最终结果,分组集合列表

        def _rec_rst(res):
            if res in rst:
                return
            dels = []
            for old in rst:
                if cai.check_depen(res, old):
                    return  # 待记录的区域比已有区域大,不记录了.
                if cai.check_depen(old, res):
                    dels.append(old)  # 如果待记录的区域比已有区域小,则准备删除已有区域.

            for d in dels:
                rst.remove(d)

            rst.append(res)

        def az_one(ids):
            """分析单组检索结果(组内多个区划代码的细分处理)"""
            if not isinstance(ids, list):
                ids = list(ids)

            ids_len = len(ids)
            if ids_len == 1:
                _rec_rst({ids[0]})  # 单名区划代码,直接放入最终结果
                return

            res = set()
            pc_groups = cai.grouping(ids)  # 将待处理同名区划代码按省分组
            for pc in pc_groups:
                pc_ids = pc_groups[pc]  # 省内同名区划代码字典
                for ci in pc_ids:
                    ci_ids = pc_ids[ci]  # 市级同名区划代码
                    res.add(min(ci_ids))  # 取范围大的结果(区划代码的最小值),比如: 阜新 => 阜新市/阜新县 => 阜新市
            _rec_rst(res)

        last_deps = mrs[0][2]
        if mrs_len == 1:  # 只有一个区划名称被匹配,分析结果后直接返回
            az_one(last_deps)
            return rst

        for mi in range(1, mrs_len):
            prev_mr = mrs[mi - 1]  # 前一个地名检索结果
            curr_mr = mrs[mi]  # 得到当前的地名检索结果
            isbk = curr_mr[0] - prev_mr[1] >= 10  # 判断前后两个地名的字间距是否过远
            deps = cai.check_depen(prev_mr[2], curr_mr[2])  # 判定从属关系

            if deps:  # 从属关系存在的情况
                if isbk:  # 两个地名相距过远时,也需要单独记录前一个地名
                    az_one(prev_mr[2])

                if mi == mrs_len - 1:
                    az_one(deps)  # 如果循环即将结束,那么当前地名从属关系就是最后的结果
                else:
                    last_deps = deps  # 否则尝试等待下一次判定
            else:  # 本次前后地名的从属判定是不相关的
                az_one(last_deps)  # 则记录上一次的最后结果
                if mi == mrs_len - 1:
                    az_one(curr_mr[2])  # 如果循环马上结束了,那么就记录当前的最后结果
                else:
                    last_deps = list(curr_mr[2]) #否则当前区划信息留存到下次处理

        return rst

    def query(self, txt):
        """根据给定的文本,尝试分析其中出现过的行政区划层级地址.返回值:[(省,市,区县)]或None"""
        id_grops = self.extract(txt)
        if id_grops is None:
            return None

        rst = []
        for ids in id_grops:
            for id in ids:
                lst = cai.split_ex(id)
                if lst:
                    rst.append([str(id), *lst[0]])  # 记录[区划id,以及区划分级名字列表]
        return rst
