# -*- coding: utf-8 -*-
"""
     CDP - Chrome DevTools Protocol
     这里封装一套CDP客户端,便于操控Chrome,完成高级爬虫相关功能.
"""

import logging
import spd_base as sb
import util_base as ub
import py_util
import util_curve as uv

from cdp.cdp_driver import driver_t
from cdp.cdp_tab import tab_t
from cdp.cdp_tab import browser_t


class spd_cdp_t:
    """基于CDP的爬虫功能主体"""
