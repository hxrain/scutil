import util_base as ub


class lru_fifo_t:
    """先进先出保留固定数量的最近使用记录"""

    def __init__(self, fname=None, limit=1000):
        self._ids = set()
        self._dat = {'limit': limit, 'lst': []}
        self._fname = fname
        self.load()
        self.limit(limit)

    def load(self):
        """装载"""
        if self._fname is None:
            return True
        dat = ub.dict_load(self._fname, 'utf-8')
        if dat is None:
            return False
        self._dat = dat
        for iid in self._dat['lst']:
            self._ids.add(iid)
        return True

    def limit(self, newlimit=None):
        """获取或设置新的数量上限;新上限小于原上限的时候,则清理部分旧数据"""
        oldlimit = self._dat['limit']
        if newlimit is None:
            return oldlimit

        self._dat['limit'] = newlimit
        if oldlimit > newlimit:
            rmcnt = len(self._ids) - newlimit
            if rmcnt > 0:
                for i in range(rmcnt):
                    iid = self._dat['lst'].pop(0)
                    self._ids.remove(iid)
        return newlimit

    def size(self):
        """获取现有元素数量"""
        return len(self._ids)

    def hit(self, iid, add=False):
        """判断给定的标识是否存在;如果不存在,则进行追加;返回值:True已存在,False不存在"""
        if iid in self._ids:
            return True

        if not add:
            return False

        if len(self._ids) >= self._dat['limit']:
            old = self._dat['lst'].pop(0)
            self._ids.remove(old)

        self._dat['lst'].append(iid)
        self._ids.add(iid)
        return False

    def save(self):
        """将内部状态存盘"""
        if self._fname is None:
            return False
        return ub.dict_save(self._fname, self._dat, 'utf-8')
