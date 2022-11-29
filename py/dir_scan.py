# -*- coding: utf-8 -*-

import os
import stat


class event_handler_t:
    """目录扫描器的事件响应处理器"""

    def __init__(self):
        pass

    def on_file(self, path, file, deep):
        """遍历发现了文件"""
        print("%3d F %s\\%s" % (deep, path, file))

    def on_dir(self, path, dir, deep):
        """遍历发现了目录"""
        # print("%3d D %s\\%s" % (deep, path, dir))

    def on_err(self, errno, path, deep, isdir, e):
        """出现了错误"""
        T = 'D' if isdir else 'F'
        print("%3d %s errno=%d(%s) %s" % (deep, T, errno, os.strerror(errno), path))


class dir_scaner_t:
    """目录扫描器"""

    def __init__(self, handler=None):
        self._handler = handler
        if self._handler is None:
            self._handler = event_handler_t()

        self._cnt_files = None
        self._cnt_dirs = None
        self._cnt_errs = None
        self._deep = None

    def _on_err(self, e):
        self._cnt_errs += 1
        isdir = False
        try:
            st = os.stat(e.filename)
            isdir = stat.S_ISDIR(st.st_mode)
        except:
            pass
        self._handler.on_err(e.errno, e.filename, self._deep, isdir, e)

    def _loop(self, irlen, ls):
        if not ls:
            return

        for root, dirs, files in ls:
            self._deep = len(root[irlen:].split(os.path.sep))
            for file in files:  # 遍历当前的所有文件
                try:
                    self._cnt_files += 1
                    if self._handler.on_file(root, file, self._deep):
                        return
                except:
                    pass

            for dir in dirs:  # 遍历当前的所有子目录
                self._cnt_dirs += 1
                if self._handler.on_dir(root, dir, self._deep):
                    return

    def loop(self, path, topdown=True, followlinks=False):
        """遍历扫描指定的目录path,topdown是否遍历广度优先,followlinks是否遍历符号连接指向的目录"""
        self._cnt_files = 0
        self._cnt_dirs = 0
        self._cnt_errs = 0
        self._deep = 0
        ls = None
        try:
            ls = os.walk(path, topdown, self._on_err, followlinks)
        except:
            self._cnt_errs += 1
            return self._cnt_dirs, self._cnt_files, self._cnt_errs

        self._loop(len(path), ls)
        return self._cnt_dirs, self._cnt_files, self._cnt_errs
