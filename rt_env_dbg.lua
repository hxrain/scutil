#! /usr/bin/lua

--默认测试连接目标服务器
local host = "20.0.2.154"
local port = 8001

--输出外部脚本执行结果
local dump = function(v) 
    if nil ~= v then
        print("----------------return---------------")
        if type(v)=='table' then
            for i=1,#v do
                print(v[i])
            end
            print('Total '..#v)
        else
            print(v)
        end
        print("-------------------------------------\n")
    else
        print("done with non return")
    end
end

--执行外部脚本
local exec = function (script_file)
	print("executing script...")
	local scritp=loadfile(script_file)
	print("----------------output---------------")
    return scritp()                 --执行外部脚本,可以跟踪进入逐行调试
end

--工作使用的变量
local script_file = ""
_G.KEYS={}
_G.ARGV={}

--解析命令行参数
local is_keys=true
local i=1
while i<=#arg do
	if arg[i] == '-p' then          --尝试解析redis端口
		port = tonumber(arg[i+1])
        i = i + 2
	elseif arg[i] == '-h' then      --尝试解析redis地址
        host = arg[i+1]
        i = i + 2
	elseif arg[i] == '--eval' then  --尝试解析外部脚本名称
		script_file = arg[i+1]
        i = i + 2
	else                            --尝试解析keys和argv
        if arg[i]==',' then
            is_keys=false
        elseif is_keys then
            table.insert(_G.KEYS,arg[i])
        else
            table.insert(_G.ARGV,arg[i])
        end
        i = i + 1
    end
end

--检查脚本参数
if script_file == "" then
    print("usage:\n\t lua.exe rt_env_dbg.lua -p xx -h xxx --eval script key1 key2 , arg1 arg2")
    return
end

--导入redis与仿真模块
emu = require 'rt_env_emu'

--连接redis并执行外部脚本
if emu(host,port) then
    dump(exec(script_file))
end




