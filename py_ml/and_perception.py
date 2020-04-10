'''
零基础入门深度学习(1) - 感知器
https://www.zybuluo.com/hanbingtao/note/433855
'''

from functools import reduce


class Perceptron(object):
    def __init__(self, input_num, activator):
        '''
        初始化感知器，设置输入参数的个数，以及激活函数。
        激活函数的类型为double -> double
        '''
        self.activator = activator
        # 权重向量初始化为0
        self.weights = [0.0 for _ in range(input_num)]
        # 偏置项初始化为0
        self.bias = 0.0

    def __str__(self):
        '''
        打印学习到的权重、偏置项
        '''
        return 'weights\t:%s\nbias\t:%f\n' % (self.weights, self.bias)

    def predict(self, input_vec):
        '''
        根据输入向量，计算输出感知器的计算结果
        '''
        # 把input_vec[x1,x2,x3...]和weights[w1,w2,w3,...]打包在一起
        ivw = list(zip(input_vec, self.weights))  # 变成[(x1,w1),(x2,w2),(x3,w3),...]
        # 然后利用map函数计算[x1*w1, x2*w2, x3*w3]
        ivw_sums = list(map(lambda v: v[0] * v[1], ivw))
        # 利用reduce求和
        sum = reduce(lambda a, b: a + b, ivw_sums, 0.0) + self.bias
        # 调用激活函数给出结果
        return self.activator(sum)

    def train(self, input_vecs, labels, iteration, rate):
        '''
        输入训练数据：输入样本向量集、输入的期待结果集labels,训练轮数、学习率
        '''
        # 把输入和期待输出打包在一起，成为样本的列表[(input_vec, label), ...]
        samples = list(zip(input_vecs, labels))  # 每个训练样本是(input_vec, label)

        for i in range(iteration):
            # 用样本数据循环迭代进行训练
            for (input_vec, label) in samples:
                # 计算感知器在当前权重下的输出
                output = self.predict(input_vec)
                # 对每个样本，按照感知器规则更新权重
                self._update_weights(input_vec, output, label, rate)

    def _update_weights(self, input_vec, output, label, rate):
        '''
        按照感知器规则更新权重
        '''
        # 把input_vec[x1,x2,x3,...]和weights[w1,w2,w3,...]打包在一起
        ivw = list(zip(input_vec, self.weights))  # 变成[(x1,w1),(x2,w2),(x3,w3),...]
        # 然后利用感知器规则更新权重
        delta = label - output
        self.weights = list(map(lambda v: v[1] + rate * delta * v[0], ivw))
        # 更新bias
        self.bias += rate * delta


def train_and_perceptron():
    '''
    使用and真值表训练感知器
    '''

    def f(x):
        '''
        定义激活函数f
        '''
        return 1 if x > 0 else 0

    # 创建感知器，输入参数个数为2（因为and是二元函数），激活函数为f
    p = Perceptron(2, f)

    # 输入向量集
    input_vecs = [[1, 1], [0, 0], [1, 0], [0, 1]]
    # 期望的输出集，要与输入一一对应
    labels = [1, 0, 0, 0]

    # 训练，迭代n轮, 学习速率为0.1
    p.train(input_vecs, labels, 5, 0.1)
    # 返回训练好的感知器
    return p


if __name__ == '__main__':
    # 训练and感知器
    and_perception = train_and_perceptron()
    # 打印训练获得的权重
    print(and_perception)

    # 定义输出测试函数
    def test(a, b):
        print('%d and %d = %d' % (a, b, and_perception.predict([a, b])))

    # 测试
    test(1, 1)
    test(0, 0)
    test(1, 0)
    test(0, 1)

'''
    学习后记:
        1 训练迭代的次数应该可以进行动态优化,迭代一定次数后如果w/b参数不再变化则可以停止训练,提高效率.
        2 调整训练调用处的参数,迭代次数和学习速率,可以观察训练次数太少时不能达到预期效果;学习速率调整后w/b参数的值也会跟随改变
        3 最终预测的时候,可以调整入参,会发现训练好的w/b参数有一定的容错能力,但入参偏离样本值太大的时候,结果也是不准确的,证明了训练集与预测集之间的相关性.
'''