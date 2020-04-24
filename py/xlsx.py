import xlsxwriter
import hashlib

'''
excel文件生成器,每次生成都会覆盖原有内容

xw = xlsx_writer('tst.xlsx')
xw.create('表格1', ['列1', '列2'])
xw.append(('v10', 'v11'))
xw.appendx([('v20', 'v21'),('v30', 'v31')])

xw.create('表格2', ['列1', '列2'])
xw.append(('v10', 'v11'))
xw.append(('v11', 'v12'))
xw.close()

'''


class xlsx_writer:
    def __init__(self, fname, keyIdx=0):
        # 打开文件
        self.book = xlsxwriter.Workbook(fname)
        # 定义单元格样式
        self.cell_style = self.book.add_format({
            'text_wrap': False,
            'valign': 'vcenter',
            'align': 'fill',
        })
        self.sheet = None
        self.rows = 0
        self.keys = None
        self.keyIdx = keyIdx

    def md5(self, str):
        return hashlib.md5(str.encode('utf-8')).hexdigest()

    def _calc_key(self, line):
        if type(self.keyIdx).__name__ == 'int':
            return self.md5(line[self.keyIdx])
        else:
            ks = ''.join(line[self.keyIdx[0]:self.keyIdx[1] + 1])
            return self.md5(ks)

    def create(self, sheet_name, cols=None):
        """创建数据表,告知表名与列头"""
        self.sheet = self.book.add_worksheet(sheet_name)

        self.keys = set()
        # 添加列头
        if cols:
            self.rows = 0
            for i in range(len(cols)):
                self.sheet.write(self.rows, i, cols[i])
        else:
            self.rows = -1

    def append(self, t):
        """追加一个元组"""
        if not self.sheet:
            return -1
        key = self._calc_key(t)
        if key in self.keys:
            return 0
        self.rows += 1
        for col in range(len(t)):
            self.sheet.write(self.rows, col, t[col])
        self.keys.add(key)
        return 2

    def appendx(self, lst):
        """追加元组列表"""
        for t in lst:
            self.append(t)

    def close(self):
        """关闭文档保存内容"""
        if not self.sheet:
            return
        self.book.close()
        self.keys = None
        self.book = None
        self.sheet = None