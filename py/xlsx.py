import xlsxwriter

from hash_util import *

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


class xlsx_sheet:
    def __init__(self, keyIdx=0):
        self.sheet = None
        self.rows = 0
        self.keys = None
        self.keyIdx = keyIdx

    def append(self, t, fmts=None):
        """追加一个元组"""
        if not self.sheet:
            return -1

        if self.keys:
            key = calc_key(t, self.keyIdx)
            if key in self.keys:
                return 0
            self.keys.add(key)

        if fmts is None:
            fmts = [0] * len(t)

        self.rows += 1
        for col in range(len(t)):
            self.sheet.write(self.rows, col, t[col], self.cell_style[fmts[col]])

        return 2

    def appendx(self, lst):
        """追加元组列表"""
        for t in lst:
            self.append(t)


class xlsx_maker:
    def __init__(self, fname):
        # 打开文件
        self.book = xlsxwriter.Workbook(fname)
        # 定义单元格样式
        self.cell_style = []
        self.add_style({
            'text_wrap': False,
            'valign': 'vcenter',
            'align': 'left',
        })

    def add_style(self, styles_dict):
        fmt = self.book.add_format(styles_dict)
        self.cell_style.append(fmt)
        return len(self.cell_style) - 1

    def create(self, sheet_name, cols=None, chk_keys=True):
        """创建数据表,告知表名与列头"""
        s = xlsx_sheet()
        s.sheet = self.book.add_worksheet(sheet_name)
        s.cell_style = self.cell_style

        if chk_keys:
            s.keys = set()

        # 添加列头
        if cols:
            s.rows = 0
            for i in range(len(cols)):
                s.sheet.write(s.rows, i, cols[i])
        else:
            s.rows = -1
        return s

    def close(self):
        """关闭文档保存内容"""
        self.book.close()


class xlsx_writer:
    def __init__(self, fname, keyIdx=0):
        self.maker = xlsx_maker(fname)
        self.sheet = None

    def add_style(self, styles_dict):
        self.maker.add_style(styles_dict)

    def create(self, sheet_name, cols=None, chk_keys=True):
        """创建数据表,告知表名与列头"""
        self.sheet = self.maker.create(sheet_name, cols, chk_keys)

    def append(self, t, fmts=None):
        """追加一个元组"""
        return self.sheet.append(t, fmts)

    def appendx(self, lst):
        """追加元组列表"""
        return self.sheet.appendx(t)

    def close(self):
        """关闭文档保存内容"""
        if not self.sheet:
            return
        self.maker.close()
        self.sheet = None
