class converge_tree_t:
    """基于树结构进行词汇计数聚合分析的工具类"""

    class node_t:
        """树节点"""

        def __init__(self, words='', tag=None):
            self.count = 0  # 当前字符出现的次数,0为root节点
            self.words = words  # 当前级别对应词汇,''为root节点
            self.rate = None  # 当前节点占父节点的数量比率,在end之后才有效
            self.tag = tag  # 该节点首次被创建时对应的源数据标记
            self.childs = {}  # 当前节点的子节点

        def __repr__(self):
            return f"""words={self.words} count={self.count} rate={self.rate} tag={self.tag} childs={len(self.childs)}"""

    def __init__(self, reversed=False):
        self.root = self.node_t()
        self.reversed = reversed  # reversed告知是否为逆向遍历

    def add(self, txt, limited=-1, cnt=1, tag=None):
        """添加文本txt,进行计数累计.limited告知是否限定遍历长度"""
        lmt = 0
        if self.reversed:
            iter = range(len(txt) - 1, -1, -1)
        else:
            iter = range(len(txt))

        node = self.root
        for i in iter:
            if limited != -1 and lmt >= limited:
                break
            lmt += 1
            char = txt[i]
            if char not in node.childs:
                node.childs[char] = self.node_t(txt[i:] if self.reversed else txt[:i], tag)  # 确保当前字符在当前节点的子节点中
            node = node.childs[char]  # 得到当前字符对应的子节点
            node.count += cnt  # 累计字符数量

        return lmt

    def end(self):
        """统计子节点对父节点的占比"""

        def cb_func(paths, child, parent):
            rate = 1 if parent.count == 0 else child.count / parent.count
            child.rate = round(rate, 4)

        self.lookup(1, cb_func)

    def lookup(self, counts=1, cb=None):
        """遍历树节点,使用回调函数cb进行处理.counts限定节点计数."""

        def cb_func(paths, child, parent):
            """返回值:True停止当前分支的继续递归;其他继续递归"""
            print('\t' * (len(paths) - 1), child)
            if child.rate == 1 and len(child.words) > 1:
                return True

        if cb is None:
            cb = cb_func

        paths = []  # 对外输出的节点完整路径信息

        def loop(node):
            chars = sorted(node.childs.keys(), key=lambda k: (node.childs[k].count, k))
            for char in chars:
                child = node.childs[char]
                paths.append((char, child.count))
                stop = None
                if child.count >= counts:
                    stop = cb(paths, child, node)  # 只有超过限额计数的节点,才对外输出
                if not stop:
                    loop(child)  # 递归遍历当前子节点
                paths.pop(-1)

        loop(self.root)  # 从根节点进行遍历


class words_trie_t:
    """轻量级词汇匹配树"""

    def __init__(self, reversed=False):
        self.root = {}
        self.reversed = reversed  # reversed告知是否为逆向遍历

    def add(self, word):
        """添加词汇word"""

        if self.reversed:
            iter = range(len(word) - 1, -1, -1)
        else:
            iter = range(len(word))

        ret = 0
        node = self.root
        for i in iter:
            char = word[i]
            if char not in node:
                node[char] = {}  # 确保当前字符节点存在
                ret += 1
            node = node[char]  # 指向下级节点
        return ret  # 返回值告知新登记的字符数量

    def lookup(self, cb=None):
        """遍历树节点,使用回调函数cb进行处理."""

        def cb_func(paths, child, parent):
            """返回值:True停止当前分支的继续递归;其他继续递归"""
            print(paths, ' ' * (len(paths) - 1), child)

        if cb is None:
            cb = cb_func

        paths = []  # 对外输出的节点完整路径信息

        def loop(node):
            for char in node:
                child = node[char]
                paths.append(char)
                if not cb(paths, child, node):
                    loop(child)  # 递归遍历当前子节点
                paths.pop(-1)

        loop(self.root)  # 从根节点进行遍历

    def find(self, word):
        """查找指定的词汇是否存在.
            返回值:(deep,node)
                deep=0          - 不匹配:node为root;
                deep=len(word)  - 匹配:node为{}空字典则为完整匹配,否则为半匹配;
                0<deep<len(word)- 部分匹配:node为下级节点
        """
        if not word:
            return 0, self.root

        if self.reversed:
            iter = range(len(word) - 1, -1, -1)
        else:
            iter = range(len(word))

        deep = 0
        node = self.root
        for i in iter:
            char = word[i]
            if char not in node:
                return deep, node
            deep += 1
            node = node[char]  # 指向下级节点
        return deep, node


words = words_trie_t()
words.add('123')
words.add('1234')
words.add('12345')
words.find('234')
words.find('12')
words.find('123')
words.find('12345')
words.lookup()
