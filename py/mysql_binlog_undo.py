# -*- coding: utf-8 -*-

import re

import time

#定义函数，进行utc秒到标准时间的转换
def utc2loc(sec):
    ltime=time.localtime(int(sec))
    timeStr=time.strftime("%Y-%m-%d %H:%M:%S", ltime)
    return timeStr

#打开输出文件
out_file=open('C:\\Users\\admin\\Desktop\\mysql-binlog数据\\do.sql','w',encoding='utf-8')

#打开输入文件并读取
in_file=open('C:\\Users\\admin\\Desktop\\mysql-binlog数据\\log.sql','r',encoding='utf-8')
in_str=in_file.read()

#定义insert搜索re表达式并提取结果
re_find=r'''### INSERT INTO `pro_data`\.`sys_label_plan`\s*### SET\s*###\s*@1=(\d*)'''
m=re.findall(re_find,in_str,re.DOTALL)

#将insert语句的数据内容改为delete语句并输出
for i in m:
    s='delete from `pro_data`.`sys_label_plan` where id=%s;\n' % (i)
    out_file.writelines([s])
    #print(s)

#定义delete搜索re表达式并提取结果
re_find=r'''DELETE FROM `pro_data`\.`sys_label_plan`.*?@1=(\d*).*?@2='(.*?)'.*?@3='(.*?)'.*?@4='(.*?)'.*?@5='(.*?)'.*?@6=(\d*).*?@7=(\d*).*?@8=(\d*).*?@9=(\d*).*?@10=(\d*).*?@11=(\d*).*?# at'''
m=re.findall(re_find,in_str,re.DOTALL)

#将delete语句中的数据转换为insert语句并输出
for i in m:
    #print(i)
    s="insert into `pro_data`.`sys_label_plan` values(%s,'%s','%s','%s','%s',%s,%s,%s,%s,%s,'%s');\n" % (i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8],i[9],utc2loc(i[10]))
    out_file.writelines([s])

