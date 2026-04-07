import util_base as ub
from tqdm import tqdm
import sys

def file_loop(src, cb, title, src_encode='utf-8', bats=1, igs_cb=None,cln_cb=None):
    """循环处理过程的扩展,基于文件尺寸进行进度条的显示
        src: 文件名,或util_base.read_lines_t对象
        cb: 处理文件内容的回调函数
        title: 用于进度提示的标题串
        src_encode: src文件的编码格式
        bats: cb处理时,是否为批量模式,bats<=1为逐行模式.
        igs_cb: 可对待处理的内容行进行忽略性过滤处理的回调函数
    """
    if isinstance(src, str):
        src = ub.read_lines_t(src, src_encode)

    if src.fp is None:
        print('file open error', src.fname)
        return -1

    feat = ub.eat_file_size(src.fp)
    progs = tqdm(total=feat.total(), file=sys.stderr, desc=title)

    def _igs_cb(txt, row):
        if not txt or txt.startswith('#'):
            return True

    if igs_cb is None:
        igs_cb = _igs_cb

    def cb_warp(line, row):
        txt = line.strip()
        if cln_cb:
            txt=cln_cb(txt)

        if row % 100 == 0:
            progs.update(feat.eat())
        if igs_cb(txt, row):
            return

        r = cb(txt, row)
        if r:
            return r

    cache = []
    rows = []

    def cb_warps(line, row):
        nonlocal cache, rows
        txt = line.strip()
        if cln_cb:
            txt=cln_cb(txt)
        if row % 100 == 0:
            progs.update(feat.eat())
        if igs_cb(txt, row):
            return

        cache.append(txt)
        rows.append(row)
        if len(cache) < bats:
            return
        r = cb(cache, rows)
        cache = []
        rows = []
        if r:
            return r

    if bats <= 1:
        src.loop(cb_warp, True)
    else:
        src.loop(cb_warps, True)
        if cache:
            cb(cache, rows)
        cb([], [])  # 给出最后的结束通知

    progs.update(feat.eat())
