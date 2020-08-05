import argparse
import importlib
import sys

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

logger = None  # 全局日志输出对象
proxy = None  # 全局代理地址信息
lists_rate = 1  # 全局概览翻页倍率
info_upd_mode = False  # 是否开启采集源全局更新模式(根据排重条件查询得到主键id,之后更新此信息)


# 绑定全局默认代理地址
def bing_global_proxy(str):
    global proxy
    proxy = str


# 设置全局概览翻页倍率
def set_lists_rate(r):
    global lists_rate
    lists_rate = r


# 设置是否开启采集源全局更新模式
def set_info_updmode(v):
    global info_upd_mode
    info_upd_mode = v


# 统一生成默认请求参数
def _make_req_param():
    req = {}
    if proxy:
        req['PROXY'] = proxy
    return req


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


class source_base:
    """概细览采集源基类,提供概细览采集所需功能的核心接口与数据结构定义"""

    def __init__(self):
        """记录采集源动作信息"""
        self.interval = 1000 * 60 * 30  # 采集源任务运行间隔
        self.id = -1  # 采集源注册后得到的唯一标识
        self.name = None  # 采集源的唯一名称,注册后不要改动,否则需要同时改库
        self.url = None  # 采集源对应的站点url
        self.info_upd_mode = False  # 是否开启该信息源的更新模式
        self.http_timeout = 20  # http请求超时时间,秒
        self.list_url_idx = 0  # 当前概览页号
        self.list_url_cnt = 1  # 初始默认的概览翻页数量
        self.list_inc_cnt = 2  # 达到默认翻页数量上限的时候,如果仍有信息被采回,则进行自动增量翻页的数量
        self.list_max_cnt = 99999  # 概览翻页最大数量
        self.list_is_json = False  # 告知概览页面是否为json串,进而决定默认格式化方式
        self.page_is_json = False  # 告知细览页面是否为json串,进而决定默认格式化方式
        self.list_url_sleep = 0  # 概览翻页的延迟休眠时间
        self.page_url_sleep = 0  # 细览翻页的延迟休眠时间
        self.last_list_items = -1  # 记录最后一次概览提取元素数量
        self.list_take_retry = 1  # 概览页面抓取并提取信息的动作重试次数
        self.page_take_retry = 1  # 细览页面抓取动作重试次数
        self.on_list_empty_limit = 3  # 概览内容提取为空的次数上限,连续超过此数量时概览循环终止
        self.on_list_rulenames = []  # 概览页面的信息提取规则名称列表,需与info_t的字段名字相符且与on_list_rules的顺序一致
        self.on_list_rules = []  # 概览页面的信息xpath提取规则列表
        self.on_check_repeats = []  # 概览排重检查所需的info字段列表
        self.on_pages_repeats = []  # 细览排重检查所需的info字段列表
        pass

    def warn(self, msg):
        logger.warn('source <%s : %s> %s' % (self.name, self.url, msg))

    def can_listing(self):
        """判断是否可以翻页"""
        max_cnt = min(self.list_max_cnt, lists_rate * self.list_url_cnt)
        return self.list_url_idx <= max_cnt

    def on_ready(self, req):
        """准备进行采集动作了,可以返回入口url获取最初得到cookie等内容,也可进行必要的初始化或设置req请求参数"""
        self.list_url_idx = 0
        return None

    def on_ready_info(self, rsp):
        """如果on_ready给出了入口地址,则这里会进行入口信息的处理.比如获取初始访问key;返回值告知是否继续抓取."""
        return True

    def on_list_format(self, rsp):
        """返回列表页面的格式化内容,默认对html进行新xhtml格式化;返回值:None告知停止循环;其他为xml格式内容"""
        if self.list_is_json:
            return json2xml(rsp)[0]
        else:
            return format_xhtml(rsp)

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
        return None

    def on_list_url(self, req):
        """告知待抓取的概览URL地址,填充req请求参数.返回None停止采集"""
        if not self.can_listing():
            rc = self.check_list_end(req)  # 给出判断机会,如果循环条件不允许了,翻页采集结束
            if rc is None: return None

        url = self.make_list_urlz(req)  # 先尝试生成0序列的概览列表地址
        self.list_url_idx += 1  # 概览页索引增加
        if url is not None:
            return url

        if not self.can_listing():
            rc = self.check_list_end(req)  # 给出判断机会,如果循环条件不允许了,翻页采集结束
            if rc is None: return None

        url = self.make_list_url(req)  # 再尝试调用1序列的概览地址生成函数
        return url

    def on_list_take(self, list_url, req):
        """发起对list_url的http抓取动作,在self.spider.http.rst['BODY']中保存了抓取结果;.rst['status_code']记录http状态码;.rst['error']记录错误原因.返回值:是否抓取成功."""
        return self.spider.http.take(list_url, req)

    def on_info_filter(self, info):
        """对待入库的信息进行过滤,判断是应该入库.返回值:是否可以入库"""
        return True

    def on_page_url(self, info, list_url, req):
        """可以对info内容进行修正,填充细览请求参数req.返回值告知实际抓取细览页的url地址."""
        return None

    def on_page_take(self, info, page_url, req):
        """发起对page_url的http抓取动作,self.spider.http.rst['BODY'] 中保存了抓取结果;
                                      self.spider.http.rst['status_code'] 记录http状态码;
                                      self.spider.http.rst['error'] 记录错误原因.
        返回值:是否抓取成功."""
        return self.spider.http.take(page_url, req)

    def on_page_info(self, info, list_url, page):
        """从page中提取必要的细览页信息放入info中.返回值告知是否处理成功"""
        return True


class tick_meter:
    '毫秒间隔计时器'

    def __init__(self, interval_ms, first_hit=True):
        self.last_time = 0 if first_hit else int(time.time() * 1000)
        self.interval = interval_ms

    def hit(self):
        '判断当前时间是否超过了最后触发时间一定的间隔'
        cur_time = int(time.time() * 1000)
        if cur_time - self.last_time > self.interval:
            self.last_time = cur_time
            return True
        return False


def spd_sleep(sec):
    logger.debug('time.sleep(%d)' % (sec))
    time.sleep(sec)


class spider_base:
    """爬虫任务基类,提供采集任务运行所需功能的核心接口"""

    def __init__(self, source):
        self.http = spd_base.spd_base()
        self.source = source
        self.source.spider = self  # 给采集源对象绑定当前的爬虫对象实例
        self.http.timeout = self.source.http_timeout
        self.begin_time = 0
        self.meter = tick_meter(source.interval)

    # 对采集源待调用方法进行统一包装,防范意外错误
    def call_src_method(self, method, *args):
        try:
            call = getattr(self.source, method)  # 获取指定的方法
            return call(*args)  # 调用指定的方法
        except Exception as e:
            logger.error('<%s> running call <%s> error <%s>', self.source.name, method, str(e))  # 统一记录错误
            return None

    def _do_page_take(self, info, list_url, page_url, req_param):
        """尝试对细览页进行循环重试抓取"""
        take_stat = False
        info_stat = True
        for i in range(self.source.page_take_retry):
            take_stat = self.call_src_method('on_page_take', info, page_url, req_param)
            if self.source.page_url_sleep:
                spd_sleep(self.source.page_url_sleep)  # 细览页面需要间隔休眠

            if not take_stat:
                logger.warning('page_url http take error <%s> :: <%d> %s' % (page_url, self.http.get_status_code(), self.http.get_error()))
                continue

            # 对细览页进行后续处理
            xstr = self.call_src_method('on_page_format', self.http.get_BODY())
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

        # 先进行一下过滤判断
        if not self.call_src_method('on_info_filter', info):
            return None

        # 给出对info.url的处理机会,并用来判断是否需要抓取细览页
        req_param = _make_req_param()
        take_page_url = self.call_src_method('on_page_url', info, list_url, req_param)

        if info.source_id is None:  # 在on_page_url调用之后,给出信息废弃的机会,是另一种on_info_filter过滤处理
            logger.debug("page_url <%s> is list DISCARD", info.url)
            return None

        # 进行概览排重检查
        rid = dbs.check_repeat(info, self.source.on_check_repeats)
        if self._is_upd_mode():
            # 要求进行信息更新,则记录当前已有信息主键id,继续处理
            self.updid = rid
        else:
            # 不要求信息更新,如果信息已存在,则结束处理
            if rid is not None:
                logger.debug("page_url <%s> is list REPEATED <%d>", info.url, rid)
                return None

        page_info_ok = True
        if take_page_url:
            # 需要抓取细览页并提取信息
            self.reqs += 1
            take_stat, page_info_ok = self._do_page_take(info, list_url, take_page_url, req_param)
            if not take_stat:
                return None
            self.rsps += 1
            logger.debug('page_url http take <%s> :: %d' % (take_page_url, self.http.get_status_code()))
            if page_info_ok:
                self.succ += 1

        # 进行信息过滤判断
        if not page_info_ok or not self.call_src_method('on_info_filter', info):
            logger.debug("page_url <%s> is page DISCARD", info.url)
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
                return info  # 细览排重通过,可以存盘
            else:
                logger.debug("page_url <%s> is page REPEATED <%d>", info.url, rid)

        return None

    def _do_page_loop(self, list_items, list_url, dbs):
        """执行细览抓取处理循环,返回值告知本次成功抓取并保存的信息数量"""
        infos = 0
        self.call_src_method('on_list_begin', self.infos)  # 概览页处理开始

        # 进行细览循环
        tol_items = len(list_items)
        for i in range(tol_items):
            item = list_items[i]
            self.updid = None
            self.source.list_item_index = (i + 1, tol_items)  # 告知采集源,当前的概览页条目索引信息
            info = self._do_page(item, list_url, dbs)
            if info:
                dbs.save_info(info, self.updid)
                infos += 1
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

            if not self.call_src_method('on_list_take', list_url, req_param):
                if self.source.list_url_sleep > 0:  # 根据需要进行概览采集休眠
                    spd_sleep(self.source.list_url_sleep)
                continue

            rsp_body = self.http.get_BODY()
            if self.http.get_status_code() == 200:
                logger.debug('list_url http take <%s> :: %d' % (list_url, self.http.get_status_code()))
                if not rsp_body:
                    logger.warn('list_url http take empty <%s> :: %d' % (list_url, self.http.get_status_code()))
            else:
                logger.warn('list_url http take <%s> :: %d' % (list_url, self.http.get_status_code()))
                if self.http.get_status_code() >= 400:
                    break

            # 格式化概览页内容为xpath格式
            xstr = self.call_src_method('on_list_format', rsp_body)
            if xstr is None:  # 如果返回值为None则意味着要求停止翻页
                return xstr, rst, msg

            if self.source.list_url_sleep > 0:  # 根据需要进行概览采集休眠
                spd_sleep(self.source.list_url_sleep)

            # 提取概览页信息列表
            rst, msg = pair_extract(xstr, self.source.on_list_rules)
            self.source.last_list_items = len(rst)  # 记录最后一次概览提取元素数量
            if xstr == '__EMPTY__':
                break

            if msg != '' or self.source.last_list_items == 0:
                continue
            else:
                break

        return xstr, rst, msg

    def run(self, dbs):
        """对当前采集任务进行完整流程处理:概览循环与细览循环"""
        if not self.meter.hit():
            return False

        self.reqs = 0
        self.rsps = 0
        self.succ = 0
        self.infos = 0
        self.updid = None  # 进行细览页循环与信息保存的时候,记录已存在信息的主键ID,决定是否需要对信息进行更新
        self.list_info_bulking = 0  # None没有进入增量模式.其他为本轮增量翻页的信息抓取数量.初值为0则对首轮进行累计
        self.begin_time = int(time.time())

        # 进行入口请求的处理
        req_param = _make_req_param()
        entry_url = self.call_src_method('on_ready', req_param)
        if entry_url is not None:
            self.reqs += 1
            if self.http.take(entry_url, req_param):
                logger.debug('entry_url take <%s>:: %d' % (entry_url, self.http.get_status_code()))
                self.rsps += 1
                self.succ += 1
                if not self.call_src_method('on_ready_info', self.http.get_BODY()):
                    logger.warning('entry_url http info extract fail. <%s>' % (entry_url))
                    return False
            else:
                logger.warning('entry_url http take error <%s> :: %s' % (entry_url, self.http.get_error()))
                return False

        # 进行概览抓取循环
        list_url = self.call_src_method('on_list_url', req_param)
        list_emptys = 0
        while list_url is not None:
            self.reqs += 1
            xstr, rst, msg = self._do_list_take(list_url, req_param)
            if xstr:  # 抓取成功
                self.rsps += 1
                # 格式化概览页内容为xpath格式
                if msg == '':
                    if self.source.last_list_items == 0:
                        # 概览页面提取为空,需要判断连续为空的次数是否超过了循环停止条件
                        if xstr != '__EMPTY__':
                            logger.warning('list_url pair_extract empty <%s> :: <%d>\n%s' % (list_url, self.http.get_status_code(), xstr))
                            list_emptys += 1
                            if list_emptys >= self.source.on_list_empty_limit:
                                logger.warning('list_url pair_extract empty <%s> :: %d >= %d limit!' % (list_url, list_emptys, self.source.on_list_empty_limit))
                                break
                        else:
                            list_emptys = 0
                            self.succ += 1
                            logger.info('source <%s> none <  0> list <%s>' % (self.source.name, list_url))
                    else:
                        reqbody = req_param['BODY'] if 'METHOD' in req_param and req_param['METHOD'] == 'post' and 'BODY' in req_param else ''
                        list_emptys = 0
                        self.succ += 1
                        infos = self._do_page_loop(rst, list_url, dbs)  # 进行概览循环
                        logger.info('source <%s> news <%3d> list <%s>%s' % (self.source.name, infos, list_url, reqbody))
                else:
                    logger.warning('list_url pair_extract error <%s> :: %s \n%s' % (list_url, msg, self.http.get_BODY()))

            if xstr is None:
                dbs.update_act(self, False)  # 进行中间状态更新
                break  # 要求采集源停止运行

            self._do_list_bulking()  # 尝试进行概览翻页递增
            list_url = self.call_src_method('on_list_url', req_param)
            dbs.update_act(self, list_url is not None)  # 进行中间状态更新

        return True


locker = lock_t()


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

    def register(self, name, site_url):
        """根据名字进行采集源在数据库中的注册,返回值:-1失败,成功为采集源ID"""
        rows, msg = self.dbq.query("select id,reg_time,site_url from tbl_sources where name=?", (name,))
        # 先查询指定的采集源是否存在
        if msg != '':
            logger.error('source <%s : %s> register QUERY fail. DB error <%s>', name, site_url, msg)
            return -1

        if len(rows) == 0:
            # 采集源不存在,则插入
            ret, msg = self.dbq.exec("insert into tbl_sources(name,site_url,reg_time) values(?,?,?)",
                                     (name, site_url, self.stime))
            if not ret:
                logger.error('source <%s : %s> register INSERT fail. DB error <%s>', name, site_url, msg)
                return -1

            rows = [(self.dbq.cur.lastrowid, self.stime, site_url)]  # 记录最后的插入id,作为采集源id
        else:
            if rows[0][1] != self.stime:
                # 采集源已经存在,但需要更新注册时间
                ret, msg = self.dbq.exec("update tbl_sources set reg_time=? where name=?", (self.stime, name))
                if not ret:
                    logger.error('source <%s : %s> register UPDATE fail. DB error <%s>', name, site_url, msg)
                    return -1
            else:
                # 同名采集源重复注册了
                logger.error('source <%s : %s> register REPEATED!. EXIST URL<%s>', name, site_url, rows[0][2])
                return -1

        logger.info('source register OK! <%3d : %s : %s>', rows[0][0], name, site_url)
        return rows[0][0]

    @guard(locker)
    def update_act(self, spd: spider_base, during=False):
        """更新采集源的动作信息"""
        end_time = int(time.time())
        dat = (spd.begin_time, end_time, spd.reqs, spd.rsps, spd.succ, spd.infos, spd.source.id)
        ret, msg = self.dbq.exec(
            "update tbl_sources set last_begin_time=?,last_end_time=?,last_req_count=?,last_rsp_count=?,last_req_succ=?,last_infos_count=? where id=?", dat)
        if not ret:
            logger.error("update source act <%s> fail. DB error <%s>", str(dat), msg)
            return False

        return True

    @guard(locker)
    def save_info(self, info: info_t, updid=None):
        """保存指定的信息入库,外面应进行排重判断;可指定updid进行信息的强制更新;返回值告知是否成功"""

        def d2j(d):
            if d is None:
                return None
            try:
                return json.dumps(d, indent=4, ensure_ascii=False)
            except Exception as e:
                logger.error('info ext dict2json error <%s>', str(e))
                return None

        dat = (info.source_id, int(time.time()), info.title, info.url, info.content, info.pub_time, info.addr, info.keyword, d2j(info.ext), info.memo)
        if updid is None:
            # 常规插入模式
            sql = "insert into tbl_infos(source_id,create_time,title,url,content,pub_time,addr,keyword,ext,memo) values(?,?,?,?,?,?,?,?,?,?)"
        else:
            # 数据更新模式
            dat += (updid,)
            sql = "update tbl_infos set source_id=?,create_time=?,title=?,url=?,content=?,pub_time=?,addr=?,keyword=?,ext=?,memo=? where id=?"

        ret, msg = self.dbq.exec(sql, dat)
        if not ret:
            logger.error("info <%s> save fail. DB error <%s>", str(dat), msg)
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
            logger.error('info <%s> repeat QUERY fail. DB error <%s>', info.__dict__.__str__(), msg)
            return None

        if len(rows) == 0:
            return None

        return rows[0][0]


class collect_manager:
    """采集系统管理器"""

    def __init__(self, dbs):
        self.dbs = dbs
        self.spiders = []
        logger.info('tiny spider collect manager is starting ...')
        pass

    def register(self, source_t, spider_t=spider_base):
        """注册采集源与对应的爬虫类,准备后续的遍历调用"""
        if type(source_t).__name__ == 'module':  # 传递模块对象,引用默认类
            source_t = source_t.source_t
        elif type(source_t).__name__ == 'str':  # 传递模块名字,动态装载
            source_t = importlib.import_module(source_t).source_t

        src = source_t()  # 默认传递采集源的类或被动态装载后得到了采集源的类,创建实例

        # 检查字段有效性
        if len(src.on_list_rulenames) == 0:
            logger.warn('<%s> not setup info field.' % src.name)
            return False

        for field in src.on_list_rulenames:
            if field[0] != '_' and field not in {'url', 'title', 'content', 'pub_time', 'addr', 'keyword', 'memo'}:
                logger.warn('<%s> using illegal info field <%s>.' % (src.name, field))
                return False

        src.id = self.dbs.register(src.name, src.url)
        if src.id == -1:
            return False

        spd = spider_t(src)
        self.spiders.append(spd)
        return True

    @guard(locker)
    def _inc_infos_(self, inc):
        self.infos += inc

    def _run_one(self, spd):
        logger.info("source <%s{%3d}> begin[%d+%d:%d]. <%s>", spd.source.name, spd.source.id, spd.source.list_url_cnt, spd.source.list_inc_cnt,
                    spd.source.list_max_cnt, spd.source.url)
        spd.run(self.dbs)
        self._inc_infos_(spd.infos)
        self.dbs.update_act(spd)
        logger.info("source <%s> end. reqs<%d> rsps<%d> succ<%d> infos<%d>", spd.source.name, spd.reqs, spd.rsps, spd.succ, spd.infos)

    def run(self):
        """对全部爬虫逐一进行调用"""
        self.infos = 0
        total_spiders = len(self.spiders)
        logger.info("total sources <%3d>", total_spiders)
        if locker.inited():  # 使用多线程并发运行全部的爬虫
            threads = []
            for spd in self.spiders:
                threads.append(start_thread(self._run_one, spd))  # 将全部爬虫都放入线程中

            for thd in threads:  # 等待全部线程执行完毕
                thd.join()
        else:
            idx = 1
            for spd in self.spiders:  # 在主线程中顺序执行全部的爬虫
                logger.info("progress <%3d/%d>", idx, total_spiders)
                self._run_one(spd)
                idx += 1

        logger.info("total sources <%d>. new infos <%d>.", total_spiders, self.infos)

    def loop(self):
        """进行持续循环运行"""
        while True:
            self.run()
            time.sleep(1)

    def close(self):
        self.spiders.clear()
        self.spiders = None
        self.dbs = None
        logger.info('tiny spider collect manager is stop.')


def make_collect_mgr(log_path='./log_spd_tiny.txt', db_path='spd_tiny.sqlite3', log_con_lvl=logging.INFO, log_file_lvl=logging.INFO):
    """创建采集系统管理器对象,告知日志路径和数据库路径.
        返回值:None失败.其他为采集系统管理器对象
    """
    global logger
    logger = make_logger(log_path, log_file_lvl)
    bind_logger_console(logger, log_con_lvl)

    dbs = db_base(db_path)  # 打开数据库
    if not dbs.opened():
        logger.error('DB open fail. <%s>', db_path)
        return None

    if not dbs.dbq.has('tbl_sources'):
        for s in sql_tbl:
            ret, msg = dbs.db.exec(s)  # 尝试在新库中自动建表
            if not ret:
                logger.error("DB init create fail! < %s >" % msg)

    cm = collect_manager(dbs)
    return cm


def run_collect_sys(dbg_src=None):
    # 定义并处理命令行参数
    def get_params():
        parser = argparse.ArgumentParser()
        parser.add_argument("--workdir", type=str, default='', help="spider work dir.")
        parser.add_argument("--tagname", type=str, default='', help="spider tag name.")
        parser.add_argument("--dbname", type=str, default='', help="sqlite3 db file name.")
        parser.add_argument("--logname", type=str, default='', help="spider log file name.")
        parser.add_argument("--prefix", type=str, default='src_', help="source file name prefix.")
        parser.add_argument("--thread", type=int, default=0, help="enable thread mode.")
        parser.add_argument("--debug", type=int, default=0, help="enable debug info output.")
        return parser.parse_args()

    args = get_params()

    # 获取当前文件所在路径,添加到python搜索路径中
    curdir = args.workdir if args.workdir != '' else os.path.dirname(os.path.abspath(sys.argv[0]))
    sys.path.append(curdir)
    sys.path.append(curdir + '/spd')
    sys.path.append(curdir + '/src')

    # 是否开启多线程并发模式
    if args.thread:
        locker.init()

    # 获取运行文件名称作为标记
    tag = args.tagname if args.tagname != '' else re.split('[\\\\/]', sys.argv[0])[-1].split('.')[0]

    dbname = args.dbname if args.dbname != '' else './%s.sqlite3' % tag
    logname = args.logname if args.logname != '' else './%s.log' % tag

    # 获取采集系统对象并打开数据库与日志
    cm = make_collect_mgr(logname, dbname, logging.INFO)
    if cm is None:
        print('SDP INIT FAIL!')
        exit(-1)

    # 注册采集源
    if dbg_src:
        cm.register('src.%s' % dbg_src)
    else:
        # 装载采集源列表
        srcs = os.listdir(curdir + '/src')
        for s in srcs:
            if not s.startswith(args.prefix):
                continue
            if not s.endswith('.py'):
                continue
            cm.register('src.%s' % s[:-3])

    # 运行全部采集爬虫
    cm.run()
    cm.close()
