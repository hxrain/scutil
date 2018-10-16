--获取Lock标识
local lockkey = KEYS[1]
--获取owner标识
local owner = ARGV[1]
--锁的续期时间(ms,在持续时间内再次上锁则进行续约)
local ptime = tonumber(ARGV[2])

--锁操作返回值:
--      > 0成功:1锁定成功;2续约成功
--      <=0错误:0无法锁定;-1续约错误

--先尝试直接设置
local rc=redis.call('set',lockkey,owner,'nx','px',ptime)

if type(rc)=='table' and rc.ok=='OK' then
    --直接设置成功,锁定完成
    return 1
else
    --直接设置不成功,需要判断是否为续约
    if redis.call('get',lockkey) == owner then
        --续约动作,设置新的生存时间
        if redis.call('PEXPIRE',lockkey,ptime)==1 then
            return 2
        else
            return -1   --续约错误
        end
    else
        return 0    --不是续约,也不是初次锁定,操作不成功
    end
end
