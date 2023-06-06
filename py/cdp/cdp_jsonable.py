# -*- coding: utf-8 -*-
"""
    针对自动生成的CDP类型与事件对象(构造函数中描述了成员与类别)的轻量级序列化和反序列化功能.
"""
import json
import sys


class jsonable:
    """自描述对象的序列化与反序列化功能"""
    custom_procs = {}  # 自定义编解码器处理函数映射表 {'class':(func_en,func_de)}

    @staticmethod
    def _is_basic(value):
        """判断指定的值类型,是否为内置的基本类型"""
        if value is None:
            return True
        if type(value) is not type:
            value = type(value)
        return value in {int, float, str, bool}

    @staticmethod
    def _is_list(value):
        """判断指定的值类型,是否为可迭代容器类型"""
        if value is not None and type(value) is list:
            return value[0]
        return None

    @staticmethod
    def bind(cls, func_de, func_en=None):
        """绑定指定类型cls的自定义反序列化func_de函数与序列化函数func_en"""
        jsonable.custom_procs[cls.__name__] = (func_en, func_de)

    @staticmethod
    def encode(obj):
        """将obj序列化为json串"""

        def _dat_key(key):
            ul = getattr(obj, 'underline', None)
            if ul is None:
                return key
            return key.replace('_', ul)

        def _as_dict(obj, datas):
            """将obj对象完整递归转换为datas字典数据"""
            for key in obj.__dict__:
                value = getattr(obj, key)
                datkey = _dat_key(key)
                if jsonable._is_basic(value):
                    datas[datkey] = value  # 基础类型,直接记录
                else:
                    sval = jsonable._is_list(value)
                    if not sval:
                        datas[datkey] = {}  # 无需迭代,单对象
                        _as_dict(value, datas[datkey])
                    elif jsonable._is_basic(sval):
                        datas[datkey] = [v for v in value]  # 可迭代的基础类型
                    else:
                        datas[datkey] = [_as_dict(v, {}) for v in value]  # 可迭代的对象类型

            return datas

        out = None
        # 尝试使用自定义编码函数进行特殊编码处理
        clsname = obj.__class__.__name__
        if clsname in jsonable.custom_procs:
            func = jsonable.custom_procs[clsname][0]
            if func:
                out = func(obj)
        if out is None:
            out = _as_dict(obj, {})
        return json.dumps(out, ensure_ascii=False)

    @staticmethod
    def decode(cls, jdat, *args, **argv):
        """装载json串或数据字典jdat到cls类别实例对象中并返回."""
        obj = cls(*args, **argv)  # 默认构造目标结果对象,要求其默认成员为类型描述

        def _dat_key(key):
            ul = getattr(cls, 'underline', None)
            if ul is None:
                return key
            return key.replace('_', ul)

        def _as_value(obj, dat):
            for key in obj.__dict__:
                datkey = _dat_key(key)
                if datkey not in dat:
                    setattr(obj, key, None)
                    continue
                value = getattr(obj, key)
                if jsonable._is_basic(value):
                    setattr(obj, key, dat[datkey])  # 基础类型,直接赋值
                else:
                    stype = jsonable._is_list(value)
                    if not stype:
                        setattr(obj, key, _as_value(value(), dat[datkey]))  # 无需迭代,单对象
                    elif jsonable._is_basic(stype):
                        setattr(obj, key, [v for v in dat[datkey]])  # 可迭代的基础类型
                    else:
                        setattr(obj, key, [_as_value(stype(), v) for v in dat[datkey]])  # 可迭代的对象类型
            return obj

        if isinstance(jdat, str):
            if sys.version_info < (3, 9):
                dat = json.loads(jdat, encoding='utf8')
            else:
                dat = json.loads(jdat)
        else:
            dat = jdat

        # 尝试使用自定义解码函数进行特殊解码处理
        clsname = obj.__class__.__name__
        if clsname in jsonable.custom_procs:
            func = jsonable.custom_procs[clsname][1]
            if func:
                return func(obj, dat)

        return _as_value(obj, dat)
