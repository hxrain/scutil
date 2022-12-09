# -*- coding: utf-8 -*-

import argparse
import importlib
import sys

import gui_dlg as _gd
from db_sqlite import *
from mutex_lock import *
from spd_base import *
from spd_chrome import *

"""说明:
    这里基于spd_base封装一个功能更加全面的微型概细览采集系统.需求目标有:
    1 基于sqlite数据库,部署简单
    2 本采集系统用于专属领域的特定任务目标,不同领域建议使用不同的实例.
    3 核心概念有:
        A 采集源:代表对一个目标网站的一个频道或多个频道进行抓取的功能配置与参数
        B 爬虫:将采集源实例化并将其运行起来的任务功能;也有不依赖采集源的个性化爬虫.
        C 采集系统:运行调度多个爬虫并行或串行执行的整体.
        D 数据库:记录采集源信息;记录采集得到的细览信息与正文;
    4 核心采集流程为:
        采集源提供概览页面URL,且维护翻页逻辑;采集源维护概览采集所需HTTP头与参数,确保抓取概览页;
        爬虫根据采集源配置参数,获取概览URL,构造抓取概览页面的参数与验证码等前提条件,之后抓取概览页面.
        爬虫根据采集源配置参数,从概览页面中提取信息列表或细览URL列表,再根据采集源配置决定排重后是否入库.
        爬虫循环细览URL列表,构造抓取概览页面的参数与验证码等前提条件,之后抓取细览页面.
        爬虫根据采集源配置参数,从细览页面中提取信息,再根据采集源配置决定排重后是否入库.
        采集系统管理爬虫对象的生存周期,爬虫管理采集源对象的生存周期.
        采集系统记录采集源的任务执行情况,统计整体采集运行情况.
"""

"""采集源表结构(tbl_sources)说明:
    id	            INTEGER     自增主键
    name	        TEXT        采集源名称,唯一索引
    site_url	    TEXT        采集源站点URL
    reg_time	    integer     采集源活动注册时间
    last_begin_time	integer     采集源最后的开始时间
    last_end_time	integer     采集源最后的结束时间
    last_req_count	integer     采集源最后活动中的请求数量
    last_rsp_count	integer     采集源最后活动中的回应数量
    last_req_succ   integer     采集源最后活动中的请求完成数量
    last_infos_count integer    采集源最后活动中的有效信息数量
"""

"""信息主表(tbl_infos)字段说明:
    id	            INTEGER     自增主键
    source_id	    INTEGER     所属采集源id
    create_time	    integer     信息的创建时间,索引
    title	        TEXT        信息标题,可选,索引
    url	            TEXT        信息细览URL,索引
    content	        TEXT        信息正文内容,可选
    pub_time	    TEXT        信息发布时间,可选,索引
    addr	        TEXT        信息所属地址,可选
    keyword	        TEXT        信息关键词,可选
    ext	            TEXT        扩展信息,可选
    memo	        TEXT        信息备注说明,可选
"""

sql_tbl = ['''
           CREATE TABLE "tbl_sources" (
              "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
              "name" TEXT NOT NULL,
              "site_url" TEXT NOT NULL,
              "reg_time" integer NOT NULL,
              "last_begin_time" integer NOT NULL DEFAULT 0,
              "last_end_time" integer NOT NULL DEFAULT 0,
              "last_req_count" integer NOT NULL DEFAULT 0,
              "last_rsp_count" integer NOT NULL DEFAULT 0,
              "last_req_succ" integer NOT NULL DEFAULT 0,
              "last_infos_count" integer NOT NULL DEFAULT 0
           );
           ''',
           '''
           CREATE UNIQUE INDEX "idx_sources_name"
           ON "tbl_sources" (
             "name" ASC
           );
           ''',
           '''
           CREATE TABLE "tbl_infos" (
             "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
             "source_id" INTEGER NOT NULL,
             "create_time" integer NOT NULL,
             "title" TEXT,
             "url" TEXT NOT NULL,
             "content" TEXT,
             "pub_time" TEXT,
             "addr" TEXT,
             "keyword" TEXT,
             "ext" TEXT,
             "memo" TEXT
           );
           ''',
           '''
           CREATE INDEX "idx_infos_crttime"
           ON "tbl_infos" (
             "create_time"
           );
           ''',
           '''
           CREATE INDEX "idx_infos_pubtime"
           ON "tbl_infos" (
             "pub_time"
           );
           ''',
           '''
           CREATE INDEX "idx_infos_title"
           ON "tbl_infos" (
             "title"
           );
           ''',
           '''
           CREATE INDEX "idx_infos_url"
           ON "tbl_infos" (
             "url"
           );
           ''']

_logger = None  # 全局日志输出对象
_proxy = None  # 全局代理地址信息
lists_rate = 1  # 全局概览翻页倍率
info_upd_mode = False  # 是否开启采集源全局更新模式(根据排重条件查询得到主键id,之后更新此信息)
locker = lock_t()  # 全局多线程保护锁
locker_dg = lock_t()  # 全局多线程对话框锁
_cnt_input_vcode = 0  # 记录全局手动输入验证码的总数


# 绑定全局默认代理地址
def bing_global_proxy(str):
    global _proxy
    _proxy = str


# 设置全局概览翻页倍率
def set_lists_rate(r):
    global lists_rate
    lists_rate = r


# 设置是否开启采集源全局更新模式
def set_info_updmode(v):
    global info_upd_mode
    info_upd_mode = v


class info_t:
    """待入库的信息对象"""

    def __init__(self, source_id):
        self.source_id = source_id  # 信息所属采集源
        self.url = None  # 信息细览URL
        self.title = None  # 标题
        self.content = None  # 正文主体内容
        self.pub_time = None  # 信息发布时间
        self.addr = None  # 信息所属地域
        self.keyword = None  # 关键词
        self.ext = None  # 扩展的个性化字典信息
        self.memo = None  # 对此信息的备注说明


# 概览页为空的标识串
__EMPTY_PAGE__ = '__EMPTY__'


def query_cookie_value(cookies, name):
    """在cookies对象数组中查询对应名字的值"""
    for cookie in cookies:
        if cookie.get('name') == name:
            return cookie.get('value')
    return None


class source_base:
    """概细览采集源基类,提供概细览采集所需功能的核心接口与数据结构定义"""
    proxy = None

    def __init__(self):
        """记录采集源动作信息"""
        self.stat = {}  # 记录运行的状态码计数
        self.spider = None  # 运行时绑定的爬虫功能对象
        self.dbs = None  # 运行时绑定的数据功能对象
        self.order_level = 0  # 运行优先级,高优先级的先执行,比如需要人工交互的
        self.interval = 1000 * 60 * 30  # 采集源任务运行间隔
        self.id = None  # 采集源注册后得到的唯一标识
        self.name = None  # 采集源的唯一名称,注册后不要改动,否则需要同时改库
        self.url = None  # 采集源对应的站点url
        self.info_upd_mode = False  # 是否开启该信息源的更新模式
        self.proxy_addr = None  # 代理服务器地址,格式为 http://192.168.20.108:808
        self.http_timeout = 60  # http请求超时时间,秒
        self.chrome_timeout = 300  # chrome等待超时,秒
        self.item_combs = items_comb()  # 信息列表组合管理器，便于对多分类组合进行遍历抓取
        self.list_url_idx = 0  # 当前概览页号
        self.list_begin_idx = 0  # 初始概览页号
        self.list_url_cnt = 1  # 初始默认的概览翻页数量
        self.list_inc_cnt = 2  # 达到默认翻页数量上限的时候,如果仍有信息被采回,则进行自动增量翻页的数量
        self.list_max_cnt = 99999  # 概览翻页最大数量
        self.list_empty_re = None  # 用于判断当前概览页面是否为空的re表达式
        self.list_is_json = False  # 告知概览页面是否为json串,进而决定默认格式化方式
        self.page_is_json = False  # 告知细览页面是否为json串,进而决定默认格式化方式
        self.list_url_sleep = 0  # 概览翻页的延迟休眠时间
        self.page_url_sleep = 0  # 细览翻页的延迟休眠时间
        self.page_url_trys = 0  # 记录当前这是第几次重试抓取细览页
        self.last_list_items = -1  # 记录最后一次概览提取元素数量
        self.last_list_url = None  # 记录最后一次概览地址
        self.list_take_retry = 1  # 概览页面抓取并提取信息的动作重试次数
        self.page_take_retry = 1  # 细览页面抓取动作重试次数
        self.on_list_empty_limit = 3  # 概览内容提取为空的次数上限,连续超过此数量时概览循环终止
        self.on_list_rulenames = []  # 概览页面的信息提取规则名称列表,需与info_t的字段名字相符且与on_list_rules的顺序一致
        self.on_list_rules = []  # 概览页面的信息xpath提取规则列表
        self.on_check_repeats = []  # 概览排重检查所需的info字段列表
        self.on_pages_repeats = []  # 细览排重检查所需的info字段列表

    def log_warn(self, msg):
        _logger.warn('source <%s> :: %s' % (self.name, msg))

    def log_info(self, msg):
        _logger.info('source <%s> :: %s' % (self.name, msg))

    def log_error(self, msg):
        _logger.error('source <%s> :: %s' % (self.name, msg))

    def log_debug(self, msg):
        _logger.debug('source <%s> :: %s' % (self.name, msg))

    def rec_stat(self, code):
        """记录采集源运行的状态码计数统计"""
        v = self.stat.get(code, 0)
        self.stat[code] = v + 1

    def can_listing(self):
        """判断是否可以翻页"""
        max_cnt = min(self.list_max_cnt, lists_rate * self.list_url_cnt)
        return self.list_url_idx <= max_cnt

    def on_ready(self, req):
        """进行采集初始动作,也可进行必要的初始化或设置req请求参数.
            返回值:初始动作需要抓取的url地址,None则不抓取.
        """
        self.list_url_idx = self.list_begin_idx
        return None

    def on_ready_info(self, rsp):
        """如果on_ready返回了初始地址,则这里会进行抓取结果的处理.比如获取最初的cookie等内容,获取初始访问key;
            返回值:告知是否继续采集源的运行.
        """
        return True

    def on_end(self):
        """全部概细览动作完成,可进行最后的收尾动作"""

    def on_list_format(self, rsp):
        """返回列表页面的格式化内容,默认对html进行新xhtml格式化;返回值:None告知停止循环;__EMPTY_PAGE__为跳过当前概览页;其他为xml格式内容"""
        if self.list_empty_re and len(query_re(rsp, self.list_empty_re)[0]):
            return __EMPTY_PAGE__

        if self.list_is_json:
            ret = json2xml(rsp)[0]
        else:
            ret = format_xhtml(rsp)

        if self.list_empty_re and len(query_re(ret, self.list_empty_re)[0]):
            return __EMPTY_PAGE__

        return ret

    def on_list_begin(self, infos):
        """对一个概览页开始进行遍历处理之前的事件.infos记录已经抓取的信息数量"""
        pass

    def on_list_end(self, infos, news):
        """对一个概览页完成遍历处理之后的事件.infos记录已经抓取的信息总量,news为本次有效信息数量"""
        pass

    def on_page_format(self, rsp):
        """返回细览页面的格式化内容,默认对html进行新xhtml格式化"""
        if self.page_is_json:
            return json2xml(rsp)[0]
        else:
            return format_xhtml(rsp)

    def make_list_urlz(self, req):
        """生成概览列表url,self.list_url_idx从0开始;返回值:概览所需抓取的url,None则尝试调用make_list_url"""
        return None

    def make_list_url(self, req):
        """生成概览列表url,self.list_url_idx从1开始;返回值:概览所需抓取的url,None则停止循环"""
        return None

    def check_list_end(self, req):
        """判断概览翻页循环是否应该结束.返回值:None则停止循环"""
        if self.item_combs.next():  # 调整到下一个组合数据
            return None  # 如果组合循环点归零,说明全部排列组合都已循环一轮,可以真正结束了.
        self.on_next_plan()
        self.list_url_idx = self.list_begin_idx + self.check_list_adj  # 否则,翻页索引复位,准备继续抓取
        return True

    def on_next_plan(self):
        """item_combs组合器进行下一个组合值的生成时,可以进行相关的初始化动作"""
        pass

    def on_list_plan(self):
        """对一个概览页完成遍历处理之后的事件.可告知当前采集计划的进度总量信息(对于组合遍历时可大致告知总体进度)"""
        return self.item_combs.plan()

    def on_list_url(self, req):
        """告知待抓取的概览URL地址,填充req请求参数.返回None停止采集"""
        is_check_list_end = False
        self.check_list_adj = 0  # 告知概览检查处于的位置,并对应的调整计数.
        if not self.can_listing():
            rc = self.check_list_end(req)  # 给出判断机会,如果循环条件不允许了,翻页采集结束
            if rc is None: return None
            is_check_list_end = True

        self.last_list_url = self.make_list_urlz(req)  # 先尝试生成0序列的概览列表地址
        self.list_url_idx += 1  # 概览页索引增加
        if self.last_list_url is not None:
            return self.last_list_url

        self.check_list_adj = 1  # 告知概览检查处于的位置,并对应的调整计数.
        if not self.can_listing() and not is_check_list_end:
            rc = self.check_list_end(req)  # 给出判断机会,如果循环条件不允许了,翻页采集结束
            if rc is None: return None

        self.last_list_url = self.make_list_url(req)  # 再尝试调用1序列的概览地址生成函数
        return self.last_list_url

    def make_http_result(self, body, code=200, err=''):
        """生成http抓取结果"""
        self.spider.http.rst['BODY'] = body
        self.spider.http.rst['status_code'] = code
        self.spider.http.rst['error'] = err

    def http_take(self, url, body=None, head=None):
        """使用内置的http组件发起一次请求.没有body时为get,否则为post
            返回值:(code,body)
                code >0 :http status code,body为回应数据
                code <=0:error code,body为错误说明
        """
        req = {}
        if head:
            req['HEAD'] = head
        if body:
            req['BODY'] = body
            req['METHOD'] = 'post'
        else:
            req['METHOD'] = 'get'
        rc = self.spider.http.take(url, req)

        if not rc:
            return 0, self.spider.http.get_error()
        else:
            return self.spider.http.get_status_code(), self.spider.http.get_BODY()

    def chrome_wait(self, chrome, tab, cond_re, body_only=False, timeout=None, frmSel=None):
        """等待页面装载完毕:
            chrome - chrome客户端对象
            tab - chrome页面标识
            cond_re - 页面完成判定(正则表达式)
            body_only - 是否仅返回html/body内容
            timeout - 外部指定的完成等待超时上限
            frmSel - 页面iframe选取器(css选取器)
            返回值:空等待超时;否则为页面内容
        """
        if timeout is None:
            timeout = self.chrome_timeout
        rsp, msg = chrome.wait_re(tab, cond_re, timeout, body_only, frmSel)  # 等待页面装载完成
        if msg != '' or rsp is None:
            self.make_http_result('', 998, msg)
            return ''
        else:
            self.make_http_result(rsp)
            return rsp

    def chrome_wait_xp(self, chrome, tab, cond_xp, body_only=False, timeout=None, frmSel=None):
        """等待页面装载完毕:
            chrome - chrome客户端对象
            tab - chrome页面标识
            cond_xp - 页面完成判定(xpath表达式)
            body_only - 是否仅返回html/body内容
            timeout - 外部指定的完成等待超时上限
            frmSel - 页面iframe选取器(css选取器)
            返回值:空等待超时;否则为页面内容
        """
        if timeout is None:
            timeout = self.chrome_timeout
        rsp, msg = chrome.wait_xp(tab, cond_xp, timeout, body_only, frmSel)  # 等待页面装载完成
        if msg != '' or rsp is None:
            self.make_http_result('', 997, msg)
            return ''
        else:
            self.make_http_result(rsp)
            return rsp

    def chrome_hold(self, url, chrome, tab, timeout=None, url_is_re=False):
        """在指定的tab上提取指定url的回应内容"""
        if timeout is None:
            timeout = self.chrome_timeout

        rbody = ''
        reqs, msg = chrome.wait_request_urls(tab, url, timeout, url_is_re)
        if msg == '':
            rbody, msg = chrome.get_response_body(tab, url, url_is_re)

        if msg != '':
            self.make_http_result('', 994, msg)
            return False

        self.make_http_result(rbody)

        chrome.clear_request(tab)
        return True

    def chrome_exec(self, js, chrome, tab, cond_re, is_run=False, body_only=True, timeout=None, frmSel=None, cond_xp=None):
        """在指定的tab上运行指定的js代码(或代码列表),完成条件是cond_re"""

        def exec(s):
            if is_run:
                r = chrome.run(tab, s)  # 附带dom100.js运行指定的脚本
            else:
                r = chrome.exec(tab, s)  # 不附带dom100.js运行指定的脚本
            if r[1]:
                self.make_http_result('', 993, 'chrome exec js fail.')
                return False
            return True

        if isinstance(js, str):
            if not exec(js):
                return False
        elif isinstance(js, list):
            for s in js:
                if not exec(s):
                    return False
        if cond_xp:
            return self.chrome_wait_xp(chrome, tab, cond_xp, body_only, timeout, frmSel)
        else:
            return self.chrome_wait(chrome, tab, cond_re, body_only, timeout, frmSel)

    def chrome_cookies(self, url, chrome, tab):
        """在指定的tab上获取指定url对应的cookie值列表
                url - 用于匹配cookie作用域和路径
            返回值:None失败,或[cookie信息]列表
        """
        cks, msg = chrome.query_cookies(tab, url)
        if msg:
            return None
        return cks

    def chrome_goto(self, url, chrome, tab, preclean=True):
        """在指定的tab上浏览指定的url页面,不进行完成等待
                preclean - 是否在浏览之前进行页面预清空,避免前后内容干扰等待条件的判断.
            返回值:是否成功
        """
        chrome.stop(tab, preclean)
        r = chrome.goto(tab, url)  # 控制浏览器访问入口url
        if not r[0]:
            self.make_http_result('', 900, 'chrome open fail. %s' % r[2])
            return False
        return True

    def chrome_take(self, url, chrome, tab, cond_re, body_only=False, frmSel=None, preclean=True):
        """便捷函数结合goto/wait功能,在指定的tab上浏览指定的url页面,根据完成条件cond_re进行结果等待.
                body_only - 是否仅返回body节点内部的内容.
                frmSel - iframe选取器,用于抓取该iframe内部的内容.
                preclean - 是否在浏览之前进行页面预清空,避免前后内容干扰等待条件的判断.
            返回值:是否成功
        """
        chrome.stop(tab, preclean)
        r = chrome.goto(tab, url)  # 控制浏览器访问入口url
        if not r[0]:
            self.make_http_result('', 900, 'chrome open fail. %s' % r[2])
            return False
        return self.chrome_wait(chrome, tab, cond_re, body_only, frmSel=frmSel)

    def chrome_post(self, url, chrome, data, tab, cond_re, body_only=False, contentType="application/x-www-form-urlencoded"):
        """在指定的tab上发起ajax/post请求url页面,完成条件是cond_re"""
        r = chrome.post(tab, url, data, contentType)  # 控制浏览器访问入口url
        if r[1]:
            self.make_http_result('', 996, r[1])
            return False
        return self.chrome_wait(chrome, tab, cond_re, body_only)

    def chrome_get(self, url, chrome, tab, cond_re, body_only=False):
        """在指定的tab上发起ajax/get请求url页面,完成条件是cond_re"""
        r = chrome.get(tab, url)  # 控制浏览器访问入口url
        if r[1]:
            self.make_http_result('', 995, r[1])
            return False
        return self.chrome_wait(chrome, tab, cond_re, body_only)

    def chrome_mouseact(self, chrome, tab):
        """获取鼠标动作执行器.返回值:None或MouseAct对象"""
        tab, msg = chrome.tab(tab)
        if msg:
            return None
        return MouseAct(tab)

    def on_list_take(self, list_url, req):
        """发起对list_url的http抓取动作
            self.spider.http.rst['BODY']中保存了抓取结果;
            self.rst['status_code']记录http状态码;
            self.rst['error']记录错误原因.
            返回值:是否抓取成功."""
        return self.spider.http.take(list_url, req)

    def on_info_filter(self, info):
        """对待入库的信息进行过滤,判断是应该入库.返回值:是否可以入库"""
        return True

    def on_page_url(self, info, list_url, req):
        """可以对info内容进行修正,填充细览请求参数req.返回值告知实际抓取细览页的url地址.如果返回__EMPTY__则放弃当前信息."""
        return None

    def on_page_take(self, info, page_url, req):
        """发起对page_url的http抓取动作,快捷方法为: make_http_result
            self.spider.http.rst['BODY'] 中保存了抓取结果;
            self.spider.http.rst['status_code'] 记录http状态码;
            self.spider.http.rst['error'] 记录错误原因.
            返回值:是否抓取成功."""
        return self.spider.http.take(page_url, req)

    def on_page_info(self, info, list_url, page):
        """从page中提取必要的细览页信息放入info中.返回值告知是否处理成功"""
        return True

    def on_save_info(self, info, updid):
        """使用dbs保存info到数据库中,updid告知是否为信息更新模式.返回值:保存的信息数量."""
        if self.dbs.save_info(info, updid):
            return 1
        return 0

    def do_vcode_calc(self, vdata, **param):
        """进行验证码的识别计算
            参数说明:
                data为待识别的验证码数据
                param为预留的扩展参数
                    vcode_mode - 告知验证码类型,默认为'classic'
                    vcode_svr_url -  告知验证码识别服务器地址
            返回值:(识别结果,错误说明)
        """
        mode = param.get('vcode_mode', 'classic')
        rec_svr_url = param.get('vcode_svr_url', 'http://jobs.spider.zb:9722/classic')
        if mode == 'classic':
            rc, vcode = self.http_take(rec_svr_url, vdata)
            if rc != 200 or not vcode:
                # 自动识别出错时进行手动处理
                if rc != 200:
                    self.log_warn('<%s> vcode calc error: %s' % (rec_svr_url, self.spider.http.get_error()))
                vcode = self.input_validcode(vdata)

            if not vcode:
                return None, f'vcode calc error: {rc}'
            return vcode, ''

        return None, f'not impl vcode_mode: {mode}'

    @guard(locker_dg)  # 单进程内多线程并发时,对话框UI需要进行锁保护调用
    def input_validcode(self, vdata):
        """显示给定的图片数据并返回输入的验证码"""
        self.spider.cnt_input_vcode += 1  # 当前采集源爬虫手动输入验证码计数增加
        global _cnt_input_vcode
        _cnt_input_vcode += 1  # 全局验证码输入计数增加
        title = f'{self.spider.cnt_input_vcode}/{_cnt_input_vcode}'
        return _gd.input_validcode(vdata, title)

    def on_attach_update(self, info, att_idx, att_url, att_name, file_path):
        """更新当前附件信息在正文中的内容部分,确保再次浏览正文时可访问本地附件文件.返回空正常
            参数说明:
                info - 细览信息
                att_idx - 当前附件在整体附件列表中的索引
                att_url - 附件地址,来自于抽取规则的结果
                att_name - 附件文件名,来自于抽取规则的结果
                file_path - 附件在本地的路径,可直接用于正文中相关信息的更新
            返回值: 错误信息
        """
        info.content.replace(att_url, file_path)
        return ''

    def on_attach_make_url(self, info, att_idx, att_url, att_name, req, retry, **param):
        """构造抓取附件的请求和url地址
            参数说明:
                info - 细览信息
                att_idx - 当前附件在整体附件列表中的索引
                att_url - 附件地址,来自于抽取规则的结果
                att_name - 附件文件名,来自于抽取规则的结果
                req - http的请求信息
                retry - 当前附件的重试请求次数,0为首次请求.
                param - 附件抓取控制参数
            返回值:(附件目标地址,错误说明)
        """
        dst_url = up.urljoin(info.url, att_url)
        return dst_url, ''

    def on_attach_extract(self, info, **param):
        """按附件抽取规则,在info.content中抽取待抓取的附件.
            返回值:[(att_url,att_name)] 附件地址和名字的元组列表
            参数说明:
                info - 当前的细览信息
                param - 扩展参数字典
                    rule_url - 从正文中抽取附件url或标识的xpath
                    rule_name - 从正文中抽取附件文件名的xpath
                    rule_root - 从正文中抽取附件信息的根表达式xpath,有此参数时,rule_url和rule_name的路径必须对应其子节点
        """
        rst = []
        rule_url = param.get('rule_url')
        rule_name = param.get('rule_name')
        rule_root = param.get('rule_root')
        if rule_root:
            # 进行父子模式的查询
            xrst, err = pair_extract2(info.content, rule_root, [rule_url, rule_name] if rule_name else [rule_url])
        else:
            # 进行伙伴模式的查询
            xrst, err = pair_extract(info.content, [rule_url, rule_name] if rule_name else [rule_url])

        if err:
            self.log_warn(f'on_attach_extract {param} error: {err}')

        if rule_name:
            rst = xrst
        else:
            for x in xrst:
                rst.append((x[0], None))

        return rst

    def on_attach_take(self, att_url, req, **param):
        """抓取指定附件.
            返回值:(size,data)
                size: -1下载错误;-2验证码错误;>=0数据长度
                data: 下载的数据内容
        """
        # 根据给定的参数,抓取指定的附件
        if not self.spider.http.take2(att_url, req):
            return -1, None

        # 从入参中获取"验证码错误"的提示检查字样
        vcode_cc_re = param.get('vcode_cc_re')

        # 尝试检查是否为验证码错误的应答
        attdata = self.spider.http.get_BODY(b'')
        if isinstance(attdata, str) and vcode_cc_re and query_re_str(attdata, vcode_cc_re):
            return -2, None

        return len(attdata), attdata

    def do_attach(self, info, **param):
        """根据当前的细览内容进行附件抓取处理.正常时错误信息列表为空.
            返回值: [{附件信息}],[错误信息]
                param - 扩展参数字典,参见on_attach_extract/do_vcode_calc函数说明
                    rule_url - 从正文中抽取附件url或标识的xpath
                    rule_name - 从正文中抽取附件文件名的xpath
                    rule_root - 从正文中抽取附件信息的根表达式xpath,有此参数时,rule_url和rule_name的路径必须对应其子节点
                    vcode_mode - 验证码模式,默认为'classic'经典验证码
                    vcode_svr_url - 验证码识别服务器地址
                    vcode_cc_re - 判断错误验证码下载内容的re表达式
        """
        errs = []
        rsts = []
        if info.content is None:
            msg = f'ATTACH Content Empty: {info.title} | {info.url}'
            self.log_warn(msg)
            errs.append(msg)
            return rsts, errs

        # 先抽取查询待下载的附件列表
        att_infos = self.on_attach_extract(info, **param)
        for i in range(len(att_infos)):
            # 处理具体的附件,得到附件地址和文件名
            att_url = att_infos[i][0]
            att_name = att_infos[i][1]

            # 进行附件下载前的准备(可进行验证码的处理)
            req = {}
            dst_url, err = self.on_attach_make_url(info, i, att_url, att_name, req, 0, **param)
            if err:
                self.log_warn(err)
                errs.append(err)
                continue
            if not dst_url:
                continue

            # 根据当前附件的url和名字生成文件id,为了避免可能的重复,还可取用on_attach_make_url处理后的req中的参数_fileid_
            id_a = '%x' % hash_string(att_url)
            id_b = '%x' % hash_string(f'{att_name}_{req.get("_fileid_")}')
            fileid = f'src{id_a}_{id_b}'

            # 抓取附件数据
            datalen, attdata = self.on_attach_take(dst_url, req, **param)
            if datalen == -2:
                # 验证码错误的时候,再进行一下重试
                dst_url, err = self.on_attach_make_url(info, i, att_url, att_name, req, 1, **param)
                if err:
                    self.log_warn(err)
                    errs.append(err)
                    continue
                if not dst_url:
                    continue
                datalen, attdata = self.on_attach_take(dst_url, req, **param)

            # 处理抓取错误
            if datalen < 0 or attdata is None:
                err = 'verification code error.' if datalen == -2 else 'download error.'
                msg = f'ATTACH TAKE FAIL <{err}>: {info.title} | {dst_url}'
                self.log_warn(msg)
                errs.append(msg)
                continue

            # 尝试解析得到附件的扩展名
            ename = None
            if att_name:
                names = os.path.splitext(att_name)
                if len(names):
                    ename = names[-1]

            # 扩展名不能直接获取时则尝试根据数据内容进行猜测
            if not ename or len(ename) >= 6:
                ename = guess_mime(attdata, True)

            # 生成落地后的多级路径,构造落地后的附件文件名
            fpath = f'/files/{info.pub_time}/'
            fname = f'{self.id}_{fileid}{ename}'
            file_path = f'{fpath}/{fname}'

            # 附件存盘落地
            if not save_to_file2(f'.{fpath}', fname, attdata, encode=None, mode='wb'):
                msg = f'ATTACH SAVE FAIL: .{file_path} => {info.title} | {info.url}'
                self.log_warn(msg)
                errs.append(msg)
                continue

            # 进行info.content正文更新
            err = self.on_attach_update(info, i, att_url, att_name, file_path)
            if err:
                msg = f'ATTACH UPDATE FAIL: .{file_path} => {info.title} | {info.url} :: {err}'
                self.log_warn(msg)
                errs.append(msg)
                continue

            # 记录抓取结果信息
            rsts.append({'att_url': att_url, 'att_name': att_name, 'file_path': file_path, 'att_size': datalen})

        return rsts, errs


def spd_sleep(sec):
    if sec:
        time.sleep(sec)


class spider_base:
    """爬虫任务基类,提供采集任务运行所需功能的核心接口"""

    def __init__(self, source):
        self.http = spd_base.spd_base()
        self.source = source
        self.source.spider = self  # 给采集源对象绑定当前的爬虫对象实例
        self.http.timeout = self.source.http_timeout
        self.begin_time = 0
        self.cnt_input_vcode = 0  # 记录手动输入验证码次数

    # 对采集源待调用方法进行统一包装,防范意外错误
    def call_src_method(self, method, *args):
        try:
            call = getattr(self.source, method)  # 获取指定的方法
            return call(*args)  # 调用指定的方法
        except Exception as e:
            self.source.log_error('call <%s> error <%s>' % (method, ei(e)))  # 统一记录错误
            return None

    # 统一生成默认请求参数
    def _make_req_param(self, source):
        req = {}
        if source.proxy:
            req['PROXY'] = source.proxy  # 尝试绑定采集源静态代理
        elif source.proxy_addr:
            req['PROXY'] = source.proxy_addr  # 尝试绑定采集源动态代理
        elif _proxy:
            req['PROXY'] = _proxy  # 再尝试绑定全局代理服务器
        return req

    def _do_page_take(self, info, list_url, page_url, req_param):
        """尝试对细览页进行循环重试抓取,返回值:(页面抓取状态,信息提取状态)"""
        take_stat = False
        info_stat = True
        for i in range(self.source.page_take_retry):
            self.source.page_url_trys = i + 1  # 记录当前这是第几次重试抓取细览页
            if len(self.http.rst) and self.source.page_url_sleep:
                self.source.log_info('page sleeping %d second ...' % self.source.page_url_sleep)
                spd_sleep(self.source.page_url_sleep)  # 细览页面需要间隔休眠
            take_stat = self.call_src_method('on_page_take', info, page_url, req_param)

            if not take_stat:
                self.source.log_warn('page_url http take error <%s> :: <%d> %s' % (page_url, self.http.get_status_code(), self.http.get_error()))
                self.source.rec_stat(self.http.get_status_code())
                continue

            # 对细览页进行后续处理
            xstr = self.call_src_method('on_page_format', self.http.get_BODY())
            if xstr == '__EMPTY__':
                break
            info_stat = self.call_src_method('on_page_info', info, list_url, xstr)
            if not info_stat:
                continue
            break
        return (take_stat, info_stat)

    def _do_page(self, item, list_url, dbs):
        """进行细览抓取与提取信息的处理"""
        info = info_t(self.source.id)
        # 将概览页提取的信息元组赋值到标准info对象
        for i in range(len(self.source.on_list_rulenames)):
            info.__dict__[self.source.on_list_rulenames[i]] = item[i]
        # 进行细览url的补全
        info.url = up.urljoin(list_url, info.url)

        # 给采集源绑定数据库功能对象
        self.source.dbs = dbs

        # 先进行一下过滤判断
        if not self.call_src_method('on_info_filter', info):
            return None

        # 给出对info.url的处理机会,并用来判断是否需要抓取细览页
        req_param = self._make_req_param(self.source)
        take_page_url = self.call_src_method('on_page_url', info, list_url, req_param)
        if take_page_url == __EMPTY_PAGE__:
            return None  # 要求放弃当前页面信息

        if info.source_id is None:  # 在on_page_url调用之后,给出信息废弃的机会,是另一种on_info_filter过滤处理
            self.source.log_debug("page_url <%s> is list DISCARD" % info.url)
            return None

        # 进行概览排重检查
        rid = dbs.check_repeat(info, self.source.on_check_repeats)
        if self._is_upd_mode():
            # 要求进行信息更新,则记录当前已有信息主键id,继续处理
            self.updid = rid
        else:
            # 不要求信息更新,如果信息已存在,则结束处理
            if rid is not None:
                self.source.log_debug("page_url <%s> is list REPEATED <%d>" % (info.url, rid))
                return None

        page_info_ok = True
        if take_page_url:
            # 需要抓取细览页并提取信息
            self.reqs += 1
            take_stat, page_info_ok = self._do_page_take(info, list_url, take_page_url, req_param)
            if not take_stat:
                return None
            self.rsps += 1
            self.source.log_debug('page_url http take <%s> :: %d' % (take_page_url, self.http.get_status_code()))
            self.source.rec_stat(self.http.get_status_code())
            if page_info_ok:
                self.succ += 1

        # 进行信息过滤判断
        if not page_info_ok or not self.call_src_method('on_info_filter', info):
            self.source.log_debug("page_url <%s> is page DISCARD" % info.url)
            return None

        # 进行细览排重检查
        rid = dbs.check_repeat(info, self.source.on_pages_repeats)
        if self._is_upd_mode():
            # 要求进行信息更新,则尝试使用细览排重得到的信息主键id
            if self.updid is None or rid is not None:
                self.updid = rid
            return info  # 更新模式,可以存盘
        else:
            if rid is None:
                if take_page_url:
                    self.source.log_info('page_url new <%s>' % (take_page_url))
                return info  # 细览排重通过,可以存盘
            else:
                self.source.log_debug("page_url <%s> is page REPEATED <%d>" % (info.url, rid))

        return None

    def _do_page_loop(self, list_items, list_url, dbs):
        """执行细览抓取处理循环,返回值告知本次成功抓取并保存的信息数量"""
        infos = 0
        self.call_src_method('on_list_begin', self.infos)  # 概览页处理开始

        # 进行细览循环
        tol_items = len(list_items)
        for i in range(tol_items):
            item = list_items[i]
            self.source.list_item_index = (i + 1, tol_items)  # 告知采集源,当前的概览页条目索引信息
            self.updid = None
            info = self._do_page(item, list_url, dbs)
            if info:
                infos += self.call_src_method('on_save_info', info, self.updid)  # 概览页处理完成

        self.infos += infos
        self.call_src_method('on_list_end', self.infos, infos)  # 概览页处理完成

        if self.list_info_bulking is not None:
            self.list_info_bulking += infos  # 处于增量抓取状态时,累计增量抓取的数量

        return infos

    def _do_list_bulking(self):
        # 到达预期的翻页数量后,发现仍有数据,则尝试自动增长翻页数量
        if self.list_info_bulking and self.source.list_inc_cnt > 0 and self.source.list_url_idx == self.source.list_url_cnt:
            self.source.list_url_cnt = min(self.source.list_url_cnt + self.source.list_inc_cnt, self.source.list_max_cnt)
            self.list_info_bulking = 0  # 需要开启新一轮增量抓取的时候,清空本轮增量抓取数量

    def _is_upd_mode(self):
        """判断当前采集源是否需要进行信息的更新处理"""
        if info_upd_mode or self.source.info_upd_mode:
            return True
        return False

    def _do_list_take(self, list_url, req_param):
        """尝试多次进行概览页的抓取与内容提取.返回值:(xstr格式化后的概览页内容,rst提取得到的细览信息列表,msg错误消息).xstr为None的时候要求结束采集源的执行"""
        xstr = ''
        rst = []
        msg = ''
        for r in range(max(self.source.list_take_retry, 1)):
            xstr = ''
            rst = []
            msg = ''

            if len(self.http.rst) and self.source.list_url_sleep:
                self.source.log_info('list sleeping %d second ...' % self.source.list_url_sleep)
                spd_sleep(self.source.list_url_sleep)  # 根据需要进行概览采集休眠

            if not self.call_src_method('on_list_take', list_url, req_param):
                self.source.log_warn('list_url http fail <%s> :: %d - %s' % (list_url, self.http.get_status_code(), self.http.get_error()))
                self.source.rec_stat(self.http.get_status_code())
                continue

            rsp_body = self.http.get_BODY()
            if self.http.get_status_code() == 200:
                self.source.rec_stat(self.http.get_status_code())
                self.source.log_debug('list_url http take <%s> :: %d' % (list_url, self.http.get_status_code()))
                if not rsp_body:
                    self.source.log_warn('list_url http take empty <%s> :: %d' % (list_url, self.http.get_status_code()))
                    self.source.rec_stat(201)
            else:
                self.source.log_warn('list_url http take <%s> :: %d' % (list_url, self.http.get_status_code()))
                self.source.rec_stat(self.http.get_status_code())
                if self.http.get_status_code() >= 400:
                    break

            # 格式化概览页内容为xpath格式
            xstr = self.call_src_method('on_list_format', rsp_body)
            if xstr is None:  # 如果返回值为None则意味着要求停止翻页
                return xstr, rst, msg

            # 提取概览页信息列表
            rst, msg = pair_extract(xstr, self.source.on_list_rules)
            self.source.last_list_items = len(rst)  # 记录最后一次概览提取元素数量
            if xstr == __EMPTY_PAGE__:
                break

            if msg != '' or self.source.last_list_items == 0:
                continue
            else:
                break

        return xstr, rst, msg

    def run(self, dbs):
        """对当前采集任务进行完整流程处理:概览循环与细览循环"""
        self.source.stat.clear()
        self.reqs = 0
        self.rsps = 0
        self.succ = 0
        self.infos = 0
        self.updid = None  # 进行细览页循环与信息保存的时候,记录已存在信息的主键ID,决定是否需要对信息进行更新
        self.list_info_bulking = 0  # None没有进入增量模式.其他为本轮增量翻页的信息抓取数量.初值为0则对首轮进行累计
        self.begin_time = int(time.time())

        # 进行入口请求的处理
        req_param = self._make_req_param(self.source)
        entry_url = self.call_src_method('on_ready', req_param)
        if isinstance(entry_url, bool) and not entry_url:
            return False
        if entry_url is not None:
            self.reqs += 1
            if self.http.take(entry_url, req_param):
                self.source.log_debug('on_ready entry_url take <%s>:: %d' % (entry_url, self.http.get_status_code()))
                self.source.rec_stat(self.http.get_status_code())
                self.rsps += 1
                self.succ += 1
                if not self.call_src_method('on_ready_info', self.http.get_BODY()):
                    self.source.log_warn('on_ready_info entry_url info extract fail. <%s>' % (entry_url))
                    return False
            else:
                self.source.log_warn('entry_url http take error <%s> :: %s' % (entry_url, self.http.get_error()))
                return False

        # 进行概览抓取循环
        list_url = self.call_src_method('on_list_url', req_param)
        list_emptys = 0
        while list_url is not None:
            self.reqs += 1
            self.source._list_content, self.source._list_infos, msg = self._do_list_take(list_url, req_param)

            if self.source._list_content:  # 抓取成功
                self.rsps += 1
                reqbody = req_param['BODY'] if 'METHOD' in req_param and req_param['METHOD'] == 'post' and 'BODY' in req_param else ''
                if msg == '':
                    ci, cn = self.source.on_list_plan()
                    plan = '' if ci is None else 'plan<%d/%d>' % (ci, cn)
                    plan += '[%d/%d/%d]' % (self.source.list_url_idx, self.source.list_url_cnt, self.source.list_max_cnt)  # 阶段与进度

                    if self.source.last_list_items == 0:
                        # 概览页面提取为空,需要判断连续为空的次数是否超过了循环停止条件
                        if self.source._list_content != __EMPTY_PAGE__:
                            self.source.log_warn('list_url pair_extract empty <%s> :: <%d>' % (list_url, self.http.get_status_code()))
                            self.source.rec_stat(994)
                            list_emptys += 1
                            if list_emptys >= self.source.on_list_empty_limit:
                                self.source.log_warn('list_url pair_extract empty <%s> :: %d >= %d limit!' % (list_url, list_emptys, self.source.on_list_empty_limit))
                                break
                        else:
                            list_emptys = 0
                            self.succ += 1
                            self.source.log_info('none <  -> list %s <%s> %s' % (plan, list_url, reqbody))
                    else:
                        list_emptys = 0
                        self.succ += 1
                        infos = self._do_page_loop(self.source._list_infos, list_url, dbs)  # 进行概览循环
                        self.source.log_info('news <%3d> list %s <%s> %s' % (infos, plan, list_url, reqbody))
                else:
                    self.source.rec_stat(993)
                    self.source.log_warn('list_url pair_extract error <%s> :: %s %s\n%s' % (list_url, msg, reqbody, self.http.get_BODY()))

            if self.source._list_content is None:
                dbs.update_act(self, False)  # 进行中间状态更新
                break  # 要求采集源停止运行

            self._do_list_bulking()  # 尝试进行概览翻页递增
            list_url = self.call_src_method('on_list_url', req_param)
            dbs.update_act(self, list_url is not None)  # 进行中间状态更新

        self.call_src_method('on_end')
        return True


class db_base:
    """采集系统数据库功能接口"""

    def __init__(self, fname):
        self.db = s3db(fname)
        self.db.opt_def()
        self.dbq = s3query(self.db)
        self.stime = int(time.time())
        pass

    def opened(self):
        return self.db.opened()

    def close(self):
        if self.db:
            self.dbq.close()
            self.dbq = None
            self.db.close()
            self.db = None

    def register(self, name, site_url, id=None):
        """根据名字进行采集源在数据库中的注册,返回值:-1失败,成功为采集源ID"""
        rows, msg = self.dbq.query("select id,reg_time,site_url from tbl_sources where name=?", (name,))
        # 先查询指定的采集源是否存在
        if msg != '':
            _logger.error('source <%s : %s> register QUERY fail. DB error <%s>', name, site_url, msg)
            return -1

        if len(rows) == 0:
            # 采集源不存在,则插入
            if id is None:
                ret, msg = self.dbq.exec("insert into tbl_sources(name,site_url,reg_time) values(?,?,?)",
                                         (name, site_url, self.stime))
                if not ret:
                    _logger.error('source <%s : %s> register INSERT fail. DB error <%s>', name, site_url, msg)
                    return -1

                rows = [(self.dbq.cur.lastrowid, self.stime, site_url)]  # 记录最后的插入id,作为采集源id
            else:
                ret, msg = self.dbq.exec("insert into tbl_sources(id,name,site_url,reg_time) values(?,?,?,?)",
                                         (id, name, site_url, self.stime))
                if not ret:
                    _logger.error('source <%s : %s> register INSERT fail. DB error <%s>', name, site_url, msg)
                    return -1

                rows = [(id, self.stime, site_url)]  # 记录最后的插入id,作为采集源id
        else:
            if rows[0][1] != self.stime:
                # 采集源已经存在,但需要更新注册时间
                ret, msg = self.dbq.exec("update tbl_sources set reg_time=? where name=?", (self.stime, name))
                if not ret:
                    _logger.error('source <%s : %s> register UPDATE fail. DB error <%s>', name, site_url, msg)
                    return -1
            else:
                # 同名采集源重复注册了
                _logger.error('source <%s : %s> register REPEATED!. EXIST URL<%s>', name, site_url, rows[0][2])
                return -1

        _logger.info('source register OK! <%3d : %s : %s>', rows[0][0], name, site_url)
        return rows[0][0]

    @guard(locker)
    def update_act(self, spd: spider_base, during=False):
        """更新采集源的动作信息"""
        end_time = int(time.time())
        dat = (spd.begin_time, end_time, spd.reqs, spd.rsps, spd.succ, spd.infos, spd.source.id)
        ret, msg = self.dbq.exec(
            "update tbl_sources set last_begin_time=?,last_end_time=?,last_req_count=?,last_rsp_count=?,last_req_succ=?,last_infos_count=? where id=?",
            dat)
        if not ret:
            _logger.error("update source act <%s> fail. DB error <%s>", str(dat), msg)
            return False

        return True

    @guard(locker)
    def clear_old(self, days=15, srcid=None):
        """清理旧数据,仅保留days天的数据.srcid可指定采集源编号,或全部.
            返回值:<0错误;>=0为删除的记录数
        """
        if srcid is None:
            sql = f"delete from tbl_infos where create_time<strftime('%s',datetime('now','localtime','-{days} day'))"
        else:
            sql = f"delete from tbl_infos where source_id={srcid} and create_time<strftime('%s',datetime('now','localtime','-{days} day'))"

        ret, msg = self.dbq.exec(sql)
        if not ret:
            _logger.error("clear source old <%s> fail. DB error <%s>", str(srcid), msg)
            return -1

        return msg

    @guard(locker)
    def save_info(self, info: info_t, updid=None):
        """保存指定的信息入库,外面应进行排重判断;可指定updid进行信息的强制更新;返回值告知是否成功"""

        def d2j(d):
            if d is None:
                return None
            try:
                return json.dumps(d, indent=4, ensure_ascii=False)
            except Exception as e:
                _logger.error('info ext dict2json error <%s>', es(e))
                return None

        dat = (info.source_id, int(time.time()), info.title, info.url, info.content, info.pub_time, info.addr, info.keyword, d2j(info.ext),
               info.memo)
        if updid is None:
            # 常规插入模式
            sql = "insert into tbl_infos(source_id,create_time,title,url,content,pub_time,addr,keyword,ext,memo) values(?,?,?,?,?,?,?,?,?,?)"
        else:
            # 数据更新模式
            dat += (updid,)
            sql = "update tbl_infos set source_id=?,create_time=?,title=?,url=?,content=?,pub_time=?,addr=?,keyword=?,ext=?,memo=? where id=?"

        ret, msg = self.dbq.exec(sql, dat)
        if not ret:
            _logger.error("info <%s> save fail. DB error <%s>", str(dat), msg)
            return False

        return True

    def _cat_cond(self, info: info_t, cond):
        """ 拼装排重条件与值元组
            cond为['字段1','字段2']时,代表多个字段为and逻辑
            cond为[('字段1','字段2'),('字段3','字段4')]时,代表多个字段组为or逻辑,组内字段为and逻辑
        """
        vals = ()
        cons = ()

        # 统计分组的数量
        grps = 0
        for i in range(len(cond)):
            if isinstance(cond[i], tuple):
                grps += 1

        if grps:
            # 有分组,需要先对分组中的tuple进行检查修正
            for i in range(len(cond)):
                if not isinstance(cond[i], tuple):
                    cond[i] = (cond[i],)

            for fields in cond:
                # 对每个组进行处理,拼装and部分的逻辑串
                vals += tuple(info.__dict__[c] for c in fields)
                cons += ('(' + ' and '.join(tuple(c + '=?' for c in fields)) + ')',)
        else:
            # 无分组,直接拼装and部分的逻辑
            vals = tuple(info.__dict__[c] for c in cond)
            cons += (' and '.join(tuple(c + '=?' for c in cond)),)

        # 多个and条件,进行or连接
        cons = ' or '.join(tuple(c for c in cons))
        return vals, cons

    @guard(locker)
    def check_repeat(self, info: info_t, cond):
        """使用指定的信息对象,根据给定的cond条件(字段名列表),判断其是否重复.
            返回值:None不重复;其他为已有信息的ID
        """
        if len(cond) == 0:
            return None  # 没有给出判重条件,则认为不重复

        val, cnd = self._cat_cond(info, cond)
        rows, msg = self.dbq.query("select id from tbl_infos where %s limit 1" % cnd, val)

        if msg != '':
            _logger.error('info <%s> repeat QUERY fail. DB error <%s>', info.__dict__.__str__(), msg)
            return None

        if len(rows) == 0:
            return None

        return rows[0][0]


class collect_manager:
    """采集系统管理器"""

    def __init__(self, dbs, threads=0):
        self.dbs = dbs
        self.spiders = []
        self.sources = []
        self.on_idle = self._on_idle
        self.threads = max(1, threads)
        if self.threads > 1:
            locker.init()
            locker_dg.init()

        _logger.info('tiny spider collect manager is starting ...')

    def _on_idle(self):
        """默认的空闲函数,返回值为True,则停止抓取流程"""
        return False

    def register(self, source_t, spider_t=spider_base):
        """注册采集源与对应的爬虫类,准备后续的遍历调用"""
        mname = None
        if type(source_t).__name__ == 'module':  # 传递模块对象,引用默认类
            mname = source_t.__name__
            source_t = source_t.source_t
        elif type(source_t).__name__ == 'str':  # 传递模块名字,动态装载
            m = importlib.import_module(source_t)
            mname = m.__name__
            source_t = m.source_t

        src = source_t()  # 默认传递采集源的类或被动态装载后得到了采集源的类,创建实例
        # 检查字段有效性
        if len(src.on_list_rulenames) == 0:
            _logger.warn('<%s> not setup info field.' % src.name)
            return False

        for field in src.on_list_rulenames:
            if field[0] != '_' and field not in {'url', 'title', 'content', 'pub_time', 'addr', 'keyword', 'memo'}:
                _logger.warn('<%s> using illegal info field <%s>.' % (src.name, field))
                return False

        sid = self.dbs.register(src.name, src.url, src.id)
        if sid == -1:
            return False

        meter = tick_meter(src.interval)  # 采集源运行间隔计时器
        spdmeta = (spider_t, source_t, sid, mname, meter)
        self.sources.append(spdmeta)  # 记录采集源爬虫元数据
        self._make_spider(spdmeta, src)  # 根据采集源爬虫元数据生成首次运行需要的爬虫实例
        return True

    def _make_spider(self, spdmeta, src=None):
        """根据采集源类型等参数生成爬虫实例"""
        meter = spdmeta[4]
        if not meter.hit():
            return False  # 对于本轮不运行的采集源,跳过

        if src is None:
            src = spdmeta[1]()
        src.id = spdmeta[2]
        src.module_name = spdmeta[3]
        spd = spdmeta[0](src)  # 重新构造当前采集源对应的爬虫实例

        if src.order_level:
            self.spiders.insert(0, spd)
        else:
            self.spiders.append(spd)
        return True

    @guard(locker)
    def _inc_infos_(self, inc):
        """记录每轮抓取的信息数量.可能被多线程并发,所以需要锁定."""
        self.infos += inc

    def _run_one(self, spd):
        """真正执行爬虫实例的过程"""
        if spd is None:
            return  # 本轮无需运行的爬虫实例

        _logger.info("source <%s{%3d}> begin[%d+%d:%d]. <%s>", spd.source.name, spd.source.id, spd.source.list_url_cnt,
                     spd.source.list_inc_cnt,
                     spd.source.list_max_cnt, spd.source.url)
        spd.run(self.dbs)
        self._inc_infos_(spd.infos)
        self.dbs.update_act(spd)
        _logger.info("source <%s> end. reqs<%d> rsps<%d> succ<%d> infos<%d> vcodes<%d>", spd.source.name, spd.reqs, spd.rsps, spd.succ, spd.infos, spd.cnt_input_vcode)

    def run(self):
        """对全部爬虫逐一进行调用.返回值:是否要求停止"""

        if len(self.spiders) == 0:  # 进行预处理,适应多次运行时的爬虫实例初始化
            for spdmeta in self.sources:
                self._make_spider(spdmeta)

        total_spiders = len(self.spiders)
        if total_spiders == 0:
            return None  # 预处理后确实没有需要运行的采集源,直接结束
        else:
            _logger.info("spiders will run <%d> ..." % total_spiders)

        self.infos = 0
        stop = False

        if self.threads > 1:  # 使用多线程并发运行全部的爬虫
            task_ids = [i - 1 for i in range(len(self.spiders), 0, -1)]  # 待处理任务索引列表,倒序,便于后面pop使用
            workers = []  # 工作线程对象列表
            while len(task_ids) or len(workers):
                ends, stop = wait_threads(workers, 0.1, idle_cb=self.on_idle)  # 在批量线程中等待任意线程结束
                if stop:
                    for t in workers:
                        stop_thread(t)
                    break
                tc = self.threads - len(workers)
                for i in range(tc):  # 循环补充新的工作线程
                    if len(task_ids) == 0:
                        break  # 没有待处理任务了,结束
                    spd = self.spiders[task_ids.pop()]  # 得到待处理任务
                    workers.append(start_thread(self._run_one, spd))  # 创建线程,执行任务,并记录线程对象
        else:
            idx = 1
            for spd in self.spiders:  # 在主线程中顺序执行全部的爬虫
                if self.on_idle and self.on_idle():
                    stop = True
                    break
                if total_spiders > 1:
                    _logger.info("progress <%d/%d>", idx, total_spiders)
                self._run_one(spd)
                idx += 1

        for spd in self.spiders:
            if spd is None or len(spd.source.stat) == 0:
                continue
            if len(spd.source.stat) == 1 and 200 in spd.source.stat:
                continue
            _logger.warning("<%s> | source <%s {%d}> | stat <%s> | %s", spd.source.module_name, spd.source.name, spd.source.id, spd.source.stat, spd.source.url)
        _logger.info("spiders collect <%d>, vcodes<%d>" % (self.infos, _cnt_input_vcode))

        # 爬虫实例用过一次就作废,全部清空等待重新创建.
        self.spiders.clear()
        return stop

    def close(self):
        self.spiders.clear()
        self.sources.clear()
        self.sources = None
        self.spiders = None
        self.dbs = None
        _logger.info('end.')


def make_collect_mgr(log_path='./log_spd_tiny.txt', db_path='spd_tiny.sqlite3', threads=0, log_con_lvl=logging.INFO,
                     log_file_lvl=logging.INFO):
    """创建采集系统管理器对象,告知日志路径和数据库路径.
        返回值:None失败.其他为采集系统管理器对象
    """
    global _logger
    if isinstance(log_path, str):
        _logger = make_logger(log_path, log_file_lvl)
        bind_logger_console(_logger, log_con_lvl)
    else:
        _logger = make_logger2(log_path, log_file_lvl)

    dbs = db_base(db_path)  # 打开数据库
    if not dbs.opened():
        _logger.error('DB open fail. <%s>', db_path)
        return None

    if not dbs.dbq.has('tbl_sources'):
        for s in sql_tbl:
            ret, msg = dbs.db.exec(s)  # 尝试在新库中自动建表
            if not ret:
                _logger.error("DB init create fail! < %s >" % msg)

    cm = collect_manager(dbs, threads)
    return cm


def run_collect_sys(srcs=None, params=None):
    # 定义并处理命令行参数
    def get_params():
        parser = argparse.ArgumentParser()
        parser.add_argument("--workdir", type=str, default='', help="spider work dir.")
        parser.add_argument("--tagname", type=str, default='', help="spider tag name.")
        parser.add_argument("--dbname", type=str, default='', help="sqlite3 db file name.")
        parser.add_argument("--logname", type=str, default='', help="spider log file name.")
        parser.add_argument("--prefix", type=str, default='src_', help="source file name prefix.")
        parser.add_argument("--root", type=str, default='src', help="source file root path")
        parser.add_argument("--thread", type=int, default=0, help="enable thread mode.")
        parser.add_argument("--debug", type=int, default=0, help="enable debug info output.")
        parser.add_argument("--loop_count", type=int, default=1, help="enable long loop mode,loops count.")
        parser.add_argument("--loop_sleep", type=int, default=30, help="long loop mode,sleep second.")

        args = parser.parse_args()
        if params:
            for key in args.__dict__.keys():
                if key in params:  # 尝试使用函数入参进行命令行参数的修正
                    dv = parser.get_default(key)
                    if dv == args.__dict__[key]:  # 命令行参数是默认值的时候,进行入参的校正
                        args.__dict__[key] = params[key]

        return args

    args = get_params()

    # 获取当前文件所在路径,添加到python搜索路径中
    curdir = args.workdir if args.workdir != '' else os.path.dirname(os.path.abspath(sys.argv[0]))
    rootpath = args.root
    sys.path.append(curdir)
    sys.path.append(curdir + '/spd')
    sys.path.append(curdir + f'/{rootpath}')

    # 获取运行文件名称作为标记
    tag = args.tagname if args.tagname != '' else re.split('[\\\\/]', sys.argv[0])[-1].split('.')[0]
    dbname = args.dbname if args.dbname != '' else './%s.sqlite3' % tag
    logname = args.logname if args.logname != '' else './%s.log' % tag

    # 获取采集系统对象并打开数据库与日志
    cm = make_collect_mgr(logname, dbname, args.thread,
                          logging.DEBUG if args.debug else logging.INFO)
    if cm is None:
        print('SDP INIT FAIL!')
        exit(-1)

    if params and 'idle_cb' in params:
        idle_cb = params.get('idle_cb')
        if idle_cb:
            cm.on_idle = idle_cb

    # 注册采集源
    if srcs:
        if isinstance(srcs, str):
            cm.register('%s.%s' % (rootpath, srcs))
        if isinstance(srcs, list):
            for s in srcs:
                if isinstance(s, str):
                    cm.register('%s.%s' % (rootpath, s))
                else:
                    cm.register(s)
    else:
        # 装载采集源列表
        srcs = os.listdir(curdir + f'/{rootpath}')
        for s in srcs:
            if not s.startswith(args.prefix):
                continue
            if not s.endswith('.py'):
                continue
            cm.register('%s.%s' % (rootpath, s[:-3]))

    loop_sleep = max(5, args.loop_sleep)
    # 运行全部采集爬虫
    if args.loop_count == -1:
        while True:
            cm.run()
            _logger.info('sleeping ...')
            time.sleep(loop_sleep)
    else:
        for i in range(max(1, args.loop_count)):
            if i != 0:
                _logger.info('sleeping ...')
                time.sleep(loop_sleep)
            cm.run()

    cm.dbs.close()
    cm.close()
