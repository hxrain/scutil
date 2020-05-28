from collections import defaultdict


class TextRank:
    class weightGraph:
        '''用于计算各个节点与边的相关度的权重图功能封装'''
        d = 0.85  # TextRank的经验系数d

        def __init__(self):
            self.graph = defaultdict(list)  # 使用value为list的字典,记录图的每个节点对应的全部的边列表

        def addEdge(self, start, end, freq):
            '''给图中添加要素,由"开始节点/结束节点/边的频次"构成'''
            self.graph[start].append((start, end, freq))  # 对于开始节点,追加'正向边'
            self.graph[end].append((end, start, freq))  # 对于结束节点,追加'逆向边'

        def calc(self, iters=10):
            '''计算当前图结构中每个节点的权重结果,可控制迭代次数'''
            weights = defaultdict(float)  # 记录每个节点的最终权重结果字典
            outSum = defaultdict(float)  # 记录每个节点的出度字典

            wsdef = 1.0 / (len(self.graph) or 1.0)  # 定义每个节点的初始权重
            for n, edges in self.graph.items():
                weights[n] = wsdef  # 设定每个节点的权重结果初值
                outSum[n] = sum((e[2] for e in edges), 0.0)  # 累计每个节点与所有相关节点的频次和作为当前节点的出度

            # 可以对图中节点进行排序,确保迭代结果的稳定性
            # sorted_keys = sorted(self.graph.keys())
            sorted_keys = self.graph.keys()

            for x in range(iters):  # 迭代计算指定的次数
                for n in sorted_keys:  # 对于每个节点进行相关度计算
                    s = 0
                    for e in self.graph[n]:  # 对于每个节点的全部边进行迭代
                        # 边的频次*边的终点权重/边的终点出度,作为本节点的贡献度(PageRank和TextRank算法的核心)
                        s += e[2] / outSum[e[1]] * weights[e[1]]
                    # 用当前节点的最新贡献度更新其权重
                    weights[n] = (1 - self.d) + self.d * s

            # 全部迭代完成,准备筛选节点权重的最大和最小值
            (min_rank, max_rank) = (0, 0)
            for n, w in weights.items():
                if w < min_rank:
                    min_rank = w
                if w > max_rank:
                    max_rank = w

            # 利用节点权重的最大最小值进行每个节点权重的归一化
            for n, w in weights.items():
                weights[n] = (w - min_rank / 10.0) / (max_rank - min_rank / 10.0)

            return weights

    @staticmethod
    def rank(words, span=5, iters=10):
        """
            基于TextRank算法的短语提取函数
            words为句子分词后的词列表;iters为迭代计算次数
            span 为节点相似度计算的前后跨度
            返回值为defaultdict类型的字典,记录每个词条与对应的权重

        """
        graph = TextRank.weightGraph()  # 用于rank权重计算的图结构对象
        freqs = defaultdict(int)  # 记录'词条对'出现频次的字典

        for i, word in enumerate(words):  # 对输入的词列表进行遍历
            for j in range(i + 1, i + span):  # 对当前词与之后的跨度范围内的词进行遍历
                if j >= len(words):
                    break
                freqs[(word, words[j])] += 1  # 当前词与后续词组成了'词条对',并且累计其出现的次数

        for terms, freq in freqs.items():  # 用累计后的'词条对'频次数据进行图结构的构造
            graph.addEdge(terms[0], terms[1], freq)

        return graph.calc(iters)  # 进行迭代计算,得到每个词的权重
