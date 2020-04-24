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


# 导出结果到excel文件
def export_rst(file='./公司失信处罚记录.xlsx', sheet='北京'):
    workbook = xlsxwriter.Workbook(file)
    worksheet = workbook.add_worksheet(sheet)
    # 单元格样式
    col_format = workbook.add_format({
        'text_wrap': False,
        'valign': 'vcenter',
        'align': 'fill',
    })
    heads = ['公司名称', '失信记录', '违规记录']
    for i in range(len(heads)):
        worksheet.write(0, i, heads[i])

    # 查询待处理记录
    try:
        rows = db_conn.query(
            "select b.cops_name,a.punish_infos,a.illegal_infos from tbl_cops_cert a left JOIN active_record b on a.cops_id=b.cops_id where a.punish_infos<>'' and a.batid=%d" % (
                batid))
    except Exception as e:
        spd_logger.warning('DB结果查询错误 <%s> :: %s' % (file, str(e)))
        return None, str(e)

    def conv(s):
        return s.replace('<?xml version="1.0" ?>\n', '') \
            .replace('\t', '    ') \
            .replace('<结果>', '<条目>').replace('</结果>', '</条目>')

    r = 1
    for row in rows.all():
        worksheet.write(r, 0, row.cops_name)
        worksheet.write(r, 1, conv(row.punish_infos), col_format)
        worksheet.write(r, 2, conv(row.illegal_infos), col_format)
        r += 1

    workbook.close()
