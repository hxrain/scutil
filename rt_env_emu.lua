--要求使用lua/5.3 版本的环境.

--引入 https://github.com/nrk/redis-lua 模块
redis = require 'redis'
--引入 https://github.com/openresty/lua-cjson 模块
cjson = require 'cjson'
--引入 https://github.com/antirez/lua-cmsgpack 模块
cmsgpack = require 'cmsgpack'

--伪装redis内部日志打印方法
redis.LOG_DEBUG='debug'
redis.LOG_VERBOSE='verbose'
redis.LOG_NOTICE='notice'
redis.LOG_WARNING='warn'
redis.log = function(lvl, ...) 
    print(lvl..':',...)
end

--伪装redis内部接口调用方法
redis.call = function(cmd, ...) 
    --原理是根据给定的cmd动态拼装redis客户端调用方法
    local rc=load('return client:'.. string.lower(cmd) ..'(...)')(...)
    
    --根据redis结果规则,将k/v值转换为k,v...顺序数组
    local ret={}
    for i,v in pairs(rc) do
        if type(i) ~='number' then      --数组的索引不放入最终结果
            table.insert(ret,i)         
        end
        table.insert(ret,v)
    end
    return ret
end

--连接目标redis
function ready(host,port)
    print("connect to "..host..":"..port)
    client = redis.connect(host, port)
    if not client:ping() then
        print("client " .. host..":"..port.." unreachable")
        return false
    end
    return true
end

--外面需要调用此方法,连接服务器
return ready


