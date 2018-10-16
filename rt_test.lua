#! /usr/bin/lua

--默认测试连接目标服务器
local host = "20.0.2.154"
local port = 8001

--引入 https://github.com/nrk/redis-lua 模块
redis = require 'redis'

--伪装redis内部接口方法
redis.call = function(cmd, ...) 
    --原理是根据给定的cmd动态拼装redis客户端调用方法
    return assert(loadstring('return client:'.. string.lower(cmd) ..'(...)'))(...)
end

--输出外部脚本执行结果
local dump = function(v) 
    if nil ~= v then
	print("----------------return---------------")
	print(v)
	print("-------------------------------------\n")
    else
	print("done with non return")
    end
end

--执行外部脚本
local exec = function (script_file)
	print("executing script...")
	s=loadfile(script_file)
	print("----------------output---------------")
    return s()
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
    print("usage:\n\t lua.exe rt_test.lua -p xx -h xxx --eval script key1 key2 , arg1 arg2")
    return
end

--连接目标redis
print("connect to "..host..":"..port)
client = redis.connect(host, port)
if not client:ping() then
	print("client " .. host..":"..port.." unreachable")
	return
end

--执行外部脚本并输出结果
dump(exec(script_file))




