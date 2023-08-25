import numpy as np


class std_hmm_t:
    """标准HMM算法功能实现.要求:状态值从0开始,有status_N个;观测值从0开始,有observed_M个"""

    def __init__(self, status_N=3, observed_M=65535):
        self.N = status_N  # 状态集合元素数量(状态数BIO)
        self.M = observed_M  # 观测集合元素数量(汉字)
        self._pre_status = -1  # 训练使用,记录上一次状态值,便于前后序列的分隔统计
        self.A = self.B = self.PI = None

    def train_begin(self):
        """训练开始,生成空的模型矩阵"""
        self.A = np.zeros((self.N, self.N))  # (N,N) 状态转移矩阵,某个状态转移到另外状态的概率
        self.B = np.zeros((self.N, self.M))  # (N,M) 发射矩阵,某个状态下对应出现每个观测值的概率
        self.PI = np.zeros(self.N)  # (N,) 初始状态概率,观测序列首个观测值对应的状态概率

    def train_add(self, v, s):
        """添加训练要素:s-状态值;v-观测值.返回值:是否添加成功"""
        if s == -1 or v >= self.M:
            self._pre_status = -1  # 当前状态无效,或当前值无效,则认为这是一次观测序列的分隔点
            return None

        if self._pre_status != -1:  # 观测序列是连续的
            self.A[self._pre_status, s] += 1  # 累积前后状态转移计数
        else:  # 上一个为分隔符
            self.PI[s] += 1  # 累积新观测序列的首状态计数

        self.B[s, v] += 1  # 累积当前状态对应观测值计数
        self._pre_status = s  # 迭代更新当前状态为上一次状态
        return True

    def train_end(self):
        """训练结束,生成模型参数矩阵.对数运算获取指数,用指数相减的方式代替传统除法,便于后续的矩阵运算"""
        try:
            epsilon = 1e-8
            self.PI[self.PI == 0] = epsilon  # 填充最小值
            self.PI = np.log(self.PI) - np.log(np.sum(self.PI))  # 计算初始状态概率指数

            self.A[self.A == 0] = epsilon  # 填充最小值
            self.A = np.log(self.A) - np.log(np.sum(self.A, axis=1, keepdims=True))  # 计算状态转移矩阵概率指数

            self.B[self.B == 0] = epsilon  # 填充最小值
            self.B = np.log(self.B) - np.log(np.sum(self.B, axis=1, keepdims=True))  # 计算发射矩阵概率指数
            return ''
        except Exception as e:
            return e

    def model_save(self, dst_path='./', tag='std'):
        """保存模型数据到dst_path路径,并可指定tag标识"""
        try:
            np.savetxt(f'{dst_path}/hmm_{tag}_A.csv', self.A, delimiter=',')
            np.savetxt(f'{dst_path}/hmm_{tag}_B.csv', self.B, delimiter=',')
            np.savetxt(f'{dst_path}/hmm_{tag}_PI.csv', self.PI, delimiter=',')
            return ''
        except Exception as e:
            return e

    def model_load(self, dst_path='./', tag='std'):
        """从指定的路径dst_path中装载指定tag标识的模型文件"""
        try:
            self.A = np.genfromtxt(f'{dst_path}/hmm_{tag}_A.csv', delimiter=',')
            self.B = np.genfromtxt(f'{dst_path}/hmm_{tag}_B.csv', delimiter=',')
            self.PI = np.genfromtxt(f'{dst_path}/hmm_{tag}_PI.csv', delimiter=',')
            return ''
        except Exception as e:
            return e

    def model_watch(self, col, dst='B', row=None):
        """查看目标模型dst中指定行row和列col的概率值"""
        if dst in {'A', 'a'}:
            if row is None:
                return self.A[:, col]
            elif col is None:
                return self.A[row,]
            else:
                return self.A[row, col]
        elif dst in {'B', 'b'}:
            if row is None:
                return self.B[:, col]
            elif col is None:
                return self.B[row,]
            else:
                return self.B[row, col]
        else:
            if col is None:
                return self.PI
            else:
                return self.PI[col]

    def predict(self, obs, sep_status=None):
        """使用维特比算法进行序列obs对应状态的预测,返回值:[预测的状态值列表],[有效区间列表(begin,end)]"""
        O = len(obs)  # 待预测的序列长度
        if O == 0:
            return [], None

        delta = np.zeros((self.N, O))  # delta计算前一个观测的所有状态到当前状态的最大概率
        psi = np.zeros((self.N, O), dtype=np.int32)  # 回溯路径矩阵,psi记录最大概率的前一个状态的位置

        # 因为模型矩阵中的概率值已经归一化为指数,所以下列矩阵运算中,加法操作就是概率相乘
        delta[:, 0] = self.PI + self.B[:, obs[0]]  # delta[:,0] 计算首个观测值对应每个状态的概率(self.B[:, obs[0]]为首个观测值对应每个状态的概率)
        # psi[:,0]=np.argmax(delta[:,0]) #默认值始终为0,不用计算
        for i in range(1, O):
            temp = delta[:, i - 1] + self.A.T  # 计算前一个观测的每个状态转移到当前状态的全部可能性
            psi[:, i] = np.argmax(temp, axis=1)  # psi[:,i] 到达当前观测的最大概率值的上一个状态的位置
            delta[:, i] = np.max(temp, axis=1) + self.B[:, obs[i]]  # delta[:,i] 更新到达当前观测序列的每个状态的最大概率值

        ret = [0] * O
        # 从delta的最后取最大值，利用psi向前回溯即可找到最大概率序列
        ret[-1] = np.argmax(delta[:, -1])
        for i in range(O - 2, -1, -1):
            ret[i] = psi[ret[i + 1]][i + 1]

        # 不进行状态分隔,直接返回
        if sep_status is None:
            return ret, None

        def find(pos):
            """在ret列表中,从pos位置开始,查找一个有效状态序列"""
            while pos < O and ret[pos] == sep_status:
                pos += 1
            begin = pos
            while pos < O and ret[pos] != sep_status:
                pos += 1
            end = pos
            return begin, end

        # 进行状态分隔统计
        seps = []
        pos = 0
        while pos < O:
            b, e = find(pos)
            if b != e:
                seps.append((b, e))
            pos = e
        return ret, seps


class train_hmm_t:
    """对hmm进行标注训练处理的功能适配器"""

    def __init__(self, dstpath, tag, SN=3, OM=65535):
        self.hmm = std_hmm_t(SN, OM)  # HMM功能对象
        self.tag = tag
        self.dstpath = dstpath

    def on_begin(self):
        self.hmm.train_begin()

    def on_end(self):
        self.hmm.train_end()
        return self.hmm.model_save(self.dstpath, self.tag)

    def on_add(self, row, rc):
        """对row正文和已知nt进行预处理,生成训练数据"""
        self.hmm.train_add(row[1], row[0])


class trains_all_t(train_hmm_t):
    """对hmm进行标注训练处理的功能转发适配器,便于一次性训练多个模型"""

    def __init__(self):
        self.makers = []

    def on_begin(self):
        for maker in self.makers:
            maker.on_begin()

    def on_end(self):
        for maker in self.makers:
            maker.on_end()

    def on_add(self, row, rc):
        """对row正文和已知nt进行预处理,生成训练数据"""
        for maker in self.makers:
            maker.on_add(row, rc)



def train_from_file(hmm: train_hmm_t, fn_label, cb_parse=None):
    """基于标注样本文件fn_label,对hmm进行训练的通用方法.
        要求每一行有两个元素,文字和状态序号,使用逗号进行分隔.
        返回值:(样本数量,错误信息)
    """

    def get_file_size(f):
        """通过打开的文件获取其字节大小"""
        pos = f.tell()
        f.seek(0, os.SEEK_END)
        ret = f.tell()
        f.seek(pos, os.SEEK_SET)
        return ret

    def parse(pre, line):
        """默认的行解析方法"""
        p = line.split(',')
        v = ord(p[0])
        s = int(p[-1])
        return v, s

    if cb_parse is None:
        cb_parse = parse

    try:
        hmm.on_begin()  # 准备训练
        fr = open(fn_label, 'r', encoding='utf-8')
        cnt = 0
        old_pos = 0
        pre = None  # 前一行模型数据
        bar = tqdm.tqdm(total=get_file_size(fr))  # 定义进度条
        line = fr.readline()
        while line:
            cnt += 1
            if cnt % 1000 == 0:  # 间隔刷新进度条
                pos = fr.tell()
                bar.update(pos - old_pos)  # 更新本轮文件长度的增量
                old_pos = pos
            v, s = cb_parse(pre, line)  # 解析当前行(附带告知前一行)得到观测值与对应状态
            hmm.on_add((v, s), cnt)  # 迭代训练HMM模型
            pre = line
            line = fr.readline()

        # 完成训练
        return cnt, hmm.on_end()
    except Exception as e:
        return None, e
