#! /usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from tab import Tab


# Chrome浏览器管理对象
class Browser(object):

    def __init__(self, url="http://127.0.0.1:9222"):
        self.dev_url = url
        self._tabs = {}  # 记录被管理的tab页

    def new_tab(self, url=None, timeout=None):
        """打开新tab页,并浏览指定的网址"""
        url = url or ''
        rp = requests.get("%s/json/new?%s" % (self.dev_url, url), json=True, timeout=timeout)
        tab = Tab(**rp.json())
        self._tabs[tab.id] = tab
        return tab

    def list_tab(self, timeout=None):
        """列出浏览器所有打开的tab页"""
        rp = requests.get("%s/json" % self.dev_url, json=True, timeout=timeout)
        tabs_map = {}
        for tab_json in rp.json():
            if tab_json['type'] != 'page':  # pragma: no cover
                continue  # 只保留page页面tab,其他后台进程不记录

            id = tab_json['id']
            if id in self._tabs and self._tabs[id].status != Tab.status_stopped:
                tabs_map[id] = self._tabs[id]
            else:
                tabs_map[id] = Tab(**tab_json)

        self._tabs = tabs_map
        return list(self._tabs.values())

    def activate_tab(self, tab_id, timeout=None):
        """激活指定的tab页"""
        if isinstance(tab_id, Tab):
            tab_id = tab_id.id

        rp = requests.get("%s/json/activate/%s" % (self.dev_url, tab_id), timeout=timeout)
        return rp.text

    def close_tab(self, tab_id, timeout=None):
        """关闭指定的tab页"""
        if isinstance(tab_id, Tab):
            tab_id = tab_id.id

        tab = self._tabs.pop(tab_id, None)
        if tab and tab.status == Tab.status_started:  # pragma: no cover
            tab.stop()

        rp = requests.get("%s/json/close/%s" % (self.dev_url, tab_id), timeout=timeout)
        return rp.text

    def version(self, timeout=None):
        """查询浏览器的版本信息"""
        rp = requests.get("%s/json/version" % self.dev_url, json=True, timeout=timeout)
        return rp.json()

    def __str__(self):
        return '<Browser %s>' % self.dev_url

    __repr__ = __str__
