# -*- coding: utf-8 -*-
"""
     CDP - Chrome DevTools Protocol
     这里封装一套CDP客户端,便于操控Chrome,完成高级爬虫相关功能.
"""

import util_base as ub
import json


def make_cdp_driver_api(fname='./cdp/cdp.json', indent=0):
    """根据CDP描述文件生成驱动模块的API接口代码"""
    from flask import Flask, render_template_string
    app = Flask(__name__)
    srcs, err = ub.dict_load2(fname)
    if err:
        return err
    rst = []

    def rec(txt='', sp=0):
        lines = txt.split('\n')
        for line in lines:
            if not line:
                rst.append('\n')
            else:
                rst.append(f"{' ' * indent * 4}{' ' * sp * 4}{line}")

    def make_import(domain, name):
        """生成功能域文件导入项"""
        rec('''"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""''')
        rec('''from cdp.cdp_comm import *''')
        rec()

    def make_domain(domain, name):
        """生成功能域对应的类结构"""
        deps = domain.get('dependencies', [])
        for dep in deps:
            rec(f'''import cdp.{dep} as {dep}''')

        desc = domain.get('description', name)
        rec(f'''# ================================================================================''')
        rec(f'''# {name} Domain.''')
        rec(f'''# ================================================================================''')
        rec(f'''class {name}(DomainT):''')
        rec(f'''"""''', 1)
        rec(desc, 2)
        rec(f'''"""''', 1)
        rec(f'''def __init__(self, drv):''', 1)
        rec(f'''self.drv = drv''', 2)
        rec()

    def take_ref(data, domainName=''):
        if '$ref' not in data:
            return 'BAD_TYPE!!'
        ref = data['$ref']
        if ref.find('.') == -1 and domainName:
            ref = f'{domainName}.{ref}'
        return ref

    def take_type(data):
        """根据描述数据对象,分析对应py中的数据类型"""
        type = data.get('type')
        maps = {'integer': 'int', 'string': 'str', 'object': 'class', 'number': 'int', 'boolean': 'bool', 'binary': 'str', 'any': 'str'}
        if type in maps:
            return maps[type]
        elif type == 'array':
            itype = data['items'].get('type')
            if not itype:
                itype = take_ref(data['items'])
            if itype in maps:
                itype = maps[itype]
            return f'List[{itype}]'
        else:
            return take_ref(data)

    def make_type(data, domainName):
        """生成当前功能域下的数据结构定义"""
        name = data['id']
        desc = data.get('description', name).strip()
        type = take_type(data)
        enum = data.get('enum', None)
        if type in {'int', 'str', 'bool'}:  # 输出简单类型
            desc = desc.replace('\n', '')
            rec(f'''# typing: {desc}''')
            rec(f'''{name} = {type}''')
            if enum:
                rec(f'''{name}Enums = {enum}''')
        elif type.startswith('List['):  # 输出数组类型
            desc = desc.replace('\n', '')
            rec(f'''# typing: {desc}''')
            rec(f'''{name} = {type}''')
        elif type == 'class':  # 输出复杂类
            rec(f'''# object: {name}''')
            rec(f'''class {name}(TypingT):''')
            rec(f'''"""''', 1)
            rec(desc, 2)
            rec(f'''"""''', 1)
            rec(f'''def __init__(self):''', 1)
            props = data.get('properties', [])
            for prop in props:
                pname = prop['name']
                pdesc = prop.get('description', pname).replace('\n', '')
                poptl = 'OPTIONAL, ' if prop.get('optional') else ''
                ptype = take_type(prop)
                rec(f'''# {poptl}{pdesc}''', 2)
                rec(f'''self.{pname}: {ptype} = {ptype[4:] if ptype.startswith('List') else ptype}''', 2)
            if not props:
                rec(f'''pass''', 2)
        else:
            assert False, 'UNKNOWN!'
        rec()

    def make_event(data, domainName):
        """生成当前功能域下的事件通知对象"""
        if data.get('experimental', False):
            return
        name = data['name']
        desc = data.get('description', name).strip()
        props = data.get('parameters', [])
        rec(f'''# event: {name}''')
        rec(f'''class {name}(EventT):''')
        rec(f'''"""''', 1)
        rec(desc, 2)
        rec(f'''"""''', 1)
        rec(f'''event="{domainName}.{name}"''', 1)
        rec(f'''def __init__(self):''', 1)
        for prop in props:
            pname = prop['name']
            pdesc = prop.get('description', pname).replace('\n', '')
            penum = prop.get('enum', None)
            poptl = 'OPTIONAL, ' if prop.get('optional') else ''
            ptype = take_type(prop)
            if penum:
                rec(f'''{pname}Enums = {penum}''', 2)
            rec(f'''# {poptl}{pdesc}''', 2)
            rec(f'''self.{pname}: {ptype} = {ptype[4:] if ptype.startswith('List') else ptype}''', 2)
        if not props:
            rec(f'''pass''', 2)
        rec()

    def make_method_return(data, domainName):
        """生成当前功能域下的功能方法API的返回值"""
        props = data.get('returns')
        if not props:
            return
        name = data['name']
        rec(f'''# return: {name}Return''', 1)
        rec(f'''class {name}Return(ReturnT):''', 1)
        rec(f'''def __init__(self):''', 2)
        for prop in props:
            pname = prop['name']
            pdesc = prop.get('description', pname).replace('\n', '')
            penum = prop.get('enum', None)
            poptl = 'OPTIONAL, ' if prop.get('optional') else ''
            ptype = take_type(prop)
            if penum:
                rec(f'''{pname}Enums = {penum}''', 3)
            rec(f'''# {poptl}{pdesc}''', 3)
            rec(f'''self.{pname}: {ptype} = {ptype[4:] if ptype.startswith('List') else ptype}''', 3)
        if not props:
            rec(f'''pass''', 3)
        rec()

    def make_method_func(data, domainName):
        """生成当前功能域下的功能方法API函数调用"""
        name = data['name']
        desc = data.get('description', '').strip()
        props = data.get('parameters', [])
        rtype = f'{name}Return' if data.get('returns') else ''
        rtstr = f' -> {rtype}' if data.get('returns') else ''
        # 先生成入参列表
        args = []
        argv = []
        for prop in props:
            pname = prop['name']
            ptype = take_type(prop)
            poptl = prop.get('optional')
            args.append(f'{pname}:{ptype}{"=None" if poptl else ""}')
            argv.append(f'{pname}={pname}')
        args.append('**kwargs')
        argv.append('**kwargs')
        # 生成函数方法声明
        rec(f'''# func: {name}''', 1)
        rec(f'''def {name}(self,{', '.join(args)}){rtstr}:''', 1)
        # 生成函数方法描述
        rec(f'''"""''', 2)
        if desc:
            rec(desc, 3)
        if props:
            # 生成函数参数说明
            rec(f'''Params:''', 2)
            for i, prop in enumerate(props):
                pname = prop['name']
                pdesc = prop.get('description', '').replace('\n', '')
                poptl = ' (OPTIONAL)' if prop.get('optional') else ''
                ptype = take_type(prop)
                penum = prop.get('enum', None)
                if penum:
                    rec(f'''{pname}Enums = {penum}''', 3)
                rec(f'''{i + 1}. {pname}: {ptype}{poptl}''', 3)
                if pdesc:
                    rec(f'''{pdesc}''', 4)
        if rtype:
            # 生成函数返回值类型说明
            rec(f'''Return: {rtype}''', 2)
        rec(f'''"""''', 2)
        # 生成底层转发调用
        retv = f"""{domainName}.{rtype}""" if rtype else 'None'
        rec(f'''return self.drv.call({retv},'{domainName}.{name}',{', '.join(argv)})''', 2)
        rec()

    def make_drv_init(domains):
        rst.clear()
        for domain_name in domains:
            rec(f'''from cdp import {domain_name}''')
        rec()
        rec(f'''def __init__(self):''')
        for domain_name in domains:
            rec(f'''self.{domain_name} = {domain_name}.{domain_name}(self)''', 1)
        return '\n'.join(rst)

    domains = []
    for dm in srcs['domains']:  # 对全部CDP功能域进行遍历
        rst.clear()
        if dm.get('experimental'):
            continue  # 体验版功能域不处理
        if dm.get('deprecated'):
            continue  # 被废弃功能域不处理
        domain_name = dm['domain']
        domains.append(domain_name)
        make_import(dm, domain_name)
        for data in dm.get('types', []):
            make_type(data, domain_name)
        for data in dm.get('events', []):
            make_event(data, domain_name)
        make_domain(dm, domain_name)
        for data in dm.get('commands', []):
            make_method_return(data, domain_name)
            make_method_func(data, domain_name)
        rec()
        ub.save_to_file2('./cdp/', f'{domain_name}.py', '\n'.join(rst))

    return make_drv_init(domains)


c = make_cdp_driver_api()
print(c)
