import json

"""
    针对自动生成的CDP类型与事件对象(构造函数中描述了成员与类别)的轻量级序列化和反序列化功能.
"""


class jsonable:
    """自描述对象的序列化与反序列化功能"""

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
    def encode(obj):
        """将obj序列化为json串"""

        def _as_dict(obj, datas):
            """将obj对象完整递归转换为datas字典数据"""
            for key in obj.__dict__:
                value = getattr(obj, key)
                if jsonable._is_basic(value):
                    datas[key] = value  # 基础类型,直接记录
                else:
                    sval = jsonable._is_list(value)
                    if not sval:
                        datas[key] = {}  # 无需迭代,单对象
                        _as_dict(value, datas[key])
                    elif jsonable._is_basic(sval):
                        datas[key] = [v for v in value]  # 可迭代的基础类型
                    else:
                        datas[key] = [_as_dict(v, {}) for v in value]  # 可迭代的对象类型

            return datas

        return json.dumps(_as_dict(obj, {}), ensure_ascii=False)

    @staticmethod
    def decode(cls, jdat, *args, **argv):
        """装载json串或数据字典jdat到cls类别实例对象中并返回."""
        obj = cls(*args, **argv)  # 默认构造目标结果对象,要求其默认成员为类型描述

        def _as_value(obj, dat):
            for key in obj.__dict__:
                if key not in dat:
                    setattr(obj, key, None)
                    continue
                value = getattr(obj, key)
                if jsonable._is_basic(value):
                    setattr(obj, key, dat[key])  # 基础类型,直接赋值
                else:
                    stype = jsonable._is_list(value)
                    if not stype:
                        _as_value(value, dat[key])  # 无需迭代,单对象
                    elif jsonable._is_basic(stype):
                        setattr(obj, key, [v for v in dat[key]])  # 可迭代的基础类型
                    else:
                        setattr(obj, key, [_as_value(stype(), v) for v in dat[key]])  # 可迭代的对象类型
            return obj

        return _as_value(obj, json.loads(jdat, encoding='utf8') if isinstance(jdat, str) else jdat)
